"""Descarga AIFS-single (ECMWF open data vía AWS, CC-BY 4.0): 2t, 10u, 10v, tp a 0,25°.
Uso: python fetch_aifs.py              -> última corrida completa disponible
     python fetch_aifs.py 2026-10-13 6 -> corrida específica (fecha, hora UTC)

Elige la corrida sin usar Client.latest(): mientras ECMWF publica una corrida, el bucket
responde 503 y el cliente reintenta cada 120 s hasta 500 veces, lo que colgaba el job."""
import os, time
from ecmwf.opendata import Client
from corridas import STEPS, corrida_pedida

PARAMS = ["2t", "10u", "10v", "tp", "tcc"]   # tcc: nubosidad total, para el ícono del pronóstico
BASE = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
os.makedirs("data", exist_ok=True)


def url_indice(run, step):
    return f"{BASE}/{run:%Y%m%d}/{run:%H}z/aifs-single/0p25/oper/{run:%Y%m%d%H}0000-{step}h-oper-fc.index"


run = corrida_pedida("AIFS", url_indice)
name = f"data/aifs_{run:%Y%m%d_%H}.grib2"
if os.path.exists(name):
    print("AIFS run:", run, "ya descargado en", name)
    raise SystemExit(0)

# Reintentos acotados (por defecto: 500 veces cada 120 s).
c = Client(source="aws", model="aifs-single", resol="0p25",
           maximum_retries=5, retry_after=20, use_server_retry_after=False)
t0 = time.time()
tmp = "data/_dl_aifs.grib2"
r = c.retrieve(type="fc", step=STEPS, param=PARAMS, target=tmp, date=f"{run:%Y-%m-%d}", time=run.hour)
os.replace(tmp, name)
print("AIFS run:", r.datetime, "->", name, "en", round(time.time() - t0), "s")
