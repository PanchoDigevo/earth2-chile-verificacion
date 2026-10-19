"""Datos de la pestaña "En vivo": rayos GOES-19 (sensor GLM, NOAA) de los últimos 90 minutos sobre la zona central
y METAR de las últimas 12 horas de Tobalaba, Pudahuel, Santo Domingo y Viña del Mar.

Corre cada 10 minutos en GitHub Actions (envivo.yml) y escribe rayos.json y metar.json en la carpeta indicada,
que el workflow guarda en la rama datos-en-vivo (un solo commit que se reemplaza, para no llenar el historial).
Es incremental: rayos.json guarda qué archivos GLM ya se procesaron. La página site/envivo.html los lee desde
raw.githubusercontent.com. No es un aviso; las alertas oficiales son de la DMC y SENAPRED.

Uso: python envivo/actualizar.py --salida datos/envivo"""
import argparse, datetime as dt, json, os, re, urllib.request
import netCDF4, numpy as np

LAT0, LAT1, LON0, LON1 = -38.5, -28.5, -74.5, -68.0
VENTANA_MIN = 90
GLM = "https://noaa-goes19.s3.amazonaws.com"
METAR = "https://aviationweather.gov/api/data/metar?ids=SCTB,SCEL,SCSN,SCVM&format=json&hours=12"
UA = {"User-Agent": "earth2-chile-verificacion/envivo"}


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


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--salida", required=True); a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    rayos(os.path.join(a.salida, "rayos.json")); metar(os.path.join(a.salida, "metar.json"))
