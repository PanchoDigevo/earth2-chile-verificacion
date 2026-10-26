"""Respuesta por dirección: "¿Vives cerca de una quebrada?" en Quebradas y En vivo.

El navegador geocodifica la dirección con Nominatim (OpenStreetMap, sin clave; no se guarda nada) o usa la ubicación del
teléfono, y responde con una frase y un número: a cuántos metros está el cauce más cercano y de qué quebrada, si el punto
queda dentro de su cuenca, el nivel del indicador de quebradas con lo medido (pluviómetros a menos de 25 km, 2 h) y con lo
previsto (quebradas/indicador.json), y cuántos rayos hubo a menos de 8 km en los últimos 30 minutos (GOES-19). Todo se
calcula en el navegador con site/quebradas/cuencas.geojson y cauces.geojson (cauces del DEM y de OpenStreetMap).

Es cercanía a los cauces que seguimos (Santiago oriente), no una alerta ni una probabilidad para la casa. Fuera de la zona
seguida, solo informa la distancia a lo más cercano, la lluvia medida y los rayos.

Se incluye con html() y, en la página, JS después del script del mapa: lee window.MAPA_VIVO o window.MAPA_QUEBRADAS (Leaflet)
para marcar el punto, y window.ELEGIR_QUEBRADA (solo Quebradas) para abrir la ficha de la quebrada."""

RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/datos-en-vivo/envivo"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

CSS = """
.dir{display:grid;gap:10px}
.dir h2{margin:0}
.dir form{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px}
.dir input[type=search]{min-width:0;width:100%;font:inherit;font-size:16px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg)}
.dir input[type=search]:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.dir button{font:inherit;font-weight:600;font-size:15px;padding:10px 14px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer;white-space:nowrap}
.dir button.sec{background:var(--surface);color:var(--accent)}
.dir button:disabled{opacity:.6;cursor:default}
.dir .acciones{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.dir .estado{font-size:14px;color:var(--muted);margin:0;min-height:1.2em}
.dir .sug{display:grid;gap:4px;margin:0;padding:0;list-style:none}
.dir .sug button{text-align:left;background:var(--bg);color:var(--fg);border-color:var(--line);font-weight:500;white-space:normal}
.dir-res{border-top:1px solid var(--line-soft);padding-top:10px;display:grid;gap:10px}
.dir-res[hidden]{display:none}
.dir-res .frase{font-size:17px;margin:0;line-height:1.4}
.dir-res .frase strong.m{font-family:var(--font-display);font-size:24px}
.dir-chips{display:flex;flex-wrap:wrap;gap:6px;margin:0;padding:0;list-style:none}
.dir-chip{display:inline-flex;align-items:center;gap:6px;font-size:13.5px;font-weight:600;padding:3px 10px 3px 8px;border-radius:999px;border:1px solid var(--line);background:var(--bg)}
.dir-chip i{width:8px;height:8px;border-radius:50%;background:var(--sin,var(--muted))}
.dir-chip.n-bajo i{background:var(--bajo,var(--bueno))} .dir-chip.n-atencion i{background:var(--atencion,var(--medio))} .dir-chip.n-aviso i{background:var(--aviso,var(--alto))}
.dir-chip.rayos i{background:var(--aviso,var(--alto))}
.dir-escala{position:relative;height:10px;border-radius:5px;margin:4px 0 20px;background:linear-gradient(90deg,var(--aviso,var(--alto)) 0 25%,var(--atencion,var(--medio)) 25% 50%,var(--bajo,var(--bueno)) 50% 100%);opacity:.9}
.dir-escala b{position:absolute;top:-5px;width:20px;height:20px;border-radius:50%;background:var(--surface);border:3px solid var(--fg);transform:translateX(-50%);box-shadow:0 1px 3px rgba(0,0,0,.3)}
.dir-escala span{position:absolute;top:14px;transform:translateX(-50%);font-size:11.5px;color:var(--muted);white-space:nowrap}
.dir-res .nota{font-size:13px;color:var(--muted);margin:0}
.dir-res .nota a{color:inherit}
"""

JS = r"""<script>
(function(){
  const raiz = document.getElementById('dir'); if (!raiz) return;
  const RAW = '__RAW__', NOM = '__NOM__';
  const $ = s => raiz.querySelector(s);
  const n = (v, d) => v == null || isNaN(v) ? '–' : Number(v).toLocaleString('es-CL', {maximumFractionDigits: d || 0, minimumFractionDigits: d || 0});
  const corto = s => (s || '').split(' (')[0];
  const NIV = {bajo: 'bajo', atencion: 'atención', aviso: 'aviso'};
  // geometría: metros en un plano local
  const R = Math.PI / 180, K = 111320;
  const xy = (lat, lon, lat0) => [(lon) * K * Math.cos(lat0 * R), lat * K];
  function dSeg(p, a, b) { const vx = b[0] - a[0], vy = b[1] - a[1], wx = p[0] - a[0], wy = p[1] - a[1], l2 = vx * vx + vy * vy;
    const t = l2 ? Math.max(0, Math.min(1, (wx * vx + wy * vy) / l2)) : 0; const q = [a[0] + t * vx, a[1] + t * vy]; return {d: Math.hypot(p[0] - q[0], p[1] - q[1]), q}; }
  function dentro(lat, lon, anillo) { let c = false; for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) { const [xi, yi] = anillo[i], [xj, yj] = anillo[j];
    if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) c = !c; } return c; }
  const anillos = g => g.type === 'Polygon' ? [g.coordinates[0]] : g.coordinates.map(p => p[0]);
  function dLinea(p, coords, lat0) { let best = {d: Infinity, q: null}; for (let i = 1; i < coords.length; i++) { const r = dSeg(p, xy(coords[i - 1][1], coords[i - 1][0], lat0), xy(coords[i][1], coords[i][0], lat0)); if (r.d < best.d) best = r; } return best; }
  const km = (a, b) => 111.2 * Math.hypot(a[0] - b[0], (a[1] - b[1]) * Math.cos(a[0] * R));

  let D = null;
  async function j(u, op) { try { const r = await fetch(u, op); return r.ok ? await r.json() : null; } catch (e) { return null; } }
  async function datos() {
    if (D) return D;
    const [cu, ca, ind, ll, ry] = await Promise.all([j('quebradas/cuencas.geojson'), j('quebradas/cauces.geojson'), j('quebradas/indicador.json'),
      j(RAW + '/lluvia.json?t=' + Date.now()), j(RAW + '/rayos.json?t=' + Date.now())]);
    const cuencas = (cu ? cu.features : []).map(f => { const an = anillos(f.geometry), todo = an.flat();
      return {p: f.properties, an, lat: todo.reduce((s, c) => s + c[1], 0) / todo.length, lon: todo.reduce((s, c) => s + c[0], 0) / todo.length}; });
    const cauces = (ca ? ca.features : []).filter(f => f.geometry && f.geometry.type === 'LineString').map(f => { const c = f.geometry.coordinates, m = c[Math.floor(c.length / 2)];
      const cu = cuencas.find(q => q.an.some(a => dentro(m[1], m[0], a))); return {nombre: f.properties.nombre, coords: c, cuenca: cu ? cu.p.id : null}; });
    const porId = {}; ((ind && ind.cuencas) || []).forEach(c => porId[c.id] = c);
    D = {cuencas, cauces, ind, porId, ll, ry}; return D;
  }
  function medida2h(ll, lat, lon, ahora) {
    if (!ll || ahora - ll.generado > 3 * 3600) return null;
    let best = null;
    ll.estaciones.filter(e => e.alt < 1500 && km([lat, lon], [e.lat, e.lon]) <= 25).forEach(e => {
      const o = (ll.obs[e.wmo] || []).filter(x => x[0] > ahora - 2 * 3600 - 600 && x[1] != null); if (!o.length) return;
      const mm = o.reduce((s, x) => s + x[1], 0); if (!best || mm > best.mm) best = {mm, nombre: e.nombre.replace(/\s*\(([^)]*)\)/, ', $1'), km: km([lat, lon], [e.lat, e.lon])}; });
    return best;
  }
  function rayos30(ry, lat, lon, ahora) {
    if (!ry || ahora - ry.generado > 30 * 60) return null;
    return ry.rayos.filter(r => ahora - r[2] <= 30 * 60 && km([lat, lon], [r[0], r[1]]) <= 8).length;
  }
  function nivelDe(mm, c) { return !c || c.mm_atencion == null ? null : mm >= c.mm_aviso ? 'aviso' : mm >= c.mm_atencion ? 'atencion' : 'bajo'; }

  async function responder(lat, lon, etiqueta) {
    const d = await datos(), ahora = Date.now() / 1000, p = xy(lat, lon, lat);
    // cuenca que contiene el punto, o la más cercana por su borde
    let en = null, cerca = null;
    d.cuencas.forEach(c => { if (c.an.some(a => dentro(lat, lon, a))) { if (!en) en = {c, d: 0}; return; }
      const dd = Math.min(...c.an.map(a => dLinea(p, a, lat).d)); if (!cerca || dd < cerca.d) cerca = {c, d: dd}; });
    const ref = en || cerca;
    // cauce más cercano: de esa cuenca si tiene; si no, cualquiera
    const cand = ref ? d.cauces.filter(x => x.cuenca === ref.c.p.id) : [];
    let cauce = null;
    (cand.length ? cand : d.cauces).forEach(x => { const r = dLinea(p, x.coords, lat); if (!cauce || r.d < cauce.d) cauce = {x, d: r.d, q: r.q}; });
    const med = medida2h(d.ll, lat, lon, ahora), ray = rayos30(d.ry, lat, lon, ahora);
    const res = $('.dir-res'); res.hidden = false;
    const lejos = !ref || (ref.d > 20000);
    let frase, chips = [], escala = '', sal = null;
    if (lejos) {
      frase = `<p class="frase">${etiqueta} queda ${ref ? `a <strong class="m">${n(ref.d / 1000)} km</strong> de ${corto(ref.c.p.nombre)}, la más cercana de` : 'fuera de'} las quebradas que seguimos (Santiago oriente). No tenemos indicador para ese lugar.</p>`;
    } else {
      const q = ref.c.p, ind = d.porId[q.id], dm = cauce ? cauce.d : ref.d;
      const nomC = cauce && cauce.x.nombre && corto(cauce.x.nombre) !== corto(q.nombre) ? ` (${cauce.x.nombre})` : '';
      frase = en ? `<p class="frase">${etiqueta} está <strong>dentro de la cuenca</strong> de la <strong>${corto(q.nombre)}</strong>${q.comuna ? ' (' + q.comuna + ')' : ''}, a <strong class="m">${n(dm)} m</strong> de su cauce${nomC}.</p>`
                 : `<p class="frase">${etiqueta} está a <strong class="m">${n(dm)} m</strong> del cauce más cercano${nomC}, de la <strong>${corto(q.nombre)}</strong>${q.comuna ? ' (' + q.comuna + ')' : ''}; fuera de su cuenca.</p>`;
      const nm = med ? nivelDe(med.mm, ind) : null;
      if (ind && ind.mm_atencion != null) {
        chips.push(`<li class="dir-chip n-${nm || 'bajo'}"><i></i>Con lo medido: ${nm ? NIV[nm] : 'sin lluvia medida cerca'}${med ? ` (${n(med.mm, 1)} mm en 2 h, ${med.nombre})` : ''}</li>`);
        chips.push(`<li class="dir-chip n-${ind.nivel}"><i></i>Si cae lo previsto: ${NIV[ind.nivel] || ind.nivel}</li>`);
      } else chips.push(`<li class="dir-chip"><i></i>Sin indicador: esta quebrada casi no se quemó</li>`);
      // aguas abajo: la quebrada quemada cuya salida (donde el cauce entra a la ciudad) queda más cerca, si es otra
      d.cuencas.forEach(c => { const i = d.porId[c.p.id]; if (!i || i.mm_atencion == null || c.p.id === q.id || !c.p.salida) return;
        const dd = km([lat, lon], [c.p.salida[1], c.p.salida[0]]) * 1000; if (dd <= 3000 && (!sal || dd < sal.d)) sal = {c, i, d: dd}; });
      if (sal) { const nm2 = med ? nivelDe(med.mm, sal.i) : null;
        frase += `<p class="frase">La quebrada quemada más cercana es la <strong>${corto(sal.c.p.nombre)}</strong>: su salida a la ciudad está a <strong class="m">${n(sal.d)} m</strong>${sal.d < 1500 ? ', así que el agua que baje por ella puede llegar por las calles' : ''}.</p>`;
        chips.push(`<li class="dir-chip n-${nm2 || 'bajo'}"><i></i>${corto(sal.c.p.nombre)}, con lo medido: ${nm2 ? NIV[nm2] : 'sin lluvia medida cerca'}</li>`);
        chips.push(`<li class="dir-chip n-${sal.i.nivel}"><i></i>${corto(sal.c.p.nombre)}, si cae lo previsto: ${NIV[sal.i.nivel] || sal.i.nivel}</li>`); }
      const tope = 600, pos = Math.min(dm, tope) / tope * 100;
      escala = `<div class="dir-escala" role="img" aria-label="A ${n(dm)} m del cauce"><b style="left:${pos}%"></b><span style="left:0">cauce</span><span style="left:${100 / 6}%">100 m</span><span style="left:${100 / 3}%">200 m</span><span style="left:${200 / 3}%">400 m</span><span style="left:100%">600 m o más</span></div>`;
    }
    if (ray != null) chips.push(`<li class="dir-chip ${ray ? 'rayos' : ''}"><i></i>${ray ? `Tormenta encima: ${ray} ${ray === 1 ? 'rayo' : 'rayos'} a menos de 8 km en 30 min` : 'Sin rayos a menos de 8 km en 30 min'}</li>`);
    if (lejos && med) chips.push(`<li class="dir-chip"><i></i>Lluvia medida: ${n(med.mm, 1)} mm en 2 h (${med.nombre})</li>`);
    const q = ref && !lejos ? ref.c.p : null, q2 = sal ? sal.c.p : null;
    res.innerHTML = frase + (chips.length ? `<ul class="dir-chips">${chips.join('')}</ul>` : '') + escala +
      `<div class="acciones"><button type="button" class="sec" data-ver>Ver en el mapa</button>${q ? (window.ELEGIR_QUEBRADA ? `<button type="button" class="sec" data-q="${(q2 || q).id}">Ver datos de la ${corto((q2 || q).nombre)}</button>` : `<a href="quebradas.html">Ver la quebrada y sus umbrales</a>`) : ''}</div>
      <p class="nota">Cercanía al cauce trazado con el relieve y OpenStreetMap; no es una alerta ni una probabilidad para esta casa. «Con lo medido»: lluvia de la estación más lluviosa a menos de 25 km en las últimas 2 h, comparada con los umbrales del <a href="quebradas.html">indicador de quebradas</a>; ahí donde hay tormenta encima, la lluvia puede ser mayor que la medida. Alertas oficiales: <a href="https://www.senapred.cl/alertas-vigentes/" rel="noopener">SENAPRED</a> y <a href="https://www.meteochile.gob.cl/" rel="noopener">DMC</a>. La dirección no se guarda.</p>`;
    marcar(lat, lon, cauce && !lejos ? cauce.q : null, etiqueta);
    res.querySelector('[data-ver]').addEventListener('click', () => marcar(lat, lon, cauce && !lejos ? cauce.q : null, etiqueta, true));
    const bq = res.querySelector('[data-q]'); if (bq) bq.addEventListener('click', () => window.ELEGIR_QUEBRADA(Number(bq.dataset.q), true));
    try { history.replaceState(null, '', '#d=' + lat.toFixed(5) + ',' + lon.toFixed(5)); } catch (e) {}
  }
  let capa = null;
  function marcar(lat, lon, q, etiqueta, ir) {
    const mapa = window.MAPA_QUEBRADAS || window.MAPA_VIVO; if (!mapa || !window.L) return;
    if (!capa) capa = L.layerGroup().addTo(mapa); capa.clearLayers();
    const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
    L.circleMarker([lat, lon], {radius: 8, color: css('--surface'), weight: 2, fillColor: css('--accent'), fillOpacity: 1}).bindTooltip(etiqueta).addTo(capa);
    if (q) { const lon0 = q[0] / (K * Math.cos(lat * R)), lat0 = q[1] / K; L.polyline([[lat, lon], [lat0, lon0]], {color: css('--accent'), weight: 2, dashArray: '4 4'}).addTo(capa); }
    if (ir || !mapa._loaded) mapa.setView([lat, lon], Math.max(mapa.getZoom(), 14)); else mapa.panTo([lat, lon]);
    if (ir) mapa.getContainer().scrollIntoView({behavior: 'smooth', block: 'center'});
  }
  async function geocodificar(q) {
    const u = `${NOM}?format=jsonv2&countrycodes=cl&limit=5&accept-language=es&q=${encodeURIComponent(q)}`;
    const r = await j(u, {headers: {'Accept': 'application/json'}});
    return (r || []).map(x => ({lat: +x.lat, lon: +x.lon, nombre: x.display_name.split(',').slice(0, 3).join(',')}));
  }
  const est = $('.estado'), sug = $('.sug'), form = $('form'), inp = $('input[type=search]');
  form.addEventListener('submit', async e => { e.preventDefault(); const q = inp.value.trim(); if (!q) return;
    est.textContent = 'Buscando la dirección…'; sug.innerHTML = '';
    const r = await geocodificar(q);
    if (!r.length) { est.textContent = 'No se encontró esa dirección. Prueba con calle, número y comuna.'; return; }
    if (r.length === 1 || /\d/.test(q)) { est.textContent = ''; responder(r[0].lat, r[0].lon, r[0].nombre); return; }
    est.textContent = 'Elige una:'; sug.innerHTML = r.map((x, i) => `<li><button type="button" data-i="${i}">${x.nombre}</button></li>`).join('');
    sug.querySelectorAll('button').forEach(b => b.addEventListener('click', () => { const x = r[+b.dataset.i]; sug.innerHTML = ''; est.textContent = ''; inp.value = x.nombre; responder(x.lat, x.lon, x.nombre); })); });
  $('[data-ubic]').addEventListener('click', () => { if (!navigator.geolocation) { est.textContent = 'Este navegador no entrega la ubicación.'; return; }
    est.textContent = 'Pidiendo tu ubicación…';
    navigator.geolocation.getCurrentPosition(p => { est.textContent = ''; inp.value = ''; responder(p.coords.latitude, p.coords.longitude, 'Tu ubicación'); },
      () => { est.textContent = 'No se pudo obtener la ubicación. Escribe la dirección.'; }, {enableHighAccuracy: true, timeout: 12000}); });
  const m = location.hash.match(/#d=(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (m) setTimeout(() => responder(+m[1], +m[2], 'Este punto'), 800);
})();
</script>"""


def html(titulo="¿Vives cerca de una quebrada?"):
    """Tarjeta con la caja de dirección; el JS va aparte (js()) después del script del mapa de la página."""
    return f"""<section class="card dir" id="dir" aria-label="Respuesta por dirección">
  <h2>{titulo}</h2>
  <form role="search"><input type="search" placeholder="Calle y número, comuna" aria-label="Dirección o lugar en Chile" autocomplete="street-address"><button type="submit">Buscar</button></form>
  <div class="acciones"><button type="button" class="sec" data-ubic>Usar mi ubicación</button><span class="small muted">O escribe una dirección de Santiago oriente.</span></div>
  <p class="estado" aria-live="polite"></p>
  <ul class="sug"></ul>
  <div class="dir-res" hidden aria-live="polite"></div>
</section>"""


def js():
    return JS.replace("__RAW__", RAW).replace("__NOM__", NOMINATIM)
