"""Genera site/escenarios.html (pestaña Escenarios) desde escenarios/data/actual.json e historial.csv."""
import csv, json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "verificacion"))
from render_site import head, escribir                      # noqa: E402
from comun import JS_DEF, MESES, d, hora_chile, nav, num, pie  # noqa: E402

DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

CSS_ESC = """
:root{--p-alta:#e8a33a;--p-critica:#c2410c}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--p-alta:#f0b55a;--p-critica:#f07a45}}
:root[data-theme="dark"]{--p-alta:#f0b55a;--p-critica:#f07a45}
.comuna{display:none} .comuna.visible{display:grid;gap:14px}
.barras{width:100%;height:auto;display:block}
.barras .eje{font:11px var(--font-data);fill:var(--muted)}
.barras .dia{font:11.5px var(--font-body);fill:var(--muted)}
.barras .grid-l{stroke:var(--line-soft);stroke-width:1}
.barras .alta{fill:var(--p-alta)} .barras .critica{fill:var(--p-critica)}
.barras .val{font:600 11px var(--font-data);fill:var(--fg)}
.ley{display:flex;gap:14px;flex-wrap:wrap;font-size:14px;color:var(--muted)}
.ley i{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:6px}
.ley .a i{background:var(--p-alta)} .ley .c i{background:var(--p-critica)}
.calor{border-collapse:separate;border-spacing:2px;width:100%;font-size:14px}
.calor th{font:600 12px var(--font-body);color:var(--muted);text-align:center;padding:2px;white-space:nowrap}
.calor th.l{text-align:left;color:var(--fg);font-size:14px;font-weight:600;padding-right:8px;white-space:normal;min-width:130px;text-transform:none;letter-spacing:0}
.calor td{font:12px var(--font-data);text-align:center;border-radius:4px;padding:7px 2px;min-width:30px;color:var(--fg);
  background:color-mix(in srgb,var(--accent) calc(var(--p) * 0.6%),var(--surface));outline:1px solid var(--line-soft)}
.calor td.bajo{color:var(--muted)} .calor td.sin{background:var(--surface);color:var(--muted)}
.calor-escala{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--muted)}
.calor-escala i{display:inline-block;width:120px;height:10px;border-radius:3px;background:linear-gradient(90deg,var(--surface),color-mix(in srgb,var(--accent) 60%,var(--surface)));outline:1px solid var(--line-soft)}
.seccion-faena{display:grid;gap:14px}
"""

RIESGOS = [("viento", "Viento fuerte", "50 km/h o más a media tarde"), ("nieve", "Nevada", "unos 2 cm de nieve o más en el día"),
           ("convectivo", "Chubasco convectivo", "posible tormenta eléctrica"), ("frio", "Frío extremo", "−10 °C o menos de madrugada")]


def mapa_calor(f):
    cab = "".join(f"<th scope='col'>{fecha_corta(x['fecha'])[0]}</th>" for x in f["dias"])
    filas = []
    for k, nombre, regla in RIESGOS:
        celdas = []
        for x in f["dias"]:
            p = x["p"][k]
            if p is None:
                celdas.append(f"<td class='sin' title='{fecha_corta(x['fecha'])[1]}: sin dato'>–</td>")
            else:
                celdas.append(f"<td class='{'bajo' if p < 10 else ''}' style='--p:{p:.0f}' title='{fecha_corta(x['fecha'])[1]}: {num(p, 0)} % de los escenarios con {nombre.lower()}'>{num(p, 0)}</td>")
        filas.append(f"<tr><th scope='row' class='l'>{nombre}<br><span class='small muted' style='font-weight:400'>{regla}</span></th>{''.join(celdas)}</tr>")
    return (f"<div class='tabla'><table class='calor' aria-label='Porcentaje de escenarios con cada riesgo, por día'><thead><tr><th class='l'>Riesgo</th>{cab}</tr></thead>"
            f"<tbody>{''.join(filas)}</tbody></table></div>")


def resumen_faena(f):
    partes = []
    for k, nombre, _ in RIESGOS:
        vals = [(x["p"][k], x["fecha"]) for x in f["dias"] if x["p"][k] is not None]
        if not vals:
            continue
        p, fecha = max(vals)
        if p >= 20:
            partes.append(f"{nombre.lower()} el {fecha_corta(fecha)[1]} ({num(p, 0)} % de los escenarios)")
    if not partes:
        return "En los próximos 15 días ningún riesgo llega al 20 % de los escenarios."
    return "Lo más probable en los próximos 15 días: " + "; ".join(partes) + "."


def tabla_faena(f):
    r = lambda v, u="": "–" if v is None else f"{num(v, 0)}{u}"
    filas = "".join(
        f"<tr><td class='l'>{fecha_corta(x['fecha'])[0]}</td>"
        f"<td class='num'>{r(x['t_madrugada'][1], ' °C')} <span class='muted'>({r(x['t_madrugada'][0])} a {r(x['t_madrugada'][2])})</span></td>"
        f"<td class='num'>{r(x['t_tarde'][1], ' °C')} <span class='muted'>({r(x['t_tarde'][0])} a {r(x['t_tarde'][2])})</span></td>"
        f"<td class='num'>{r(x['v'][1], ' km/h')} <span class='muted'>(hasta {r(x['v'][2])})</span></td>"
        f"<td class='num'>{num(x['nieve'][0], 1)} mm <span class='muted'>(hasta {num(x['nieve'][1], 1)})</span></td>"
        f"<td class='num'>{num(x['convectivo'][0], 1)} mm <span class='muted'>(hasta {num(x['convectivo'][1], 1)})</span></td></tr>" for x in f["dias"])
    return ("<div class='tabla'><table><thead><tr><th class='l'>Día</th><th>Madrugada</th><th>Tarde</th><th>Viento</th><th>Nieve (agua)</th><th>Convectiva</th></tr></thead>"
            "<tbody>" + filas + "</tbody></table></div>")


def bloque_faena(f, a):
    grilla = (f"El cuadrado de 25 km del modelo tiene el terreno a {num(f['altura_grilla_m'], 0)} m; la temperatura se llevó a {num(float(f['altitud_m']), 0)} m "
              f"({'+' if f['correccion_c'] > 0 else ''}{num(f['correccion_c'], 1)} °C).") if f.get("altura_grilla_m") is not None else ""
    lat, lon = abs(float(f["lat"])), abs(float(f["lon"]))
    gms = lambda v: f"{int(v)}°{round((v - int(v)) * 60):02d}′"
    return f'''<section class="seccion-faena">
  <div class="sec-head"><h2>{f["faena"]}</h2><p class="small muted">{f["descripcion"]} · comuna de {f["comuna"]}, {f["region"]} · {gms(lat)}S {gms(lon)}W · {num(float(f["altitud_m"]), 0)} m</p></div>
  <p>{resumen_faena(f)}</p>
  <div class="card">{mapa_calor(f)}
  <div class="calor-escala"><span>0 %</span><i></i><span>100 % de los {a["miembros"]} escenarios</span><span>· corrida del {hora_chile(a["corrida"])}</span></div></div>
  <details><summary>Temperatura, viento y nieve de cada día</summary><div class="body"><p class="small muted">Valor central de los escenarios y, entre paréntesis, el rango del 80 % central o el valor que supera solo uno de cada diez escenarios. Madrugada: 03 h de Chile; tarde: 15 h. {grilla}</p>{tabla_faena(f)}</div></details>
</section>'''



def fecha_corta(iso):
    import datetime as dt
    f = dt.date.fromisoformat(iso)
    return f"{DIAS[f.weekday()]} {f.day}", f"{f.day} {MESES[f.month - 1]}"


def svg_barras(dias):
    W, H, ml, mb, mt = 720, 200, 34, 34, 14
    n = len(dias); ancho = (W - ml - 8) / n
    y = lambda p: mt + (H - mt - mb) * (1 - p / 100)
    out = []
    for t in (0, 25, 50, 75, 100):
        out.append(f'<line class="grid-l" x1="{ml}" x2="{W - 4}" y1="{y(t):.1f}" y2="{y(t):.1f}"/><text class="eje" x="{ml - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{t}%</text>')
    for i, dd in enumerate(dias):
        x = ml + i * ancho + 3; w = ancho - 6
        pa, pc = dd["p_alta"], dd["p_critica"]
        if pa > 0:
            out.append(f'<rect class="alta" x="{x:.1f}" y="{y(pa):.1f}" width="{w:.1f}" height="{y(0) - y(pa):.1f}" rx="3"><title>{dd["fecha"]}: {num(pa, 0)} % alta o crítica</title></rect>')
        if pc > 0:
            out.append(f'<rect class="critica" x="{x:.1f}" y="{y(pc):.1f}" width="{w:.1f}" height="{y(0) - y(pc):.1f}" rx="3"><title>{dd["fecha"]}: {num(pc, 0)} % crítica</title></rect>')
        if pa >= 10:
            out.append(f'<text class="val" x="{x + w / 2:.1f}" y="{y(pa) - 4:.1f}" text-anchor="middle">{num(pa, 0)}</text>')
        dia, _ = fecha_corta(dd["fecha"])
        out.append(f'<text class="dia" x="{x + w / 2:.1f}" y="{H - 14}" text-anchor="middle">{dia}</text>')
    return f'<svg class="barras" viewBox="0 0 {W} {H}" role="img" aria-label="Porcentaje de escenarios en condición alta o crítica por día">{"".join(out)}</svg>'


def tabla_dias(dias):
    filas = "".join(
        f"<tr><td class='l'>{fecha_corta(x['fecha'])[0]}</td><td class='num'>{num(x['p_alta'], 0)} %</td><td class='num'>{num(x['p_critica'], 0)} %</td>"
        f"<td class='num'>{num(x['t'][1], 0)} °C <span class='muted'>({num(x['t'][0], 0)}–{num(x['t'][2], 0)})</span></td>"
        f"<td class='num'>{num(x['hr'][1], 0)} % <span class='muted'>({num(x['hr'][0], 0)}–{num(x['hr'][2], 0)})</span></td>"
        f"<td class='num'>{num(x['v'][1], 0)} km/h <span class='muted'>({num(x['v'][0], 0)}–{num(x['v'][2], 0)})</span></td>"
        f"<td class='num'>{x['secos_p50']}</td></tr>" for x in dias)
    return ("<div class='tabla'><table><thead><tr><th class='l'>Día</th><th>Alta o crítica</th><th>Crítica</th><th>Temperatura</th>"
            "<th>Humedad</th><th>Viento</th><th>Días sin lluvia</th></tr></thead><tbody>" + filas + "</tbody></table></div>")


def como_cambia(comuna, hist):
    filas = [h for h in hist if h["comuna"] == comuna]
    corridas = sorted({h["corrida"] for h in filas})[-5:]
    if len(corridas) < 2:
        return "<p class='small muted'>Cuando haya más de una corrida, aquí se verá cómo cambia la probabilidad de un mismo día a medida que se acerca.</p>"
    objetivos = sorted({h["fecha_objetivo"] for h in filas if h["corrida"] == corridas[-1]})[:7]
    idx = {(h["corrida"], h["fecha_objetivo"]): h for h in filas}
    cab = "".join(f"<th>{c[8:10]}/{c[5:7]} {c[11:13]}h</th>" for c in corridas)
    cuerpo = "".join("<tr><td class='l'>" + fecha_corta(o)[0] + "</td>" + "".join(
        f"<td class='num'>{num(float(idx[(c, o)]['p_alta']), 0)} %</td>" if (c, o) in idx else "<td class='num muted'>–</td>" for c in corridas) + "</tr>"
        for o in objetivos)
    return ("<p class='small muted'>Porcentaje de escenarios en condición alta o crítica para cada día, según la corrida (fecha y hora UTC).</p>"
            f"<div class='tabla'><table><thead><tr><th class='l'>Día</th>{cab}</tr></thead><tbody>{cuerpo}</tbody></table></div>")


def render():
    try:
        a = json.load(open(os.path.join(AQUI, "data", "actual.json"), encoding="utf-8"))
    except FileNotFoundError:
        print("sin escenarios todavía"); return
    try:
        hist = list(csv.DictReader(open(os.path.join(AQUI, "data", "historial.csv"), encoding="utf-8")))
    except FileNotFoundError:
        hist = []
    u = a["umbrales"]
    faenas = "".join(bloque_faena(f, a) for f in a.get("faenas", []))
    opciones = "".join(f'<option value="{i}">{c["comuna"]} · {c["region"]}</option>' for i, c in enumerate(a["comunas"]))
    bloques = []
    for i, c in enumerate(a["comunas"]):
        mx = max(c["dias"], key=lambda x: x["p_alta"])
        resumen = (f"En los próximos 15 días, el día con más escenarios en condición alta o crítica es el {fecha_corta(mx['fecha'])[1]}: {num(mx['p_alta'], 0)} % de los escenarios."
                   if mx["p_alta"] >= 1 else "En los próximos 15 días, ningún escenario llega a condición alta o crítica.")
        bloques.append(f'''<div class="comuna{' visible' if i == 0 else ''}" data-i="{i}">
  <div class="sec-head"><h2>{c["comuna"]}</h2><p class="small muted">{c["region"]} · {c["criterio"]} (<a href="{c["fuente"]}" rel="noopener">fuente</a>)</p></div>
  <p>{resumen}</p>
  <div class="card">{svg_barras(c["dias"])}
  <div class="ley"><span class="a"><i></i>Condición alta o crítica</span><span class="c"><i></i>Condición crítica (30-30-30)</span><span>Porcentaje de los {a["miembros"]} escenarios</span></div></div>
  <details><summary>Temperatura, humedad y viento de cada día</summary><div class="body"><p class="small muted">Valor central de los escenarios y, entre paréntesis, el rango del 80 % central, a las 18 UTC (15 h de Chile en horario de verano, 14 h en invierno).</p>{tabla_dias(c["dias"])}</div></details>
  <details><summary>Cómo cambia la probabilidad a medida que se acerca el día</summary><div class="body">{como_cambia(c["comuna"], hist)}</div></details>
</div>''')
    regla = d("30-30-30", definicion=f"Regla que usa CONAF: temperatura de {num(u['t'], 0)} °C o más, humedad de {num(u['hr'], 0)} % o menos y viento de {num(u['v'], 0)} km/h o más, al mismo tiempo.")
    html = f"""{head("Escenarios · Earth-2 Chile", "Probabilidad de viento, nieve, tormenta y frío en una faena minera, y de tiempo propicio para incendios por comuna, en los próximos 15 días, con los 50 escenarios del ensamble de IA de ECMWF. Indicador de apoyo, no alerta.")}
<body>
{nav("escenarios")}
<div class="wrap">
<header>
  <div class="eyebrow">Escenarios a 15 días</div>
  <h1>¿Qué podría pasar en las próximas dos semanas?</h1>
  <p class="lead">El modelo de IA de ECMWF calcula 50 escenarios posibles del tiempo a 15 días. Contamos en cuántos de ellos se da cada condición: así se ve qué tan probable es, día por día.</p>
  <div class="aviso"><p class="small">Es un indicador de apoyo a la decisión, no una alerta. Los avisos y alertas oficiales son de la <a href="https://www.meteochile.gob.cl/" rel="noopener">Dirección Meteorológica de Chile</a>, de <a href="https://www.senapred.cl/" rel="noopener">SENAPRED</a> y, para incendios, de <a href="https://www.conaf.cl/" rel="noopener">CONAF</a>.</p></div>
</header>
{faenas}
<section class="sec-head"><h2>Tiempo de incendio por comuna</h2><p>Cuántos escenarios cumplen la regla {regla} en cada comuna, o casi la cumplen después de varios días sin lluvia.</p></section>
<section class="card">
  <div class="controles"><label for="comuna" class="eyebrow">Comuna</label> <select id="comuna">{opciones}</select></div>
  <p class="small muted">Corrida del {hora_chile(a["corrida"])}. Comunas incluidas por ahora: las nombradas públicamente como prioritarias para la temporada en estas regiones; la lista oficial completa de CONAF aún no está publicada.</p>
</section>
{''.join(bloques)}
<details><summary>Cómo se calcula</summary><div class="body">
  <p>Fuente: AIFS-ENS, el ensamble de inteligencia artificial de ECMWF (50 escenarios, grilla de 0,25°, datos abiertos CC-BY 4.0). Para cada comuna se toma el punto de grilla más cercano y, cada día, la temperatura, la humedad relativa (calculada desde el punto de rocío) y el viento a 10 m de las 18 UTC, y la lluvia acumulada del día.</p>
  <p>Condición crítica: se cumplen a la vez las tres partes de la regla 30-30-30. Condición alta: se cumplen al menos dos y la comuna lleva {u["dias_secos"]} días o más sin lluvia dentro del pronóstico. El porcentaje es la parte de los escenarios en esa condición.</p>
  <p>Faena: con los mismos escenarios se cuenta, cada día, viento de {num(a.get("umbrales_faena", {}).get("viento", 50), 0)} km/h o más a 10 m a las 18 UTC; nevada de 2 mm o más de agua equivalente (unos 2 cm de nieve) y precipitación convectiva de 2 mm o más entre las 18 UTC de un día y las del siguiente; y −10 °C o menos a las 06 UTC. La temperatura del cuadrado de 25 km se lleva a la altura de la faena con 6,5 °C por kilómetro. El modelo no pronostica rayos: la precipitación convectiva es el indicio de tormenta. El viento se mira a una sola hora del día, así que una ráfaga de otra hora no aparece; en un relieve tan marcado, el viento real en la faena puede ser bastante mayor o menor que el del cuadrado de 25 km.</p>
  <p>Límites: en comunas cercanas a la costa, como Quilpué o Tomé, el cuadrado de 25 km más cercano incluye mar, así que la temperatura sale más baja y la humedad más alta que en los valles del interior; el indicador queda por debajo de lo que se viviría tierra adentro. Es la misma brecha que mide la sección Tu zona. Además, la grilla no ve el viento de quebradas y laderas, ni el estado del combustible; los días sin lluvia se cuentan desde el inicio del pronóstico, no desde la última lluvia real. El índice canadiense FWI no se calcula porque necesita la humedad del combustible de días anteriores, que el ensamble no trae.</p>
</div></details>
{pie(a["generado"])}
</div>
<script>
document.getElementById('comuna').addEventListener('change', e => {{
  document.querySelectorAll('.comuna').forEach(b => b.classList.toggle('visible', b.dataset.i === e.target.value));
}});
</script>
{JS_DEF}
</body>
</html>
"""
    kb = escribir("escenarios.html", html.replace("</style>", CSS_ESC + "</style>", 1))
    print(f"site/escenarios.html listo ({kb} KB)")


if __name__ == "__main__":
    render()
