"""Prueba de los conectores GOES y GOESGLM de Earth2Studio para la tormenta de Santiago del 13 de octubre de 2026,
entre las 14:00 y las 19:00 hora de Chile (17 a 22 UTC).

- GOES-19, imagen de disco completo (cada 10 min; aquí cada 30 min para no bajar decenas de GB): temperatura de brillo
  del canal 13 (infrarrojo limpio, 10,35 µm) en una caja sobre Santiago. Topes de nube muy fríos (menos de −50 °C)
  indican nubes de tormenta profundas.
- GLM (detector de rayos de GOES-East): destellos (flashes) en la misma caja, cada 10 minutos.
Salida: earth2/data/goes_13oct.csv (una fila por hora, ambas fuentes)."""
import datetime as dt, os
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
CAJA = (-34.0, -71.2, -33.0, -70.2)        # lat_min, lon_min, lat_max, lon_max: Santiago y su precordillera
T0, T1 = dt.datetime(2026, 10, 13, 17, 0), dt.datetime(2026, 10, 13, 22, 0)


def abi():
    from earth2studio.data import GOES
    src = GOES(satellite="goes19", scan_mode="F", cache=False, verbose=False)
    lat, lon = GOES.grid(satellite="goes19", scan_mode="F")
    m = (lat >= CAJA[0]) & (lat <= CAJA[2]) & (lon >= CAJA[1]) & (lon <= CAJA[3])
    filas = []
    t = T0
    while t <= T1:
        try:
            da = src([t], ["abi13c"])
            bt = np.asarray(da.isel(time=0).sel(variable="abi13c").values)[m] - 273.15
            filas.append({"hora_utc": t, "bt13_min_c": float(np.nanmin(bt)), "bt13_p10_c": float(np.nanpercentile(bt, 10)),
                          "pct_bajo_menos50": float(100 * np.nanmean(bt < -50))})
            print(t, "ABI ok", round(filas[-1]["bt13_min_c"], 1), flush=True)
        except Exception as e:
            print(t, "ABI falló:", e, flush=True)
        t += dt.timedelta(minutes=30)
    return pd.DataFrame(filas)


def glm():
    from earth2studio.data import GOESGLM
    src = GOESGLM(satellite="east", lat_lon_bbox=CAJA, time_tolerance=(np.timedelta64(0, "m"), np.timedelta64(10, "m")),
                  cache=False, verbose=False)
    filas = []
    t = T0
    while t < T1:
        try:
            df = src([t], ["lightning_flash_count"])
            filas.append({"hora_utc": t, "destellos_10min": int(len(df))})
        except Exception as e:
            print(t, "GLM falló:", e, flush=True)
            filas.append({"hora_utc": t, "destellos_10min": np.nan})
        t += dt.timedelta(minutes=10)
    return pd.DataFrame(filas)


def main():
    os.makedirs(os.path.join(AQUI, "data"), exist_ok=True)
    g = glm()
    print("GLM:", int(np.nansum(g.destellos_10min)), "destellos en la caja entre 17 y 22 UTC", flush=True)
    a = abi()
    g["hora"] = g.hora_utc.dt.floor("h"); a["hora"] = a.hora_utc.dt.floor("h") if len(a) else a.get("hora")
    res = g.groupby("hora").destellos_10min.sum().reset_index().rename(columns={"destellos_10min": "destellos"})
    if len(a):
        res = res.merge(a.groupby("hora").agg(bt13_min_c=("bt13_min_c", "min"), pct_bajo_menos50=("pct_bajo_menos50", "max")).reset_index(), on="hora", how="outer")
    res["hora_chile"] = res.hora - pd.Timedelta(hours=3)
    res.to_csv(os.path.join(AQUI, "data", "goes_13oct.csv"), index=False)
    print(res.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
    # Salida inmediata: al cerrar Python, eccodes y las bibliotecas netCDF/HDF5 que carga Earth2Studio chocan
    # (segmentation fault / double free) aunque el trabajo ya terminó bien.
    import sys as _s; _s.stdout.flush(); _s.stderr.flush(); os._exit(0)
