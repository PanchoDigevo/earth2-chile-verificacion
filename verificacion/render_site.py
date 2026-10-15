"""Genera ../site/index.html a partir de data/verif_puntos.csv (pares pronóstico-observación acumulados).

Uso: python render_site.py            -> regenera el sitio con lo que hay en data/
     desde verify.py: render_site(pts)

Diseño: una sola columna, resumen antes del detalle, mapa de Chile en tres franjas (norte, centro, sur),
tablas con barras de error y semáforo de tres niveles con texto (nunca solo color). Modo claro y oscuro.
Lenguaje: "aviso"/"pronóstico de impacto", nunca "alerta"; las alertas oficiales son de la DMC y SENAPRED."""
import json, math, os
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
    "SCIC": ("Curicó", "Maule"), "SCCH": ("Chillán", "Ñuble"), "SCIE": ("Concepción", "Biobío"), "SCGE": ("Los Ángeles", "Biobío"),
    "SCTC": ("Temuco (Maquehue)", "La Araucanía"), "SCQP": ("Temuco (La Araucanía)", "La Araucanía"), "SCPC": ("Pucón", "La Araucanía"),
    "SCVD": ("Valdivia", "Los Ríos"), "SCJO": ("Osorno", "Los Lagos"), "SCTE": ("Puerto Montt", "Los Lagos"),
    "SCAS": ("Puerto Aysén", "Aysén"), "SCCY": ("Coyhaique", "Aysén"), "SCBA": ("Balmaceda", "Aysén"),
    "SCNT": ("Puerto Natales", "Magallanes"), "SCCI": ("Punta Arenas", "Magallanes"), "SCRM": ("Base Frei (Antártica)", "Antártica"),
}

# Umbrales del semáforo (error medio absoluto). Temperatura en °C, viento en m/s.
UMBRAL_T = (1.5, 3.0)
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
    return f'<span class="chip {nv}"><i aria-hidden="true"></i>{NIVELES[nv]}</span>'


def barra(v, vmax, nv):
    pct = 0 if pd.isna(v) else max(2, min(100, 100 * v / vmax))
    return f'<span class="bar {nv}" aria-hidden="true"><i style="width:{pct:.0f}%"></i></span>'


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


def mapa(bye):
    path = contorno_path()
    if not path:
        return ""
    svgs = []
    for i, (titulo, la0, la1, lo0, lo1) in enumerate(FRANJAS):
        x0, y0 = proj(lo0, la0)
        x1, y1 = proj(lo1, la1)
        w, h = x1 - x0, y1 - y0
        defs = f'<defs><path id="chile" d="{path}"/></defs>' if i == 0 else ""
        puntos = []
        for r in bye.itertuples(index=False):
            if not (la1 <= r.lat <= la0 and lo0 <= r.lon <= lo1):
                continue
            x, y = proj(r.lon, r.lat)
            nv = nivel(r.t_mae, UMBRAL_T)
            corto, _ = nombre(r.icao, r.name)
            etiqueta = f'<text x="{x + 7:.1f}" y="{y + 3.5:.1f}">{r.icao}</text>' if nv == "alto" else ""
            puntos.append(f'<g class="est {nv}"><title>{corto} ({r.icao}): error medio de temperatura {num(r.t_mae, 1, " °C")}, '
                          f'viento {num(r.w_mae, 1, " m/s")}, {int(r.n)} pares</title>'
                          f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5"/>{etiqueta}</g>')
        svgs.append(f'<figure class="franja"><svg viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" '
                    f'role="img" aria-label="Mapa de la zona {titulo.lower()} de Chile con las estaciones">{defs}'
                    f'<use href="#chile" class="tierra"/>{"".join(puntos)}</svg><figcaption>{titulo}</figcaption></figure>')
    return '<div class="mapa">' + "".join(svgs) + "</div>"


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
"""


def render_site(pts):
    pts = pts.copy()
    pts["run"] = pd.to_datetime(pts["run"])
    pts["valid"] = pd.to_datetime(pts["valid"])
    mae = lambda e: e.abs().mean()

    res = (pts.groupby("lead_h").agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae),
                                     w_bias=("w_err", "mean"), w_mae=("w_err", mae)).reset_index().sort_values("lead_h"))
    bye = (pts.groupby("icao").agg(name=("name", "first"), lat=("lat", "first"), lon=("lon", "first"), elev=("elev", "first"),
                                   n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae), w_mae=("w_err", mae))
           .reset_index().sort_values("t_mae", ascending=False))
    por_run = pts.groupby("run").agg(n=("t_err", "size"), t_mae=("t_err", mae)).reset_index().sort_values("run")

    runs = sorted(pts.run.unique())
    ultima = pd.Timestamp(runs[-1])
    n_runs = len(runs)
    ahora = pd.Timestamp.now("UTC")

    # Cifra principal: error a 24 h si existe; si no, el plazo más largo disponible.
    fila_hero = res[res.lead_h == 24]
    if fila_hero.empty:
        fila_hero = res.iloc[[-1]]
    hero_lead = int(fila_hero.lead_h.iloc[0]); hero_mae = float(fila_hero.t_mae.iloc[0]); hero_n = int(fila_hero.n.iloc[0])
    hero_nv = nivel(hero_mae, UMBRAL_T)
    hero_txt = {"bueno": "Dentro de lo que un buen pronóstico puede ofrecer a esta escala.",
                "medio": "Aceptable para una grilla de 25 km; mejora con el downscaling.",
                "alto": "La grilla de 25 km no resuelve bien estos lugares."}[hero_nv]

    t_max = max(4.0, math.ceil(max(res.t_mae.max(), bye.t_mae.max()) + 0.01))
    w_max = max(4.0, math.ceil(max(res.w_mae.max(), bye.w_mae.max()) + 0.01))

    # --- tabla por plazo ---
    filas_plazo = []
    for r in res.itertuples(index=False):
        nt, nw = nivel(r.t_mae, UMBRAL_T), nivel(r.w_mae, UMBRAL_W)
        filas_plazo.append(
            f"<tr><td class='l num'>{int(r.lead_h)} h</td><td class='num'>{int(r.n)}</td>"
            f"<td class='medida'><span class='medida-in'>{barra(r.t_mae, t_max, nt)}<span class='num'>{num(r.t_mae, 2, ' °C')}</span></span></td>"
            f"<td class='num'>{signo(r.t_bias, 2, ' °C')}</td>"
            f"<td class='medida'><span class='medida-in'>{barra(r.w_mae, w_max, nw)}<span class='num'>{num(r.w_mae, 2, ' m/s')}</span></span></td>"
            f"<td class='num'>{signo(r.w_bias, 2, ' m/s')}</td><td>{chip(nt)}</td></tr>")
    plazos_pend = [h for h in (0, 6, 12, 18, 24, 36, 48) if h not in set(res.lead_h)]
    nota_plazos = (f"Los plazos de {', '.join(str(h) for h in plazos_pend)} h aparecerán a medida que las observaciones alcancen "
                   f"las horas pronosticadas." if plazos_pend else "")

    # --- tabla por estación ---
    filas_est = []
    for r in bye.itertuples(index=False):
        nt, nw = nivel(r.t_mae, UMBRAL_T), nivel(r.w_mae, UMBRAL_W)
        corto, region = nombre(r.icao, r.name)
        elev = "" if pd.isna(r.elev) else f"{int(float(r.elev))} m"
        filas_est.append(
            f"<tr><td class='l est-nombre'>{corto}<span class='icao'>{r.icao}</span>"
            f"<span class='region'>{region}{' · ' if region and elev else ''}{elev}</span></td>"
            f"<td class='num'>{int(r.n)}</td>"
            f"<td class='medida'><span class='medida-in'>{barra(r.t_mae, t_max, nt)}<span class='num'>{num(r.t_mae, 1, ' °C')}</span></span></td>"
            f"<td class='num'>{signo(r.t_bias, 1, ' °C')}</td>"
            f"<td class='medida'><span class='medida-in'>{barra(r.w_mae, w_max, nw)}<span class='num'>{num(r.w_mae, 1, ' m/s')}</span></span></td>"
            f"<td>{chip(nt)}</td></tr>")

    n_alto = int((bye.t_mae >= UMBRAL_T[1]).sum()); n_bueno = int((bye.t_mae < UMBRAL_T[0]).sum())
    sesgo_global = float(pts.t_err.mean())
    frio_calor = "frío (el modelo pronostica más frío de lo observado)" if sesgo_global < -0.3 else \
                 "cálido (el modelo pronostica más calor de lo observado)" if sesgo_global > 0.3 else "casi nulo"

    # --- serie por corrida (cuando haya más de una) ---
    serie = ""
    if n_runs >= 2:
        filas = "".join(f"<tr><td class='l num'>{pd.Timestamp(r.run):%d-%m %H}z</td><td class='num'>{int(r.n)}</td>"
                        f"<td class='medida'><span class='medida-in'>{barra(r.t_mae, t_max, nivel(r.t_mae, UMBRAL_T))}"
                        f"<span class='num'>{num(r.t_mae, 2, ' °C')}</span></span></td></tr>" for r in por_run.tail(30).itertuples(index=False))
        serie = f"""<section>
  <div class="sec-head"><h2>Corrida por corrida</h2>
  <p class="muted">Error medio de temperatura de cada corrida del modelo, todos los plazos y estaciones juntos. Últimas {min(30, n_runs)} corridas.</p></div>
  <div class="card tabla"><table><thead><tr><th class="l">Corrida (UTC)</th><th>Pares</th><th>Error temp.</th></tr></thead><tbody>{filas}</tbody></table></div>
</section>"""

    MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    fecha_ultima = f"{ultima.day} {MESES[ultima.month - 1]} · {ultima:%H} UTC"
    generado = f"{ahora.day} {MESES[ahora.month - 1]} {ahora.year}, {ahora:%H:%M} UTC"

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Verificación Earth-2 Chile</title>
<meta name="description" content="Cada día comparamos el pronóstico de inteligencia artificial de ECMWF (AIFS) con lo que midieron los aeródromos de Chile. Error por plazo y por estación, en lenguaje simple.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="eyebrow">Earth-2 Chile · verificación diaria</div>
  <h1>¿Qué tan bien acierta el pronóstico de IA en Chile?</h1>
  <p class="lead">Cada día tomamos el pronóstico del modelo de inteligencia artificial de ECMWF (AIFS) y lo comparamos con lo que
  realmente midieron {bye.icao.nunique()} aeródromos del país, de Arica a la Antártica. Aquí está el resultado, sin maquillaje.</p>
  <div class="aviso"><p class="small">Esta página es apoyo a la decisión y verificación pública de un modelo. Las alertas oficiales son de la
  <a href="https://www.meteochile.gob.cl/" rel="noopener">Dirección Meteorológica de Chile</a> y de
  <a href="https://www.senapred.cl/" rel="noopener">SENAPRED</a>.</p></div>
</header>

<section>
  <div class="tiles">
    <div class="tile hero">
      <div class="label">Error medio de temperatura a {hero_lead} h</div>
      <div class="value">{num(hero_mae, 1)}<small>°C</small></div>
      <div class="foot">{chip(hero_nv)} &nbsp;{hero_txt} {hero_n} pares.</div>
    </div>
    <div class="tile"><div class="label">Última corrida verificada</div><div class="value fecha">{fecha_ultima}</div><div class="foot">{ultima.year}. El modelo corre 4 veces al día.</div></div>
    <div class="tile"><div class="label">Corridas acumuladas</div><div class="value">{n_runs}</div><div class="foot">Desde el {pd.Timestamp(runs[0]).day} {MESES[pd.Timestamp(runs[0]).month - 1]} {pd.Timestamp(runs[0]).year}</div></div>
    <div class="tile"><div class="label">Pares pronóstico–observación</div><div class="value">{len(pts)}</div><div class="foot">{bye.icao.nunique()} estaciones</div></div>
    <div class="tile"><div class="label">Estaciones con error alto</div><div class="value">{n_alto}<small>de {len(bye)}</small></div><div class="foot">{n_bueno} con error bajo (menos de {num(UMBRAL_T[0])} °C)</div></div>
  </div>
</section>

<section class="dos">
  <div class="card">
    <div class="sec-head"><h2>Dónde acierta y dónde no</h2>
    <p class="muted small">Error medio de temperatura por estación. Pasa el cursor sobre un punto para ver el detalle.</p></div>
    {mapa(bye)}
    <div class="leyenda"><span class="item">{chip("bueno")} menos de {num(UMBRAL_T[0])} °C</span><span class="item">{chip("medio")} {num(UMBRAL_T[0])} a {num(UMBRAL_T[1])} °C</span><span class="item">{chip("alto")} {num(UMBRAL_T[1])} °C o más</span></div>
  </div>
  <div class="explica">
    <h2>Cómo leer esta página</h2>
    <ol>
      <li><strong>Error medio</strong> es cuánto se equivocó el modelo en promedio, sin importar el signo. Si dice 1,5 °C, el pronóstico estuvo típicamente un grado y medio arriba o abajo de lo medido.</li>
      <li><strong>Sesgo</strong> es la dirección del error. Negativo: el modelo pronostica más frío de lo que ocurre. Hoy el sesgo global es {signo(sesgo_global, 1, " °C")}, {frio_calor}.</li>
      <li><strong>Plazo</strong> es cuántas horas antes se hizo el pronóstico. A 0 h es casi una foto del presente; a 48 h ya es un pronóstico de dos días.</li>
      <li>El modelo trabaja con una grilla de 25 km. Donde el error es alto suele haber mar y cordillera en una misma celda (costa del norte, Patagonia). Esa es la brecha que el downscaling a 2 a 4 km debe cerrar.</li>
    </ol>
    <p class="muted small">Umbrales: menos de {num(UMBRAL_T[0])} °C es bueno, hasta {num(UMBRAL_T[1])} °C aceptable, y más de eso alto. Son umbrales de trabajo; el asesor meteorológico del proyecto los revisará.</p>
  </div>
</section>

<section>
  <div class="sec-head"><h2>Error por plazo</h2>
  <p class="muted">Cuánto se equivoca el modelo según las horas de anticipación. Todas las estaciones juntas. {nota_plazos}</p></div>
  <div class="card tabla">
    <table>
      <thead><tr><th class="l">Plazo</th><th>Pares</th><th>Error temp.</th><th>Sesgo temp.</th><th>Error viento</th><th>Sesgo viento</th><th class="l">Nivel</th></tr></thead>
      <tbody>{''.join(filas_plazo)}</tbody>
    </table>
  </div>
</section>

<section>
  <div class="sec-head"><h2>Error por estación</h2>
  <p class="muted">Ordenado de mayor a menor error de temperatura, para ver primero lo que requiere atención. Temperatura a 2 m y viento a 10 m, todos los plazos juntos.</p></div>
  <div class="card tabla">
    <table>
      <thead><tr><th class="l">Estación</th><th>Pares</th><th>Error temp.</th><th>Sesgo temp.</th><th>Error viento</th><th class="l">Nivel</th></tr></thead>
      <tbody>{''.join(filas_est)}</tbody>
    </table>
  </div>
</section>

{serie}

<section>
  <details>
    <summary>Cómo se calcula</summary>
    <div class="body">
      <p>Pronóstico: AIFS single (ECMWF, grilla global de 0,25°, datos abiertos CC-BY 4.0), variables temperatura a 2 m, viento a 10 m y precipitación, plazos 0, 6, 12, 18, 24, 36 y 48 h. Se toma el punto de grilla más cercano a cada aeródromo, sin corrección por altura.</p>
      <p>Observación: reportes METAR horarios de {bye.icao.nunique()} aeródromos chilenos (emitidos por la DMC, distribuidos por NOAA/AWC, dominio público). Un par se forma cuando hay una observación a menos de 31 minutos de la hora pronosticada.</p>
      <p>Error medio absoluto = promedio de |pronóstico − observación|. Sesgo = promedio de (pronóstico − observación). El pipeline corre 4 veces al día en GitHub Actions y acumula todos los pares; los resultados y el código son públicos.</p>
      <p>Próximos pasos: comparar también IFS (ECMWF físico) y GFS (NOAA), sumar estaciones de la DMC, precipitación y la serie de 30 días.</p>
    </div>
  </details>
</section>

<footer>
  <p>Generado el {generado}. Datos: ECMWF open data (CC-BY 4.0), NOAA/AWC METAR (dominio público), contorno de Natural Earth (dominio público).
  Código abierto: <a href="{REPO}" rel="noopener">github.com/PanchoDigevo/earth2-chile-verificacion</a>.</p>
  <p>Earth-2 Chile es un proyecto de inteligencia climática con IA a escala kilométrica. Esta verificación es información de apoyo a la decisión y no sustituye las alertas oficiales de la DMC ni de SENAPRED.</p>
</footer>

</div>
</body>
</html>
"""
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site/index.html listo ({len(html) // 1024} KB, {n_runs} corridas, {len(pts)} pares, {len(bye)} estaciones)")


if __name__ == "__main__":
    ruta = os.path.join(AQUI, "data", "verif_puntos.csv")
    render_site(pd.read_csv(ruta, parse_dates=["run", "valid"]))
