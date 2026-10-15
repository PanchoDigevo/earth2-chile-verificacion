"""Pronósticos AIFS/IFS/GFS en las estaciones usando los conectores de Earth2Studio.
Reemplazo de verificacion/fetch_aifs.py: misma lista de estaciones, misma salida CSV.
Sin GPU. Uso: python earth2/fetch_e2s.py --modelo aifs --corrida 2026-10-14T00 --plazos 0,6,12,24
"""
import argparse, csv, datetime as dt, pathlib
import numpy as np, pandas as pd

MODELOS = {"aifs": ("AIFS_FX", {}), "ifs": ("IFS_FX", {}), "gfs": ("GFS_FX", {})}
VARS = ["t2m", "u10m", "v10m", "tp"]  # lexicón Earth2Studio; tp es acumulado desde la corrida

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="aifs", choices=MODELOS)
    ap.add_argument("--corrida", required=True, help="YYYY-MM-DDTHH (UTC)")
    ap.add_argument("--plazos", default="0,6,12,24")
    ap.add_argument("--estaciones", default="historico/estaciones.csv")
    ap.add_argument("--salida", default="verificacion/data/raw")
    a = ap.parse_args()
    from earth2studio import data as e2d
    cls, kw = MODELOS[a.modelo]
    src = getattr(e2d, cls)(**kw)
    corrida = dt.datetime.fromisoformat(a.corrida)
    plazos = [int(x) for x in a.plazos.split(",")]
    est = pd.read_csv(a.estaciones)
    filas = []
    for h in plazos:
        da = src(corrida, [np.timedelta64(h, "h")], VARS)  # xarray: (time, lead_time, variable, lat, lon)
        da = da.isel(time=0, lead_time=0)
        lon = ((est["lon"] + 360) % 360).values if float(da.lon.max()) > 180 else est["lon"].values
        pts = da.sel(lat=est["lat"].to_xarray(), lon=("index", lon) if False else est["lon"].to_xarray(), method="nearest")
        for i, r in est.iterrows():
            v = {var: float(pts.sel(variable=var).isel(index=i)) for var in VARS}
            filas.append({"modelo": a.modelo.upper(), "corrida": corrida.isoformat(), "lead_h": h, "icao": r["icao"],
                          "t2m_c": v["t2m"] - 273.15, "viento_ms": float(np.hypot(v["u10m"], v["v10m"])), "tp_mm": v["tp"] * 1000})
    out = pathlib.Path(a.salida); out.mkdir(parents=True, exist_ok=True)
    f = out / f"{a.modelo}_{corrida:%Y%m%dT%H}.csv"
    pd.DataFrame(filas).to_csv(f, index=False)
    print(f, len(filas))

if __name__ == "__main__":
    main()
