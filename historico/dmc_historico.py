"""Lo medido en la red de estaciones automáticas de la DMC, para la verificación retroactiva en esas estaciones.

Usa la API de Servicios Climáticos de la DMC con los secretos DMC_USUARIO (correo de la cuenta) y DMC_TOKEN; sin ellos
no hace nada. Corre en GitHub Actions (historico-dmc.yml), nunca con el token a la vista.

  --catalogo                 getEstacionesRedEma -> historico/estaciones_dmc.csv (icao = "D" + código nacional, para que
                             extraer_puntos.py y el análisis las traten igual que a los aeródromos; nombre, lat, lon, elev).
  --desde AAAA-MM --hasta AAAA-MM
                             getDatosRecientesEma/<código>/<año>/<mes> (datos cada 15 minutos de un mes) de cada estación;
                             se guarda solo la lectura de las 00, 06, 12 y 18 UTC: temperatura, viento medio de 10 minutos y
                             su máximo (m/s) y humedad, en historico/data/dmc_obs/AAAA-MM.csv.gz.
  --probar                   describe la respuesta de una estación y un mes (claves y primeras filas, sin la URL).

Uso: DMC_USUARIO=... DMC_TOKEN=... python historico/dmc_historico.py --desde 2025-01 --hasta 2026-10"""
import argparse, csv, datetime as dt, gzip, json, os, re, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = "https://climatologia.meteochile.gob.cl/application/servicios/"
UA = {"User-Agent": "earth2-chile-verificacion/historico"}
SALIDA = os.path.join(AQUI, "data", "dmc_obs")
CATALOGO = os.path.join(AQUI, "estaciones_dmc.csv")
HORAS = {0, 6, 12, 18}
NUM = re.compile(r"-?\d+(?:\.\d+)?")
KT = 0.514444


def q():
    u, t = os.environ.get("DMC_USUARIO", "").strip(), os.environ.get("DMC_TOKEN", "").strip()
    if not u or not t:
        print("DMC: faltan DMC_USUARIO y DMC_TOKEN; no se consulta nada"); sys.exit(0)
    return urllib.parse.urlencode({"usuario": u, "token": t})


def get(ruta, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{BASE}{ruta}?{q()}", headers=UA), timeout=180) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            print(f"  sin respuesta ({i + 1}/{intentos}): {type(e).__name__}", flush=True)   # sin la URL: lleva el token
            time.sleep(15 * (i + 1))
    return None


def registros(x):
    """La lista de mediciones (diccionarios con 'momento') dentro de la respuesta, sin suponer su forma exacta."""
    if isinstance(x, list):
        if x and isinstance(x[0], dict) and "momento" in x[0]:
            return x
        for y in x:
            r = registros(y)
            if r:
                return r
    elif isinstance(x, dict):
        for y in x.values():
            r = registros(y)
            if r:
                return r
    return []


def num(v):
    m = NUM.search(str(v)) if v not in (None, "") else None
    return float(m.group(0)) if m else None


def viento(v):
    """'6.0 kt' -> m/s; si la unidad no es kt, se deja como viene."""
    x = num(v)
    return None if x is None else round(x * KT, 2) if "kt" in str(v).lower() else x


def catalogo():
    j = get("getEstacionesRedEma")
    filas = []
    for e in registros_est(j):
        cod = str(e.get("codigoNacional") or "").strip()
        if not cod:
            continue
        filas.append({"icao": "D" + cod, "nombre": e.get("nombreEstacion", ""), "lat": e.get("latitud"), "lon": e.get("longitud"),
                      "elev": e.get("altura", ""), "codigo": cod, "wmo": e.get("CodigoOMM") or e.get("codigoOMM") or "",
                      "oaci": e.get("codigoOACI", ""), "region": e.get("NombreRegion", ""), "zona": e.get("zonaGeografica", "")})
    if not filas:
        print("DMC catálogo: sin estaciones; claves de la respuesta:", list((j or {}).keys())[:12]); return
    with open(CATALOGO, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0])); w.writeheader(); w.writerows(filas)
    print(f"DMC catálogo: {len(filas)} estaciones en {os.path.relpath(CATALOGO)}")


def registros_est(x):
    """Lista de estaciones (diccionarios con codigoNacional) en cualquier parte de la respuesta."""
    if isinstance(x, list):
        if x and isinstance(x[0], dict) and "codigoNacional" in x[0]:
            return x
        for y in x:
            r = registros_est(y)
            if r:
                return r
    elif isinstance(x, dict):
        for y in x.values():
            r = registros_est(y)
            if r:
                return r
    return []


def meses(desde, hasta):
    a, m = map(int, desde.split("-")); a1, m1 = map(int, hasta.split("-"))
    while (a, m) <= (a1, m1):
        yield a, m
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)


def mes(a, m, estaciones):
    filas = []
    for k, e in enumerate(estaciones):
        j = get(f"getDatosRecientesEma/{e['codigo']}/{a}/{m:02d}")
        for r in registros(j):
            try:
                t = dt.datetime.strptime(str(r["momento"])[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if t.minute or t.hour not in HORAS:
                continue
            filas.append({"icao": e["icao"], "time": f"{t:%Y-%m-%d %H:%M}", "temp_c": num(r.get("temperatura")),
                          "viento_ms": viento(r.get("fuerzaDelVientoPromedio10Minutos")),
                          "racha_ms": viento(r.get("fuerzaDelViento10MinutosMax")), "hr": num(r.get("humedadRelativa"))})
        time.sleep(1)
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, f"{a}-{m:02d}.csv.gz")
    with gzip.open(ruta, "wt", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["icao", "time", "temp_c", "viento_ms", "racha_ms", "hr"]); w.writeheader(); w.writerows(filas)
    print(f"DMC {a}-{m:02d}: {len(filas)} lecturas de {len({f['icao'] for f in filas})} estaciones", flush=True)


def probar():
    j = get("getDatosRecientesEma/330020/2025/06")
    print("claves:", list(j.keys()) if isinstance(j, dict) else type(j).__name__)
    r = registros(j)
    print("registros:", len(r))
    for x in r[:2] + r[-1:]:
        print({k: v for k, v in x.items() if v not in (None, "")})
    j2 = get("getEstacionesRedEma")
    est = registros_est(j2)
    print("catálogo:", type(j2).__name__, list(j2.keys())[:10] if isinstance(j2, dict) else "", "estaciones:", len(est), est[:1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogo", action="store_true"); ap.add_argument("--probar", action="store_true")
    ap.add_argument("--desde"); ap.add_argument("--hasta")
    a = ap.parse_args()
    if a.probar:
        return probar()
    if a.catalogo:
        catalogo()
    if a.desde:
        est = list(csv.DictReader(open(CATALOGO, encoding="utf-8")))
        for an, m in meses(a.desde, a.hasta or a.desde):
            mes(an, m, est)


if __name__ == "__main__":
    main()
