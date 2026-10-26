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
- nieve en caminos: lluvia con línea de nieve bajo 2.500 m; deshielo acelerado: isoterma sobre 3.500 m.
Es apoyo a la decisión, no una alerta: las alertas son de SENAPRED y la DMC."""

RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/datos-en-vivo/envivo/lluvia.json"

CSS = """
.monitor{display:grid;gap:12px}
.monitor .mon-ahora{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.monitor .mon-ahora div{display:grid;gap:2px}
.monitor .mon-ahora .v{font-family:var(--font-display);font-size:24px;font-weight:600;line-height:1.15}
.monitor .mon-ahora .l{font-size:13px;color:var(--muted)}
.monitor h3{margin:6px 0 0;font-size:16px}
.monitor ul.efectos{margin:0;padding-left:18px;display:grid;gap:6px}
.monitor ul.efectos li.fuerte{font-weight:600}
.monitor .q-fila{display:grid;gap:2px;padding:8px 0;border-top:1px solid var(--line-soft)}
.monitor .barra{height:8px;border-radius:4px;background:var(--line-soft);overflow:hidden;position:relative}
.monitor .barra i{position:absolute;inset:0 auto 0 0;background:var(--accent)}
.monitor .barra b{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--medio)}
.monitor .barra b.av{background:var(--alto)}
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
    const [ll, cu, qb] = await Promise.all([j('__RAW__'), j('datos/cuencas_72h.json'), j('quebradas/indicador.json')]);
    return {ll, cu, qb, ahora: Date.now() / 1000};
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
  return {n, datos, medida, isoAhora, cuenca, efectos};
})();
"""

JS_MONITOR = r"""<script>
__COMUN__
(async function(){
  const caja = document.getElementById('monitor'); if (!caja) return;
  async function pintar() {
    const {ll, cu, qb, ahora} = await MON.datos(), n = MON.n;
    const hora = s => new Date(s * 1000).toLocaleTimeString('es-CL', {timeZone: 'America/Santiago', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'});
    let html = '';
    // 1. lo que está pasando
    const est = ll ? ll.estaciones.filter(e => e.km <= 45 && e.alt < 1500).map(e => ({e, h1: MON.medida(ll, e.wmo, 1, ahora), h3: MON.medida(ll, e.wmo, 3, ahora)})).filter(x => x.h3 != null) : [];
    const max3 = est.sort((a, b) => b.h3 - a.h3)[0], iso = MON.isoAhora(ll);
    html += `<div class="mon-ahora"><div><span class="v">${max3 ? n(max3.h3, 1) + ' mm' : '–'}</span><span class="l">lluvia en 3 h, la mayor medida cerca de Santiago${max3 ? ' (' + max3.e.nombre + ')' : ''}</span></div>
      <div><span class="v">${iso ? n(iso.iso) + ' m' : '–'}</span><span class="l">isoterma 0 °C estimada ahora${iso ? ' (El Colorado, 2.750 m, ' + n(iso.temp, 1) + ' °C a las ' + hora(iso.t) + ')' : ''}</span></div></div>`;
    // 2. quebradas: medido contra los umbrales del indicador
    const qs = qb ? qb.cuencas.filter(c => c.nivel !== 'sin_quema') : [];
    if (qs.length && est.length) {
      const cerca = est.filter(x => x.e.km <= 25).map(x => ({e: x.e, m2: MON.medida(ll, x.e.wmo, 2, ahora) || 0})).sort((a, b) => b.m2 - a.m2)[0];
      const m2 = cerca ? cerca.m2 : 0;
      html += `<h3>Quebradas quemadas de Santiago oriente</h3>`;
      qs.forEach(c => { const tope = c.mm_aviso * 1.4, w = x => Math.min(100, x / tope * 100);
        html += `<div class="q-fila"><span><strong>${c.nombre}</strong> · pronóstico: nivel ${c.nivel === 'aviso' ? 'aviso' : c.nivel === 'atencion' ? 'atención' : 'bajo'} si la lluvia de las próximas 6 h (hasta ${n(qb.mm6, 1)} mm) cayera en 2 h</span>
          <div class="barra" role="img" aria-label="${n(m2, 1)} mm medidos en 2 h; atención desde ${n(c.mm_atencion, 1)} mm, aviso desde ${n(c.mm_aviso, 1)} mm"><i style="width:${w(m2)}%"></i><b style="left:${w(c.mm_atencion)}%"></b><b class="av" style="left:${w(c.mm_aviso)}%"></b></div>
          <span class="small muted">Medido: ${n(m2, 1)} mm en 2 h${cerca ? ' (' + cerca.e.nombre + ', la estación más lluviosa a menos de 25 km)' : ''}. Atención desde ${n(c.mm_atencion, 1)} mm en 2 h; aviso desde ${n(c.mm_aviso, 1)} mm. ${m2 >= c.mm_aviso ? '<strong>Ya superó el umbral de aviso.</strong>' : m2 >= c.mm_atencion ? '<strong>Ya superó el umbral de atención.</strong>' : 'Faltan ' + n(c.mm_atencion - m2, 1) + ' mm en 2 h para atención.'}</span></div>`; });
    }
    // 3. ríos y cordillera
    if (cu) {
      const filas = Object.entries(cu.cuencas).map(([id, c]) => ({id, c, r: MON.cuenca(c, ahora)}));
      html += `<h3>Ríos y cordillera, próximas 24 horas</h3><div class="tabla"><table><thead><tr><th class="l">Cuenca</th><th>Lluvia</th><th>Línea de nieve</th><th>Cuenca con lluvia</th><th>Lluvia líquida</th></tr></thead><tbody>` +
        filas.map(({c, r}) => `<tr class="${r.mm >= 5 && r.fr >= 0.5 ? 'lluvia' : ''}"><td class="l">${c.nombre}</td><td class="num">${n(r.mm)} mm<br><span class="small muted">${r.rango.map(([m, v]) => m + ' ' + n(v)).join(' · ')}</span></td>
          <td class="num">${r.nieve == null ? '–' : n(r.nieve) + ' m'}</td><td class="num">${r.fr == null ? '–' : n(r.fr * 100) + ' %'}</td><td class="num">${n(r.hm3, r.hm3 < 10 ? 1 : 0)} mill. m³</td></tr>`).join('') + '</tbody></table></div>';
      const ef = MON.efectos(filas);
      html += `<h3>Posibles efectos</h3>` + (ef.length ? `<ul class="efectos">${ef.map(e => `<li class="${e.f ? 'fuerte' : ''}">${e.t}</li>`).join('')}</ul>` : '<p>Sin efectos esperables en las cuencas cordilleranas en las próximas 24 horas.</p>');
      html += `<p class="small muted">Lluvia media sobre cada cuenca según GFS (corrida de las ${cu.corrida_gfs.slice(11, 16)}), con el total de cada modelo debajo; línea de nieve: ${cu.bajo_isoterma_m} m bajo la isoterma 0 °C; lluvia líquida: lluvia × área bajo la línea de nieve. Reglas y límites en <a href="metodo.html#cordillera">Método</a>. Las alertas oficiales son de SENAPRED y la DMC.</p>`;
    }
    caja.innerHTML = html || '<p>Sin datos todavía.</p>';
  }
  pintar(); setInterval(pintar, 5 * 60000);
})();
</script>"""

JS_AVISO = r"""<script>
__COMUN__
(async function(){
  const caja = document.getElementById('lluvia-curso'); if (!caja) return;
  const {ll, cu, qb, ahora} = await MON.datos(), n = MON.n;
  const est = ll && ahora - ll.generado < 3 * 3600 ? ll.estaciones.filter(e => e.km <= 45 && e.alt < 1500).map(e => ({e, h3: MON.medida(ll, e.wmo, 3, ahora)})).filter(x => x.h3 != null) : [];
  const llueve = est.filter(x => x.h3 >= 0.5).sort((a, b) => b.h3 - a.h3);
  const cord = cu ? Object.entries(cu.cuencas).map(([id, c]) => ({c, r: MON.cuenca(c, ahora)})).filter(x => x.r.mm >= 5 && x.r.fr >= 0.5) : [];
  const qbs = qb ? qb.cuencas.filter(c => c.nivel === 'aviso' || c.nivel === 'atencion') : [];
  if (!llueve.length && !cord.length && !qbs.length) return;
  const partes = [];
  if (llueve.length) partes.push(`está lloviendo en la zona de Santiago: ${n(llueve[0].h3, 1)} mm en 3 h en ${llueve[0].e.nombre}`);
  if (cord.length) partes.push(`en las próximas 24 h llueve (no nieva) en buena parte de la cordillera del ${cord.map(x => x.c.rio).join(', ')}`);
  if (qbs.length) partes.push(`las quebradas quemadas de Santiago oriente están en ${qbs.some(c => c.nivel === 'aviso') ? 'aviso' : 'atención'} si la lluvia prevista se concentrara`);
  caja.innerHTML = `<strong class="t">Lluvia en curso</strong><p>${partes.join('; ').replace(/^./, s => s.toUpperCase())}. <a href="envivo.html#monitor">Ver qué está pasando y qué puede pasar →</a></p>`;
  caja.hidden = false;
})();
</script>"""


def seccion():
    """Sección completa para En vivo."""
    return ('<section class="card monitor" id="monitor-card"><h2>Qué está pasando y qué puede pasar</h2><div class="monitor" id="monitor" aria-live="polite">'
            '<p>Cargando…</p></div></section>' + JS_MONITOR.replace("__COMUN__", JS_COMUN.replace("__RAW__", RAW)))


def aviso():
    """Aviso corto para la portada y Pronóstico (oculto si no llueve ni viene lluvia en la cordillera)."""
    return '<section class="lluvia-curso" id="lluvia-curso" role="status" hidden></section>' + JS_AVISO.replace("__COMUN__", JS_COMUN.replace("__RAW__", RAW))
