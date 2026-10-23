"""Dataset de entrenamiento de CorrDiff-Chile (tarea 6): pares ERA5 25 km → SAAG-WRF 4 km sobre Chile, en el formato Zarr
que lee el cargador "cwb" del ejemplo corrdiff de PhysicsNeMo v1.3.0 (datasets/cwb.py, clase _ZarrDataset).

Fuentes (abiertas, sin clave):
  - Objetivo 4 km: SAAG-WRF de NCAR (RDA d616000), un archivo HDF5 de ~736 MB por hora para toda Sudamérica, leído por
    HTTPS vía OSDF. Solo se bajan los trozos de las variables y de la caja de Chile: ~27 MB por hora para 8 variables.
    La copia en AWS (s3://saag-wrf) que nombra el registro de AWS no existe.
  - Entrada 25 km: ERA5 de Google (ARCO, Zarr público). Solo variables de superficie: un trozo de superficie pesa ~2-3 MB
    por hora, mientras que uno de altura trae los 37 niveles juntos (~80 MB). Además son las que entregan AIFS y FCN3,
    los modelos que alimentarán a CorrDiff-Chile al pronosticar (t2m, u10m, v10m, u100m, v100m, msl; tcwv en FCN3 y
    tcw, casi lo mismo, en AIFS).
  - Fijas: relieve y máscara tierra-mar de SAAG a 4 km, como canales extra de entrada.

Grilla: la de SAAG (Lambert conforme, 4 km), recortada en filas 27-1146 y columnas 267-618: 1.120 × 352 puntos, múltiplos
de 32 como pide la red, de Arica (18,4° S) al Cabo de Hornos (56° S). La base antártica queda fuera de SAAG.
ERA5 se interpola bilinealmente a esa grilla.

Formato (lo que lee _ZarrDataset): cwb (time, cwb_channel, south_north, west_east) objetivo; era5 (time, era5_channel, ...)
entrada; cwb_center/scale y era5_center/scale (media y desviación por canal); cwb_variable/era5_variable (nombres);
cwb_pressure/era5_pressure (NaN = superficie); cwb_valid (time) y era5_valid (time, era5_channel); time con unidades;
XLAT y XLONG. Para el entrenamiento usar ds_factor=1 (si no, el cargador degrada el objetivo).

Uso (en una instancia de nube o nodos CPU del POD; nunca en el Mac):
  python entrenamiento/preparar_dataset.py --desde 2012-01-01T00 --hasta 2021-12-31T22 --cada 2 --salida /datos/corrdiff_chile.zarr --procesos 32
Muestra (la corre .github/workflows/dataset-muestra.yml): --desde 2018-01-01T00 --hasta 2018-01-01T22 --cada 2"""
import argparse, datetime as dt, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

SAAG = "https://osdf-director.osg-htc.org/ncar/rda/d616000"
ARCO = "https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
F0, C0, ALTO, ANCHO = 27, 267, 1120, 352
# (variable de SAAG, nombre del canal); PREC_ACC_NC es la lluvia de la última hora (prec_acc_dt = 60 min)
SALIDAS = [("T2", "temperature_2m"), ("U10", "eastward_wind_10m"), ("V10", "northward_wind_10m"),
           ("WSPD10MAX", "max_wind_speed_10m"), ("PREC_ACC_NC", "precipitation_1h"), ("SNOW_ACC_NC", "snowfall_1h"),
           ("Q2", "specific_humidity_2m"), ("SWDOWN", "shortwave_down")]
ENTRADAS = [("2m_temperature", "t2m"), ("10m_u_component_of_wind", "u10m"), ("10m_v_component_of_wind", "v10m"),
            ("100m_u_component_of_wind", "u100m"), ("100m_v_component_of_wind", "v100m"),
            ("mean_sea_level_pressure", "msl"), ("total_column_water_vapour", "tcwv")]
FIJAS = [("HGT", "terrain_height"), ("LANDMASK", "land_mask")]
_era5 = None


def h5_http(url):
    import fsspec, h5py
    return h5py.File(fsspec.filesystem("https", block_size=4 * 2**20).open(url, "rb", cache_type="blockcache"), "r")


def recorte(ds):
    v = ds[...]
    v = v[0] if v.ndim == 3 else v
    return np.asarray(v[F0:F0 + ALTO, C0:C0 + ANCHO], dtype=np.float32)


def constantes():
    h = h5_http(f"{SAAG}/INVARIANT/wrfconstants_SAAG.nc")
    return recorte(h["XLAT"]), recorte(h["XLONG"]), np.stack([recorte(h[k]) for k, _ in FIJAS])


def era5():
    global _era5
    if _era5 is None:
        import fsspec, xarray as xr
        _era5 = xr.open_zarr(fsspec.get_mapper(ARCO), consolidated=True, chunks=None)
    return _era5


def interpolar(campo, lat_g, lon_g, xlat, xlon):
    from scipy.interpolate import RegularGridInterpolator
    orden = np.argsort(lat_g)
    f = RegularGridInterpolator((lat_g[orden], lon_g), campo[orden], bounds_error=False, fill_value=np.nan)
    return f(np.stack([xlat.ravel(), (xlon.ravel() + 360) % 360], -1)).reshape(xlat.shape).astype(np.float32)


def una_hora(args):
    """Lee SAAG y ERA5 de una hora. Devuelve (objetivo, entrada, objetivo_válido, entrada_válida por canal, MB de SAAG)."""
    t, xlat, xlon = args
    obj = np.zeros((len(SALIDAS), ALTO, ANCHO), np.float32); ok_obj = True
    ent = np.zeros((len(ENTRADAS), ALTO, ANCHO), np.float32); ok_ent = np.ones(len(ENTRADAS), bool)
    for intento in range(3):
        try:
            h = h5_http(f"{SAAG}/hist2D/{t:%Y%m}/wrf2d_d01_{t:%Y-%m-%d_%H}0000.nc")
            for i, (k, _) in enumerate(SALIDAS):
                obj[i] = recorte(h[k])
            ok_obj = True; break
        except Exception as e:
            ok_obj = False; err = e; time.sleep(5 * (intento + 1))
    if ok_obj and not np.isfinite(obj).all():
        ok_obj = False; print(f"SAAG {t:%Y-%m-%d %H}: {int((~np.isfinite(obj)).sum())} puntos sin valor", flush=True)
    if not ok_obj and "err" in locals():
        print(f"SAAG {t:%Y-%m-%d %H}: {type(err).__name__} {err}", flush=True)
    e5 = era5()
    caja = dict(latitude=slice(0, -70), longitude=slice(260, 320))      # holgada: el trozo de ERA5 es global de todos modos
    for i, (k, _) in enumerate(ENTRADAS):
        try:
            da = e5[k].sel(time=np.datetime64(t)).sel(**caja)
            ent[i] = interpolar(da.values, da.latitude.values, da.longitude.values, xlat, xlon)
            ok_ent[i] = np.isfinite(ent[i]).all()
            if not ok_ent[i]:
                print(f"ERA5 {k} {t:%Y-%m-%d %H}: {int((~np.isfinite(ent[i])).sum())} puntos sin valor", flush=True)
        except Exception as e:
            ok_ent[i] = False; print(f"ERA5 {k} {t:%Y-%m-%d %H}: {type(e).__name__} {e}", flush=True)
    return obj, ent, ok_obj, ok_ent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", required=True); ap.add_argument("--hasta", required=True)
    ap.add_argument("--cada", type=int, default=2, help="horas entre muestras")
    ap.add_argument("--salida", required=True); ap.add_argument("--procesos", type=int, default=8)
    ap.add_argument("--bloque", type=int, default=48, help="muestras por escritura")
    a = ap.parse_args()
    import xarray as xr, zarr
    t0 = dt.datetime.strptime(a.desde, "%Y-%m-%dT%H"); t1 = dt.datetime.strptime(a.hasta, "%Y-%m-%dT%H")
    horas = [t0 + dt.timedelta(hours=h) for h in range(0, int((t1 - t0).total_seconds() // 3600) + 1, a.cada)]
    print(f"{len(horas)} muestras de {t0} a {t1}, cada {a.cada} h -> {a.salida}", flush=True)
    xlat, xlon, fijas = constantes()
    n_ent = len(ENTRADAS) + len(FIJAS)
    suma_o = np.zeros(len(SALIDAS)); suma2_o = np.zeros(len(SALIDAS)); n_o = 0
    suma_e = np.zeros(n_ent); suma2_e = np.zeros(n_ent); n_e = 0
    inicio, primero = time.time(), True
    with ProcessPoolExecutor(a.procesos) as pool:
        for b in range(0, len(horas), a.bloque):
            tb = horas[b:b + a.bloque]
            res = list(pool.map(una_hora, [(t, xlat, xlon) for t in tb]))
            obj = np.stack([r[0] for r in res]); ok_o = np.array([r[2] for r in res])
            ent = np.concatenate([np.stack([r[1] for r in res]), np.broadcast_to(fijas, (len(tb),) + fijas.shape)], axis=1)
            ok_e = np.concatenate([np.stack([r[3] for r in res]), np.ones((len(tb), len(FIJAS)), bool)], axis=1)
            buenos = ok_o & ok_e.all(1)
            if buenos.any():
                x = obj[buenos].astype(np.float64); suma_o += x.sum((0, 2, 3)); suma2_o += (x ** 2).sum((0, 2, 3)); n_o += x.shape[0] * ALTO * ANCHO
                x = ent[buenos].astype(np.float64); suma_e += x.sum((0, 2, 3)); suma2_e += (x ** 2).sum((0, 2, 3)); n_e += x.shape[0] * ALTO * ANCHO
            ds = xr.Dataset({"cwb": (("time", "cwb_channel", "south_north", "west_east"), obj),
                             "era5": (("time", "era5_channel", "south_north", "west_east"), np.ascontiguousarray(ent)),
                             "cwb_valid": (("time",), ok_o), "era5_valid": (("time", "era5_channel"), ok_e)},
                            coords={"time": np.array(tb, dtype="datetime64[ns]")})
            if primero:
                ds = ds.assign(XLAT=(("south_north", "west_east"), xlat), XLONG=(("south_north", "west_east"), xlon),
                               cwb_variable=(("cwb_channel",), np.array([n for _, n in SALIDAS])),
                               era5_variable=(("era5_channel",), np.array([n for _, n in ENTRADAS] + [n for _, n in FIJAS])),
                               cwb_pressure=(("cwb_channel",), np.full(len(SALIDAS), np.nan)),
                               era5_pressure=(("era5_channel",), np.full(n_ent, np.nan)))
                cod = {"time": {"units": "hours since 2001-01-01 00:00:00", "calendar": "standard", "dtype": "int64"},
                       "cwb": {"chunks": (1, len(SALIDAS), ALTO, ANCHO)}, "era5": {"chunks": (1, n_ent, ALTO, ANCHO)}}
                ds.to_zarr(a.salida, mode="w", encoding=cod, consolidated=True, zarr_format=2)
                primero = False
            else:
                ds.to_zarr(a.salida, append_dim="time", consolidated=True)
            hechas = b + len(tb)
            print(f"{hechas}/{len(horas)} muestras ({buenos.sum()} válidas en este bloque), {(time.time() - inicio) / 60:.1f} min", flush=True)
    media_o = suma_o / max(n_o, 1); desv_o = np.sqrt(np.maximum(suma2_o / max(n_o, 1) - media_o ** 2, 1e-12))
    media_e = suma_e / max(n_e, 1); desv_e = np.sqrt(np.maximum(suma2_e / max(n_e, 1) - media_e ** 2, 1e-12))
    xr.Dataset({"cwb_center": (("cwb_channel",), media_o.astype(np.float32)), "cwb_scale": (("cwb_channel",), desv_o.astype(np.float32)),
                "era5_center": (("era5_channel",), media_e.astype(np.float32)), "era5_scale": (("era5_channel",), desv_e.astype(np.float32))}
               ).to_zarr(a.salida, mode="a", consolidated=True)
    zarr.consolidate_metadata(a.salida)
    resumen = {"muestras": len(horas), "objetivo": dict(zip([n for _, n in SALIDAS], np.round(media_o, 4).tolist())),
               "minutos": round((time.time() - inicio) / 60, 1)}
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
