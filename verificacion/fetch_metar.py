"""Observaciones METAR de aeródromos chilenos (reportadas por la DMC; API pública de aviationweather.gov).
Acumula en data/metar_obs.csv sin duplicados."""
import csv, json, os, urllib.request

ICAO = ("SCEL,SCSE,SCIE,SCDA,SCAR,SCCF,SCFA,SCTE,SCCI,SCBA,SCVD,SCTC,SCQP,SCIC,SCCH,SCGE,"
        "SCJO,SCSN,SCER,SCRM,SCAT,SCPC,SCAS,SCNT,SCCY,SCTB")
URL = f"https://aviationweather.gov/api/data/metar?ids={ICAO}&format=json&hours=48"
PATH = "data/metar_obs.csv"
FIELDS = ["icao", "name", "lat", "lon", "elev", "time", "temp_c", "dewp_c", "wdir", "wspd_kt", "raw"]

os.makedirs("data", exist_ok=True)
req = urllib.request.Request(URL, headers={"User-Agent": "earth2-chile-verificacion/0.1"})
rows = json.load(urllib.request.urlopen(req, timeout=60))
seen = set()
exists = os.path.exists(PATH)
if exists:
    with open(PATH) as f:
        for r in csv.DictReader(f):
            seen.add((r["icao"], r["time"]))
new = 0
with open(PATH, "a", newline="") as f:
    w = csv.writer(f)
    if not exists:
        w.writerow(FIELDS)
    for r in rows:
        key = (r["icaoId"], r["reportTime"])
        if key in seen or r.get("temp") is None:
            continue
        seen.add(key)
        w.writerow([r["icaoId"], r.get("name", ""), r["lat"], r["lon"], r.get("elev", ""), r["reportTime"],
                    r["temp"], r.get("dewp", ""), r.get("wdir", ""), r.get("wspd", ""), r.get("rawOb", "")])
        new += 1
print(f"METAR: {len(rows)} reportes recibidos, {new} nuevos, archivo con {len(seen)} filas")
