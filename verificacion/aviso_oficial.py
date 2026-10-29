"""Avisos, alertas y alarmas oficiales vigentes de la Dirección Meteorológica de Chile, arriba del Resumen, Tu zona, En vivo
y Pronóstico (Quebradas lleva su propia copia del script, para sus comunas).

Desde el 29-oct-2026 es automático: estaciones/dmc_productos.py lee cada hora el Sistema de Alerta Meteorológica de la DMC
y estaciones/dmc_avisos.py escribe estaciones/datos/dmc_pron/avisos_vigentes.json, con las comunas que toca cada uno. El
navegador lo lee de la rama main y muestra solo lo vigente (hasta la hora de término que da la DMC). Antes, un aviso se
cargaba a mano en site/aviso_oficial.json.

Dos modos:
  html()               todos los vigentes del país (Resumen, Tu zona, En vivo); oculto si no hay ninguno.
  html(modo="comunas", ids=[...], lugar=...)  los que tocan alguna de esas comunas (Quebradas, vía comun.py).
  html(modo="comuna")  solo los que tocan la comuna elegida en Pronóstico, con la parte de la comuna (cordillera,
                       valle...); si no hay, una línea que lo dice. La página llama window.avisosDMC.comuna(id, nombre).

Este proyecto no emite alertas: copia las de la DMC con su nombre oficial y enlaza a la fuente y a SENAPRED."""

RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/main/estaciones/datos/dmc_pron/avisos_vigentes.json"
MAPA = "https://archivos.meteochile.gob.cl/portaldmc/AAA/aaa_mapa.php"

CSS = """
.avisos-dmc{border:1px solid var(--medio,#c98500);border-left:6px solid var(--medio,#c98500);background:color-mix(in srgb,var(--medio,#c98500) 9%,var(--surface));
  border-radius:var(--radius);padding:14px 16px;display:grid;gap:8px}
.avisos-dmc[hidden]{display:none}
.avisos-dmc.hay-alerta{border-color:#e06a00;border-left-color:#e06a00;background:color-mix(in srgb,#e06a00 9%,var(--surface))}
.avisos-dmc.hay-alarma{border-color:var(--alto,#d03b3b);border-left-color:var(--alto,#d03b3b);background:color-mix(in srgb,var(--alto,#d03b3b) 9%,var(--surface))}
.avisos-dmc.sin{border-color:var(--border,#ccc);border-left-color:var(--border,#ccc);background:none;padding:8px 14px}
.avisos-dmc strong.t{font-family:var(--font-display);font-size:17px}
.avisos-dmc p{max-width:80ch;margin:0}
.avisos-dmc ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.avisos-dmc li{display:grid;gap:2px}
.avisos-dmc .nivel{display:inline-block;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;border-radius:4px;
  padding:1px 6px;margin-right:6px;color:#1a1a1a;background:var(--medio,#c98500)}
.avisos-dmc .nivel.alerta{background:#e06a00;color:#fff}
.avisos-dmc .nivel.alarma{background:var(--alto,#d03b3b);color:#fff}
.avisos-dmc .cuando,.avisos-dmc .donde{font-size:14px;color:var(--muted)}
.avisos-dmc details{font-size:14px}
.avisos-dmc details table{border-collapse:collapse;margin:6px 0;font-size:13px}
.avisos-dmc details th,.avisos-dmc details td{border:1px solid var(--border,#ccc);padding:2px 6px;text-align:left}
.avisos-dmc .enlaces{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:15px}
.avisos-dmc .pie{font-size:13px;color:var(--muted)}
@media (max-width:600px){.avisos-dmc details{overflow-x:auto}}
"""

JS = r"""<script>
(function(){
  const caja = document.getElementById("avisos-dmc"); if (!caja) return;
  const MODO = caja.dataset.modo || "pais";
  const EXTRA = (document.getElementById("avisos-dmc-extra") || {}).innerHTML || "";
  let D = null, pedida = null;
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  const corto = s => esc(String(s || "").replace(/ de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) del? \d{4}/gi, ""));
  const hora = t => new Date(t * 1000).toLocaleString("es-CL", {timeZone: "America/Santiago", weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  const plural = (n, s, p) => n + " " + (n === 1 ? s : p);
  function vigentes() {
    const ahora = Date.now() / 1000;
    return (D.avisos || []).filter(a => !a.hasta_ts || a.hasta_ts > ahora);
  }
  function cuando(a) {
    const ahora = Date.now() / 1000;
    if (a.desde_ts && a.desde_ts > ahora) return `Desde ${corto(a.desde)} hasta ${corto(a.hasta)}`;
    return `En curso, hasta ${corto(a.hasta)}`;
  }
  function tablaHTML(a) {
    return (a.tabla || []).map(b => `<table><caption style="text-align:left;font-weight:600">${esc(b.region)}</caption>
      <tr><th>Zona</th>${b.dias.map(d => `<th>${esc(d)}</th>`).join("")}</tr>
      ${b.filas.map(f => `<tr>${f.map(c => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</table>`).join("");
  }
  function item(a, partes, fijo) {
    const t = (a.tipo || "Aviso").toLowerCase();
    const donde = fijo ? fijo : partes !== undefined
      ? (partes && partes.length ? "En la " + partes.join(", ") + " de la comuna" : "")
      : (a.zonas_texto || []).join(" · ");
    return `<li><div><span class="nivel ${t}">${esc(a.tipo)}</span><strong>${esc(a.fenomeno)}</strong>${a.observacion ? " · " + esc(a.observacion) : ""}</div>
      <div class="cuando">${cuando(a)}</div>${donde ? `<div class="donde">${esc(donde)}</div>` : ""}
      <details><summary>Detalle de la DMC</summary>
        <p>${esc(a.titulo)}. Condición: ${esc(a.condicion)}. Emitido el ${corto(a.emision)} (${esc(a.codigo)}).</p>
        ${a.tabla && a.tabla.length ? `<p>${esc(a.tabla_titulo)}:</p>${tablaHTML(a)}` : ""}
      </details></li>`;
  }
  function clases(lista) {
    caja.classList.toggle("hay-alarma", lista.some(a => a.tipo === "Alarma"));
    caja.classList.toggle("hay-alerta", !lista.some(a => a.tipo === "Alarma") && lista.some(a => a.tipo === "Alerta"));
  }
  function pie() {
    const viejo = Date.now() / 1000 - D.generado > 3 * 3600;
    return `<p class="pie">Copiados tal cual del Sistema de Alerta Meteorológica de la Dirección Meteorológica de Chile, que este sitio lee cada hora
      (última lectura: ${hora(D.generado)}${viejo ? "; está atrasada, revise la fuente" : ""}). Este sitio no emite alertas.</p>
      <div class="enlaces"><a href="__MAPA__" rel="noopener">Mapa oficial de avisos de la DMC</a><a href="https://senapred.cl/alertas/" rel="noopener">Alertas vigentes de SENAPRED</a>__EXTRA__</div>`;
  }
  function conteo(lista) {
    const n = t => lista.filter(a => a.tipo === t).length;
    const partes = [];
    if (n("Alarma")) partes.push(plural(n("Alarma"), "alarma", "alarmas"));
    if (n("Alerta")) partes.push(plural(n("Alerta"), "alerta", "alertas"));
    if (n("Aviso")) partes.push(plural(n("Aviso"), "aviso", "avisos"));
    return partes.length > 1 ? partes.slice(0, -1).join(", ") + " y " + partes[partes.length - 1] : partes[0];
  }
  function pais() {
    const lista = vigentes(); if (!lista.length) { caja.hidden = true; return; }
    clases(lista);
    caja.innerHTML = `<strong class="t">Dirección Meteorológica de Chile: ${conteo(lista)} vigente${lista.length === 1 ? "" : "s"}</strong>
      <ul>${lista.map(a => item(a)).join("")}</ul>${EXTRA}` + pie().replace("__EXTRA__", '<a href="pronostico.html">¿Toca tu comuna? Míralo en Pronóstico</a>');
    caja.hidden = false;
  }
  function grupo() {
    const ids = (caja.dataset.ids || "").split(","), lugar = caja.dataset.lugar || "esta zona";
    const lista = vigentes().filter(a => a.comunas && ids.some(i => i in a.comunas));
    if (!lista.length) { caja.hidden = true; return; }
    clases(lista);
    const donde = a => ids.filter(i => i in a.comunas).map(i => (D.nombres[i] || i) + (a.comunas[i].length ? " (" + a.comunas[i].join(", ") + ")" : "")).join(", ");
    caja.innerHTML = `<strong class="t">Dirección Meteorológica de Chile: ${conteo(lista)} vigente${lista.length === 1 ? "" : "s"} en ${esc(lugar)}</strong>
      <ul>${lista.map(a => item(a, undefined, "Comunas: " + donde(a))).join("")}</ul>${EXTRA}` + pie().replace("__EXTRA__", "");
    caja.hidden = false;
  }
  function comuna(id, nombre) {
    pedida = [id, nombre]; if (!D) return;
    const lista = vigentes().filter(a => a.comunas && id in a.comunas);
    clases(lista); caja.classList.toggle("sin", !lista.length);
    caja.innerHTML = lista.length
      ? `<strong class="t">Para ${esc(nombre)}, la Dirección Meteorológica de Chile tiene ${conteo(lista)} vigente${lista.length === 1 ? "" : "s"}</strong>
         <ul>${lista.map(a => item(a, a.comunas[id])).join("")}</ul>` + pie().replace("__EXTRA__", "")
      : `<p class="pie">Sin avisos, alertas ni alarmas de la Dirección Meteorológica de Chile para ${esc(nombre)} (lectura de ${hora(D.generado)}). <a href="__MAPA__" rel="noopener">Mapa oficial</a></p>`;
    caja.hidden = false;
  }
  window.avisosDMC = {comuna: comuna};
  fetch("__RAW__?t=" + Math.floor(Date.now() / 600000)).then(r => r.ok ? r.json() : null).then(d => {
    if (!d) return; D = d;
    if (MODO === "comuna") { if (pedida) comuna(pedida[0], pedida[1]); } else if (MODO === "comunas") grupo(); else pais();
    document.dispatchEvent(new Event("avisos-dmc"));
  }).catch(() => {});
})();
</script>""".replace("__RAW__", RAW).replace("__MAPA__", MAPA)


def html(extra="", modo="pais", ids=(), lugar=""):
    """Recuadro de avisos oficiales de la DMC (se llena en el navegador). `extra` (HTML) va bajo la lista cuando hay
    avisos; modo="comunas" muestra solo los que tocan alguna de `ids` (Quebradas), nombrando el `lugar`."""
    plantilla = f'<template id="avisos-dmc-extra">{extra}</template>' if extra else ""
    return (f'{plantilla}<section class="avisos-dmc" id="avisos-dmc" data-modo="{modo}" data-ids="{",".join(ids)}" data-lugar="{lugar}" '
            f'role="status" aria-label="Avisos oficiales de la DMC" hidden></section>{JS}')
