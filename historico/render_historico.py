"""Genera ../site/historico.html con los resultados de analizar.py. Reutiliza el diseño (tokens, chips, barras)
de verificacion/render_site.py para que las dos páginas se vean como una sola."""
import os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "verificacion"))
from render_site import CSS, MODELOS, ORDEN, UMBRAL_T, chip, nivel, nombre, num, signo, barra  # noqa: E402

SITE = os.path.join(AQUI, "..", "site")
REPO = "https://github.com/PanchoDigevo/earth2-chile-verificacion"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
PLAZOS = [24, 48, 72]
TITULOS_EVENTO = {"coquimbo-jul": "Coquimbo y Huasco, 14 al 24 de julio", "centrosur-ago": "Centro-sur, 30 de julio al 2 de agosto",
                  "lascondes-oct": "Las Condes, 8 de octubre"}

CSS_EXTRA = """
:root{--serie-global:#0e7c86;--serie-corr:#d95926}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--serie-global:#44bcc6;--serie-corr:#f08a5d}}
:root[data-theme="dark"]{--serie-global:#44bcc6;--serie-corr:#f08a5d}
.multiples{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.multiples figure{margin:0;display:grid;gap:6px}
.multiples figcaption{font-family:var(--font-display);font-weight:600;font-size:15px}
.multiples svg{width:100%;height:auto;display:block}
.grid-l{stroke:var(--line-soft);stroke-width:1}
.eje{font:11px var(--font-data);fill:var(--muted)}
.serie{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.serie.global{stroke:var(--serie-global)} .serie.corr{stroke:var(--serie-corr)}
.pto{stroke:var(--surface);stroke-width:2}
.pto.global{fill:var(--serie-global)} .pto.corr{fill:var(--serie-corr)}
.etq{font:600 11px var(--font-data);fill:var(--fg)}
.ley{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:var(--muted)}
.ley i{display:inline-block;width:18px;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px}
.ley .g i{background:var(--serie-global)} .ley .c i{background:var(--serie-corr)}
.evento{display:grid;gap:10px}
.evento .desc{color:var(--muted);max-width:72ch}
td.mm{font-family:var(--font-data);font-size:14px;font-variant-numeric:tabular-nums}
td.mm.fuerte{font-weight:600}
.si{color:var(--fg);font-weight:600} .no{color:var(--muted)}
.nav{font-size:14px}
"""


def etq_modelo(m):
    n, tipo, org = MODELOS.get(m, (m, "", ""))
    return f"{n} <span class='muted small'>({tipo.lower()}, {org})</span>" if tipo else n


def grafico(filas, ymax):
    """Dos curvas (global y corregido) por plazo, a escala. filas: DataFrame con lead_h, mae_global, mae_corregido."""
    W, H, ml, mr, mt, mb = 320, 180, 36, 44, 12, 28
    x = lambda lead: ml + (PLAZOS.index(int(lead))) * (W - ml - mr) / (len(PLAZOS) - 1)
    y = lambda v: mt + (H - mt - mb) * (1 - v / ymax)
    pasos = [t for t in np.arange(0, ymax + 0.01, 0.5 if ymax <= 3 else 1.0)]
    grid = "".join(f'<line class="grid-l" x1="{ml}" x2="{W - mr}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>'
                   f'<text class="eje" x="{ml - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{num(t, 1)}</text>' for t in pasos)
    ejex = "".join(f'<text class="eje" x="{x(l):.1f}" y="{H - 8}" text-anchor="middle">{l} h</text>' for l in PLAZOS)
    f = filas.set_index("lead_h")
    out = [grid, ejex]
    for clase, col in (("global", "mae_global"), ("corr", "mae_corregido")):
        pts = [(x(l), y(f.loc[l, col])) for l in PLAZOS if l in f.index and pd.notna(f.loc[l, col])]
        if len(pts) >= 2:
            out.append(f'<polyline class="serie {clase}" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}"/>')
        for a, b in pts:
            out.append(f'<circle class="pto {clase}" cx="{a:.1f}" cy="{b:.1f}" r="4"/>')
        if pts:
            a, b = pts[-1]; v = f.loc[PLAZOS[len(pts) - 1], col]
            out.append(f'<text class="etq" x="{a + 8:.1f}" y="{b + 4:.1f}">{num(v, 2)}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Error medio por plazo, global y corregido">{"".join(out)}</svg>'


def tabla(encabezados, filas_html):
    th = "".join(("<th class='l'>" if i == 0 else "<th>") + str(h) + "</th>" for i, h in enumerate(encabezados))
    return f'<div class="card tabla"><table><thead><tr>{th}</tr></thead><tbody>{"".join(filas_html)}</tbody></table></div>'


def seccion_correccion(r):
    cp = r["correccion_plazos"]
    if cp.empty:
        return """<section><div class="sec-head"><h2>Global frente a global corregido</h2>
<p class="muted">La corrección por estación se aprende con los pares de 2025 y se evalúa con los de 2026. Aparecerá aquí cuando
el histórico de 2025 esté extraído.</p></div></section>"""
    ymax = max(2.0, float(np.ceil(max(cp.mae_global.max(), cp.mae_corregido.max()) * 2) / 2))
    figs = []
    for m in ORDEN:
        f = cp[cp.modelo == m]
        if f.empty:
            continue
        figs.append(f'<figure><figcaption>{etq_modelo(m)}</figcaption>{grafico(f, ymax)}</figure>')
    mejor = cp[cp.lead_h == 24].sort_values("mae_corregido").head(1)
    frase = ""
    if not mejor.empty:
        b = mejor.iloc[0]
        mejora = 100 * (1 - b.mae_corregido / b.mae_global) if b.mae_global else 0
        frase = (f"A 24 h, con {b.modelo}, la corrección por estación baja el error medio de {num(b.mae_global, 2)} °C a "
                 f"{num(b.mae_corregido, 2)} °C ({num(mejora, 0)} % menos) en {int(b.n)} pares de 2026.")
    filas = []
    for rr in cp.sort_values(["modelo", "lead_h"]).itertuples(index=False):
        mejora = 100 * (1 - rr.mae_corregido / rr.mae_global) if rr.mae_global else np.nan
        filas.append(f"<tr><td class='l'>{etq_modelo(rr.modelo)}</td><td class='num'>{int(rr.lead_h)} h</td><td class='num'>{int(rr.n)}</td>"
                     f"<td class='num'>{num(rr.mae_global, 2, ' °C')}</td><td class='num'>{signo(rr.sesgo_global, 2, ' °C')}</td>"
                     f"<td class='num'>{num(rr.mae_corregido, 2, ' °C')}</td><td class='num'>{signo(rr.sesgo_corregido, 2, ' °C')}</td>"
                     f"<td class='num'>{signo(-mejora, 0, ' %')}</td></tr>")
    return f"""<section>
  <div class="sec-head"><h2>Global frente a global corregido por estación</h2>
  <p class="muted">Cada estación le enseña al sistema su sesgo propio: el error medio de 2025 por estación, modelo, plazo y hora de
  corrida. Esa corrección se aplica a 2026 sin haber visto 2026. Es la primera capa chilena, la más simple; el downscaling a 4 km viene después.</p></div>
  <p><strong>{frase}</strong></p>
  <div class="card"><div class="multiples">{"".join(figs)}</div>
  <div class="ley"><span class="g"><i></i>Global (sin corregir)</span><span class="c"><i></i>Global corregido por estación</span><span>Error medio de temperatura en °C, pares de 2026</span></div></div>
  {tabla(["Modelo", "Plazo", "Pares", "Error global", "Sesgo global", "Error corregido", "Sesgo corregido", "Cambio"], filas)}
</section>"""


def seccion_eventos(r):
    det, res = r["eventos_detalle"], r["eventos_resumen"]
    if det.empty:
        return ""
    bloques = []
    for ev, d in det.groupby("evento", sort=False):
        titulo = TITULOS_EVENTO.get(ev, ev)
        resumen = res[res.evento == ev] if not res.empty else pd.DataFrame()
        frases = []
        for m in ORDEN:
            partes = []
            for l in PLAZOS:
                x = resumen[(resumen.modelo == m) & (resumen.lead_h == l)]
                if not x.empty and (x.aciertos.iloc[0] + x.fallas.iloc[0]) > 0:
                    partes.append(f"{int(x.aciertos.iloc[0])} de {int(x.aciertos.iloc[0] + x.fallas.iloc[0])} a {l} h")
            if partes:
                frases.append(f"<li><strong>{m}</strong> marcó lluvia en {', '.join(partes)}.</li>")
        obs_dias = d.drop_duplicates(["dia", "icao"])
        con_lluvia = int((obs_dias.lluvia_obs == 1).sum()); total = int(obs_dias.lluvia_obs.notna().sum())
        filas = []
        for (dia, icao), g in d.groupby(["dia", "icao"], sort=True):
            g0 = g.iloc[0]
            corto, _ = nombre(icao, icao)
            if pd.isna(g0.lluvia_obs):
                obs_html = "<span class='no'>sin datos</span>"
            elif g0.lluvia_obs:
                obs_html = f"<span class='si'>Llovió</span> <span class='muted small'>({int(g0.horas_lluvia_obs)} h con lluvia)</span>"
            else:
                obs_html = "<span class='no'>No llovió</span>"
            celdas = []
            for l in (72, 48, 24):
                for m in ORDEN:
                    x = g[(g.lead_h == l) & (g.modelo == m)]
                    if x.empty or pd.isna(x.tp24_fc.iloc[0]):
                        celdas.append("<td class='mm'>–</td>")
                    else:
                        v = float(x.tp24_fc.iloc[0])
                        celdas.append(f"<td class='mm{' fuerte' if v >= 10 else ''}'>{num(v, 1)}</td>")
            t_obs = "" if pd.isna(g0.t_obs) else f" · {num(g0.t_obs, 0)} °C"
            filas.append(f"<tr><td class='l'>{dia.strftime('%d %b').replace(dia.strftime('%b'), MESES[dia.month - 1])}</td>"
                         f"<td class='l'>{corto} <span class='muted small'>{icao}</span></td><td class='l'>{obs_html}<span class='muted small'>{t_obs}</span></td>{''.join(celdas)}</tr>")
        enc = ["Día", "Estación", "Observado en las 24 h del día"] + [f"{m} {l} h" for l in (72, 48, 24) for m in ORDEN]
        bloques.append(f"""<div class="evento"><h3>{titulo}</h3><p class="desc">{d.zona.iloc[0]}. De {total} día-estación con observación, en {con_lluvia} llovió.
  Las columnas muestran la lluvia pronosticada (mm) para las 24 h de ese día, de las 12 UTC (8 o 9 de la mañana en Chile) a las 12 UTC del día siguiente, según la corrida emitida 72, 48 y 24 h antes del cierre de esa ventana; en negrita 10 mm o más.</p>
  <ul>{''.join(frases)}</ul>{tabla(enc, filas)}</div>""")
    return f"""<section>
  <div class="sec-head"><h2>Los tres eventos de 2026, vistos desde antes</h2>
  <p class="muted">Para cada día de cada evento: qué lluvia anunciaba cada modelo con 72, 48 y 24 horas de anticipación en los aeródromos de la zona,
  y si de verdad llovió según los reportes horarios. Un modelo "marca" lluvia cuando pronostica {num(UMBRAL_LLUVIA_MM(), 0)} mm o más en 24 h.</p></div>
  {''.join(bloques)}
</section>"""


def UMBRAL_LLUVIA_MM():
    import analizar
    return analizar.UMBRAL_LLUVIA_MM


def seccion_lluvia(r):
    c = r["lluvia"]
    if c.empty:
        return ""
    filas = []
    for rr in c.sort_values(["modelo", "lead_h"]).itertuples(index=False):
        filas.append(f"<tr><td class='l'>{etq_modelo(rr.modelo)}</td><td class='num'>{int(rr.lead_h)} h</td><td class='num'>{int(rr.n)}</td>"
                     f"<td class='num'>{num(100 * rr.frec_obs, 0, ' %')}</td><td class='num'>{num(100 * rr.pod, 0, ' %')}</td><td class='num'>{num(100 * rr.far, 0, ' %')}</td></tr>")
    return f"""<section>
  <div class="sec-head"><h2>Lluvia: cuándo avisó y cuándo no</h2>
  <p class="muted">El METAR chileno dice si está lloviendo pero no cuánto, así que aquí la pregunta es sí o no. "Acertó cuando llovió" es la parte de los
  días con lluvia observada en que el modelo había anunciado lluvia. "Avisó en falso" es la parte de los avisos del modelo en que después no llovió.</p></div>
  {tabla(["Modelo", "Plazo", "Casos", "Días con lluvia", "Acertó cuando llovió", "Avisó en falso"], filas)}
</section>"""


def seccion_temperatura(r, pares):
    pl, me, es = r["plazos"], r["mensual"], r["estaciones"]
    filas = [f"<tr><td class='l'>{etq_modelo(rr.modelo)}</td><td class='num'>{int(rr.lead_h)} h</td><td class='num'>{int(rr.n)}</td>"
             f"<td class='medida'><span class='medida-in'>{barra(rr.mae, 4, nivel(rr.mae, UMBRAL_T))}<span class='num'>{num(rr.mae, 2, ' °C')}</span></span></td>"
             f"<td class='num'>{signo(rr.sesgo, 2, ' °C')}</td><td>{chip(nivel(rr.mae, UMBRAL_T))}</td></tr>"
             for rr in pl.sort_values(["modelo", "lead_h"]).itertuples(index=False)]
    t_plazos = tabla(["Modelo", "Plazo", "Pares", "Error medio", "Sesgo", "Nivel"], filas)
    # mensual a 24 h, una columna por modelo
    m24 = me[me.lead_h == 24].pivot(index="mes", columns="modelo", values="mae").reindex(columns=[m for m in ORDEN if m in me.modelo.unique()])
    n24 = me[me.lead_h == 24].groupby("mes").n.sum()
    filas = []
    for mes, row in m24.iterrows():
        a, mm = mes.split("-")
        celdas = "".join(f"<td class='num'>{num(v, 2) if pd.notna(v) else '–'}</td>" for v in row.values)
        filas.append(f"<tr><td class='l'>{MESES[int(mm) - 1]} {a}</td><td class='num'>{int(n24.get(mes, 0))}</td>{celdas}</tr>")
    t_mensual = tabla(["Mes", "Pares"] + [f"{m} (°C)" for m in m24.columns], filas)
    # estaciones a 24 h
    e24 = es[es.lead_h == 24].pivot(index="icao", columns="modelo", values="mae").reindex(columns=[m for m in ORDEN if m in es.modelo.unique()])
    e24["peor"] = e24.max(axis=1); e24 = e24.sort_values("peor", ascending=False)
    filas = []
    for icao, row in e24.iterrows():
        corto, region = nombre(icao, icao)
        celdas = "".join(f"<td class='medida'><span class='medida-in'>{barra(v, 6, nivel(v, UMBRAL_T))}<span class='num'>{num(v, 1)}</span></span></td>" if pd.notna(v) else "<td>–</td>"
                         for v in row.drop("peor").values)
        filas.append(f"<tr><td class='l est-nombre'>{corto}<span class='icao'>{icao}</span><span class='region'>{region}</span></td>{celdas}</tr>")
    t_est = tabla(["Estación"] + [f"{m} a 24 h (°C)" for m in e24.columns if m != "peor"], filas)
    return f"""<section>
  <div class="sec-head"><h2>Temperatura: error por plazo, por mes y por estación</h2>
  <p class="muted">Error medio absoluto de la temperatura a 2 m, sin corrección, en todo el período. Mismas estaciones y mismas horas para los tres modelos.</p></div>
  {t_plazos}
  <h3>Por mes, a 24 h</h3>{t_mensual}
  <h3>Por estación, a 24 h (de mayor a menor error)</h3>{t_est}
</section>"""


def render(pares, r):
    t = pares.dropna(subset=["t_err"])
    ahora = pd.Timestamp.now("UTC")
    d0, d1 = t.valid.min(), t.valid.max()
    modelos = [m for m in ORDEN if m in t.modelo.unique()]
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Verificación retroactiva Earth-2 Chile</title>
<meta name="description" content="Qué decían AIFS, IFS y GFS 24, 48 y 72 horas antes, comparado con lo que midieron los aeródromos de Chile en 2025 y 2026, y cuánto mejora una corrección por estación.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}{CSS_EXTRA}</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="eyebrow">Earth-2 Chile · verificación retroactiva</div>
  <p class="nav"><a href="./">← Verificación diaria</a></p>
  <h1>Lo que los modelos decían antes de que pasara</h1>
  <p class="lead">En vez de esperar a que pasen los días, miramos hacia atrás: tomamos los pronósticos que {', '.join(modelos[:-1]) + ' y ' + modelos[-1] if len(modelos) > 1 else (modelos[0] if modelos else 'los modelos')}
  emitieron a las 00 y 12 UTC entre {d0.day} de {MESES[d0.month - 1]} de {d0.year} y {d1.day} de {MESES[d1.month - 1]} de {d1.year}, con 24, 48 y 72 horas de anticipación,
  y los comparamos con lo que después midieron {t.icao.nunique()} aeródromos del país.</p>
  <div class="aviso"><p class="small">Verificación pública de modelos; apoyo a la decisión. Las alertas oficiales son de la
  <a href="https://www.meteochile.gob.cl/" rel="noopener">Dirección Meteorológica de Chile</a> y de <a href="https://www.senapred.cl/" rel="noopener">SENAPRED</a>.</p></div>
</header>
<section><div class="tiles">
  <div class="tile"><div class="label">Pares pronóstico–observación</div><div class="value">{len(t):,}</div><div class="foot">temperatura a 2 m</div></div>
  <div class="tile"><div class="label">Corridas de modelo</div><div class="value">{t.run.nunique():,}</div><div class="foot">00 y 12 UTC</div></div>
  <div class="tile"><div class="label">Modelos</div><div class="value">{len(modelos)}</div><div class="foot">{', '.join(modelos)}</div></div>
  <div class="tile"><div class="label">Estaciones</div><div class="value">{t.icao.nunique()}</div><div class="foot">aeródromos con METAR</div></div>
</div></section>
{seccion_correccion(r)}
{seccion_eventos(r)}
{seccion_lluvia(r)}
{seccion_temperatura(r, pares)}
<section><details><summary>Cómo se calcula</summary><div class="body">
<p>Pronósticos: archivo de datos abiertos de ECMWF en AWS (AIFS single e IFS, 0,25°, CC-BY 4.0) y archivo del GFS de NOAA en AWS (0,25°, dominio público). De cada corrida de 00 y 12 UTC se leen solo los campos de temperatura a 2 m y precipitación acumulada a 24, 48 y 72 h, en el punto de grilla más cercano a cada aeródromo. No se guardan los archivos de modelo, solo los valores en las estaciones.</p>
<p>Observaciones: archivo METAR de la Iowa Environmental Mesonet (reportes de la DMC distribuidos por la red mundial). Temperatura: la observación más cercana a la hora pronosticada, a menos de 31 minutos. Lluvia: los METAR chilenos no informan milímetros, así que se usa el tiempo presente (RA, DZ, SH, TS, SN...) para saber si llovió en las 24 h que terminan a la hora pronosticada; se exige al menos 12 reportes en esas 24 h.</p>
<p>Corrección por estación: sesgo medio de 2025 por estación, modelo, plazo y hora de corrida, con al menos 30 pares; se resta del pronóstico de 2026. Las celdas sin suficientes pares de 2025 no se corrigen y no entran en la comparación.</p>
</div></details></section>
<footer>
  <p>Generado el {ahora.day} {MESES[ahora.month - 1]} {ahora.year}, {ahora:%H:%M} UTC. Datos: ECMWF open data (CC-BY 4.0), NOAA GFS (dominio público), Iowa Environmental Mesonet (archivo ASOS/METAR).
  Código abierto: <a href="{REPO}" rel="noopener">github.com/PanchoDigevo/earth2-chile-verificacion</a>.</p>
  <p><em>Información de apoyo a la decisión. No reemplaza los avisos ni las alertas oficiales de la Dirección Meteorológica de Chile ni de SENAPRED.</em></p>
</footer>
</div>
</body>
</html>
"""
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "historico.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site/historico.html listo ({len(html) // 1024} KB)")
