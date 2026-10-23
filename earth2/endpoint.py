"""Conector para un endpoint propio de Earth-2 (por ejemplo una función en NVIDIA Cloud Functions o un NIM).

Lo corre el workflow diario (verificacion.yml) desde la carpeta verificacion/, después de bajar AIFS, IFS y GFS.
Si no existe el secreto EARTH2_URL, termina sin hacer nada. Si existe, pide el pronóstico, lo lleva a los mismos
aeródromos que los otros modelos y escribe verificacion/data/puntos_<MODELO>_<corrida>.csv, que verify.py ya sabe leer:
desde ese momento el modelo se verifica en público igual que AIFS, IFS y GFS.

Configuración (GitHub → Settings → Secrets and variables → Actions):
  secreto  EARTH2_URL       dirección del endpoint
  secreto  EARTH2_API_KEY   clave (nunca en el código ni en el chat: el repo es público)
  variable EARTH2_MODELO    nombre corto que aparecerá en el sitio (por defecto "E2")

pedir_pronostico() sigue el contrato de la función de NVCF de Guillermo: se manda {"corrida": "YYYY-MM-DDTHH", "horas": N},
la primera respuesta es {"estado": "lanzada"} y se repite la llamada cada 20 s hasta recibir el netCDF (formato estándar
de Earth2Studio: t2m, u10m, v10m sobre lead_time, lat, lon). Guía completa: docs/guia_endpoint_earth2.md.

Prueba local sin endpoint, con un archivo ya descargado:
  python earth2/endpoint.py --archivo salida.nc --corrida 2026-10-20T00"""
import argparse, datetime as dt, io, os, sys, urllib.request
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTACIONES = os.path.join(AQUI, "..", "historico", "estaciones.csv")
SALIDA = os.path.join(AQUI, "..", "verificacion", "data")
PLAZOS = [0, 6, 12, 18, 24, 36, 48]


ESPERA_S = 20            # Guillermo: la corrida tarda ~60 s y el gateway de NVCF corta conexiones largas
TOPE_MIN = 15            # tope total de espera; el job de verificación tiene 30 min en total


def _llamar(url, clave, cuerpo=None, metodo="POST"):
    import json, urllib.error
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    h = {"Authorization": f"Bearer {clave}", "Accept": "application/x-netcdf, application/octet-stream, application/json"}
    if datos is not None:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=datos, headers=h, method=metodo), timeout=120) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:   # corte de red o del gateway: se reintenta
        return 0, {}, str(e).encode()


def _es_netcdf(b):
    return b[:4] in (b"\x89HDF", b"CDF\x01", b"CDF\x02")


def pedir_pronostico(url, clave, corrida, plazos):
    """Pide al endpoint el pronóstico que parte en `corrida` (datetime UTC) y devuelve un xarray.Dataset con t2m (K),
    u10m y v10m (m/s) sobre lead_time, lat y lon (la salida estándar de Earth2Studio).

    Cómo responde la función de Guillermo en NVCF: la corrida tarda ~60 s y el gateway corta las conexiones largas, así
    que la primera llamada la lanza y devuelve {"estado": "lanzada"}; se repite la MISMA llamada cada 20 s hasta que
    llega el netCDF. También se aceptan las respuestas propias de NVCF: 202 con NVCF-REQID (se consulta
    /v2/nvcf/pexec/status/<id>) y un resultado grande entregado como enlace (Location o "url" en el JSON)."""
    import json, time, xarray as xr
    cuerpo = {"corrida": corrida.strftime("%Y-%m-%dT%H"), "horas": max(plazos)}
    t0, intento, sondeo = time.time(), 0, None
    while time.time() - t0 < TOPE_MIN * 60:
        intento += 1
        st, h, b = _llamar(sondeo, clave, metodo="GET") if sondeo else _llamar(url, clave, cuerpo)
        h = {k.lower(): v for k, v in h.items()}
        if st == 200 and _es_netcdf(b):
            print(f"Earth-2: netCDF recibido en el intento {intento} ({len(b) / 1e6:.1f} MB, {time.time() - t0:.0f} s)")
            return xr.open_dataset(io.BytesIO(b)).load()
        enlace = h.get("location")
        info = {}
        if b[:1] == b"{":
            try:
                info = json.loads(b)
            except ValueError:
                info = {}
            enlace = enlace or info.get("url")
        if enlace and st in (200, 302, 303):
            with urllib.request.urlopen(enlace, timeout=300) as r:
                b = r.read()
            if _es_netcdf(b):
                return xr.open_dataset(io.BytesIO(b)).load()
        if info.get("estado") == "error":                       # la función corrió y falló: mostrar el detalle completo
            print("Earth-2: la función respondió error para la corrida", info.get("corrida"))
            print(info.get("detalle", ""))
            raise RuntimeError("Earth-2: la función de NVCF falló al correr el modelo (detalle arriba)")
        if st == 202 and h.get("nvcf-reqid"):
            base = url.split("/v2/nvcf/")[0] if "/v2/nvcf/" in url else "https://api.nvcf.nvidia.com"
            sondeo = f"{base}/v2/nvcf/pexec/status/{h['nvcf-reqid']}"
        elif st in (200, 202) and (info.get("estado") in ("lanzada", "corriendo", "en_curso") or st == 202):
            pass
        elif st in (0, 429, 500, 502, 503, 504):
            print(f"Earth-2: el endpoint respondió {st}; se reintenta")
        else:
            raise RuntimeError(f"Earth-2: respuesta inesperada {st}: {b[:200]!r}")
        print(f"Earth-2: intento {intento}, estado {info.get('estado') or st}; espero {ESPERA_S} s")
        time.sleep(ESPERA_S)
    raise TimeoutError(f"Earth-2: sin netCDF después de {TOPE_MIN} min")


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
