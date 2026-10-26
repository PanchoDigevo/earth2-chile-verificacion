"""Monitor de la lluvia en curso: lo que está pasando (lluvia medida, isoterma de ahora), lo que viene (modelos) y los
posibles efectos (quebradas, ríos, agua potable, caminos, deshielo). Va completo en En vivo y como aviso corto arriba de
la portada y Pronóstico cuando llueve o viene lluvia en la cordillera.

Lo arma el navegador con tres archivos: la lluvia de las estaciones (datos-en-vivo/envivo/lluvia.json, cada 15 min),
la isoterma y la lluvia por cuenca (site/datos/cuencas_72h.json, cordillera/pronostico.py, 4 veces al día) y el indicador
de quebradas (site/quebradas/indicador.json).

Reglas de los efectos (simples, explicadas en Método, todavía sin verificar contra caudales de la DGA):
- isoterma de ahora: El Colorado (2.750 m) más su temperatura dividida por 6,5 °C/km (gradiente estándar);
- parte de la cuenca con lluvia: bajo la línea de nieve (300 m bajo la isoterma), con la curva de alturas;
- "lluvia en la cordillera": 5 mm o más en 24 h sobre la cuenca y la mitad o más de ella bajo la línea de nieve;
- nieve en caminos: lluvia con línea de nieve bajo 2.500 m; deshielo acelerado: isoterma sobre 3.500 m;
- tormenta encima de una quebrada: rayos del GOES-19 a menos de 8 km de su centro en los últimos 30 minutos. Es una señal,
  no un umbral: donde hay una celda de tormenta, la lluvia en la quebrada puede ser mucho mayor que la que miden las
  estaciones del valle (26-oct-2026: quebradas activadas en Las Condes y Lo Barnechea con menos de 1 mm en el valle).
Es apoyo a la decisión, no una alerta: las alertas son de SENAPRED y la DMC."""

RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/datos-en-vivo/envivo/lluvia.json"
RAW_RAYOS = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/datos-en-vivo/envivo/rayos.json"

CSS = """
.monitor{display:grid;gap:18px}
.mon-estado{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;font-size:14.5px;color:var(--muted)}
.mon-cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}
.mon-cifra{border:1px solid var(--line-soft);border-radius:var(--radius);padding:12px 14px;display:grid;gap:2px;align-content:start}
.mon-cifra .k{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600}
.mon-cifra .v{font-family:var(--font-display);font-size:28px;font-weight:600;line-height:1.15}
.mon-cifra .s{font-size:13px;color:var(--muted)}
.mon-bloque{display:grid;gap:10px}
.mon-bloque h3{margin:0;font-size:16px}
.mon-qb{border:1px solid var(--line-soft);border-radius:var(--radius);padding:12px 14px;display:grid;gap:8px}
.mon-qb .cab{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px 12px}
.mon-qb .cab strong{font-size:15.5px}
.mon-qb .chips{display:flex;flex-wrap:wrap;gap:6px}
.mon-escala{position:relative;height:10px;border-radius:5px;background:var(--line-soft);margin:4px 0 18px}
.mon-escala .ll{position:absolute;inset:0 auto 0 0;border-radius:5px;background:var(--accent)}
.mon-escala .um{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--medio)}
.mon-escala .um.av{background:var(--alto)}
.mon-escala .um span{position:absolute;top:16px;transform:translateX(-50%);font-size:11.5px;color:var(--muted);white-space:nowrap}
.mon-qb p{margin:0;font-size:14px}
.mon-rios td .mini{display:inline-block;width:54px;height:6px;border-radius:3px;background:var(--line-soft);vertical-align:middle;margin-right:6px;position:relative;overflow:hidden}
.mon-rios td .mini i{position:absolute;inset:0 auto 0 0;background:var(--accent)}
.mon-rios tr.crece td{background:color-mix(in srgb,var(--alto) 8%,transparent)}
.mon-rios .mods{display:block;font-size:12px;color:var(--muted)}
.mon-efectos{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.mon-efectos li{display:grid;grid-template-columns:12px 1fr;gap:10px;align-items:start;font-size:14.5px}
.mon-efectos li::before{content:"";width:10px;height:10px;border-radius:50%;margin-top:6px;background:var(--medio)}
.mon-efectos li.f::before{background:var(--alto)}
.mon-pie{font-size:13px;color:var(--muted);margin:0}
.mon-rayos{border-left:4px solid var(--alto);background:color-mix(in srgb,var(--alto) 8%,var(--surface));border-radius:6px;padding:10px 12px;display:grid;gap:4px;font-size:14.5px}
.mon-rayos span{color:var(--muted);font-size:13.5px}
.lluvia-curso{border:1px solid var(--accent);border-left:6px solid var(--accent);background:color-mix(in srgb,var(--accent) 8%,var(--surface));
  border-radius:var(--radius);padding:12px 16px;display:grid;gap:4px}
.lluvia-curso[hidden]{display:none}
.lluvia-curso strong.t{font-family:var(--font-display);font-size:17px}
.lluvia-curso p{margin:0;max-width:80ch}
"""

JS_COMUN = r"""
const MON = (function(){
  const n = (v, d) => v == null || isNaN(v) ? '–' : Number(v).toLocaleString('es-CL', {maximumFractionDigits: d || 0, minimumFractionDigits: d || 0});
  async function j(u) { try { const r = await fetch(u + (u.includes('?') ? '&' : '?') + 't=' + Date.now()); return r.ok ? await r.json() : null; } catch (e) { return null; } }
  async function datos() {
    const [ll, cu, qb, ry, gq] = await Promise.all([j('__RAW__'), j('datos/cuencas_72h.json'), j('quebradas/indicador.json'), j('__RAYOS__'), j('quebradas/cuencas.geojson')]);
    const ahora = Date.now() / 1000;
    return {ll, cu, qb, ahora, encima: encima(ry, gq, ahora)};
  }
  // rayos de los últimos 30 min a menos de 8 km del centro de cada quebrada: {id: {nombre, n}} (solo las que tienen alguno)
  function encima(ry, gq, ahora) {
    const out = {};
    if (!ry || !gq || ahora - ry.generado > 30 * 60) return out;
    const rec = ry.rayos.filter(r => ahora - r[2] <= 30 * 60), cos = Math.cos(-33.4 * Math.PI / 180);
    gq.features.forEach(f => {
      const anillo = f.geometry.type === 'Polygon' ? f.geometry.coordinates[0] : f.geometry.coordinates[0][0];
      const lo = anillo.reduce((s, p) => s + p[0], 0) / anillo.length, la = anillo.reduce((s, p) => s + p[1], 0) / anillo.length;
      const k = rec.filter(r => 111.2 * Math.hypot(r[0] - la, (r[1] - lo) * cos) <= 8).length;
      if (k) out[f.properties.id] = {nombre: f.properties.nombre, corto: f.properties.nombre.replace(/^Quebrada (de |del )?/, '').replace(/\s*\(ramal.*\)/, ''), n: k};
    });
    return out;
  }
  // lluvia medida en las últimas h horas en una estación (suma de las horarias; null si faltan)
  function medida(ll, wmo, h, ahora) {
    const o = (ll.obs[wmo] || []).filter(x => x[0] > ahora - h * 3600 - 600);
    const hs = o.filter(x => x[1] != null); if (!hs.length) return null;
    return hs.reduce((s, x) => s + x[1], 0);
  }
  function isoAhora(ll) {
    const c = (ll && ll.obs['85594'] || []).filter(o => o[3] != null).pop();
    return c ? {t: c[0], temp: c[3], iso: Math.round((2750 + c[3] / 0.0065) / 50) * 50} : null;
  }
  // resumen por cuenca de las próximas 24 h (GFS cada 3 h) y el rango de lluvia de los tres modelos
  function cuenca(c, ahora) {
    const fut = c.pasos.filter(p => { const t = new Date(p.c).getTime() / 1000; return t > ahora && t <= ahora + 24 * 3600; });
    const mm = fut.reduce((s, p) => s + p.mm, 0), hm3 = fut.reduce((s, p) => s + p.hm3, 0);
    const fr = mm > 0 ? fut.reduce((s, p) => s + p.fr * p.mm, 0) / mm : (fut.length ? Math.max(...fut.map(p => p.fr)) : null);
    const lluviosos = fut.filter(p => p.mm >= 0.5);
    const nieve = lluviosos.length ? Math.max(...lluviosos.map(p => p.nieve)) : null;
    const iso72 = c.pasos.length ? Math.max(...c.pasos.filter(p => new Date(p.c).getTime() / 1000 > ahora).map(p => p.iso)) : null;
    const rango = Object.entries(c.lluvia6 || {}).map(([m, v]) => [m, v.filter(p => { const t = new Date(p.c).getTime() / 1000; return t > ahora && t <= ahora + 24 * 3600 + 3 * 3600; }).reduce((s, p) => s + p.mm, 0)]);
    return {mm, hm3, fr, nieve, iso72, rango};
  }
  // posibles efectos, agrupados: cada uno con la lista de ríos donde aplica
  function efectos(filas) {
    const lista = xs => xs.length === 1 ? xs[0] : xs.slice(0, -1).join(', ') + ' y ' + xs[xs.length - 1];
    const de = f => filas.filter(f).map(x => x.c.rio), out = [];
    const lluvia = filas.filter(x => x.r.mm >= 5 && x.r.fr >= 0.5);
    if (lluvia.length) out.push({f: true, t: `Lluvia en la cordillera del ${lista(lluvia.map(x => x.c.rio))}: llueve en ${lista(lluvia.map(x => n(x.r.fr * 100) + ' %'))} de la cuenca (línea de nieve sobre ${n(Math.min(...lluvia.map(x => x.r.nieve)))} m). El agua escurre de inmediato en vez de quedar como nieve: crecida probable y agua más turbia.`});
    if (lluvia.some(x => x.id === 'maipo' || x.id === 'mapocho')) out.push({f: true, t: 'El Maipo da la mayor parte del agua potable de Santiago: con lluvia en su cordillera sube la turbiedad y Aguas Andinas puede reducir la producción, como en abril de 2016 y febrero de 2017. En el Cajón del Maipo son comunes los derrumbes en la ruta G-25.'});
    const nieva = de(x => x.r.mm >= 5 && x.r.fr < 0.5);
    if (nieva.length) out.push({t: `En ${lista(nieva)} la mayor parte de lo que cae en la cordillera es nieve: poca crecida inmediata, pero la nieve queda para después.`});
    const caminos = de(x => x.r.mm >= 5 && x.r.nieve != null && x.r.nieve < 2500);
    if (caminos.length) out.push({t: `Nieve bajo 2.500 m en la cordillera de ${lista(caminos)}: caminos de montaña (Farellones, Paso Los Libertadores, Cajón del Maipo) con nieve o hielo.`});
    const calor = filas.filter(x => x.r.iso72 >= 3500), tras = calor.filter(x => x.r.mm >= 5 && x.r.fr < 0.5);
    if (tras.length) out.push({f: true, t: `Nieve nueva y después calor en ${lista(tras.map(x => x.c.rio))}: la isoterma sube a ${n(Math.max(...tras.map(x => x.r.iso72)))} m en los próximos 3 días. Deshielo rápido de la nieve recién caída: los ríos crecen en las tardes y la nieve húmeda queda inestable en laderas (avalanchas).`});
    const calorSolo = calor.filter(x => !tras.includes(x)).map(x => x.c.rio);
    if (calorSolo.length) out.push({t: `Isoterma sobre 3.500 m en los próximos 3 días en ${lista(calorSolo)}: deshielo acelerado, los ríos crecen en las tardes.`});
    return out;
  }
  // las quebradas con más rayos, sin repetir nombre: "El Quisco (48), Los Carboneros (47) y Los Chanchos (45)"
  function masRayos(lista, k) {
    const vistos = new Set(), top = [];
    for (const x of lista) { if (!vistos.has(x.corto)) { vistos.add(x.corto); top.push(`${x.corto} (${x.n})`); } if (top.length === k) break; }
    return top.length === 1 ? top[0] : top.slice(0, -1).join(', ') + ' y ' + top[top.length - 1];
  }
  return {n, datos, medida, isoAhora, cuenca, efectos, masRayos};
})();
"""

JS_MONITOR = r"""<script>
__COMUN__
(async function(){
  const caja = document.getElementById('monitor'); if (!caja) return;
  const nivelTxt = {bajo: 'bajo', atencion: 'atención', aviso: 'aviso'}, nivelCls = {bajo: 'bueno', atencion: 'medio', aviso: 'alto'};
  const sinParen = s => s.replace(/\s*\(([^)]*)\)/, ', $1');
  async function pintar() {
    const {ll, cu, qb, ahora, encima} = await MON.datos(), n = MON.n;
    const hora = s => new Date(s * 1000).toLocaleTimeString('es-CL', {timeZone: 'America/Santiago', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'});
    const est = ll ? ll.estaciones.filter(e => e.km <= 45 && e.alt < 1500).map(e => ({e, h3: MON.medida(ll, e.wmo, 3, ahora), h2: MON.medida(ll, e.wmo, 2, ahora)})).filter(x => x.h3 != null) : [];
    const max3 = [...est].sort((a, b) => b.h3 - a.h3)[0], iso = MON.isoAhora(ll);
    const llueve = max3 && max3.h3 >= 0.5;
    let h = `<p class="mon-estado"><span class="chip ${llueve ? 'medio' : 'bueno'}"><i></i>${llueve ? 'Está lloviendo' : 'Sin lluvia importante en las últimas 3 h'}</span>${ll ? `<span>Estaciones leídas a las ${hora(ll.generado)}</span>` : ''}</p>`;
    // tres cifras
    const pr = qb ? Object.entries(qb.lluvia_prevista || {}).map(([m, v]) => [m, v.mm6]).filter(x => x[1] != null) : [];
    const lo = pr.length ? Math.min(...pr.map(x => x[1])) : null, hi = pr.length ? Math.max(...pr.map(x => x[1])) : null;
    h += `<div class="mon-cifras">
      <div class="mon-cifra"><span class="k">Lluvia medida, 3 h</span><span class="v">${max3 ? n(max3.h3, 1) + ' mm' : '–'}</span><span class="s">${max3 ? 'La mayor cerca de Santiago: ' + sinParen(max3.e.nombre) : 'Sin estaciones con datos'}</span></div>
      <div class="mon-cifra"><span class="k">Isoterma 0 °C ahora</span><span class="v">${iso ? n(iso.iso) + ' m' : '–'}</span><span class="s">${iso ? `Estimada con El Colorado (2.750 m): ${n(iso.temp, 1)} °C a las ${hora(iso.t)}` : 'Sin dato de El Colorado'}</span></div>
      <div class="mon-cifra"><span class="k">Próximas 6 h, Santiago oriente</span><span class="v">${lo == null ? '–' : lo === hi ? n(lo, 1) + ' mm' : n(lo, 0) + '–' + n(hi, 0) + ' mm'}</span><span class="s">${pr.map(([m, v]) => m + ' ' + n(v, 1)).join(' · ') || 'Sin pronóstico'}</span></div></div>`;
    // quebradas
    const qs = qb ? qb.cuencas.filter(c => c.nivel !== 'sin_quema') : [];
    const conRayos = Object.values(encima).sort((a, b) => b.n - a.n);
    if (qs.length || conRayos.length) {
      const cerca = est.filter(x => x.e.km <= 25 && x.h2 != null).sort((a, b) => b.h2 - a.h2)[0], m2 = cerca ? cerca.h2 : 0;
      h += `<div class="mon-bloque"><h3>Quebradas de Santiago oriente</h3>` + (conRayos.length ? `<div class="mon-rayos"><strong>Tormenta eléctrica encima de ${conRayos.length === 1 ? 'una quebrada' : conRayos.length + ' quebradas'} en los últimos 30 minutos</strong> Más rayos a menos de 8 km: ${MON.masRayos(conRayos, 3)}.
          <span>Donde hay una celda de tormenta, la lluvia en la quebrada puede ser mucho mayor que la que miden las estaciones del valle: el 26 de octubre se activaron quebradas en Las Condes y Lo Barnechea con menos de 1 mm medido en el valle.</span></div>` : '') + qs.map(c => {
        const ray = encima[c.id];
        const med = m2 >= c.mm_aviso ? 'aviso' : m2 >= c.mm_atencion ? 'atencion' : 'bajo', tope = Math.max(c.mm_aviso * 1.3, m2 * 1.1), w = x => Math.min(100, x / tope * 100);
        return `<div class="mon-qb"><div class="cab"><strong>${c.nombre.replace(/\s*\(.*\)/, '')}</strong><span class="chips">
            ${ray ? `<span class="chip alto"><i></i>Tormenta encima: ${ray.n} ${ray.n === 1 ? 'rayo' : 'rayos'} en 30 min</span>` : ''}<span class="chip ${nivelCls[med]}"><i></i>Con lo medido${ray ? ' en el valle' : ''}: ${nivelTxt[med]}</span><span class="chip ${nivelCls[c.nivel]}"><i></i>Si cae lo previsto: ${nivelTxt[c.nivel]}</span></span></div>
          <div class="mon-escala" role="img" aria-label="${n(m2, 1)} mm medidos en 2 h; atención desde ${n(c.mm_atencion, 1)} mm, aviso desde ${n(c.mm_aviso, 1)} mm">
            <span class="ll" style="width:${w(m2)}%"></span><span class="um" style="left:${w(c.mm_atencion)}%"><span>atención ${n(c.mm_atencion, 1)}</span></span><span class="um av" style="left:${w(c.mm_aviso)}%"><span>aviso ${n(c.mm_aviso, 1)}</span></span></div>
          <p><strong>${n(m2, 1)} mm</strong> en las últimas 2 h${cerca ? ' (' + sinParen(cerca.e.nombre) + ')' : ''}. ${med === 'aviso' ? 'Superó el umbral de aviso.' : med === 'atencion' ? 'Superó el umbral de atención.' : `Faltan ${n(c.mm_atencion - m2, 1)} mm en 2 h para atención.`}</p></div>`; }).join('') +
        `<p class="mon-pie">Fichas: las quebradas con laderas quemadas. Umbrales en milímetros en 2 horas del <a href="quebradas.html">indicador de quebradas</a>. Tormenta encima: rayos del satélite GOES-19 a menos de 8 km del centro de la quebrada. «Si cae lo previsto»: si la lluvia que pronostican los modelos para las próximas 6 horas cayera concentrada en 2.</p></div>`;
    }
    // ríos y cordillera
    if (cu) {
      const filas = Object.entries(cu.cuencas).map(([id, c]) => ({id, c, r: MON.cuenca(c, ahora)}));
      h += `<div class="mon-bloque"><h3>Ríos y cordillera, próximas 24 horas</h3><div class="tabla mon-rios"><table><thead><tr><th class="l">Cuenca</th><th>Lluvia</th><th>Nieve desde</th><th class="l">Recibe lluvia</th><th>Agua líquida</th></tr></thead><tbody>` +
        filas.map(({c, r}) => `<tr class="${r.mm >= 5 && r.fr >= 0.5 ? 'crece' : ''}"><td class="l">${c.rio}</td><td class="num">${n(r.mm)} mm<span class="mods">${r.rango.map(([m, v]) => m + ' ' + n(v)).join(' · ')}</span></td>
          <td class="num">${r.nieve == null ? '–' : n(r.nieve) + ' m'}</td><td class="l num">${r.fr == null ? '–' : `<span class="mini"><i style="width:${n(r.fr * 100)}%"></i></span>${n(r.fr * 100)} %`}</td><td class="num">${n(r.hm3, r.hm3 < 10 ? 1 : 0)} mill. m³</td></tr>`).join('') + '</tbody></table></div>';
      const ef = MON.efectos(filas);
      h += `<h3>Posibles efectos</h3>` + (ef.length ? `<ul class="mon-efectos">${ef.map(e => `<li class="${e.f ? 'f' : ''}"><span>${e.t}</span></li>`).join('')}</ul>` : '<p>Sin efectos esperables en las cuencas cordilleranas en las próximas 24 horas.</p>');
      h += `<p class="mon-pie">Lluvia media sobre cada cuenca alta según GFS (corrida de las ${cu.corrida_gfs.slice(11, 16)}), con el total de cada modelo debajo. «Nieve desde»: 300 m bajo la isoterma 0 °C. «Recibe lluvia»: parte de la cuenca bajo esa altura. «Agua líquida»: lluvia sobre esa parte. Reglas y límites en <a href="metodo.html#cordillera">Método</a>. Las alertas oficiales son de SENAPRED y la DMC.</p></div>`;
    }
    caja.innerHTML = h;
  }
  pintar(); setInterval(pintar, 5 * 60000);
})();
</script>"""

JS_AVISO = r"""<script>
__COMUN__
(async function(){
  const caja = document.getElementById('lluvia-curso'); if (!caja) return;
  const {ll, cu, qb, ahora, encima} = await MON.datos(), n = MON.n;
  const est = ll && ahora - ll.generado < 3 * 3600 ? ll.estaciones.filter(e => e.km <= 45 && e.alt < 1500).map(e => ({e, h3: MON.medida(ll, e.wmo, 3, ahora)})).filter(x => x.h3 != null) : [];
  const llueve = est.filter(x => x.h3 >= 0.5).sort((a, b) => b.h3 - a.h3);
  const cord = cu ? Object.entries(cu.cuencas).map(([id, c]) => ({c, r: MON.cuenca(c, ahora)})).filter(x => x.r.mm >= 5 && x.r.fr >= 0.5) : [];
  const qbs = qb ? qb.cuencas.filter(c => c.nivel === 'aviso' || c.nivel === 'atencion') : [];
  const conRayos = Object.values(encima).sort((a, b) => b.n - a.n);
  if (!llueve.length && !cord.length && !qbs.length && !conRayos.length) return;
  const partes = [];
  if (conRayos.length) partes.push(`hay tormenta eléctrica encima de ${conRayos.length === 1 ? 'la ' + conRayos[0].nombre : conRayos.length + ' quebradas de Santiago oriente (más rayos: ' + MON.masRayos(conRayos, 2) + ')'}; ahí la lluvia puede ser mucho mayor que la medida en el valle`);
  if (llueve.length) partes.push(`está lloviendo en la zona de Santiago: ${n(llueve[0].h3, 1)} mm en 3 h en ${llueve[0].e.nombre}`);
  if (cord.length) partes.push(`en las próximas 24 h llueve (no nieva) en buena parte de la cordillera del ${cord.map(x => x.c.rio).join(', ')}`);
  if (qbs.length) partes.push(`las quebradas quemadas de Santiago oriente están en ${qbs.some(c => c.nivel === 'aviso') ? 'aviso' : 'atención'} si la lluvia prevista se concentrara`);
  caja.innerHTML = `<strong class="t">${conRayos.length ? 'Tormenta sobre las quebradas de Santiago oriente' : 'Lluvia en curso'}</strong><p>${partes.join('; ').replace(/^./, s => s.toUpperCase())}. <a href="envivo.html#monitor">Ver qué está pasando y qué puede pasar →</a></p>`;
  caja.hidden = false;
})();
</script>"""


def seccion():
    """Sección completa para En vivo."""
    return ('<section class="card" id="monitor-card"><h2>Qué está pasando y qué puede pasar</h2><div class="monitor" id="monitor" aria-live="polite">'
            '<p>Cargando…</p></div></section>' + JS_MONITOR.replace("__COMUN__", JS_COMUN.replace("__RAW__", RAW).replace("__RAYOS__", RAW_RAYOS)))


def aviso():
    """Aviso corto para la portada y Pronóstico (oculto si no llueve ni viene lluvia en la cordillera)."""
    return '<section class="lluvia-curso" id="lluvia-curso" role="status" hidden></section>' + JS_AVISO.replace("__COMUN__", JS_COMUN.replace("__RAW__", RAW).replace("__RAYOS__", RAW_RAYOS))
