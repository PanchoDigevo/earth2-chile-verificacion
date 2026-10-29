"""Pronósticos de la Dirección Meteorológica de Chile (DMC), la referencia oficial, para verificarlos junto a AIFS, IFS y GFS.

Dos productos de meteochile.gob.cl:

1. El modelo WRF de la DMC, desde su servicio oficial getDatosModelo (pide usuario y token: secretos DMC_USUARIO y
   DMC_TOKEN). Entrega las últimas cinco corridas por estación con su día, hora (00 o 12 UTC) y condición de borde: GFS
   ("WRF-DMC") o ECMWF ("WRF-DMC-EC"), hora a hora en UTC: temperatura, viento (se supone en nudos; ver NUDO), humedad y agua caída en 6 h. Se guarda
   como modelo externo en data/puntos_<modelo>_<corrida>.csv (columnas modelo, run, lead_h, icao, t_fc, w_fc, tp_fc, rr6),
   que verify.py empareja con los METAR igual que a los demás modelos. Hasta el 29-oct-2026 se leía el meteograma público
   y la hora de corrida se suponía; el supuesto rotulaba mal la corrida de las 12 UTC y esos datos se borraron.
   2. El pronóstico oficial redactado por los meteorólogos de la DMC: mínima, máxima y tiempo por tramo del día (madrugada,
   mañana, tarde, noche) a 5 días para 103 localidades, en archivos.meteochile.gob.cl/portaldmc/meteochile/js/pronostico.js,
   el mismo archivo que alimenta la portada de meteochile.gob.cl. Se acumula en data/dmc_oficial.csv y lo verifica
   dmc_oficial.py contra la mínima, la máxima y la lluvia medidas en el aeródromo de cada localidad.

Se citan como "DMC". Uso: python fetch_dmc.py (lo llama verificacion.yml cuatro veces al día)."""
import csv, datetime as dt, glob, html, json, os, re, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "data")
UA = {"User-Agent": "earth2-chile-verificacion (github.com/PanchoDigevo/earth2-chile-verificacion)"}
SERVICIO = "https://climatologia.meteochile.gob.cl/application/serviciosb/getDatosModelo/{codigo}?{q}"
OFICIAL_URL = "https://archivos.meteochile.gob.cl/portaldmc/meteochile/js/pronostico.js"
# La DMC corre su WRF dos veces al día con dos condiciones de borde: GFS (NOAA) y ECMWF. Cada una es un "modelo" aparte.
FUENTES = {"gfs": "WRF-DMC", "ecmwf": "WRF-DMC-EC"}
# sigla del servicio -> variable (temperatura °C, viento, agua caída en 6 h mm)
VARIABLES = {"T": "t", "VV": "w", "RR6h": "rr6"}
# Viento: el meteograma lo rotula "m/s", pero el 29-oct-2026 los 20 primeros pares contra METAR daban sesgo +3,5 m/s en
# todas las estaciones (Calama 22,6 "m/s" con 12,9 medidos); leídos como nudos, sesgo -0,6 y error 1,5, como GFS e IFS.
# Supuesto declarado: vienen en nudos. Revisar con más días (verif_puntos.csv, modelo WRF-DMC).
NUDO = 0.514444
DIAS_PUNTOS, DIAS_OFICIAL = 3, 90

# Aeródromo METAR -> código nacional de la DMC de la estación del mismo lugar (126 estaciones tienen modelo).
WRF = {"SCAR": "180005", "SCDA": "200006", "SCCF": "220002", "SCFA": "230001", "SCAT": "270008", "SCSE": "290004",
       "SCER": "320056", "SCTB": "330019", "SCEL": "330021", "SCSN": "330030", "SCIC": "340031", "SCCH": "360011",
       "SCIE": "360019", "SCGE": "370033", "SCTC": "380013", "SCQP": "380029", "SCVD": "390006", "SCJO": "400009",
       "SCTE": "410005", "SCAS": "450001", "SCCY": "450004", "SCBA": "450005", "SCNT": "510005", "SCCI": "520006"}
# Localidad del pronóstico oficial -> aeródromo con METAR en esa ciudad (Santiago poniente = Pudahuel, oriente = Tobalaba).
# Caldera/Copiapó no se emparejan con SCAT (el aeródromo está a 25 km de una y 50 de la otra, en el desierto).
OFICIAL = {"arica": "SCAR", "iquique": "SCDA", "calama": "SCCF", "antofagasta": "SCFA", "serena": "SCSE", "snantonio": "SCSN",
           "stgop": "SCEL", "stgoo": "SCTB", "curico": "SCIC", "chillan": "SCCH", "concepcion": "SCIE", "angeles": "SCGE",
           "temuco": "SCQP", "valdivia": "SCVD", "osorno": "SCJO", "pmontt": "SCTE", "aysen": "SCAS", "coyhaique": "SCCY",
           "balmaceda": "SCBA", "natales": "SCNT", "parenas": "SCCI", "antartica": "SCRM"}
LLUVIA = re.compile(r"lluvia|llovizna|chubasco|precipitaci|aguanieve|nieve|tormenta", re.I)
TRAMOS = ("madrugada", "mañana", "tarde", "noche")


def bajar(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ---------- 1. modelo WRF de la DMC (servicio getDatosModelo, con usuario y token) ----------
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def corrida_de(clave, hoy):
    """'29_12_gfs' -> (datetime UTC de inicio, fuente). El servicio da solo el día del mes: si es mayor que hoy, es del mes pasado."""
    dia, hora, fuente = clave.split("_")
    d = hoy.replace(day=1) - dt.timedelta(days=1) if int(dia) > hoy.day else hoy
    return dt.datetime(d.year, d.month, int(dia), int(hora), tzinfo=dt.timezone.utc), fuente


def modelo_dmc(codigo, q, hoy):
    """{(inicio, fuente): {valid: {"t":, "w":, "rr6":}}} para una estación, desde el servicio oficial."""
    with urllib.request.urlopen(urllib.request.Request(SERVICIO.format(codigo=codigo, q=q), headers=UA), timeout=120) as r:
        j = json.loads(r.read().decode("utf-8"))
    if "elementos" not in j:
        raise LookupError(str(j.get("mensaje") or j.get("status") or "sin elementos")[:80])
    out = {}
    for el in j["elementos"]:
        var = VARIABLES.get((el.get("elemento") or {}).get("sigla"))
        if not var:
            continue
        for clave, c in el.items():
            if clave == "elemento" or not isinstance(c, dict):
                continue
            try:
                inicio, fuente = corrida_de(clave, hoy)
            except ValueError:
                continue
            serie = out.setdefault((inicio, fuente), {})
            for x in c.get("valorPronosticado") or []:
                valid = dt.datetime.fromtimestamp(int(x["timeStamp"]), dt.timezone.utc)
                serie.setdefault(valid, {})[var] = _num(x.get("valor"))
    return out


def puntos_wrf():
    """data/puntos_<WRF-DMC|WRF-DMC-EC>_<corrida>.csv con los plazos múltiplos de 6 h, como los demás modelos.

    El servicio recorta cada corrida a la hora actual: cada lectura agrega los plazos que faltan y se conservan los ya
    guardados. La lluvia (tp_fc) se arma sumando los acumulados de 6 h desde el primer plazo leído de la corrida; lluvia.py
    usa la diferencia entre plazos separados por 24 h, así que esa base común se cancela. Si falta un tramo de 6 h, la suma se
    corta ahí (sin tp_fc en adelante)."""
    usuario, token = os.environ.get("DMC_USUARIO", "").strip(), os.environ.get("DMC_TOKEN", "").strip()
    if not usuario or not token:
        print("WRF-DMC: faltan DMC_USUARIO y DMC_TOKEN; no se lee el modelo"); return 0
    q = urllib.parse.urlencode({"usuario": usuario, "token": token})
    hoy = dt.datetime.now(dt.timezone.utc).date()
    nuevas, fallas = {}, []          # (modelo, inicio) -> {(lead, icao): fila}
    for icao, codigo in WRF.items():
        try:
            corridas = modelo_dmc(codigo, q, hoy)
        except Exception as e:
            fallas.append(f"{icao} ({type(e).__name__})"); continue
        for (inicio, fuente), serie in corridas.items():
            modelo = FUENTES.get(fuente)
            if not modelo:
                continue
            for valid, v in serie.items():
                lead = (valid - inicio).total_seconds() / 3600
                if lead <= 0 or lead % 6 or v.get("t") is None or v.get("w") is None:
                    continue
                nuevas.setdefault((modelo, inicio), {})[(int(lead), icao)] = {
                    "modelo": modelo, "run": inicio.strftime("%Y-%m-%d %H:%M:%S"), "lead_h": int(lead), "icao": icao,
                    "t_fc": v["t"], "w_fc": round(v["w"] * NUDO, 2), "rr6": v.get("rr6")}
        time.sleep(1)
    if not nuevas:
        print("WRF-DMC: sin datos" + (f"; fallas: {', '.join(fallas)}" if fallas else "")); return 0
    total = 0
    for (modelo, inicio), filas in sorted(nuevas.items()):
        ruta = os.path.join(DATOS, f"puntos_{modelo}_{inicio:%Y%m%d_%H}.csv")
        todas = {}
        if os.path.exists(ruta):
            for r in csv.DictReader(open(ruta, encoding="utf-8")):
                todas[(int(r["lead_h"]), r["icao"])] = r
        todas.update(filas)
        for icao in {k[1] for k in todas}:              # acumulado de lluvia continuo desde el primer plazo leído
            acum, previo = 0.0, None
            for lead in sorted(k[0] for k in todas if k[1] == icao):
                f = todas[(lead, icao)]
                rr = _num(f.get("rr6"))
                if acum is not None and rr is not None and (previo is None or lead == previo + 6):
                    acum += rr; f["tp_fc"] = round(acum, 2)
                else:
                    acum = None; f["tp_fc"] = ""
                previo = lead
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["modelo", "run", "lead_h", "icao", "t_fc", "w_fc", "tp_fc", "rr6"], extrasaction="ignore")
            w.writeheader(); w.writerows(todas[k] for k in sorted(todas))
        total += len(filas)
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_PUNTOS)
    for modelo in FUENTES.values():
        for f in glob.glob(os.path.join(DATOS, f"puntos_{modelo}_*.csv")):
            try:
                if dt.datetime.strptime(os.path.basename(f)[len(modelo) + 8:-4], "%Y%m%d_%H").replace(tzinfo=dt.timezone.utc) < limite:
                    os.remove(f)
            except ValueError:
                pass
    print(f"WRF-DMC: {total} valores en {len(WRF) - len(fallas)} aeródromos; corridas "
          f"{', '.join(f'{m} {i:%d-%m %H}Z' for m, i in sorted(nuevas, key=lambda k: (k[1], k[0])))}"
          + (f"; sin datos: {', '.join(fallas)}" if fallas else ""))
    return total


# ---------- 2. pronóstico oficial (meteorólogos) ----------
def oficial():
    """Filas del pronóstico oficial: una por localidad y día, con la emisión que la redactó."""
    js = html.unescape(bajar(OFICIAL_URL))
    filas = []
    for ent in re.finditer(r"Pronostico\.push\(\{(.*?)\n\}\);", js, re.S):
        b = ent.group(1)
        campo = lambda k: (re.search(r"\n\s*" + k + r"\s*:\s*\"([^\"]*)\"", b) or re.search(r"^\s*" + k + r"\s*:\s*\"([^\"]*)\"", b))
        indice, ciudad = campo("indice"), campo("ciudad")
        fsql, emision = campo("fechasql"), campo("fechasqlredaccion")
        if not (indice and fsql and emision):
            continue
        # Cada arreglo termina donde empieza la clave siguiente ("],\n  icono :"); las listas internas terminan en "],\n   [".
        mt = re.search(r"\n\s*temperatura\s*:\s*\[(.*?)\]\s*,?\s*\n\s*\w+\s*:", b, re.S)
        mx = re.search(r"\n\s*texto\s*:\s*\[(.*?)\]\s*,?\s*\n\s*\w+\s*:", b, re.S)
        if not (mt and mx):
            continue
        temps = re.findall(r"\"([^\"]*)\"", mt.group(1))
        textos = [re.findall(r"\"([^\"]*)\"", d) for d in re.findall(r"\[(.*?)\]", mx.group(1), re.S)]
        try:
            dia0 = dt.date.fromisoformat(fsql.group(1))
        except ValueError:
            continue
        for k, tt in enumerate(temps):
            tmin, _, tmax = tt.partition("/")
            tramos = [t.strip() for t in textos[k]] if k < len(textos) else []
            if not any(tramos) and not tmin and not tmax:
                continue
            filas.append({"emision": emision.group(1), "indice": indice.group(1), "ciudad": ciudad.group(1) if ciudad else indice.group(1),
                          "icao": OFICIAL.get(indice.group(1), ""), "fecha": (dia0 + dt.timedelta(days=k)).isoformat(), "dia": k,
                          "tmin": tmin.strip(), "tmax": tmax.strip(), "lluvia": int(any(LLUVIA.search(t) for t in tramos)),
                          "texto": " / ".join(f"{n}: {t}" for n, t in zip(TRAMOS, tramos) if t)})
    return filas


def guardar_oficial(filas):
    ruta = os.path.join(DATOS, "dmc_oficial.csv")
    campos = ["emision", "indice", "ciudad", "icao", "fecha", "dia", "tmin", "tmax", "lluvia", "texto"]
    viejas = {}
    if os.path.exists(ruta):
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            viejas[(r["emision"], r["indice"], r["fecha"])] = r
    for r in filas:
        viejas[(r["emision"], r["indice"], r["fecha"])] = r
    limite = (dt.date.today() - dt.timedelta(days=DIAS_OFICIAL)).isoformat()
    todas = sorted((r for r in viejas.values() if r["fecha"] >= limite), key=lambda r: (r["emision"], r["indice"], r["fecha"]))
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos); w.writerow(dict(zip(campos, campos))); w.writerows(todas)
    emisiones = sorted({r["emision"] for r in filas})
    print(f"DMC oficial: {len(filas)} filas nuevas ({len({r['indice'] for r in filas})} localidades, emisión {emisiones[-1] if emisiones else '?'}); "
          f"{len(todas)} guardadas")


if __name__ == "__main__":
    os.makedirs(DATOS, exist_ok=True)
    errores = 0
    for nombre, fn in (("WRF-DMC", puntos_wrf), ("oficial", lambda: guardar_oficial(oficial()))):
        try:
            fn()
        except Exception as e:
            errores += 1; print(f"{nombre}: falló ({type(e).__name__}: {e})", flush=True)
    sys.exit(1 if errores == 2 else 0)
