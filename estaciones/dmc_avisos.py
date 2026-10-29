"""Avisos, alertas y alarmas vigentes de la DMC, por comuna, para el sitio (estaciones/datos/dmc_pron/avisos_vigentes.json).

Lo llama dmc_productos.py cada hora con el JSON del Sistema de Alerta Meteorológica de la DMC (AAA/datos_AAA.json). El
navegador lo lee desde la rama main (raw.githubusercontent.com) en Resumen, Tu zona, Pronóstico, En vivo y Quebradas.

Qué comunas toca cada uno, según cómo la DMC dibuja el área:
  - "zonas" (litoral, valle, precordillera, cordillera... de cada región): las comunas con al menos 10 % de su área en
    una de esas zonas, o con su cabecera dentro (cruce fijo en estaciones/dmc_zonas_comunas.csv, de zonas_dmc.py).
  - "area" (polígono libre): las comunas con su cabecera dentro o al menos 10 % de sus puntos de muestra
    (estaciones/comunas_muestras.csv); la parte, por la zona DMC de los puntos que caen dentro.
  - "regiones": todas las comunas de esas regiones (Isla de Pascua = ip, Juan Fernández = jf).
Para cada comuna se guardan las zonas tocadas ("cordillera", "valle"...), para decir qué parte de la comuna afecta.

Horario: la DMC lo escribe en texto ("la tarde del jueves 29 de octubre del 2026"); se pasa a hora de Chile con
madrugada 0-6, mañana 6-12, tarde 12-18 y noche 18-24 (desde = inicio del tramo; hasta = su fin). Si no se entiende,
queda vacío y el aviso se muestra mientras la DMC lo publique.

Son atribución de la DMC (y SENAPRED declara las alertas de protección civil): el sitio los copia tal cual, con su
nombre oficial, y enlaza a la fuente. No los modifica ni los emite."""
import csv, datetime as dt, html, json, os, re

try:
    from zoneinfo import ZoneInfo
    CHILE = ZoneInfo("America/Santiago")
except Exception:                                   # sin base de husos: verano de Chile
    CHILE = dt.timezone(dt.timedelta(hours=-3))

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "datos", "dmc_pron", "avisos_vigentes.json")
MESES = {m: i + 1 for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())}
TRAMOS = {"madrugada": (0, 6), "mañana": (6, 12), "manana": (6, 12), "tarde": (12, 18), "noche": (18, 24)}
ISLAS = {"Isla de Pascua": "ip", "Juan Fernández": "jf"}
MIN_FR = 0.10
ENLACE = "https://archivos.meteochile.gob.cl/portaldmc/AAA/aaa_mapa.php"


def plano(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(t or "")))).strip()


def momento(texto, fin=False):
    """'la tarde del jueves 29 de octubre del 2026' -> epoch (inicio o fin del tramo), o None."""
    t = plano(texto).lower()
    m = re.search(r"(madrugada|mañana|manana|tarde|noche)\D+?(\d{1,2}) de (\w+) del? (\d{4})", t)
    if not m or m.group(3) not in MESES:
        return None
    h0, h1 = TRAMOS[m.group(1)]
    d = dt.datetime(int(m.group(4)), MESES[m.group(3)], int(m.group(2)), tzinfo=CHILE)
    return int((d + dt.timedelta(hours=h1 if fin else h0)).timestamp())


def tabla(t):
    """tablaHTML -> [{region, dias, filas: [[zona, v1, v2...]]}]; una imagen en la celda = ocurre ("sí")."""
    bloques, actual = [], None
    for fila in re.findall(r"<tr[^>]*>(.*?)</tr>", str(t or ""), re.S):
        celdas = re.findall(r"<t([dh])[^>]*>(.*?)</t[dh]>", fila, re.S)
        vals = [("sí" if "<img" in c and not plano(c) else plano(c)) for _, c in celdas]
        if len(vals) == 1 and vals[0].lower().startswith("región"):
            actual = {"region": vals[0].split(":", 1)[-1].strip(), "dias": [], "filas": []}; bloques.append(actual)
        elif actual is not None and vals and vals[0].lower() == "zona":
            actual["dias"] = vals[1:]
        elif actual is not None and vals:
            actual["filas"].append(vals)
    return bloques


def _en_poligono(lat, lon, poli):
    dentro, n = False, len(poli)
    for i in range(n):
        (y1, x1), (y2, x2) = poli[i], poli[(i + 1) % n]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            dentro = not dentro
    return dentro


def _cargar():
    zonas, region, nombres = {}, {}, {}
    for r in csv.DictReader(open(os.path.join(AQUI, "dmc_zonas_comunas.csv"), encoding="utf-8")):
        nombres[r["id"]] = r["nombre"]
        if r["region_dmc"]:
            region[r["id"]] = r["region_dmc"]
        if float(r["fraccion"]) >= MIN_FR or r["centro"] == "1":
            zonas.setdefault(r["zona"], []).append(r["id"])
    for r in csv.DictReader(open(os.path.join(AQUI, "..", "verificacion", "comunas.csv"), encoding="utf-8")):
        nombres.setdefault(r["id"], r["nombre"])
        if r["nombre"] in ISLAS:
            region[r["id"]] = ISLAS[r["nombre"]]
    muestras = {}
    for r in csv.DictReader(open(os.path.join(AQUI, "comunas_muestras.csv"), encoding="utf-8")):
        muestras.setdefault(r["id"], []).append((float(r["lat"]), float(r["lon"]), r.get("zona", "")))
    return zonas, region, nombres, muestras


def parte(zona):
    """'05m_Valle_Longitudinal' -> 'valle'; '12_Insular_Sur' -> 'insular sur'."""
    z = zona.split("_", 1)[-1].replace("_", " ").lower()
    return {"valle longitudinal": "valle", "cordillera costa": "cordillera de la costa"}.get(z, z)


def comunas_de(a, zonas, region, muestras):
    """{id comuna: [partes]} afectadas por un aviso."""
    tipo, data = a.get("tipoZonaAfecta"), str(a.get("dataZonaAfecta") or "")
    out = {}
    if tipo == "zonas":
        for z in [x.strip() for x in data.split(",") if x.strip()]:
            for c in zonas.get(z, []):
                out.setdefault(c, []).append(parte(z))
    elif tipo == "regiones":
        regs = {x.strip() for x in data.split(",") if x.strip()}
        out = {c: [] for c, r in region.items() if r in regs}
    elif tipo == "area":
        poli = []
        for v in data.split("|"):
            try:
                la, lo = (float(x) for x in v.split(",")[:2]); poli.append((la, lo))
            except ValueError:
                pass
        if len(poli) >= 3:
            for c, pts in muestras.items():
                dentro = [_en_poligono(la, lo, poli) for la, lo, _ in pts]
                if dentro[0] or sum(dentro) >= MIN_FR * len(dentro):
                    zs = [z for (_, _, z), d in zip(pts, dentro) if d and z]          # partes: zonas con 2 o más puntos dentro
                    out[c] = [parte(z) for z in sorted(set(zs)) if zs.count(z) >= 2]
    return out


def vigentes(j, ahora=None):
    """Escribe avisos_vigentes.json desde el JSON de la DMC y devuelve un resumen en texto."""
    ahora = ahora or dt.datetime.now(dt.timezone.utc)
    zonas, region, nombres, muestras = _cargar()
    avisos = []
    for a in j.get("AAA") or []:
        cs = comunas_de(a, zonas, region, muestras)
        avisos.append({
            "id": str(a.get("id")), "tipo": plano(a.get("tipo")), "codigo": plano(a.get("codigoMeteo")),
            "fenomeno": plano(a.get("fenomeno")), "titulo": plano(a.get("titulo")), "emision": plano(a.get("emision")),
            "desde": plano(a.get("desde")), "hasta": plano(a.get("hasta")),
            "desde_ts": momento(a.get("desde")), "hasta_ts": momento(a.get("hasta"), fin=True),
            "condicion": plano(a.get("condicionSinoptica")), "observacion": plano(a.get("observacion")),
            "zonas_texto": [plano(z) for z in re.split(r"<br\s*/?>", str(a.get("textoZonaAfecta") or ""), flags=re.I) if plano(z)],
            "tabla_titulo": plano(a.get("tablaTitulo")), "tabla": tabla(a.get("tablaHTML")),
            "comunas": {c: sorted(set(p)) for c, p in sorted(cs.items())},
        })
    orden = {"Alarma": 0, "Alerta": 1, "Aviso": 2}
    avisos.sort(key=lambda x: (orden.get(x["tipo"], 3), x["desde_ts"] or 0))
    salida = {"generado": int(ahora.timestamp()), "actualizado_dmc": j.get("fecha_actualizacion"),
              "fuente": ENLACE, "conteo": {"Aviso": j.get("Avisos", 0), "Alerta": j.get("Alertas", 0), "Alarma": j.get("Alarmas", 0)},
              "nombres": {c: nombres[c] for c in sorted({c for x in avisos for c in x["comunas"]}) if c in nombres},
              "avisos": avisos}
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    json.dump(salida, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return f"{len(avisos)} vigentes en {len(salida['nombres'])} comunas"
