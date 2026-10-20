"""Lector de la API de Servicios Climáticos de la DMC (estaciones meteorológicas automáticas, EMA).

La API pide usuario (el correo registrado) y token, que se obtienen al registrarse en
https://climatologia.meteochile.gob.cl (lo hace Pancho; no se registran cuentas desde aquí). Se leen de las variables
de entorno DMC_USUARIO y DMC_TOKEN, que en GitHub Actions son secretos del repo. Si no están, el script termina sin
hacer nada, así el workflow sigue verde.

Para cada estación DMC de catalogo.csv con código nacional pide los datos recientes (getDatosRecientesEma) y guarda
en estaciones/datos/dmc_reciente.csv las columnas de lluvia, nieve y temperatura que encuentre, sin la respuesta cruda.
Con el token también se pueden sumar estaciones que no envían SYNOP (por ejemplo Tobalaba): basta agregarlas al
catálogo con red DMC, su código nacional y lectura "dmc".

Uso: DMC_USUARIO=... DMC_TOKEN=... python estaciones/dmc.py"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "catalogo.csv")
CSV = os.path.join(AQUI, "datos", "dmc_reciente.csv")
API = "https://climatologia.meteochile.gob.cl/application/servicios/getDatosRecientesEma/{codigo}?{q}"
UA = {"User-Agent": "earth2-chile-verificacion/estaciones"}
INTERES = re.compile(r"agua|precip|lluvia|nieve|temperatura", re.I)


def get(url, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"sin respuesta ({i + 1}/{intentos}): {type(e).__name__}", flush=True)   # sin la URL: lleva el token
            time.sleep(15 * (i + 1))
    return None


def planos(obj, pref=""):
    """Aplana los diccionarios anidados de la respuesta ({"temperatura": {"valor": 3}} -> temperatura_valor)."""
    out = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            out.update(planos(v, f"{pref}{k}_"))
        elif not isinstance(v, list):
            out[f"{pref}{k}"] = v
    return out


def registros(resp):
    """Busca la lista de mediciones dentro de la respuesta, sin suponer su estructura exacta."""
    if isinstance(resp, list):
        if resp and isinstance(resp[0], dict) and any("momento" in k.lower() or "fecha" in k.lower() for k in resp[0]):
            return resp
        for x in resp:
            r = registros(x)
            if r:
                return r
    if isinstance(resp, dict):
        for v in resp.values():
            r = registros(v)
            if r:
                return r
    return []


def main():
    usuario, token = os.environ.get("DMC_USUARIO", "").strip(), os.environ.get("DMC_TOKEN", "").strip()
    if not usuario or not token:
        print("DMC: faltan DMC_USUARIO y DMC_TOKEN; no se consulta la API (se activa al cargar los secretos)")
        return 0
    q = urllib.parse.urlencode({"usuario": usuario, "token": token})
    est = [r for r in csv.DictReader(open(CATALOGO, encoding="utf-8")) if r["red"] == "DMC" and r["codigo"]]
    filas, columnas = [], {"codigo", "momento"}
    for e in est:
        resp = get(API.format(codigo=e["codigo"], q=q))
        if resp is None:
            continue
        if isinstance(resp, dict) and "mensaje" in resp and not registros(resp):
            print(f"DMC {e['codigo']} {e['nombre']}: {resp['mensaje']}")
            if "bloque" in str(resp["mensaje"]).lower():
                print("DMC: el usuario o el token no están habilitados; no se consultan las demás estaciones"); break
            continue
        n = 0
        for r in registros(resp):
            p = planos(r)
            mom = next((v for k, v in p.items() if "momento" in k.lower() or "fecha" in k.lower()), None)
            fila = {"codigo": e["codigo"], "momento": mom}
            fila.update({k: v for k, v in p.items() if INTERES.search(k)})
            columnas |= set(fila); filas.append(fila); n += 1
        print(f"DMC {e['codigo']} {e['nombre']}: {n} registros")
        time.sleep(2)
    if not filas:
        print("DMC: la API no entregó registros; no se escribe nada"); return 0
    previas = {}
    if os.path.exists(CSV):
        for r in csv.DictReader(open(CSV, encoding="utf-8")):
            previas[(r["codigo"], r["momento"])] = r; columnas |= set(r)
    for f in filas:
        previas[(f["codigo"], str(f["momento"]))] = f
    orden = ["codigo", "momento"] + sorted(columnas - {"codigo", "momento"})
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=orden, extrasaction="ignore"); w.writeheader()
        for k in sorted(previas, key=lambda k: (str(k[1]), k[0])):
            w.writerow(previas[k])
    print(f"DMC: {len(filas)} registros nuevos; {len(previas)} en {os.path.relpath(CSV)}. Columnas: {', '.join(orden[2:])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
