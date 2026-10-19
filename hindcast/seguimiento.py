"""Seguimiento permanente de los pronósticos sobre Santiago oriente.

Cada hora (workflow seguimiento.yml) revisa si AIFS, IFS (ECMWF open data en AWS) o GFS (NOAA en AWS) publicaron
una corrida nueva y, si es así, guarda lo que pronostica para las próximas 72 h en bloques de 6 h, para las quebradas
con laderas quemadas (centro de cada cuenca) y los aeródromos de Tobalaba y Pudahuel. Se conservan todas las corridas,
así que queda registrada la evolución del pronóstico para un mismo día, con la fecha de cada commit como prueba de que
se registró antes de que ocurriera.

Además del total, para cada quebrada quemada guarda la probabilidad y el nivel del indicador si la lluvia del bloque
cayera concentrada en 2 h (misma regla que quebradas/indicador.py), y la isoterma 0 °C de GFS (los otros no la publican).

Uso:
  python hindcast/seguimiento.py                       -> agrega las corridas nuevas a hindcast/seguimiento/pronosticos.csv
  python hindcast/seguimiento.py --evento 2026-10-20-rm --desde "2026-10-20 00:00" --hasta "2026-10-21 12:00"
                                                        -> además escribe hindcast/eventos/prerregistro/<evento>/LEEME.md
Si un servidor no responde (ECMWF limita con "503 Slow Down"), esa corrida se omite y se reintenta la hora siguiente."""
import argparse, csv, datetime as dt, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, os.path.join(RAIZ, "historico")); sys.path.insert(0, os.path.join(RAIZ, "quebradas"))
import extraer_puntos as x          # noqa: E402
import indicador as ind             # noqa: E402
import eccodes as ec                # noqa: E402

try:
    from zoneinfo import ZoneInfo
    CL = ZoneInfo("America/Santiago")
except Exception:
    CL = dt.timezone(dt.timedelta(hours=-3))
UTC = dt.timezone.utc
CSV = os.path.join(AQUI, "seguimiento", "pronosticos.csv")
CAMPOS = ["modelo", "corrida_utc", "plazo_h", "bloque_inicio_chile", "bloque_fin_chile", "punto", "nombre", "mm_6h",
          "isoterma0_m", "prob_si_2h", "nivel_si_2h", "registrado_utc"]
PASOS = list(range(6, 73, 6))
AEROPUERTOS = [("SCTB", "Tobalaba (Las Condes)", -33.456, -70.547), ("SCEL", "Santiago (Pudahuel)", -33.393, -70.786)]


def puntos():
    from shapely.geometry import shape
    cu = json.load(open(os.path.join(RAIZ, "site", "quebradas", "cuencas.geojson"), encoding="utf-8"))
    out = []
    for f in cu["features"]:
        p = f["properties"]
        if (p.get("prop_hm23") or 0) >= ind.PROP_MIN:
            c = shape(f["geometry"]).centroid
            out.append({"id": f"Q{p['id']}", "nombre": p["nombre"], "lat": c.y, "lon": c.x, "prop_hm23": p["prop_hm23"], "dnbr": p.get("dnbr_medio") or 0})
    out += [{"id": i, "nombre": n, "lat": la, "lon": lo} for i, n, la, lo in AEROPUERTOS]
    return out


def valores(datos, pts):
    if not datos:
        return None
    gid = ec.codes_new_from_message(datos)
    try:
        f = 1000.0 if ec.codes_get(gid, "units") == "m" else 1.0
        return {p["id"]: ec.codes_grib_find_nearest(gid, p["lat"], p["lon"])[0].value * f for p in pts}
    finally:
        ec.codes_release(gid)


def ecmwf(modelo, run, pts):
    """Lluvia de cada bloque de 6 h (diferencia de acumulados). None si falta algún paso."""
    acum, prev = {}, {p["id"]: 0.0 for p in pts}
    for s in PASOS:
        r = x.rangos_ecmwf(modelo, run, s)
        if "tp" not in r:
            return None
        v = valores(x.get(*r["tp"]), pts)
        if v is None:
            return None
        acum[s] = {k: (max(0.0, v[k] - prev[k]), None) for k in v}
        prev = v
    return acum


def gfs(run, pts):
    base = f"{x.GFS}/gfs.{run:%Y%m%d}/{run:%H}/atmos/gfs.t{run:%H}z.pgrb2.0p25.f"
    out = {}
    for s in PASOS:
        idx = x.get(base + f"{s:03d}.idx")
        if not idx:
            return None
        L = [l.split(":") for l in idx.decode().splitlines() if l.strip()]
        mm = iso = None
        for i, l in enumerate(L):
            d = ":".join(l[3:6]); off = int(l[1]); fin = int(L[i + 1][1]) - 1 if i + 1 < len(L) else ""
            if d.startswith(f"APCP:surface:{s - 6}-{s} hour acc"):
                mm = valores(x.get(base + f"{s:03d}", (off, fin)), pts)
            elif d.startswith("HGT:0C isotherm:"):
                iso = valores(x.get(base + f"{s:03d}", (off, fin)), pts)
        if mm is None:
            return None
        out[s] = {k: (mm[k], iso[k] if iso else None) for k in mm}
    return out


def registradas():
    if not os.path.exists(CSV):
        return set()
    return {(r["modelo"], r["corrida_utc"]) for r in csv.DictReader(open(CSV, encoding="utf-8"))}


def agregar(filas):
    nuevo = not os.path.exists(CSV)
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(CAMPOS)
        w.writerows(filas)


def seguir():
    pts, hechas = puntos(), registradas()
    ahora = dt.datetime.now(UTC).replace(tzinfo=None)
    base = ahora.replace(minute=0, second=0, microsecond=0, hour=(ahora.hour // 6) * 6)
    candidatas = [base - dt.timedelta(hours=6 * k) for k in range(6)]          # últimas 30 h
    nuevas = 0
    for nombre, fn in (("GFS", lambda r: gfs(r, pts)), ("AIFS", lambda r: ecmwf("aifs-single", r, pts)), ("IFS", lambda r: ecmwf("ifs", r, pts))):
        for run in sorted(candidatas):
            clave = (nombre, f"{run:%Y-%m-%d %H:%M}")
            if clave in hechas:
                continue
            datos = fn(run)
            if not datos:
                print(f"{nombre} {run:%Y-%m-%d %H}Z: todavía no disponible o sin respuesta; se reintenta la próxima hora", flush=True)
                continue
            filas, reg = [], f"{dt.datetime.now(UTC):%Y-%m-%d %H:%M}"
            for s in PASOS:
                fin = (run.replace(tzinfo=UTC) + dt.timedelta(hours=s)).astimezone(CL); ini = fin - dt.timedelta(hours=6)
                for p in pts:
                    mm, iso = datos[s][p["id"]]
                    prob = nivel = ""
                    if "prop_hm23" in p:
                        pr = ind.probabilidad(mm, 2.0, p["prop_hm23"], p["dnbr"]); prob, nivel = round(pr, 3), ind.nivel(pr)
                    filas.append([nombre, clave[1], s, f"{ini:%Y-%m-%d %H:%M}", f"{fin:%Y-%m-%d %H:%M}", p["id"], p["nombre"],
                                  round(mm, 1), "" if iso is None else round(iso), prob, nivel, reg])
            agregar(filas); nuevas += 1
            print(f"{nombre} {run:%Y-%m-%d %H}Z: registrada", flush=True)
    print(f"corridas nuevas registradas: {nuevas}")
    return pts


def resumen_evento(evento, desde, hasta, pts):
    """LEEME del evento: para cada modelo y corrida, lluvia total en la ventana y bloque más lluvioso por punto."""
    import pandas as pd
    df = pd.read_csv(CSV)
    d0, d1 = pd.Timestamp(desde), pd.Timestamp(hasta)
    df["ini"] = pd.to_datetime(df.bloque_inicio_chile); df["fin"] = pd.to_datetime(df.bloque_fin_chile)
    v = df[(df.ini >= d0) & (df.fin <= d1)]
    ahora = dt.datetime.now(UTC).astimezone(CL)
    lin = [f"# Registro previo: {evento}", "",
           f"Ventana del evento: {desde} a {hasta} (hora de Chile). Resumen actualizado el {ahora:%d-%m-%Y %H:%M} (hora de Chile).",
           "Cada fila es una corrida de un modelo; las más nuevas, abajo. La fecha de cada registro está en la columna",
           "registrado_utc de hindcast/seguimiento/pronosticos.csv y en el historial de git.", ""]
    for p in pts:
        x_ = v[v.punto == p["id"]]
        if x_.empty:
            continue
        lin += [f"## {p['nombre']}", "", "| Modelo | Corrida (UTC) | Lluvia en la ventana | Bloque más lluvioso | Isoterma 0 °C |", "|---|---|---|---|---|"]
        for (m, c), g in x_.groupby(["modelo", "corrida_utc"], sort=False):
            g = g.sort_values("plazo_h")
            mx = g.loc[g.mm_6h.idxmax()]
            iso = g.isoterma0_m.dropna()
            lin.append(f"| {m} | {c} | {g.mm_6h.sum():.0f} mm | {mx.mm_6h:.1f} mm ({pd.Timestamp(mx.ini):%d %H}-{pd.Timestamp(mx.fin):%H} h) | "
                       + (f"{iso.min():.0f} a {iso.max():.0f} m" if len(iso) else "–") + " |")
        if "prop_hm23" in p:
            at = ind.lluvia_umbral(ind.UMBRALES[0], p["prop_hm23"], p["dnbr"]); av = ind.lluvia_umbral(ind.UMBRALES[1], p["prop_hm23"], p["dnbr"])
            lin += ["", f"Umbral del indicador: atención con unos {at:.0f} mm en 2 h; aviso de impacto con unos {av:.0f} mm en 2 h."]
        lin.append("")
    lin.append("Registro para verificación posterior. No es un aviso ni una alerta: las alertas oficiales son de la DMC y SENAPRED.")
    destino = os.path.join(RAIZ, "hindcast", "eventos", "prerregistro", evento)
    os.makedirs(destino, exist_ok=True)
    open(os.path.join(destino, "LEEME.md"), "w", encoding="utf-8").write("\n".join(lin) + "\n")
    print("\n".join(lin[:40]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--evento"); ap.add_argument("--desde"); ap.add_argument("--hasta")
    a = ap.parse_args()
    pts = seguir()
    if a.evento:
        resumen_evento(a.evento, a.desde, a.hasta, pts)
