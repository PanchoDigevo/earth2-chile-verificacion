"""Verifica tres modelos globales (0,25°) contra METAR de aeródromos chilenos: temperatura 2 m y viento 10 m por plazo.
  AIFS  ECMWF, inteligencia artificial      data/aifs_*.grib2
  IFS   ECMWF, modelo físico                 data/ifs_*.grib2
  GFS   NOAA, modelo físico                  data/gfs_*.grib2

Flujo:
 1. De cada GRIB se extrae el valor del punto de grilla más cercano a cada aeródromo y se guarda en
    data/pronostico_puntos.csv (una fila por modelo, corrida, plazo y estación). Así los plazos largos
    se emparejan en corridas posteriores, cuando ya existe la observación, aunque el GRIB ya no esté.
 2. Cada pronóstico guardado se empareja con la observación METAR más cercana (±31 min).
 3. Los pares se acumulan en data/verif_puntos.csv (columna "modelo"; el histórico sin columna es AIFS),
    se resume en data/verif_resumen.csv y render_site.py genera ../site/index.html."""
import glob, os
import numpy as np, pandas as pd, xarray as xr

MODELOS = {"aifs": "AIFS", "ifs": "IFS", "gfs": "GFS"}
PRON = "data/pronostico_puntos.csv"
HIST = "data/verif_puntos.csv"
CLAVE = ["modelo", "run", "lead_h", "icao"]
DIAS_PRON = 4          # los pronósticos cuya hora válida sea más antigua ya no recibirán observaciones nuevas

obs = pd.read_csv("data/metar_obs.csv", parse_dates=["time"])
obs["time"] = obs["time"].dt.tz_localize(None)
obs["wspd_ms"] = pd.to_numeric(obs["wspd_kt"], errors="coerce") * 0.514444
obs = obs.dropna(subset=["temp_c"]).sort_values("time")
stations = obs.groupby("icao").agg(lat=("lat", "first"), lon=("lon", "first"), name=("name", "first"), elev=("elev", "first")).reset_index()


def abrir(f, short_name):
    return xr.open_dataset(f, engine="cfgrib", backend_kwargs={"filter_by_keys": {"shortName": short_name}, "indexpath": ""})


def puntos_de(f, modelo):
    """Valores de 2t y viento 10 m en el punto de grilla más cercano a cada aeródromo, para cada plazo del GRIB."""
    ds2t, ds10u, ds10v = abrir(f, "2t"), abrir(f, "10u"), abrir(f, "10v")
    t2m, u10, v10 = ds2t["t2m"], ds10u["u10"], ds10v["v10"]
    if "step" not in t2m.dims:               # un solo plazo: step es escalar
        t2m, u10, v10 = (a.expand_dims("step") for a in (t2m, u10, v10))
    run = pd.Timestamp(ds2t.time.values)
    lons = ds2t.longitude.values
    lon_360 = lons.max() > 180
    filas = []
    for icao, lat, lon, name, elev in stations[["icao", "lat", "lon", "name", "elev"]].itertuples(index=False):
        lon_m = lon % 360 if lon_360 else lon
        t = t2m.sel(latitude=lat, longitude=lon_m, method="nearest").values - 273.15
        u = u10.sel(latitude=lat, longitude=lon_m, method="nearest").values
        v = v10.sel(latitude=lat, longitude=lon_m, method="nearest").values
        w = np.hypot(u, v)
        for k, step in enumerate(np.atleast_1d(t2m.step.values)):
            lead = int(pd.Timedelta(step).total_seconds() // 3600)
            filas.append(dict(modelo=modelo, run=run, lead_h=lead, valid=run + pd.Timedelta(step), icao=icao, name=name,
                              lat=lat, lon=lon, elev=elev, t_fc=float(t[k]), w_fc=float(w[k])))
    return filas


# 1. pronósticos en las estaciones ---------------------------------------------------------------
nuevos = []
for f in sorted(glob.glob("data/*_*.grib2")):
    pref = os.path.basename(f).split("_")[0]
    if pref not in MODELOS:
        continue
    try:
        filas = puntos_de(f, MODELOS[pref])
    except Exception as e:
        print("no se pudo leer", f, "->", type(e).__name__, e); continue
    print(f"{MODELOS[pref]}: {f} -> {len(filas)} valores en estaciones")
    nuevos += filas
pron = pd.DataFrame(nuevos, columns=["modelo", "run", "lead_h", "valid", "icao", "name", "lat", "lon", "elev", "t_fc", "w_fc"])
if os.path.exists(PRON):
    pron = pd.concat([pd.read_csv(PRON, parse_dates=["run", "valid"]), pron])
pron = pron.drop_duplicates(subset=CLAVE, keep="last")
ahora = pd.Timestamp.now("UTC").tz_localize(None)
pron = pron[pron.valid >= ahora - pd.Timedelta(days=DIAS_PRON)].sort_values(["run", "modelo", "lead_h", "icao"])
pron.to_csv(PRON, index=False)
print(f"pronósticos guardados: {len(pron)} filas ({pron.modelo.nunique()} modelos, {pron.run.nunique()} corridas)")

# 2. emparejar con la observación más cercana (±31 min) ------------------------------------------
# Misma resolución temporal en ambas claves (pandas >= 3 infiere microsegundos al leer CSV; merge_asof exige igualdad).
cand = pron[pron.valid <= obs.time.max()].copy()
cand["valid"] = cand["valid"].astype("datetime64[ns]")
cand = cand.sort_values("valid")
o = obs[["icao", "time", "temp_c", "wspd_ms"]].rename(columns={"time": "t_obs_time"})
o["t_obs_time"] = o["t_obs_time"].astype("datetime64[ns]")
o = o.sort_values("t_obs_time")
pares = pd.merge_asof(cand, o, left_on="valid", right_on="t_obs_time", by="icao",
                      tolerance=pd.Timedelta("31min"), direction="nearest").dropna(subset=["temp_c"])
pares = pares.rename(columns={"temp_c": "t_obs", "wspd_ms": "w_obs"}).drop(columns=["t_obs_time"])
pares["t_err"] = pares.t_fc - pares.t_obs
pares["w_err"] = pares.w_fc - pares.w_obs
print(f"pares nuevos o actualizados: {len(pares)}")

# 3. acumular histórico (sin duplicar; el histórico anterior a la columna "modelo" es AIFS) ------
if os.path.exists(HIST):
    old = pd.read_csv(HIST, parse_dates=["run", "valid"])
    if "modelo" not in old.columns:
        old.insert(0, "modelo", "AIFS")
    old["modelo"] = old["modelo"].fillna("AIFS")
    pares = pd.concat([old, pares])
pts = pares.drop_duplicates(subset=CLAVE, keep="last")
if pts.empty:
    print("sin pares pronóstico-observación todavía"); raise SystemExit(0)
cols = ["modelo", "run", "lead_h", "valid", "icao", "name", "lat", "lon", "elev", "t_fc", "t_obs", "t_err", "w_fc", "w_obs", "w_err"]
pts = pts[cols].sort_values(["run", "modelo", "lead_h", "icao"])
pts.to_csv(HIST, index=False)

mae = lambda e: e.abs().mean()
res = (pts.groupby(["modelo", "lead_h"]).agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae),
                                             w_bias=("w_err", "mean"), w_mae=("w_err", mae)).reset_index())
res.to_csv("data/verif_resumen.csv", index=False)
bye = (pts.groupby(["modelo", "icao", "name", "elev"], dropna=False).agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae), w_mae=("w_err", mae))
       .reset_index().sort_values(["modelo", "t_mae"], ascending=[True, False]))
print(res.round(2).to_string(index=False)); print(); print(bye.round(2).to_string(index=False))

from render_site import render_site
render_site(pts)
