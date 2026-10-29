"""Piezas comunes a todas las páginas del sitio: navegación, formato de números y fechas (convención chilena),
aviso oficial, pie de página y definiciones que se abren al tocar un término.

Se importa desde render_site.py (Resumen y Tu zona, cada corrida) y render_historico.py (Eventos y Método).
site/quebradas.html es estática: lleva copiados la barra (nav("quebradas")), CSS_NAV/CSS_DEF/JS_DEF y la respuesta por dirección (direccion.py).
Si cambias algo aquí, corre `python verificacion/comun.py` para actualizar quebradas.html.
Brief de diseño: docs/brief_sitio.md."""
import datetime as dt
import math
import os
import re

try:
    from zoneinfo import ZoneInfo
    TZ_CL = ZoneInfo("America/Santiago")
except Exception:          # sin base de zonas horarias: se informa en UTC
    TZ_CL = None

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = "https://github.com/PanchoDigevo/earth2-chile-verificacion"

# Las secciones responden a las preguntas del visitante, no al origen de los datos.
SECCIONES = [
    ("resumen", "./", "Resumen"),
    ("pronostico", "pronostico.html", "Pronóstico"),
    ("zona", "zona.html", "Tu zona"),
    ("eventos", "eventos.html", 'Eventos<span class="largo">2026</span>'),
    ("quebradas", "quebradas.html", "Quebradas"),
    ("escenarios", "escenarios.html", "Escenarios"),
    ("envivo", "envivo.html", "En vivo"),
    ("gemelo", "gemelo.html", "Gemelo"),
    ("metodo", "metodo.html", "Método"),
]

# Nombre de cada evento del catálogo: título de su tarjeta y forma corta para usar dentro de una frase.
EVENTOS = {
    "santiago-13oct": ("Santiago, tormenta del 13 de octubre", "la tormenta de Santiago del 13 de octubre"),
    "lascondes-oct": ("Las Condes, aluvión del 8 de octubre", "el aluvión de Las Condes"),
    "centrosur-ago": ("Centro-sur, frontal del 30 de julio al 2 de agosto", "el frontal del centro-sur"),
    "coquimbo-jul": ("Coquimbo y Huasco, frontal del 14 al 24 de julio", "el frontal de Coquimbo"),
    "incendios-ene": ("Ñuble y Biobío, incendios del 17 al 21 de enero", "los incendios de enero en Ñuble y Biobío"),
}

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ---------- números ----------
def _nan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def num(v, dec=1, unidad=""):
    """Número con punto de miles, coma decimal y signo menos tipográfico (−). '–' si no hay dato."""
    if _nan(v):
        return "–"
    v = float(v)
    if round(v, dec) == 0:
        v = 0.0                                   # evita "−0,0"
    s = f"{abs(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if v < 0 else "") + s + unidad


def entero(v):
    return num(v, 0)


def signo(v, dec=1, unidad=""):
    if _nan(v):
        return "–"
    return ("+" if round(float(v), dec) > 0 else "") + num(v, dec, unidad)


# ---------- fechas ----------
def a_chile(ts):
    """Convierte un instante UTC (datetime, pandas Timestamp o texto ISO) a hora de Chile."""
    if isinstance(ts, str):
        ts = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if hasattr(ts, "to_pydatetime"):
        ts = ts.to_pydatetime()
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(TZ_CL) if TZ_CL else ts


def hora_chile(ts):
    """'16 oct, 10:43 (hora de Chile)'."""
    t = a_chile(ts)
    sufijo = "hora de Chile" if TZ_CL else "UTC"
    return f"{t.day} {MESES[t.month - 1]}, {t:%H:%M} ({sufijo})"


def fecha(ts, largo=False):
    t = a_chile(ts) if not isinstance(ts, dt.date) or isinstance(ts, dt.datetime) else ts
    return f"{t.day} de {MESES_LARGO[t.month - 1]} de {t.year}" if largo else f"{t.day} {MESES[t.month - 1]} {t.year}"


# ---------- definiciones al tocar ----------
GLOSARIO = {
    "error medio": "Cuánto se equivocó el pronóstico en promedio, hacia arriba o hacia abajo. Si dice 1,5 °C, el pronóstico "
                   "estuvo típicamente un grado y medio sobre o bajo lo que marcó el termómetro.",
    "sesgo": "La dirección del error. Negativo: el modelo pronostica más frío de lo que ocurre. Positivo: más calor.",
    "plazo": "Cuántas horas antes se hizo el pronóstico. A 24 h es el pronóstico de mañana; a 72 h, el de pasado mañana y un día más.",
    "corrección por estación": "Cada aeródromo le enseña al sistema su error típico, aprendido solo con datos de 2025, y se le resta "
                               "al pronóstico de 2026. Es la primera capa chilena, la más simple.",
    "preliminar": "Cifra con pocos datos todavía (menos de 30 comparaciones). Puede cambiar bastante en los próximos días.",
    "comparaciones": "Cada vez que un pronóstico se compara con lo que de verdad midió un aeródromo a esa misma hora.",
    "corrida": "Cada vez que un modelo calcula un pronóstico nuevo. Los tres modelos corren cuatro veces al día.",
    "25 km": "Los modelos globales dividen el planeta en cuadrados de unos 25 km de lado y dan un solo valor por cuadrado. "
             "En Chile, un cuadrado puede incluir mar, costa y cerro a la vez.",
    "AIFS": "El modelo de inteligencia artificial del Centro Europeo de Pronósticos (ECMWF). Aprende de décadas de datos.",
    "IFS": "El modelo físico del Centro Europeo (ECMWF): resuelve las ecuaciones de la atmósfera.",
    "GFS": "El modelo físico global de Estados Unidos (NOAA).",
    "WRF-DMC": "El modelo regional de la Dirección Meteorológica de Chile (WRF), leído de su meteograma público por estación. "
               "Es la referencia oficial: lo que ya tiene el país.",
    "indicador": "Probabilidad estimada de que una quebrada quemada produzca un flujo de detritos con cierta lluvia. Es apoyo a "
                 "la decisión, no una alerta: las alertas oficiales son de la DMC y SENAPRED.",
}


def d(termino, texto=None, definicion=None):
    """Término con definición que se abre al tocarlo. texto = lo que se muestra (por defecto, el término)."""
    definicion = definicion or GLOSARIO.get(termino.lower()) or GLOSARIO.get(termino, "")
    texto = texto or termino
    definicion = definicion.replace('"', "&quot;")
    return f'<button type="button" class="def" data-def="{definicion}">{texto}</button>'


CSS_DEF = """
.def{all:unset;cursor:help;border-bottom:1.5px dotted currentColor;text-underline-offset:2px}
.def:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px}
.def-pop{position:absolute;z-index:2000;max-width:min(320px,calc(100vw - 32px));background:var(--fg);color:var(--bg);
  font:400 14.5px/1.45 var(--font-body);padding:10px 12px;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.18)}
"""

JS_DEF = """
<script>
(function(){
  let pop=null, dueno=null;
  function cerrar(){ if(pop){pop.remove();pop=null;} if(dueno){dueno.setAttribute('aria-expanded','false');dueno=null;} }
  document.addEventListener('click',function(e){
    const b=e.target.closest('.def');
    if(!b){ if(pop && !e.target.closest('.def-pop')) cerrar(); return; }
    e.preventDefault();
    if(dueno===b){cerrar();return;}
    cerrar(); dueno=b; b.setAttribute('aria-expanded','true');
    pop=document.createElement('div'); pop.className='def-pop'; pop.setAttribute('role','tooltip'); pop.textContent=b.dataset.def;
    document.body.appendChild(pop);
    const r=b.getBoundingClientRect(), w=pop.offsetWidth;
    let x=r.left+window.scrollX; x=Math.min(x, window.scrollX+document.documentElement.clientWidth-w-16); x=Math.max(16+window.scrollX,x);
    pop.style.left=x+'px'; pop.style.top=(r.bottom+window.scrollY+6)+'px';
  });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') cerrar(); });
  window.addEventListener('resize',cerrar);
})();
</script>
"""


# ---------- navegación ----------
CSS_NAV = """
.topnav{position:sticky;top:0;z-index:1100;background:var(--surface);border-bottom:1px solid var(--line)}
.topnav .in{max-width:1400px;margin:0 auto;padding-inline:16px;display:flex;align-items:center;gap:16px;min-height:52px}
.topnav .marca{font-family:var(--font-display);font-weight:600;font-size:15px;color:var(--fg);text-decoration:none;white-space:nowrap;letter-spacing:-.01em}
.topnav .marca small{color:var(--muted);font-weight:500;font-size:13px;margin-left:8px}
.topnav .tabs{display:flex;gap:2px;margin-left:auto;overflow-x:auto;scrollbar-width:none}
.topnav .tabs::-webkit-scrollbar{display:none}
.topnav .tabs a{display:inline-flex;align-items:center;height:52px;padding:0 12px;color:var(--muted);text-decoration:none;font-weight:600;font-size:14.5px;border-bottom:3px solid transparent;white-space:nowrap}
.topnav .tabs a:hover{color:var(--fg)}
.topnav .tabs a.activa{color:var(--fg);border-bottom-color:var(--accent)}
.topnav .tabs a:focus-visible{outline:2px solid var(--accent);outline-offset:-4px;border-radius:4px}
.topnav .largo{margin-left:.3em}
@media (max-width:1060px){
  .topnav .in{flex-wrap:wrap;gap:0;padding-inline:0}
  .topnav .marca{padding:10px 16px 2px;font-size:14px}
  .topnav .marca small{display:none}
  .topnav .tabs{margin-left:0;width:100%;padding-inline:6px}
  .topnav .tabs a{height:42px;padding:0 10px;font-size:14px}
  .topnav .largo{display:none}
}
@media (max-width:620px){
  /* en teléfono las seis pestañas no caben: se desplazan y el borde derecho se desvanece como pista */
  .topnav .tabs{-webkit-mask-image:linear-gradient(to right,#000 85%,transparent);mask-image:linear-gradient(to right,#000 85%,transparent);padding-right:28px}
  .topnav .tabs a{padding:0 9px}
}
"""


def nav(activa):
    tabs = []
    for clave, href, titulo in SECCIONES:
        extra = ' class="activa" aria-current="page"' if clave == activa else ""
        tabs.append(f'<a href="{href}"{extra}>{titulo}</a>')
    return ('<nav class="topnav" aria-label="Secciones del sitio"><div class="in">'
            '<a class="marca" href="./">Earth-2 Chile<small>verificación pública del pronóstico</small></a>'
            f'<div class="tabs">{"".join(tabs)}</div></div></nav>')


# ---------- aviso oficial y pie ----------
def aviso():
    return ('<div class="aviso"><p class="small">Apoyo a la decisión, no una alerta. Las alertas oficiales son de la '
            '<a href="https://www.meteochile.gob.cl/" rel="noopener">Dirección Meteorológica de Chile</a> y de '
            '<a href="https://www.senapred.cl/" rel="noopener">SENAPRED</a>.</p></div>')


def pie(generado=None):
    cuando = f"Actualizado el {hora_chile(generado)}. " if generado is not None else ""
    return (f'<footer><p>{cuando}Datos abiertos: ECMWF (AIFS e IFS, CC-BY 4.0), NOAA (GFS y METAR, dominio público), '
            'Iowa Environmental Mesonet, DMC (estaciones automáticas, SYNOP vía Ogimet), Copernicus (DEM y Sentinel-2), '
            'OpenStreetMap (ODbL), SERNAGEOMIN. '
            f'<a href="metodo.html">Cómo se calcula</a> · Código abierto: <a href="{REPO}" rel="noopener">GitHub</a>.</p>'
            '<p><em>Información de apoyo a la decisión. No reemplaza los avisos ni las alertas oficiales de la Dirección '
            'Meteorológica de Chile ni de SENAPRED.</em></p></footer>')


# ---------- quebradas.html (estática) ----------
def actualizar_quebradas():
    """Reemplaza en site/quebradas.html la barra de navegación y los bloques CSS/JS comunes marcados."""
    ruta = os.path.join(AQUI, "..", "site", "quebradas.html")
    s = open(ruta, encoding="utf-8").read()
    s = re.sub(r'<nav class="topnav".*?</nav>', nav("quebradas"), s, count=1, flags=re.S)
    s = re.sub(r"/\* comun:css \*/.*?/\* /comun:css \*/", "/* comun:css */" + CSS_NAV + CSS_DEF + "/* /comun:css */", s, count=1, flags=re.S)
    s = re.sub(r"<!-- comun:js -->.*?<!-- /comun:js -->", "<!-- comun:js -->" + JS_DEF + "<!-- /comun:js -->", s, count=1, flags=re.S)
    import direccion
    s = re.sub(r"<!-- direccion:html -->.*?<!-- /direccion:html -->", "<!-- direccion:html -->" + direccion.html() + "<!-- /direccion:html -->", s, count=1, flags=re.S)
    s = re.sub(r"/\* direccion:css \*/.*?/\* /direccion:css \*/", "/* direccion:css */" + direccion.CSS + "/* /direccion:css */", s, count=1, flags=re.S)
    s = re.sub(r"<!-- direccion:js -->.*?<!-- /direccion:js -->", lambda m: "<!-- direccion:js -->" + direccion.js() + "<!-- /direccion:js -->", s, count=1, flags=re.S)
    open(ruta, "w", encoding="utf-8").write(s)
    print("quebradas.html: barra y bloques comunes actualizados")


if __name__ == "__main__":
    actualizar_quebradas()


# ---------- etapas del proyecto (portada y Método) ----------
ETAPAS = [
    ("Funciona hoy", "hecho",
     "Verificación diaria de tres pronósticos globales de 25 km (AIFS, IFS y GFS, que bajamos ya calculados) y corrección por estación "
     "(medida: baja el error entre 19 y 28 %), junto a la referencia oficial: el pronóstico y el modelo WRF de la Dirección Meteorológica "
     "de Chile, verificados con la misma vara. Sobre eso: pronóstico por comuna a 48 h y 15 días, 16 escenarios con el ensamble de IA de ECMWF, "
     "dos avisos de tormenta (ambiente a 72 h y salto de rayos del GOES-19 cada 5 min), monitor de lluvia y nieve en la cordillera, "
     "quebradas quemadas con respuesta por dirección, 76 cámaras públicas y el gemelo del lugar con la nieve pintada sobre el terreno."),
    ("Siguiente", "curso",
     "Correr nosotros, en las GPUs del POD, modelos globales de Earth-2: AIFS (para comprobar que da lo mismo que el de ECMWF) y FourCastNet, "
     "y verificarlos aquí junto a los demás. Sirven en Chile tal como vienen, porque cubren todo el planeta."),
    ("Por entrenar", "pendiente",
     "CorrDiff-Chile, el zoom de 25 a 4 km. NVIDIA entrega la receta, pero los modelos ya entrenados solo existen para Estados Unidos y Taiwán "
     "y no sirven para Chile. Hay que entrenarlo con 22 años de simulación del clima chileno a 4 km (SAAG-WRF). Todavía no existe: nada de "
     "lo que se ve hoy en el sitio usa CorrDiff. <a href=\"zoom.html\">Mira en una tormenta real qué cambia de 25 a 4 km</a>."),
]

CSS_ETAPAS = """
.etapas{display:grid;gap:10px;margin:0;padding:0;list-style:none}
.etapas li{display:grid;grid-template-columns:8.5em 1fr;gap:4px 12px;align-items:start}
.etapas .tag{justify-self:start}
.etapas .tag{font:600 12px var(--font-body);letter-spacing:.02em;padding:3px 9px;border-radius:999px;border:1px solid var(--line);white-space:nowrap;margin-top:2px}
.etapas .hecho .tag{background:var(--accent-soft);border-color:var(--accent);color:var(--fg)}
.etapas .curso .tag{background:color-mix(in srgb,var(--medio) 14%,var(--surface));border-color:var(--medio);color:var(--fg)}
.etapas .pendiente .tag{background:var(--surface);border-style:dashed;color:var(--muted)}
.etapas p{margin:0}
@media (max-width:560px){.etapas li{grid-template-columns:1fr}}
"""


def etapas():
    """Bloque "En qué etapa estamos": qué funciona hoy, qué sigue y qué hay que entrenar."""
    filas = "".join(f'<li class="{c}"><span class="tag">{t}</span><p>{x}</p></li>' for t, c, x in ETAPAS)
    return (f'<section class="card" aria-labelledby="etapas-t"><div class="sec-head"><h2 id="etapas-t">En qué etapa estamos</h2></div>'
            f'<ul class="etapas">{filas}</ul></section>')

