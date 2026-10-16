"""Monitor del océano (capa estándar 3): anomalía de temperatura del mar frente a la costa de Chile y en Niño 1+2,
desde datos primarios (nunca desde noticias).

Fuentes (dominio público, NOAA):
  - OISST v2.1 diario a 0,25° (AWS noaa-cdr-sea-surface-temp-optimum-interpolation-pds; respaldo NCEI). Los últimos
    ~14 días son "preliminares" y se reemplazan por la versión final; por eso cada corrida reprocesa los últimos 20 días.
  - Climatología diaria 1991-2020 de NOAA PSL (sst.day.mean.ltm.1991-2020), leída por OPeNDAP solo en las cajas.
  - Índices semanales Niño 1+2, 3, 3.4 y 4 de NOAA CPC (wksst9120.for, base 1991-2020).

Salidas en oceano/data/: clima_cajas.csv (una vez), sst_cajas.csv (diario, acumulado), nino_semanal.csv.
Uso: python oceano/oceano.py                 -> clima si falta, últimos 20 días y CPC
     python oceano/oceano.py --desde 2025-01-01  -> relleno histórico (lento: ~1,5 MB por día)"""
import argparse, csv, datetime as dt, io, os, sys, time, urllib.error, urllib.request
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
EST = os.path.join(AQUI, "..", "historico", "estaciones.csv")
AWS = "https://noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.amazonaws.com/data/v2.1/avhrr/{ym}/oisst-avhrr-v02r01.{ymd}{suf}.nc"
NCEI = "https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/{ym}/oisst-avhrr-v02r01.{ymd}{suf}.nc"
CLIMA = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.ltm.1991-2020.nc"
CPC = "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for"
UA = {"User-Agent": "earth2-chile-verificacion/oceano (github.com/PanchoDigevo/earth2-chile-verificacion)"}

# Aeródromos costeros y su tramo de costa. La caja va mar adentro: ±0,5° de latitud y 1,25° de longitud al oeste.
COSTA = [("SCAR", "Arica"), ("SCDA", "Iquique"), ("SCFA", "Antofagasta"), ("SCAT", "Caldera"), ("SCSE", "La Serena"),
         ("SCSN", "Santo Domingo"), ("SCIE", "Concepción"), ("SCTE", "Puerto Montt")]


def cajas():
    est = {r["icao"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(EST, encoding="utf-8"))}
    out = {}
    for icao, nombre in COSTA:
        la, lo = est[icao]
        out[icao] = (nombre, la - 0.5, la + 0.5, 360 + lo - 1.25, 360 + lo)
    out["NINO12"] = ("Niño 1+2", -10.0, 0.0, 270.0, 280.0)
    return out


def get(url, intentos=4, timeout=180):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(10 * (i + 1))
        except Exception:
            time.sleep(10 * (i + 1))
    return None


def indices(lat, lon, caja):
    _, la0, la1, lo0, lo1 = caja
    return np.where((lat >= la0) & (lat <= la1))[0], np.where((lon >= lo0) & (lon <= lo1))[0]


def clima():
    """Media de la climatología 1991-2020 en cada caja, por día del año (365 días; el 29-feb usa el 28-feb)."""
    ruta = os.path.join(DATA, "clima_cajas.csv")
    if os.path.exists(ruta):
        out = {}
        for r in csv.DictReader(open(ruta)):
            out[(r["caja"], int(r["doy"]))] = float(r["clim"])
        return out
    import netCDF4
    print("bajando climatología 1991-2020 por OPeNDAP (solo las cajas)...", flush=True)
    d = netCDF4.Dataset(CLIMA)
    lat, lon = d["lat"][:], d["lon"][:]
    out = {}
    for k, c in cajas().items():
        ila, ilo = indices(lat, lon, c)
        for t0 in range(0, 365, 61):                     # por tramos: el servidor rechaza pedidos grandes
            t1 = min(365, t0 + 61)
            for intento in range(5):
                try:
                    v = d["sst"][t0:t1, ila[0]:ila[-1] + 1, ilo[0]:ilo[-1] + 1]; break
                except RuntimeError:
                    time.sleep(10 * (intento + 1))
            else:
                raise SystemExit(f"la climatología no respondió para {k}; alternativa: ERA5 SST")
            m = np.ma.masked_invalid(v).reshape(v.shape[0], -1).mean(axis=1)
            for i, doy in enumerate(range(t0, t1)):
                out[(k, doy + 1)] = float(m[i])
        print(f"  {c[0]} lista", flush=True)
    with open(ruta, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["caja", "doy", "clim"])
        for (k, doy), v in sorted(out.items()):
            w.writerow([k, doy, round(v, 3)])
    print("clima_cajas.csv listo", flush=True)
    return out


def doy365(fecha):
    """Día del año en un calendario de 365 días (la climatología no trae 29 de febrero)."""
    d = fecha.timetuple().tm_yday
    bisiesto = fecha.year % 4 == 0 and (fecha.year % 100 != 0 or fecha.year % 400 == 0)
    if bisiesto and fecha.month > 2:
        d -= 1
    return min(d, 365)


def oisst(fecha):
    """(datos netCDF en bytes, preliminar) para una fecha; prueba la versión final y luego la preliminar."""
    ym, ymd = f"{fecha:%Y%m}", f"{fecha:%Y%m%d}"
    for suf, prelim in (("", False), ("_preliminary", True)):
        for base in (AWS, NCEI):
            b = get(base.format(ym=ym, ymd=ymd, suf=suf))
            if b:
                return b, prelim
    return None, None


def procesar(fecha, cl, cjs):
    import netCDF4
    b, prelim = oisst(fecha)
    if b is None:
        return None
    d = netCDF4.Dataset("oisst", memory=b)
    lat, lon, sst = d["lat"][:], d["lon"][:], d["sst"][0, 0]
    filas = []
    for k, c in cjs.items():
        ila, ilo = indices(lat, lon, c)
        v = np.ma.masked_invalid(sst[ila[0]:ila[-1] + 1, ilo[0]:ilo[-1] + 1])
        if v.count() == 0:
            continue
        m = float(v.mean()); clim = cl[(k, doy365(fecha))]
        filas.append([f"{fecha:%Y-%m-%d}", k, c[0], round(m, 2), round(clim, 2), round(m - clim, 2), int(prelim), int(v.count())])
    d.close()
    return filas


def guardar_sst(nuevas):
    ruta = os.path.join(DATA, "sst_cajas.csv")
    campos = ["fecha", "caja", "nombre", "sst", "clim", "anom", "preliminar", "celdas"]
    previas = {}
    if os.path.exists(ruta):
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            previas[(r["fecha"], r["caja"])] = [r[c] for c in campos]
    for f in nuevas:
        previas[(f[0], f[1])] = f
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(campos)
        for k in sorted(previas):
            w.writerow(previas[k])
    return len(previas)


def cpc():
    b = get(CPC)
    if not b:
        print("AVISO: NOAA CPC no respondió; se conserva nino_semanal.csv anterior", flush=True); return
    filas = []
    for linea in b.decode("latin-1").splitlines():
        p = linea.split()
        if not p or not p[0][:2].isdigit() or len(p[0]) != 9:
            continue
        # columnas de ancho fijo: SST y anomalía pegadas cuando la anomalía es negativa (p. ej. "20.6-0.1")
        cuerpo = linea[10:]
        vals = [cuerpo[i:i + 13] for i in range(0, 52, 13)]
        try:
            nums = [(float(v[:5]), float(v[5:])) for v in (x.strip().rjust(9) for x in vals) if v.strip()]
        except ValueError:
            continue
        if len(nums) != 4:
            continue
        semana = dt.datetime.strptime(p[0].title(), "%d%b%Y").date()
        filas.append([f"{semana:%Y-%m-%d}"] + [x for par in nums for x in par])
    ruta = os.path.join(DATA, "nino_semanal.csv")
    with open(ruta, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["semana", "nino12_sst", "nino12_anom", "nino3_sst", "nino3_anom", "nino34_sst", "nino34_anom", "nino4_sst", "nino4_anom"])
        w.writerows(filas)
    print(f"nino_semanal.csv: {len(filas)} semanas, última {filas[-1][0]}: Niño 1+2 {filas[-1][2]:+.1f} °C, Niño 3.4 {filas[-1][6]:+.1f} °C", flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--desde"); ap.add_argument("--hasta")
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    cl, cjs = clima(), cajas()
    hoy = dt.date.today()
    d1 = dt.date.fromisoformat(a.hasta) if a.hasta else hoy
    ruta = os.path.join(DATA, "sst_cajas.csv")
    # sin historia todavía: rellenar desde 2025 (para cruzar con la deriva); si no, reprocesar los últimos 20 días
    d0 = dt.date.fromisoformat(a.desde) if a.desde else (hoy - dt.timedelta(days=20) if os.path.exists(ruta) else dt.date(2025, 1, 1))
    nuevas, faltan = [], 0
    dia = d0
    while dia <= d1:
        f = procesar(dia, cl, cjs)
        if f:
            nuevas += f
        else:
            faltan += 1
        dia += dt.timedelta(days=1)
    n = guardar_sst(nuevas)
    print(f"sst_cajas.csv: {len(nuevas)} filas nuevas o actualizadas ({faltan} días sin archivo todavía), {n} en total", flush=True)
    cpc()


if __name__ == "__main__":
    main()
