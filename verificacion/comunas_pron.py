"""Pronóstico en el centro de cada comuna de Chile (verificacion/comunas.csv, 352 comunas desde Wikidata) y en las estaciones
de la DMC (estaciones/catalogo.csv), leído de los mismos GRIB globales que ya se bajan para los aeródromos.

Lo llama verify.py por cada GRIB. Escribe data/pronostico_comunas.csv (modelo, run, lead_h, valid, id, t_fc, w_fc, tp_fc) con
las dos últimas corridas de cada modelo: es lo que necesita la pestaña Pronóstico. Las comunas llevan id "Q…" (Wikidata) y las
estaciones de la DMC, "wmo…". Las lecturas son del punto de grilla más cercano (unos 25 km): la comuna recibe el valor del
cuadrado que la contiene, sin corrección por altura."""
import os
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "data", "pronostico_comunas.csv")
_puntos = None


def puntos():
    """DataFrame con id, nombre, lat, lon de comunas y estaciones DMC."""
    global _puntos
    if _puntos is None:
        c = pd.read_csv(os.path.join(AQUI, "comunas.csv"))[["id", "nombre", "lat", "lon"]]
        try:
            e = pd.read_csv(os.path.join(AQUI, "..", "estaciones", "catalogo.csv")).dropna(subset=["lat", "lon", "wmo"])
            e = e[e.red == "DMC"].assign(id=lambda d: "wmo" + d.wmo.astype(int).astype(str))[["id", "nombre", "lat", "lon"]]
        except Exception:
            e = pd.DataFrame(columns=["id", "nombre", "lat", "lon"])
        _puntos = pd.concat([c, e], ignore_index=True)
    return _puntos


def _indices(gid, lat, lon):
    """Índice del punto de grilla más cercano a cada (lat, lon) en el arreglo de valores del mensaje GRIB."""
    import eccodes as ec
    glat = ec.codes_get_double_array(gid, "latitudes"); glon = ec.codes_get_double_array(gid, "longitudes")
    lon = np.where(glon.max() > 180, lon % 360, lon)
    out = np.empty(len(lat), dtype=int)
    for i, (la, lo) in enumerate(zip(lat, lon)):
        d = (glat - la) ** 2 + ((glon - lo + 180) % 360 - 180) ** 2 * np.cos(np.radians(la)) ** 2
        out[i] = int(np.argmin(d))
    return out


def leer_grib(f):
    """{(shortName, lead_h): valores en los puntos} para 2t, 10u, 10v, tp (mm, el acumulado mayor en cada plazo) y tcc
    (nubosidad total en %, solo la instantánea; AIFS e IFS la dan de 0 a 1 o en %, GFS en %)."""
    import eccodes as ec
    p = puntos(); idx = None; out = {}; run = None
    with open(f, "rb") as fh:
        while True:
            gid = ec.codes_grib_new_from_file(fh)
            if gid is None:
                break
            try:
                sn = ec.codes_get(gid, "shortName")
                if sn not in ("2t", "10u", "10v", "tp", "tcc"):
                    continue
                if sn == "tcc" and ec.codes_get(gid, "stepType") != "instant":
                    continue
                if idx is None:
                    idx = _indices(gid, p.lat.values, p.lon.values)
                    run = pd.Timestamp(f"{ec.codes_get(gid, 'dataDate')} {int(ec.codes_get(gid, 'dataTime')) // 100:02d}:00")
                lead = int(ec.codes_get(gid, "endStep"))
                v = ec.codes_get_values(gid)[idx]
                if sn == "tp":
                    v = v * (1000.0 if ec.codes_get(gid, "units") == "m" else 1.0)
                    out[(sn, lead)] = np.maximum(out.get((sn, lead), 0.0), v)
                elif sn == "tcc":
                    out[(sn, lead)] = np.clip(v * (100.0 if np.nanmax(v) <= 1.0001 else 1.0), 0, 100)
                else:
                    out[(sn, lead)] = v
            finally:
                ec.codes_release(gid)
    return run, out


def extraer(f, modelo):
    run, v = leer_grib(f)
    if run is None:
        return pd.DataFrame()
    p = puntos(); filas = []
    for lead in sorted({l for s, l in v if s == "2t"}):
        t = v[("2t", lead)] - 273.15
        w = np.hypot(v.get(("10u", lead), np.nan), v.get(("10v", lead), np.nan))
        tp = v.get(("tp", lead), np.full(len(p), 0.0 if lead == 0 else np.nan))
        nub = v.get(("tcc", lead), np.full(len(p), np.nan))
        filas.append(pd.DataFrame({"modelo": modelo, "run": run, "lead_h": lead, "valid": run + pd.Timedelta(hours=lead),
                                   "id": p.id.values, "t_fc": np.round(t, 2), "w_fc": np.round(w, 2), "tp_fc": np.round(tp, 2),
                                   "nub_fc": np.round(nub, 0)}))
    return pd.concat(filas, ignore_index=True)


def guardar(nuevas, corridas_por_modelo=2):
    """Suma las filas nuevas y conserva las últimas corridas de cada modelo."""
    nuevas = [d for d in nuevas if d is not None and not d.empty]
    partes = []
    if os.path.exists(SALIDA):
        old = pd.read_csv(SALIDA)
        for c in ("run", "valid"):
            old[c] = pd.to_datetime(old[c], format="mixed")
        partes.append(old)
    partes += nuevas
    if not partes:
        return 0
    d = pd.concat(partes, ignore_index=True).drop_duplicates(subset=["modelo", "run", "lead_h", "id"], keep="last")
    ult = d.groupby("modelo").run.apply(lambda s: sorted(s.unique())[-corridas_por_modelo:])
    d = d[[r in set(ult[m]) for m, r in zip(d.modelo, d.run)]].sort_values(["modelo", "run", "lead_h", "id"])
    d.to_csv(SALIDA, index=False, date_format="%Y-%m-%d %H:%M:%S")
    return len(d)
