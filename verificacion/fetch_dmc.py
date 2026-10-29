"""Pronósticos de la Dirección Meteorológica de Chile (DMC), la referencia oficial, para verificarlos junto a AIFS, IFS y GFS.

Dos productos públicos de meteochile.gob.cl, sin clave:

1. El modelo WRF de la DMC: meteograma por estación a 5 días, hora a hora (temperatura, lluvia, humedad, viento), en
   climatologia.meteochile.gob.cl/application/diarioe/graficoMeteogramaEstacion/<código nacional>. Se actualiza a las 08:00
   y 20:00 hora local. Se guarda como modelo externo "WRF-DMC" en data/puntos_WRF-DMC_<corrida>.csv (columnas modelo, run,
   lead_h, icao, t_fc, w_fc, tp_fc), que verify.py empareja con los METAR igual que a los demás modelos.
   - Las horas del meteograma vienen en hora de Chile (se comprobó con el ciclo diario: máxima a las 16 h); se pasan a UTC.
   - La DMC no publica la hora de inicio del modelo, solo la "fecha de generación de los datos" (UTC), que avanza cada hora
     porque la página recorta la serie a la hora actual. Supuesto (por confirmar con la DMC): la actualización de las 08:00
     usa la corrida de las 00 UTC y la de las 20:00, la de las 12 UTC; el plazo se cuenta desde ese inicio, igual que en los
     modelos globales.
   - La serie empieza en la hora de generación, no en el inicio del modelo: el acumulado de lluvia tp_fc solo se escribe en los
     plazos cuyas 24 h anteriores están completas en la serie, para que lluvia.py no reste un acumulado que no parte de cero.
2. El pronóstico oficial redactado por los meteorólogos de la DMC: mínima, máxima y tiempo por tramo del día (madrugada,
   mañana, tarde, noche) a 5 días para 103 localidades, en archivos.meteochile.gob.cl/portaldmc/meteochile/js/pronostico.js,
   el mismo archivo que alimenta la portada de meteochile.gob.cl. Se acumula en data/dmc_oficial.csv y lo verifica
   dmc_oficial.py contra la mínima, la máxima y la lluvia medidas en el aeródromo de cada localidad.

Se citan como "DMC". Uso: python fetch_dmc.py (lo llama verificacion.yml cuatro veces al día)."""
import csv, datetime as dt, glob, html, os, re, sys, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "data")
UA = {"User-Agent": "earth2-chile-verificacion (github.com/PanchoDigevo/earth2-chile-verificacion)"}
METEOGRAMA = "https://climatologia.meteochile.gob.cl/application/diarioe/graficoMeteogramaEstacion/{codigo}"
OFICIAL_URL = "https://archivos.meteochile.gob.cl/portaldmc/meteochile/js/pronostico.js"
MODELO = "WRF-DMC"
CHILE = dt.timezone(dt.timedelta(hours=-3))      # el meteograma viene en hora de Chile; en invierno (UTC-4) habría que revisarlo
DIAS_PUNTOS, DIAS_OFICIAL = 3, 90

# Aeródromo METAR -> código nacional de la DMC de la estación del mismo lugar (listado del meteograma, 126 estaciones).
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


# ---------- 1. modelo WRF de la DMC ----------
def arreglo(bloque, clave):
    m = re.search(r"\n\s*" + clave + r"\s*:\s*\[(.*?)\],?\n\s*\w+\s*:", bloque, re.S)
    if not m:
        return []
    return [x.strip().strip("'\"") for x in m.group(1).split(",")]


def meteograma(codigo):
    """Serie horaria del WRF para una estación: (generación UTC, [(valid UTC, t, mm, viento m/s), ...])."""
    pag = bajar(METEOGRAMA.format(codigo=codigo))
    i = pag.find("const data1"); j = pag.find("\n};", i)
    if i < 0 or j < 0:
        raise LookupError("sin datos en la página")
    bloque = pag[i:j + 3]
    horas = arreglo(bloque, "time"); temp = arreglo(bloque, "temperature"); lluvia = arreglo(bloque, "precipitation")
    mw = re.search(r"\n\s*wind\s*:\s*\[(.*?)\]\s*,?\n\s*\w+\s*:", bloque, re.S)        # [[m/s, grados], ...]
    viento = re.findall(r"\[\s*([-\d.]+)\s*,\s*[-\d.]+\s*\]", mw.group(1)) if mw else []
    g = re.search(r"generaci\S+ de los datos\s+(\d\d)-(\d\d)-(\d{4})\s+(\d\d):(\d\d)", html.unescape(pag))
    if not g or not horas:
        raise LookupError("sin hora de generación o sin horas")
    dd, mm, aa, hh, mi = (int(x) for x in g.groups())
    generado = dt.datetime(aa, mm, dd, hh, 0, tzinfo=dt.timezone.utc)
    serie = []
    for k, h in enumerate(horas):
        try:
            valid = dt.datetime.strptime(h, "%Y-%m-%d %H:%M:%S").replace(tzinfo=CHILE).astimezone(dt.timezone.utc)
            t = float(temp[k]) if k < len(temp) and temp[k] not in ("", "null") else None
            p = float(lluvia[k]) if k < len(lluvia) and lluvia[k] not in ("", "null") else None
            w = float(viento[k]) if k < len(viento) else None
        except (ValueError, IndexError):
            continue
        if t is not None:
            serie.append((valid, t, p, w))
    return generado, serie


def inicio(generado):
    """Corrida del WRF (supuesta) detrás de una generación: 00 UTC si se generó entre la actualización de las 08:00 y la de las
    20:00 (11 a 23 UTC en horario de verano), 12 UTC del día de la actualización si no."""
    if 11 <= generado.hour < 23:
        return generado.replace(hour=0, minute=0)
    dia = generado if generado.hour >= 23 else generado - dt.timedelta(days=1)
    return dia.replace(hour=12, minute=0)


def puntos_wrf():
    """data/puntos_WRF-DMC_<corrida>.csv con los plazos múltiplos de 6 h, como los demás modelos."""
    filas, fallas, corridas = [], [], set()
    for icao, codigo in WRF.items():
        try:
            generado, serie = meteograma(codigo)
        except Exception as e:
            fallas.append(f"{icao} ({type(e).__name__})"); continue
        generado = inicio(generado)
        corridas.add(generado)
        primera = serie[0][0]
        acum, acumulados = 0.0, {}
        for valid, t, p, w in serie:
            acum += p or 0.0
            acumulados[valid] = acum
        for valid, t, p, w in serie:
            lead = (valid - generado).total_seconds() / 3600
            if lead < 0 or lead % 6 or w is None:
                continue
            tp = acum_24 = None
            if valid - dt.timedelta(hours=24) >= primera:   # las 24 h anteriores están completas en la serie
                tp = round(acumulados[valid], 2)
            filas.append({"modelo": MODELO, "run": generado.strftime("%Y-%m-%d %H:%M:%S"), "lead_h": int(lead), "icao": icao,
                          "t_fc": t, "w_fc": w, "tp_fc": tp})
    if not filas:
        print("WRF-DMC: sin datos" + (f"; fallas: {', '.join(fallas)}" if fallas else "")); return 0
    # Cada estación puede venir de una generación distinta (08 o 20 h); un archivo por corrida.
    for run in sorted({f["run"] for f in filas}):
        ruta = os.path.join(DATOS, f"puntos_{MODELO}_{run[:13].replace('-', '').replace(' ', '_')}.csv")
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["modelo", "run", "lead_h", "icao", "t_fc", "w_fc", "tp_fc"]); w.writeheader()
            w.writerows(f for f in filas if f["run"] == run)
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_PUNTOS)
    for f in glob.glob(os.path.join(DATOS, f"puntos_{MODELO}_*.csv")):
        try:
            if dt.datetime.strptime(os.path.basename(f)[len(MODELO) + 8:-4], "%Y%m%d_%H").replace(tzinfo=dt.timezone.utc) < limite:
                os.remove(f)
        except ValueError:
            pass
    print(f"WRF-DMC: {len(filas)} valores en {len(WRF) - len(fallas)} aeródromos, generación "
          f"{', '.join(c.strftime('%d-%m %H:%M UTC') for c in sorted(corridas))}" + (f"; sin datos: {', '.join(fallas)}" if fallas else ""))
    return len(filas)


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
