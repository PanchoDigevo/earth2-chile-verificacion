"""Datos de la pestaña "En vivo": rayos GOES-19 (sensor GLM, NOAA) de los últimos 90 minutos sobre la zona central
las tormentas que se intensifican (salto de rayos, tormentas.json),
METAR de las últimas 12 horas de Tobalaba, Pudahuel, Santo Domingo y Viña del Mar, y la lluvia horaria de las
últimas 26 horas en las estaciones DMC cercanas a las quebradas (mensajes SYNOP, estaciones/synop.py).

Corre cada 10 minutos en GitHub Actions (envivo.yml) y escribe rayos.json, metar.json y lluvia.json en la carpeta indicada,
que el workflow guarda en la rama datos-en-vivo (un solo commit que se reemplaza, para no llenar el historial).
Es incremental: rayos.json guarda qué archivos GLM ya se procesaron. La página site/envivo.html los lee desde
raw.githubusercontent.com. No es un aviso; las alertas oficiales son de la DMC y SENAPRED.

Uso: python envivo/actualizar.py --salida datos/envivo"""
import argparse, datetime as dt, json, math, os, re, sys, urllib.request
import netCDF4, numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "estaciones"))
import synop  # noqa: E402
import salto_rayos  # noqa: E402

LAT0, LAT1, LON0, LON1 = -38.5, -28.5, -74.5, -68.0
VENTANA_MIN = 90
GLM = "https://noaa-goes19.s3.amazonaws.com"
METAR = "https://aviationweather.gov/api/data/metar?ids=SCTB,SCEL,SCSN,SCVM&format=json&hours=12"
UA = {"User-Agent": "earth2-chile-verificacion/envivo"}
APOQ = (-33.40, -70.51)
RADIO_KM = 45                 # estaciones de lluvia que se muestran: hasta esta distancia de Apoquindo, más El Colorado
CADA_MIN = 15                 # los SYNOP llegan cada hora: no hace falta pedirlos a Ogimet cada 5 minutos
COMUNAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verificacion", "comunas.csv")
ACTIVA_MIN = 30               # una tormenta con salto en los últimos 30 minutos se muestra como "intensificándose"
KM_CHILE = 25                 # tormentas a más de 25 km de toda comuna (casi siempre del lado argentino) no se marcan
REGISTRO_DIAS = 30


def get(url, timeout=60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print("sin respuesta:", url[:100], e, flush=True); return None


def inicio(clave):
    a, d, h, mi, s = map(int, re.search(r"_s(\d{4})(\d{3})(\d{2})(\d{2})(\d{2})", clave).groups())
    return dt.datetime(a, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=d - 1, hours=h, minutes=mi, seconds=s)


def rayos(ruta):
    previo = {}
    try:
        previo = json.load(open(ruta, encoding="utf-8"))
    except Exception:
        pass
    ahora = dt.datetime.now(dt.timezone.utc); limite = ahora - dt.timedelta(minutes=VENTANA_MIN)
    por_archivo = {k: v for k, v in (previo.get("por_archivo") or {}).items() if inicio(k) >= limite}
    claves = []
    for k in (2, 1, 0):
        t = ahora - dt.timedelta(hours=k)
        xml = get(f"{GLM}/?list-type=2&prefix=GLM-L2-LCFA/{t:%Y}/{t.timetuple().tm_yday:03d}/{t:%H}/")
        if xml:
            claves += re.findall(r"<Key>([^<]+)</Key>", xml.decode())
    nuevas = [c for c in claves if c not in por_archivo and inicio(c) >= limite]
    for c in nuevas:
        b = get(f"{GLM}/{c}")
        if not b:
            continue
        try:
            d = netCDF4.Dataset("glm", memory=b); la, lo = np.asarray(d["flash_lat"][:]), np.asarray(d["flash_lon"][:]); d.close()
        except Exception:
            continue
        m = (la >= LAT0) & (la <= LAT1) & (lo >= LON0) & (lo <= LON1)
        t = int(inicio(c).timestamp())
        por_archivo[c] = [[round(float(a), 3), round(float(o), 3), t] for a, o in zip(la[m], lo[m])]
    todos = [f for v in por_archivo.values() for f in v]
    json.dump({"generado": int(ahora.timestamp()), "ventana_min": VENTANA_MIN, "fuente": "NOAA GOES-19 GLM (GLM-L2-LCFA)",
               "rayos": todos, "por_archivo": por_archivo}, open(ruta, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"rayos: {len(nuevas)} archivos nuevos, {len(todos)} rayos en la zona en {VENTANA_MIN} min", flush=True)


def tormentas(ruta_rayos, ruta):
    """Saltos de rayos (salto_rayos.py) en los 90 minutos de rayos.json. Agrupa los de una misma tormenta (a menos de
    40 km) y le pone la comuna más cercana. Guarda además un registro de 30 días con cada tormenta marcada, para
    verificar después con lo que informen SENAPRED, la DMC o la prensa."""
    import csv
    ahora = dt.datetime.now(dt.timezone.utc).timestamp()
    rayos_ = [tuple(f) for f in json.load(open(ruta_rayos, encoding="utf-8"))["rayos"]]
    saltos = salto_rayos.detectar(rayos_, fin=ahora)
    com = [(r["nombre"], r["region"], float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(COMUNAS, encoding="utf-8"))]
    try:
        previo = json.load(open(ruta, encoding="utf-8"))
    except Exception:
        previo = {}
    registro = [r for r in previo.get("registro", []) if ahora - r["ultimo"] < REGISTRO_DIAS * 86400]
    grupos = []
    for s in saltos:
        p = (s["lat"], s["lon"])
        g = next((g for g in grupos if salto_rayos.km(p, g["pos"]) <= 40 and s["t"] - g["ultimo"] <= 1800), None)
        if g:
            g.update(ultimo=s["t"], pos=p, tasa=s["tasa"], saltos=g["saltos"] + 1, tasa_max=max(g["tasa_max"], s["tasa"]))
        else:
            grupos.append({"inicio": s["t"], "ultimo": s["t"], "pos": p, "tasa": s["tasa"], "tasa_max": s["tasa"], "saltos": 1})
    for g in grupos:
        c = min(com, key=lambda c: salto_rayos.km(g["pos"], (c[2], c[3])))
        g.update(lat=g["pos"][0], lon=g["pos"][1], comuna=c[0], region=c[1], km=round(salto_rayos.km(g["pos"], (c[2], c[3]))))
        del g["pos"]
        if g["km"] > KM_CHILE:
            continue
        # si la misma tormenta ya está en el registro (otra vuelta de 5 minutos), se actualiza en vez de repetirla
        r = next((r for r in registro if salto_rayos.km((g["lat"], g["lon"]), (r["lat"], r["lon"])) <= 40
                  and g["inicio"] - r["ultimo"] <= 1800 and g["ultimo"] >= r["inicio"]), None)
        if r:
            r.update(ultimo=max(r["ultimo"], g["ultimo"]), tasa_max=max(r["tasa_max"], g["tasa_max"]), lat=g["lat"], lon=g["lon"])
        else:
            registro.append({k: g[k] for k in ("inicio", "ultimo", "lat", "lon", "comuna", "region", "km", "tasa_max")})
    activas = [g for g in grupos if ahora - g["ultimo"] <= ACTIVA_MIN * 60 and g["km"] <= KM_CHILE]
    json.dump({"generado": int(ahora), "activa_min": ACTIVA_MIN,
               "metodo": "Salto de rayos, algoritmo 2σ de Schultz et al. (2009, 2011): tasa de al menos 10 rayos/min y aumento mayor que 2 desviaciones estándar de los 10 minutos previos",
               "activas": sorted(activas, key=lambda g: -g["ultimo"]), "registro": sorted(registro, key=lambda r: r["inicio"])},
              open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"tormentas: {len(saltos)} saltos en 90 min; intensificándose ahora: {', '.join(g['comuna'] for g in activas) or 'ninguna'}", flush=True)


def metar(ruta):
    b = get(METAR)
    if not b:
        return
    try:
        filas = json.loads(b)
    except Exception:
        return
    obs = [{"icao": r["icaoId"], "t": r.get("obsTime"), "temp": r.get("temp"), "wspd": r.get("wspd"), "wgst": r.get("wgst"),
            "wdir": r.get("wdir"), "wx": r.get("wxString") or "", "raw": r.get("rawOb", "")} for r in filas]
    json.dump({"generado": int(dt.datetime.now(dt.timezone.utc).timestamp()), "fuente": "METAR vía aviationweather.gov (NOAA)", "obs": obs},
              open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"metar: {len(obs)} reportes", flush=True)


def lluvia(ruta):
    try:
        previo = json.load(open(ruta, encoding="utf-8"))
        if dt.datetime.now(dt.timezone.utc).timestamp() - previo["generado"] < CADA_MIN * 60:
            print("lluvia: se mantiene la lectura de hace menos de 15 min", flush=True); return
    except Exception:
        pass
    r = math.pi / 180
    km = lambda la, lo: 111.2 * math.hypot(la - APOQ[0], (lo - APOQ[1]) * math.cos(APOQ[0] * r))
    est = []
    for w, e in synop.estaciones().items():
        d = km(float(e["lat"]), float(e["lon"]))
        if d <= RADIO_KM or w == "85594":
            est.append({"wmo": w, "nombre": e["nombre"], "lat": float(e["lat"]), "lon": float(e["lon"]), "alt": int(e["altura_m"]), "km": round(d, 1)})
    filas = synop.recientes(26)
    if not filas:
        print("lluvia: Ogimet no entregó datos; se mantiene la lectura anterior", flush=True); return
    obs = {}
    for f in filas:
        t = int(dt.datetime.strptime(f["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
        obs.setdefault(f["wmo"], {})[t] = [t, f["mm_1h"], f["mm_6h"], f["temp_c"]]
    json.dump({"generado": int(dt.datetime.now(dt.timezone.utc).timestamp()),
               "fuente": "Estaciones automáticas de la DMC, mensajes SYNOP de la OMM vía Ogimet (datos provisorios)",
               "estaciones": sorted(est, key=lambda e: e["km"]),
               "obs": {w: [v[t] for t in sorted(v)] for w, v in obs.items() if any(e["wmo"] == w for e in est)}},
              open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    llovio = sorted({f["wmo"] for f in filas if (f["mm_1h"] or 0) > 0 or (f["mm_6h"] or 0) > 0})
    print(f"lluvia: {len(filas)} reportes SYNOP; con lluvia en 26 h: {', '.join(llovio) or 'ninguna'}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--salida", required=True); a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    rayos(os.path.join(a.salida, "rayos.json")); metar(os.path.join(a.salida, "metar.json"))
    try:
        tormentas(os.path.join(a.salida, "rayos.json"), os.path.join(a.salida, "tormentas.json"))
    except Exception as e:
        print("tormentas: falló esta vuelta:", e, flush=True)
    try:
        lluvia(os.path.join(a.salida, "lluvia.json"))
    except Exception as e:                      # la lluvia no debe frenar los rayos ni el METAR
        print("lluvia: falló esta vuelta:", e, flush=True)
