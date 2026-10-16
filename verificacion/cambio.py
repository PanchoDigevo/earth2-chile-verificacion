"""Sección "Lo que está cambiando" del Resumen y datos de deriva y corrección móvil por aeródromo.

Todo sale de datos primarios (oceano/data/, generado por oceano/oceano.py y oceano/deriva.py):
  - sst_cajas.csv: anomalía diaria de la temperatura del mar (NOAA OISST v2.1, base 1991-2020) frente a cada aeródromo costero y en Niño 1+2.
  - nino_semanal.csv: índices semanales de NOAA CPC.
  - deriva_estado.csv y correccion_movil.csv: deriva por aeródromo y comparación de la corrección fija (2025) con la móvil (45 días).
Regla: lenguaje descriptivo; si un dato no lo muestra, el sitio no lo dice."""
import os
import numpy as np
import pandas as pd
from comun import d, fecha, num, signo

AQUI = os.path.dirname(os.path.abspath(__file__))
OCEANO = os.path.join(AQUI, "..", "oceano", "data")
ORDEN_COSTA = ["SCAR", "SCDA", "SCFA", "SCAT", "SCSE", "SCSN", "SCIE", "SCTE", "NINO12"]

CSS_CAMBIO = """
:root{--calido:#d9622b;--frio:#2a78d6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--calido:#ef8a55;--frio:#5aa0f0}}
:root[data-theme="dark"]{--calido:#ef8a55;--frio:#5aa0f0}
.cambios{display:grid;gap:12px;grid-template-columns:1fr}
@media (min-width:900px){.cambios{grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)}.cambios .cambio:nth-child(3){grid-column:1/-1}}
.barras-mar{width:100%;max-width:560px;height:auto;display:block}
.barras-mar .nom{font:14px var(--font-body);fill:var(--fg)}
.barras-mar .val{font:600 12.5px var(--font-data);fill:var(--fg)}
.barras-mar .eje{font:11.5px var(--font-data);fill:var(--muted)}
.barras-mar .eje0{stroke:var(--line);stroke-width:1}
.barras-mar .calido{fill:var(--calido)} .barras-mar .frio{fill:var(--frio)}
.indices{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.indices > div{display:grid;gap:2px}
.indices .lbl{font-size:13px;color:var(--muted)}
.indices .v{font-family:var(--font-display);font-size:30px;font-weight:600;line-height:1.1}
.indices .v small{font-size:15px;color:var(--muted);margin-left:2px}
.serie-mini{width:100%;max-width:260px;height:auto}
.serie-mini .cero{stroke:var(--line);stroke-width:1}
.serie-mini .linea{fill:none;stroke:var(--calido);stroke-width:2;stroke-linejoin:round}
.serie-mini .fin{fill:var(--calido);stroke:var(--surface);stroke-width:2}
.lista-deriva{margin:0;padding-left:1.2em;display:grid;gap:6px;font-size:15.5px;max-width:80ch}
"""


def leer(nombre_csv, **kw):
    try:
        return pd.read_csv(os.path.join(OCEANO, nombre_csv), **kw)
    except Exception:
        return pd.DataFrame()


def datos():
    out = {}
    s = leer("sst_cajas.csv", parse_dates=["fecha"])
    if not s.empty:
        ult = s.fecha.max()
        v = s[s.fecha > ult - pd.Timedelta(days=7)].groupby(["caja", "nombre"]).anom.mean().reset_index()
        v["o"] = v.caja.map({k: i for i, k in enumerate(ORDEN_COSTA)})
        out["sst"] = {"hasta": ult, "cajas": v.sort_values("o"), "prelim": bool(s[s.fecha == ult].preliminar.max())}
    n = leer("nino_semanal.csv", parse_dates=["semana"])
    if not n.empty:
        out["nino"] = n.tail(26)
    dv = leer("deriva_estado.csv", parse_dates=["fecha"])
    if not dv.empty:
        out["deriva"] = dv
    return out


def por_estacion(icao, modelo):
    """Para la ficha de Tu zona: corrección fija vs. móvil a 24 h y deriva actual, si existen."""
    out = {}
    mv = leer("correccion_movil.csv")
    if not mv.empty:
        x = mv[(mv.modelo == modelo) & (mv.icao == icao) & (mv.lead_h == 24)]
        if len(x):
            out.update(fija=round(float(x.mae_fija.iloc[0]), 2), movil=round(float(x.mae_movil.iloc[0]), 2), gana=x.gana.iloc[0])
    dv = leer("deriva_estado.csv")
    if not dv.empty:
        y = dv[(dv.modelo == modelo) & (dv.icao == icao)]
        if len(y) and str(y.deriva.iloc[0]).lower() == "true":
            out["deriva"] = round(float(y.res30.iloc[0]), 2)
    try:
        ve = pd.read_csv(os.path.join(AQUI, "..", "historico", "data", "resultados", "viento_estaciones.csv"))
        z = ve[(ve.modelo == modelo) & (ve.icao == icao) & (ve.lead_h == 24)]
        if len(z) and pd.notna(z.w_mae.iloc[0]):
            out["viento"] = round(float(z.w_mae.iloc[0]) * 3.6, 1)
            out["viento_sesgo"] = round(float(z.w_sesgo.iloc[0]) * 3.6, 1)
            if pd.notna(z.g_mae.iloc[0]):
                out["rafaga"] = round(float(z.g_mae.iloc[0]) * 3.6, 1)
    except Exception:
        pass
    return out


def svg_barras_mar(cajas):
    """Barras divergentes de anomalía (°C) por tramo de costa, de norte a sur, a escala."""
    W, fila, ml, mr = 560, 26, 120, 56
    vmax = max(1.0, float(np.ceil(cajas.anom.abs().max())))
    x0 = ml + (W - ml - mr) / 2
    x = lambda v: x0 + (W - ml - mr) / 2 * v / vmax
    H = fila * len(cajas) + 26
    out = [f'<line class="eje0" x1="{x0:.1f}" x2="{x0:.1f}" y1="0" y2="{H - 22}"/>']
    for t in (-vmax, 0, vmax):
        out.append(f'<text class="eje" x="{x(t):.1f}" y="{H - 6}" text-anchor="middle">{signo(t, 0)} °C</text>')
    for i, r in enumerate(cajas.itertuples(index=False)):
        y = i * fila + 4
        xa, xb = sorted((x0, x(r.anom)))
        lado = r.anom >= 0
        out.append(f'<text class="nom" x="{ml - 8}" y="{y + 13}" text-anchor="end">{r.nombre}</text>'
                   f'<rect class="{"calido" if lado else "frio"}" x="{xa:.1f}" y="{y + 2}" width="{max(1.5, xb - xa):.1f}" height="{fila - 10}" rx="3"/>'
                   f'<text class="val" x="{x(r.anom) + (6 if lado else -6):.1f}" y="{y + 13}" text-anchor="{"start" if lado else "end"}">{signo(r.anom, 1)}</text>')
    return f'<svg class="barras-mar" viewBox="0 0 {W} {H}" role="img" aria-label="Anomalía de la temperatura del mar por tramo de costa">{"".join(out)}</svg>'


def svg_serie(valores, etiqueta):
    """Línea de las últimas semanas, con el cero como referencia y el último punto destacado."""
    W, H, m = 260, 70, 6
    v = [float(x) for x in valores]
    lo, hi = min(0.0, min(v)), max(0.0, max(v))
    rng = (hi - lo) or 1
    xs = [m + i * (W - 2 * m) / max(1, len(v) - 1) for i in range(len(v))]
    y = lambda val: m + (H - 2 * m) * (1 - (val - lo) / rng)
    pts = " ".join(f"{a:.1f},{y(b):.1f}" for a, b in zip(xs, v))
    return (f'<svg class="serie-mini" viewBox="0 0 {W} {H}" role="img" aria-label="{etiqueta}">'
            f'<line class="cero" x1="{m}" x2="{W - m}" y1="{y(0):.1f}" y2="{y(0):.1f}"/>'
            f'<polyline class="linea" points="{pts}"/><circle class="fin" cx="{xs[-1]:.1f}" cy="{y(v[-1]):.1f}" r="4"/></svg>')


def bloque_mar(x):
    costa = x["cajas"][x["cajas"].caja != "NINO12"]
    nino = x["cajas"][x["cajas"].caja == "NINO12"]
    calidos = costa[costa.anom >= 0.5]
    if len(calidos):
        frase = f"En los últimos 7 días, el mar frente a {len(calidos)} de los {len(costa)} tramos de costa estuvo medio grado o más sobre su promedio 1991–2020."
    else:
        frase = "En los últimos 7 días, ningún tramo de costa estuvo medio grado o más sobre su promedio 1991–2020."
    if len(nino):
        frase += f" En la región Niño 1+2, frente a Ecuador y el norte de Perú, la anomalía fue de {signo(float(nino.anom.iloc[0]), 1, ' °C')}."
    prelim = ", con datos preliminares los últimos días" if x["prelim"] else ""
    return ('<div class="card cambio"><h3>El mar frente a la costa</h3>'
            f'<p class="small">{frase}</p>{svg_barras_mar(x["cajas"])}'
            f'<p class="small muted">Anomalía media de la temperatura del mar en los 7 días hasta el {fecha(x["hasta"])}{prelim}. '
            'Caja de unos 100 km mar adentro frente a cada aeródromo. Fuente: NOAA OISST v2.1; promedio de referencia 1991–2020.</p></div>')


def bloque_nino(n):
    u = n.iloc[-1]
    return ('<div class="card cambio"><h3>Índices del Pacífico ecuatorial</h3><div class="indices">'
            f'<div><span class="lbl">Niño 1+2</span><span class="v">{signo(u.nino12_anom, 1)}<small>°C</small></span>{svg_serie(n.nino12_anom, "Niño 1+2, últimas 26 semanas")}</div>'
            f'<div><span class="lbl">Niño 3.4</span><span class="v">{signo(u.nino34_anom, 1)}<small>°C</small></span>{svg_serie(n.nino34_anom, "Niño 3.4, últimas 26 semanas")}</div></div>'
            f'<p class="small muted">Anomalía de la temperatura del mar en la semana del {fecha(u.semana)} y las 26 semanas anteriores. '
            'Niño 1+2 es el mar frente a Ecuador y el norte de Perú; Niño 3.4, el centro del Pacífico ecuatorial. Fuente: NOAA CPC; promedio de referencia 1991–2020.</p></div>')


def bloque_deriva(dv, nombres):
    dv = dv.copy(); dv["deriva"] = dv.deriva.astype(str).str.lower() == "true"
    aifs = dv[(dv.modelo == "AIFS") & dv.deriva].sort_values("res30")
    otros = dv[(dv.modelo != "AIFS") & dv.deriva]
    items = []
    for r in aifs.itertuples(index=False):
        t = (f'<li><a href="zona.html#{r.icao}">{nombres.get(r.icao, r.icao)}</a>: en los últimos 30 días la IA pronosticó '
             f'{num(abs(r.res30), 1)} °C más {"frío" if r.res30 < 0 else "calor"} de lo que corresponde a su error habitual')
        if pd.notna(r.sst_anom30):
            t += f"; el mar frente a este aeródromo estuvo {signo(r.sst_anom30, 1, ' °C')} respecto de lo normal"
        items.append(t + ".</li>")
    if not items:
        items = ["<li>Ningún aeródromo en deriva con la IA (AIFS).</li>"]
    extra = ""
    if len(otros):
        frios = int((otros.res30 < 0).sum())
        extra = f" Con los modelos físicos hay {len(otros)} casos más; en {frios} de ellos el modelo pronosticó más frío de lo habitual."
    definicion = ("El error que queda después de la corrección aprendida en 2025, promediado en 30 días, pasa de 1 °C. "
                  "Indica que algo cambió respecto del año anterior: el mar, el entorno del aeródromo o el modelo.")
    return ('<div class="card cambio"><h3>Aeródromos donde el error cambió</h3>'
            f'<p class="small">Un aeródromo está en {d("deriva", definicion=definicion)} cuando su error de los últimos 30 días se aleja más de 1 °C '
            f'del que tenía en 2025.{extra}</p><ul class="lista-deriva">{"".join(items)}</ul>'
            f'<p class="small muted">Al {fecha(dv.fecha.max())}, pronóstico de temperatura a 24 h, con al menos 20 comparaciones.</p></div>')


def seccion(est):
    c = datos()
    if not c:
        return ""
    nombres = {e["icao"]: e["nombre"] for e in est}
    bloques = []
    if "sst" in c:
        bloques.append(bloque_mar(c["sst"]))
    if "nino" in c:
        bloques.append(bloque_nino(c["nino"]))
    if "deriva" in c:
        bloques.append(bloque_deriva(c["deriva"], nombres))
    return ('<section aria-labelledby="t-cambio"><div class="sec-head"><h2 id="t-cambio">Lo que está cambiando</h2>'
            '<p class="muted">Datos de satélite y de los aeródromos, sin interpretación: si un dato no lo muestra, aquí no se dice.</p></div>'
            f'<div class="cambios">{"".join(bloques)}</div></section>')
