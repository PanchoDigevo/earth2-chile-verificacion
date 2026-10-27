"""Genera site/escenarios.html (pestaña Escenarios) desde escenarios/data/actual.json e historial.csv."""
import csv, json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "verificacion"))
from render_site import head, escribir, proj, contorno_path, FRANJAS   # noqa: E402
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
/* catálogo */
.destacados{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.destacados button{all:unset;cursor:pointer;display:grid;gap:4px;border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px;background:var(--surface);min-width:0}
.destacados button:hover,.destacados button:focus-visible{border-color:var(--accent);outline:none}
.destacados button.sel{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
.destacados .k{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600}
.destacados .t{font-family:var(--font-display);font-weight:600;font-size:16px;line-height:1.2}
.destacados .v{font-family:var(--font-display);font-size:26px;font-weight:600;line-height:1.1}
.destacados .d{font-size:13.5px;color:var(--muted)}
.destacados .d strong{color:var(--fg)}
.controles-esc{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center}
.controles-esc select{font:inherit;font-size:15px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg);max-width:100%}
.dias-esc{display:flex;flex-wrap:wrap;gap:4px}
.dias-esc button{font:600 12.5px var(--font-body);padding:5px 8px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}
.dias-esc button.sel{background:var(--accent);border-color:var(--accent);color:#fff}
.mapa-esc{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:flex-start;justify-content:center}
.mapa-esc figure{margin:0;display:grid;gap:4px;justify-items:center}
.mapa-esc figcaption{font-size:12.5px;color:var(--muted)}
.mapa-esc svg{max-width:100%;height:auto}
.mapa-esc .tierra{fill:var(--tierra);stroke:var(--costa);stroke-width:.8}
.mapa-esc circle.co{fill:color-mix(in srgb,var(--p-critica) calc(var(--p) * 1%),var(--surface));stroke:var(--surface);stroke-width:.6;cursor:pointer}
.mapa-esc circle.co.cero{fill:var(--line)}
.mapa-esc circle.co.sel{stroke:var(--fg);stroke-width:2}
.mapa-esc-escala{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--muted)}
.mapa-esc-escala i{display:inline-block;width:120px;height:10px;border-radius:3px;background:linear-gradient(90deg,var(--surface),var(--p-critica));outline:1px solid var(--line-soft)}
.mapa-esc-top{font-size:14.5px;margin:0}
.tabs-sec{display:flex;flex-wrap:wrap;gap:6px}
.tabs-sec button{font:600 14px var(--font-body);padding:7px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}
.tabs-sec button[aria-selected=true]{background:var(--accent);border-color:var(--accent);color:#fff}
.sector-bloque{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.sector-bloque .card h3{margin:0 0 2px;font-size:15.5px}
.sector-bloque .card .regla{font-size:13px;color:var(--muted);margin:0 0 6px}
.sector-bloque table{font-size:14px}
.sector-bloque td.l a{color:inherit;text-decoration:none;border-bottom:1px dotted var(--muted)}
.sector-bloque .nada{font-size:14px;color:var(--muted);margin:0}
.calor td.p0{background:var(--surface);color:var(--muted)}
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


PRINCIPALES = ["helada", "calor", "lluvia5", "lluvia20", "viento50", "nieve", "tormenta", "frio", "incendio_alta", "nublado"]


def mapa_comunas(com):
    """Las tres franjas del país con un círculo por comuna (data-id); el color lo pone el JS según escenario y día."""
    path = contorno_path()
    if not path:
        return ""
    figs = []
    for titulo, la0, la1, lo0, lo1 in FRANJAS:
        x0, y0 = proj(lo0, la0); x1, y1 = proj(lo1, la1)
        w, h = x1 - x0, y1 - y0
        pts = []
        for k, c in com.items():
            if la1 <= c["lat"] <= la0 and lo0 <= c["lon"] <= lo1:
                x, y = proj(c["lon"], c["lat"])
                pts.append(f'<circle class="co" data-id="{k}" cx="{x:.1f}" cy="{y:.1f}" r="4" style="--p:0"><title>{c["n"]}</title></circle>')
        figs.append(f'<figure><svg viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" role="group" aria-label="Zona {titulo.lower()}">'
                    f'<use href="#chile-esc" class="tierra"/>{"".join(pts)}</svg><figcaption>{titulo}</figcaption></figure>')
    return (f'<svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs><path id="chile-esc" d="{path}"/></defs></svg>'
            f'<div class="mapa-esc">{"".join(figs)}</div>')


JS_ESC = r"""
<script>
(function(){
  const E = window.ESC; if (!E) return;
  const $ = s => document.querySelector(s), n = v => Number(v).toLocaleString('es-CL');
  const DIAS = ['dom','lun','mar','mié','jue','vie','sáb'], MES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  const fcorta = iso => { const f = new Date(iso + 'T12:00'); return DIAS[f.getDay()] + ' ' + f.getDate(); };
  const flarga = iso => { const f = new Date(iso + 'T12:00'); return f.getDate() + ' ' + MES[f.getMonth()]; };
  const esc = {}; E.escenarios.forEach(e => esc[e.id] = e);
  const ids = Object.keys(E.comunas);
  const pde = (id, k) => (E.comunas[id].p[k] || null);
  // máximo de un escenario en una comuna: [p, índice del día]
  const maxDe = (id, k) => { const a = pde(id, k); if (!a) return [0, -1]; let m = 0, i = -1; a.forEach((v, j) => { if (v > m) { m = v; i = j; } }); return [m, i]; };
  const ranking = (k, nmax) => ids.map(id => [id, ...maxDe(id, k)]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, nmax);
  const st = {k: 'lluvia20', d: 0, c: null};

  // 1. destacados
  const cajaD = $('#destacados');
  cajaD.innerHTML = E.principales.map(k => { const r = ranking(k, 4), e = esc[k];
    const top = r[0] ? `<span class="v">${r[0][1]} %</span><span class="d"><strong>${E.comunas[r[0][0]].n}</strong> · ${fcorta(E.fechas[r[0][2]])}</span>` : `<span class="v">0 %</span><span class="d">en ninguna comuna</span>`;
    const otras = r.slice(1).map(x => `${E.comunas[x[0]].n} ${x[1]} %`).join(' · ');
    return `<button type="button" data-k="${k}" class="${k === st.k ? 'sel' : ''}"><span class="k">${e.sectores.map(s => E.sectores.find(x => x[0] === s)[1]).slice(0, 2).join(' · ')}</span><span class="t">${e.nombre}</span>${top}<span class="d">${otras || e.regla}</span></button>`; }).join('');
  cajaD.addEventListener('click', ev => { const b = ev.target.closest('button[data-k]'); if (!b) return; st.k = b.dataset.k; $('#sel-esc').value = st.k; pintar(); $('#mapa-esc-sec').scrollIntoView({behavior: 'smooth', block: 'start'}); });

  // 2. mapa
  $('#sel-esc').innerHTML = E.escenarios.map(e => `<option value="${e.id}">${e.nombre} · ${e.regla}</option>`).join('');
  $('#sel-esc').value = st.k;
  $('#dias-esc').innerHTML = E.fechas.map((f, i) => `<button type="button" data-d="${i}">${fcorta(f)}</button>`).join('');
  $('#sel-esc').addEventListener('change', e => { st.k = e.target.value; pintar(); });
  $('#dias-esc').addEventListener('click', ev => { const b = ev.target.closest('button[data-d]'); if (!b) return; st.d = +b.dataset.d; pintar(); });
  document.querySelectorAll('.mapa-esc circle.co').forEach(c => c.addEventListener('click', () => { st.c = c.dataset.id; $('#sel-com').value = st.c; pintarComuna(); $('#com-sec').scrollIntoView({behavior: 'smooth', block: 'start'}); }));
  function pintar() {
    document.querySelectorAll('#destacados button').forEach(b => b.classList.toggle('sel', b.dataset.k === st.k));
    document.querySelectorAll('#dias-esc button').forEach(b => b.classList.toggle('sel', +b.dataset.d === st.d));
    const e = esc[st.k];
    document.querySelectorAll('.mapa-esc circle.co').forEach(c => { const a = pde(c.dataset.id, st.k), p = a ? a[st.d] : 0;
      c.style.setProperty('--p', p); c.classList.toggle('cero', !p); c.classList.toggle('sel', c.dataset.id === st.c);
      c.querySelector('title').textContent = `${E.comunas[c.dataset.id].n}: ${p} % de los escenarios con ${e.nombre.toLowerCase()} el ${flarga(E.fechas[st.d])}`; });
    const dia = ids.map(id => [id, (pde(id, st.k) || [])[st.d] || 0]).filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 6);
    $('#mapa-esc-top').innerHTML = `<strong>${e.nombre}</strong> (${e.regla}), ${flarga(E.fechas[st.d])}: ` + (dia.length ? 'más probable en ' + dia.map(x => `<a href="#com-sec" data-c="${x[0]}">${E.comunas[x[0]].n}</a> ${x[1]} %`).join(', ') + '.' : 'en ningún escenario, en ninguna comuna.');
    $('#mapa-esc-top').querySelectorAll('a[data-c]').forEach(a => a.addEventListener('click', ev => { ev.preventDefault(); st.c = a.dataset.c; $('#sel-com').value = st.c; pintarComuna(); $('#com-sec').scrollIntoView({behavior: 'smooth', block: 'start'}); }));
  }

  // 3. por comuna
  const porRegion = {}; ids.forEach(id => (porRegion[E.comunas[id].r] = porRegion[E.comunas[id].r] || []).push(id));
  $('#sel-com').innerHTML = Object.keys(porRegion).sort().map(r => `<optgroup label="${r}">${porRegion[r].sort((a, b) => E.comunas[a].n.localeCompare(E.comunas[b].n)).map(id => `<option value="${id}">${E.comunas[id].n}</option>`).join('')}</optgroup>`).join('');
  st.c = (location.hash.match(/#c=(Q\d+)/) || [])[1] || (ranking('lluvia20', 1)[0] || [ids[0]])[0];
  $('#sel-com').value = st.c;
  $('#sel-com').addEventListener('change', e => { st.c = e.target.value; pintarComuna(); });
  function pintarComuna() {
    const c = E.comunas[st.c]; if (!c) return;
    $('#com-nombre').textContent = c.n; $('#com-region').textContent = c.r;
    $('#com-pron').href = 'pronostico.html#' + st.c;
    const cab = E.fechas.map(f => `<th scope="col">${fcorta(f)}</th>`).join('');
    const filas = E.escenarios.map(e => { const a = pde(st.c, e.id);
      return `<tr><th scope="row" class="l">${e.nombre}<br><span class="small muted" style="font-weight:400">${e.regla}</span></th>` +
        E.fechas.map((f, i) => { const p = a ? a[i] : 0; return `<td class="${p ? (p < 10 ? 'bajo' : '') : 'p0'}" style="--p:${p}" title="${flarga(f)}: ${p} % de los escenarios">${p}</td>`; }).join('') + '</tr>'; }).join('');
    $('#com-tabla').innerHTML = `<table class="calor" aria-label="Porcentaje de escenarios con cada caso, por día, en ${c.n}"><thead><tr><th class="l">Caso</th>${cab}</tr></thead><tbody>${filas}</tbody></table>`;
    const tops = E.escenarios.map(e => [e, ...maxDe(st.c, e.id)]).filter(x => x[1] >= 20).sort((a, b) => b[1] - a[1]).slice(0, 4);
    $('#com-resumen').innerHTML = tops.length ? 'Lo más probable en los próximos 15 días: ' + tops.map(x => `${x[0].nombre.toLowerCase()} el ${flarga(E.fechas[x[2]])} (${x[1]} %)`).join('; ') + '.' : 'En los próximos 15 días ningún caso del catálogo llega al 20 % de los escenarios en esta comuna.';
    document.querySelectorAll('.mapa-esc circle.co').forEach(x => x.classList.toggle('sel', x.dataset.id === st.c));
    try { history.replaceState(null, '', '#c=' + st.c); } catch (e) {}
  }

  // 4. por sector
  const tabs = $('#tabs-sec');
  tabs.innerHTML = E.sectores.map(([k, nm], i) => `<button type="button" role="tab" data-s="${k}" aria-selected="${i === 0}">${nm}</button>`).join('');
  let sec = E.sectores[0][0];
  tabs.addEventListener('click', ev => { const b = ev.target.closest('button[data-s]'); if (!b) return; sec = b.dataset.s; tabs.querySelectorAll('button').forEach(x => x.setAttribute('aria-selected', x === b)); pintarSector(); });
  function pintarSector() {
    const lista = E.escenarios.filter(e => e.sectores.includes(sec));
    $('#sector-bloque').innerHTML = lista.map(e => { const r = ranking(e.id, 8);
      return `<div class="card"><h3>${e.nombre}</h3><p class="regla">${e.regla}</p>` + (r.length ? `<div class="tabla"><table><thead><tr><th class="l">Comuna</th><th>Escenarios</th><th class="l">Día</th></tr></thead><tbody>` +
        r.map(x => `<tr><td class="l"><a href="#com-sec" data-c="${x[0]}">${E.comunas[x[0]].n}</a> <span class="small muted">${E.comunas[x[0]].r}</span></td><td class="num">${x[1]} %</td><td class="l">${fcorta(E.fechas[x[2]])}</td></tr>`).join('') + '</tbody></table></div>' : '<p class="nada">En ninguna comuna en los próximos 15 días.</p>') + '</div>'; }).join('');
    $('#sector-bloque').querySelectorAll('a[data-c]').forEach(a => a.addEventListener('click', ev => { ev.preventDefault(); st.c = a.dataset.c; $('#sel-com').value = st.c; pintarComuna(); $('#com-sec').scrollIntoView({behavior: 'smooth', block: 'start'}); }));
  }
  pintar(); pintarComuna(); pintarSector();
})();
</script>"""


def catalogo_html(E):
    return f"""<section class="sec-head"><h2>Lo que más se repite en los 50 escenarios</h2><p>Para cada caso del catálogo, la comuna y el día donde más escenarios lo dan en los próximos 15 días. Toca un caso para verlo en el mapa.</p></section>
<div class="destacados" id="destacados"></div>
<section class="sec-head" id="mapa-esc-sec"><h2>Dónde y cuándo</h2><p>Elige un caso y un día: cada punto es una comuna y su color, el porcentaje de los escenarios.</p></section>
<section class="card">
  <div class="controles-esc"><label for="sel-esc" class="eyebrow">Caso</label> <select id="sel-esc"></select></div>
  <div class="dias-esc" id="dias-esc" role="group" aria-label="Día"></div>
  <p class="mapa-esc-top" id="mapa-esc-top"></p>
  {mapa_comunas(E["comunas"])}
  <div class="mapa-esc-escala"><span>0 %</span><i></i><span>100 % de los {E["miembros"]} escenarios</span><span>· corrida del {hora_chile(E["corrida"])}</span></div>
</section>
<section class="sec-head" id="com-sec"><h2>Todos los casos en tu comuna</h2><p>Los 16 casos del catálogo, día por día, para la comuna que elijas.</p></section>
<section class="card">
  <div class="controles-esc"><label for="sel-com" class="eyebrow">Comuna</label> <select id="sel-com"></select> <a id="com-pron" href="pronostico.html">Ver su pronóstico →</a></div>
  <div class="sec-head"><h2 id="com-nombre"></h2><p class="small muted" id="com-region"></p></div>
  <p id="com-resumen"></p>
  <div class="tabla" id="com-tabla"></div>
  <div class="calor-escala"><span>0 %</span><i></i><span>100 % de los {E["miembros"]} escenarios</span></div>
</section>
<section class="sec-head"><h2>Por sector</h2><p>Para quien decide en cada rubro: las comunas donde cada caso es más probable en los próximos 15 días.</p></section>
<div class="tabs-sec" id="tabs-sec" role="tablist"></div>
<div class="sector-bloque" id="sector-bloque"></div>"""


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
    try:
        E = json.load(open(os.path.join(AQUI, "..", "site", "datos", "escenarios_15d.json"), encoding="utf-8"))
    except FileNotFoundError:
        E = None
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
{catalogo_html(E) if E else ""}
<section class="sec-head" id="faenas-sec"><h2>Faenas</h2><p>Riesgos de faena con los mismos 50 escenarios, llevando la temperatura a la altura del lugar.</p></section>
{faenas}
<section class="sec-head"><h2>Tiempo de incendio en las comunas prioritarias</h2><p>Cuántos escenarios cumplen la regla {regla} en cada comuna, o casi la cumplen después de varios días sin lluvia; con el registro de cómo cambió la probabilidad corrida a corrida.</p></section>
<section class="card">
  <div class="controles"><label for="comuna" class="eyebrow">Comuna</label> <select id="comuna">{opciones}</select></div>
  <p class="small muted">Corrida del {hora_chile(a["corrida"])}. Comunas incluidas por ahora: las nombradas públicamente como prioritarias para la temporada en estas regiones; la lista oficial completa de CONAF aún no está publicada.</p>
</section>
{''.join(bloques)}
<details><summary>Cómo se calcula</summary><div class="body">
  <p>Fuente: AIFS-ENS, el ensamble de inteligencia artificial de ECMWF (50 escenarios, grilla de 0,25°, datos abiertos CC-BY 4.0). Para cada comuna se toma el punto de grilla más cercano y, cada día, la temperatura, la humedad relativa (calculada desde el punto de rocío) y el viento a 10 m de las 18 UTC, y la lluvia acumulada del día.</p>
  <p>Condición crítica: se cumplen a la vez las tres partes de la regla 30-30-30. Condición alta: se cumplen al menos dos y la comuna lleva {u["dias_secos"]} días o más sin lluvia dentro del pronóstico. El porcentaje es la parte de los escenarios en esa condición.</p>
  <p>Faena: con los mismos escenarios se cuenta, cada día, viento de {num(a.get("umbrales_faena", {}).get("viento", 50), 0)} km/h o más a 10 m a las 18 UTC; nevada de 2 mm o más de agua equivalente (unos 2 cm de nieve) y precipitación convectiva de 2 mm o más entre las 18 UTC de un día y las del siguiente; y −10 °C o menos a las 06 UTC. La temperatura del cuadrado de 25 km se lleva a la altura de la faena con 6,5 °C por kilómetro. El modelo no pronostica rayos: la precipitación convectiva es el indicio de tormenta. El viento se mira a una sola hora del día, así que una ráfaga de otra hora no aparece; en un relieve tan marcado, el viento real en la faena puede ser bastante mayor o menor que el del cuadrado de 25 km.</p>
  <p>Catálogo por comuna: para las 352 comunas de Chile se cuenta, con los mismos 50 escenarios y el punto de grilla de 25 km más cercano al centro de la comuna, en cuántos se da cada caso: helada (0 °C o menos a las 06 UTC) y helada fuerte (−3 °C); calor (32 °C o más a las 18 UTC) y calor extremo (35 °C); lluvia del día de 5, 20 y 40 mm o más; viento de 50 y 70 km/h o más a las 18 UTC; nevada de 2 y 10 mm de agua equivalente (unos 2 y 10 cm de nieve); chubasco convectivo de 2 mm o más (tormenta posible); frío extremo (−10 °C o menos a las 06 UTC); tiempo de incendio en condición alta y crítica; y día muy nublado (85 % o más de nubes a las 18 UTC). Los umbrales son los de uso común en los avisos de la DMC y en la agricultura, sin ajustar a ningún evento. La temperatura es la del cuadrado de 25 km, sin corregir por la altura del centro de la comuna: en comunas cordilleranas la helada y la nevada reales pueden ser más frecuentes que lo que dice el cuadrado, y en comunas costeras el calor menos frecuente que tierra adentro.</p>
  <p>Límites: en comunas cercanas a la costa, como Quilpué o Tomé, el cuadrado de 25 km más cercano incluye mar, así que la temperatura sale más baja y la humedad más alta que en los valles del interior; el indicador queda por debajo de lo que se viviría tierra adentro. Es la misma brecha que mide la sección Tu zona. Además, la grilla no ve el viento de quebradas y laderas, ni el estado del combustible; los días sin lluvia se cuentan desde el inicio del pronóstico, no desde la última lluvia real. El índice canadiense FWI no se calcula porque necesita la humedad del combustible de días anteriores, que el ensamble no trae.</p>
</div></details>
{pie(a["generado"])}
</div>
<script>
document.getElementById('comuna').addEventListener('change', e => {{
  document.querySelectorAll('.comuna').forEach(b => b.classList.toggle('visible', b.dataset.i === e.target.value));
}});
</script>
{("<script>window.ESC = " + json.dumps({**E, "principales": PRINCIPALES}, ensure_ascii=False, separators=(",", ":")) + ";</script>" + JS_ESC) if E else ""}
{JS_DEF}
</body>
</html>
"""
    kb = escribir("escenarios.html", html.replace("</style>", CSS_ESC + "</style>", 1))
    print(f"site/escenarios.html listo ({kb} KB)")


if __name__ == "__main__":
    render()
