"""Pestaña "En vivo" (site/envivo.html): rayos de los últimos 90 minutos sobre la zona central (GOES-19 GLM),
METAR de las últimas 12 horas, lluvia medida en las estaciones DMC más cercanas (SYNOP) y la última corrida de cada
modelo para la Quebrada de Apoquindo, con lo medido en los bloques que ya pasaron.

La página es un armazón que se genera con el resto del sitio; los datos los lee el navegador desde la rama
datos-en-vivo (envivo/actualizar.py, cada 10 minutos) y desde el seguimiento horario de pronósticos
(hindcast/seguimiento/pronosticos.csv en main). No es un aviso: arriba va el aviso oficial vigente, si lo hay."""
import aviso_oficial
import tormenta_vivo
import monitor_lluvia
from comun import JS_DEF, aviso, d, nav, pie

RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion"

CSS = """
.vivo{display:grid;gap:14px}
@media (min-width:1000px){.vivo{grid-template-columns:minmax(0,1fr) 420px;align-items:start}}
#mapa-vivo{height:72vh;min-height:380px;border:1px solid var(--line);border-radius:var(--radius);background:var(--line-soft)}
@media (min-width:1000px){#mapa-vivo{position:sticky;top:72px}}
.vivo .panel{display:grid;gap:12px}
.cifras-vivo{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.cifras-vivo div{display:grid;gap:2px}
.cifras-vivo .v{font-family:var(--font-display);font-size:30px;font-weight:600;line-height:1.1}
.cifras-vivo .l{font-size:12.5px;color:var(--muted)}
.ley-vivo{display:flex;gap:12px;flex-wrap:wrap;font-size:13.5px;color:var(--muted)}
.ley-vivo i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
:root{--r10:#d03b3b;--r30:#e07b39;--r90:#c98500}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--r10:#ee6a6a;--r30:#f08a4b;--r90:#e0a428}}
:root[data-theme="dark"]{--r10:#ee6a6a;--r30:#f08a4b;--r90:#e0a428}
tr.lluvia td{background:color-mix(in srgb,var(--accent) 14%,transparent)}
td.alto{font-weight:700;color:var(--alto)}
td.medido{font-weight:600}
td.parcial{color:var(--muted)}
.iso-vivo{font-size:14.5px}
.estado-vivo{font-size:14.5px;color:var(--muted)}
.estado-vivo.atrasado{color:inherit;background:color-mix(in srgb,var(--medio) 12%,var(--surface));border-left:4px solid var(--medio);padding:8px 12px;border-radius:6px}
.leaflet-container{font-family:var(--font-body)}
.leaflet-control-attribution{font-size:10px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .leaflet-tile{filter:brightness(.78) contrast(1.05)}}
:root[data-theme="dark"] .leaflet-tile{filter:brightness(.78) contrast(1.05)}
"""

JS = r"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
(function(){
  const RAW = "__RAW__";
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const APOQ = [-33.40, -70.51];
  const mapa = L.map("mapa-vivo", {scrollWheelZoom: false}).setView([-33.6, -70.9], 8);
  mapa.on("focus", () => mapa.scrollWheelZoom.enable()); mapa.on("blur", () => mapa.scrollWheelZoom.disable());
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 14, attribution: "© OpenStreetMap"}).addTo(mapa);
  L.circle(APOQ, {radius: 30000, color: css("--accent"), weight: 1, dashArray: "4 4", fill: false, interactive: false}).addTo(mapa);
  fetch("quebradas/cuencas.geojson").then(r => r.json()).then(g => L.geoJSON(g, {interactive: false, style: f => {
    const q = (f.properties.prop_hm23 || 0) >= 0.01; return {color: css("--accent"), weight: q ? 2.5 : 0.8, fillOpacity: q ? 0.25 : 0.04}; }}).addTo(mapa)).catch(() => {});
  const capa = L.layerGroup().addTo(mapa), capaT = L.layerGroup().addTo(mapa);
  const hora = s => new Date(s * 1000).toLocaleTimeString("es-CL", {timeZone: "America/Santiago", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  const dist = (a, b) => { const r = Math.PI / 180, dl = (b[0] - a[0]) * r, dn = (b[1] - a[1]) * r;
    const h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dn / 2) ** 2; return 12742 * Math.asin(Math.sqrt(h)); };
  const NOM = {SCTB: "Tobalaba", SCEL: "Pudahuel", SCSN: "Santo Domingo", SCVM: "Viña del Mar"};
  const WX = s => s.replace(/\+/g, "fuerte ").replace(/-/g, "débil ").replace(/TSRA/g, "tormenta con lluvia").replace(/SHRA/g, "chubasco")
    .replace(/TS/g, "tormenta").replace(/RA/g, "lluvia").replace(/DZ/g, "llovizna").replace(/GR|GS/g, "granizo").replace(/BR/g, "neblina").replace(/FG/g, "niebla").replace(/VC/g, "cerca: ");
  // desfase de Chile continental para una fecha "YYYY-MM-DD HH:MM" (horario de verano: −03, de invierno: −04)
  function desfase(b) { const f = new Date(b.replace(" ", "T") + ":00Z"); const p = new Intl.DateTimeFormat("en-US", {timeZone: "America/Santiago", hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit"}).formatToParts(f);
    const g = k => +p.find(x => x.type === k).value; const loc = Date.UTC(g("year"), g("month") - 1, g("day"), g("hour")); const h = Math.round((loc - f.getTime()) / 3600000); return (h < 0 ? "-" : "+") + String(Math.abs(h)).padStart(2, "0") + ":00"; }
  const cifra = v => v == null ? "–" : v.toLocaleString("es-CL", {minimumFractionDigits: 1, maximumFractionDigits: 1});
  const capaLl = L.layerGroup().addTo(mapa);
  // lluvia.json: por estación, [hora UTC, mm en 1 h, mm en 6 h, °C]. Las estaciones con observador (Quinta Normal,
  // Pudahuel) informan a las 00/06/12/18 UTC la lluvia de 6 h y a las 03/09/15/21 UTC ninguna: en las sumas, sus 6 h
  // cubren esas horas. Para la última hora, la de 6 h se reconstruye restando las 5 anteriores cuando se puede.
  function lluvia(d, ahora) {
    const H = {}, H6 = {}, R = {};
    for (const e of d.estaciones) { const o = d.obs[e.wmo] || [], h = {}, h6 = {};
      o.forEach(([t, m1, m6]) => { if (m1 != null || m6 != null) R[e.wmo] = Math.max(R[e.wmo] || 0, t); if (m1 != null) h[t] = m1; if (m6 != null) h6[t] = m6; });
      H[e.wmo] = h; H6[e.wmo] = h6; }
    const hora1 = (w, t) => { if (H[w][t] != null) return H[w][t]; const m6 = H6[w][t]; if (m6 == null) return null;
      let s = 0; for (let k = 1; k < 6; k++) { const v = H[w][t - k * 3600]; if (v == null) return null; s += v; } return Math.max(0, Math.round((m6 - s) * 10) / 10); };
    // suma de las horas que terminan en (t0, t1]; parcial si el bloque sigue en curso
    const suma = (w, t0, t1) => { const h = H[w], h6 = H6[w], ini = Math.ceil((t0 + 1) / 3600) * 3600, fin = Math.min(t1, ahora), cub = new Set();
      let s = 0, n = 0, esp = 0;
      for (let t = ini; t <= fin; t += 3600) if (t % 21600 === 0 && h6[t] != null && t - 5 * 3600 >= ini) { s += h6[t]; for (let k = 0; k < 6; k++) cub.add(t - k * 3600); }
      for (let t = ini; t <= fin; t += 3600) { esp++; if (cub.has(t)) n++; else if (h[t] != null) { s += h[t]; n++; } }
      return {mm: esp && (n === esp || (n >= esp - 1 && t1 > ahora)) ? Math.round(s * 10) / 10 : null, parcial: t1 > ahora, n, esp}; };
    const filas = d.estaciones.filter(e => e.alt < 1500 && R[e.wmo] && ahora - R[e.wmo] < 6 * 3600).map(e => { let u = R[e.wmo];
      const h1 = hora1(e.wmo, u);
      let h6 = suma(e.wmo, u - 6 * 3600, u), h24 = suma(e.wmo, u - 24 * 3600, u);
      const u6 = Math.max(0, ...Object.keys(H6[e.wmo]).map(Number));   // con observador: hasta su último total de 6 h
      if ((h6.mm == null || h24.mm == null) && u6) { u = u6; h6 = suma(e.wmo, u - 6 * 3600, u); h24 = suma(e.wmo, u - 24 * 3600, u); }
      return {e, u, h1, h6, h24}; });
    document.querySelector("#lluvia tbody").innerHTML = filas.slice(0, 6).map(f => `<tr class="${(f.h24.mm || 0) >= 1 ? "lluvia" : ""}"><td class="l">${f.e.nombre}<br><span class="small muted">${f.e.alt.toLocaleString("es-CL")} m · ${Math.round(f.e.km)} km</span></td>
      <td class="num">${cifra(f.h1)}</td><td class="num">${f.h6.mm == null ? "s/d" : cifra(f.h6.mm)}</td><td class="num">${f.h24.mm == null ? "s/d" : cifra(f.h24.mm)}</td><td class="l num">${hora(f.u)}</td></tr>`).join("") || `<tr><td class="l" colspan="5">Sin reportes recientes.</td></tr>`;
    capaLl.clearLayers();
    filas.forEach(f => { const v = f.h24.mm;
      L.circleMarker([f.e.lat, f.e.lon], {radius: 7, color: css("--accent"), weight: 2, fillColor: v >= 1 ? css("--accent") : css("--surface"), fillOpacity: 0.9})
        .bindTooltip(`${f.e.nombre}: ${v == null ? "sin datos completos" : cifra(v) + " mm en 24 h"}`).addTo(capaLl); });
    const cerca = filas[0] ? filas[0].e : null;
    const col = (d.obs["85594"] || []).filter(o => o[3] != null).pop();
    return {generado: d.generado, cerca, colorado: col ? {t: col[0], temp: col[3]} : null,
      bloque: (t0, t1) => cerca && t0 < ahora ? suma(cerca.wmo, t0, t1) : null};
  }
  async function j(url) { try { const r = await fetch(url + "?t=" + Date.now()); return r.ok ? r : null; } catch (e) { return null; } }
  function csv(t) { const L = t.trim().split("\n"); const c = L[0].split(","); return L.slice(1).map(l => { const v = l.split(","); const o = {}; c.forEach((k, i) => o[k] = v[i]); return o; }); }

  async function actualizar() {
    const ahora = Date.now() / 1000;
    const [ry, mt, sg, ll, tm] = await Promise.all([j(RAW + "/datos-en-vivo/envivo/rayos.json"), j(RAW + "/datos-en-vivo/envivo/metar.json"), j(RAW + "/main/hindcast/seguimiento/pronosticos.csv"), j(RAW + "/datos-en-vivo/envivo/lluvia.json"), j(RAW + "/datos-en-vivo/envivo/tormentas.json")]);
    if (tm) { const d = await tm.json(); capaT.clearLayers();
      const act = (d.activas || []).filter(g => ahora - g.ultimo <= d.activa_min * 60);
      act.forEach(g => L.circle([g.lat, g.lon], {radius: 15000, color: css("--alto"), weight: 3, fill: false})
        .bindTooltip(`Tormenta intensificándose cerca de ${g.comuna}: salto de rayos a las ${hora(g.inicio)}, hasta ${Math.round(g.tasa_max)} rayos/min`).addTo(capaT));
      const hoy = (d.registro || []).filter(r => ahora - r.inicio < 24 * 3600).reverse();
      document.querySelector("#saltos tbody").innerHTML = hoy.map(r => `<tr class="${act.some(g => g.comuna === r.comuna) ? "lluvia" : ""}"><td class="l num">${hora(r.inicio)}</td><td class="l">${r.comuna} <span class="small muted">· ${r.region}</span></td><td class="num">${Math.round(r.tasa_max)}</td></tr>`).join("")
        || `<tr><td class="l" colspan="3">Ninguna tormenta se intensificó en las últimas 24 horas.</td></tr>`; }
    let gen = [], medido = null;
    if (ll) { const d = await ll.json(); medido = lluvia(d, ahora); }
    if (ry) { const d = await ry.json(); gen.push(d.generado);
      capa.clearLayers(); let c10 = 0, c30 = 0, c90 = 0, tot = 0;
      d.rayos.forEach(([la, lo, t]) => { const e = (ahora - t) / 60; if (e > 90) return; tot++; const col = e < 10 ? "--r10" : e < 30 ? "--r30" : "--r90";
        L.circleMarker([la, lo], {radius: e < 10 ? 4 : 3, stroke: false, fillColor: css(col), fillOpacity: 0.85, interactive: false}).addTo(capa);
        if (dist(APOQ, [la, lo]) <= 30) { c90++; if (e < 30) c30++; if (e < 10) c10++; } });
      document.getElementById("r10").textContent = c10; document.getElementById("r30").textContent = c30; document.getElementById("r90").textContent = c90;
      document.getElementById("rtot").textContent = tot.toLocaleString("es-CL"); }
    if (mt) { const d = await mt.json(); gen.push(d.generado);
      document.querySelector("#metar tbody").innerHTML = d.obs.sort((a, b) => b.t - a.t).map(o => `<tr class="${/RA|DZ|TS|GR/.test(o.wx) ? "lluvia" : ""}"><td class="l num">${hora(o.t)}</td><td class="l">${NOM[o.icao] || o.icao}</td>
        <td class="num">${o.temp ?? "–"} °C</td><td class="num">${o.wspd != null ? Math.round(o.wspd * 1.852) + " km/h" : "–"}</td><td class="num">${o.wgst ? Math.round(o.wgst * 1.852) + " km/h" : "–"}</td><td class="l">${o.wx ? WX(o.wx) : "–"}</td></tr>`).join(""); }
    if (sg) { const filas = csv(await sg.text()); const ult = {};
      filas.forEach(r => { if (!ult[r.modelo] || r.corrida_utc > ult[r.modelo]) ult[r.modelo] = r.corrida_utc; });
      // para cada modelo y bloque, la corrida más reciente que lo cubre (en los bloques futuros, la última corrida)
      const q = {}; filas.filter(r => r.punto === "Q1").forEach(r => { const k = r.modelo + "|" + r.bloque_inicio_chile; if (!q[k] || r.corrida_utc > q[k].corrida_utc) q[k] = r; });
      const mods = ["AIFS", "IFS", "GFS"].filter(m => ult[m]);
      const seg = b => new Date(b.replace(" ", "T") + ":00" + desfase(b)).getTime() / 1000;
      const bl = [...new Set(Object.values(q).map(r => r.bloque_inicio_chile))].sort().filter(b => seg(b) > ahora - (medido ? 24 : 6) * 3600).slice(0, medido ? 10 : 8);
      const fmt = v => v.toLocaleString("es-CL", {maximumFractionDigits: 1});
      document.querySelector("#pronos thead tr").innerHTML = `<th class="l">Bloque de 6 h</th>` + mods.map(m => `<th>${m}</th>`).join("") + (medido ? `<th>Medido</th>` : "");
      document.querySelector("#pronos tbody").innerHTML = bl.map(b => { const t0 = seg(b), mdd = medido ? medido.bloque(t0, t0 + 6 * 3600) : null;
        return `<tr><td class="l num">${b.slice(8, 10)}/${b.slice(5, 7)} ${b.slice(11, 13)}–${String((+b.slice(11, 13) + 6) % 24).padStart(2, "0")} h</td>` +
        mods.map(m => { const r = q[m + "|" + b]; const v = r ? +r.mm_6h : null;
          return `<td class="num${v != null && v >= 10 ? " alto" : ""}">${v == null ? "–" : fmt(v)}</td>`; }).join("") +
        (medido ? `<td class="num medido${mdd && mdd.parcial ? " parcial" : ""}">${mdd == null ? "" : mdd.mm == null ? "s/d" : cifra(mdd.mm) + (mdd.parcial ? "…" : "")}</td>` : "") + "</tr>"; }).join("");
      if (medido) document.getElementById("pronos-medido").innerHTML = ` La columna Medido es la lluvia del pluviómetro de ${medido.cerca.nombre} (${medido.cerca.alt.toLocaleString("es-CL")} m, a ${Math.round(medido.cerca.km)} km); con «…», el bloque en curso, y «s/d», sin datos completos. En los bloques que ya pasaron, cada modelo muestra su corrida más reciente que los cubría.`;
      const iso = Object.values(q).filter(r => r.modelo === "GFS" && r.isoterma0_m && seg(r.bloque_inicio_chile) <= ahora && ahora < seg(r.bloque_inicio_chile) + 6 * 3600)[0];
      if (medido && medido.colorado) { const c = medido.colorado;
        document.getElementById("iso-vivo").innerHTML = `En El Colorado (2.750 m) hacían <strong>${c.temp.toLocaleString("es-CL")} °C</strong> a las ${hora(c.t)}: ` +
          (c.temp > 0 ? "la isoterma 0 °C está más arriba de esa altura." : "la isoterma 0 °C está a esa altura o más abajo.") +
          (iso ? ` GFS la pronostica a unos ${(+iso.isoterma0_m).toLocaleString("es-CL")} m en este bloque.` : ""); }
      document.getElementById("pronos-corridas").textContent = mods.map(m => `${m} ${ult[m].slice(8, 10)}/${ult[m].slice(5, 7)} ${ult[m].slice(11, 13)} UTC`).join(", "); }
    const g = gen.length ? Math.min(...gen) : null;
    const est = document.getElementById("estado-vivo"), atraso = g ? Math.round((ahora - g) / 60) : null;
    est.classList.toggle("atrasado", atraso != null && atraso > 20);
    est.textContent = g == null ? "Los datos en vivo todavía no están disponibles."
      : atraso > 20 ? `Los datos en vivo están atrasados: son de las ${hora(g)} (hace ${atraso} min). Los rayos y mediciones posteriores todavía no aparecen; los conteos solo cubren lo que llegó.`
      : `Datos de las ${hora(g)} (hora de Chile). Se actualizan cada unos 5 minutos; esta página vuelve a leerlos cada minuto.`;
  }
  actualizar(); setInterval(actualizar, 60000);
})();
</script>
"""


def pagina(head, escribir, ahora):
    html = f"""{head("En vivo · Earth-2 Chile", "Rayos de los últimos 90 minutos sobre la zona central de Chile, lo que miden los aeródromos y lo que pronostican los modelos para las quebradas de Santiago oriente. Se actualiza cada unos 10 minutos.")}
<body>
{nav("envivo")}
<div class="wrap">
{aviso_oficial.html()}
{tormenta_vivo.html()}
<header>
  <div class="eyebrow">En vivo</div>
  <h1>Dónde hay tormenta ahora en la zona central</h1>
  <p class="lead">Los rayos que detecta el satélite GOES-19 muestran dónde hay tormentas en este momento. Junto a ellos, la lluvia que miden las estaciones más cercanas y lo que pronostican los modelos para la Quebrada de Apoquindo.</p>
  <p class="estado-vivo" id="estado-vivo" aria-live="polite">Cargando los datos en vivo…</p>
</header>
{monitor_lluvia.seccion()}
<div class="vivo">
  <div id="mapa-vivo" role="img" aria-label="Mapa de rayos de los últimos 90 minutos en la zona central, con las quebradas de Santiago oriente"></div>
  <div class="panel">
    <div class="card"><h2>Rayos cerca de las quebradas</h2>
      <div class="cifras-vivo"><div><span class="v" id="r10">–</span><span class="l">últimos 10 min</span></div><div><span class="v" id="r30">–</span><span class="l">últimos 30 min</span></div><div><span class="v" id="r90">–</span><span class="l">últimos 90 min</span></div></div>
      <p class="small muted">A menos de 30 km de la Quebrada de Apoquindo (círculo punteado). En toda la zona del mapa: <strong id="rtot">–</strong> rayos en 90 minutos. La lluvia sin tormenta eléctrica no aparece en el mapa.</p>
      <div class="ley-vivo"><span><i style="background:var(--r10)"></i>hace 0 a 10 min</span><span><i style="background:var(--r30)"></i>10 a 30 min</span><span><i style="background:var(--r90)"></i>30 a 90 min</span></div></div>
    <div class="card"><h2>Tormentas que se intensificaron</h2>
      <div class="tabla"><table id="saltos"><thead><tr><th class="l">Hora</th><th class="l">Cerca de</th><th>Rayos/min</th></tr></thead><tbody><tr><td class="l" colspan="3">Cargando…</td></tr></tbody></table></div>
      <p class="small muted">Últimas 24 horas en la zona del mapa. Se marca un {d("salto de rayos", definicion="Aumento brusco de la cantidad de rayos de una tormenta: al menos 10 por minuto y una subida mayor que 2 desviaciones estándar de los 10 minutos previos (Schultz et al., 2009 y 2011). Suele anteceder en 10 a 30 minutos granizo, rachas fuertes o, rara vez, un tornado. En EE.UU. acertó 79 % de los eventos severos y 1 de cada 3 marcas no trajo daño.")} cuando la tasa de rayos de una tormenta se dispara; en el mapa, con un anillo rojo mientras dura (30 minutos). Los umbrales son los publicados en EE.UU., no ajustados a un evento chileno: cuántas marcas traen daño en Chile se está midiendo (<a href="eventos.html">Eventos</a>). No es una alerta oficial.</p></div>
    <div class="card"><h2>Lluvia medida cerca de las quebradas</h2>
      <div class="tabla"><table id="lluvia"><thead><tr><th class="l">Estación</th><th>Última hora</th><th>6 h</th><th>24 h</th><th class="l">Hasta</th></tr></thead><tbody><tr><td class="l" colspan="5">Cargando…</td></tr></tbody></table></div>
      <p class="iso-vivo" id="iso-vivo"></p>
      <p class="small muted">Milímetros medidos por los pluviómetros de las estaciones automáticas de la {d("DMC", definicion="Dirección Meteorológica de Chile. Sus estaciones envían cada hora un mensaje SYNOP a la red de la Organización Meteorológica Mundial con la lluvia de la última hora.")}, de la más cercana a la Quebrada de Apoquindo a la más lejana, bajo 1.500 m. Llegan cada hora con unos 30 a 60 minutos de atraso y son provisorios. «s/d»: faltan horas. Quinta Normal y Pudahuel informan la lluvia cada 6 h: su «última hora» puede faltar y sus 6 y 24 h van hasta su último informe de 6 h. Los puntos del mapa son estas estaciones; rellenos, si midieron 1 mm o más en 24 h. Detalle en <a href="metodo.html#estaciones">Método</a>.</p></div>
    <div class="card"><h2>Lo que miden los aeródromos</h2>
      <div class="tabla"><table id="metar"><thead><tr><th class="l">Hora</th><th class="l">Aeródromo</th><th>Temp.</th><th>Viento</th><th>Ráfaga</th><th class="l">Tiempo</th></tr></thead><tbody></tbody></table></div>
      <p class="small muted">Reportes METAR de las últimas 12 horas, del más reciente al más antiguo; las filas con lluvia van marcadas. Los aeródromos chilenos no informan milímetros.</p></div>
    <div class="card"><h2>Lo que pronostican para la Quebrada de Apoquindo</h2>
      <div class="tabla"><table id="pronos"><thead><tr><th class="l">Bloque de 6 h</th></tr></thead><tbody></tbody></table></div>
      <p class="small muted">Lluvia en milímetros por bloque de 6 horas, última corrida de cada modelo (<span id="pronos-corridas">–</span>). En rojo, 10 mm o más: si esa lluvia se concentrara en 2 horas, la quebrada pasaría a {d("atención", definicion="Nivel intermedio del indicador de quebradas: probabilidad estimada de flujo de detritos entre 20 y 50 %. Ver la pestaña Quebradas.")}. Detalle en la pestaña <a href="quebradas.html">Quebradas</a>.<span id="pronos-medido"></span></p></div>
  </div>
</div>
{aviso()}
{pie(ahora)}
</div>
{JS.replace("__RAW__", RAW)}
{JS_DEF}
</body>
</html>
"""
    head_extra = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">'
    html = html.replace("</style>", CSS + "</style>" + head_extra, 1)
    return escribir("envivo.html", html)
