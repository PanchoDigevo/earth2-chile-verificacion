"""Pronósticos AIFS/IFS/GFS en las estaciones usando los conectores de Earth2Studio (sin GPU).
Reemplazo candidato de verificacion/fetch_aifs.py: misma lista de estaciones (historico/estaciones.csv).

Corrección de la selección por estación: la grilla de Earth2Studio va de 0 a 359,75° de longitud, así que la longitud
de cada estación se pasa a ese rango, y la selección es punto a punto (latitud y longitud emparejadas en una dimensión
"estacion"), no la combinación de todas las latitudes con todas las longitudes.

Uso: python earth2/fetch_e2s.py --modelo aifs --corrida 2026-10-14T00 --plazos 0,6,12,24"""
import argparse, datetime as dt, pathlib
import numpy as np, pandas as pd, xarray as xr

MODELOS = {"aifs": "AIFS_FX", "ifs": "IFS_FX", "gfs": "GFS_FX"}
VARS = ["t2m", "u10m", "v10m"]


def en_estaciones(da, est):
    """Valor del punto de grilla más cercano a cada estación (selección vectorizada punto a punto)."""
    lat = xr.DataArray(est["lat"].values, dims="estacion")
    lon360 = (est["lon"].values + 360.0) % 360.0
    lon = xr.DataArray(lon360 if float(da.lon.max()) > 180 else est["lon"].values, dims="estacion")
    return da.sel(lat=lat, lon=lon, method="nearest")


def extraer(modelo, corrida, plazos, est):
    from earth2studio import data as e2d
    # Tiempo total mayor y reintentos cortos: el bucket de ECMWF responde "503 Slow Down" y el cliente por defecto
    # espera 120 s por intento (hasta 500), lo que agota el límite de 600 s de Earth2Studio (FSTimeoutError).
    src = getattr(e2d, MODELOS[modelo])(cache=False, async_timeout=3600)
    if modelo in ("aifs", "ifs"):
        from ecmwf import opendata
        src.client = opendata.Client(source="aws", model="aifs-single" if modelo == "aifs" else "ifs",
                                     maximum_retries=8, retry_after=15, use_server_retry_after=False)
    da = src(corrida, [dt.timedelta(hours=h) for h in plazos], VARS).isel(time=0)
    pts = en_estaciones(da, est)
    filas = []
    for k, h in enumerate(plazos):
        for i, r in est.reset_index(drop=True).iterrows():
            v = {var: float(pts.isel(lead_time=k, estacion=i).sel(variable=var)) for var in VARS}
            filas.append({"modelo": modelo.upper(), "run": corrida, "lead_h": h, "icao": r["icao"],
                          "t_fc": v["t2m"] - 273.15, "w_fc": float(np.hypot(v["u10m"], v["v10m"]))})
    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="aifs", choices=MODELOS)
    ap.add_argument("--corrida", required=True, help="YYYY-MM-DDTHH (UTC)")
    ap.add_argument("--plazos", default="0,6,12,24")
    ap.add_argument("--estaciones", default="historico/estaciones.csv")
    ap.add_argument("--salida", default="earth2/data")
    a = ap.parse_args()
    df = extraer(a.modelo, dt.datetime.fromisoformat(a.corrida), [int(x) for x in a.plazos.split(",")], pd.read_csv(a.estaciones))
    out = pathlib.Path(a.salida); out.mkdir(parents=True, exist_ok=True)
    f = out / f"e2s_{a.modelo}_{a.corrida.replace(':', '')}.csv"
    df.to_csv(f, index=False)
    print(f, len(df))


if __name__ == "__main__":
    main()
