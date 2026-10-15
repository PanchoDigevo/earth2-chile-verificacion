"""Genera ../site/index.html a partir de data/verif_puntos.csv (pares pronóstico-observación acumulados).

Uso: python render_site.py            -> regenera el sitio con lo que hay en data/
     desde verify.py: render_site(pts)

Compara tres modelos globales contra las mismas estaciones: AIFS (IA, ECMWF), IFS (físico, ECMWF) y GFS (físico, NOAA).
Diseño: una sola columna, resumen antes del detalle, mapa de Chile en tres franjas (norte, centro, sur) con selector
de modelo, tablas con barras de error y semáforo de tres niveles con texto (nunca solo color). Modo claro y oscuro.
Lenguaje: "aviso"/"pronóstico de impacto", nunca "alerta"; las alertas oficiales son de la DMC y SENAPRED."""
import json, math, os, re
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(AQUI, "..", "site")
CONTORNO = os.path.join(AQUI, "..", "docs", "chile_natural_earth_10m.json")
REPO = "https://github.com/PanchoDigevo/earth2-chile-verificacion"

# Nombre corto y región para cada aeródromo (el METAR trae nombres en inglés y con abreviaturas).
ESTACIONES = {
    "SCAR": ("Arica", "Arica y Parinacota"), "SCDA": ("Iquique", "Tarapacá"), "SCCF": ("Calama", "Antofagasta"),
    "SCFA": ("Antofagasta", "Antofagasta"), "SCAT": ("Caldera", "Atacama"), "SCSE": ("La Serena", "Coquimbo"),
    "SCER": ("Quintero", "Valparaíso"), "SCSN": ("Santo Domingo", "Valparaíso"), "SCEL": ("Santiago (Pudahuel)", "Metropolitana"),
    "SCTB": ("Tobalaba (Las Condes)", "Metropolitana"),
    "SCIC": ("Curicó", "Maule"), "SCCH": ("Chillán", "Ñuble"), "SCIE": ("Concepción", "Biobío"), "SCGE": ("Los Ángeles", "Biobío"),
    "SCTC": ("Temuco (Maquehue)", "La Araucanía"), "SCQP": ("Temuco (La Araucanía)", "La Araucanía"), "SCPC": ("Pucón", "La Araucanía"),
    "SCVD": ("Valdivia", "Los Ríos"), "SCJO": ("Osorno", "Los Lagos"), "SCTE": ("Puerto Montt", "Los Lagos"),
    "SCAS": ("Puerto Aysén", "Aysén"), "SCCY": ("Coyhaique", "Aysén"), "SCBA": ("Balmaceda", "Aysén"),
    "SCNT": ("Puerto Natales", "Magallanes"), "SCCI": ("Punta Arenas", "Magallanes"), "SCRM": ("Base Frei (Antártica)", "Antártica"),
}

# Modelos comparados, en orden de presentación. (nombre corto, tipo, centro)
MODELOS = {"AIFS": ("AIFS", "Inteligencia artificial", "ECMWF"), "IFS": ("IFS", "Modelo físico", "ECMWF"), "GFS": ("GFS", "Modelo físico", "NOAA")}
ORDEN = list(MODELOS)

# Umbrales del semáforo (error medio absoluto). Temperatura en °C, viento en m/s.
UMBRAL_T = (1.5, 3.0)
UMBRAL_BRECHA = 2.5     # "la brecha": estaciones con error medio de temperatura sobre este valor
MIN_PARES = 30          # por debajo de esto una estación se muestra como "preliminar", sin cifras
HIST_EST = os.path.join(AQUI, "..", "historico", "data", "resultados", "estaciones.csv")
UMBRAL_W = (1.5, 3.0)
NIVELES = {"bueno": "Bueno", "medio": "Aceptable", "alto": "Alto"}


def nivel(v, umbral):
    if pd.isna(v):
        return "sin"
    return "bueno" if v < umbral[0] else "medio" if v < umbral[1] else "alto"


def num(v, dec=1, unidad=""):
    """Número con coma decimal (convención chilena) y signo explícito solo si se pide."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + unidad


def signo(v, dec=1, unidad=""):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return ("+" if v > 0 else "") + num(v, dec, unidad)


def nombre(icao, fallback):
    if icao in ESTACIONES:
        return ESTACIONES[icao]
    n = str(fallback).split(",")[0].replace(" Arpt", "").replace(" Intl", "")
    return (n, "")


def chip(nv):
    if nv == "sin":
        return '<span class="chip sin">Sin datos</span>'
    if nv == "prelim":
        return '<span class="chip prelim">Preliminar</span>'
    return f'<span class="chip {nv}"><i aria-hidden="true"></i>{NIVELES[nv]}</span>'


def barra(v, vmax, nv):
    pct = 0 if pd.isna(v) else max(2, min(100, 100 * v / vmax))
    return f'<span class="bar {nv}" aria-hidden="true"><i style="width:{pct:.0f}%"></i></span>'


NARRATIVA = os.path.join(AQUI, "..", "docs", "narrativa_sitio.md")


def narrativa():
    """Lee docs/narrativa_sitio.md (fuente de verdad del mensaje público). Devuelve (html, aviso_final)."""
    import re
    try:
        texto = open(NARRATIVA, encoding="utf-8").read()
    except Exception:
        return "", ""
    if "\n---\n" in texto:
        texto = texto.split("\n---\n", 1)[1]
    inline = lambda t: re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t.strip())
    bloques, aviso, lista = [], "", []
    def cierra_lista():
        nonlocal lista
        if lista:
            bloques.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in lista) + "</ol>"); lista = []
    for parrafo in re.split(r"\n\s*\n", texto.strip()):
        parrafo = parrafo.strip()
        if not parrafo:
            continue
        if parrafo.startswith("## "):
            cierra_lista(); bloques.append(f"<h2>{inline(parrafo[3:])}</h2>")
        elif re.match(r"^\d+\.\s", parrafo):
            for linea in re.split(r"\n(?=\d+\.\s)", parrafo):
                lista.append(re.sub(r"^\d+\.\s+", "", linea.strip()))
        elif parrafo.startswith("*") and parrafo.endswith("*") and not parrafo.startswith("**"):
            cierra_lista(); aviso = inline(parrafo.strip("*"))
        else:
            cierra_lista(); bloques.append(f"<p>{inline(' '.join(parrafo.splitlines()))}</p>")
    cierra_lista()
    return "".join(bloques), aviso


def brecha_fuente(bye):
    """Estaciones con su error a 24 h para la cifra de portada. Prefiere el histórico 2025-2026 (AIFS, 24 h, >= MIN_PARES);
    si no existe, usa la verificación diaria. Devuelve (tabla icao/n/t_mae, texto de fuente, preliminar)."""
    try:
        h = pd.read_csv(HIST_EST)
        h = h[(h.modelo == "AIFS") & (h.lead_h == 24) & (h.n >= MIN_PARES)].rename(columns={"mae": "t_mae"})
        if len(h) >= 5:
            return h[["icao", "n", "t_mae"]].reset_index(drop=True), "histórico 2025–2026 (AIFS a 24 h)", False
    except Exception:
        pass
    d = bye[["icao", "n", "t_mae"]].reset_index(drop=True)
    ok = d[d.n >= MIN_PARES]
    if len(ok) >= 5:
        return ok, "verificación diaria (AIFS, todos los plazos)", False
    return d, "verificación diaria (AIFS, todos los plazos)", True


# ---------- mapa ----------
K = 20.0            # px por grado de latitud
LAT_TOP = -17.0
CX = 0.80           # cos(37°): compresión de la longitud a la latitud media de Chile
FRANJAS = [("Norte", -17.3, -30.6, -71.9, -66.9), ("Centro", -30.6, -43.9, -75.0, -70.0), ("Sur", -43.9, -56.2, -76.0, -66.0)]


def proj(lon, lat):
    return (lon + 76.0) * K * CX, (LAT_TOP - lat) * K


def contorno_path():
    try:
        anillos = json.load(open(CONTORNO))
    except Exception:
        return ""
    partes = []
    for anillo in anillos:
        if len(anillo) < 5:
            continue
        pts = [proj(lon, lat) for lon, lat in anillo]
        partes.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(partes)


def mapa(bye, modelo):
    """Tres franjas (norte, centro, sur) con las estaciones coloreadas por el error medio de temperatura de un modelo.
    El contorno de Chile se define una sola vez en la página (defs_contorno) y aquí se referencia con <use>."""
    svgs = []
    corto_m = MODELOS[modelo][0]
    for titulo, la0, la1, lo0, lo1 in FRANJAS:
        x0, y0 = proj(lo0, la0)
        x1, y1 = proj(lo1, la1)
        w, h = x1 - x0, y1 - y0
        puntos = []
        for r in bye.itertuples(index=False):
            if not (la1 <= r.lat <= la0 and lo0 <= r.lon <= lo1):
                continue
            x, y = proj(r.lon, r.lat)
            prelim = int(r.n) < MIN_PARES
            nv = "sin" if prelim else nivel(r.t_mae, UMBRAL_T)
            corto, _ = nombre(r.icao, r.name)
            etiqueta = f'<text x="{x + 7:.1f}" y="{y + 3.5:.1f}">{r.icao}</text>' if nv == "alto" else ""
            detalle = (f"preliminar: {int(r.n)} pares, se publica desde {MIN_PARES}" if prelim else
                       f"error medio de temperatura {num(r.t_mae, 1, ' °C')}, viento {num(r.w_mae, 1, ' m/s')}, {int(r.n)} pares")
            puntos.append(f'<g class="est {nv}"><title>{corto} ({r.icao}), {corto_m}: {detalle}</title>'
                          f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5"/>{etiqueta}</g>')
        svgs.append(f'<figure class="franja"><svg viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" '
                    f'role="img" aria-label="Mapa de la zona {titulo.lower()} de Chile con las estaciones, modelo {corto_m}">'
                    f'<use href="#chile" class="tierra"/>{"".join(puntos)}</svg><figcaption>{titulo}</figcaption></figure>')
    return f'<div class="mapa mapa-modelo" data-modelo="{modelo}">' + "".join(svgs) + "</div>"


def defs_contorno():
    path = contorno_path()
    if not path:
        return ""
    return f'<svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs><path id="chile" d="{path}"/></defs></svg>'


def mapas(bye_m):
    """Selector de modelo (botones de radio, sin JavaScript) y un mapa por modelo; se muestra el elegido."""
    defs = defs_contorno()
    if not defs:
        return ""
    presentes = [m for m in ORDEN if m in bye_m]
    botones = "".join(f'<label><input type="radio" name="mapa" id="mapa-{m}" value="{m}"{" checked" if i == 0 else ""}>'
                      f'{MODELOS[m][0]} <span class="muted">{MODELOS[m][1].split()[0].lower() if m != "AIFS" else "IA"}</span></label>'
                      for i, m in enumerate(presentes))
    cuerpo = "".join(mapa(bye_m[m], m) for m in presentes)
    return (f'<div class="mapas">{defs}<fieldset class="selector"><legend class="eyebrow">Modelo</legend>{botones}</fieldset>'
            f'{cuerpo}</div>')


# ---------- página ----------
CSS = """
/* Diseño: columna única de 1080 px, resumen antes del detalle; franjas de mapa + tablas con barras.
   Neutros fríos con leve sesgo azul (cielo y hielo), acento verde glaciar; semáforo fijo con texto. */
:root{
  --bg:#f4f6f8; --surface:#ffffff; --fg:#17212b; --muted:#5a6977; --line:#d8dfe6; --line-soft:#e9eef2;
  --accent:#0e7c86; --accent-soft:#d7eef0; --tierra:#e3e9ee; --costa:#9fb0bd;
  --bueno:#0ca30c; --medio:#c98500; --alto:#d03b3b; --sin:#8a99a6;
  --font-display:"Sora",system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-body:"Source Sans 3","Source Sans Pro",system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-data:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --radius:10px; color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#111821; --surface:#19222c; --fg:#e7ecf1; --muted:#9fadba; --line:#2c3845; --line-soft:#232e3a;
  --accent:#44bcc6; --accent-soft:#163b40; --tierra:#243040; --costa:#4f6071;
  --bueno:#2fbf2f; --medio:#e0a428; --alto:#ee6a6a; --sin:#7d8c99; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#111821; --surface:#19222c; --fg:#e7ecf1; --muted:#9fadba; --line:#2c3845; --line-soft:#232e3a;
  --accent:#44bcc6; --accent-soft:#163b40; --tierra:#243040; --costa:#4f6071;
  --bueno:#2fbf2f; --medio:#e0a428; --alto:#ee6a6a; --sin:#7d8c99; color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--fg);font-family:var(--font-body);font-size:17px;line-height:1.5;
  -webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}
.wrap{max-width:1080px;margin:0 auto;padding-inline:16px;padding-block:28px 56px;display:grid;gap:28px}
@media (min-width:720px){.wrap{padding-inline:28px;padding-block:40px 72px;gap:36px}}
h1,h2,h3{font-family:var(--font-display);text-wrap:balance;margin:0;letter-spacing:-.01em}
h1{font-size:clamp(26px,3.6vw,38px);line-height:1.15;font-weight:600;max-width:24ch}
h2{font-size:20px;font-weight:600}
h3{font-size:16px;font-weight:600}
p{margin:0;max-width:65ch}
.eyebrow{font-family:var(--font-display);font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-weight:600}
.muted{color:var(--muted)}
.nav{font-size:15px;max-width:none}
.small{font-size:14.5px}
header{display:grid;gap:12px}
header .lead{font-size:18px;color:var(--muted);max-width:62ch}
.aviso{border-left:3px solid var(--accent);padding:10px 14px;background:var(--accent-soft);border-radius:0 var(--radius) var(--radius) 0;max-width:72ch}
.aviso p{max-width:none}
.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media (min-width:600px){.tiles{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (min-width:960px){.tiles{grid-template-columns:repeat(6,minmax(0,1fr))}}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;display:grid;gap:4px;align-content:start}
.tile .label{font-size:13px;color:var(--muted)}
.tile .value{font-family:var(--font-display);font-size:30px;font-weight:600;line-height:1.1}
.tile .value small{font-size:15px;font-weight:500;color:var(--muted);margin-left:2px}
.tile .value.fecha{font-size:22px;line-height:1.2}
.tile.hero{grid-column:span 2;border-color:var(--accent)}
.tile.hero .value{font-size:44px}
.tile .foot{font-size:13px;color:var(--muted)}
section{display:grid;gap:14px}
.sec-head{display:grid;gap:4px}
.dos{display:grid;gap:24px}
@media (min-width:860px){.dos{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);align-items:start}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px;display:grid;gap:12px;min-width:0}
.leyenda{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:14px;color:var(--muted);align-items:center}
.leyenda span.item{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;padding:2px 9px 2px 7px;border-radius:999px;
  border:1px solid var(--line);background:var(--bg);color:var(--fg);white-space:nowrap}
.chip i{width:8px;height:8px;border-radius:50%;background:var(--sin)}
.chip.bueno i{background:var(--bueno)} .chip.medio i{background:var(--medio)} .chip.alto i{background:var(--alto)}
.chip.sin{color:var(--muted)}
.chip.prelim{color:var(--muted);border-style:dashed}
.mapa{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:flex-start;justify-content:center}
.franja{margin:0;display:grid;gap:4px;justify-items:center}
.franja svg{max-width:100%;height:auto;display:block}
.franja figcaption{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.tierra{fill:var(--tierra);stroke:var(--costa);stroke-width:.6;vector-effect:non-scaling-stroke}
.est circle{stroke:var(--surface);stroke-width:2;fill:var(--sin)}
.est.bueno circle{fill:var(--bueno)} .est.medio circle{fill:var(--medio)} .est.alto circle{fill:var(--alto)}
.est text{font:600 9px var(--font-data);fill:var(--fg)}
.est:hover circle{r:6.5}
.tabla{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:15px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line-soft);text-align:right;vertical-align:middle;white-space:nowrap}
th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line)}
th.l,td.l{text-align:left}
td.num{font-family:var(--font-data);font-size:14px;font-variant-numeric:tabular-nums}
td.est-nombre{white-space:normal;min-width:11em}
td.est-nombre .icao{font-family:var(--font-data);font-size:12.5px;color:var(--muted);margin-left:6px}
td.est-nombre .region{display:block;font-size:13px;color:var(--muted)}
td.medida{min-width:9.5em}
.medida-in{display:inline-grid;grid-template-columns:72px auto;gap:8px;align-items:center;justify-items:end}
.bar{display:block;width:72px;height:8px;border-radius:4px;background:var(--line-soft);overflow:hidden}
.bar i{display:block;height:100%;border-radius:4px;background:var(--sin)}
.bar.bueno i{background:var(--bueno)} .bar.medio i{background:var(--medio)} .bar.alto i{background:var(--alto)}
tbody tr:hover{background:color-mix(in srgb,var(--accent) 6%,transparent)}
.narrativa{display:grid;gap:12px;max-width:68ch}
header .narrativa{font-size:18px}
header .narrativa p{color:var(--fg)}
.narrativa h2{font-size:24px}
.narrativa p{max-width:none}
.narrativa ol{margin:0;padding-left:1.25em;display:grid;gap:8px}
.explica{display:grid;gap:10px}
.explica ol{margin:0;padding-left:1.2em;display:grid;gap:6px;max-width:65ch}
details{border:1px solid var(--line);border-radius:var(--radius);background:var(--surface);padding:0}
summary{cursor:pointer;padding:12px 16px;font-weight:600;font-family:var(--font-display);font-size:15px;list-style:none;display:flex;justify-content:space-between;gap:12px}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";color:var(--muted);font-weight:400}
details[open] summary::after{content:"–"}
details .body{padding:0 16px 16px;display:grid;gap:10px}
details .body p{max-width:72ch}
footer{border-top:1px solid var(--line);padding-top:20px;display:grid;gap:8px;font-size:14px;color:var(--muted)}
footer p{max-width:80ch}
@media (max-width:600px){.tile .value{font-size:26px}.tile.hero .value{font-size:38px}}
@media (prefers-reduced-motion:no-preference){.est circle{transition:r .15s ease}}
/* comparación de modelos */
.modelos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
@media (max-width:640px){.modelos{grid-template-columns:1fr}}
.modelo{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 16px;display:grid;gap:4px;align-content:start}
.modelo.ia{border-color:var(--accent)}
.modelo .tipo{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.modelo .nombre{font-family:var(--font-display);font-size:20px;font-weight:600}
.modelo .nombre small{font-size:14px;font-weight:500;color:var(--muted);margin-left:6px}
.modelo .value{font-family:var(--font-display);font-size:34px;font-weight:600;line-height:1.1}
.modelo .value small{font-size:15px;font-weight:500;color:var(--muted);margin-left:2px}
.modelo .foot{font-size:13px;color:var(--muted)}
.modelo .mejor{display:inline-block;font-size:12px;font-weight:600;color:var(--accent);background:var(--accent-soft);border-radius:999px;padding:1px 8px;margin-left:6px;vertical-align:middle}
.frase{font-size:18px;max-width:70ch}
.frase strong{color:var(--accent)}
/* selector de modelo del mapa */
.mapas{display:grid;gap:12px;position:relative}
.selector{display:flex;flex-wrap:wrap;gap:6px 8px;border:0;padding:0;margin:0;align-items:center}
.selector legend{float:left;margin-right:6px;padding:0}
.selector label{position:relative;cursor:pointer;border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:14px;font-weight:600;background:var(--bg)}
.selector label .muted{font-weight:400;font-size:13px}
.selector input{position:absolute;opacity:0;width:0;height:0;margin:0}
.selector label:has(input:checked){background:var(--accent-soft);border-color:var(--accent)}
.selector label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:2px}
.mapas:has(.selector) .mapa-modelo{display:none}
.mapas:has(#mapa-AIFS:checked) .mapa-modelo[data-modelo="AIFS"]{display:flex}
.mapas:has(#mapa-IFS:checked) .mapa-modelo[data-modelo="IFS"]{display:flex}
.mapas:has(#mapa-GFS:checked) .mapa-modelo[data-modelo="GFS"]{display:flex}
@supports not selector(:has(a)){.mapas .mapa-modelo{display:flex}.mapa-modelo::before{content:attr(data-modelo);width:100%;text-align:center;font-weight:600}}
/* tablas con fila por modelo */
td.plazo{font-weight:600;vertical-align:top}
tr.sep td{border-top:1px solid var(--line)}
td.modelo-nombre{font-weight:600}
td.modelo-nombre .tipo{display:block;font-size:12px;color:var(--muted);font-weight:400}
td.num.mejor{font-weight:700;color:var(--accent)}
th.grupo{text-align:center;border-bottom:0;padding-bottom:0}
"""


def etiqueta_modelo(m):
    corto, tipo, centro = MODELOS[m]
    return f"{corto} ({'IA' if m == 'AIFS' else 'físico'}, {centro})"


def render_site(pts):
    pts = pts.copy()
    if "modelo" not in pts.columns:
        pts.insert(0, "modelo", "AIFS")
    pts["modelo"] = pts["modelo"].fillna("AIFS")
    pts["run"] = pd.to_datetime(pts["run"])
    pts["valid"] = pd.to_datetime(pts["valid"])
    mae = lambda e: e.abs().mean()
    presentes = [m for m in ORDEN if m in set(pts.modelo)]
    ausentes = [m for m in ORDEN if m not in presentes]

    res = (pts.groupby(["modelo", "lead_h"]).agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae),
                                                 w_bias=("w_err", "mean"), w_mae=("w_err", mae)).reset_index().sort_values(["lead_h", "modelo"]))
    bye_all = (pts.groupby(["modelo", "icao"]).agg(name=("name", "first"), lat=("lat", "first"), lon=("lon", "first"), elev=("elev", "first"),
                                                   n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae), w_mae=("w_err", mae))
               .reset_index())
    bye_m = {m: bye_all[bye_all.modelo == m].sort_values("t_mae", ascending=False) for m in presentes}
    base = "AIFS" if "AIFS" in bye_m else presentes[0]
    bye = bye_m[base]
    estaciones = sorted(set(pts.icao))
    por_run = pts.pivot_table(index="run", columns="modelo", values="t_err", aggfunc=mae).sort_index()
    por_run_n = pts.groupby("run").size()

    runs = sorted(pts.run.unique())
    ultima = pd.Timestamp(runs[-1])
    n_runs = len(runs)
    ahora = pd.Timestamp.now("UTC")

    # Cifra principal (AIFS): error a 24 h si existe; si no, el plazo más largo disponible.
    res_base = res[res.modelo == base]
    fila_hero = res_base[res_base.lead_h == 24]
    if fila_hero.empty:
        fila_hero = res_base.iloc[[-1]]
    hero_lead = int(fila_hero.lead_h.iloc[0]); hero_mae = float(fila_hero.t_mae.iloc[0]); hero_n = int(fila_hero.n.iloc[0])
    hero_nv = nivel(hero_mae, UMBRAL_T)
    hero_txt = {"bueno": "Dentro de lo que un buen pronóstico puede ofrecer a esta escala.",
                "medio": "Aceptable para una grilla de 25 km; mejora con el downscaling.",
                "alto": "La grilla de 25 km no resuelve bien estos lugares."}[hero_nv]

    t_max = max(4.0, math.ceil(max(res.t_mae.max(), bye_all.t_mae.max()) + 0.01))
    w_max = max(4.0, math.ceil(max(res.w_mae.max(), bye_all.w_mae.max()) + 0.01))

    # --- comparación: plazo común a todos los modelos presentes (24 h si se puede) ---
    leads_por_modelo = [set(res[res.modelo == m].lead_h) for m in presentes]
    comunes = set.intersection(*leads_por_modelo) if leads_por_modelo else set()
    lead_cmp = 24 if 24 in comunes else (max(comunes) if comunes else hero_lead)
    cmp = {r.modelo: r for r in res[res.lead_h == lead_cmp].itertuples(index=False)}
    mejor = min((m for m in presentes if m in cmp), key=lambda m: cmp[m].t_mae, default=None)

    tarjetas = []
    for m in ORDEN:
        corto, tipo, centro = MODELOS[m]
        clase = "modelo ia" if m == "AIFS" else "modelo"
        if m in cmp:
            r = cmp[m]
            sello = '<span class="mejor">menor error</span>' if m == mejor and len(cmp) > 1 else ""
            tarjetas.append(f'<div class="{clase}"><div class="tipo">{tipo} · {centro}</div><div class="nombre">{corto}{sello}</div>'
                            f'<div class="value">{num(r.t_mae, 1)}<small>°C</small></div>'
                            f'<div class="foot">{chip(nivel(r.t_mae, UMBRAL_T))} &nbsp;Error medio de temperatura a {lead_cmp} h, {int(r.n)} pares. '
                            f'Viento {num(r.w_mae, 1, " m/s")}.</div></div>')
        else:
            motivo = "Todavía sin pares a este plazo." if m in presentes else "Entra en la próxima corrida del pipeline."
            tarjetas.append(f'<div class="{clase}"><div class="tipo">{tipo} · {centro}</div><div class="nombre">{corto}</div>'
                            f'<div class="value muted">–</div><div class="foot">{chip("sin")} &nbsp;{motivo}</div></div>')

    if len(cmp) >= 2 and "AIFS" in cmp:
        fisicos = [m for m in ("IFS", "GFS") if m in cmp]
        mejor_fis = min(fisicos, key=lambda m: cmp[m].t_mae)
        d = cmp["AIFS"].t_mae - cmp[mejor_fis].t_mae
        veredicto = (f"Hoy la IA va <strong>por delante</strong> del mejor modelo físico ({MODELOS[mejor_fis][0]}) por {num(abs(d), 1, ' °C')}." if d < -0.1 else
                     f"Hoy la IA va <strong>por detrás</strong> del mejor modelo físico ({MODELOS[mejor_fis][0]}) por {num(abs(d), 1, ' °C')}." if d > 0.1 else
                     f"Hoy la IA y el mejor modelo físico ({MODELOS[mejor_fis][0]}) están <strong>empatados</strong>.")
        partes = [f"la IA ({MODELOS['AIFS'][0]}) se equivoca en promedio <strong>{num(cmp['AIFS'].t_mae, 1, ' °C')}</strong> en la temperatura"]
        partes += [f"el modelo físico de {MODELOS[m][2]} ({MODELOS[m][0]}) {num(cmp[m].t_mae, 1, ' °C')}" for m in fisicos]
        frase = f"A {lead_cmp} h de anticipación, " + "; ".join(partes) + f". {veredicto}"
    elif "AIFS" in cmp:
        frase = (f"A {lead_cmp} h de anticipación, la IA ({MODELOS['AIFS'][0]}) se equivoca en promedio <strong>{num(cmp['AIFS'].t_mae, 1, ' °C')}</strong> "
                 f"en la temperatura. Los modelos físicos (IFS y GFS) aparecerán aquí en cuanto tengan pares al mismo plazo.")
    else:
        frase = "La comparación aparecerá cuando los tres modelos tengan pares al mismo plazo."
    nota_cmp = (f"Se compara al plazo de {lead_cmp} h porque es el más largo que ya tienen los tres modelos; a medida que lleguen las observaciones, pasa a 24 h."
                if lead_cmp != 24 and len(cmp) > 1 else "")

    # --- tabla por plazo: una fila por plazo y modelo ---
    filas_plazo = []
    for lead, grupo in res.groupby("lead_h", sort=True):
        grupo = grupo.set_index("modelo").reindex([m for m in ORDEN if m in grupo.modelo.values])
        mejor_lead = grupo.t_mae.idxmin() if len(grupo) > 1 else None
        for i, (m, r) in enumerate(grupo.iterrows()):
            nt, nw = nivel(r.t_mae, UMBRAL_T), nivel(r.w_mae, UMBRAL_W)
            celda_plazo = f"<td class='l num plazo' rowspan='{len(grupo)}'>{int(lead)} h</td>" if i == 0 else ""
            filas_plazo.append(
                f"<tr class='{'sep' if i == 0 else ''}'>{celda_plazo}"
                f"<td class='l modelo-nombre'>{MODELOS[m][0]}<span class='tipo'>{'IA' if m == 'AIFS' else 'físico'} · {MODELOS[m][2]}</span></td>"
                f"<td class='num'>{int(r.n)}</td>"
                f"<td class='medida'><span class='medida-in'>{barra(r.t_mae, t_max, nt)}<span class='num{' mejor' if m == mejor_lead else ''}'>{num(r.t_mae, 2, ' °C')}</span></span></td>"
                f"<td class='num'>{signo(r.t_bias, 2, ' °C')}</td>"
                f"<td class='medida'><span class='medida-in'>{barra(r.w_mae, w_max, nw)}<span class='num'>{num(r.w_mae, 2, ' m/s')}</span></span></td>"
                f"<td class='num'>{signo(r.w_bias, 2, ' m/s')}</td><td>{chip(nt)}</td></tr>")
    plazos_pend = [h for h in (0, 6, 12, 18, 24, 36, 48) if h not in set(res.lead_h)]
    nota_plazos = (f"Los plazos de {', '.join(str(h) for h in plazos_pend)} h aparecerán a medida que las observaciones alcancen "
                   f"las horas pronosticadas." if plazos_pend else "")

    # --- tabla por estación: base AIFS, columnas de error de temperatura por modelo ---
    tmae_m = {m: bye_m[m].set_index("icao").t_mae for m in presentes}
    n_m = {m: bye_m[m].set_index("icao").n for m in presentes}
    filas_est = []
    orden_est = list(bye.icao) + [i for i in estaciones if i not in set(bye.icao)]
    info = bye_all.drop_duplicates("icao").set_index("icao")
    for icao in orden_est:
        r = bye.set_index("icao").loc[icao] if icao in set(bye.icao) else None
        corto, region = nombre(icao, info.loc[icao, "name"])
        elev_v = info.loc[icao, "elev"]
        elev = "" if pd.isna(elev_v) else f"{int(float(elev_v))} m"
        vals = {m: (float(tmae_m[m].get(icao, float("nan"))) if int(n_m[m].get(icao, 0)) >= MIN_PARES else float("nan")) for m in presentes}
        validos = {m: v for m, v in vals.items() if not math.isnan(v)}
        mejor_est = min(validos, key=validos.get) if len(validos) > 1 else None
        celdas = ""
        for m in ORDEN:
            v = vals.get(m, float("nan"))
            if math.isnan(v):
                celdas += "<td class='num muted'>–</td>"
            else:
                celdas += (f"<td class='medida'><span class='medida-in'>{barra(v, t_max, nivel(v, UMBRAL_T))}"
                           f"<span class='num{' mejor' if m == mejor_est else ''}'>{num(v, 1, ' °C')}</span></span></td>")
        prelim = r is None or int(r.n) < MIN_PARES
        nt = "prelim" if prelim else nivel(r.t_mae, UMBRAL_T)
        if prelim and r is not None:
            r = r.copy(); r[["t_bias", "w_mae"]] = float("nan")
        filas_est.append(
            f"<tr><td class='l est-nombre'>{corto}<span class='icao'>{icao}</span>"
            f"<span class='region'>{region}{' · ' if region and elev else ''}{elev}</span></td>"
            f"<td class='num'>{int(r.n) if r is not None else 0}</td>{celdas}"
            f"<td class='num'>{signo(r.t_bias, 1, ' °C') if r is not None else '–'}</td>"
            f"<td class='medida'><span class='medida-in'>{barra(r.w_mae, w_max, nivel(r.w_mae, UMBRAL_W)) if r is not None else ''}<span class='num'>{num(r.w_mae, 1, ' m/s') if r is not None else '–'}</span></span></td>"
            f"<td>{chip(nt)}</td></tr>")
    cab_modelos = "".join(f"<th>Error temp. {MODELOS[m][0]}</th>" for m in ORDEN)

    bye_ok = bye[bye.n >= MIN_PARES]
    n_alto = int((bye_ok.t_mae >= UMBRAL_T[1]).sum()); n_bueno = int((bye_ok.t_mae < UMBRAL_T[0]).sum())
    brecha, brecha_fuente_txt, brecha_prelim = brecha_fuente(bye)
    brecha_est = brecha[brecha.t_mae >= UMBRAL_BRECHA].sort_values("t_mae", ascending=False)
    brecha_nombres = ", ".join(f"{nombre(i, i)[0]} ({num(v, 1)} °C)" for i, v in zip(brecha_est.icao, brecha_est.t_mae))
    sesgo_global = float(pts[pts.modelo == base].t_err.mean())
    frio_calor = "frío (el modelo pronostica más frío de lo observado)" if sesgo_global < -0.3 else \
                 "cálido (el modelo pronostica más calor de lo observado)" if sesgo_global > 0.3 else "casi nulo"

    # --- serie por corrida (cuando haya más de una): una columna por modelo ---
    serie = ""
    if n_runs >= 2:
        cab = "".join(f"<th>{MODELOS[m][0]}</th>" for m in presentes)
        filas = []
        for run, fila in por_run.tail(30).iterrows():
            celdas = ""
            for m in presentes:
                v = fila.get(m, float("nan"))
                celdas += ("<td class='num muted'>–</td>" if pd.isna(v) else
                           f"<td class='medida'><span class='medida-in'>{barra(v, t_max, nivel(v, UMBRAL_T))}<span class='num'>{num(v, 2, ' °C')}</span></span></td>")
            filas.append(f"<tr><td class='l num'>{pd.Timestamp(run):%d-%m %H}z</td><td class='num'>{int(por_run_n[run])}</td>{celdas}</tr>")
        serie = f"""<section>
  <div class="sec-head"><h2>Corrida por corrida</h2>
  <p class="muted">Error medio de temperatura de cada corrida, por modelo, con todos los plazos y estaciones juntos. Últimas {min(30, n_runs)} corridas.</p></div>
  <div class="card tabla"><table><thead><tr><th class="l">Corrida (UTC)</th><th>Pares</th>{cab}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>
</section>"""

    narr_html, narr_aviso = narrativa()
    m_narr = re.match(r"\s*<h2>(.*?)</h2>(.*)$", narr_html, flags=re.S) if narr_html else None
    narr_titulo = m_narr.group(1) if m_narr else "¿Qué tan bien acierta el pronóstico de IA en Chile?"
    narr_cuerpo = m_narr.group(2) if m_narr else ""
    MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    fecha_ultima = f"{ultima.day} {MESES[ultima.month - 1]} · {ultima:%H} UTC"
    generado = f"{ahora.day} {MESES[ahora.month - 1]} {ahora.year}, {ahora:%H:%M} UTC"
    n_est = len(estaciones)
    lista_modelos = ", ".join(etiqueta_modelo(m) for m in presentes)

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Verificación Earth-2 Chile</title>
<meta name="description" content="Cada día comparamos el pronóstico de inteligencia artificial de ECMWF (AIFS) y los modelos físicos IFS (ECMWF) y GFS (NOAA) con lo que midieron los aeródromos de Chile. Error por plazo y por estación, en lenguaje simple.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="eyebrow">Earth-2 Chile · verificación diaria</div>
  <h1>{narr_titulo}</h1>
  {f'<div class="narrativa">{narr_cuerpo}</div>' if narr_cuerpo else f'<p class="lead">Cada día comparamos AIFS (IA, ECMWF), IFS (ECMWF) y GFS (NOAA) con lo que midieron {n_est} aeródromos del país.</p>'}
  <div class="aviso"><p class="small">Esta página es apoyo a la decisión y verificación pública de modelos. Las alertas oficiales son de la
  <a href="https://www.meteochile.gob.cl/" rel="noopener">Dirección Meteorológica de Chile</a> y de
  <a href="https://www.senapred.cl/" rel="noopener">SENAPRED</a>.</p></div>
  <p class="nav"><a href="historico.html">Verificación retroactiva 2025–2026: qué decían los modelos 72, 48 y 24 h antes →</a><br><a href="quebradas.html">Visor de quebradas de Santiago oriente: laderas quemadas, pendiente y lluvia prevista por cuenca →</a></p>
</header>

<section>
  <div class="tiles">
    <div class="tile hero">
      <div class="label">La brecha: estaciones donde el pronóstico global se equivoca más de {num(UMBRAL_BRECHA)} °C</div>
      <div class="value">{len(brecha_est)}<small>de {len(brecha)}</small></div>
      <div class="foot">{chip("prelim") if brecha_prelim else (chip("alto") if len(brecha_est) else chip("bueno"))} &nbsp;{brecha_nombres if len(brecha_est) else "Ninguna por ahora."}
      Fuente: {brecha_fuente_txt}{f"; preliminar, aún con menos de {MIN_PARES} pares por estación" if brecha_prelim else ""}.</div>
    </div>
    <div class="tile"><div class="label">Última corrida verificada</div><div class="value fecha">{fecha_ultima}</div><div class="foot">{ultima.year}. Los modelos corren 4 veces al día.</div></div>
    <div class="tile"><div class="label">Corridas acumuladas</div><div class="value">{n_runs}</div><div class="foot">Desde el {pd.Timestamp(runs[0]).day} {MESES[pd.Timestamp(runs[0]).month - 1]} {pd.Timestamp(runs[0]).year}</div></div>
    <div class="tile"><div class="label">Pares pronóstico–observación</div><div class="value">{len(pts)}</div><div class="foot">{n_est} estaciones · {len(presentes)} modelo{'s' if len(presentes) != 1 else ''}</div></div>
    <div class="tile"><div class="label">Error medio de {MODELOS[base][0]} a {hero_lead} h</div><div class="value">{num(hero_mae, 1)}<small>°C</small></div><div class="foot">{chip("prelim") if hero_n < MIN_PARES else chip(hero_nv)} {hero_n} pares, todas las estaciones.</div></div>
  </div>
</section>

<section class="dos">
  <div class="card">
    <div class="sec-head"><h2>Dónde acierta y dónde no</h2>
    <p class="muted small">Error medio de temperatura por estación. Elige el modelo y pasa el cursor sobre un punto para ver el detalle.</p></div>
    {mapas(bye_m)}
    <div class="leyenda"><span class="item">{chip("bueno")} menos de {num(UMBRAL_T[0])} °C</span><span class="item">{chip("medio")} {num(UMBRAL_T[0])} a {num(UMBRAL_T[1])} °C</span><span class="item">{chip("alto")} {num(UMBRAL_T[1])} °C o más</span></div>
  </div>
  <div class="explica">
    <h2>Cómo leer esta página</h2>
    <ol>
      <li><strong>Error medio</strong> es cuánto se equivocó el modelo en promedio, sin importar el signo. Si dice 1,5 °C, el pronóstico estuvo típicamente un grado y medio arriba o abajo de lo medido.</li>
      <li><strong>Sesgo</strong> es la dirección del error. Negativo: el modelo pronostica más frío de lo que ocurre. Hoy el sesgo global de {MODELOS[base][0]} es {signo(sesgo_global, 1, " °C")}, {frio_calor}.</li>
      <li><strong>Plazo</strong> es cuántas horas antes se hizo el pronóstico. A 0 h es casi una foto del presente; a 48 h ya es un pronóstico de dos días.</li>
      <li><strong>IA frente a físico.</strong> AIFS aprende de décadas de datos; IFS y GFS resuelven las ecuaciones de la atmósfera. Si la IA empata o gana a 25 km, el siguiente paso es bajarla a 4 km con Chile adentro.</li>
      <li>Los tres modelos trabajan con una grilla de 25 km. Donde el error es alto suele haber mar y cordillera en una misma celda (costa del norte, Patagonia). Esa es la brecha que el downscaling a 2 a 4 km debe cerrar.</li>
    </ol>
    <p class="muted small">Umbrales: menos de {num(UMBRAL_T[0])} °C es bueno, hasta {num(UMBRAL_T[1])} °C aceptable, y más de eso alto. Son umbrales de trabajo; el asesor meteorológico del proyecto los revisará.</p>
  </div>
</section>

<section>
  <div class="sec-head"><h2>La IA frente al modelo físico</h2>
  <p class="frase">{frase}</p>
  {f'<p class="muted small">{nota_cmp}</p>' if nota_cmp else ''}</div>
  <div class="modelos">{''.join(tarjetas)}</div>
  <p class="muted small">Los tres modelos usan la misma grilla de 25 km y se miden contra las mismas estaciones y observaciones. AIFS es la versión de inteligencia artificial de ECMWF; IFS es su modelo físico tradicional; GFS es el modelo físico global de Estados Unidos (NOAA). Cada uno se verifica en su última corrida completa, por eso el número de pares puede diferir.</p>
</section>

<section>
  <div class="sec-head"><h2>Error por plazo</h2>
  <p class="muted">Cuánto se equivoca cada modelo según las horas de anticipación. Todas las estaciones juntas; en cada plazo, el menor error de temperatura va destacado. {nota_plazos}</p></div>
  <div class="card tabla">
    <table>
      <thead><tr><th class="l">Plazo</th><th class="l">Modelo</th><th>Pares</th><th>Error temp.</th><th>Sesgo temp.</th><th>Error viento</th><th>Sesgo viento</th><th class="l">Nivel</th></tr></thead>
      <tbody>{''.join(filas_plazo)}</tbody>
    </table>
  </div>
</section>

<section>
  <div class="sec-head"><h2>Error por estación</h2>
  <p class="muted">Ordenado de mayor a menor error de temperatura de {MODELOS[base][0]}, para ver primero lo que requiere atención. Error de temperatura a 2 m de cada modelo (el menor va destacado); pares, sesgo, viento a 10 m y nivel corresponden a {MODELOS[base][0]}. Todos los plazos juntos.</p></div>
  <div class="card tabla">
    <table>
      <thead><tr><th class="l">Estación</th><th>Pares</th>{cab_modelos}<th>Sesgo temp.</th><th>Error viento</th><th class="l">Nivel</th></tr></thead>
      <tbody>{''.join(filas_est)}</tbody>
    </table>
  </div>
</section>

{serie}

<section>
  <details>
    <summary>Cómo se calcula</summary>
    <div class="body">
      <p>Pronósticos: {lista_modelos}{'; pendientes: ' + ', '.join(etiqueta_modelo(m) for m in ausentes) if ausentes else ''}. Los tres en grilla global de 0,25° (unos 25 km), con temperatura a 2 m, viento a 10 m y precipitación, plazos 0, 6, 12, 18, 24, 36 y 48 h. AIFS e IFS vienen de los datos abiertos de ECMWF (CC-BY 4.0); GFS, del bucket público de NOAA en AWS (dominio público). Se toma el punto de grilla más cercano a cada aeródromo, sin corrección por altura.</p>
      <p>Observación: reportes METAR horarios de {n_est} aeródromos chilenos (emitidos por la DMC, distribuidos por NOAA/AWC, dominio público). Un par se forma cuando hay una observación a menos de 31 minutos de la hora pronosticada. Los valores pronosticados en cada estación se guardan, así que los plazos largos se emparejan en las corridas siguientes, cuando ya existe la observación.</p>
      <p>Error medio absoluto = promedio de |pronóstico − observación|. Sesgo = promedio de (pronóstico − observación). El pipeline corre 4 veces al día en GitHub Actions, toma la última corrida completa de cada modelo y acumula todos los pares; los resultados y el código son públicos.</p>
      <p>Próximos pasos: sumar estaciones de la DMC, verificar precipitación y mostrar la serie de 30 días.</p>
    </div>
  </details>
</section>

<footer>
  <p>Generado el {generado}. Datos: ECMWF open data, AIFS e IFS (CC-BY 4.0); NOAA GFS (dominio público); NOAA/AWC METAR (dominio público); contorno de Natural Earth (dominio público).
  Código abierto: <a href="{REPO}" rel="noopener">github.com/PanchoDigevo/earth2-chile-verificacion</a>.</p>
  <p><em>{narr_aviso or 'Información de apoyo a la decisión. No reemplaza los avisos ni las alertas oficiales de la Dirección Meteorológica de Chile ni de SENAPRED.'}</em></p>
</footer>

</div>
</body>
</html>
"""
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site/index.html listo ({len(html) // 1024} KB, {n_runs} corridas, {len(pts)} pares, {n_est} estaciones, modelos: {', '.join(presentes)})")


if __name__ == "__main__":
    ruta = os.path.join(AQUI, "data", "verif_puntos.csv")
    render_site(pd.read_csv(ruta, parse_dates=["run", "valid"]))
