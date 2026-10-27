"""Escenarios de peligro meteorológico de incendio a 15 días con el ensamble de IA de ECMWF (AIFS-ENS, 50 miembros).

Para cada comuna de escenarios/comunas.csv y cada día, en cada miembro:
  - temperatura, humedad relativa (desde el punto de rocío) y viento a 10 m a las 18 UTC (media tarde en Chile;
    con la corrida de 12 UTC son los pasos de 6, 30, 54... horas, no los de 18, 42...),
  - lluvia del día (diferencia del acumulado) y días seguidos sin lluvia dentro del pronóstico (menos de 1 mm).
Indicador (regla 30-30-30 que usa CONAF): "condición crítica" si a la vez temperatura ≥ 30 °C, humedad ≤ 30 % y viento
≥ 30 km/h; "condición alta" si se cumplen al menos dos de las tres y lleva 5 días o más sin lluvia.
Probabilidad = porcentaje de los 50 miembros en esa condición. El FWI canadiense no se calcula: necesita el estado de
humedad del combustible de días anteriores, que el ensamble no trae.

Fuente: ECMWF open data en AWS (AIFS-ENS, 0,25°, CC-BY 4.0). Solo se bajan los mensajes necesarios por rango de bytes.
Faenas (escenarios/faenas.csv): con los mismos 50 escenarios, la probabilidad de cada día de
  - viento fuerte: 50 km/h o más a 10 m a las 18 UTC,
  - nevada: 2 mm o más de agua equivalente en nieve (unos 2 cm de nieve) entre las 18 UTC del día anterior y las de ese día,
  - chubasco convectivo: 2 mm o más de precipitación convectiva en ese lapso (indicio de tormenta eléctrica; el modelo no da rayos),
  - frío extremo: −10 °C o menos a las 06 UTC (madrugada), llevando la temperatura de la grilla a la altura de la faena con
    6,5 °C por kilómetro de diferencia entre el terreno de la grilla (z del miembro de control) y la faena.
Comunas de todo Chile (verificacion/comunas.csv, 352): con los mismos escenarios, el porcentaje de miembros que cumple cada caso del
CATALOGO (helada, calor, lluvia, viento, nieve, tormenta, frío, tiempo de incendio, nublado) por día -> site/datos/escenarios_15d.json.
Salidas: escenarios/data/actual.json y escenarios/data/historial.csv (para ver cómo cambia la probabilidad de un mismo día).
Uso: python escenarios/escenarios.py [--fecha YYYY-MM-DD]"""
import argparse, csv, datetime as dt, json, os, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
import sys
import numpy as np
import eccodes as ec
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
B = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
UA = {"User-Agent": "earth2-chile-verificacion/escenarios"}
CAMPOS = ("2t", "2d", "10u", "10v", "tp", "sf", "cp", "tcc")   # tcc: nubosidad de la tarde, para el ícono de 15 días
F_VIENTO, F_NIEVE, F_CONV, F_FRIO = 50.0, 2.0, 2.0, -10.0   # km/h, mm de agua, mm, °C
GRADIENTE = 6.5                                              # °C por km


def pasos(run, hora_utc):
    """Pasos (h) de la corrida que caen a hora_utc, uno por día, 15 días."""
    return [h for h in range(6, 361, 6) if (run.hour + h) % 24 == hora_utc][:15]
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
            ix = get(base(run, 360) + ".index", intentos=3)
            if ix and ix[:1] == b"{":
                return run
    raise SystemExit("no hay corrida AIFS-ENS completa en los últimos 4 días")


def mensajes(run, paso, campos=CAMPOS):
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
        if e.get("levtype") == "sfc" and e.get("param") in campos:
            o, n = int(e["_offset"]), int(e["_length"])
            out.append((paso, int(e["number"]), e["param"], base(run, paso) + ".grib2", (o, o + n - 1)))
    return out


_IDX = {}
_CERROJO = threading.Lock()


def indices(gid, puntos):
    """Índice del punto de grilla más cercano a cada (lat, lon), calculado una vez por grilla y reutilizado en cada mensaje:
    con cientos de puntos (las comunas), leer todo el arreglo y tomar índices es mucho más rápido que find_nearest."""
    clave = (ec.codes_get(gid, "Ni"), ec.codes_get(gid, "Nj"), len(puntos))
    with _CERROJO:
        if clave not in _IDX:
            glat = ec.codes_get_double_array(gid, "latitudes"); glon = ec.codes_get_double_array(gid, "longitudes")
            out = np.empty(len(puntos), dtype=int)
            for i, (la, lo) in enumerate(puntos):
                lo = lo % 360 if glon.max() > 180 else lo
                out[i] = int(np.argmin((glat - la) ** 2 + ((glon - lo + 180) % 360 - 180) ** 2 * np.cos(np.radians(la)) ** 2))
            _IDX[clave] = out
        return _IDX[clave]


def valores(m, puntos):
    paso, miembro, param, url, rango = m
    datos = get(url, rango)
    if not datos:
        return m[:3], None
    gid = ec.codes_new_from_message(datos)
    try:
        f = 1000.0 if ec.codes_get(gid, "units") == "m" else 1.0      # acumulados: kg m-2 = mm; si vinieran en m, a mm
        return m[:3], (f * ec.codes_get_values(gid)[indices(gid, puntos)]).tolist()
    finally:
        ec.codes_release(gid)


def orografia(run, puntos):
    """Altura (m) del terreno de la grilla en cada punto, desde z del miembro de control en el paso 0."""
    b = f"{B}/{run:%Y%m%d}/{run:%H}z/aifs-ens/0p25/enfo/{run:%Y%m%d%H}0000-0h-enfo-cf"
    for l in (get(b + ".index") or b"").decode().splitlines():
        if l.startswith("{"):
            e = json.loads(l)
            if e.get("levtype") == "sfc" and e.get("param") == "z":
                o = int(e["_offset"]); _, v = valores((0, 0, "z", b + ".grib2", (o, o + int(e["_length"]) - 1)), puntos)
                return None if v is None else [x / 9.80665 for x in v]
    return None


def acumulado_diario(x):
    """De acumulado desde el inicio a lo caído entre un paso y el anterior (el primero, desde el inicio)."""
    return np.diff(np.concatenate([np.zeros(x[:, :1].shape), x], axis=1), axis=1).clip(min=0)


def humedad(t, td):
    a, b = 17.625, 243.04
    return 100 * np.exp(a * td / (b + td) - a * t / (b + t))


def faenas_salida(run, faenas, pf, fechas, oro):
    pct = lambda x, q: None if np.isnan(x).all() else round(float(np.nanpercentile(x, q)), 1)
    viento = np.hypot(pf["10u"], pf["10v"]) * 3.6
    nieve, conv = acumulado_diario(pf["sf"]), acumulado_diario(pf["cp"])
    salida, hist = [], []
    for j, c in enumerate(faenas):
        dz = ((oro[j] - float(c["altitud_m"])) / 1000 * GRADIENTE) if oro else 0.0   # grilla más baja -> faena más fría
        t_tarde, t_madr = pf["2t"][:, :, j] - 273.15 + dz, pf["2t_06"][:, :, j] - 273.15 + dz
        dias = []
        for d, f in enumerate(fechas):
            def prob(x, cond):
                ok = ~np.isnan(x[:, d]); n = int(ok.sum())
                return (round(100 * float(cond(x[ok, d]).sum()) / n, 1) if n else None), n
            p = {"viento": prob(viento[:, :, j], lambda v: v >= F_VIENTO)[0], "nieve": prob(nieve[:, :, j], lambda v: v >= F_NIEVE)[0],
                 "convectivo": prob(conv[:, :, j], lambda v: v >= F_CONV)[0], "frio": prob(t_madr, lambda v: v <= F_FRIO)[0]}
            dias.append({"fecha": f.isoformat(), "p": p, "n": prob(viento[:, :, j], lambda v: v >= 0)[1],
                         "v": [pct(viento[:, d, j], q) for q in (10, 50, 90)], "t_tarde": [pct(t_tarde[:, d], q) for q in (10, 50, 90)],
                         "t_madrugada": [pct(t_madr[:, d], q) for q in (10, 50, 90)],
                         "nieve": [pct(nieve[:, d, j], q) for q in (50, 90)], "convectivo": [pct(conv[:, d, j], q) for q in (50, 90)]})
            hist.append([f"{run:%Y-%m-%d %H}", c["faena"], f.isoformat(), d + 1] + [p[k] for k in ("viento", "nieve", "convectivo", "frio")])
        salida.append({**c, "altura_grilla_m": round(oro[j]) if oro else None, "correccion_c": round(dz, 1), "dias": dias})
    return salida, hist


def guardar_historial_faenas(hist):
    ruta = os.path.join(DATA, "historial_faenas.csv")
    previas = set()
    if os.path.exists(ruta):
        previas = {(r["corrida"], r["faena"], r["fecha_objetivo"]) for r in csv.DictReader(open(ruta, encoding="utf-8"))}
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(["corrida", "faena", "fecha_objetivo", "dias_antes", "p_viento", "p_nieve", "p_convectivo", "p_frio"])
        for h in hist:
            if tuple(h[:3]) not in previas:
                w.writerow(h)


def quince_dias(run, chile, pch, fechas):
    """site/datos/pronostico_15d.json: por comuna y día, máxima (18 UTC) y mínima (06 UTC) con el rango del ensamble,
    lluvia del día (valor central, rango y probabilidad de 1 mm o más) y viento de la tarde."""
    pct = lambda x, q: np.nanpercentile(x, q, axis=0)
    t18 = pch["2t"] - 273.15; t06 = pch["2t_06"] - 273.15
    vv = np.hypot(pch["10u"], pch["10v"]) * 3.6
    lluvia = acumulado_diario(pch["tp"])
    n = (~np.isnan(t18)).sum(axis=0)
    p1 = 100 * np.nansum(lluvia >= 1, axis=0) / np.maximum(n, 1)
    p5 = 100 * np.nansum(lluvia >= 5, axis=0) / np.maximum(n, 1)
    q = lambda a, qs: [np.round(pct(a, k), 1) for k in qs]
    tx = q(t18, (10, 50, 90)); tn = q(t06, (10, 50, 90)); ll = q(lluvia, (50, 90)); vi = q(vv, (50, 90))
    nub = pch["tcc"] * (100.0 if np.nanmax(pch["tcc"]) <= 1.0001 else 1.0)
    nb = np.round(pct(nub, 50))
    def fila(j):
        dias = []
        for d, f in enumerate(fechas):
            if n[d, j] == 0:
                continue
            tnv = [None if np.isnan(x[d, j]) else float(x[d, j]) for x in tn]
            dias.append({"f": f.isoformat(), "tmax": [float(x[d, j]) for x in tx], "tmin": tnv,
                         "ll": [float(x[d, j]) for x in ll], "p1": round(float(p1[d, j])), "p5": round(float(p5[d, j])),
                         "v": [float(x[d, j]) for x in vi], "nub": None if np.isnan(nb[d, j]) else int(nb[d, j]), "n": int(n[d, j])})
        return dias
    salida = {"corrida": f"{run:%Y-%m-%dT%H:%MZ}", "generado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "miembros": int(n.max()),
              "nota": "máxima = 18 UTC, mínima = 06 UTC (aprox.); lluvia de 24 h hasta las 18 UTC; viento a las 18 UTC; "
                      "los tres valores son los percentiles 10, 50 y 90 del ensamble (lluvia y viento: 50 y 90)",
              "comunas": {c["id"]: fila(j) for j, c in enumerate(chile)}}
    carpeta = os.path.join(AQUI, "..", "site", "datos"); os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "pronostico_15d.json")
    json.dump(salida, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{ruta}: {len(chile)} comunas, {len(fechas)} días, {os.path.getsize(ruta) // 1024} KB")


# Catálogo de escenarios por comuna (todas las comunas de Chile): id, nombre, regla en palabras, sectores, y cómo se cuenta.
# Los umbrales son los de uso común en los avisos de la DMC y en la agricultura; no están ajustados a ningún evento.
CATALOGO = [
    ("helada", "Helada", "0 °C o menos de madrugada", ["agro", "ciudades"]),
    ("helada_fuerte", "Helada fuerte", "−3 °C o menos de madrugada", ["agro"]),
    ("calor", "Calor", "32 °C o más a media tarde", ["ciudades", "agro", "energia", "incendios"]),
    ("calor_extremo", "Calor extremo", "35 °C o más a media tarde", ["ciudades", "energia"]),
    ("lluvia5", "Lluvia que moja la cosecha", "5 mm o más en el día", ["agro"]),
    ("lluvia20", "Lluvia fuerte", "20 mm o más en el día", ["ciudades", "agro"]),
    ("lluvia40", "Lluvia muy fuerte", "40 mm o más en el día", ["ciudades"]),
    ("viento50", "Viento fuerte", "50 km/h o más a media tarde", ["energia", "incendios", "agro", "cordillera"]),
    ("viento70", "Temporal de viento", "70 km/h o más a media tarde", ["energia", "ciudades"]),
    ("nieve", "Nevada", "unos 2 cm de nieve o más en el día", ["cordillera"]),
    ("nieve10", "Nevada intensa", "unos 10 cm de nieve o más en el día", ["cordillera"]),
    ("tormenta", "Tormenta posible", "chubasco convectivo de 2 mm o más", ["ciudades", "cordillera", "agro"]),
    ("frio", "Frío extremo", "−10 °C o menos de madrugada", ["cordillera"]),
    ("incendio_alta", "Tiempo de incendio, condición alta", "dos de las tres partes de la regla 30-30-30 y 5 días sin lluvia", ["incendios"]),
    ("incendio", "Tiempo de incendio, condición crítica", "regla 30-30-30 completa", ["incendios"]),
    ("nublado", "Día muy nublado", "85 % o más de nubes a media tarde", ["energia"]),
]
SECTORES = [("agro", "Agricultura"), ("ciudades", "Ciudades y quebradas"), ("incendios", "Incendios"), ("cordillera", "Cordillera, nieve y faenas"), ("energia", "Energía y redes")]


def escenarios_comunas(run, chile, pch, fechas):
    """site/datos/escenarios_15d.json: por comuna y escenario del CATALOGO, el porcentaje de los 50 miembros que lo cumple cada día."""
    t18 = pch["2t"] - 273.15; t06 = pch["2t_06"] - 273.15; td = pch["2d"] - 273.15
    hr = humedad(t18, td)
    vv = np.hypot(pch["10u"], pch["10v"]) * 3.6
    lluvia, nieve, conv = acumulado_diario(pch["tp"]), acumulado_diario(pch["sf"]), acumulado_diario(pch["cp"])
    nub = pch["tcc"] * (100.0 if np.nanmax(pch["tcc"]) <= 1.0001 else 1.0)
    secos = np.zeros_like(lluvia)
    for d in range(lluvia.shape[1]):
        secos[:, d] = np.where(lluvia[:, d] < 1, (secos[:, d - 1] if d else 0) + 1, 0)
    cumple = (t18 >= T_UMB).astype(int) + (hr <= HR_UMB).astype(int) + (vv >= V_UMB).astype(int)
    cond = {"helada": t06 <= 0, "helada_fuerte": t06 <= -3, "calor": t18 >= 32, "calor_extremo": t18 >= 35,
            "lluvia5": lluvia >= 5, "lluvia20": lluvia >= 20, "lluvia40": lluvia >= 40, "viento50": vv >= 50, "viento70": vv >= 70,
            "nieve": nieve >= 2, "nieve10": nieve >= 10, "tormenta": conv >= 2, "frio": t06 <= -10,
            "incendio_alta": ((cumple >= 2) & (secos >= DIAS_SECOS)) | (cumple == 3), "incendio": cumple == 3, "nublado": nub >= 85}
    base = {"helada": t06, "helada_fuerte": t06, "frio": t06, "calor": t18, "calor_extremo": t18, "lluvia5": lluvia, "lluvia20": lluvia, "lluvia40": lluvia,
            "viento50": vv, "viento70": vv, "nieve": nieve, "nieve10": nieve, "tormenta": conv, "incendio_alta": t18, "incendio": t18, "nublado": nub}
    comunas = {}
    for j, c in enumerate(chile):
        fila = {}
        for k, _, _, _ in CATALOGO:
            ok = ~np.isnan(base[k][:, :, j]); n = ok.sum(axis=0)
            p = np.where(n > 0, 100 * (cond[k][:, :, j] & ok).sum(axis=0) / np.maximum(n, 1), 0)
            if p.max() > 0:
                fila[k] = [int(round(x)) for x in p]
        comunas[c["id"]] = {"n": c["nombre"], "r": c["region"], "lat": round(float(c["lat"]), 3), "lon": round(float(c["lon"]), 3), "p": fila}
    salida = {"corrida": f"{run:%Y-%m-%dT%H:%MZ}", "generado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "miembros": 50,
              "fechas": [f.isoformat() for f in fechas], "escenarios": [{"id": k, "nombre": nm, "regla": rg, "sectores": sc} for k, nm, rg, sc in CATALOGO],
              "sectores": SECTORES, "comunas": comunas}
    carpeta = os.path.join(AQUI, "..", "site", "datos"); os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "escenarios_15d.json")
    json.dump(salida, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{ruta}: {len(comunas)} comunas, {len(CATALOGO)} escenarios, {os.path.getsize(ruta) // 1024} KB")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fecha")
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    comunas = list(csv.DictReader(open(os.path.join(AQUI, "comunas.csv"), encoding="utf-8")))
    faenas = list(csv.DictReader(open(os.path.join(AQUI, "faenas.csv"), encoding="utf-8")))
    chile = list(csv.DictReader(open(os.path.join(AQUI, "..", "verificacion", "comunas.csv"), encoding="utf-8")))   # las 352 comunas
    puntos = [(float(c["lat"]), float(c["lon"])) for c in comunas + faenas + chile]
    run = ultima_corrida(dt.date.fromisoformat(a.fecha) if a.fecha else None)
    PASOS, MADRUGADA = pasos(run, 18), pasos(run, 6)
    print("corrida AIFS-ENS:", run, flush=True)
    t0 = time.time()
    lista = [m for p in PASOS for m in mensajes(run, p)] + [(p + 1000,) + m[1:] for p in MADRUGADA for m in mensajes(run, p, ("2t",))]
    print(f"{len(lista)} mensajes por bajar", flush=True)
    V = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for k, v in ex.map(lambda m: valores(m, puntos), lista):
            if v is not None:
                V[k] = v
    print(f"bajados {len(V)} en {round(time.time() - t0)} s", flush=True)
    nm, nd, nc = 50, len(PASOS), len(comunas)
    fechas = [(run + dt.timedelta(hours=p)).date() for p in PASOS]
    arr = {p: np.full((nm, nd, len(puntos)), np.nan) for p in CAMPOS + ("2t_06",)}
    for (paso, miembro, param), v in V.items():
        if paso >= 1000:                                   # madrugada (06 UTC) del mismo día de Chile
            f = (run + dt.timedelta(hours=paso - 1000)).date()
            if f in fechas:
                arr["2t_06"][miembro - 1, fechas.index(f)] = v
        else:
            arr[param][miembro - 1, PASOS.index(paso)] = v
    nf = len(faenas)
    pf = {p: x[:, :, nc:nc + nf] for p, x in arr.items()}  # faenas
    pch = {p: x[:, :, nc + nf:] for p, x in arr.items()}   # todas las comunas de Chile (pestaña Pronóstico)
    arr = {p: x[:, :, :nc] for p, x in arr.items()}        # comunas prioritarias de incendio
    t = arr["2t"] - 273.15; td = arr["2d"] - 273.15
    hr = humedad(t, td)
    vv = np.hypot(arr["10u"], arr["10v"]) * 3.6
    lluvia = acumulado_diario(arr["tp"])
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
              "umbrales": {"t": T_UMB, "hr": HR_UMB, "v": V_UMB, "dias_secos": DIAS_SECOS}, "miembros": int(n.max()), "comunas": [],
              "umbrales_faena": {"viento": F_VIENTO, "nieve": F_NIEVE, "convectivo": F_CONV, "frio": F_FRIO, "gradiente": GRADIENTE}, "faenas": []}
    salida["faenas"], hist_f = faenas_salida(run, faenas, pf, fechas, orografia(run, puntos[nc:]))
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
    guardar_historial_faenas(hist_f)
    quince_dias(run, chile, pch, fechas)
    escenarios_comunas(run, chile, pch, fechas)
    for f in salida["faenas"]:
        print(f"{f['faena']}: grilla a {f['altura_grilla_m']} m; " + "; ".join(
            f"{k} máx. {max(x['p'][k] for x in f['dias'] if x['p'][k] is not None)} %" for k in ("viento", "nieve", "convectivo", "frio")))
    for c in salida["comunas"]:
        mx = max(c["dias"], key=lambda x: x["p_alta"])
        print(f"{c['comuna']}: máximo de condición alta o crítica {mx['p_alta']} % el {mx['fecha']}; T p50 {mx['t'][1]} °C, HR {mx['hr'][1]} %, viento {mx['v'][1]} km/h")
    import render_escenarios
    render_escenarios.render()


if __name__ == "__main__":
    main()
