"""Conector para un endpoint propio de Earth-2 (por ejemplo una función en NVIDIA Cloud Functions o un NIM).

Lo corre el workflow diario (verificacion.yml) desde la carpeta verificacion/, después de bajar AIFS, IFS y GFS.
Si no existe el secreto EARTH2_URL, termina sin hacer nada. Si existe, pide el pronóstico, lo lleva a los mismos
aeródromos que los otros modelos y escribe verificacion/data/puntos_<MODELO>_<corrida>.csv, que verify.py ya sabe leer:
desde ese momento el modelo se verifica en público igual que AIFS, IFS y GFS.

Configuración (GitHub → Settings → Secrets and variables → Actions):
  secreto  EARTH2_URL       dirección del endpoint
  secreto  EARTH2_API_KEY   clave (nunca en el código ni en el chat: el repo es público)
  variable EARTH2_MODELO    nombre corto que aparecerá en el sitio (por defecto "E2")

Lo único que falta escribir es pedir_pronostico(): depende de qué devuelve el endpoint. Lo más simple es que devuelva
un archivo netCDF o Zarr con el formato estándar de Earth2Studio (variables t2m, u10m, v10m; dimensiones lead_time,
lat, lon). Con eso, el resto de este archivo ya funciona. Guía completa: docs/guia_endpoint_earth2.md.

Prueba local sin endpoint, con un archivo ya descargado:
  python earth2/endpoint.py --archivo salida.nc --corrida 2026-10-20T00"""
import argparse, datetime as dt, io, os, sys, urllib.request
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTACIONES = os.path.join(AQUI, "..", "historico", "estaciones.csv")
SALIDA = os.path.join(AQUI, "..", "verificacion", "data")
PLAZOS = [0, 6, 12, 18, 24, 36, 48]


def pedir_pronostico(url, clave, corrida, plazos):
    """Pide al endpoint el pronóstico que parte en `corrida` (datetime UTC) para los `plazos` en horas.

    Debe devolver un xarray.Dataset con t2m (K), u10m y v10m (m/s) y dimensiones lead_time (timedelta), lat y lon
    (grados; lon de 0 a 360 o de −180 a 180). Esa es la salida estándar de Earth2Studio.

    POR ESCRIBIR según la documentación del endpoint (qué condición inicial recibe, en qué formato responde).
    Un ejemplo típico de llamada HTTP:
        req = urllib.request.Request(url, data=json.dumps({...}).encode(), headers={"Authorization": f"Bearer {clave}"})
        datos = urllib.request.urlopen(req, timeout=900).read()
        return xarray.open_dataset(io.BytesIO(datos))
    """
    raise NotImplementedError("falta adaptar pedir_pronostico() al endpoint: ver docs/guia_endpoint_earth2.md")


def en_estaciones(ds, corrida, modelo, est):
    """Valor del punto de grilla más cercano a cada aeródromo, para cada plazo (selección punto a punto).
    Un aeródromo a más de medio grado de la grilla (fuera del recorte) se omite: el más cercano sería otro lugar."""
    import xarray as xr
    lon_e = (est.lon.values + 360.0) % 360.0 if float(np.nanmax(ds.lon.values)) > 180 else est.lon.values
    dentro = [float(np.abs(ds.lat.values - la).min()) <= 0.5 and float(np.abs(ds.lon.values - lo).min()) <= 0.5 for la, lo in zip(est.lat.values, lon_e)]
    if not all(dentro):
        print("Fuera del recorte, se omiten:", ", ".join(est.icao[[not x for x in dentro]]))
        est = est[dentro].reset_index(drop=True)
    lat = xr.DataArray(est.lat.values, dims="estacion")
    lon_ds = ds.lon.values
    lon = xr.DataArray((est.lon.values + 360.0) % 360.0 if float(np.nanmax(lon_ds)) > 180 else est.lon.values, dims="estacion")
    p = ds[["t2m", "u10m", "v10m"]].sel(lat=lat, lon=lon, method="nearest")
    if "time" in p.dims:
        p = p.isel(time=0)
    filas = []
    for lt in np.atleast_1d(p.lead_time.values):
        h = int(pd.Timedelta(lt).total_seconds() // 3600)
        x = p.sel(lead_time=lt)
        for i, icao in enumerate(est.icao):
            t, u, v = (float(x[k].isel(estacion=i)) for k in ("t2m", "u10m", "v10m"))
            filas.append({"modelo": modelo, "run": corrida.strftime("%Y-%m-%d %H:%M:%S"), "lead_h": h, "icao": icao,
                          "t_fc": round(t - 273.15 if t > 150 else t, 2), "w_fc": round(float(np.hypot(u, v)), 2)})
    return pd.DataFrame(filas)


def ultima_corrida(ahora=None):
    """La corrida de 00, 06, 12 o 18 UTC más reciente con al menos 6 horas de antigüedad."""
    ahora = ahora or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    t = ahora - dt.timedelta(hours=6)
    return t.replace(minute=0, second=0, microsecond=0, hour=(t.hour // 6) * 6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archivo", help="netCDF o Zarr ya descargado, para probar sin endpoint")
    ap.add_argument("--corrida", help="YYYY-MM-DDTHH (UTC); por defecto, la última corrida con 6 h de antigüedad")
    a = ap.parse_args()
    modelo = (os.environ.get("EARTH2_MODELO") or "E2").strip()
    corrida = dt.datetime.strptime(a.corrida, "%Y-%m-%dT%H") if a.corrida else ultima_corrida()
    if a.archivo:
        import xarray as xr
        ds = xr.open_zarr(a.archivo) if a.archivo.endswith(".zarr") else xr.open_dataset(a.archivo)
    else:
        url, clave = os.environ.get("EARTH2_URL", "").strip(), os.environ.get("EARTH2_API_KEY", "").strip()
        if not url:
            print("Earth-2: sin endpoint configurado (secreto EARTH2_URL vacío); no se hace nada.")
            return 0
        ds = pedir_pronostico(url, clave, corrida, PLAZOS)
    est = pd.read_csv(ESTACIONES)
    df = en_estaciones(ds, corrida, modelo, est)
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, f"puntos_{modelo}_{corrida:%Y%m%d_%H}.csv")
    df.to_csv(ruta, index=False)
    print(f"Earth-2 ({modelo}): corrida {corrida:%Y-%m-%d %H}Z, {len(df)} valores en {df.icao.nunique()} aeródromos -> {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
