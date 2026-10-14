"""Descarga AIFS-single (ECMWF open data vía AWS, CC-BY 4.0): 2t, 10u, 10v, tp a 0,25°.
Uso: python fetch_aifs.py              -> última corrida disponible
     python fetch_aifs.py 2026-10-13 6 -> corrida específica (fecha, hora UTC)"""
import os, sys, time
from ecmwf.opendata import Client

STEPS = [0, 6, 12, 18, 24, 36, 48]
os.makedirs("data", exist_ok=True)
c = Client(source="aws", model="aifs-single", resol="0p25")
kw = dict(date=sys.argv[1], time=int(sys.argv[2])) if len(sys.argv) >= 3 else {}
t0 = time.time()
tmp = "data/_dl.grib2"
r = c.retrieve(type="fc", step=STEPS, param=["2t", "10u", "10v", "tp"], target=tmp, **kw)
name = f"data/aifs_{r.datetime:%Y%m%d_%H}.grib2"
os.replace(tmp, name)
print("AIFS run:", r.datetime, "->", name, "en", round(time.time() - t0), "s")
