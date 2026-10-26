"""Aviso de tormenta intensificándose (salto de rayos), arriba de la portada, Pronóstico y En vivo.

Lo arma el navegador con datos-en-vivo/envivo/tormentas.json (envivo/actualizar.py, cada 5 minutos): si alguna tormenta
tuvo un salto de rayos en los últimos 30 minutos, se muestra; si no, la sección queda oculta. Si los datos en vivo
están atrasados más de 30 minutos, no se muestra nada, para no dar por actual algo viejo.

Es un aviso, no una alerta: dice qué detectó el satélite, cuántas veces un salto así no trae daño y enlaza a SENAPRED
y la DMC, que son quienes alertan."""

RAW = "https://raw.githubusercontent.com/PanchoDigevo/earth2-chile-verificacion/datos-en-vivo/envivo/tormentas.json"

CSS = """
.tormenta-vivo{border:1px solid var(--alto);border-left:6px solid var(--alto);background:color-mix(in srgb,var(--alto) 10%,var(--surface));
  border-radius:var(--radius);padding:14px 16px;display:grid;gap:6px}
.tormenta-vivo[hidden]{display:none}
.tormenta-vivo strong.t{font-family:var(--font-display);font-size:17px}
.tormenta-vivo p{max-width:80ch;margin:0}
.tormenta-vivo .enlaces{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:15px}
"""

JS = r"""<script>
(async function(){
  const caja = document.getElementById("tormenta-vivo"); if (!caja) return;
  let d; try { const r = await fetch("__RAW__?t=" + Date.now()); if (!r.ok) return; d = await r.json(); } catch (e) { return; }
  const ahora = Date.now() / 1000;
  if (ahora - d.generado > 1800) return;
  const act = (d.activas || []).filter(g => ahora - g.ultimo <= d.activa_min * 60);
  if (!act.length) return;
  const hora = s => new Date(s * 1000).toLocaleTimeString("es-CL", {timeZone: "America/Santiago", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  const lugar = g => `${g.comuna} (${g.region})`;
  const lugares = act.map(lugar);
  const lista = lugares.length === 1 ? lugares[0] : lugares.slice(0, -1).join(", ") + " y " + lugares[lugares.length - 1];
  const g = act[0];
  caja.innerHTML = `<strong class="t">${act.length === 1 ? "Tormenta intensificándose" : act.length + " tormentas intensificándose"} cerca de ${lista}</strong>
    <p>El satélite GOES-19 detectó un salto en la cantidad de rayos${act.length === 1 ? ` a las ${hora(g.inicio)}: ${Math.round(g.tasa_max)} rayos por minuto` : ""}. Un salto así suele anteceder en 10 a 30 minutos granizo, rachas fuertes y, rara vez, un tornado; muchas veces no trae daño (en EE.UU., uno de cada tres). En Chile lo estamos midiendo. No es una alerta oficial.</p>
    <div class="enlaces">${location.pathname.endsWith("envivo.html") ? "" : '<a href="envivo.html">Ver los rayos en vivo</a>'}<a href="https://senapred.cl/alertas/" rel="noopener">Alertas vigentes de SENAPRED</a><a href="https://www.meteochile.gob.cl/PortalDMC-web/index.xhtml" rel="noopener">Dirección Meteorológica de Chile</a></div>`;
  caja.hidden = false;
})();
</script>"""


def html():
    return '<section class="tormenta-vivo" id="tormenta-vivo" role="status" aria-live="polite" hidden></section>' + JS.replace("__RAW__", RAW)
