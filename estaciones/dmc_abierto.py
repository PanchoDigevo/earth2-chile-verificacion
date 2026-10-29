"""Servicios abiertos de la DMC (GeoJSON, sin usuario ni token) para las ~150 estaciones automáticas de su red:

1. Extremos del día (geoservicios/getClimatDiarioRecienteEmas): máxima, mínima y agua caída de hoy y de ayer. Se guarda
   solo "ayer", que ya está cerrado, en estaciones/datos/dmc_extremos.csv (una fila por día y estación). Con esto se
   verifica el pronóstico oficial de la DMC (verificacion/dmc_oficial.py).
2. Riesgo de incendio (geoservicios/getRiesgoIncendio): lo medido en las últimas 6 h (máxima, humedad mínima, viento
   máximo) y el pronóstico de la DMC para hoy y mañana de esos mismos tres ingredientes, los de la regla 30-30-30.
   - Pronóstico: estaciones/datos/dmc_riesgo_pron.csv, la primera lectura de cada día (no se reemplaza con lecturas
     posteriores, para no premiar una actualización hecha con el día ya avanzado).
   - Medido: estaciones/datos/dmc_riesgo_obs.csv, humedad mínima, viento máximo y máxima del día armados con las
     ventanas de 6 h de cada lectura horaria (las que terminan entre las 06 y las 24 UTC cubren el día completo menos
     su última hora); n = lecturas usadas.

Horas y días en UTC, como los entrega el servicio (el día va de las 21 h a las 21 h en Chile en horario de verano; la
máxima y la mínima caen el mismo día en ambas cuentas). Viento: el servicio no declara la unidad; por los valores se
supone km/h (la regla 30-30-30 usa km/h). Agua caída "s/p" = sin precipitación.

Lo llama estaciones.yml cada hora. Uso: python estaciones/dmc_abierto.py"""
import csv, datetime as dt, json, os, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "datos")
BASE = "https://climatologia.meteochile.gob.cl/application/geoservicios/"
UA = {"User-Agent": "earth2-chile-verificacion/estaciones (github.com/PanchoDigevo/earth2-chile-verificacion)"}
DIAS = 120
EXTREMOS = os.path.join(DATOS, "dmc_extremos.csv")
PRON = os.path.join(DATOS, "dmc_riesgo_pron.csv")
OBS = os.path.join(DATOS, "dmc_riesgo_obs.csv")
C_EXT = ["fecha", "codigo", "nombre", "lat", "lon", "altura_m", "comuna", "tmax", "tmin", "mm"]
C_PRON = ["emitido", "codigo", "fecha", "dia", "tmax", "hrmin", "vmax"]
C_OBS = ["fecha", "codigo", "tmax", "hrmin", "vmax", "n", "ultima"]


def bajar(servicio):
    with urllib.request.urlopen(urllib.request.Request(BASE + servicio, headers=UA), timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def limpio(s):
    """Algunos nombres llegan codificados dos veces ("SÃÂ¡nchez"): se deshace mientras se pueda."""
    s = (s or "").strip()
    for _ in range(3):
        if "Ã" not in s:
            break
        try:
            s = s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
    return s


def numero(v, sin_lluvia=False):
    if v is None or v == "":
        return ""
    if sin_lluvia and str(v).strip().lower() == "s/p":
        return 0.0
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return ""


def leer(ruta, clave):
    if not os.path.exists(ruta):
        return {}
    return {tuple(r[k] for k in clave): r for r in csv.DictReader(open(ruta, encoding="utf-8"))}


def escribir(ruta, filas, campos, orden):
    limite = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=DIAS)).isoformat()
    filas = sorted((f for f in filas if f["fecha"] >= limite), key=lambda f: tuple(f[k] for k in orden))
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); w.writerows(filas)
    return len(filas)


def extremos(ahora):
    if ahora.hour == 0:                       # en la primera hora UTC "ayer" puede ser todavía el día anterior del servicio
        print("DMC extremos: se omite la lectura de las 00 UTC"); return
    fecha = (ahora.date() - dt.timedelta(days=1)).isoformat()
    tabla = leer(EXTREMOS, ("fecha", "codigo"))
    n = 0
    for f in bajar("getClimatDiarioRecienteEmas")["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        fila = {"fecha": fecha, "codigo": str(p["codigoNacional"]), "nombre": limpio(p.get("nombreEstacion")),
                "lat": round(lat, 4), "lon": round(lon, 4), "altura_m": numero(p.get("altitud")), "comuna": limpio(p.get("comuna")),
                "tmax": numero(p.get("temperaturaMaximaAyer")), "tmin": numero(p.get("temperaturaMinimaAyer")),
                "mm": numero(p.get("aguaCaidaDiariaAyer"), sin_lluvia=True)}
        if fila["tmax"] == "" and fila["tmin"] == "" and fila["mm"] == "":
            continue
        tabla[(fecha, fila["codigo"])] = fila; n += 1
    total = escribir(EXTREMOS, tabla.values(), C_EXT, ("fecha", "codigo"))
    print(f"DMC extremos: {n} estaciones con datos del {fecha} (UTC); {total} filas guardadas")


def riesgo(ahora):
    datos = bajar("getRiesgoIncendio")["features"]
    pron, obs = leer(PRON, ("emitido", "codigo", "fecha")), leer(OBS, ("fecha", "codigo"))
    emitidos = {(r["emitido"][:10], r["codigo"], r["fecha"]) for r in pron.values()}
    nuevos_p = nuevos_o = 0
    for f in datos:
        p = f["properties"]
        codigo = str(p["CodigoNacional"])
        try:
            momento = dt.datetime.strptime(p["momento"], "%Y-%m-%d %H:%M:%S")
        except (KeyError, TypeError, ValueError):
            continue
        if ahora.replace(tzinfo=None) - momento > dt.timedelta(hours=3):      # estación sin datos recientes
            continue
        # pronóstico: la primera lectura de cada día de emisión
        for dia, suf in ((0, "Hoy"), (1, "Manana")):
            fecha = (momento.date() + dt.timedelta(days=dia)).isoformat()
            if (momento.date().isoformat(), codigo, fecha) in emitidos:
                continue
            fila = {"emitido": momento.strftime("%Y-%m-%d %H:%M"), "codigo": codigo, "fecha": fecha, "dia": dia,
                    "tmax": numero(p.get("temperaturaMaxima" + suf)), "hrmin": numero(p.get("humedadMinima" + suf)),
                    "vmax": numero(p.get("intensidadVientoMaximo" + suf))}
            if fila["tmax"] != "" or fila["hrmin"] != "" or fila["vmax"] != "":
                pron[(fila["emitido"], codigo, fecha)] = fila; nuevos_p += 1
        # medido: ventana de 6 h que termina en esta lectura, si cae entera dentro del día
        if momento.hour < 6:
            continue
        clave = (momento.date().isoformat(), codigo)
        o = obs.get(clave) or {"fecha": clave[0], "codigo": codigo, "tmax": "", "hrmin": "", "vmax": "", "n": 0, "ultima": ""}
        if o.get("ultima") == p["momento"]:   # la misma lectura ya se contó (el workflow corrió dos veces en la hora)
            continue
        for campo, fuente, mejor in (("tmax", "temperatura6h", max), ("hrmin", "humedad6h", min), ("vmax", "intensidadVientoMaximo6h", max)):
            v = numero(p.get(fuente))
            if v != "":
                o[campo] = v if o[campo] in ("", None) else mejor(float(o[campo]), v)
        o["n"] = int(o["n"]) + 1; o["ultima"] = p["momento"]
        obs[clave] = o; nuevos_o += 1
    tp = escribir(PRON, pron.values(), C_PRON, ("fecha", "codigo", "emitido"))
    to = escribir(OBS, obs.values(), C_OBS, ("fecha", "codigo"))
    print(f"DMC riesgo de incendio: {nuevos_p} pronósticos nuevos ({tp} guardados), {nuevos_o} lecturas medidas ({to} estación-día)")


if __name__ == "__main__":
    os.makedirs(DATOS, exist_ok=True)
    ahora = dt.datetime.now(dt.timezone.utc)
    for nombre, fn in (("extremos", extremos), ("riesgo", riesgo)):
        try:
            fn(ahora)
        except Exception as e:                # un servicio caído no detiene el otro ni el workflow
            print(f"DMC {nombre}: falló ({type(e).__name__}: {e})")
