"""Genera ../site/index.html (Resumen) y ../site/zona.html (Tu zona) en cada corrida del pipeline.

Uso: python render_site.py            -> regenera con lo que hay en data/ y en historico/data/resultados/
     desde verify.py: render_site(pts)

Fuentes de las cifras:
  - Consolidadas (lo que se presenta como resultado): historico/data/resultados/*.csv, año 2026, pronóstico a 24 h,
    error sin corregir y corregido por estación (corrección aprendida solo con 2025).
  - Últimos días (siempre rotulado "preliminar" hasta juntar 30 días): data/verif_puntos.csv de este pipeline.
  - Lluvia en milímetros: data/verif_lluvia.csv (lluvia.py), pronóstico de 24 h frente a la estación SYNOP de la DMC
    en cada aeródromo; preliminar hasta juntar 30 días.
  - Quebradas hoy: site/quebradas/indicador.json + cuencas.geojson.
Diseño: docs/brief_sitio.md. Lenguaje de aviso/indicador, nunca "alerta"."""
import json, math, os, re
import pandas as pd
import aviso_oficial
import cambio
from comun import (CSS_ETAPAS, CSS_NAV, CSS_DEF, JS_DEF, etapas, EVENTOS, GLOSARIO, MESES, a_chile, aviso, d, entero, fecha, hora_chile, nav, num, pie, signo)

AQUI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(AQUI, "..", "site")
CONTORNO = os.path.join(AQUI, "..", "docs", "chile_natural_earth_10m.json")
NARRATIVA = os.path.join(AQUI, "..", "docs", "narrativa_sitio.md")
RES = os.path.join(AQUI, "..", "historico", "data", "resultados")
HIST_INFO = os.path.join(AQUI, "..", "historico", "estaciones.csv")
QUEB = os.path.join(SITE, "quebradas")

# Nombre corto y región de cada aeródromo (el METAR trae nombres en inglés y con abreviaturas).
ESTACIONES = {
    "SCAR": ("Arica", "Arica y Parinacota"), "SCDA": ("Iquique", "Tarapacá"), "SCCF": ("Calama", "Antofagasta"),
    "SCFA": ("Antofagasta", "Antofagasta"), "SCAT": ("Caldera", "Atacama"), "SCSE": ("La Serena", "Coquimbo"),
    "SCER": ("Quintero", "Valparaíso"), "SCSN": ("Santo Domingo", "Valparaíso"), "SCEL": ("Santiago (Pudahuel)", "Metropolitana"),
    "SCTB": ("Tobalaba (Las Condes)", "Metropolitana"),
    "SCIC": ("Curicó", "Maule"), "SCCH": ("Chillán", "Ñuble"), "SCIE": ("Concepción", "Biobío"), "SCGE": ("Los Ángeles", "Biobío"),
    "SCTC": ("Temuco (Maquehue)", "La Araucanía"), "SCQP": ("Temuco (La Araucanía)", "La Araucanía"), "SCPC": ("Pucón", "La Araucanía"),
    "SCVD": ("Valdivia", "Los Ríos"), "SCJO": ("Osorno", "Los Lagos"), "SCTE": ("Puerto Montt", "Los Lagos"),
    "SCAS": ("Puerto Aysén", "Aysén"), "SCCY": ("Coyhaique", "Aysén"), "SCBA": ("Balmaceda", "Aysén"),
    "SCNT": ("Puerto Natales", "Magallanes"), "SCCI": ("Punta Arenas", "Magallanes"), "SCRM": ("Base Frei (Antártica)", "Antártica"),
}

# Modelos comparados, en orden de presentación. (nombre corto, tipo, centro)
MODELOS = {"AIFS": ("AIFS", "Inteligencia artificial", "ECMWF"), "IFS": ("IFS", "Modelo físico", "ECMWF"), "GFS": ("GFS", "Modelo físico", "NOAA")}
ORDEN = list(MODELOS)

# Una sola escala para todo el sitio (tarjetas, mapa, tablas y leyenda). Error medio de temperatura en °C.
UMBRAL_T = (1.5, 3.0)
UMBRAL_W = (1.5, 3.0)
MIN_PARES = 30              # bajo esto, una cifra por estación no se publica
DIAS_CONSOLIDADO = 30       # el bloque de "últimos días" deja de ser preliminar al cumplir esto
NIVELES = {"bueno": "Bueno", "medio": "Aceptable", "alto": "Alto"}

# Regla del indicador de quebradas (misma que quebradas/indicador.py), para calcular umbrales aquí.
B0, B1, B2, B3, KF = -3.63, 0.41, 0.67, 0.70, 0.25


def nivel(v, umbral=UMBRAL_T):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "sin"
    return "bueno" if v < umbral[0] else "medio" if v < umbral[1] else "alto"


def nombre(icao, fallback=""):
    if icao in ESTACIONES:
        return ESTACIONES[icao]
    n = str(fallback or icao).split(",")[0].replace(" Arpt", "").replace(" Intl", "")
    return (n, "")


def chip(nv):
    if nv == "sin":
        return '<span class="chip sin">Sin datos</span>'
    if nv == "prelim":
        return '<span class="chip prelim">Preliminar</span>'
    return f'<span class="chip {nv}"><i aria-hidden="true"></i>{NIVELES[nv]}</span>'


def barra(v, vmax, nv):
    pct = 0 if v is None or (isinstance(v, float) and math.isnan(v)) else max(2, min(100, 100 * v / vmax))
    return f'<span class="bar {nv}" aria-hidden="true"><i style="width:{pct:.0f}%"></i></span>'


def etiqueta_modelo(m):
    corto, tipo, centro = MODELOS[m]
    return f"{corto} ({'IA' if m == 'AIFS' else 'físico'}, {centro})"


def narrativa():
    """docs/narrativa_sitio.md -> (html, aviso_final). Es la fuente de verdad del mensaje de fondo."""
    try:
        texto = open(NARRATIVA, encoding="utf-8").read()
    except Exception:
        return "", ""
    if "\n---\n" in texto:
        texto = texto.split("\n---\n", 1)[1]
    inline = lambda t: re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t.strip())
    bloques, aviso_final, lista = [], "", []

    def cierra_lista():
        nonlocal lista
        if lista:
            bloques.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in lista) + "</ol>"); lista = []
    for parrafo in re.split(r"\n\s*\n", texto.strip()):
        parrafo = parrafo.strip()
        if not parrafo:
            continue
        if parrafo.startswith("## "):
            cierra_lista(); bloques.append(f"<h3>{inline(parrafo[3:])}</h3>")
        elif re.match(r"^\d+\.\s", parrafo):
            for linea in re.split(r"\n(?=\d+\.\s)", parrafo):
                lista.append(re.sub(r"^\d+\.\s+", "", linea.strip()))
        elif parrafo.startswith("*") and parrafo.endswith("*") and not parrafo.startswith("**"):
            cierra_lista(); aviso_final = inline(parrafo.strip("*"))
        else:
            cierra_lista(); bloques.append(f"<p>{inline(' '.join(parrafo.splitlines()))}</p>")
    cierra_lista()
    return "".join(bloques), aviso_final


# ---------- datos consolidados ----------
def leer(nombre_csv):
    try:
        return pd.read_csv(os.path.join(RES, nombre_csv))
    except Exception:
        return pd.DataFrame()


def datos_estaciones():
    """Por aeródromo y modelo: error medio a 24 h en 2026 sin corregir (g) y corregido (c), comparaciones (n) y sesgo
    del período 2025-2026 (s). Solo celdas con al menos MIN_PARES comparaciones. Ordenado de norte a sur."""
    ce, es = leer("correccion_estaciones.csv"), leer("estaciones.csv")
    try:
        info = pd.read_csv(HIST_INFO)
    except Exception:
        return []
    if ce.empty:
        return []
    ce, es = ce[ce.lead_h == 24], (es[es.lead_h == 24] if not es.empty else es)
    out = []
    for r in info.itertuples(index=False):
        m = {}
        for mod in ORDEN:
            x = ce[(ce.modelo == mod) & (ce.icao == r.icao)]
            if x.empty or int(x.n.iloc[0]) < MIN_PARES:
                continue
            s = es[(es.modelo == mod) & (es.icao == r.icao)] if not es.empty else es
            m[mod] = {"g": round(float(x.mae_global.iloc[0]), 2), "c": round(float(x.mae_corregido.iloc[0]), 2),
                      "n": int(x.n.iloc[0]), "s": round(float(s.sesgo.iloc[0]), 2) if len(s) else None}
        if not m:
            continue
        for mod in m:
            m[mod].update(cambio.por_estacion(r.icao, mod))
        corto, region = nombre(r.icao, r.nombre)
        out.append({"icao": r.icao, "nombre": corto, "region": region, "elev": None if pd.isna(r.elev) else int(float(r.elev)),
                    "lat": float(r.lat), "lon": float(r.lon), "m": m})
    return sorted(out, key=lambda e: -e["lat"])


def cifras_portada(est):
    """Las tres cifras del Resumen, todas consolidadas (2026, 24 h)."""
    cp = leer("correccion_plazos.csv")
    out = {}
    if not cp.empty:
        c24 = cp[cp.lead_h == 24].set_index("modelo")
        if "AIFS" in c24.index:
            out["aifs_g"], out["aifs_c"], out["aifs_n"] = float(c24.loc["AIFS", "mae_global"]), float(c24.loc["AIFS", "mae_corregido"]), int(c24.loc["AIFS", "n"])
        mejoras = {m: 100 * (1 - c24.loc[m, "mae_corregido"] / c24.loc[m, "mae_global"]) for m in ORDEN if m in c24.index}
        if mejoras:
            out["mejora_min"], out["mejora_max"] = min(mejoras.values()), max(mejoras.values())
            out["mejoras"] = mejoras
            out["g"] = {m: float(c24.loc[m, "mae_global"]) for m in mejoras}
    # ejemplo: el aeródromo donde la corrección más reduce el error de AIFS
    cands = [e for e in est if "AIFS" in e["m"]]
    if cands:
        ej = max(cands, key=lambda e: e["m"]["AIFS"]["g"] - e["m"]["AIFS"]["c"])
        out["ejemplo"] = ej
    return out


def eventos_destacado():
    """La frase de la puerta 'Eventos': el evento con más casos de lluvia y lo que marcó AIFS 72 h antes."""
    er = leer("eventos_resumen.csv")
    if er.empty:
        return None
    x = er[(er.modelo == "AIFS") & (er.lead_h == 72)].copy()
    x["con_lluvia"] = x.aciertos + x.fallas
    x = x[x.con_lluvia > 0]
    if x.empty:
        return None
    r = x.sort_values("con_lluvia", ascending=False).iloc[0]
    return {"evento": r.evento, "aciertos": int(r.aciertos), "total": int(r.con_lluvia)}


def quebradas_hoy():
    """Resumen del indicador de quebradas: niveles de las cuencas con quema relevante, lluvia prevista y umbrales."""
    try:
        ind = json.load(open(os.path.join(QUEB, "indicador.json"), encoding="utf-8"))
        cu = {f["properties"]["id"]: f["properties"] for f in json.load(open(os.path.join(QUEB, "cuencas.geojson"), encoding="utf-8"))["features"]}
    except Exception:
        return None
    prop_min = (ind.get("parametros") or {}).get("prop_min", 0.01)
    factor = ind.get("factor_antecedente", 1.0) or 1.0
    quemadas = []
    for c in ind.get("cuencas", []):
        p = cu.get(c["id"], {})
        if (p.get("prop_hm23") or 0) < prop_min:
            continue
        coef = B1 * p["prop_hm23"] + B2 * (p.get("dnbr_medio") or 0) + B3 * KF
        mm_at = (math.log(0.2 / 0.8) - B0) / coef * 2 / factor
        quemadas.append({"nombre": c["nombre"], "nivel": c["nivel"] if c["nivel"] != "sin_quema" else "bajo", "mm_atencion": mm_at})
    cuenta = {k: sum(1 for q in quemadas if q["nivel"] == k) for k in ("bajo", "atencion", "aviso")}
    mas_cerca = min(quemadas, key=lambda q: q["mm_atencion"]) if quemadas else None
    return {"generado": ind.get("generado"), "mm6": ind.get("mm6", 0), "mm24": ind.get("mm24", 0), "cuenta": cuenta,
            "n_quemadas": len(quemadas), "n_total": len(ind.get("cuencas", [])), "mas_cerca": mas_cerca}


def datos_lluvia(est):
    """Lluvia de 24 h pronosticada frente a la medida (lluvia.py): totales por modelo y, en cada aeródromo de est, su
    estación, sus cuentas por modelo y los últimos días (e["ll"]). None si todavía no hay comparaciones."""
    try:
        import lluvia
        v, par = lluvia.dias(), lluvia.parejas()
    except Exception as e:
        print("AVISO: sin lluvia medida:", type(e).__name__, e)
        return None
    v = v[v.modelo.isin(ORDEN)] if not v.empty else v
    if v.empty:
        return None
    hora = f"{a_chile(v.valid.iloc[0]):%H:%M}".lstrip("0")
    for e in est:
        p, g = par.get(e["icao"]), v[v.icao == e["icao"]]
        if not p or g.empty:
            continue
        donde = "en el mismo aeródromo" if p["km"] < 2 else f"de {p['estacion']}, a {num(p['km'], 1)} km"
        tabla = g.pivot_table(index="valid", values="mm_fc", columns="modelo").join(g.groupby("valid").mm_obs.first()).sort_index().tail(7)
        dias = [{"f": f"{a_chile(t).day} {MESES[a_chile(t).month - 1]}", "o": float(r.mm_obs),
                 "p": {m: float(r[m]) for m in ORDEN if m in r and not pd.isna(r[m])}} for t, r in tabla.iterrows()]
        e["ll"] = {"donde": donde, "m": {m: lluvia.cuentas(x) for m, x in g.groupby("modelo")}, "dias": dias[::-1]}
    n_dias = (v.valid.max() - v.valid.min()).days + 1
    return {"tot": {m: lluvia.cuentas(v[v.modelo == m]) for m in ORDEN if (v.modelo == m).any()}, "desde": v.valid.min(),
            "n_dias": n_dias, "n_est": v.icao.nunique(), "hora": hora, "umbral": lluvia.UMBRAL}


DIA_AERO = d("días-aeródromo", definicion="Cada día en cada aeródromo cuenta una vez: 15 días en 20 aeródromos son 300 días-aeródromo.")


def seccion_lluvia(ll):
    """Resumen: la lluvia en milímetros, por modelo. Preliminar hasta DIAS_CONSOLIDADO días."""
    if not ll:
        return ""
    tot = ll["tot"]
    tarjetas = "".join(
        f'<div class="modelo"><div class="tipo">{MODELOS[m][1]} · {MODELOS[m][2]}</div><div class="nombre">{m}</div>'
        f'<div class="value">{c["avisados"]}<small>de {c["llovio"]}</small></div><div class="que">días con lluvia avisados el día anterior</div>'
        f'<div class="foot">Acertó si llovería o no en {num(100 * c["aciertos"] / c["n"], 0)} % de {entero(c["n"])} {DIA_AERO}; '
        f'{c["falsas"]} {"falsa alarma" if c["falsas"] == 1 else "falsas alarmas"}. Error medio {num(c["mae"], 1)} mm por día'
        f'{f""", {num(c["mae_lluvia"], 1)} mm los días con lluvia""" if c["mae_lluvia"] is not None else ""}.</div></div>'
        for m, c in tot.items())
    mas = [m for m, c in tot.items() if c["medido"] > 0 and c["pronosticado"] > 1.2 * c["medido"]]
    medido = max(c["medido"] for c in tot.values())
    frase = ""
    if medido > 0:
        partes = ", ".join(f'{m} {entero(c["pronosticado"])} mm' for m, c in tot.items())
        frase = (f'<p class="small">Sumando todos los días y aeródromos cayeron {entero(medido)} mm; los modelos pronosticaron {partes}. '
                 + ("Los tres anunciaron más lluvia de la que cayó." if len(mas) == len(tot) else "") + "</p>")
    prelim = ll["n_dias"] < DIAS_CONSOLIDADO
    rotulo = (f'{chip("prelim")} {ll["n_dias"]} días de datos; se consolida al cumplir {DIAS_CONSOLIDADO} días.' if prelim
              else f'{ll["n_dias"]} días de datos.')
    return f"""<section class="card" id="lluvia">
  <div class="sec-head"><h2>Y la lluvia, en milímetros</h2>
  <p class="muted small">Los aeródromos no informan milímetros. Desde el {fecha(ll["desde"])}, comparamos la lluvia de 24 horas que pronosticó cada modelo el día anterior con lo que midió el pluviómetro de la {d("DMC", definicion="Dirección Meteorológica de Chile. Sus estaciones automáticas envían cada hora la lluvia de la última hora a la red de la Organización Meteorológica Mundial.")} en {ll["n_est"]} aeródromos. Cada día va de las {ll["hora"]} a las {ll["hora"]} (hora de Chile) y cuenta como día con lluvia desde {num(ll["umbral"], 0)} mm.</p></div>
  <div class="prelim-bloque"><p class="small">{rotulo}</p><div class="modelos">{tarjetas}</div>{frase}</div>
  <p class="small"><a href="zona.html">Ver la lluvia en tu zona →</a> · <a href="metodo.html#lluvia-mm">Cómo se compara</a></p>
</section>"""


# ---------- mapa de aeródromos (SVG en tres franjas, coloreado con JavaScript) ----------
K = 20.0            # px por grado de latitud
LAT_TOP = -17.0
CX = 0.80           # cos(37°): compresión de la longitud a la latitud media de Chile
FRANJAS = [("Norte", -17.3, -30.6, -71.9, -66.9), ("Centro", -30.6, -43.9, -75.0, -68.6), ("Sur", -43.9, -56.2, -76.0, -66.0)]


def proj(lon, lat):
    return (lon + 76.0) * K * CX, (LAT_TOP - lat) * K


def contorno_path():
    try:
        anillos = json.load(open(CONTORNO))
    except Exception:
        return ""
    partes = []
    for anillo in anillos:
        if len(anillo) < 5:
            continue
        partes.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (proj(lon, lat) for lon, lat in anillo)) + "Z")
    return "".join(partes)


def mapa_svg(est):
    """Las tres franjas con un punto por aeródromo. Cada punto es un botón (data-icao); el color lo pone el JS."""
    path = contorno_path()
    if not path:
        return ""
    figs = []
    for titulo, la0, la1, lo0, lo1 in FRANJAS:
        x0, y0 = proj(lo0, la0); x1, y1 = proj(lo1, la1)
        w, h = x1 - x0, y1 - y0
        pts = []
        for e in est:
            if not (la1 <= e["lat"] <= la0 and lo0 <= e["lon"] <= lo1):
                continue
            x, y = proj(e["lon"], e["lat"])
            etq = e["nombre"].split(" (")[0]
            # la etiqueta va a la derecha del punto; si no cabe antes del borde de la franja, a la izquierda
            cabe = (x1 - x) > 8 * len(etq) + 12
            tx, ancla = (x + 9, "start") if cabe else (x - 9, "end")
            pts.append(f'<g class="est sin" data-icao="{e["icao"]}" tabindex="0" role="button" aria-label="{e["nombre"]}">'
                       f'<title>{e["nombre"]}</title><circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="11"/>'
                       f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="5"/>'
                       f'<text class="etq" x="{tx:.1f}" y="{y + 4:.1f}" text-anchor="{ancla}">{etq}</text></g>')
        figs.append(f'<figure class="franja"><svg viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" '
                    f'role="group" aria-label="Zona {titulo.lower()}"><use href="#chile" class="tierra"/>{"".join(pts)}</svg>'
                    f'<figcaption>{titulo}</figcaption></figure>')
    return (f'<svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs><path id="chile" d="{path}"/></defs></svg>'
            f'<div class="mapa">{"".join(figs)}</div>')


def leyenda():
    return (f'<div class="leyenda"><span class="item">{chip("bueno")} menos de {num(UMBRAL_T[0])} °C</span>'
            f'<span class="item">{chip("medio")} {num(UMBRAL_T[0])} a {num(UMBRAL_T[1])} °C</span>'
            f'<span class="item">{chip("alto")} {num(UMBRAL_T[1])} °C o más</span></div>')


# JavaScript del mapa y la ficha, común a Resumen y Tu zona. Recibe los datos en window.ZONA.
JS_MAPA = r"""
<script>
(function(){
  const Z = window.ZONA, E = Z.est, porId = {};
  E.forEach(e => porId[e.icao] = e);
  const st = { modelo: Z.modelo || 'AIFS', estado: 'g', sel: null };
  const fmt = (v, d=1) => v == null ? '–' : Number(v).toLocaleString('es-CL', {minimumFractionDigits:d, maximumFractionDigits:d}).replace('-', '−');
  const niv = v => v == null ? 'sin' : v < 1.5 ? 'bueno' : v < 3 ? 'medio' : 'alto';
  const NIV = {bueno:'Bueno', medio:'Aceptable', alto:'Alto', sin:'Sin datos'};
  const chip = n => `<span class="chip ${n}"><i aria-hidden="true"></i>${NIV[n]}</span>`;
  const val = (e, est) => { const x = e.m[st.modelo]; return x ? x[est || st.estado] : null; };
  const MOD = {AIFS:'la IA de ECMWF (AIFS)', IFS:'el modelo físico de ECMWF (IFS)', GFS:'el modelo físico de NOAA (GFS)'};

  function pintar(){
    const peores = E.filter(e => val(e) != null).sort((a,b) => val(b) - val(a)).slice(0, 3).map(e => e.icao);
    document.querySelectorAll('.est').forEach(g => {
      const e = porId[g.dataset.icao]; if (!e) return;
      const v = val(e), sel = e.icao === st.sel;
      g.setAttribute('class', 'est ' + niv(v) + (sel ? ' sel' : '') + (sel || peores.includes(e.icao) ? ' con-etq' : ''));
      g.querySelector('title').textContent = e.nombre + ': ' + (v == null ? 'sin datos suficientes' : fmt(v) + ' °C de error medio');
      g.setAttribute('aria-label', e.nombre + ', ' + (v == null ? 'sin datos' : fmt(v) + ' grados de error medio'));
    });
    if (Z.ficha) { ficha(); tabla(); }
    document.querySelectorAll('[data-estado-txt]').forEach(el => el.textContent = st.estado === 'g' ? 'sin corregir' : 'corregido por estación');
  }

  function ficha(){
    const box = document.getElementById('ficha'); const e = porId[st.sel]; if (!box || !e) return;
    const x = e.m[st.modelo];
    let cuerpo;
    if (!x) cuerpo = `<p class="muted">Sin datos suficientes de ${st.modelo} en este aeródromo.</p>`;
    else {
      const mej = 100 * (1 - x.c / x.g);
      const frase_c = x.c < x.g ? `Con la corrección por estación queda en <strong>${fmt(x.c)} °C</strong>: ${fmt(mej, 0)} % menos.`
                                : `Aquí la corrección no ayuda: queda en ${fmt(x.c)} °C.`;
      const sesgo = (x.s != null && Math.abs(x.s) >= 0.5) ? ` Tiende a pronosticar ${fmt(Math.abs(x.s))} °C más ${x.s < 0 ? 'frío' : 'calor'} de lo que ocurre.` : '';
      cuerpo = `<div class="antes-despues"><div><span class="lbl">Sin corregir</span><span class="v">${fmt(x.g)}<small>°C</small></span>${chip(niv(x.g))}</div>
        <span class="flecha" aria-hidden="true">→</span>
        <div><span class="lbl">Corregido</span><span class="v">${fmt(x.c)}<small>°C</small></span>${chip(niv(x.c))}</div></div>
        <p>En ${e.nombre}, ${MOD[st.modelo]} se equivoca en promedio <strong>${fmt(x.g)} °C</strong> al pronosticar la temperatura de mañana. ${frase_c}${sesgo}</p>`;
    }
    const filas = ['AIFS','IFS','GFS'].map(m => { const y = e.m[m]; return `<tr${m === st.modelo ? ' class="actual"' : ''}><td class="l">${m}</td><td class="num">${y ? fmt(y.g) + ' °C' : '–'}</td><td class="num">${y ? fmt(y.c) + ' °C' : '–'}</td></tr>`; }).join('');
    const n = x ? x.n : 0;
    box.innerHTML = `<div class="ficha-cab"><h2>${e.nombre}</h2><p class="muted small">${e.region}${e.elev != null ? ' · ' + e.elev.toLocaleString('es-CL') + ' m de altura' : ''}</p></div>
      ${cuerpo}
      ${x && x.movil != null ? `<p class="small">Corregir con los últimos 45 días en vez de 2025: ${fmt(x.movil)} °C frente a ${fmt(x.fija)} °C. ${x.gana === 'móvil' ? 'Aquí gana la corrección móvil.' : x.gana === 'fija' ? 'Aquí gana la corrección de 2025.' : 'Aquí dan casi lo mismo.'}</p>` : ''}
      ${x && x.deriva != null ? `<p class="small"><span class="chip medio"><i></i>En deriva</span> En los últimos 30 días, este modelo pronosticó aquí ${fmt(Math.abs(x.deriva))} °C más ${x.deriva < 0 ? 'frío' : 'calor'} de lo que corresponde a su error de 2025.</p>` : ''}
      ${x && x.viento != null ? `<p class="small">Viento: ${MOD[st.modelo]} se equivoca en promedio ${fmt(x.viento, 0)} km/h en la velocidad de mañana${Math.abs(x.viento_sesgo) >= 3 ? (x.viento_sesgo > 0 ? ', y tiende a pronosticar más viento del que hay' : ', y tiende a pronosticar menos viento del que hay') : ''}${x.rafaga != null ? `; en las ráfagas, ${fmt(x.rafaga, 0)} km/h` : (st.modelo === 'AIFS' ? '; AIFS no pronostica ráfagas' : '')}.</p>` : ''}
      <table class="mini"><thead><tr><th class="l">Modelo</th><th>Sin corregir</th><th>Corregido</th></tr></thead><tbody>${filas}</tbody></table>
      <p class="muted small">Error medio de la temperatura pronosticada con 24 h de anticipación, ${n.toLocaleString('es-CL')} comparaciones en 2026. <a href="#${e.icao}">Enlace a esta estación</a></p>
      ${lluvia(e)}`;
  }

  function lluvia(e){
    const L = Z.lluvia; if (!L) return '';
    if (!e.ll) return `<h3>Lluvia</h3><p class="small muted">Este aeródromo no tiene un pluviómetro de la DMC a menos de 15 km y a una altura parecida.</p>`;
    const c = e.ll.m[st.modelo];
    const dias = n => n === 1 ? '1 día' : n + ' días', cap = t => t[0].toUpperCase() + t.slice(1);
    const txt = !c ? `<p class="muted small">Sin comparaciones de lluvia de ${st.modelo} en este aeródromo.</p>` :
      `<p class="small">Desde el ${L.desde}, el pluviómetro de la DMC ${e.ll.donde}${e.ll.donde.startsWith('en ') ? '' : ','} midió ${L.umbral} mm o más en <strong>${c.llovio} de ${dias(c.n)}</strong>.
       ${c.llovio ? `${cap(MOD[st.modelo])} avisó la lluvia el día anterior ${c.avisados === c.llovio ? (c.llovio === 1 ? 'ese día' : 'en los ' + c.llovio) : (c.avisados === 0 ? 'en ninguno' : 'en ' + c.avisados + (c.llovio === 1 ? '' : ' de esos ' + c.llovio))}` : `${cap(MOD[st.modelo])} no tenía lluvia que avisar`}${c.falsas ? `${c.llovio ? ', y' : ', pero'} anunció lluvia que no cayó en ${dias(c.falsas)}` : ''}.
       Se equivocó en promedio ${fmt(c.mae)} mm por día${c.mae_lluvia != null ? ` (${fmt(c.mae_lluvia)} mm los días con lluvia)` : ''}.</p>`;
    const mm = v => v == null ? '–' : fmt(v);
    const filas = e.ll.dias.map(x => `<tr><td class="l">${x.f}</td><td class="num${x.o >= L.umbral ? ' mejor' : ''}">${mm(x.o)}</td>${['AIFS','IFS','GFS'].map(m => `<td class="num${m === st.modelo ? ' sel' : ''}">${mm(x.p[m])}</td>`).join('')}</tr>`).join('');
    return `<h3>Lluvia</h3>${txt}
      <table class="mini"><thead><tr><th class="l">Día</th><th>Medido</th><th>AIFS</th><th>IFS</th><th>GFS</th></tr></thead><tbody>${filas}</tbody></table>
      <p class="muted small">Milímetros en 24 h hasta las ${L.hora} de cada día, últimos días con datos. Pronóstico hecho el día anterior.</p>`;
  }

  function tabla(){
    const tb = document.querySelector('#tabla-est tbody'); if (!tb) return;
    const filas = E.filter(e => e.m[st.modelo]).sort((a,b) => val(b,'g') - val(a,'g'));
    tb.innerHTML = filas.map(e => { const x = e.m[st.modelo], mej = 100 * (1 - x.c / x.g);
      return `<tr data-icao="${e.icao}" tabindex="0"${e.icao === st.sel ? ' class="actual"' : ''}><td class="l">${e.nombre}<span class="region">${e.region}</span></td>
        <td class="num">${fmt(x.g)} °C</td><td class="num">${fmt(x.c)} °C</td><td class="num">${x.c < x.g ? '−' + fmt(mej, 0) : '+' + fmt(-mej, 0)} %</td><td>${chip(niv(val(e)))}</td></tr>`; }).join('');
    const cab = document.getElementById('tabla-modelo'); if (cab) cab.textContent = st.modelo;
    const tl = document.querySelector('#tabla-lluvia tbody'); if (!tl) return;
    tl.innerHTML = E.filter(e => e.ll && e.ll.m[st.modelo]).map(e => { const c = e.ll.m[st.modelo];
      return `<tr data-icao="${e.icao}"${e.icao === st.sel ? ' class="actual"' : ''}><td class="l">${e.nombre}<span class="region">Pluviómetro ${e.ll.donde.replace('en el mismo aeródromo', 'en el aeródromo')}</span></td>
        <td class="num">${c.n}</td><td class="num">${c.llovio}</td><td class="num">${c.llovio ? c.avisados : '–'}</td><td class="num">${c.falsas}</td><td class="num">${fmt(c.mae)} mm</td></tr>`; }).join('');
    document.querySelectorAll('[data-modelo-txt]').forEach(el => el.textContent = st.modelo);
  }

  function elegir(icao, desplazar){
    if (!porId[icao]) return;
    if (Z.navegar) { location.href = 'zona.html#' + icao; return; }
    st.sel = icao; pintar();
    const s = document.getElementById('estacion'); if (s) s.value = icao;
    if (location.hash.slice(1) !== icao) history.replaceState(null, '', '#' + icao);
    if (desplazar) document.getElementById('ficha').scrollIntoView({behavior:'smooth', block:'nearest'});
  }

  document.addEventListener('click', ev => {
    const g = ev.target.closest('.est'); if (g) { elegir(g.dataset.icao, true); return; }
    const tr = ev.target.closest('#tabla-est tr[data-icao], #tabla-lluvia tr[data-icao]'); if (tr) elegir(tr.dataset.icao, true);
  });
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    const g = ev.target.closest && (ev.target.closest('.est') || ev.target.closest('#tabla-est tr[data-icao]'));
    if (g) { ev.preventDefault(); elegir(g.dataset.icao, true); }
  });
  document.querySelectorAll('input[name="modelo"]').forEach(i => i.addEventListener('change', () => { st.modelo = i.value; pintar(); }));
  document.querySelectorAll('input[name="estado"]').forEach(i => i.addEventListener('change', () => { st.estado = i.value; pintar(); }));
  const s = document.getElementById('estacion'); if (s) s.addEventListener('change', () => elegir(s.value, false));
  window.addEventListener('hashchange', () => elegir(location.hash.slice(1), false));

  const h = location.hash.slice(1);
  st.sel = porId[h] ? h : (Z.inicial || (E[0] && E[0].icao));
  if (s) s.value = st.sel;
  pintar();
})();
</script>
"""


# ---------- estilos ----------
CSS = """
/* Una columna de 1080 px; lo consolidado antes que lo preliminar; cada número con su explicación al lado.
   Neutros fríos con leve sesgo azul (cielo y hielo), acento verde glaciar; semáforo fijo y siempre con texto. */
:root{
  --bg:#f4f6f8; --surface:#ffffff; --fg:#17212b; --muted:#5a6977; --line:#d8dfe6; --line-soft:#e9eef2;
  --accent:#0e7c86; --accent-soft:#d7eef0; --tierra:#e3e9ee; --costa:#9fb0bd;
  --bueno:#0ca30c; --medio:#c98500; --alto:#d03b3b; --sin:#8a99a6;
  --font-display:"Sora",system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-body:"Source Sans 3","Source Sans Pro",system-ui,-apple-system,"Segoe UI",sans-serif;
  --font-data:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --radius:10px; color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#111821; --surface:#19222c; --fg:#e7ecf1; --muted:#9fadba; --line:#2c3845; --line-soft:#232e3a;
  --accent:#44bcc6; --accent-soft:#163b40; --tierra:#243040; --costa:#4f6071;
  --bueno:#2fbf2f; --medio:#e0a428; --alto:#ee6a6a; --sin:#7d8c99; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#111821; --surface:#19222c; --fg:#e7ecf1; --muted:#9fadba; --line:#2c3845; --line-soft:#232e3a;
  --accent:#44bcc6; --accent-soft:#163b40; --tierra:#243040; --costa:#4f6071;
  --bueno:#2fbf2f; --medio:#e0a428; --alto:#ee6a6a; --sin:#7d8c99; color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--fg);font-family:var(--font-body);font-size:17px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible,button:focus-visible,summary:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}
.wrap{max-width:1080px;margin:0 auto;padding-inline:16px;padding-block:24px 56px;display:grid;gap:32px}
@media (min-width:720px){.wrap{padding-inline:28px;padding-block:40px 72px;gap:44px}}
h1,h2,h3{font-family:var(--font-display);text-wrap:balance;margin:0;letter-spacing:-.01em}
h1{font-size:clamp(26px,3.8vw,40px);line-height:1.15;font-weight:600;max-width:26ch}
h2{font-size:22px;font-weight:600}
h3{font-size:17px;font-weight:600}
p{margin:0;max-width:65ch}
.eyebrow{font-family:var(--font-display);font-size:12px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-weight:600}
.muted{color:var(--muted)}
.small{font-size:14.5px}
header{display:grid;gap:12px}
header .lead{font-size:19px;color:var(--muted);max-width:60ch}
.aviso{border-left:3px solid var(--accent);padding:10px 14px;background:var(--accent-soft);border-radius:0 var(--radius) var(--radius) 0;max-width:72ch}
.aviso p{max-width:none}
section{display:grid;gap:14px}
.sec-head{display:grid;gap:6px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px;display:grid;gap:12px;min-width:0}
/* cifras de la portada */
.cifras{display:grid;gap:12px;grid-template-columns:1fr}
@media (min-width:760px){.cifras{grid-template-columns:repeat(3,minmax(0,1fr))}}
.cifra{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:18px;display:grid;gap:6px;align-content:start}
.cifra .v{font-family:var(--font-display);font-size:42px;font-weight:600;line-height:1.05;letter-spacing:-.02em}
.cifra .v small{font-size:18px;font-weight:500;color:var(--muted);margin-left:3px}
.cifra .v .flecha{color:var(--muted);font-weight:400;margin:0 6px}
.cifra p{font-size:15.5px}
.cifra.principal{border-color:var(--accent)}
/* puertas de entrada */
.puertas{display:grid;gap:12px;grid-template-columns:1fr}
@media (min-width:760px){.puertas{grid-template-columns:repeat(3,minmax(0,1fr))}}
.puerta{display:grid;gap:6px;align-content:start;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;color:var(--fg);text-decoration:none}
.puerta:hover{border-color:var(--accent)}
.puerta .q{font-family:var(--font-display);font-weight:600;font-size:18px}
.puerta .ir{color:var(--accent);font-weight:600;font-size:15px}
.puerta p{font-size:15.5px;color:var(--muted)}
.confianza{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:14.5px;color:var(--muted)}
/* controles */
.controles{display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center}
.selector{display:flex;flex-wrap:wrap;gap:6px;border:0;padding:0;margin:0;align-items:center}
.selector legend{float:left;margin-right:6px;padding:0}
.selector label{position:relative;cursor:pointer;border:1px solid var(--line);border-radius:999px;padding:5px 13px;font-size:14.5px;font-weight:600;background:var(--bg)}
.selector label .muted{font-weight:400;font-size:13px}
.selector input{position:absolute;opacity:0;width:0;height:0;margin:0}
.selector label:has(input:checked){background:var(--accent-soft);border-color:var(--accent)}
.selector label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:2px}
select{font:inherit;font-size:16px;padding:7px 10px;border-radius:8px;border:1px solid var(--line);background:var(--surface);color:var(--fg);max-width:100%}
/* mapa */
.mapa{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:flex-start;justify-content:center}
.franja{margin:0;display:grid;gap:4px;justify-items:center}
.franja svg{max-width:100%;height:auto;display:block;overflow:hidden}
.franja figcaption{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.tierra{fill:var(--tierra);stroke:var(--costa);stroke-width:.6;vector-effect:non-scaling-stroke}
.est{cursor:pointer;outline:none}
.est .hit{fill:transparent}
.est .pt{stroke:var(--surface);stroke-width:2;fill:var(--sin)}
.est.bueno .pt{fill:var(--bueno)} .est.medio .pt{fill:var(--medio)} .est.alto .pt{fill:var(--alto)}
.est .etq{display:none;font:600 10px var(--font-body);fill:var(--fg);paint-order:stroke;stroke:var(--surface);stroke-width:3px;stroke-linejoin:round}
.est.con-etq .etq{display:block}
.est.sel .pt{stroke:var(--fg);stroke-width:2.5;r:7}
.est:focus-visible .pt{stroke:var(--accent);stroke-width:3}
.est:hover .pt{r:7}
.leyenda{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:14px;color:var(--muted);align-items:center}
.leyenda span.item{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;padding:2px 9px 2px 7px;border-radius:999px;border:1px solid var(--line);background:var(--bg);color:var(--fg);white-space:nowrap}
.chip i{width:8px;height:8px;border-radius:50%;background:var(--sin)}
.chip.bueno i{background:var(--bueno)} .chip.medio i{background:var(--medio)} .chip.alto i{background:var(--alto)}
.chip.sin{color:var(--muted)} .chip.prelim{color:var(--muted);border-style:dashed}
/* tu zona */
.zona{display:grid;gap:20px}
@media (min-width:900px){.zona{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);align-items:start}}
.ficha{position:relative}
@media (min-width:900px){.ficha{position:sticky;top:72px}}
.ficha-cab{display:grid;gap:2px}
.antes-despues{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.antes-despues > div{display:grid;gap:2px;justify-items:start}
.antes-despues .lbl{font-size:13px;color:var(--muted)}
.antes-despues .v{font-family:var(--font-display);font-size:34px;font-weight:600;line-height:1.1}
.antes-despues .v small{font-size:16px;font-weight:500;color:var(--muted);margin-left:2px}
.antes-despues .flecha{font-size:24px;color:var(--muted)}
/* tablas */
.tabla{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:15px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line-soft);text-align:right;vertical-align:middle;white-space:nowrap}
th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line)}
th.l,td.l{text-align:left}
td.num{font-family:var(--font-data);font-size:14px;font-variant-numeric:tabular-nums}
td .region{display:block;font-size:13px;color:var(--muted)}
tr.actual td{background:var(--accent-soft)}
#tabla-est tbody tr,#tabla-lluvia tbody tr{cursor:pointer}
#tabla-est tbody tr:hover td,#tabla-lluvia tbody tr:hover td{background:color-mix(in srgb,var(--accent) 8%,transparent)}
.ficha h3{margin-top:6px}
table.mini td.sel{background:var(--accent-soft)}
.modelo .que{font-size:14.5px;margin-bottom:4px}
table.mini{font-size:14.5px} table.mini th,table.mini td{padding:6px 8px}
td.medida{min-width:9.5em}
.medida-in{display:inline-grid;grid-template-columns:72px auto;gap:8px;align-items:center;justify-items:end}
.bar{display:block;width:72px;height:8px;border-radius:4px;background:var(--line-soft);overflow:hidden}
.bar i{display:block;height:100%;border-radius:4px;background:var(--sin)}
.bar.bueno i{background:var(--bueno)} .bar.medio i{background:var(--medio)} .bar.alto i{background:var(--alto)}
td.plazo{font-weight:600;vertical-align:top} tr.sep td{border-top:1px solid var(--line)}
td.modelo-nombre{font-weight:600} td.modelo-nombre .tipo{display:block;font-size:12px;color:var(--muted);font-weight:400}
td.num.mejor{font-weight:700;color:var(--accent)}
/* bloque preliminar */
.prelim-bloque{border:1px dashed var(--line);border-radius:var(--radius);padding:16px;display:grid;gap:12px;background:var(--surface)}
.modelos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
@media (max-width:640px){.modelos{grid-template-columns:1fr}}
.modelo{border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px;display:grid;gap:2px;align-content:start;background:var(--bg)}
.modelo .tipo{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.modelo .nombre{font-family:var(--font-display);font-size:18px;font-weight:600}
.modelo .value{font-family:var(--font-display);font-size:28px;font-weight:600;line-height:1.1}
.modelo .value small{font-size:15px;font-weight:500;color:var(--muted);margin-left:2px}
.modelo .foot{font-size:13px;color:var(--muted)}
/* narrativa y desplegables */
.narrativa{display:grid;gap:12px;max-width:68ch}
.narrativa p{max-width:none}
.narrativa ol{margin:0;padding-left:1.25em;display:grid;gap:8px}
details{border:1px solid var(--line);border-radius:var(--radius);background:var(--surface);padding:0}
summary{cursor:pointer;padding:12px 16px;font-weight:600;font-family:var(--font-display);font-size:15.5px;list-style:none;display:flex;justify-content:space-between;gap:12px}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";color:var(--muted);font-weight:400}
details[open] summary::after{content:"–"}
details .body{padding:0 16px 16px;display:grid;gap:12px}
details .body p{max-width:72ch}
footer{border-top:1px solid var(--line);padding-top:20px;display:grid;gap:8px;font-size:14px;color:var(--muted)}
footer p{max-width:85ch}
@media (max-width:600px){.cifra .v{font-size:36px}}
@media (prefers-reduced-motion:no-preference){.est .pt{transition:r .15s ease}}
"""


def head(titulo, descripcion):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}{CSS_NAV}{CSS_DEF}{CSS_ETAPAS}{aviso_oficial.CSS}{cambio.CSS_CAMBIO}</style>
</head>"""


def escribir(nombre_archivo, html):
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, nombre_archivo), "w", encoding="utf-8") as f:
        f.write(html)
    return len(html) // 1024


# ---------- página: Resumen ----------
def pagina_resumen(est, ahora, ll=None):
    c = cifras_portada(est)
    ev = eventos_destacado()
    q = quebradas_hoy()
    narr_html, narr_aviso = narrativa()
    n_est = len(est)

    tarjetas = []
    if "aifs_g" in c:
        tarjetas.append(f'<div class="cifra principal"><div class="v">{num(c["aifs_g"], 2)}<small>°C</small></div>'
                        f'<p>de {d("error medio")} de la IA de ECMWF ({d("AIFS")}) al pronosticar la temperatura de mañana en '
                        f'{n_est} aeródromos, durante 2026. Los modelos físicos se equivocan más: '
                        f'IFS {num(c["g"].get("IFS"), 2)} °C y GFS {num(c["g"].get("GFS"), 2)} °C.</p></div>')
    if "mejora_min" in c:
        tarjetas.append(f'<div class="cifra"><div class="v">{num(c["mejora_min"], 0)} a {num(c["mejora_max"], 0)}<small>% menos</small></div>'
                        f'<p>de error con la {d("corrección por estación")}: cada aeródromo corrige su error típico, aprendido en 2025 '
                        f'y probado en 2026. Es la primera capa chilena.</p></div>')
    if "ejemplo" in c:
        x = c["ejemplo"]["m"]["AIFS"]
        tarjetas.append(f'<div class="cifra"><div class="v">{num(x["g"], 1)}<span class="flecha">→</span>{num(x["c"], 1)}<small>°C</small></div>'
                        f'<p>{c["ejemplo"]["nombre"]}: el error de la IA antes y después de corregir. Ahí la grilla de {d("25 km")} '
                        f'mezcla mar, costa y cerro en un mismo cuadrado.</p></div>')

    puertas = [f'<a class="puerta" href="zona.html"><span class="q">¿Cuánto se equivoca en tu zona?</span>'
               f'<p>Elige un aeródromo y compara los tres modelos, con y sin corrección.</p><span class="ir">Ver Tu zona →</span></a>']
    if ev:
        corto = EVENTOS.get(ev["evento"], (ev["evento"], ev["evento"]))[1]
        puertas.append(f'<a class="puerta" href="eventos.html#{ev["evento"]}"><span class="q">¿Lo vieron venir?</span>'
                       f'<p>En {corto}, la IA marcó lluvia 72 horas antes en {ev["aciertos"]} de los {ev["total"]} casos en que llovió.</p>'
                       f'<span class="ir">Ver los eventos de 2026 →</span></a>')
    if q:
        k = q["cuenta"]
        estado = (f'{k["aviso"]} en aviso y {k["atencion"]} en atención' if (k["aviso"] or k["atencion"])
                  else "todas en nivel bajo")
        lluvia = "sin lluvia prevista en las próximas 24 horas" if q["mm24"] < 1 else f"{num(q['mm24'], 1)} mm previstos en 24 horas"
        cerca = (f' {q["mas_cerca"]["nombre"].split(" (")[0]} pasaría a atención con unos {num(q["mas_cerca"]["mm_atencion"], 0)} mm en 2 horas.'
                 if q["mas_cerca"] else "")
        puertas.append(f'<a class="puerta" href="quebradas.html"><span class="q">Quebradas de Santiago oriente hoy</span>'
                       f'<p>{q["n_quemadas"]} quebradas con laderas quemadas: {estado}, {lluvia}.{cerca}</p>'
                       f'<span class="ir">Ver el mapa de quebradas →</span></a>')

    datos_js = json.dumps({"est": est, "modelo": "AIFS", "navegar": True, "ficha": False}, ensure_ascii=False)
    html = f"""{head("Earth-2 Chile", "Medimos en público cuánto se equivoca el pronóstico global en Chile y cómo lo corrige una capa chilena. Datos abiertos, actualizados cuatro veces al día.")}
<body>
{nav("resumen")}
<div class="wrap">
{aviso_oficial.html('<p>Para las quebradas quemadas de Santiago oriente, mire también <a href="quebradas.html">cuánta lluvia las acercaría a un umbral</a>.</p>')}

<header>
  <div class="eyebrow">Verificación pública del pronóstico del tiempo en Chile</div>
  <h1>El pronóstico global ve Chile en cuadrados de 25 km. Medimos cuánto se equivoca y cómo corregirlo.</h1>
  <p class="lead">Comparamos los tres mejores modelos globales con lo que de verdad marcan {n_est} aeródromos del país, de Arica a Punta Arenas, y publicamos el resultado aquí, todos los días.</p>
</header>

<section aria-label="Cifras principales">
  <div class="cifras">{''.join(tarjetas)}</div>
</section>

<section class="card">
  <div class="sec-head"><h2>Dónde se equivoca más</h2>
  <p class="muted small">Error medio de la IA (AIFS) al pronosticar la temperatura de mañana, por aeródromo, en 2026. Cambia a "corregido" para ver la primera capa chilena. Toca un punto para ver su detalle.</p></div>
  <div class="controles"><fieldset class="selector"><legend class="eyebrow">Mostrar</legend>
    <label><input type="radio" name="estado" value="g" checked>Sin corregir</label>
    <label><input type="radio" name="estado" value="c">Corregido por estación</label></fieldset></div>
  {mapa_svg(est)}
  {leyenda()}
</section>

{cambio.seccion(est)}

{seccion_lluvia(ll)}

<section aria-label="Explorar">
  <div class="puertas">{''.join(puertas)}</div>
  <p class="confianza"><span>Datos al {hora_chile(ahora)}</span><span>Se actualiza cuatro veces al día</span><span><a href="metodo.html">Cómo se calcula</a></span><span><a href="https://github.com/PanchoDigevo/earth2-chile-verificacion" rel="noopener">Código y datos abiertos</a></span></p>
  {aviso()}
</section>

{etapas()}

{f'''<details><summary>Por qué hacemos esto</summary><div class="body narrativa">{narr_html}</div></details>''' if narr_html else ''}

{pie(ahora)}
</div>
<script>window.ZONA = {datos_js};</script>
{JS_MAPA}
{JS_DEF}
</body>
</html>
"""
    return escribir("index.html", html)


# ---------- página: Tu zona ----------
def bloque_ultimos_dias(pts):
    """Comparación de los tres modelos con los datos del pipeline diario. Preliminar hasta cumplir DIAS_CONSOLIDADO."""
    if pts is None or pts.empty:
        return "", ""
    mae = lambda e: e.abs().mean()
    res = (pts.groupby(["modelo", "lead_h"]).agg(n=("t_err", "size"), t_bias=("t_err", "mean"), t_mae=("t_err", mae),
                                                 w_bias=("w_err", "mean"), w_mae=("w_err", mae)).reset_index().sort_values(["lead_h", "modelo"]))
    presentes = [m for m in ORDEN if m in set(pts.modelo)]
    leads = [set(res[res.modelo == m].lead_h) for m in presentes]
    comunes = set.intersection(*leads) if leads else set()
    lead = 24 if 24 in comunes else (max(comunes) if comunes else None)
    if lead is None:
        return "", ""
    dias = max(1, (pts.valid.max() - pts.valid.min()).days + 1)
    prelim = dias < DIAS_CONSOLIDADO
    cmp = {r.modelo: r for r in res[res.lead_h == lead].itertuples(index=False)}
    tarjetas = "".join(
        f'<div class="modelo"><div class="tipo">{MODELOS[m][1]} · {MODELOS[m][2]}</div><div class="nombre">{m}</div>'
        f'<div class="value">{num(cmp[m].t_mae, 1)}<small>°C</small></div><div class="foot">{entero(cmp[m].n)} comparaciones</div></div>'
        for m in ORDEN if m in cmp)
    rotulo = (f'{chip("prelim")} Se consolida al cumplir {DIAS_CONSOLIDADO} días; mientras tanto, las cifras pueden cambiar bastante.'
              if prelim else "")
    bloque = f"""<section>
  <div class="sec-head"><h2>Últimos {dias} días</h2>
  <p class="muted">Lo mismo, con los pronósticos que el sistema verifica cada día desde el {fecha(pts.valid.min())}: error medio de la temperatura a {lead} h de {d("plazo")}, todas las estaciones juntas.</p></div>
  <div class="prelim-bloque"><p class="small">{rotulo}</p><div class="modelos">{tarjetas}</div></div>
</section>"""

    # tablas técnicas: por plazo y por corrida
    t_max = max(4.0, math.ceil(res.t_mae.max() + 0.01)); w_max = max(4.0, math.ceil(res.w_mae.max() + 0.01))
    filas = []
    for ld, grupo in res.groupby("lead_h", sort=True):
        grupo = grupo.set_index("modelo").reindex([m for m in ORDEN if m in grupo.modelo.values])
        mejor = grupo.t_mae.idxmin() if len(grupo) > 1 else None
        for i, (m, r) in enumerate(grupo.iterrows()):
            nt = nivel(r.t_mae)
            celda = f"<td class='l num plazo' rowspan='{len(grupo)}'>{int(ld)} h</td>" if i == 0 else ""
            filas.append(f"<tr class='{'sep' if i == 0 else ''}'>{celda}<td class='l modelo-nombre'>{m}</td><td class='num'>{entero(r.n)}</td>"
                         f"<td class='medida'><span class='medida-in'>{barra(r.t_mae, t_max, nt)}<span class='num{' mejor' if m == mejor else ''}'>{num(r.t_mae, 2, ' °C')}</span></span></td>"
                         f"<td class='num'>{signo(r.t_bias, 2, ' °C')}</td><td class='num'>{num(r.w_mae, 2, ' m/s')}</td></tr>")
    por_run = pts.pivot_table(index="run", columns="modelo", values="t_err", aggfunc=mae).sort_index().tail(20)
    filas_r = "".join(f"<tr><td class='l num'>{hora_chile(pd.Timestamp(run))}</td>" +
                      "".join(f"<td class='num'>{num(fila.get(m), 2, ' °C')}</td>" for m in presentes) + "</tr>"
                      for run, fila in por_run.iterrows())
    tecnico = f"""<details><summary>Para técnicos: error por plazo y por corrida</summary><div class="body">
  <p class="small muted">Datos del pipeline diario ({entero(len(pts))} comparaciones desde el {fecha(pts.valid.min())}). {d("Sesgo")} negativo: el modelo pronostica más frío de lo observado. Viento a 10 m.</p>
  <div class="tabla"><table><thead><tr><th class="l">Plazo</th><th class="l">Modelo</th><th>Comparaciones</th><th>Error temp.</th><th>Sesgo temp.</th><th>Error viento</th></tr></thead><tbody>{''.join(filas)}</tbody></table></div>
  <p class="small muted">Últimas corridas: error medio de cada una, todos los plazos y estaciones juntos.</p>
  <div class="tabla"><table><thead><tr><th class="l">Corrida</th>{''.join(f'<th>{m}</th>' for m in presentes)}</tr></thead><tbody>{filas_r}</tbody></table></div>
</div></details>"""
    return bloque, tecnico


def lluvia_js(ll):
    return {"desde": fecha(ll["desde"]), "umbral": num(ll["umbral"], 0), "hora": ll["hora"]} if ll else None


def tabla_lluvia(ll):
    """Tu zona: lluvia medida frente a pronosticada en cada aeródromo (la llena el JS según el modelo elegido)."""
    if not ll:
        return ""
    return f"""<section id="lluvia">
  <div class="sec-head"><h2>La lluvia en cada aeródromo</h2>
  <p class="muted">Modelo <strong data-modelo-txt>AIFS</strong>. Desde el {fecha(ll["desde"])}: días comparados, días en que el pluviómetro de la DMC midió {num(ll["umbral"], 0)} mm o más, cuántos de ellos avisó el modelo el día anterior, días en que anunció lluvia que no cayó y su {d("error medio")} en milímetros por día. De norte a sur; toca una fila para ver su ficha.</p></div>
  <div class="prelim-bloque"><p class="small">{chip("prelim") + f" {ll['n_dias']} días de datos; se consolida al cumplir {DIAS_CONSOLIDADO} días." if ll["n_dias"] < DIAS_CONSOLIDADO else f"{ll['n_dias']} días de datos."} Detalle en <a href="metodo.html#lluvia-mm">Método</a>.</p>
  <div class="tabla"><table id="tabla-lluvia"><thead><tr><th class="l">Aeródromo</th><th>Días</th><th>Con lluvia</th><th>Avisados</th><th>Falsas alarmas</th><th>Error medio</th></tr></thead><tbody></tbody></table></div></div>
</section>"""


def pagina_zona(est, pts, ahora, ll=None):
    c = cifras_portada(est)
    inicial = c["ejemplo"]["icao"] if "ejemplo" in c else (est[0]["icao"] if est else "")
    opciones = "".join(f'<option value="{e["icao"]}">{e["nombre"]} · {e["region"]}</option>' for e in est)
    ultimos, tecnico = bloque_ultimos_dias(pts)
    datos_js = json.dumps({"est": est, "modelo": "AIFS", "navegar": False, "ficha": True, "inicial": inicial, "lluvia": lluvia_js(ll)}, ensure_ascii=False)
    html = f"""{head("Tu zona · Earth-2 Chile", "Elige un aeródromo de Chile y mira cuánto se equivocan los modelos de pronóstico al predecir la temperatura de mañana, con y sin corrección local.")}
<body>
{nav("zona")}
<div class="wrap">
{aviso_oficial.html()}

<header>
  <div class="eyebrow">Tu zona</div>
  <h1>¿Cuánto se equivoca el pronóstico donde vives?</h1>
  <p class="lead">Elige un aeródromo en la lista o en el mapa. Las cifras son el {d("error medio")} de la temperatura pronosticada para el día siguiente, durante 2026, sin corregir y con la {d("corrección por estación")}.{" Más abajo, la lluvia pronosticada frente a la que midió el pluviómetro de cada aeródromo." if ll else ""}</p>
</header>

<section class="card">
  <div class="controles">
    <label for="estacion" class="eyebrow">Aeródromo</label> <select id="estacion">{opciones}</select>
    <fieldset class="selector"><legend class="eyebrow">Modelo</legend>
      <label><input type="radio" name="modelo" value="AIFS" checked>AIFS <span class="muted">IA</span></label>
      <label><input type="radio" name="modelo" value="IFS">IFS <span class="muted">físico</span></label>
      <label><input type="radio" name="modelo" value="GFS">GFS <span class="muted">físico</span></label></fieldset>
    <fieldset class="selector"><legend class="eyebrow">Mostrar</legend>
      <label><input type="radio" name="estado" value="g" checked>Sin corregir</label>
      <label><input type="radio" name="estado" value="c">Corregido</label></fieldset>
  </div>
  <div class="zona">
    <div>{mapa_svg(est)}{leyenda()}</div>
    <div class="card ficha" id="ficha" aria-live="polite"><p class="muted">Elige un aeródromo.</p></div>
  </div>
</section>

<section>
  <div class="sec-head"><h2>Todos los aeródromos, de mayor a menor error</h2>
  <p class="muted">Modelo <strong id="tabla-modelo">AIFS</strong>, error medio a 24 h en 2026. Toca una fila para ver su ficha.</p></div>
  <div class="card tabla"><table id="tabla-est"><thead><tr><th class="l">Aeródromo</th><th>Sin corregir</th><th>Corregido</th><th>Cambio</th><th class="l">Nivel</th></tr></thead><tbody></tbody></table></div>
</section>

{tabla_lluvia(ll)}

{ultimos}

{tecnico}

{aviso()}
{pie(ahora)}
</div>
<script>window.ZONA = {datos_js};</script>
{JS_MAPA}
{JS_DEF}
</body>
</html>
"""
    return escribir("zona.html", html)


def render_site(pts):
    pts = pts.copy()
    if "modelo" not in pts.columns:
        pts.insert(0, "modelo", "AIFS")
    pts["modelo"] = pts["modelo"].fillna("AIFS")
    pts["run"] = pd.to_datetime(pts["run"])
    pts["valid"] = pd.to_datetime(pts["valid"])
    ahora = pd.Timestamp.now("UTC")
    est = datos_estaciones()
    ll = datos_lluvia(est)
    kb1 = pagina_resumen(est, ahora, ll)
    kb2 = pagina_zona(est, pts, ahora, ll)
    print(f"site/index.html ({kb1} KB) y site/zona.html ({kb2} KB) listos: {len(est)} aeródromos consolidados, "
          f"{len(pts)} comparaciones del pipeline diario" + (f", lluvia en {ll['n_est']} aeródromos" if ll else ", sin lluvia medida"))
    try:                                     # Eventos y Método se regeneran con los resultados guardados
        import sys
        sys.path.insert(0, os.path.join(AQUI, "..", "historico"))
        import render_historico
        render_historico.desde_csv()
        import envivo_pagina                 # pestaña En vivo: armazón; los datos los lee el navegador
        print(f"site/envivo.html ({envivo_pagina.pagina(head, escribir, ahora)} KB) listo")
    except Exception as e:
        print("AVISO: no se regeneraron Eventos y Método:", e)


if __name__ == "__main__":
    ruta = os.path.join(AQUI, "data", "verif_puntos.csv")
    render_site(pd.read_csv(ruta, parse_dates=["run", "valid"]))
