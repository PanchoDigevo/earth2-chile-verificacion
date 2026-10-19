"""Observaciones METAR históricas de los aeródromos chilenos desde el archivo ASOS de Iowa State
(mesonet.agron.iastate.edu). Temperatura, viento, precipitación horaria (p01i) y códigos de tiempo presente.

Uso: python metar_historico.py 2025 2026     -> escribe data/metar_2025.csv.gz y data/metar_2026.csv.gz

Nota: los METAR chilenos no incluyen el grupo de precipitación horaria "P", así que p01i viene en cero.
Para lluvia se usa wxcodes (RA, SHRA, DZ, TS...) como "llovió sí/no"."""
import csv, gzip, io, os, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTACIONES = [r["icao"] for r in csv.DictReader(open(os.path.join(AQUI, "estaciones.csv")))]
URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
CAMPOS = ["tmpf", "dwpf", "drct", "sknt", "gust", "p01i", "wxcodes"]   # gust: solo cuando hay ráfaga significativa


def bajar(anio):
    q = [("data", c) for c in CAMPOS] + [("station", s) for s in ESTACIONES]
    q += [("year1", anio), ("month1", 1), ("day1", 1), ("year2", anio + 1), ("month2", 1), ("day2", 1),
          ("tz", "Etc/UTC"), ("format", "onlycomma"), ("latlon", "no"), ("elev", "no"),
          ("missing", "M"), ("trace", "T"), ("direct", "no"), ("report_type", 3), ("report_type", 4)]
    url = URL + "?" + urllib.parse.urlencode(q)
    for intento in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "earth2-chile-verificacion/historico"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print("reintento", intento + 1, e); time.sleep(20 * (intento + 1))
    raise SystemExit("Iowa State no respondió")


def f_a_c(v):
    return "" if v in ("M", "") else round((float(v) - 32) / 1.8, 1)


def in_a_mm(v):
    if v in ("M", ""): return ""
    if v == "T": return 0.0
    return round(float(v) * 25.4, 2)


def kt_a_ms(v):
    return "" if v in ("M", "") else round(float(v) * 0.514444, 1)


for anio in [int(a) for a in sys.argv[1:]] or [2025, 2026]:
    t0 = time.time()
    crudo = bajar(anio)
    filas = list(csv.DictReader(io.StringIO(crudo)))
    salida = os.path.join(AQUI, "data", f"metar_{anio}.csv.gz")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    n = 0
    with gzip.open(salida, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["icao", "time", "temp_c", "dewp_c", "wdir", "wspd_ms", "gust_ms", "p01_mm", "wx"])
        for r in filas:
            if r.get("tmpf", "M") == "M":
                continue
            w.writerow([r["station"], r["valid"], f_a_c(r["tmpf"]), f_a_c(r.get("dwpf", "M")),
                        "" if r.get("drct", "M") == "M" else r["drct"], kt_a_ms(r.get("sknt", "M")),
                        kt_a_ms(r.get("gust", "M")),
                        in_a_mm(r.get("p01i", "M")), "" if r.get("wxcodes", "M") == "M" else r["wxcodes"]])
            n += 1
    print(f"{anio}: {len(filas)} reportes, {n} con temperatura -> {salida} en {round(time.time() - t0)} s")
