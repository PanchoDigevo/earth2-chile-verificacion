"""Corre un modelo global de Earth-2 en una GPU propia (L40S del POD) y deja su salida lista para verificar (tarea 5).

Modelos (todos globales; sirven en Chile tal como vienen):
  fcn3  FourCastNet 3 de NVIDIA. Su ficha en Earth2Studio dice ~80 GB, pero Guillermo lo desplegó y cargó en una L40S
        de 48 GB (23-oct-2026); falta probar la inferencia completa a 10 días.
  aifs  AIFS-Single 1.1 de ECMWF (~40 GB). Es el control: debe parecerse al AIFS que publica ECMWF.
  sfno  FourCastNet v2 (SFNO) de NVIDIA (~40 GB).
Se corre DENTRO del contenedor: la entrada global (un tensor de ~72 canales, ~285 MB) supera el límite de 270 MB del
gateway de NVCF, así que un NIM que la recibe por la red no sirve; la petición es una fecha y la respuesta ~3 MB.

Condición inicial: el análisis de IFS de ECMWF open data en AWS (0,25°), la misma hora de corrida que AIFS, IFS y GFS.
Salidas (todas fuera del repo salvo el CSV por estación):
  <salida>/<MODELO>_<corrida>.nc        recorte de Chile (t2m, u10m, v10m y tp si el modelo la da; lead_time, lat, lon)
  verificacion/data/puntos_<MODELO>_<corrida>.csv   valores en los aeródromos, el formato que verify.py ya lee
  earth2/workload/<MODELO>_<corrida>.json         ficha técnica de la corrida: GPU, minutos, memoria, tráfico, disco

El mismo `pronosticar()` sirve como cuerpo de una función de NVIDIA Cloud Functions: recibe la corrida y devuelve el
recorte de Chile, que earth2/endpoint.py baja desde GitHub Actions.

Uso en el POD:   python earth2/correr_pod.py --modelo aifs [--corrida 2026-10-21T00] [--horas 240] [--control]
Prueba sin GPU:  python earth2/correr_pod.py --modelo persistencia --horas 12 --control
                 (modelo trivial de Earth2Studio que repite el análisis: prueba la descarga de IFS, el recorte, los archivos y
                 el control, que a plazo 0 da ~0,6 °C por el cambio de grilla de AIFS; lo corre .github/workflows/earth2-pod-prueba.yml)
                 python earth2/correr_pod.py --modelo aifs --simular   (datos inventados, ni siquiera Earth2Studio)"""
import argparse, datetime as dt, json, os, shutil, sys, time
from collections import OrderedDict
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from endpoint import ESTACIONES, SALIDA, en_estaciones, ultima_corrida  # noqa: E402

NOMBRE = {"fcn3": "FCN3", "aifs": "AIFS-POD", "sfno": "SFNO", "persistencia": "PERSISTENCIA"}
CAJA = (-15.0, -63.0, 284.0, 302.0)   # latitud norte, sur, longitud oeste, este (0-360): Chile, su mar y el aeródromo antártico
VARS = ["t2m", "u10m", "v10m", "tp"]  # tp solo si el modelo la entrega


def cargar(modelo):
    if modelo == "persistencia":
        from earth2studio.models.px import Persistence
        return Persistence(["t2m", "u10m", "v10m"], OrderedDict({"lat": np.linspace(90, -90, 721), "lon": np.arange(0, 360, 0.25)}))
    from earth2studio.models.px import AIFS, FCN3, SFNO
    clase = {"aifs": AIFS, "fcn3": FCN3, "sfno": SFNO}[modelo]
    return clase.load_model(clase.load_default_package())


def fuente_inicial(ci):
    """Condición inicial. IFS de ECMWF en AWS responde "503 Slow Down" con carga, y con el tope por defecto de Earth2Studio
    (600 s) corta con FSTimeoutError (pasó en la función de NVCF el 23-oct-2026): tope de 1 h y reintentos cortos.
    GFS de NOAA en AWS no frena así; es el respaldo."""
    if ci == "gfs":
        from earth2studio.data import GFS
        return GFS(source="aws", cache=False, async_timeout=1800, retries=6)
    from earth2studio.data import IFS
    from ecmwf import opendata
    src = IFS(source="aws", cache=False, async_timeout=3600)
    src.client = opendata.Client(source="aws", model="ifs", maximum_retries=8, retry_after=15, use_server_retry_after=False)
    return src


def pronosticar(modelo, corrida, horas, dispositivo="cuda", ci="auto"):
    """Corre el modelo desde el análisis de IFS (o de GFS si IFS no responde, con ci="auto") y devuelve el recorte de
    Chile como xarray.Dataset; el atributo "condicion_inicial" dice con cuál partió."""
    import torch
    from earth2studio.io import XarrayBackend
    from earth2studio.run import deterministic
    m = cargar(modelo)
    oc = m.output_coords(m.input_coords())
    lat, lon = np.asarray(oc["lat"]), np.asarray(oc["lon"])
    salida = OrderedDict({
        "lat": lat[(lat <= CAJA[0]) & (lat >= CAJA[1])],
        "lon": lon[(lon >= CAJA[2]) & (lon <= CAJA[3])],
        "variable": np.array([v for v in VARS if v in list(oc["variable"])]),
    })
    for fuente in (["ifs", "gfs"] if ci == "auto" else [ci]):
        try:
            io = XarrayBackend()
            deterministic([corrida], horas // 6, m, fuente_inicial(fuente), io, output_coords=salida, device=torch.device(dispositivo))
            io.root.attrs["condicion_inicial"] = fuente.upper()
            return io.root
        except Exception as e:
            if fuente == "gfs" or ci != "auto":
                raise
            print(f"Condición inicial IFS falló ({type(e).__name__}: {e}); se usa GFS", flush=True)


def simulado(corrida, horas):
    """Recorte de Chile inventado con la forma de la salida de Earth2Studio, para probar sin GPU."""
    import xarray as xr
    lat = np.arange(CAJA[0], CAJA[1] - 0.01, -0.25); lon = np.arange(CAJA[2], CAJA[3] + 0.01, 0.25)
    lt = np.array([np.timedelta64(h, "h") for h in range(0, horas + 1, 6)])
    rng = np.random.default_rng(0); forma = (1, len(lt), len(lat), len(lon))
    base = 288.0 + 0.4 * (lat[None, None, :, None] + 33)
    return xr.Dataset({"t2m": (("time", "lead_time", "lat", "lon"), base + rng.normal(0, 2, forma)),
                       "u10m": (("time", "lead_time", "lat", "lon"), rng.normal(0, 4, forma)),
                       "v10m": (("time", "lead_time", "lat", "lon"), rng.normal(0, 4, forma))},
                      coords={"time": [np.datetime64(corrida)], "lead_time": lt, "lat": lat, "lon": lon})


def red_bytes():
    try:
        import psutil
        c = psutil.net_io_counters(); return c.bytes_recv + c.bytes_sent
    except Exception:
        return None


def control(df_pod, corrida):
    """Compara con el AIFS que publica ECMWF, mismos aeródromos y plazos. No se espera igualdad exacta: ECMWF inicializa
    con su análisis a resolución nativa y puede correr otra versión del checkpoint; aquí partimos del análisis de 0,25°."""
    from fetch_e2s import extraer
    est = pd.read_csv(ESTACIONES)
    plazos = [h for h in (0, 6, 12, 24, 48) if h in set(df_pod.lead_h)]
    ref = pd.DataFrame(extraer("aifs", corrida, plazos, est))
    m = df_pod.merge(ref, on=["lead_h", "icao"], suffixes=("_pod", "_ecmwf"))
    m["dt"] = m.t_fc_pod - m.t_fc_ecmwf; m["dw"] = m.w_fc_pod - m.w_fc_ecmwf
    tabla = m.groupby("lead_h").agg(pares=("dt", "size"), t_media=("dt", lambda x: x.abs().mean()), t_max=("dt", lambda x: x.abs().max()),
                                    v_media=("dw", lambda x: x.abs().mean()), v_max=("dw", lambda x: x.abs().max())).round(2)
    print("Control contra el AIFS de ECMWF (diferencia absoluta; °C y m/s):"); print(tabla.to_string())
    return tabla.reset_index().to_dict(orient="records")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", choices=sorted(NOMBRE), default="fcn3")
    ap.add_argument("--corrida", help="YYYY-MM-DDTHH (UTC); por defecto, la última con 6 h de antigüedad")
    ap.add_argument("--horas", type=int, default=240, help="alcance en horas, múltiplo de 6 (10 días = 240)")
    ap.add_argument("--salida", default=os.environ.get("EARTH2_DATOS", os.path.expanduser("~/earth2_datos")), help="carpeta para el recorte (fuera del repo)")
    ap.add_argument("--ci", choices=["auto", "ifs", "gfs"], default="auto", help="condición inicial (auto: IFS y, si falla, GFS)")
    ap.add_argument("--control", action="store_true", help="comparar con el AIFS de ECMWF en los mismos pares")
    ap.add_argument("--simular", action="store_true", help="sin GPU ni modelo: datos inventados, para probar el resto")
    a = ap.parse_args()
    corrida = dt.datetime.strptime(a.corrida, "%Y-%m-%dT%H") if a.corrida else ultima_corrida()
    nombre = NOMBRE[a.modelo] + ("-SIMULADO" if a.simular else "")
    ficha = {"modelo": nombre, "corrida_utc": f"{corrida:%Y-%m-%dT%H}", "horas": a.horas}

    t0, r0 = time.time(), red_bytes()
    if a.simular:
        ds = simulado(corrida, a.horas)
    elif a.modelo == "persistencia":
        ds = pronosticar(a.modelo, corrida, a.horas, dispositivo="cpu", ci=a.ci)
    else:
        import torch
        torch.cuda.reset_peak_memory_stats()
        ds = pronosticar(a.modelo, corrida, a.horas, ci=a.ci)
        ficha.update({"gpu": torch.cuda.get_device_name(0), "gpus_usadas": 1,
                      "memoria_gpu_max_gb": round(torch.cuda.max_memory_allocated() / 1e9, 1)})
    ficha["minutos"] = round((time.time() - t0) / 60, 1)
    ficha["condicion_inicial"] = ds.attrs.get("condicion_inicial", "simulada")
    if r0 is not None:
        ficha["trafico_red_gb"] = round((red_bytes() - r0) / 1e9, 2)

    os.makedirs(a.salida, exist_ok=True)
    nc = os.path.join(a.salida, f"{nombre}_{corrida:%Y%m%d_%H}.nc")
    ds.to_netcdf(nc)
    ficha["recorte_chile_mb"] = round(os.path.getsize(nc) / 1e6, 1)
    ficha["disco_libre_gb"] = round(shutil.disk_usage(a.salida).free / 1e9, 1)

    df = en_estaciones(ds, corrida, nombre, pd.read_csv(ESTACIONES))
    os.makedirs(SALIDA, exist_ok=True)
    csv = os.path.join(SALIDA, f"puntos_{nombre}_{corrida:%Y%m%d_%H}.csv")
    df.to_csv(csv, index=False)
    if a.control and not a.simular:
        ficha["control"] = control(df, corrida)

    os.makedirs(os.path.join(AQUI, "workload"), exist_ok=True)
    json.dump(ficha, open(os.path.join(AQUI, "workload", f"{nombre}_{corrida:%Y%m%d_%H}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{nombre} {corrida:%Y-%m-%d %H}Z: {ficha['minutos']} min, recorte {ficha['recorte_chile_mb']} MB en {nc}; "
          f"{len(df)} valores en {df.icao.nunique()} aeródromos -> {csv}")
    print("Ficha:", json.dumps({k: v for k, v in ficha.items() if k != "control"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
