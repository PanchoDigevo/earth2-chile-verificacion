"""Productos de pronóstico de la Dirección Meteorológica de Chile (DMC) que meteochile.gob.cl publica como datos, sin clave.

Cada hora (estaciones.yml) se guarda lo publicado, para tener el registro y poder verificarlo después. Un CSV por
producto en estaciones/datos/dmc_pron/ (horas en UTC salvo los textos de la DMC, que van como los escribe):

  aaa.csv           Sistema de Alerta Meteorológica: avisos, alertas y alarmas vigentes (AAA/datos_AAA.json). Una fila
                    por código; zonas y tabla de intensidad en texto plano. El área de cada uno (polígono o lista de
                    zonas) va en aaa_zonas.json, por id.
  cordillera.csv    Pronóstico de cordillera por región, 5 días, con la isoterma 0 °C (js/pronostico_cordillera.js).
  pasos.csv         Pronóstico de los pasos fronterizos, 5 días, con la apreciación sinóptica y la isoterma medida
                    (js/datos_pasos_fronterizos_<región>.js; Los Libertadores, con isoterma pronosticada, en
                    sim/ingreso/lib_form_pronostico_inc.js).
  uv.csv            Índice UV observado y pronosticado para mañana por estación (js/indice_radiacion.js).
  boletin.csv       Situación sinóptica y boletín de temperaturas, redactados por el meteorólogo de turno (js/boletin.js).
  turistico.csv     Pronóstico turístico de mañana para unos 25 lugares (js/pronosticos_especiales.js).

No se guardan aquí (son PDF o imágenes): cordillera zona sur, lagos, factor de ventilación, carta sinóptica, pronóstico
estacional. El pronóstico por ciudades lo guarda verificacion/fetch_dmc.py; lo medido, dmc_abierto.py y dmc.py.

Se cita como "DMC". Las alertas oficiales son de la DMC y SENAPRED: este proyecto las registra y enlaza, no las emite.
Uso: python estaciones/dmc_productos.py"""
import csv, datetime as dt, html, json, os, re, sys, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "datos", "dmc_pron")
BASE = "https://archivos.meteochile.gob.cl/portaldmc"
UA = {"User-Agent": "earth2-chile-verificacion (github.com/PanchoDigevo/earth2-chile-verificacion)"}
PASOS = {r: f"meteochile/js/datos_pasos_fronterizos_{r}.js" for r in
         ["aricaparinacota_v2", "tarapaca", "antofagasta_v2", "atacama_v2", "coquimbo", "maule_v2", "biobio",
          "araucania_v2", "losrios", "loslagos_v2", "aysen_norte", "aysen_sur", "magallanes"]}
PASOS["Valparaiso"] = "meteochile/sim/ingreso/lib_form_pronostico_inc.js"      # Complejo Los Libertadores, página propia
DIAS_GUARDA = 400
AHORA = dt.datetime.now(dt.timezone.utc)


def bajar(ruta, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(f"{BASE}/{ruta}", headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def plano(t):
    """Texto sin HTML ni entidades, en una línea."""
    t = re.sub(r"<br\s*/?>|</tr>|</p>", " · ", str(t or ""), flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"(\s*·\s*)+", " · ", re.sub(r"\s+", " ", t)).strip(" ·")


def variables(js):
    """var x = "..."; -> {x: texto}"""
    return {m.group(1): html.unescape(m.group(3)) for m in re.finditer(r"var\s+(\w+)\s*=\s*([\"'])(.*?)\2\s*;", js, re.S)}


def objetos(js, nombre):
    """Los objetos de nombre.push({ clave : "texto", lista : ["a", "b"], ... }) como diccionarios."""
    out = []
    for m in re.finditer(re.escape(nombre) + r"\.push\(\s*\{(.*?)\}\s*\)\s*;", js, re.S):
        b, d = m.group(1), {}
        for k in re.finditer(r"(\w+)\s*:\s*(\[(?:[^\[\]]|\[[^\]]*\])*\]|\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|true|false|-?[\d.]+)", b, re.S):
            v = k.group(2)
            if v.startswith("["):
                v = [html.unescape(a or b2) for a, b2 in re.findall(r"\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'", v)]
            elif v[0] in "\"'":
                v = html.unescape(v[1:-1])
            d[k.group(1)] = v
        out.append(d)
    return out


def fecha_de_dia(n, ref):
    """Número de día del mes ('Viernes 30') -> fecha, la más cercana a ref sin irse más de 20 días atrás."""
    for k in range(-20, 40):
        f = ref + dt.timedelta(days=k)
        if f.day == n:
            return f
    return None


def guardar(nombre, filas, clave, cols):
    """Une las filas nuevas con las guardadas (la nueva gana en la misma clave) y borra las de más de DIAS_GUARDA días."""
    ruta = os.path.join(CARPETA, nombre)
    todas = {}
    if os.path.exists(ruta):
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            todas[tuple(r[c] for c in clave)] = r
    nuevas = 0
    for f in filas:
        f = {c: "" if f.get(c) is None else str(f.get(c)) for c in cols}
        k = tuple(f[c] for c in clave)
        if k not in todas:
            nuevas += 1
        else:
            f["visto"] = todas[k].get("visto") or f["visto"]          # se conserva la primera vez que se vio
        todas[k] = f
    limite = (AHORA - dt.timedelta(days=DIAS_GUARDA)).strftime("%Y-%m-%d")
    filas = sorted((r for r in todas.values() if r.get("visto", "9") >= limite), key=lambda r: tuple(r[c] for c in clave))
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(filas)
    return nuevas, len(filas)


VISTO = AHORA.strftime("%Y-%m-%d %H:%M")


def aaa():
    j = json.loads(bajar("AAA/datos_AAA.json"))
    filas, zonas = [], {}
    for a in j.get("AAA") or []:
        filas.append({"visto": VISTO, "actualizado": j.get("fecha_actualizacion"), "id": a.get("id"), "tipo": a.get("tipo"),
                      "codigo": a.get("codigoMeteo"), "fenomeno": plano(a.get("fenomeno")), "emision": plano(a.get("emision")),
                      "desde": plano(a.get("desde")), "hasta": plano(a.get("hasta")),
                      "condicion": plano(a.get("condicionSinoptica")), "zonas": plano(a.get("textoZonaAfecta")),
                      "tabla": plano(a.get("tablaHTML")), "observacion": plano(a.get("observacion")), "titulo": plano(a.get("titulo"))})
        zonas[str(a.get("id"))] = {"codigo": a.get("codigoMeteo"), "tipo_zona": a.get("tipoZonaAfecta"), "zona": a.get("dataZonaAfecta")}
    ruta = os.path.join(CARPETA, "aaa_zonas.json")
    previas = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    previas.update(zonas)
    json.dump(previas, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    n = guardar("aaa.csv", filas, ["id"], ["id", "codigo", "tipo", "fenomeno", "emision", "desde", "hasta", "condicion", "zonas",
                                          "tabla", "observacion", "titulo", "actualizado", "visto"])
    return f"{j.get('Avisos', 0)} avisos, {j.get('Alertas', 0)} alertas, {j.get('Alarmas', 0)} alarmas vigentes; {n[0]} nuevos"


def cordillera():
    filas = []
    for o in objetos(bajar("meteochile/js/pronostico_cordillera.js"), "Cordillera"):
        try:
            d0 = dt.date.fromisoformat(o.get("fechasql", ""))
        except ValueError:
            continue
        for k, txt in enumerate(o.get("pronostico") or []):
            iso = (o.get("isoterma") or [""] * 5)[k] if k < len(o.get("isoterma") or []) else ""
            filas.append({"visto": VISTO, "redaccion": plano(o.get("redaccion")), "region": o.get("region"),
                          "nombre": plano(o.get("nombreregion")), "fecha": (d0 + dt.timedelta(days=k)).isoformat(), "dia": k,
                          "pronostico": plano(txt), "isoterma": iso})
    n = guardar("cordillera.csv", filas, ["redaccion", "region", "fecha"],
                ["redaccion", "region", "nombre", "fecha", "dia", "pronostico", "isoterma", "visto"])
    return f"{len({f['region'] for f in filas})} regiones; {n[0]} filas nuevas"


def pasos():
    filas, fallas, hoy = [], [], AHORA.date()
    for reg, ruta in PASOS.items():
        try:
            v = variables(bajar(ruta))
        except Exception as e:
            fallas.append(reg); continue
        # Las variables llevan sufijo de región (fechaemision_Magallanes), salvo Los Libertadores (fechaemision)
        suf = next((k[len("fechaemision"):] for k in v if k.startswith("fechaemision")), "")
        region = suf.lstrip("_") or reg
        dias = [d.strip() for d in v.get(f"PronoFechas{suf}", "").split(":")]
        iso_pron = v.get(f"PronoIsotermas{suf}", "").split(":")
        for k, val in v.items():
            if not k.startswith("Prono") or k.startswith(("PronoFechas", "PronoIsotermas")):
                continue
            for i, parte in enumerate(val.split(":")):
                icono, _, txt = parte.partition("|")
                if not txt.strip():
                    continue
                num = re.search(r"\d+", dias[i]) if i < len(dias) else None
                f = fecha_de_dia(int(num.group(0)), hoy) if num else None
                filas.append({"visto": VISTO, "region": region, "emision": plano(v.get(f"fechaemision{suf}")),
                              "apreciacion": plano(v.get(f"apreciacion{suf}")), "isoterma_medida": plano(v.get(f"iso_registrada{suf}")),
                              "isoterma_dia": plano(v.get(f"iso_fecha_registrada{suf}") or v.get(f"iso_registrada_cuando{suf}")),
                              "isoterma_pron": iso_pron[i] if i < len(iso_pron) else "", "paso": k[len("Prono"):],
                              "fecha": f.isoformat() if f else "", "dia": i, "icono": icono.replace(".png", ""), "pronostico": plano(txt)})
    n = guardar("pasos.csv", filas, ["emision", "region", "paso", "dia"],
                ["emision", "region", "paso", "fecha", "dia", "pronostico", "icono", "apreciacion", "isoterma_medida", "isoterma_dia", "isoterma_pron", "visto"])
    return f"{len({f['paso'] for f in filas})} pasos en {len(PASOS) - len(fallas)} regiones; {n[0]} filas nuevas" + \
        (f"; sin datos: {', '.join(fallas)}" if fallas else "")


def uv():
    filas = [{"visto": VISTO, "codigo": o.get("indice"), "nombre": plano(o.get("nombre")), "en_servicio": o.get("enservicio"),
              "fecha_obs": o.get("fechaobs"), "hora_obs": o.get("horaobs"), "uv_obs": o.get("indiceobs"),
              "fecha_pron": o.get("fechapron"), "uv_pron": o.get("indicepron")}
             for o in objetos(bajar("meteochile/js/indice_radiacion.js"), "RadiacionUVB")]
    n = guardar("uv.csv", filas, ["codigo", "fecha_obs", "fecha_pron"],
                ["codigo", "nombre", "en_servicio", "fecha_obs", "hora_obs", "uv_obs", "fecha_pron", "uv_pron", "visto"])
    return f"{len(filas)} estaciones; {n[0]} filas nuevas"


def boletin():
    v = variables(bajar("meteochile/js/boletin.js"))
    fila = {"visto": VISTO, "sit_fecha": plano(v.get("sit_fecha")), "sit_asunto": plano(v.get("sit_asunto")),
            "sit_descripcion": plano(v.get("sit_descripcion")), "tmp_fecha": plano(v.get("tmp_fecha")),
            "tmp_asunto": plano(v.get("tmp_asunto")), "tmp_descripcion": plano(v.get("tmp_descripcion"))}
    n = guardar("boletin.csv", [fila], ["sit_fecha", "tmp_fecha"],
                ["sit_fecha", "sit_asunto", "sit_descripcion", "tmp_fecha", "tmp_asunto", "tmp_descripcion", "visto"])
    return f"\"{fila['sit_asunto'][:60]}\"; {'nuevo' if n[0] else 'sin cambios'}"


def turistico():
    js = bajar("meteochile/js/pronosticos_especiales.js")
    fecha = variables(js).get("fecha", "")
    num = re.search(r"\d+", fecha)
    f = fecha_de_dia(int(num.group(0)), AHORA.date()) if num else None
    filas = [{"visto": VISTO, "fecha": f.isoformat() if f else fecha, "lugar": plano(o.get("lugar")), "pronostico": plano(o.get("pronostico"))}
             for o in objetos(js, "Turistico") if o.get("activo") != "false"]
    n = guardar("turistico.csv", filas, ["fecha", "lugar"], ["fecha", "lugar", "pronostico", "visto"])
    return f"{len(filas)} lugares para {fecha}; {n[0]} filas nuevas"


def main():
    os.makedirs(CARPETA, exist_ok=True)
    errores = 0
    for nombre, fn in (("avisos/alertas/alarmas", aaa), ("cordillera", cordillera), ("pasos fronterizos", pasos),
                       ("índice UV", uv), ("boletín", boletin), ("turístico", turistico)):
        try:
            print(f"DMC {nombre}: {fn()}", flush=True)
        except Exception as e:
            errores += 1; print(f"DMC {nombre}: falló ({type(e).__name__}: {e})", flush=True)
    return 1 if errores == 6 else 0


if __name__ == "__main__":
    sys.exit(main())
