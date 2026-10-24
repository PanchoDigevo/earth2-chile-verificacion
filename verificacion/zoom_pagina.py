"""Página "Por qué 4 km" (site/zoom.html): antes y después de una tormenta real, a 25 km (ERA5) y a 4 km (SAAG-WRF).
Las imágenes y los datos los arma entrenamiento/antes_despues.py (workflow antes-despues.yml) en site/zoom/."""
import json, os
from comun import JS_DEF, d, nav, num, pie

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "site", "zoom", "datos.json")

CSS = """
.comparar{position:relative;max-width:640px;margin:0 auto;border-radius:var(--radius);overflow:hidden;border:1px solid var(--line);
  background:var(--tierra);touch-action:pan-y}
.comparar img{display:block;width:100%;height:auto;user-select:none;-webkit-user-drag:none}
.comparar .arriba{position:absolute;inset:0;clip-path:inset(0 calc(100% - var(--pos, 50%)) 0 0)}
.comparar .linea{position:absolute;top:0;bottom:0;left:var(--pos, 50%);width:2px;background:var(--fg);transform:translateX(-1px);pointer-events:none}
.comparar .etq{position:absolute;top:10px;font:600 13px var(--font-body);background:var(--surface);color:var(--fg);padding:4px 9px;border-radius:999px;border:1px solid var(--line)}
.comparar .etq.izq{left:10px} .comparar .etq.der{right:10px}
.deslizador{display:block;width:100%;max-width:640px;margin:10px auto 0;accent-color:var(--accent)}
.escala{display:flex;flex-wrap:wrap;gap:2px;max-width:640px;margin:10px auto 0;font:12px var(--font-data);color:var(--muted)}
.escala span{flex:1;min-width:34px;text-align:center;padding-top:16px;position:relative}
.escala span i{position:absolute;top:0;left:0;right:0;height:12px;border-radius:2px;outline:1px solid var(--line-soft)}
.botones{display:flex;gap:8px;justify-content:center;margin-top:8px}
.botones button{font:600 13px var(--font-body);padding:8px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer;min-height:44px}
"""


def pagina(head, escribir, ahora):
    try:
        z = json.load(open(DATOS, encoding="utf-8"))
    except Exception:
        return 0
    temp = z.get("variable") == "temp"; u = z.get("unidad", "mm")
    v = lambda x, dec=0: "–" if x is None else f"{num(x, dec)} {u}"
    if temp:
        filas = "".join(f"<tr><td class='l'>{p['nombre']}</td><td class='num'>{num(p['altura_m'], 0)} m</td><td class='num'>{v(p['mm_25km'], 1)}</td>"
                        f"<td class='num'>{v(p['mm_4km'], 1)}</td><td class='num'><strong>{v(p.get('medido'), 1)}</strong></td></tr>" for p in z["puntos"])
        cab = "<th class='l'>Lugar</th><th>Altura</th><th>A 25 km</th><th>A 4 km</th><th>Medido</th>"
        titulo = "La misma madrugada, a 25 km y a 4 km"
        lead = (f"{z['nombre']}. A la izquierda, la temperatura como la ve un pronóstico global, en cuadrados de 25 km. A la derecha, la misma hora a 4 km. "
                "Mueve el control para comparar.")
        cambia = (f"En 25 km caben el valle, la precordillera y la cordillera, y el modelo les da casi la misma temperatura. A 4 km aparece lo que importa en Chile: "
                  f"la helada del valle, el frío de altura y la costa más templada. En esta zona, a 25 km la temperatura va de <strong>{v(z['min_25km'], 1)}</strong> a "
                  f"<strong>{v(z['max_25km'], 1)}</strong>; a 4 km, de <strong>{v(z['min_4km'], 1)}</strong> a <strong>{v(z['max_4km'], 1)}</strong>. "
                  "La columna «Medido» es lo que registró cada aeródromo a esa hora: es la misma diferencia que este sitio mide todos los días.")
        pie_img = "Temperatura a 2 m, en grados. Líneas grises: relieve cada 1.000 m. Puntos: los lugares de la tabla."
    else:
        filas = "".join(f"<tr><td class='l'>{p['nombre']}</td><td class='num'>{num(p['altura_m'], 0)} m</td>"
                        f"<td class='num'>{v(p['mm_25km'])}</td><td class='num'><strong>{v(p['mm_4km'])}</strong></td></tr>" for p in z["puntos"])
        cab = "<th class='l'>Lugar</th><th>Altura</th><th>A 25 km</th><th>A 4 km</th>"
        titulo = "La misma tormenta, a 25 km y a 4 km"
        lead = (f"{z['nombre']}. A la izquierda, la lluvia total como la ve un pronóstico global, en cuadrados de 25 km. A la derecha, la misma lluvia a 4 km. "
                "Mueve el control para comparar.")
        cambia = (f"En 25 km caben el valle y la cordillera, y el modelo tiene que darles a todos la misma lluvia. A 4 km aparece cuánto más llueve en la "
                  f"precordillera que en el valle. Máximo en esta zona: <strong>{v(z['max_25km'])} a 25 km</strong> y <strong>{v(z['max_4km'])} a 4 km</strong>.")
        pie_img = f"Milímetros en {z['horas']} horas. Líneas grises: relieve cada 1.000 m. Puntos rojos: los lugares de la tabla."
    niveles, colores = z["niveles"], z["colores"]
    escala = "".join(f'<span><i style="background:{c}"></i>{num(niveles[i], 0)}</span>' for i, c in enumerate(colores))
    html = f"""{head("Por qué 4 km · Earth-2 Chile", "Un caso real de Chile visto a 25 km, como lo ve un pronóstico global, y a 4 km, como lo va a aprender CorrDiff-Chile.")}
<body>
{nav("")}
<div class="wrap">
<header>
  <div class="eyebrow">Por qué 4 km</div>
  <h1>{titulo}</h1>
  <p class="lead">{lead}</p>
</header>
<section class="card">
  <div class="comparar" id="comparar" style="--pos:50%">
    <img src="zoom/saag_4km.png" alt="Mapa a 4 km sobre Chile central">
    <img class="arriba" src="zoom/era5_25km.png" alt="Mapa a 25 km sobre Chile central">
    <div class="linea" aria-hidden="true"></div>
    <span class="etq izq">25 km · pronóstico global</span><span class="etq der">4 km</span>
  </div>
  <label class="small muted" for="pos" style="display:block;text-align:center;margin-top:8px">Mueve para comparar</label>
  <input class="deslizador" id="pos" type="range" min="0" max="100" value="50" aria-label="Proporción de la imagen a 25 km">
  <div class="botones"><button type="button" data-v="100">Ver 25 km</button><button type="button" data-v="0">Ver 4 km</button></div>
  <div class="escala" aria-label="Escala de colores">{escala}</div>
  <p class="small muted" style="text-align:center">{pie_img}</p>
</section>
<section>
  <div class="sec-head"><h2>Lo que cambia con la escala</h2>
  <p>{cambia}</p></div>
  <div class="card tabla"><table><thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table></div>
</section>
<section class="card">
  <h2>Qué es y qué no es esta imagen</h2>
  <p><strong>No es un pronóstico de CorrDiff-Chile</strong>: ese modelo todavía no existe y hay que entrenarlo. Las dos imágenes son reconstrucciones del pasado. La de 25 km es ERA5, el reanálisis de ECMWF, con el mismo tamaño de cuadrado que usan los pronósticos globales como AIFS o FourCastNet. La de 4 km es SAAG-WRF, una simulación de NCAR que reconstruyó el clima de Sudamérica hora a hora a 4 km entre 2001 y 2022.</p>
  <p>CorrDiff-Chile va a aprender con miles de pares como este a pasar de la imagen de la izquierda a la de la derecha. Cuando exista, recibirá el pronóstico global y entregará el detalle a 4 km, y se medirá en este sitio contra las estaciones. La simulación a 4 km tampoco es perfecta: es la mejor referencia abierta que hay para enseñarle la geografía de Chile.</p>
  <p class="small muted">Fuentes: {z["fuentes"]["4km"]}; {z["fuentes"]["25km"]}{"; " + z["fuentes"]["medido"] if temp else ""}. Periodo: {z["desde_utc"]} a {z["hasta_utc"]} UTC. Cómo se arma: <a href="https://github.com/PanchoDigevo/earth2-chile-verificacion/blob/main/entrenamiento/antes_despues.py" rel="noopener">entrenamiento/antes_despues.py</a>.</p>
</section>
{pie(ahora)}
</div>
<script>
(function(){{
  const c = document.getElementById('comparar'), r = document.getElementById('pos');
  const poner = v => {{ c.style.setProperty('--pos', v + '%'); r.value = v; }};
  r.addEventListener('input', () => poner(r.value));
  document.querySelectorAll('.botones button').forEach(b => b.addEventListener('click', () => poner(b.dataset.v)));
  let arrastrando = false;
  const mover = ev => {{ const x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - c.getBoundingClientRect().left;
    poner(Math.max(0, Math.min(100, Math.round(100 * x / c.clientWidth)))); }};
  c.addEventListener('pointerdown', ev => {{ arrastrando = true; mover(ev); }});
  window.addEventListener('pointermove', ev => {{ if (arrastrando) mover(ev); }});
  window.addEventListener('pointerup', () => arrastrando = false);
}})();
</script>
{JS_DEF}
</body>
</html>
"""
    return escribir("zoom.html", html.replace("</style>", CSS + "</style>", 1))
