"""Tormentas en las próximas 72 horas por comuna, con los ingredientes de GFS (NOAA): inestabilidad, tapa, disparador y
cizalle. Lo llama verificacion.yml después de fetch_gfs.py, con la misma corrida.

Niveles, con cortes de uso común en la literatura (no ajustados a ningún evento chileno):
- 1 "tormentas posibles": CAPE ≥ 100 J/kg (la mayor entre la de superficie y la de la capa de 180 hPa), CIN ≥ −50 J/kg
  (sin tapa que las frene) y lluvia prevista de al menos 0,1 mm/h en el bloque, en el punto o en los vecinos a 25 km
  (algo que las dispare; la lluvia convectiva de GFS cae a menudo un poco corrida).
- 2 "tormentas fuertes posibles": además, CAPE ≥ 250 J/kg y cizalle de 35 nudos o más entre 10 m y 500 hPa (unos 5,5 km):
  el criterio de ambientes de poca inestabilidad y mucho cizalle de Sherburn y Parker (2014, Wea. Forecasting 29), donde
  ocurre buena parte de los tornados y rachas dañinas fuera de las Grandes Llanuras, y dentro del rango que usa el SPC.
A 25 km esto anticipa el ambiente, no la tormenta ni el tornado: dice dónde pueden formarse. Cuántas veces acierta se mide
contra los METAR que informan tormenta (hindcast/tormentas_gfs/).

Escribe data/tormentas_comunas.csv: id, valid, nivel, cape, cin, cizalle_kt, lluvia_mmh, ráfaga_kmh (solo filas con nivel ≥ 1
o ráfaga ≥ 60 km/h, para que el archivo sea chico).

Uso: python tormentas_gfs.py              -> la corrida del último data/gfs_*.grib2
     python tormentas_gfs.py 2026-10-26 12"""
import glob, math, os, sys, time, urllib.request
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import comunas_pron  # noqa: E402

BASE = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
SALIDA = os.path.join(AQUI, "data", "tormentas_comunas.csv")
PLAZOS = range(3, 73, 3)
CAMPOS = [("CAPE", "surface"), ("CAPE", "180-0 mb above ground"), ("CIN", "surface"), ("CIN", "180-0 mb above ground"),
          ("UGRD", "10 m above ground"), ("VGRD", "10 m above ground"), ("UGRD", "500 mb"), ("VGRD", "500 mb"),
          ("PRATE", "surface"), ("GUST", "surface")]
CAPE_1, CIN_1, LLUVIA_1 = 100.0, -50.0, 0.1 / 3600     # J/kg, J/kg, kg/m²/s (= mm/s)
CAPE_2, CIZALLE_2 = 250.0, 35.0                         # J/kg, nudos


def leer(url, headers=None, intentos=4):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=90) as r:
                return r.read()
        except Exception as e:
            if getattr(e, "code", None) == 404:
                return None
            time.sleep(10)
    return None


def mensajes(run, f):
    """{(var, nivel): bytes} de un plazo; para PRATE, el promedio del bloque (no el instantáneo)."""
    base = f"{BASE}/gfs.{run:%Y%m%d}/{run:%H}/atmos/gfs.t{run:%H}z.pgrb2.0p25.f{f:03d}"
    idx = leer(base + ".idx")
    if not idx:
        return None
    L = [l.split(":") for l in idx.decode().splitlines() if l.strip()]
    out = {}
    for i, c in enumerate(L[:-1]):
        k = (c[3], c[4])
        if k not in CAMPOS or k in out:
            continue
        if c[3] == "PRATE" and "ave" not in c[5]:
            continue
        b = leer(base, {"Range": f"bytes={c[1]}-{int(L[i + 1][1]) - 1}"})
        if b:
            out[k] = b
    return out


def corrida():
    if len(sys.argv) >= 3:
        return pd.Timestamp(f"{sys.argv[1]} {int(sys.argv[2]):02d}:00")
    f = sorted(glob.glob(os.path.join(AQUI, "data", "gfs_*.grib2")) + glob.glob("data/gfs_*.grib2"))
    if not f:
        raise SystemExit("tormentas: no hay corrida de GFS descargada")
    a, h = os.path.basename(f[-1])[4:-6].split("_")
    return pd.Timestamp(f"{a[:4]}-{a[4:6]}-{a[6:]} {h}:00")


def calcular(run, p, plazos=PLAZOS):
    """Lista de DataFrames (uno por plazo) con el nivel e ingredientes en los puntos p (id, lat, lon)."""
    import eccodes as ec
    idx = vecinos = None; filas = []
    for f in plazos:
        m = mensajes(run, f)
        if not m or len(m) < len(CAMPOS) - 1:
            print(f"tormentas: GFS {run:%Y-%m-%d %HZ} sin el plazo {f} h; se corta ahí"); break
        v = {}
        for k, b in m.items():
            g = ec.codes_new_from_message(b)
            try:
                if idx is None:
                    idx = comunas_pron._indices(g, p.lat.values, p.lon.values)
                    ni, nj = ec.codes_get(g, "Ni"), ec.codes_get(g, "Nj")
                    i, j = idx // ni, idx % ni      # vecinos a una celda (unos 25 km), para la lluvia
                    vecinos = np.stack([((i + di) % nj) * ni + (j + dj) % ni for di in (-1, 0, 1) for dj in (-1, 0, 1)])
                todo = ec.codes_get_values(g)
                v[k] = todo[vecinos].max(axis=0) if k[0] == "PRATE" else todo[idx]
            finally:
                ec.codes_release(g)
        cape = np.fmax(v[("CAPE", "surface")], v[("CAPE", "180-0 mb above ground")])
        cin = np.fmax(v[("CIN", "surface")], v[("CIN", "180-0 mb above ground")])
        ciz = np.hypot(v[("UGRD", "500 mb")] - v[("UGRD", "10 m above ground")], v[("VGRD", "500 mb")] - v[("VGRD", "10 m above ground")]) * 1.944
        ll = v.get(("PRATE", "surface"), np.zeros(len(p)))
        racha = v.get(("GUST", "surface"), np.zeros(len(p))) * 3.6
        n1 = (cape >= CAPE_1) & (cin >= CIN_1) & (ll >= LLUVIA_1)
        nivel = np.where(n1 & (cape >= CAPE_2) & (ciz >= CIZALLE_2), 2, np.where(n1, 1, 0))
        filas.append(pd.DataFrame({"run": run, "lead_h": f, "valid": run + pd.Timedelta(hours=f), "id": p.id.values, "nivel": nivel,
                                   "cape": np.round(cape), "cin": np.round(cin), "cizalle_kt": np.round(ciz), "lluvia_mmh": np.round(ll * 3600, 1),
                                   "racha_kmh": np.round(racha)}))
    return filas


def main():
    run = corrida(); p = comunas_pron.puntos()
    filas = calcular(run, p)
    if not filas:
        return
    d = pd.concat(filas, ignore_index=True)
    d = d[(d.nivel >= 1) | (d.racha_kmh >= 60)]
    d.to_csv(SALIDA, index=False, date_format="%Y-%m-%d %H:%M:%S")
    com = d[d.id.str.startswith("Q")]
    print(f"tormentas: GFS {run:%Y-%m-%d %HZ} hasta {filas[-1].lead_h.iloc[0]} h; comunas con tormentas posibles: {com[com.nivel >= 1].id.nunique()},"
          f" fuertes posibles: {com[com.nivel == 2].id.nunique()}")


if __name__ == "__main__":
    main()
