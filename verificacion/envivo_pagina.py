"""Pestaña "En vivo" (site/envivo.html): rayos de los últimos 90 minutos sobre la zona central (GOES-19 GLM),
METAR de las últimas 12 horas y la última corrida de cada modelo para la Quebrada de Apoquindo.

La página es un armazón que se genera con el resto del sitio; los datos los lee el navegador desde la rama
datos-en-vivo (envivo/actualizar.py, cada 10 minutos) y desde el seguimiento horario de pronósticos
(hindcast/seguimiento/pronosticos.csv en main). No es un aviso: arriba va el aviso oficial vigente, si lo hay."""
import aviso_oficial
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
  const capa = L.layerGroup().addTo(mapa);
  const hora = s => new Date(s * 1000).toLocaleTimeString("es-CL", {timeZone: "America/Santiago", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  const dist = (a, b) => { const r = Math.PI / 180, dl = (b[0] - a[0]) * r, dn = (b[1] - a[1]) * r;
    const h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dn / 2) ** 2; return 12742 * Math.asin(Math.sqrt(h)); };
  const NOM = {SCTB: "Tobalaba", SCEL: "Pudahuel", SCSN: "Santo Domingo", SCVM: "Viña del Mar"};
  const WX = s => s.replace(/\+/g, "fuerte ").replace(/-/g, "débil ").replace(/TSRA/g, "tormenta con lluvia").replace(/SHRA/g, "chubasco")
    .replace(/TS/g, "tormenta").replace(/RA/g, "lluvia").replace(/DZ/g, "llovizna").replace(/GR|GS/g, "granizo").replace(/BR/g, "neblina").replace(/FG/g, "niebla").replace(/VC/g, "cerca: ");
  async function j(url) { try { const r = await fetch(url + "?t=" + Date.now()); return r.ok ? r : null; } catch (e) { return null; } }
  function csv(t) { const L = t.trim().split("\n"); const c = L[0].split(","); return L.slice(1).map(l => { const v = l.split(","); const o = {}; c.forEach((k, i) => o[k] = v[i]); return o; }); }

  async function actualizar() {
    const ahora = Date.now() / 1000;
    const [ry, mt, sg] = await Promise.all([j(RAW + "/datos-en-vivo/envivo/rayos.json"), j(RAW + "/datos-en-vivo/envivo/metar.json"), j(RAW + "/main/hindcast/seguimiento/pronosticos.csv")]);
    let gen = [];
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
      const q = filas.filter(r => r.punto === "Q1" && r.corrida_utc === ult[r.modelo]); const mods = ["AIFS", "IFS", "GFS"].filter(m => ult[m]);
      const bl = [...new Set(q.map(r => r.bloque_inicio_chile))].sort().filter(b => new Date(b.replace(" ", "T") + ":00-03:00").getTime() / 1000 > ahora - 6 * 3600).slice(0, 8);
      document.querySelector("#pronos thead tr").innerHTML = `<th class="l">Bloque de 6 h</th>` + mods.map(m => `<th>${m}</th>`).join("");
      document.querySelector("#pronos tbody").innerHTML = bl.map(b => `<tr><td class="l num">${b.slice(8, 10)}/${b.slice(5, 7)} ${b.slice(11, 13)}–${String((+b.slice(11, 13) + 6) % 24).padStart(2, "0")} h</td>` +
        mods.map(m => { const r = q.find(x => x.modelo === m && x.bloque_inicio_chile === b); const v = r ? +r.mm_6h : null;
          return `<td class="num${v != null && v >= 10 ? " alto" : ""}">${v == null ? "–" : v.toLocaleString("es-CL", {maximumFractionDigits: 1})}</td>`; }).join("") + "</tr>").join("");
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
<header>
  <div class="eyebrow">En vivo</div>
  <h1>Dónde hay tormenta ahora en la zona central</h1>
  <p class="lead">Los rayos que detecta el satélite GOES-19 muestran dónde hay tormentas en este momento. Junto a ellos, lo que miden los aeródromos y lo que pronostican los modelos para la Quebrada de Apoquindo.</p>
  <p class="estado-vivo" id="estado-vivo" aria-live="polite">Cargando los datos en vivo…</p>
</header>
<div class="vivo">
  <div id="mapa-vivo" role="img" aria-label="Mapa de rayos de los últimos 90 minutos en la zona central, con las quebradas de Santiago oriente"></div>
  <div class="panel">
    <div class="card"><h2>Rayos cerca de las quebradas</h2>
      <div class="cifras-vivo"><div><span class="v" id="r10">–</span><span class="l">últimos 10 min</span></div><div><span class="v" id="r30">–</span><span class="l">últimos 30 min</span></div><div><span class="v" id="r90">–</span><span class="l">últimos 90 min</span></div></div>
      <p class="small muted">A menos de 30 km de la Quebrada de Apoquindo (círculo punteado). En toda la zona del mapa: <strong id="rtot">–</strong> rayos en 90 minutos. La lluvia sin tormenta eléctrica no aparece en el mapa.</p>
      <div class="ley-vivo"><span><i style="background:var(--r10)"></i>hace 0 a 10 min</span><span><i style="background:var(--r30)"></i>10 a 30 min</span><span><i style="background:var(--r90)"></i>30 a 90 min</span></div></div>
    <div class="card"><h2>Lo que miden los aeródromos</h2>
      <div class="tabla"><table id="metar"><thead><tr><th class="l">Hora</th><th class="l">Aeródromo</th><th>Temp.</th><th>Viento</th><th>Ráfaga</th><th class="l">Tiempo</th></tr></thead><tbody></tbody></table></div>
      <p class="small muted">Reportes METAR de las últimas 12 horas, del más reciente al más antiguo; las filas con lluvia van marcadas. Los aeródromos chilenos no informan milímetros.</p></div>
    <div class="card"><h2>Lo que pronostican para la Quebrada de Apoquindo</h2>
      <div class="tabla"><table id="pronos"><thead><tr><th class="l">Bloque de 6 h</th></tr></thead><tbody></tbody></table></div>
      <p class="small muted">Lluvia en milímetros por bloque de 6 horas, última corrida de cada modelo (<span id="pronos-corridas">–</span>). En rojo, 10 mm o más: si esa lluvia se concentrara en 2 horas, la quebrada pasaría a {d("atención", definicion="Nivel intermedio del indicador de quebradas: probabilidad estimada de flujo de detritos entre 20 y 50 %. Ver la pestaña Quebradas.")}. Detalle en la pestaña <a href="quebradas.html">Quebradas</a>.</p></div>
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
