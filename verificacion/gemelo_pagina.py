"""Pestaña Gemelo (site/gemelo.html): un lugar icónico con su cámara, lo que pasa ahora, lo que viene, los escenarios y
un simulador de "¿y si…?", más una vista 3D del terreno. Primer lugar: Sanhattan (Costanera Center), con la cámara de
Ledrium en YouTube.

La cámara va con el reproductor oficial de YouTube (embed, dominio sin cookies): YouTube bloquea a los servidores que
intentan sacar cuadros (probado en camaras-prueba.yml), así que no se archivan imágenes de esta cámara. La verificación
"lo que decía el modelo contra lo que se midió" usa el aeródromo de Tobalaba, a 7 km.

Los datos en vivo (rayos, lluvia medida) los lee el navegador de la rama datos-en-vivo; el pronóstico, de site/datos.
La vista 3D usa el relieve de AWS Terrain Tiles (Mapzen, abierto) y la imagen satelital de Esri, con atribución."""
import os
import pandas as pd
import pronostico_pagina
from comun import JS_DEF, a_chile, aviso, nav, num, pie

AQUI = os.path.dirname(os.path.abspath(__file__))
RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/datos-en-vivo/envivo"
RAW_ARCHIVO = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/camaras-archivo"

LUGAR = {
    "id": "sanhattan", "nombre": "Sanhattan, Santiago", "sub": "Costanera Center y Titanium · Providencia y Las Condes",
    "lat": -33.4175, "lon": -70.6066, "comuna": "Q51587", "comuna_nombre": "Providencia", "aerodromo": "SCTB",
    "camara": {"video": "UpHOS_enhjI", "canal": "Ledrium", "url": "https://www.youtube.com/@Ledrium", "nota": "cámara de Ledrium, empresa chilena de videovigilancia; transmisión pública en YouTube"},
    "cuenca": "mapocho", "quebradas": [1, 3],
    "hitos": [("Cerro San Cristóbal", -33.4262, -70.6325, 880), ("Cerro Manquehue", -33.3530, -70.5755, 1638), ("Farellones", -33.3540, -70.3080, 2470),
              ("Cerro Provincia", -33.3822, -70.4664, 2750), ("Valle Nevado", -33.3550, -70.2500, 3025), ("Cerro San Ramón", -33.4480, -70.4540, 3249),
              ("Cerro El Plomo", -33.2367, -70.2142, 5424)],
}

CSS = """
.gem-top{display:grid;gap:14px}
@media (min-width:1000px){.gem-top{grid-template-columns:minmax(0,3fr) minmax(300px,2fr);align-items:start}}
.gem-cam{position:relative;aspect-ratio:16/9;background:#000;border-radius:var(--radius);overflow:hidden;border:1px solid var(--line)}
.gem-cam iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.gem-cam .etq{position:absolute;left:10px;top:10px;background:rgba(0,0,0,.6);color:#fff;font-size:12.5px;padding:3px 8px;border-radius:6px}
.gem-cam .etq i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#e33;margin-right:6px;vertical-align:1px}
.gem-ahora{display:grid;gap:10px}
.gem-cifras{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}
.gem-cifra{border:1px solid var(--line-soft);border-radius:8px;padding:10px 12px;display:grid;gap:2px}
.gem-cifra .k{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600}
.gem-cifra .v{font-family:var(--font-display);font-size:24px;font-weight:600;line-height:1.15}
.gem-cifra .s{font-size:12.5px;color:var(--muted)}
.gem-horas{display:flex;gap:6px;overflow-x:auto;padding-bottom:6px;scrollbar-width:thin}
.gem-horas .h{flex:0 0 64px;display:grid;justify-items:center;gap:2px;border:1px solid var(--line-soft);border-radius:8px;padding:8px 4px;font-size:12.5px}
.gem-horas .h .d{color:var(--muted);font-size:11px;min-height:13px}
.gem-horas .h .t{font-family:var(--font-display);font-weight:600;font-size:16px}
.gem-horas .h .ll{color:var(--lluvia,var(--accent));font-size:11.5px;min-height:13px}
.gem-quince{display:flex;gap:6px;overflow-x:auto;padding-bottom:6px;scrollbar-width:thin}
.gem-quince .q{flex:0 0 58px;display:grid;justify-items:center;gap:2px;border:1px solid var(--line-soft);border-radius:8px;padding:8px 2px;font-size:12px}
.gem-quince .q .d{color:var(--muted);font-size:11px}
.gem-quince .q .mx{font-weight:600} .gem-quince .q .mn{color:var(--muted)}
.gem-quince .q .p{font-size:11px;color:var(--lluvia,var(--accent))}
.gem-casos{display:flex;flex-wrap:wrap;gap:6px;margin:0;padding:0;list-style:none}
.gem-casos li{font-size:13.5px;border:1px solid var(--line);border-radius:999px;padding:3px 10px;background:var(--bg)}
.gem-casos li b{font-family:var(--font-display)}
.gem-sim{display:grid;gap:14px}
@media (min-width:1000px){.gem-sim{grid-template-columns:1fr 1fr}}
.gem-sim label{display:grid;gap:4px;font-size:14.5px}
.gem-sim input[type=range]{width:100%;accent-color:var(--accent)}
.gem-sim .val{font-family:var(--font-display);font-weight:600;font-size:22px}
.perfil{width:100%;height:auto;display:block}
.perfil .cielo{fill:color-mix(in srgb,var(--accent) 8%,var(--surface))}
.perfil .monte{fill:var(--tierra);stroke:var(--costa);stroke-width:1}
.perfil .nieve{fill:#fff;opacity:.85}
.perfil .linea{stroke:var(--alto);stroke-width:2;stroke-dasharray:6 4}
.perfil .linea-txt{font:600 12px var(--font-body);fill:var(--alto)}
.perfil .hito{font:11.5px var(--font-body);fill:var(--fg)}
.perfil .hito-m{font:11px var(--font-data);fill:var(--muted)}
.perfil .hito-p{fill:var(--fg)}
.gem-dias{display:flex;flex-wrap:wrap;gap:4px}
.gem-dias button{font:600 12.5px var(--font-body);padding:5px 8px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer}
.gem-dias button.sel{background:var(--accent);border-color:var(--accent);color:#fff}
.gem-qb{display:grid;gap:6px}
.gem-qb .fila{display:flex;justify-content:space-between;gap:10px;align-items:center;font-size:14.5px}
#gem-3d{height:420px;border-radius:var(--radius);border:1px solid var(--line);overflow:hidden;background:var(--line-soft)}
.gem-3d-nota{font-size:13px;color:var(--muted);margin:6px 0 0}
.gem-verif td.num.bien{color:var(--bueno)} .gem-verif td.num.mal{color:var(--alto)}
.maplibregl-ctrl-attrib{font-size:10px}
.cams{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
.cam{display:grid;gap:6px;border:1px solid var(--line-soft);border-radius:var(--radius);overflow:hidden;background:var(--surface)}
.cam img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:var(--line-soft)}
.cam .cab{padding:8px 10px 0;font-weight:600;font-size:14.5px;line-height:1.25}
.cam .met{padding:0 10px 10px;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:13px;color:var(--muted)}
.cam .met b{color:var(--fg);font-family:var(--font-display);font-size:16px}
.cam .hora{font-size:12px;color:var(--muted);padding:0 10px}
.tira{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;scrollbar-width:thin}
.tira .cuadro{flex:0 0 220px;display:grid;gap:4px;font-size:12.5px}
.tira .cuadro img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:6px;background:var(--line-soft)}
.tira .cuadro .m{display:flex;gap:6px;align-items:center;color:var(--muted)}
.tira .cuadro .m b{color:var(--fg)}
"""

JS = r"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.js"></script>
<script>
(function(){
  const G = window.GEMELO, RAW = G.raw, $ = s => document.querySelector(s);
  const n = (v, d) => v == null || isNaN(v) ? '–' : Number(v).toLocaleString('es-CL', {maximumFractionDigits: d || 0, minimumFractionDigits: d || 0});
  const DIA3 = ['dom','lun','mar','mié','jue','vie','sáb'];
  const hora = s => new Date(s * 1000).toLocaleTimeString('es-CL', {timeZone: 'America/Santiago', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'});
  const km = (a, b) => 111.2 * Math.hypot(a[0] - b[0], (a[1] - b[1]) * Math.cos(a[0] * Math.PI / 180));
  async function j(u) { try { const r = await fetch(u + (u.includes('?') ? '&' : '?') + 't=' + Math.floor(Date.now() / 3e5)); return r.ok ? await r.json() : null; } catch (e) { return null; } }
  __ICONOS__

  // ---- ahora ----
  async function ahora() {
    const ahoraS = Date.now() / 1000;
    const [p48, ry, ll] = await Promise.all([j('datos/pronostico_48h.json'), j(RAW + '/rayos.json'), j(RAW + '/lluvia.json')]);
    const d = p48 && p48.comunas[G.comuna];
    const o = d && d.obs;
    $('#g-temp').innerHTML = o ? `${n(o.t)}<small>°</small>` : (d ? `${n(d.pasos[0].t)}<small>°</small>` : '–');
    $('#g-temp-s').textContent = o ? `Medido a las ${o.hora} en ${o.nombre}, a ${o.km} km` : 'Pronóstico (sin medición reciente)';
    $('#g-viento').innerHTML = o && o.w != null ? `${n(o.w)}<small> km/h</small>` : '–';
    $('#g-viento-s').textContent = o ? `En ${o.nombre}` : 'Sin medición reciente';
    const r10 = ry && ahoraS - ry.generado < 1800 ? ry.rayos.filter(r => ahoraS - r[2] <= 1800 && km([G.lat, G.lon], [r[0], r[1]]) <= 10).length : null;
    $('#g-rayos').innerHTML = r10 == null ? '–' : `${r10}<small> en 30 min</small>`;
    $('#g-rayos-s').textContent = r10 == null ? 'Sin datos de rayos recientes' : r10 ? 'Tormenta eléctrica a menos de 10 km' : 'Sin rayos a menos de 10 km';
    let lluvia = null, iso = null;
    if (ll && ahoraS - ll.generado < 3 * 3600) {
      ll.estaciones.filter(e => e.alt < 1500 && km([G.lat, G.lon], [e.lat, e.lon]) <= 20).forEach(e => { const x = (ll.obs[e.wmo] || []).filter(v => v[0] > ahoraS - 3 * 3600 - 600 && v[1] != null);
        if (x.length) { const mm = x.reduce((s, v) => s + v[1], 0); if (!lluvia || mm > lluvia.mm) lluvia = {mm, nombre: e.nombre.replace(/\s*\(([^)]*)\)/, ', $1')}; } });
      const c = (ll.obs['85594'] || []).filter(x => x[3] != null).pop(); if (c) iso = {t: c[0], temp: c[3], m: Math.round((2750 + c[3] / 0.0065) / 50) * 50};
    }
    $('#g-lluvia').innerHTML = lluvia ? `${n(lluvia.mm, 1)}<small> mm</small>` : '–';
    $('#g-lluvia-s').textContent = lluvia ? `En 3 h, ${lluvia.nombre}` : 'Sin lluvia medida cerca en 3 h';
    if (iso) { G.isoAhora = iso.m; $('#g-iso-ahora').textContent = `Ahora la isoterma 0 °C está a unos ${n(iso.m)} m (El Colorado, 2.750 m: ${n(iso.temp, 1)} °C a las ${hora(iso.t)}).`; }
    // 48 h
    if (d) {
      let ult = '';
      $('#g-horas').innerHTML = d.pasos.map(p => { const f = p.c.slice(0, 10), h = Number(p.c.slice(11, 13)), dd = new Date(f + 'T12:00'), nuevo = f !== ult; ult = f;
        return `<div class="h"><span class="d">${nuevo ? DIA3[dd.getDay()] + ' ' + dd.getDate() : ''}</span><span>${String(h).padStart(2, '0')}h</span>${icono(CIELO_P(p, h), 24)}<span class="t">${n(p.t)}°</span><span class="ll">${p.p >= 0.5 ? n(p.p, 1) + ' mm' : ''}</span></div>`; }).join('');
      const tr = d.tr72 || [];
      $('#g-tormenta').textContent = tr.length ? 'Tormentas ' + (tr.some(x => x.n >= 2) ? 'fuertes ' : '') + 'posibles: ' + tr.map(x => { const dd = new Date(x.f + 'T12:00'); return DIA3[dd.getDay()] + ' ' + dd.getDate() + (x.desde === x.hasta ? ' cerca de las ' + x.desde + ' h' : ' entre las ' + x.desde + ' y las ' + x.hasta + ' h'); }).join('; ') + '.' : '';
    }
  }

  // ---- 15 días y escenarios ----
  async function quince() {
    const [q, e] = await Promise.all([j('datos/pronostico_15d.json'), j('datos/escenarios_15d.json')]);
    const d = q && q.comunas[G.comuna];
    if (d) $('#g-quince').innerHTML = d.map(x => { const dd = new Date(x.f + 'T12:00');
      return `<div class="q"><span class="d">${DIA3[dd.getDay()]} ${dd.getDate()}</span>${icono(CIELO(x.nub, x.ll[0], 15), 22)}<span class="mx">${n(x.tmax[1])}°</span><span class="mn">${x.tmin[1] == null ? '' : n(x.tmin[1]) + '°'}</span><span class="p">${x.p1 >= 20 ? n(x.p1) + ' %' : ''}</span></div>`; }).join('');
    const c = e && e.comunas[G.comuna];
    if (c) { const casos = e.escenarios.map(s => { const a = c.p[s.id] || []; let m = 0, i = -1; a.forEach((v, k) => { if (v > m) { m = v; i = k; } }); return [s, m, i]; }).filter(x => x[1] >= 10).sort((a, b) => b[1] - a[1]).slice(0, 6);
      $('#g-casos').innerHTML = casos.length ? casos.map(x => { const dd = new Date(e.fechas[x[2]] + 'T12:00'); return `<li><b>${x[1]} %</b> ${x[0].nombre.toLowerCase()} · ${DIA3[dd.getDay()]} ${dd.getDate()}</li>`; }).join('') : '<li>Ningún caso del catálogo llega al 10 % en 15 días.</li>';
      $('#g-casos-nota').innerHTML = `Con los 50 escenarios del ensamble (corrida del ${e.corrida.slice(8, 10)}/${e.corrida.slice(5, 7)}). <a href="escenarios.html#c=${G.comuna}">Ver los 16 casos en ${G.comunaNombre} →</a>`; }
    else $('#g-casos').innerHTML = '<li>El catálogo de escenarios aparece con la próxima corrida del ensamble.</li>';
  }

  // ---- línea de nieve: perfil de la cordillera ----
  const HITOS = G.hitos, H_MAX = 5600;
  let nieveDias = null, modoNieve = 'dia', diaSel = 0, isoManual = 3000;
  function perfil(nieve, titulo) {
    const W = 760, H = 300, ml = 44, mb = 30, y = m => H - mb - (H - mb - 60) * (m / H_MAX), x0 = ml + 10;
    const orden = [...HITOS].sort((a, b) => a[3] - b[3]);
    const paso = (W - x0 - 20) / (orden.length - 1);
    const puntos = orden.map((h, i) => [x0 + i * paso, y(h[3])]);
    const poli = `M${x0 - 10} ${y(500)} L${puntos.map(p => p.join(' ')).join(' L')} L${W - 10} ${y(500)} L${W - 10} ${H - mb} L${x0 - 10} ${H - mb} Z`;
    const yN = y(Math.min(H_MAX, Math.max(0, nieve)));
    const clip = `<clipPath id="cp-nieve"><rect x="0" y="0" width="${W}" height="${yN}"/></clipPath>`;
    const hitos = orden.map((h, i) => { const [px, py] = puntos[i]; const alto = h[3] >= nieve, dy = i % 2 ? 30 : 0;   // etiquetas alternadas para que no se pisen
      return `<circle class="hito-p" cx="${px}" cy="${py}" r="3"/>${dy ? `<line x1="${px}" x2="${px}" y1="${py - 4}" y2="${py - 18 - dy}" stroke="var(--costa)" stroke-width="1"/>` : ''}<text class="hito" x="${px}" y="${py - 20 - dy}" text-anchor="middle">${h[0]}${alto ? ' ❄' : ''}</text><text class="hito-m" x="${px}" y="${py - 9 - dy}" text-anchor="middle">${n(h[3])} m</text>`; }).join('');
    return `<svg class="perfil" viewBox="0 0 ${W} ${H}" role="img" aria-label="${titulo}: línea de nieve a ${n(nieve)} m"><defs>${clip}</defs>
      <rect class="cielo" x="0" y="0" width="${W}" height="${H}"/><path class="monte" d="${poli}"/><path class="nieve" d="${poli}" clip-path="url(#cp-nieve)"/>
      <line class="linea" x1="${ml}" x2="${W - 6}" y1="${yN}" y2="${yN}"/><text class="linea-txt" x="${ml}" y="${yN - 6}">nieve desde ${n(nieve)} m</text>${hitos}
      ${[1000, 2000, 3000, 4000, 5000].map(m => `<text class="hito-m" x="${ml - 6}" y="${y(m) + 4}" text-anchor="end">${n(m)}</text>`).join('')}</svg>`;
  }
  function pintarNieve() {
    let nieve, titulo;
    if (modoNieve === 'manual') { nieve = isoManual - 300; titulo = `Si la isoterma estuviera a ${n(isoManual)} m`; }
    else if (nieveDias && nieveDias[diaSel]) { const d = nieveDias[diaSel]; nieve = d.nieve; titulo = d.titulo; }
    else { nieve = (G.isoAhora || 3000) - 300; titulo = 'Con la isoterma de ahora'; }
    $('#g-perfil').innerHTML = perfil(nieve, titulo);
    const con = HITOS.filter(h => h[3] >= nieve).map(h => h[0]), sin = HITOS.filter(h => h[3] < nieve).map(h => h[0]);
    $('#g-nieve-txt').innerHTML = `<strong>${titulo}:</strong> nieva desde unos ${n(nieve)} m (300 m bajo la isoterma). Con nieve: ${con.length ? con.join(', ') : 'ningún hito'}. Sin nieve: ${sin.length ? sin.join(', ') : 'ninguno'}.`;
    document.querySelectorAll('#g-dias button').forEach(b => b.classList.toggle('sel', modoNieve === 'dia' && +b.dataset.d === diaSel));
  }
  async function nieve() {
    const cu = await j('datos/cuencas_72h.json'); const c = cu && cu.cuencas[G.cuenca];
    if (c) { const porDia = {};
      c.pasos.forEach(p => { const f = p.c.slice(0, 10); (porDia[f] = porDia[f] || []).push(p); });
      nieveDias = Object.entries(porDia).slice(0, 4).map(([f, ps]) => { const dd = new Date(f + 'T12:00'), lluv = ps.filter(p => p.mm >= 0.5);
        const ref = lluv.length ? lluv : ps; const nv = Math.round(Math.min(...ref.map(p => p.nieve)) / 50) * 50;
        return {f, nieve: nv, titulo: `${DIA3[dd.getDay()]} ${dd.getDate()}${lluv.length ? ' (con precipitación)' : ''}`, mm: ps.reduce((s, p) => s + p.mm, 0)}; });
      $('#g-dias').innerHTML = nieveDias.map((d, i) => `<button type="button" data-d="${i}">${d.titulo.split(' (')[0]}${d.mm >= 1 ? ' · ' + n(d.mm) + ' mm' : ''}</button>`).join('');
      $('#g-dias').addEventListener('click', ev => { const b = ev.target.closest('button[data-d]'); if (!b) return; modoNieve = 'dia'; diaSel = +b.dataset.d; pintarNieve(); }); }
    pintarNieve();
  }
  const sl = $('#g-iso'); sl.addEventListener('input', () => { modoNieve = 'manual'; isoManual = +sl.value; $('#g-iso-val').textContent = n(isoManual) + ' m'; pintarNieve(); });

  // ---- ¿y si cayeran X mm en 2 h? (quebradas cercanas) ----
  async function quebradas() {
    const q = await j('quebradas/indicador.json'); if (!q) return;
    const qs = q.cuencas.filter(c => G.quebradas.includes(c.id) && c.mm_atencion != null);
    const sl2 = $('#g-mm'), out = $('#g-qb');
    const pintar = () => { const mm = +sl2.value; $('#g-mm-val').textContent = mm + ' mm';
      out.innerHTML = qs.map(c => { const nv = mm >= c.mm_aviso ? 'aviso' : mm >= c.mm_atencion ? 'atencion' : 'bajo', cls = {bajo: 'bueno', atencion: 'medio', aviso: 'alto'}[nv];
        return `<div class="fila"><span>${c.nombre.replace(/\s*\(.*\)/, '')} <span class="small muted">· atención desde ${n(c.mm_atencion, 1)} mm, aviso desde ${n(c.mm_aviso, 1)} mm</span></span><span class="chip ${cls}"><i></i>${{bajo: 'bajo', atencion: 'atención', aviso: 'aviso'}[nv]}</span></div>`; }).join('') +
        `<p class="small muted">Umbrales del <a href="quebradas.html">indicador de quebradas</a> con la humedad del suelo de hoy. Hoy, con lo previsto: ${qs.map(c => c.nombre.replace(/\s*\(.*\)/, '') + ' en ' + ({bajo: 'bajo', atencion: 'atención', aviso: 'aviso'}[c.nivel] || c.nivel)).join('; ')}.</p>`; };
    sl2.addEventListener('input', pintar); pintar();
  }

  // ---- vista 3D ----
  function tresD() {
    if (!window.maplibregl) return;
    const m = new maplibregl.Map({container: 'gem-3d', zoom: 10.6, center: [G.lon + 0.12, G.lat + 0.02], pitch: 68, bearing: 62, maxPitch: 85, attributionControl: true,
      style: {version: 8, sources: {
        sat: {type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, maxzoom: 17, attribution: 'Imagen: Esri, Maxar, Earthstar Geographics · Relieve: AWS Terrain Tiles (Mapzen, Copernicus, SRTM)'},
        dem: {type: 'raster-dem', tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'], tileSize: 256, encoding: 'terrarium', maxzoom: 14}},
        layers: [{id: 'sat', type: 'raster', source: 'sat'}], terrain: {source: 'dem', exaggeration: 1.3}}});
    m.addControl(new maplibregl.NavigationControl({visualizePitch: true}), 'top-right');
    m.on('load', () => { m.setTerrain({source: 'dem', exaggeration: 1.3});
      new maplibregl.Marker({color: '#0e7c86'}).setLngLat([G.lon, G.lat]).setPopup(new maplibregl.Popup().setText('Cámara: ' + G.nombre)).addTo(m);
      G.hitos.forEach(h => { const el = document.createElement('div'); el.style.cssText = 'font:600 11px sans-serif;background:rgba(255,255,255,.85);color:#17212b;padding:2px 6px;border-radius:4px;white-space:nowrap'; el.textContent = h[0] + ' · ' + n(h[3]) + ' m';
        new maplibregl.Marker({element: el, anchor: 'bottom'}).setLngLat([h[2], h[1]]).addTo(m); }); });
  }

  // ---- cámaras con imagen (archivo propio) ----
  async function camaras() {
    const [cj, p48, cu, idx] = await Promise.all([j(RAW + '/camaras/camaras.json'), j('datos/pronostico_48h.json'), j('datos/cuencas_72h.json'), j(G.rawArchivo + '/index.json')]);
    if (!cj) return;
    const ahoraS = Date.now() / 1000;
    const paso0 = id => { const d = p48 && p48.comunas[id]; if (!d) return null; return d.pasos.find(p => new Date(p.c).getTime() / 1000 >= ahoraS - 3 * 3600) || d.pasos[0]; };
    const nieveHoy = cuenca => { const c = cu && cu.cuencas[cuenca]; if (!c) return null; const ps = c.pasos.filter(p => { const t = new Date(p.c).getTime() / 1000; return t > ahoraS - 3 * 3600 && t <= ahoraS + 12 * 3600; }); return ps.length ? Math.round(Math.min(...ps.map(p => p.nieve)) / 50) * 50 : null; };
    $('#g-cams').innerHTML = cj.lista.map(c => { const e = cj.camaras[c.id] || {}, p = paso0(G.comunas[c.id]), nv = G.cuencas[c.id] ? nieveHoy(G.cuencas[c.id]) : null, h = Number((p || {c: '2026-01-01T12:00'}).c.slice(11, 13));
      return `<figure class="cam"><img src="${RAW}/camaras/${c.id}.jpg?t=${e.t || 0}" alt="${c.nombre}" loading="lazy"><figcaption class="cab">${c.nombre}</figcaption>
        <div class="met">${p ? `${icono(CIELO_P(p, h), 22)}<b>${n(p.t)}°</b><span>${p.p >= 0.5 ? n(p.p, 1) + ' mm' : 'sin lluvia'}</span>` : '<span>Sin pronóstico</span>'}${nv != null ? `<span>nieve desde ${n(nv)} m</span>` : ''}</div>
        <div class="hora">${e.t ? 'Cuadro de las ' + hora(e.t) : 'Sin cuadro todavía'} · ${c.fuente}</div></figure>`; }).join('');
    // tira: Valle Nevado, un cuadro cada 3 h de las últimas 24 h, con lo que decía el modelo para esa hora (nubosidad y lluvia del cuadrado de Lo Barnechea)
    const horas = idx && idx.horas && idx.horas.vallenevado_piscina || [];
    const sel = horas.slice(-24).filter((h, i, a) => (a.length - 1 - i) % 3 === 0);
    $('#g-tira').innerHTML = sel.length ? sel.map(hh => { const iso = `${hh.slice(0, 4)}-${hh.slice(4, 6)}-${hh.slice(6, 8)}T${hh.slice(9, 11)}:00:00Z`, t = new Date(iso), m = (G.modeloHoras || {})[hh];
      const local = t.toLocaleString('es-CL', {timeZone: 'America/Santiago', weekday: 'short', hour: '2-digit', hourCycle: 'h23'});
      return `<div class="cuadro"><img src="${G.rawArchivo}/vallenevado_piscina/${hh}.jpg" alt="Valle Nevado, ${local}" loading="lazy"><span>${local} h · cámara</span>
        <span class="m">${m ? `${icono(CIELO(m.nb, m.p, (t.getUTCHours() + 21) % 24), 20)}<b>${n(m.t)}°</b> modelo: ${m.nb != null ? n(m.nb) + ' % nubes' : ''}${m.p >= 0.5 ? ', ' + n(m.p, 1) + ' mm' : ''}` : 'modelo: sin dato para esa hora'}</span></div>`; }).join('') : '<p class="small muted">El archivo empieza a llenarse hoy: cada hora se guarda un cuadro y aquí aparecerán las últimas 24 horas con lo que decía el modelo.</p>';
  }
  ahora(); quince(); nieve(); quebradas(); camaras();
  try { tresD(); } catch (e) { document.getElementById('gem-3d').innerHTML = '<p class="small muted" style="padding:14px">Este navegador no puede mostrar el terreno en 3D (necesita WebGL).</p>'; }
  setInterval(ahora, 5 * 60000);
})();
</script>"""


def modelo_vs_medido(ahora):
    """Últimas 24 h en Tobalaba: temperatura pronosticada por los modelos (corrida más reciente que cubría cada hora,
    de data/pronostico_comunas.csv para Providencia) contra la medida en el METAR."""
    try:
        pr = pd.read_csv(os.path.join(AQUI, "data", "pronostico_comunas.csv"))
        ob = pd.read_csv(os.path.join(AQUI, "data", "metar_obs.csv"), parse_dates=["time"])
    except Exception:
        return ""
    for c in ("run", "valid"):
        pr[c] = pd.to_datetime(pr[c], format="mixed")
    pr = pr[(pr.id == LUGAR["comuna"]) & ~pr.modelo.str.endswith(("SIMULADO", "PRUEBA")) & (pr.modelo != "PERSISTENCIA")]
    ahora_n = ahora.tz_localize(None) if ahora.tzinfo else ahora
    pr = pr[(pr.valid >= ahora_n - pd.Timedelta(hours=24)) & (pr.valid <= ahora_n)]
    ob = ob[ob.icao == LUGAR["aerodromo"]].copy(); ob["time"] = ob.time.dt.tz_localize(None)
    if pr.empty or ob.empty:
        return ""
    filas = []
    for t, g in pr.groupby("valid"):
        ult = g[g.run == g.run.max()] if False else g.sort_values("run").groupby("modelo").tail(1)
        o = ob[(ob.time - t).abs() <= pd.Timedelta(minutes=35)].sort_values("time").tail(1)
        tm = ult.t_fc.mean(); to = float(o.temp_c.iloc[0]) if len(o) else None
        wx = str(o.raw.iloc[0]).split() if len(o) else []
        tiempo = [w for w in wx if any(k in w for k in ("RA", "DZ", "TS", "GR", "FG", "BR", "SH"))]
        dif = None if to is None else tm - to
        filas.append(f"<tr><td class='l'>{a_chile(t).strftime('%a %d, %H:%M')}</td><td class='num'>{num(tm, 1)} °C</td><td class='num'>{'–' if to is None else num(to, 1) + ' °C'}</td>"
                     f"<td class='num {'' if dif is None else ('bien' if abs(dif) < 2 else 'mal')}'>{'–' if dif is None else ('+' if dif > 0 else '') + num(dif, 1)}</td><td class='l'>{' '.join(tiempo) or ('despejado o nubes' if len(o) else '–')}</td></tr>")
    return ("<div class='tabla gem-verif'><table><thead><tr><th class='l'>Hora</th><th>Modelos</th><th>Medido</th><th>Diferencia</th><th class='l'>Tiempo observado</th></tr></thead><tbody>"
            + "".join(filas) + "</tbody></table></div>")


def modelo_por_hora(comuna, ahora, horas=30):
    """{AAAAMMDD_HH: {t, p, nb}} para las últimas `horas` horas en una comuna, con la corrida más reciente que cubría cada
    paso (los modelos van cada 6 h; se interpola a cada hora)."""
    try:
        pr = pd.read_csv(os.path.join(AQUI, "data", "pronostico_comunas.csv"))
    except Exception:
        return {}
    for c in ("run", "valid"):
        pr[c] = pd.to_datetime(pr[c], format="mixed")
    pr = pr[(pr.id == comuna) & ~pr.modelo.str.endswith(("SIMULADO", "PRUEBA")) & (pr.modelo != "PERSISTENCIA")]
    ahora_n = ahora.tz_localize(None) if ahora.tzinfo else ahora
    pr = pr[(pr.valid >= ahora_n - pd.Timedelta(hours=horas + 6)) & (pr.valid <= ahora_n + pd.Timedelta(hours=6))]
    if pr.empty:
        return {}
    pr = pr.sort_values("run").groupby(["modelo", "valid"]).tail(1)
    pr["p6"] = pr.sort_values("valid").groupby("modelo").tp_fc.diff().clip(lower=0)
    g = pr.groupby("valid").agg(t=("t_fc", "mean"), p=("p6", "mean"), nb=("nub_fc", "mean")).sort_index()
    if len(g) < 2:
        return {}
    idx = pd.date_range(g.index.min().floor("h"), g.index.max(), freq="h")
    h = g.reindex(g.index.union(idx)).interpolate(method="time").reindex(idx)
    return {t.strftime("%Y%m%d_%H"): {"t": round(float(r.t), 1), "p": None if pd.isna(r.p) else round(float(r.p), 1), "nb": None if pd.isna(r.nb) else int(round(float(r.nb)))}
            for t, r in h.iterrows() if t >= ahora_n - pd.Timedelta(hours=horas)}


def pagina(head, escribir, ahora):
    import json, csv
    L = LUGAR
    cams = list(csv.DictReader(open(os.path.join(AQUI, "..", "envivo", "camaras.csv"), encoding="utf-8")))
    datos = json.dumps({"raw": RAW, "lat": L["lat"], "lon": L["lon"], "comuna": L["comuna"], "comunaNombre": L["comuna_nombre"], "cuenca": L["cuenca"],
                        "quebradas": L["quebradas"], "hitos": L["hitos"], "nombre": L["nombre"], "rawArchivo": RAW_ARCHIVO,
                        "comunas": {c["id"]: c["comuna"] for c in cams}, "cuencas": {c["id"]: c["cuenca"] for c in cams if c["cuenca"]},
                        "modeloHoras": modelo_por_hora("Q14502", ahora)}, ensure_ascii=False)
    verif = modelo_vs_medido(ahora)
    html = f"""{head("Gemelo · Earth-2 Chile", "Un lugar icónico de Chile con su cámara, lo que pasa ahora, lo que viene, los 50 escenarios a 15 días y un simulador de qué pasaría con otra lluvia u otra isoterma, sobre el terreno en 3D.")}
<body>
{nav("gemelo")}
<div class="wrap">
<header>
  <div class="eyebrow">Gemelo · {L["nombre"]}</div>
  <h1>{L["nombre"]}: lo que se ve, lo que viene y lo que pasaría</h1>
  <p class="lead">{L["sub"]}. La cámara muestra el lugar en este momento; alrededor, lo que miden las estaciones, lo que pronostican los modelos y un simulador para probar escenarios sobre el terreno real.</p>
</header>

<div class="gem-top">
  <div>
    <div class="gem-cam"><span class="etq"><i></i>En vivo · {L["camara"]["canal"]}</span>
      <iframe src="https://www.youtube-nocookie.com/embed/{L["camara"]["video"]}?autoplay=1&mute=1&rel=0" title="Cámara en vivo: {L["nombre"]}" loading="lazy" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
    <p class="small muted">Transmisión pública de <a href="{L["camara"]["url"]}" rel="noopener">{L["camara"]["canal"]}</a> en YouTube ({L["camara"]["nota"]}). Si el reproductor no carga, el stream cambió de dirección: se actualiza en la siguiente publicación del sitio.</p>
  </div>
  <section class="card gem-ahora" aria-live="polite">
    <h2>Ahora</h2>
    <div class="gem-cifras">
      <div class="gem-cifra"><span class="k">Temperatura</span><span class="v" id="g-temp">–</span><span class="s" id="g-temp-s"></span></div>
      <div class="gem-cifra"><span class="k">Viento</span><span class="v" id="g-viento">–</span><span class="s" id="g-viento-s"></span></div>
      <div class="gem-cifra"><span class="k">Rayos a menos de 10 km</span><span class="v" id="g-rayos">–</span><span class="s" id="g-rayos-s"></span></div>
      <div class="gem-cifra"><span class="k">Lluvia medida</span><span class="v" id="g-lluvia">–</span><span class="s" id="g-lluvia-s"></span></div>
    </div>
    <p class="small muted" id="g-iso-ahora"></p>
    <p class="small muted">Tobalaba está a 7 km de la cámara; los rayos son del satélite GOES-19 (cada 5 minutos) y la lluvia, de las estaciones de la DMC a menos de 20 km. <a href="envivo.html">Ver todo en vivo →</a></p>
  </section>
</div>

<section class="card">
  <div class="sec-head"><h2>Lo que viene en {L["comuna_nombre"]}</h2><p class="muted">Próximas 48 horas cada 6 horas (los tres modelos corregidos con Tobalaba) y 15 días con el ensamble de 50 escenarios.</p></div>
  <div class="gem-horas" id="g-horas"></div>
  <p class="small" id="g-tormenta"></p>
  <div class="gem-quince" id="g-quince"></div>
  <h3>Casos más probables en 15 días</h3>
  <ul class="gem-casos" id="g-casos"></ul>
  <p class="small muted" id="g-casos-nota"></p>
  <p class="small muted"><a href="pronostico.html#{L["comuna"]}">Pronóstico completo de {L["comuna_nombre"]} →</a></p>
</section>

<section class="card gem-sim">
  <div>
    <div class="sec-head"><h2>¿Y si…? Línea de nieve en la cordillera</h2><p class="muted">Los cerros que se ven desde Santiago, con la nieve según la isoterma 0 °C: la prevista por GFS para cada día (cuenca del Mapocho) o la que tú elijas.</p></div>
    <div class="gem-dias" id="g-dias"></div>
    <label>¿Y si la isoterma estuviera a <span class="val" id="g-iso-val">3.000 m</span>?<input type="range" id="g-iso" min="1000" max="5500" step="50" value="3000"></label>
  </div>
  <div>
    <div id="g-perfil"></div>
    <p class="small" id="g-nieve-txt"></p>
  </div>
  <div>
    <div class="sec-head"><h2>¿Y si cayeran… en 2 horas?</h2><p class="muted">Las quebradas quemadas más cercanas a la cámara (Apoquindo a 8 km, Ramón a 10 km) y su nivel con esa lluvia.</p></div>
    <label><span class="val" id="g-mm-val">20 mm</span><input type="range" id="g-mm" min="0" max="50" step="1" value="20"></label>
  </div>
  <div class="gem-qb" id="g-qb"></div>
</section>

<section class="card">
  <div class="sec-head"><h2>El terreno en 3D</h2><p class="muted">Desde la cámara hacia la cordillera: relieve real con los hitos y sus alturas. Arrastra para girar; con la rueda, acercar.</p></div>
  <div id="gem-3d" role="application" aria-label="Vista 3D del terreno entre Santiago y la cordillera"></div>
  <p class="gem-3d-nota">Relieve de AWS Terrain Tiles (Mapzen: Copernicus y SRTM, abierto) e imagen satelital de Esri. Es terreno real, no una simulación de la nieve: la línea de nieve de cada día está en el perfil de arriba. La versión con la nieve y la lluvia pintadas sobre el relieve viene después.</p>
</section>

<section class="card">
  <div class="sec-head"><h2>Cámaras con imagen: lo que se ve en la cordillera y el norte</h2><p class="muted">Cámaras públicas cuya imagen se puede leer por programa: el cuadro actual con lo que el modelo dice para ese lugar ahora (cielo, temperatura, lluvia; en la cordillera, desde qué altura nieva). Se guardan cada hora.</p></div>
  <div class="cams" id="g-cams"><p class="small muted">Cargando las cámaras…</p></div>
  <h3>Valle Nevado: lo que vio la cámara y lo que decía el modelo</h3>
  <div class="tira" id="g-tira"></div>
  <p class="small muted">Un cuadro cada 3 horas de las últimas 24 (cámara Piscina, OpenSnow). El modelo es el cuadrado de 25 km de Lo Barnechea (promedio de AIFS, IFS y GFS, corrida más reciente que cubría esa hora), sin corregir por los 3.000 m de altura: lo que se compara es el cielo y la lluvia, no la temperatura exacta. Fuentes de cada cámara en <code>envivo/camaras.csv</code>; cada imagen cita la suya.</p>
</section>

{'<section class="card"><div class="sec-head"><h2>Lo que decían los modelos y lo que se midió</h2><p class="muted">Últimas 24 horas en Tobalaba: temperatura pronosticada (promedio de AIFS, IFS y GFS, corrida más reciente que cubría cada hora) contra la medida. Es la verificación de este lugar, hora a hora.</p></div>' + verif + '</section>' if verif else ''}

<details><summary>Cómo se arma este gemelo</summary><div class="body">
  <p>La cámara es la transmisión pública de {L["camara"]["canal"]} en YouTube, con el reproductor oficial. YouTube no deja sacar cuadros desde servidores, así que de esta cámara no se guardan imágenes; la verificación usa el aeródromo de Tobalaba. Las cámaras con imagen fija (Valle Nevado, Portillo, Paranal) sí permiten guardar "lo que la cámara vio" junto a "lo que el modelo decía": es el siguiente gemelo.</p>
  <p>Ahora: METAR de Tobalaba, rayos del GOES-19 a menos de 10 km y lluvia de las estaciones de la DMC a menos de 20 km. Viene: el pronóstico de {L["comuna_nombre"]} de la pestaña Pronóstico (48 h) y el ensamble de 15 días; los casos, del catálogo de Escenarios. Línea de nieve: 300 m bajo la isoterma 0 °C de GFS sobre la cuenca del Mapocho, o la que fijes con el control; los hitos son cerros y centros de ski con su altura. Quebradas: los umbrales del indicador de quebradas con la humedad del suelo de hoy. La vista 3D es relieve real; no simula la nieve ni el agua todavía.</p>
  <p>Para un cliente, el mismo armado sirve con sus cámaras (basta una imagen cada algunos minutos), sus puntos sensibles y su comuna. Nada de esto es una alerta: las alertas son de la DMC y SENAPRED.</p>
</div></details>
{aviso()}
{pie(ahora)}
</div>
<script>window.GEMELO = {datos};</script>
{JS.replace("__ICONOS__", pronostico_pagina.ICONOS_JS)}
{JS_DEF}
</body>
</html>
"""
    head_extra = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.css">'
    html = html.replace("</style>", CSS + "</style>" + head_extra, 1)
    return escribir("gemelo.html", html)
