"""Extrae de los archivos históricos de AIFS, IFS (ECMWF en AWS) y GFS (NOAA en AWS) el pronóstico en cada
estación: temperatura a 2 m, precipitación acumulada desde el inicio de la corrida, viento a 10 m (u, v) y ráfaga
(IFS: 10fg, máxima de las 6 h previas; GFS: GUST, instantánea; AIFS no publica ráfaga), para las corridas de
00 y 12 UTC y los plazos de 24, 48 y 72 h. Baja solo los mensajes GRIB necesarios por rango de bytes
(1-2 MB cada uno), los lee en memoria y escribe un CSV pequeño. No guarda GRIB.

Uso: python extraer_puntos.py --modelo aifs|ifs|gfs --desde 2026-10-01 --hasta 2026-10-03
Salida: data/puntos/{MODELO}_{desde}_{hasta}.csv con columnas modelo,run,lead_h,valid,icao,t_fc,tp_fc,u_fc,v_fc,g_fc"""
import argparse, csv, datetime as dt, http.client, json, os, re, sys, time, urllib.error, urllib.request
import eccodes as ec

AQUI = os.path.dirname(os.path.abspath(__file__))
PASOS = [24, 48, 72]
HORAS = [0, 12]
ECMWF = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
GFS = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
UA = {"User-Agent": "earth2-chile-verificacion/historico"}
PAUSA = 0.15


def estaciones(ruta=None):
    """(icao, lat, lon) de los puntos: los aeródromos (estaciones.csv) u otra lista con las mismas columnas
    (estaciones_dmc.csv: la red de la DMC, icao = "D" + código nacional)."""
    ruta = ruta or os.path.join(AQUI, "estaciones.csv")
    return [(r["icao"], float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(ruta, encoding="utf-8")) if r.get("lat") and r.get("lon")]


def get(url, rango=None, intentos=8):
    """GET con reintentos acotados. El bucket de ECMWF responde '503 SlowDown' bajo carga: esperar y repetir."""
    for i in range(intentos):
        try:
            h = dict(UA)
            if rango:
                h["Range"] = f"bytes={rango[0]}-{rango[1]}"
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(90, 2 * 2 ** i)); continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):   # incluye lecturas cortadas
            time.sleep(min(90, 2 * 2 ** i))
    print("  sin respuesta tras", intentos, "intentos:", url); return None


def rangos_ecmwf(modelo, run, paso):
    """Devuelve {param: (url_grib, (ini, fin))} para 2t, tp, 10u, 10v y 10fg a partir del índice JSON-lines de ECMWF."""
    base = f"{ECMWF}/{run:%Y%m%d}/{run:%H}z/{modelo}/0p25/oper/{run:%Y%m%d%H}0000-{paso}h-oper-fc"
    idx = get(base + ".index")
    if not idx:
        return {}
    out = {}
    for linea in idx.decode().splitlines():
        try:
            e = json.loads(linea)
        except ValueError:
            continue
        if e.get("param") in ("2t", "tp", "10u", "10v", "10fg") and e.get("levtype", "sfc") == "sfc":
            off, ln = int(e["_offset"]), int(e["_length"])
            out[e["param"]] = (base + ".grib2", (off, off + ln - 1))
    return out


def rangos_gfs(run, paso):
    """Devuelve {param: (url_grib, (ini, fin))} para TMP 2 m y APCP acumulado 0-paso a partir del .idx de wgrib2."""
    base = f"{GFS}/gfs.{run:%Y%m%d}/{run:%H}/atmos/gfs.t{run:%H}z.pgrb2.0p25.f{paso:03d}"
    idx = get(base + ".idx")
    if not idx:
        return {}
    lineas = [l.split(":") for l in idx.decode().splitlines() if l.strip()]
    out = {}
    for i, l in enumerate(lineas):
        if len(l) < 6:
            continue
        off = int(l[1]); fin = int(lineas[i + 1][1]) - 1 if i + 1 < len(lineas) else ""
        desc = ":".join(l[3:6])
        if desc.startswith("TMP:2 m above ground:"):
            out["2t"] = (base, (off, fin))
        elif desc.startswith("UGRD:10 m above ground:"):
            out["10u"] = (base, (off, fin))
        elif desc.startswith("VGRD:10 m above ground:"):
            out["10v"] = (base, (off, fin))
        elif desc.startswith("GUST:surface:"):
            out["10fg"] = (base, (off, fin))
        elif desc.startswith("APCP:surface:") and re.search(rf"APCP:surface:0-({paso} hour|{paso // 24} day) acc", desc):
            out["tp"] = (base, (off, fin))
    return out


def valores(datos, ests):
    """Valor del punto de grilla más cercano a cada estación. Precipitación siempre en mm (IFS la trae en m)."""
    gid = ec.codes_new_from_message(datos)
    try:
        unidades = ec.codes_get(gid, "units")
        factor = 1000.0 if unidades == "m" else 1.0
        return {icao: ec.codes_grib_find_nearest(gid, lat, lon)[0].value * factor for icao, lat, lon in ests}
    finally:
        ec.codes_release(gid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", required=True, choices=["aifs", "ifs", "gfs"])
    ap.add_argument("--desde", required=True); ap.add_argument("--hasta", required=True)
    ap.add_argument("--salida", default=os.path.join(AQUI, "data", "puntos"))
    ap.add_argument("--puntos", help="CSV de puntos (icao, lat, lon); por defecto, los aeródromos de estaciones.csv")
    a = ap.parse_args()
    d0, d1 = dt.date.fromisoformat(a.desde), dt.date.fromisoformat(a.hasta)
    nombre = {"aifs": "AIFS", "ifs": "IFS", "gfs": "GFS"}[a.modelo]
    ests = estaciones(a.puntos)
    os.makedirs(a.salida, exist_ok=True)
    salida = os.path.join(a.salida, f"{nombre}_{d0:%Y%m%d}_{d1:%Y%m%d}.csv")
    hechos = set()
    if os.path.exists(salida):
        for r in csv.DictReader(open(salida)):
            hechos.add((r["run"], int(r["lead_h"])))
    f = open(salida, "a", newline="")
    w = csv.writer(f)
    if not hechos:
        w.writerow(["modelo", "run", "lead_h", "valid", "icao", "t_fc", "tp_fc", "u_fc", "v_fc", "g_fc"])
    t0 = time.time(); n_ok = n_falta = 0
    dia = d0
    while dia <= d1:
        for h in HORAS:
            run = dt.datetime(dia.year, dia.month, dia.day, h)
            for paso in PASOS:
                if (f"{run:%Y-%m-%d %H:%M:%S}", paso) in hechos:
                    continue
                rangos = rangos_gfs(run, paso) if a.modelo == "gfs" else rangos_ecmwf("aifs-single" if a.modelo == "aifs" else "ifs", run, paso)
                time.sleep(PAUSA)
                if "2t" not in rangos:
                    n_falta += 1; print(f"  {run:%Y-%m-%d %Hz} +{paso}h: sin datos"); continue
                campos = {}
                for param, (url, rango) in rangos.items():
                    datos = get(url, rango); time.sleep(PAUSA)
                    if datos:
                        campos[param] = valores(datos, ests)
                if "2t" not in campos:
                    n_falta += 1; continue
                valid = run + dt.timedelta(hours=paso)
                for icao, _, _ in ests:
                    t = campos["2t"][icao] - 273.15
                    tp = campos.get("tp", {}).get(icao)
                    extra = [campos.get(k, {}).get(icao) for k in ("10u", "10v", "10fg")]
                    w.writerow([nombre, f"{run:%Y-%m-%d %H:%M:%S}", paso, f"{valid:%Y-%m-%d %H:%M:%S}", icao,
                                round(t, 2), "" if tp is None else round(tp, 2)] + ["" if x is None else round(x, 2) for x in extra])
                n_ok += 1
            f.flush()
        print(f"{nombre} {dia}: listo ({n_ok} corridas-plazo, {n_falta} faltantes, {round(time.time() - t0)} s)", flush=True)
        dia += dt.timedelta(days=1)
    f.close()
    print("salida:", salida)


if __name__ == "__main__":
    main()
