"""Escenarios de peligro meteorológico de incendio a 15 días con el ensamble de IA de ECMWF (AIFS-ENS, 50 miembros).

Para cada comuna de escenarios/comunas.csv y cada día, en cada miembro:
  - temperatura, humedad relativa (desde el punto de rocío) y viento a 10 m a las 18 UTC (media tarde en Chile),
  - lluvia del día (diferencia del acumulado) y días seguidos sin lluvia dentro del pronóstico (menos de 1 mm).
Indicador (regla 30-30-30 que usa CONAF): "condición crítica" si a la vez temperatura ≥ 30 °C, humedad ≤ 30 % y viento
≥ 30 km/h; "condición alta" si se cumplen al menos dos de las tres y lleva 5 días o más sin lluvia.
Probabilidad = porcentaje de los 50 miembros en esa condición. El FWI canadiense no se calcula: necesita el estado de
humedad del combustible de días anteriores, que el ensamble no trae.

Fuente: ECMWF open data en AWS (AIFS-ENS, 0,25°, CC-BY 4.0). Solo se bajan los mensajes necesarios por rango de bytes.
Salidas: escenarios/data/actual.json y escenarios/data/historial.csv (para ver cómo cambia la probabilidad de un mismo día).
Uso: python escenarios/escenarios.py [--fecha YYYY-MM-DD]"""
import argparse, csv, datetime as dt, json, os, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
import sys
import numpy as np
import eccodes as ec
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
B = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
UA = {"User-Agent": "earth2-chile-verificacion/escenarios"}
PASOS = list(range(18, 361, 24))           # 18 UTC de cada día, hasta 15 días
CAMPOS = ("2t", "2d", "10u", "10v", "tp")
T_UMB, HR_UMB, V_UMB = 30.0, 30.0, 30.0    # °C, %, km/h
DIAS_SECOS = 5


def get(url, rango=None, intentos=8):
    for i in range(intentos):
        try:
            h = dict(UA)
            if rango:
                h["Range"] = f"bytes={rango[0]}-{rango[1]}"
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(min(60, 2 * 2 ** i))
        except Exception:
            time.sleep(min(60, 2 * 2 ** i))
    return None


def base(run, paso):
    return f"{B}/{run:%Y%m%d}/{run:%H}z/aifs-ens/0p25/enfo/{run:%Y%m%d%H}0000-{paso}h-enfo-pf"


def ultima_corrida(fecha=None):
    hoy = fecha or dt.datetime.utcnow().date()
    for dias in range(0, 4):
        for h in (12, 0):
            run = dt.datetime(hoy.year, hoy.month, hoy.day, h) - dt.timedelta(days=dias)
            ix = get(base(run, PASOS[-1]) + ".index", intentos=3)
            if ix and ix[:1] == b"{":
                return run
    raise SystemExit("no hay corrida AIFS-ENS completa en los últimos 4 días")


def mensajes(run, paso):
    ix = None
    for _ in range(5):
        ix = get(base(run, paso) + ".index")
        if ix and ix[:1] == b"{":
            break
        time.sleep(10)
    out = []
    for l in (ix or b"").decode().splitlines():
        if not l.startswith("{"):
            continue
        e = json.loads(l)
        if e.get("levtype") == "sfc" and e.get("param") in CAMPOS:
            o, n = int(e["_offset"]), int(e["_length"])
            out.append((paso, int(e["number"]), e["param"], base(run, paso) + ".grib2", (o, o + n - 1)))
    return out


def valores(m, puntos):
    paso, miembro, param, url, rango = m
    datos = get(url, rango)
    if not datos:
        return m[:3], None
    gid = ec.codes_new_from_message(datos)
    try:
        return m[:3], [ec.codes_grib_find_nearest(gid, la, lo)[0].value for la, lo in puntos]
    finally:
        ec.codes_release(gid)


def humedad(t, td):
    a, b = 17.625, 243.04
    return 100 * np.exp(a * td / (b + td) - a * t / (b + t))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fecha")
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    comunas = list(csv.DictReader(open(os.path.join(AQUI, "comunas.csv"), encoding="utf-8")))
    puntos = [(float(c["lat"]), float(c["lon"])) for c in comunas]
    run = ultima_corrida(dt.date.fromisoformat(a.fecha) if a.fecha else None)
    print("corrida AIFS-ENS:", run, flush=True)
    t0 = time.time()
    lista = [m for p in PASOS for m in mensajes(run, p)]
    print(f"{len(lista)} mensajes por bajar", flush=True)
    V = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for k, v in ex.map(lambda m: valores(m, puntos), lista):
            if v is not None:
                V[k] = v
    print(f"bajados {len(V)} en {round(time.time() - t0)} s", flush=True)
    nm, nd, nc = 50, len(PASOS), len(comunas)
    arr = {p: np.full((nm, nd, nc), np.nan) for p in CAMPOS}
    for (paso, miembro, param), v in V.items():
        arr[param][miembro - 1, PASOS.index(paso)] = v
    t = arr["2t"] - 273.15; td = arr["2d"] - 273.15
    hr = humedad(t, td)
    vv = np.hypot(arr["10u"], arr["10v"]) * 3.6
    tp = arr["tp"] * (1000 if np.nanmax(arr["tp"]) < 5 else 1)       # m -> mm si viene en metros
    lluvia = np.diff(np.concatenate([np.zeros((nm, 1, nc)), tp], axis=1), axis=1).clip(min=0)
    secos = np.zeros_like(lluvia)
    for d in range(nd):
        secos[:, d] = np.where(lluvia[:, d] < 1, (secos[:, d - 1] if d else 0) + 1, 0)
    cumple = (t >= T_UMB).astype(int) + (hr <= HR_UMB).astype(int) + (vv >= V_UMB).astype(int)
    critica = cumple == 3
    alta = (cumple >= 2) & (secos >= DIAS_SECOS)
    validos = ~np.isnan(t) & ~np.isnan(hr) & ~np.isnan(vv)
    n = validos.sum(axis=0)
    pc = np.where(n > 0, 100 * (critica & validos).sum(axis=0) / np.maximum(n, 1), np.nan)
    pa = np.where(n > 0, 100 * ((alta | critica) & validos).sum(axis=0) / np.maximum(n, 1), np.nan)
    pct = lambda x, q: np.nanpercentile(x, q, axis=0)
    salida = {"corrida": f"{run:%Y-%m-%dT%H:%MZ}", "generado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"),
              "umbrales": {"t": T_UMB, "hr": HR_UMB, "v": V_UMB, "dias_secos": DIAS_SECOS}, "miembros": int(n.max()), "comunas": []}
    hist = []
    for j, c in enumerate(comunas):
        dias = []
        for d, paso in enumerate(PASOS):
            f = (run + dt.timedelta(hours=paso)).date()
            dias.append({"fecha": f.isoformat(), "p_critica": round(float(pc[d, j]), 1), "p_alta": round(float(pa[d, j]), 1), "n": int(n[d, j]),
                         "t": [round(float(x), 1) for x in (pct(t[:, d, j], 10), pct(t[:, d, j], 50), pct(t[:, d, j], 90))],
                         "hr": [round(float(x), 0) for x in (pct(hr[:, d, j], 10), pct(hr[:, d, j], 50), pct(hr[:, d, j], 90))],
                         "v": [round(float(x), 0) for x in (pct(vv[:, d, j], 10), pct(vv[:, d, j], 50), pct(vv[:, d, j], 90))],
                         "lluvia_p50": round(float(pct(lluvia[:, d, j], 50)), 1), "secos_p50": int(pct(secos[:, d, j], 50))})
            hist.append([f"{run:%Y-%m-%d %H}", c["comuna"], f.isoformat(), d + 1, dias[-1]["p_critica"], dias[-1]["p_alta"], dias[-1]["t"][1], dias[-1]["hr"][1], dias[-1]["v"][1]])
        salida["comunas"].append({**c, "dias": dias})
    json.dump(salida, open(os.path.join(DATA, "actual.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ruta = os.path.join(DATA, "historial.csv")
    nuevo = not os.path.exists(ruta)
    previas = set()
    if not nuevo:
        previas = {(r["corrida"], r["comuna"], r["fecha_objetivo"]) for r in csv.DictReader(open(ruta, encoding="utf-8"))}
    with open(ruta, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(["corrida", "comuna", "fecha_objetivo", "dias_antes", "p_critica", "p_alta", "t_p50", "hr_p50", "v_p50"])
        for h in hist:
            if (h[0], h[1], h[2]) not in previas:
                w.writerow(h)
    for c in salida["comunas"]:
        mx = max(c["dias"], key=lambda x: x["p_alta"])
        print(f"{c['comuna']}: máximo de condición alta o crítica {mx['p_alta']} % el {mx['fecha']}; T p50 {mx['t'][1]} °C, HR {mx['hr'][1]} %, viento {mx['v'][1]} km/h")
    import render_escenarios
    render_escenarios.render()


if __name__ == "__main__":
    main()
