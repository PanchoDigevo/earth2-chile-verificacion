"""Genera ../site/eventos.html (Eventos 2026) y ../site/metodo.html (Método) con los resultados de analizar.py,
y deja ../site/historico.html como redirección para no romper enlaces antiguos.

Uso: desde analizar.py: render(pares, r)
     python render_historico.py   -> regenera desde data/resultados/*.csv (sin volver a analizar)
Diseño: docs/brief_sitio.md. Reutiliza estilos y piezas de verificacion/render_site.py y verificacion/comun.py."""
import glob, os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "verificacion"))
sys.path.insert(0, AQUI)
from render_site import CSS, MODELOS, ORDEN, UMBRAL_T, MIN_PARES, chip, nivel, nombre, barra, head, escribir  # noqa: E402
from comun import (EVENTOS, GLOSARIO, JS_DEF, MESES, MESES_LARGO, aviso, d, entero, fecha, nav, num, pie, signo)  # noqa: E402

RES = os.path.join(AQUI, "data", "resultados")
import viento_render  # noqa: E402
CATALOGO = os.path.join(AQUI, "..", "hindcast", "eventos", "eventos_2026.csv")
PLAZOS = [72, 48, 24]
UMBRAL_LLUVIA_MM = 1.0

CSS_EXTRA = """
:root{--serie-global:#7a8896;--serie-corr:#0e7c86}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--serie-global:#8d9bab;--serie-corr:#44bcc6}}
:root[data-theme="dark"]{--serie-global:#8d9bab;--serie-corr:#44bcc6}
.indice{display:flex;flex-wrap:wrap;gap:8px}
.indice a{display:inline-flex;padding:5px 12px;border:1px solid var(--line);border-radius:999px;background:var(--surface);text-decoration:none;font-weight:600;font-size:14.5px;color:var(--fg)}
.indice a:hover{border-color:var(--accent)}
.evento{scroll-margin-top:96px}
.evento .imp{color:var(--muted);font-size:15.5px;max-width:75ch}
.lectura{border-left:3px solid var(--accent);padding:10px 14px;background:var(--accent-soft);border-radius:0 var(--radius) var(--radius) 0;max-width:80ch}
.lectura p{max-width:none}
table.matriz{max-width:560px}
table.matriz td.celda{text-align:center;font-weight:600}
table.matriz td.celda small{display:block;font-weight:400;font-size:12.5px;color:var(--muted)}
td.celda.bueno{background:color-mix(in srgb,var(--bueno) 16%,transparent)}
td.celda.medio{background:color-mix(in srgb,var(--medio) 18%,transparent)}
td.celda.alto{background:color-mix(in srgb,var(--alto) 16%,transparent)}
.ev-tabla table{font-size:13.5px} .ev-tabla th,.ev-tabla td{padding:6px 7px}
.ev-tabla th.grupo{text-align:center;border-bottom:1px solid var(--line-soft);color:var(--fg);letter-spacing:.04em}
.ev-tabla th.sub{font-size:11px}
td.mm{font-family:var(--font-data);font-size:13.5px;font-variant-numeric:tabular-nums}
td.mm.fuerte{font-weight:700}
.si{font-weight:600} .no{color:var(--muted)}
.mancuerna{width:100%;max-width:720px;height:auto;display:block}
.mancuerna .eje{font:12px var(--font-data);fill:var(--muted)}
.mancuerna .grid-l{stroke:var(--line-soft);stroke-width:1}
.mancuerna .mod{font:600 15px var(--font-display);fill:var(--fg)}
.mancuerna .tipo{font:12px var(--font-body);fill:var(--muted)}
.mancuerna .val{font:600 13px var(--font-data);fill:var(--fg)}
.mancuerna .cambio{font:700 14px var(--font-data);fill:var(--serie-corr)}
.mancuerna .tramo{stroke:var(--line);stroke-width:4;stroke-linecap:round}
.mancuerna .g{fill:var(--serie-global);stroke:var(--surface);stroke-width:2}
.mancuerna .c{fill:var(--serie-corr);stroke:var(--surface);stroke-width:2}
.ley{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:var(--muted)}
.ley i{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin-right:6px}
.ley .g i{background:var(--serie-global)} .ley .c i{background:var(--serie-corr)}
dl.glosario{display:grid;gap:10px;margin:0}
dl.glosario dt{font-weight:600} dl.glosario dd{margin:0;color:var(--muted);max-width:72ch}
ul.limites{margin:0;padding-left:1.2em;display:grid;gap:6px;max-width:75ch}
"""


def tabla(encabezados, filas_html, clase=""):
    th = "".join(("<th class='l'>" if i == 0 else "<th>") + str(h) + "</th>" for i, h in enumerate(encabezados))
    return f'<div class="card tabla {clase}"><table><thead><tr>{th}</tr></thead><tbody>{"".join(filas_html)}</tbody></table></div>'


def ordenar(df):
    """Orden de presentación AIFS, IFS, GFS (no alfabético)."""
    if df.empty or "modelo" not in df:
        return df
    df = df.copy(); df["_o"] = df.modelo.map({m: i for i, m in enumerate(ORDEN)})
    return df.sort_values(["_o"] + [c for c in ("lead_h",) if c in df]).drop(columns="_o")


# ---------- Eventos ----------
def catalogo():
    try:
        return pd.read_csv(CATALOGO, parse_dates=["inicio", "fin"])
    except Exception:
        return pd.DataFrame()


def nivel_ratio(a, t):
    if t == 0:
        return "sin"
    r = a / t
    return "bueno" if r >= 0.9 else "medio" if r >= 0.6 else "alto"


def matriz_evento(res_ev):
    filas = []
    for m in ORDEN:
        celdas = []
        for l in PLAZOS:
            x = res_ev[(res_ev.modelo == m) & (res_ev.lead_h == l)]
            if x.empty:
                celdas.append("<td class='celda'>–</td>"); continue
            a, t, f = int(x.aciertos.iloc[0]), int(x.aciertos.iloc[0] + x.fallas.iloc[0]), int(x.falsas.iloc[0])
            if t == 0:
                celdas.append(f"<td class='celda'>sin lluvia<small>{f} en falso</small></td>" if f else "<td class='celda'>sin lluvia</td>"); continue
            extra = f"<small>{f} aviso{'s' if f != 1 else ''} en falso</small>" if f else ""
            celdas.append(f"<td class='celda {nivel_ratio(a, t)}'>{a} de {t}{extra}</td>")
        filas.append(f"<tr><td class='l modelo-nombre'>{m}<span class='tipo'>{'IA' if m == 'AIFS' else 'físico'} · {MODELOS[m][2]}</span></td>{''.join(celdas)}</tr>")
    return (f"<div class='tabla'><table class='matriz'><thead><tr><th class='l'>Modelo</th>"
            + "".join(f"<th>{l} h antes</th>" for l in PLAZOS) + f"</tr></thead><tbody>{''.join(filas)}</tbody></table></div>")


def tabla_dia_a_dia(ev, dd, sat_idx):
    filas = []
    for (dia, icao), g in dd.groupby(["dia", "icao"], sort=True):
        g0 = g.iloc[0]
        dia = pd.Timestamp(dia)
        if pd.isna(g0.lluvia_obs):
            obs = "<span class='no'>sin datos</span>"
        elif g0.lluvia_obs:
            obs = f"<span class='si'>Llovió</span> <span class='muted small'>({int(g0.horas_lluvia_obs)} h con lluvia)</span>"
        else:
            obs = "<span class='no'>No llovió</span>"
        sat = sat_idx.get((ev, dia.date(), icao))
        celda_sat = f"<td class='mm'>{num(sat, 1)}</td>" if sat is not None and not pd.isna(sat) else "<td class='mm muted'>–</td>"
        celdas = []
        for l in PLAZOS:
            for m in ORDEN:
                x = g[(g.lead_h == l) & (g.modelo == m)]
                if x.empty or pd.isna(x.tp24_fc.iloc[0]):
                    celdas.append("<td class='mm'>–</td>")
                else:
                    v = float(x.tp24_fc.iloc[0])
                    celdas.append(f"<td class='mm{' fuerte' if v >= 10 else ''}'>{num(v, 1)}</td>")
        filas.append(f"<tr><td class='l'>{dia.day} {MESES[dia.month - 1]}</td><td class='l'>{nombre(icao)[0]}</td><td class='l'>{obs}</td>{celda_sat}{''.join(celdas)}</tr>")
    cab1 = ("<tr><th class='l' rowspan='2'>Día</th><th class='l' rowspan='2'>Aeródromo</th><th class='l' rowspan='2'>¿Llovió?</th>"
            "<th rowspan='2'>Satélite<br>mm</th>" + "".join(f"<th class='grupo' colspan='{len(ORDEN)}'>Pronóstico {l} h antes (mm)</th>" for l in PLAZOS) + "</tr>")
    cab2 = "<tr>" + "".join(f"<th class='sub'>{m}</th>" for _ in PLAZOS for m in ORDEN) + "</tr>"
    return f'<div class="tabla ev-tabla"><table><thead>{cab1}{cab2}</thead><tbody>{"".join(filas)}</tbody></table></div>'


def pagina_eventos(r, ahora):
    det, res = r.get("eventos_detalle", pd.DataFrame()), r.get("eventos_resumen", pd.DataFrame())
    cat = catalogo()
    try:
        sat = pd.read_csv(os.path.join(RES, "lluvia_satelite_eventos.csv"), parse_dates=["dia"])
        sat_idx = {(e, dd.date(), i): m for e, dd, i, m in zip(sat.evento, sat.dia, sat.icao, sat.mm)}
        fuente_sat = sat.fuente.iloc[0] if len(sat) else ""
    except Exception:
        sat_idx, fuente_sat = {}, ""
    try:
        from analizar import ZONAS
    except Exception:
        ZONAS = {}
    if not det.empty:
        det = det.copy(); det["dia"] = pd.to_datetime(det.dia)

    orden = list(cat.sort_values("inicio", ascending=False).id) if not cat.empty else list(dict.fromkeys(det.evento)) if not det.empty else []
    bloques, indice = [], []
    for ev in orden:
        info = cat[cat.id == ev].iloc[0] if not cat.empty and (cat.id == ev).any() else None
        titulo = EVENTOS.get(ev, (info.zona if info is not None else ev,))[0]
        dd = det[det.evento == ev] if not det.empty else pd.DataFrame()
        rr = res[res.evento == ev] if not res.empty else pd.DataFrame()
        if dd.empty and info is None:
            continue
        indice.append(f'<a href="#{ev}">{titulo.split(",")[0]}</a>')
        if info is not None:
            f0, f1 = info.inicio, info.fin
            cuando = (f"{f0.day} de {MESES_LARGO[f0.month - 1]} de {f0.year}" if f0 == f1 else
                      f"del {f0.day} de {MESES_LARGO[f0.month - 1]} al {f1.day} de {MESES_LARGO[f1.month - 1]} de {f1.year}")
            impacto = ". ".join(x.strip()[:1].upper() + x.strip()[1:] for x in str(info.descripcion).split(";") if x.strip()) if pd.notna(info.descripcion) else ""
            lectura = str(info.lectura) if "lectura" in cat.columns and pd.notna(info.lectura) else ""
            fuente = f' <a href="{info.fuente}" rel="noopener">Fuente</a>.' if pd.notna(info.fuente) else ""
        else:
            cuando, impacto, lectura, fuente = "", "", "", ""
        refs = ", ".join(nombre(i)[0] for i in ZONAS.get(ev, []))
        obs = dd.drop_duplicates(["dia", "icao"]) if not dd.empty else dd
        con_lluvia = int((obs.lluvia_obs == 1).sum()) if not obs.empty else 0
        total = int(obs.lluvia_obs.notna().sum()) if not obs.empty else 0
        matriz = matriz_evento(rr) if not rr.empty else "<p class='muted'>Sin datos de modelos para este evento todavía.</p>"
        quebradas = ('<p><a href="quebradas.html">Ver las laderas quemadas y el indicador por quebrada de Santiago oriente →</a></p>'
                     if ev in ("lascondes-oct", "santiago-13oct") else "")
        detalle = ""
        if not dd.empty:
            nota_sat = f" La columna Satélite es la lluvia estimada por {fuente_sat} en el punto del aeródromo, para el día calendario." if fuente_sat else ""
            detalle = (f'<details><summary>Ver día por día, aeródromo por aeródromo</summary><div class="body">'
                       f'<p class="small muted">Lluvia pronosticada para las 24 horas de cada día (de 8 o 9 de la mañana a la misma hora del día siguiente), '
                       f'según la corrida emitida 72, 48 y 24 horas antes. En negrita, 10 mm o más.{nota_sat}</p>'
                       f'{tabla_dia_a_dia(ev, dd, sat_idx)}</div></details>')
        if ev.startswith("incendios"):
            # evento de incendio: la pregunta es viento y sequedad, no lluvia
            secos = total - con_lluvia
            avisos = ""
            if not rr.empty:
                x = rr[(rr.modelo == "AIFS") & (rr.lead_h == 24)]
                if len(x):
                    marco = int(x.aciertos.iloc[0] + x.falsas.iloc[0])
                    avisos = f" Con un día de anticipación, la IA (AIFS) anunció lluvia en {marco} de esos {total} casos."
            cuerpo_evento = (viento_render.bloque_evento(ev, num, titulo="¿Anticiparon el viento?")
                             + (f"<h3>¿Y la sequedad?</h3><p class='small'>En los aeródromos de la zona ({refs}) no llovió en {secos} de los {total} casos con observación, contando cada día en cada aeródromo.{avisos}</p>"
                                if total else f"<p class='small muted'>Los datos de los aeródromos de la zona ({refs}) para estos días aparecerán cuando se complete el análisis del histórico.</p>"))
        else:
            cuerpo_evento = (f"<h3>¿Marcaron lluvia antes?</h3><p class='small muted'>En los aeródromos de la zona ({refs}) hubo {con_lluvia} casos con lluvia, "
                             f"contando cada día en cada aeródromo{f', de {total} con observación' if total != con_lluvia else ''}. Cada celda dice en cuántos de esos casos "
                             f"el modelo había anunciado lluvia con esa anticipación.</p>{matriz}{viento_render.bloque_evento(ev, num)}")
        bloques.append(f"""<article class="card evento" id="{ev}">
  <div class="sec-head"><div class="eyebrow">{cuando}</div><h2>{titulo}</h2>
  {f'<p class="imp">{impacto}.{fuente}</p>' if impacto else ''}</div>
  {f'<div class="lectura"><p><strong>Lectura.</strong> {lectura}</p></div>' if lectura else ''}
  {cuerpo_evento}
  {quebradas}
  {detalle}
</article>""")

    lluvia = ordenar(r.get("lluvia", pd.DataFrame()))
    filas_ll = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{entero(x.n)}</td>"
                f"<td class='num'>{num(100 * x.frec_obs, 0, ' %')}</td><td class='num'>{num(100 * x.pod, 0, ' %')}</td><td class='num'>{num(100 * x.far, 0, ' %')}</td></tr>"
                for x in lluvia.itertuples(index=False)] if not lluvia.empty else []
    seccion_ll = f"""<section>
  <div class="sec-head"><h2>Y en todo 2025–2026: ¿cuándo avisaron la lluvia?</h2>
  <p class="muted">Todos los días de los dos años, en todos los aeródromos. "Acertó cuando llovió": de los días con lluvia, en cuántos el modelo la había anunciado. "Avisó en falso": de los avisos de lluvia del modelo, cuántos no se cumplieron.</p></div>
  {tabla(["Modelo", "Anticipación", "Días comparados", "Días con lluvia", "Acertó cuando llovió", "Avisó en falso"], filas_ll)}
</section>""" if filas_ll else ""

    html = f"""{head("Eventos 2026 · Earth-2 Chile", "Qué lluvia anunciaban los modelos AIFS, IFS y GFS 72, 48 y 24 horas antes de los eventos de 2026 en Chile, y si de verdad llovió.")}
<body>
{nav("eventos")}
<div class="wrap">
<header>
  <div class="eyebrow">Eventos 2026</div>
  <h1>¿Lo vieron venir?</h1>
  <p class="lead">Para cada evento de 2026: qué lluvia anunciaban los modelos 72, 48 y 24 horas antes en los aeródromos de la zona, y si de verdad llovió. Un modelo "marca lluvia" cuando pronostica {num(UMBRAL_LLUVIA_MM, 0)} mm o más para ese día.</p>
  <nav class="indice" aria-label="Eventos">{''.join(indice)}</nav>
</header>
{''.join(bloques)}
{seccion_ll}
{aviso()}
{pie(ahora)}
</div>
{JS_DEF}
</body>
</html>
"""
    return escribir("eventos.html", html.replace("</style>", CSS_EXTRA + "</style>", 1))


# ---------- Método ----------
def mancuerna(cp24):
    """Antes y después por modelo a 24 h, a escala: un tramo del valor corregido al sin corregir."""
    W, fila, ml, mr, mt = 720, 64, 150, 90, 30
    xmax = max(2.5, float(np.ceil(cp24.mae_global.max() * 2) / 2))
    x = lambda v: ml + (W - ml - mr) * v / xmax
    H = mt + fila * len(cp24) + 26
    out = []
    for t in np.arange(0, xmax + 0.001, 0.5):
        out.append(f'<line class="grid-l" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{mt - 8}" y2="{H - 26}"/>'
                   f'<text class="eje" x="{x(t):.1f}" y="{H - 8}" text-anchor="middle">{num(t, 1)}</text>')
    for i, rr in enumerate(cp24.itertuples(index=False)):
        y = mt + fila * i + fila / 2
        mej = 100 * (1 - rr.mae_corregido / rr.mae_global)
        out.append(f'<text class="mod" x="0" y="{y - 2:.1f}">{rr.modelo}</text>'
                   f'<text class="tipo" x="0" y="{y + 15:.1f}">{"IA" if rr.modelo == "AIFS" else "físico"} · {MODELOS[rr.modelo][2]}</text>'
                   f'<line class="tramo" x1="{x(rr.mae_corregido):.1f}" x2="{x(rr.mae_global):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>'
                   f'<circle class="g" cx="{x(rr.mae_global):.1f}" cy="{y:.1f}" r="7"/><circle class="c" cx="{x(rr.mae_corregido):.1f}" cy="{y:.1f}" r="7"/>'
                   f'<text class="val" x="{x(rr.mae_global):.1f}" y="{y - 13:.1f}" text-anchor="middle">{num(rr.mae_global, 2)}</text>'
                   f'<text class="val" x="{x(rr.mae_corregido):.1f}" y="{y - 13:.1f}" text-anchor="middle">{num(rr.mae_corregido, 2)}</text>'
                   f'<text class="cambio" x="{W - 4}" y="{y + 5:.1f}" text-anchor="end">{num(-mej, 0)} %</text>')
    return (f'<svg class="mancuerna" viewBox="0 0 {W} {H}" role="img" aria-label="Error medio a 24 h por modelo, sin corregir y corregido">'
            f'{"".join(out)}</svg>')


def pagina_metodo(r, n_pares, n_corridas, n_est, ahora):
    cp = ordenar(r.get("correccion_plazos", pd.DataFrame()))
    sec_corr = ""
    if not cp.empty:
        cp24 = cp[cp.lead_h == 24]
        filas = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{entero(x.n)}</td>"
                 f"<td class='num'>{num(x.mae_global, 2, ' °C')}</td><td class='num'>{num(x.mae_corregido, 2, ' °C')}</td>"
                 f"<td class='num'>{num(-100 * (1 - x.mae_corregido / x.mae_global), 0, ' %')}</td>"
                 f"<td class='num'>{signo(x.sesgo_global, 2, ' °C')}</td><td class='num'>{signo(x.sesgo_corregido, 2, ' °C')}</td></tr>"
                 for x in cp.itertuples(index=False)]
        sec_corr = f"""<section class="card">
  <div class="sec-head"><h2>La primera capa chilena: corrección por estación</h2>
  <p class="muted">Cada aeródromo le enseña al sistema su error típico: el {d("sesgo")} medio de 2025 por aeródromo, modelo, {d("plazo")} y hora de {d("corrida")}, con al menos {MIN_PARES} comparaciones. Ese valor se resta a los pronósticos de 2026, que el sistema nunca vio. Abajo, el {d("error medio")} de la temperatura pronosticada para el día siguiente en 2026.</p></div>
  {mancuerna(cp24)}
  <div class="ley"><span class="g"><i></i>Sin corregir</span><span class="c"><i></i>Corregido por estación</span><span>°C de error medio, pronóstico a 24 h, 2026</span></div>
  <details><summary>Todos los plazos</summary><div class="body">{tabla(["Modelo", "Plazo", "Comparaciones", "Sin corregir", "Corregido", "Cambio", "Sesgo sin corregir", "Sesgo corregido"], filas)}</div></details>
</section>"""

    pl, me, es = ordenar(r.get("plazos", pd.DataFrame())), r.get("mensual", pd.DataFrame()), r.get("estaciones", pd.DataFrame())
    sec_temp = ""
    if not pl.empty:
        f_pl = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{entero(x.n)}</td>"
                f"<td class='medida'><span class='medida-in'>{barra(x.mae, 4, nivel(x.mae))}<span class='num'>{num(x.mae, 2, ' °C')}</span></span></td>"
                f"<td class='num'>{signo(x.sesgo, 2, ' °C')}</td></tr>" for x in pl.itertuples(index=False)]
        cols = [m for m in ORDEN if m in set(me.modelo)] if not me.empty else []
        f_me = []
        if cols:
            m24 = me[me.lead_h == 24].pivot(index="mes", columns="modelo", values="mae").reindex(columns=cols)
            n24 = me[me.lead_h == 24].groupby("mes").n.sum()
            for mes, row in m24.iterrows():
                a, mm = mes.split("-")
                f_me.append(f"<tr><td class='l'>{MESES[int(mm) - 1]} {a}</td><td class='num'>{entero(n24.get(mes, 0))}</td>"
                            + "".join(f"<td class='num'>{num(v, 2)}</td>" for v in row.values) + "</tr>")
        f_es = []
        if not es.empty:
            e24 = es[(es.lead_h == 24) & (es.n >= MIN_PARES)].pivot(index="icao", columns="modelo", values="mae").reindex(columns=[m for m in ORDEN if m in set(es.modelo)])
            e24 = e24.assign(_p=e24.max(axis=1)).sort_values("_p", ascending=False).drop(columns="_p")
            for icao, row in e24.iterrows():
                corto, region = nombre(icao)
                f_es.append(f"<tr><td class='l'>{corto}<span class='region'>{region}</span></td>"
                            + "".join(f"<td class='num'>{num(v, 2)}</td>" for v in row.values) + "</tr>")
        sec_temp = f"""<section>
  <div class="sec-head"><h2>Qué tan bien pronostican la temperatura</h2>
  <p class="muted">Error medio de la temperatura a 2 m, sin corregir, en enero de 2025 a octubre de 2026: {entero(n_pares)} comparaciones de {entero(n_corridas)} corridas en {n_est} aeródromos. {d("Sesgo")} negativo: el modelo pronostica más frío de lo que ocurre.</p></div>
  {tabla(["Modelo", "Plazo", "Comparaciones", "Error medio", "Sesgo"], f_pl)}
  <details><summary>Por mes, a 24 h</summary><div class="body">{tabla(["Mes", "Comparaciones"] + [f"{m} (°C)" for m in cols], f_me)}</div></details>
  <details><summary>Por aeródromo, a 24 h</summary><div class="body">{tabla(["Aeródromo"] + [f"{m} (°C)" for m in ORDEN if not es.empty and m in set(es.modelo)], f_es)}</div></details>
</section>"""

    sec_movil = ""
    try:
        mt = ordenar(pd.read_csv(os.path.join(AQUI, "..", "oceano", "data", "correccion_movil_total.csv")))
        me_ = pd.read_csv(os.path.join(AQUI, "..", "oceano", "data", "correccion_movil.csv"))
    except Exception:
        mt = pd.DataFrame()
    if not mt.empty:
        f_mt = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{entero(x.n)}</td>"
                f"<td class='num'>{num(x.mae_sin, 2, ' °C')}</td><td class='num'>{num(x.mae_fija, 2, ' °C')}</td><td class='num'>{num(x.mae_movil, 2, ' °C')}</td></tr>"
                for x in mt.itertuples(index=False)]
        g24 = me_[me_.lead_h == 24]
        cuenta = {m: g24[g24.modelo == m].gana.value_counts().to_dict() for m in ORDEN}
        frase = "; ".join(f"{m}: la móvil gana en {c.get('móvil', 0)}, la de 2025 en {c.get('fija', 0)} y empatan en {c.get('empate', 0)}" for m, c in cuenta.items() if c)
        sec_movil = f"""<section class="card">
  <div class="sec-head"><h2>Corrección fija o móvil</h2>
  <p class="muted">La corrección fija usa el error típico de 2025. La móvil usa el de los últimos 45 días antes de cada pronóstico, sin mirar el futuro, así que se adapta si algo cambia (el mar, el entorno del aeródromo, el modelo). Las dos se evalúan sobre los mismos pronósticos de 2026.</p></div>
  {tabla(["Modelo", "Plazo", "Comparaciones", "Sin corregir", "Corrección 2025", "Corrección 45 días"], f_mt)}
  <p class="small">Por aeródromo, a 24 h: {frase}. El detalle de cada uno está en su ficha de <a href="zona.html">Tu zona</a>.</p>
</section>"""

    glosario = "".join(f"<dt>{k[0].upper() + k[1:]}</dt><dd>{v}</dd>" for k, v in GLOSARIO.items())
    html = f"""{head("Método · Earth-2 Chile", "Cómo medimos el error de los pronósticos en Chile: fuentes, cálculos, corrección por estación, indicador de quebradas y límites conocidos.")}
<body>
{nav("metodo")}
<div class="wrap">
<header>
  <div class="eyebrow">Método y datos</div>
  <h1>Cómo lo medimos</h1>
  <p class="lead">Todo lo que se publica en este sitio sale de datos abiertos y de código abierto. Aquí están las fuentes, los cálculos, las tablas completas y los límites que conocemos.</p>
</header>
{sec_corr}
{sec_temp}
{sec_movil}
{viento_render.seccion_metodo(tabla, num, entero, signo, d)}
<section class="card">
  <div class="sec-head"><h2>Cómo se calcula</h2></div>
  <h3>Verificación diaria (Resumen, Tu zona)</h3>
  <p>Cuatro veces al día, un proceso automático en GitHub Actions toma la última corrida completa de AIFS (IA de ECMWF), IFS (ECMWF) y GFS (NOAA), los tres en grilla global de 0,25° (unos 25 km), y lee la temperatura a 2 m, el viento a 10 m y la lluvia en el punto de grilla más cercano a cada aeródromo, sin corrección por altura. Cada pronóstico se guarda y se compara con el reporte METAR del aeródromo más cercano en el tiempo, a menos de 31 minutos de la hora pronosticada.</p>
  <h3>Verificación retroactiva 2025–2026 (Eventos, cifras del Resumen)</h3>
  <p>Del archivo abierto de ECMWF y de NOAA en AWS se leen las corridas de 00 y 12 UTC de enero de 2025 a hoy, solo temperatura y lluvia acumulada a 24, 48 y 72 horas en cada aeródromo; los archivos de modelo no se guardan. Las observaciones vienen del archivo METAR de la Iowa Environmental Mesonet. Los METAR chilenos no informan milímetros de lluvia: se usa el tiempo presente (lluvia, llovizna, chubasco, tormenta) para saber si llovió en las 24 horas, exigiendo al menos 12 reportes. La lluvia por satélite de los eventos viene de PERSIANN-CCS (o de IMERG de la NASA, cuando hay credenciales).</p>
  <h3>Corrección por estación</h3>
  <p>Sesgo medio de 2025 por aeródromo, modelo, plazo y hora de corrida, con al menos {MIN_PARES} comparaciones; se resta al pronóstico de 2026. Las combinaciones con menos datos no se corrigen y no entran en la comparación.</p>
  <h3>Indicador de quebradas</h3>
  <p>Regla del Servicio Geológico de Estados Unidos (USGS) para flujos de detritos después de incendios (Staley y otros, 2017, modelo M1). Usa la fracción de la cuenca quemada con pendiente de 23° o más (Sentinel-2 y Copernicus DEM), la severidad media de la quema y la intensidad de la lluvia prevista por AIFS y GFS, que se supone concentrada en 2 horas. Las cuencas se delimitan desde el modelo de elevación a 30 m. Detalle completo en la sección Quebradas.</p>
</section>
<section class="card" id="estaciones">
  <div class="sec-head"><h2>Lluvia medida en estaciones</h2></div>
  <p>Los aeródromos chilenos no informan milímetros. Para medir la lluvia usamos todas las estaciones chilenas que envían cada hora un mensaje SYNOP a la red de la Organización Meteorológica Mundial, con la lluvia de la última hora y la temperatura: 141 estaciones, casi todas automáticas de la Dirección Meteorológica de Chile (DMC), de Visviri a Isla Diego Ramírez, más Isla de Pascua y Juan Fernández. Se guardan todas; por ahora la comparación con los pronósticos y la pestaña En vivo usan las de Santiago. La más cercana a las quebradas de Santiago oriente es Aguas Andinas, en La Florida (670 m, a unos 16 km de la Quebrada de Apoquindo); en la precordillera están San José Guayacán (Cajón del Maipo) y Río Clarillo (Pirque), y en la cordillera El Colorado (2.750 m), cuya temperatura indica si la isoterma 0 °C está sobre o bajo esa altura.</p>
  <h3>Cómo se usa</h3>
  <p>Cada hora un proceso automático guarda la lluvia horaria y la temperatura de esas estaciones (un archivo por mes en <code>estaciones/datos/synop/</code>; nombres, coordenadas y alturas en <code>estaciones/catalogo.csv</code>) y compara cada bloque de 6 horas que guardó el seguimiento de pronósticos de AIFS, IFS y GFS con lo medido en la estación más cercana bajo 1.500 m (<code>estaciones/VERIFICACION_LLUVIA.md</code>). Un bloque solo se compara si llegaron las seis horas. La pestaña <a href="envivo.html">En vivo</a> muestra lo medido en las últimas 24 horas junto al pronóstico para la Quebrada de Apoquindo.</p>
  <h3>Licencia y fuente</h3>
  <p>Los SYNOP son datos esenciales de libre intercambio según la Resolución 40 de la OMM. Los produce la DMC; los leemos sin clave desde Ogimet, un servicio gratuito que redistribuye los mensajes de la red mundial, con pocas consultas y pausas entre ellas. Al reutilizarlos, citar a la DMC como fuente.</p>
  <h3>Límites de esta red</h3>
  <ul class="limites">
    <li>Un pluviómetro mide un punto; el modelo, el promedio de una celda de unos 25 km. Aguas Andinas está al pie del cerro, no en las laderas quemadas: con tormentas puede llover en San Carlos de Apoquindo y no en La Florida, o al revés.</li>
    <li>Los pluviómetros automáticos miden mal la nieve y la lluvia con viento fuerte: en la cordillera los milímetros no son confiables, y por eso solo se usa su temperatura.</li>
    <li>Son datos provisorios, sin control de calidad, y pueden faltar horas o llegar con atraso. Quinta Normal y Pudahuel, que tienen observador, informan la lluvia de 6 horas a las 21, 3, 9 y 15 h (hora de verano de Chile) en vez de la de 1 hora.</li>
    <li>Todavía faltan dos redes. La de la Dirección General de Aguas (DGA, MOP), con pluviómetros en la Quebrada de Ramón, la Quebrada de Macul, Antupirén y el Cerro Calán, y estaciones de nieve como Valle Echaurren Norte, entrega sus datos en tiempo real solo después de un captcha, así que no se pueden leer de forma automática: hay que pedirle acceso a la DGA. La API de la DMC, con más estaciones (por ejemplo Tobalaba), se activa con un usuario y un token que están en trámite.</li>
    <li>Por ahora no hay una medición automática de nieve (altura o agua equivalente) para comparar con la isoterma 0 °C pronosticada.</li>
  </ul>
</section>
<section class="card">
  <div class="sec-head"><h2>Límites que conocemos</h2></div>
  <ul class="limites">
    <li>Los aeródromos no son las quebradas ni los barrios: miden en terreno plano y abierto. Las estaciones de la DMC que envían SYNOP ya se usan para la lluvia; las demás requieren un acceso que está en trámite.</li>
    <li>La lluvia observada en aeródromos es sí o no, sin milímetros. Los milímetros por satélite son estimaciones y subestiman la lluvia de montaña. Desde octubre de 2026 la lluvia se mide además en estaciones de la DMC (ver <a href="#estaciones">Lluvia medida en estaciones</a>); la verificación retroactiva 2025–2026 todavía no las usa.</li>
    <li>El modelo del USGS fue calibrado en el oeste de Estados Unidos y no está validado en Chile. Usa un valor de erodabilidad del suelo (0,25) supuesto, porque no hay mapa para Chile.</li>
    <li>Los umbrales de bueno, aceptable y alto (1,5 y 3 °C) y los del indicador de quebradas son de trabajo y están en revisión con un meteorólogo.</li>
    <li>Las cifras de los últimos días se marcan como preliminares hasta juntar 30 días.</li>
  </ul>
</section>
<section class="card">
  <div class="sec-head"><h2>Glosario</h2></div>
  <dl class="glosario">{glosario}</dl>
</section>
{aviso()}
{pie(ahora)}
</div>
{JS_DEF}
</body>
</html>
"""
    return escribir("metodo.html", html.replace("</style>", CSS_EXTRA + "</style>", 1))


def redireccion():
    html = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eventos 2026 · Earth-2 Chile</title><meta http-equiv="refresh" content="0; url=eventos.html"><link rel="canonical" href="eventos.html">
<style>body{font:17px/1.5 system-ui,sans-serif;margin:40px 16px;color:#17212b;background:#f4f6f8}@media (prefers-color-scheme:dark){body{color:#e7ecf1;background:#111821}a{color:#44bcc6}}</style>
</head><body><p>La verificación retroactiva ahora está en <a href="eventos.html">Eventos 2026</a> y en <a href="metodo.html">Método</a>.</p></body></html>
"""
    return escribir("historico.html", html)


def render(pares, r):
    ahora = pd.Timestamp.now("UTC")
    if pares is not None and len(pares):
        t = pares.dropna(subset=["t_err"])
        n_pares, n_corridas, n_est = len(t), t.run.nunique(), t.icao.nunique()
    else:
        pl = r.get("plazos", pd.DataFrame())
        n_pares = int(pl[pl.lead_h == 24].n.sum()) if not pl.empty else 0
        try:
            n_corridas = pd.read_csv(os.path.join(AQUI, "data", "pronosticos.csv.gz"), usecols=["run"]).run.nunique()
        except Exception:
            n_corridas = 0
        es = r.get("estaciones", pd.DataFrame())
        n_est = es.icao.nunique() if not es.empty else 0
    kb1 = pagina_eventos(r, ahora)
    kb2 = pagina_metodo(r, n_pares, n_corridas, n_est, ahora)
    redireccion()
    print(f"site/eventos.html ({kb1} KB), site/metodo.html ({kb2} KB) y site/historico.html (redirección) listos")


def desde_csv():
    """Regenera Eventos y Método solo con los resultados guardados (lo llama el pipeline diario)."""
    r = {os.path.basename(f)[:-4]: pd.read_csv(f) for f in glob.glob(os.path.join(RES, "*.csv"))}
    ruta_pares = os.path.join(AQUI, "data", "pares.csv.gz")
    pares = pd.read_csv(ruta_pares, parse_dates=["run", "valid"]) if os.path.exists(ruta_pares) else None
    render(pares, r)


if __name__ == "__main__":
    desde_csv()
