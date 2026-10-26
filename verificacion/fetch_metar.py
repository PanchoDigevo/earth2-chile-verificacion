"""Observaciones METAR de aeródromos chilenos (reportadas por la DMC; API pública de aviationweather.gov).
Acumula en data/metar_obs.csv sin duplicados."""
import csv, json, os, sys, time, urllib.request

ICAO = ("SCEL,SCSE,SCIE,SCDA,SCAR,SCCF,SCFA,SCTE,SCCI,SCBA,SCVD,SCTC,SCQP,SCIC,SCCH,SCGE,"
        "SCJO,SCSN,SCER,SCRM,SCAT,SCPC,SCAS,SCNT,SCCY,SCTB")
URL = f"https://aviationweather.gov/api/data/metar?ids={ICAO}&format=json&hours=48"
PATH = "data/metar_obs.csv"
FIELDS = ["icao", "name", "lat", "lon", "elev", "time", "temp_c", "dewp_c", "wdir", "wspd_kt", "raw"]

os.makedirs("data", exist_ok=True)
req = urllib.request.Request(URL, headers={"User-Agent": "earth2-chile-verificacion/0.1"})
rows = None
for intento in range(4):                      # aviationweather.gov a veces responde 502/504 por unos minutos
    try:
        rows = json.load(urllib.request.urlopen(req, timeout=60))
        break
    except Exception as e:
        print(f"METAR: intento {intento + 1} falló ({type(e).__name__}: {e})", flush=True)
        time.sleep(20 * (intento + 1))
if rows is None:
    # Sin METAR nuevos no se detiene la verificación: se sigue con las observaciones ya guardadas (se recuperan en la próxima
    # corrida, porque se piden las últimas 48 h).
    print("METAR: aviationweather.gov no respondió; se sigue con las observaciones guardadas")
    sys.exit(0)
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
