"""Verifica AIFS (0,25°) contra METAR de aeródromos chilenos: temperatura 2 m y viento 10 m por plazo.
Genera data/verif_puntos.csv, data/verif_resumen.csv y, vía render_site.py, ../site/index.html."""
import glob, os
import numpy as np, pandas as pd, xarray as xr

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
obs = pd.read_csv("data/metar_obs.csv", parse_dates=["time"])
obs["time"] = obs["time"].dt.tz_localize(None)
obs["wspd_ms"] = pd.to_numeric(obs["wspd_kt"], errors="coerce") * 0.514444
stations = obs.groupby("icao").agg(lat=("lat", "first"), lon=("lon", "first"), name=("name", "first"), elev=("elev", "first")).reset_index()

rows = []
for f in sorted(glob.glob("data/aifs_*.grib2")):
    try:
        ds2t = xr.open_dataset(f, engine="cfgrib", backend_kwargs={"filter_by_keys": {"shortName": "2t"}})
        ds10 = xr.open_dataset(f, engine="cfgrib", backend_kwargs={"filter_by_keys": {"shortName": "10u"}})
        dsv = xr.open_dataset(f, engine="cfgrib", backend_kwargs={"filter_by_keys": {"shortName": "10v"}})
    except Exception as e:
        print("no se pudo abrir", f, e); continue
    run = pd.Timestamp(ds2t.time.values)
    lons = ds2t.longitude.values
    for icao, lat, lon, name, elev in stations[["icao", "lat", "lon", "name", "elev"]].itertuples(index=False):
        lon360 = lon % 360 if lons.max() > 180 else lon
        t2 = ds2t.t2m.sel(latitude=lat, longitude=lon360, method="nearest") - 273.15
        u = ds10.u10.sel(latitude=lat, longitude=lon360, method="nearest")
        v = dsv.v10.sel(latitude=lat, longitude=lon360, method="nearest")
        for k, step in enumerate(ds2t.step.values):
            valid = run + pd.Timedelta(step)
            lead = int(pd.Timedelta(step).total_seconds() // 3600)
            o = obs[(obs.icao == icao) & ((obs.time - valid).abs() <= pd.Timedelta("31min"))]
            if o.empty:
                continue
            o = o.iloc[(o.time - valid).abs().argsort()].iloc[0]
            ft = float(t2.isel(step=k)); fw = float(np.hypot(u.isel(step=k), v.isel(step=k)))
            rows.append(dict(run=run, lead_h=lead, valid=valid, icao=icao, name=name, lat=lat, lon=lon, elev=elev,
                             t_fc=ft, t_obs=float(o.temp_c), t_err=ft - float(o.temp_c),
                             w_fc=fw, w_obs=float(o.wspd_ms), w_err=fw - float(o.wspd_ms)))
if not rows:
    print("sin pares pronóstico-observación todavía"); raise SystemExit(0)
pts = pd.DataFrame(rows)
# acumular histórico de pares (sin duplicar)
hist = "data/verif_puntos.csv"
if os.path.exists(hist):
    old = pd.read_csv(hist, parse_dates=["run", "valid"])
    pts = pd.concat([old, pts]).drop_duplicates(subset=["run", "lead_h", "icao"], keep="last")
pts.to_csv(hist, index=False)
mae = lambda e: e.abs().mean()
res = pts.groupby("lead_h").agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae), w_bias=("w_err", "mean"), w_mae=("w_err", mae)).reset_index()
res.to_csv("data/verif_resumen.csv", index=False)
bye = pts.groupby(["icao", "name", "elev"]).agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae), w_mae=("w_err", mae)).reset_index().sort_values("t_mae", ascending=False)
print(res.round(2).to_string(index=False)); print(); print(bye.round(2).to_string(index=False))

from render_site import render_site
render_site(pts)
