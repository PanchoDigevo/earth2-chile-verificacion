"""Descarga IFS HRES (ECMWF open data vía AWS, CC-BY 4.0): 2t, 10u, 10v, tp a 0,25°.
Es el modelo físico de ECMWF, la referencia natural para medir a AIFS (su modelo de IA).
Uso: python fetch_ifs.py              -> última corrida completa disponible
     python fetch_ifs.py 2026-10-13 6 -> corrida específica (fecha, hora UTC)

Misma lógica acotada que fetch_aifs.py: la corrida se elige con HEAD a los índices, nunca con
Client.latest(). Desde el ciclo 50r1 (may-2026) las corridas de 06 y 18 UTC también van en el
stream "oper"; ecmwf-opendata >= 0.3.34 lo resuelve solo según la fecha."""
import os, time
from ecmwf.opendata import Client
from corridas import STEPS, corrida_pedida

PARAMS = ["2t", "10u", "10v", "tp"]
BASE = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
os.makedirs("data", exist_ok=True)


def url_indice(run, step):
    return f"{BASE}/{run:%Y%m%d}/{run:%H}z/ifs/0p25/oper/{run:%Y%m%d%H}0000-{step}h-oper-fc.index"


run = corrida_pedida("IFS", url_indice)
name = f"data/ifs_{run:%Y%m%d_%H}.grib2"
if os.path.exists(name):
    print("IFS run:", run, "ya descargado en", name)
    raise SystemExit(0)

c = Client(source="aws", model="ifs", resol="0p25",
           maximum_retries=5, retry_after=20, use_server_retry_after=False)
t0 = time.time()
tmp = "data/_dl_ifs.grib2"
r = c.retrieve(type="fc", stream="oper", step=STEPS, param=PARAMS, target=tmp, date=f"{run:%Y-%m-%d}", time=run.hour)
os.replace(tmp, name)
print("IFS run:", r.datetime, "->", name, "en", round(time.time() - t0), "s")
