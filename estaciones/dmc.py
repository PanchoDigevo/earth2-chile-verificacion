"""Lector de la API de Servicios Climáticos de la DMC (estaciones meteorológicas automáticas, EMA).

La API pide usuario (el correo registrado) y token ("Token Web Services" del perfil), que se obtienen al registrarse en
https://climatologia.meteochile.gob.cl (lo hace Pancho; no se registran cuentas desde aquí). Se leen de las variables
de entorno DMC_USUARIO y DMC_TOKEN, que en GitHub Actions son secretos del repo. Si no están, el script termina sin
hacer nada, así el workflow sigue verde. Con el token solo, sin el correo, la API responde "bloqueado".

Una sola consulta (getDatosRecientesRedEma) trae las últimas 12 horas de toda la red (~137 estaciones, datos cada
10 minutos, ~8 MB). Se guarda solo la lectura de cada hora en punto, con temperatura, humedad, viento, presión y agua
caída, en un CSV por mes: estaciones/datos/dmc/AAAA-MM.csv (horas en UTC). Incluye estaciones que no envían SYNOP.

Uso: DMC_USUARIO=... DMC_TOKEN=... python estaciones/dmc.py"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "datos", "dmc")
API = "https://climatologia.meteochile.gob.cl/application/servicios/getDatosRecientesRedEma?{q}"
UA = {"User-Agent": "earth2-chile-verificacion/estaciones"}
# columna de salida -> campo de la API (los valores vienen como texto con unidad: "14.5 °C", "6.0 kt")
CAMPOS = {
    "t_c": "temperatura", "hr": "humedadRelativa", "td_c": "puntoDeRocio",
    "v10_kt": "fuerzaDelVientoPromedio10Minutos", "dir10": "direccionDelVientoPromedio10Minutos",
    "racha10_kt": "fuerzaDelViento10MinutosMax", "pnm_hpa": "presionNivelDelMar",
    "mm_6h": "aguaCaida6Horas", "mm_24h": "aguaCaida24Horas", "mm_min": "aguaCaidaDelMinuto",
    "tmax12": "temperaturaMaxima12Horas", "tmin12": "temperaturaMinima12Horas",
}
COLS = ["momento", "codigo", "nombre", "lat", "lon", "altura_m"] + list(CAMPOS)
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def get(url, intentos=3):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"sin respuesta ({i + 1}/{intentos}): {type(e).__name__}", flush=True)   # sin la URL: lleva el token
            time.sleep(20 * (i + 1))
    return None


def texto(v):
    """Nombres que la API entrega con los acentos dañados ("astronÃ³mico" -> "astronómico")."""
    s = str(v or "").strip()
    if "Ã" in s or "Â" in s:
        try:
            return s.encode("latin-1").decode("utf-8")
        except UnicodeError:
            pass
    return s


def numero(v):
    m = NUM.search(str(v)) if v not in (None, "") else None
    return m.group(0) if m else ""


def main():
    usuario, token = os.environ.get("DMC_USUARIO", "").strip(), os.environ.get("DMC_TOKEN", "").strip()
    if not usuario or not token:
        print("DMC: faltan DMC_USUARIO y DMC_TOKEN; no se consulta la API (se activa al cargar los secretos)")
        return 0
    resp = get(API.format(q=urllib.parse.urlencode({"usuario": usuario, "token": token})))
    if resp is None:
        print("DMC: la API no respondió"); return 0
    if "mensaje" in resp and "datosEstaciones" not in resp:
        print(f"DMC: {resp['mensaje']} (revisar que DMC_USUARIO sea el correo registrado y DMC_TOKEN el de su perfil)")
        return 0
    nuevas = {}
    for e in resp.get("datosEstaciones") or []:
        est = e.get("estacion") or {}
        for d in e.get("datos") or []:
            mom = str(d.get("momento") or "")
            if not mom.endswith(":00:00"):          # solo la hora en punto
                continue
            fila = {"momento": mom[:16], "codigo": est.get("codigoNacional"), "nombre": texto(est.get("nombreEstacion")),
                    "lat": est.get("latitud"), "lon": est.get("longitud"), "altura_m": est.get("altura")}
            fila.update({c: numero(d.get(k)) for c, k in CAMPOS.items()})
            nuevas[(fila["momento"], str(fila["codigo"]))] = fila
    if not nuevas:
        print("DMC: la API no entregó lecturas a la hora en punto; no se escribe nada"); return 0
    os.makedirs(CARPETA, exist_ok=True)
    total = 0
    for mes in sorted({k[0][:7] for k in nuevas}):
        ruta = os.path.join(CARPETA, f"{mes}.csv")
        filas = {}
        if os.path.exists(ruta):
            for r in csv.DictReader(open(ruta, encoding="utf-8")):
                filas[(r["momento"], r["codigo"])] = r
        filas.update({k: v for k, v in nuevas.items() if k[0][:7] == mes})
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore"); w.writeheader()
            for k in sorted(filas):
                w.writerow(filas[k])
        total += len(filas)
    print(f"DMC: {len(nuevas)} lecturas horarias de {len({k[1] for k in nuevas})} estaciones; "
          f"{total} filas en estaciones/datos/dmc/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
