"""Verifica los dos pronósticos públicos de la DMC por localidad contra lo que midió su propia red de estaciones automáticas
(estaciones/dmc_abierto.py, servicios abiertos, día de 00 a 24 UTC):

1. El pronóstico oficial redactado por sus meteorólogos (data/dmc_oficial.csv, de fetch_dmc.py): mínima y máxima del día y
   si anuncia lluvia, contra la mínima, la máxima y el agua caída (≥ 1 mm) de la estación de esa ciudad. Las localidades se
   emparejan a mano con una estación de la misma ciudad o su aeródromo, a altura parecida (ESTACION); las dudosas quedan
   fuera. Por día de anticipación: 0 es el mismo día (la DMC publica solo la máxima), 1 es mañana... hasta 4. De cada día
   de emisión se usa la última redacción. Las comparaciones se acumulan en data/verif_dmc_oficial.csv.
2. El pronóstico de riesgo de incendio (estaciones/datos/dmc_riesgo_pron.csv): máxima, humedad mínima y viento máximo de hoy
   y mañana en ~150 estaciones, contra lo medido (máxima de dmc_extremos.csv; humedad y viento de dmc_riesgo_obs.csv, con al
   menos MIN_LECTURAS lecturas en el día). También la regla 30-30-30 (más de 30 °C, menos de 30 % de humedad y viento sobre
   30 km/h): cuántas veces la previó y cuántas se dio. Se recalcula cada vez desde los archivos de estaciones/.

seccion() arma la tarjeta "Contra el pronóstico oficial" de la portada. Uso: python dmc_oficial.py (lo llama verify.py)."""
import datetime as dt, os
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "data", "dmc_oficial.csv")
SALIDA = os.path.join(AQUI, "data", "verif_dmc_oficial.csv")
EST = os.path.join(AQUI, "..", "estaciones", "datos")
EXTREMOS, R_PRON, R_OBS = (os.path.join(EST, f) for f in ("dmc_extremos.csv", "dmc_riesgo_pron.csv", "dmc_riesgo_obs.csv"))
UMBRAL = 1.0
MIN_LECTURAS = 10
DIAS = {0: "Hoy", 1: "Mañana", 2: "En 2 días", 3: "En 3 días", 4: "En 4 días"}
COLS = ["emision", "dia", "indice", "ciudad", "codigo", "fecha", "tmin_fc", "tmax_fc", "lluvia_fc", "tmin_obs", "tmax_obs", "mm_obs"]

# Localidad del pronóstico oficial -> estación automática de la DMC en esa ciudad o su aeródromo (código nacional).
# Fuera, por no tener una estación que la represente: Caldera, Los Vilos, Valparaíso, Los Andes, Villa Alemana, Papudo,
# Santiago norte y sur, Melipilla, Lota, Puerto Cisnes y las localidades sin estación de la DMC.
ESTACION = {
    "visviri": "170001", "putre": "180017", "arica": "180018", "colchane": "190010", "iquique": "200010", "ollague": "210901",
    "tocopilla": "220027", "calama": "220002", "mejillones": "230022", "antofagasta": "230002", "taltal": "250005",
    "salvador": "260010", "rapanui": "270001", "copiapo": "270009", "freirina": "280010", "serena": "290004", "vicuna": "300046",
    "ovalle": "300024", "combarbala": "310024", "illapel": "310040", "snfelipe": "320019", "calera": "320124", "vdelmar": "330006",
    "colina": "330162", "stgop": "330021", "stgoc": "330020", "stgoo": "330019", "curacavi": "330121", "snjosemaipo": "330112",
    "snantonio": "330161", "jfernandez": "330031", "rancagua": "340045", "pichilemu": "340115", "curico": "340031",
    "talca": "350028", "linares": "350901", "chillan": "360011", "concepcion": "360019", "talcahuano": "360019",
    "angeles": "370033", "angol": "370067", "temuco": "380013", "villarica": "390028", "panguipulli": "390029",
    "valdivia": "390015", "union": "400058", "osorno": "400013", "pmontt": "410027", "ancud": "410026", "chaiten": "420015",
    "quellon": "430001", "futaleufu": "430002", "melinka": "430009", "aysen": "450001", "coyhaique": "450004",
    "balmaceda": "450005", "ohiggins": "480002", "torres": "510020", "natales": "510005", "parenas": "520012",
    "porvenir": "530005", "pwilliams": "550001", "antartica": "950001"}


def leer(ruta, **kw):
    try:
        return pd.read_csv(ruta, dtype={"codigo": str}, **kw)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


# ---------- 1. pronóstico oficial ----------
def verificar():
    """Empareja los pronósticos oficiales de días ya cerrados con lo medido y acumula data/verif_dmc_oficial.csv."""
    viejo = leer(SALIDA)
    if viejo.empty:
        viejo = pd.DataFrame(columns=COLS)
    p, ext = leer(ENTRADA), leer(EXTREMOS)
    if p.empty or ext.empty:
        return viejo
    p = p.fillna("")
    p["codigo"] = p.indice.map(ESTACION)
    p = p.dropna(subset=["codigo"])
    p["emision_dia"] = p.emision.str[:10]
    p = p.sort_values("emision").drop_duplicates(subset=["emision_dia", "indice", "fecha"], keep="last")
    hechas = set(zip(viejo.emision.astype(str), viejo.indice.astype(str), viejo.fecha.astype(str)))
    p = p[[(e, i, f) not in hechas for e, i, f in zip(p.emision, p.indice, p.fecha)]]
    medido = {(r.codigo, r.fecha): r for r in ext.itertuples(index=False)}
    filas = []
    for r in p.itertuples(index=False):
        m = medido.get((r.codigo, r.fecha))
        if m is None:
            continue
        filas.append({"emision": r.emision, "dia": int(r.dia), "indice": r.indice, "ciudad": r.ciudad, "codigo": r.codigo, "fecha": r.fecha,
                      "tmin_fc": r.tmin, "tmax_fc": r.tmax, "lluvia_fc": r.lluvia, "tmin_obs": m.tmin, "tmax_obs": m.tmax, "mm_obs": m.mm})
    if not filas:
        return viejo
    nuevo = pd.DataFrame(filas, columns=COLS)
    nuevo = (pd.concat([viejo, nuevo]) if not viejo.empty else nuevo).drop_duplicates(subset=["emision", "indice", "fecha"], keep="last")
    nuevo = nuevo.sort_values(["fecha", "dia", "indice"])
    nuevo.to_csv(SALIDA, index=False)
    print(f"DMC oficial: {len(filas)} comparaciones nuevas, {len(nuevo)} en total")
    return nuevo


def resumen(v=None):
    """Por día de anticipación: error de la máxima y la mínima, aciertos de lluvia."""
    v = leer(SALIDA) if v is None else v
    if v.empty:
        return []
    for c in ("tmin_fc", "tmax_fc", "tmin_obs", "tmax_obs", "mm_obs", "lluvia_fc"):
        v[c] = pd.to_numeric(v[c], errors="coerce")
    out = []
    for dia, g in v.groupby("dia"):
        tmax, tmin = (g.tmax_fc - g.tmax_obs).dropna(), (g.tmin_fc - g.tmin_obs).dropna()
        l = g.dropna(subset=["mm_obs", "lluvia_fc"])
        llovio, aviso = l.mm_obs >= UMBRAL, l.lluvia_fc == 1
        out.append({"dia": int(dia), "n": int(max(len(tmax), len(tmin), len(l))),
                    "mae_tmax": float(tmax.abs().mean()) if len(tmax) else None, "mae_tmin": float(tmin.abs().mean()) if len(tmin) else None,
                    "llovio": int(llovio.sum()), "avisados": int((llovio & aviso).sum()), "falsas": int((~llovio & aviso).sum()),
                    "n_lluvia": int(len(l)), "desde": str(g.fecha.min()), "hasta": str(g.fecha.max()), "lugares": int(g.indice.nunique())})
    return out


# ---------- 2. riesgo de incendio ----------
def treinta(t, h, v):
    return (t > 30) & (h < 30) & (v > 30)


def riesgo():
    """Pares pronóstico-medido del riesgo de incendio por estación, día y anticipación (0 hoy, 1 mañana)."""
    pr, ob, ext = leer(R_PRON), leer(R_OBS), leer(EXTREMOS)
    if pr.empty or ob.empty:
        return pd.DataFrame()
    hoy = dt.datetime.now(dt.timezone.utc).date().isoformat()
    pr = pr[pr.fecha < hoy].copy()
    pr["emision_dia"] = pr.emitido.str[:10]
    pr = pr.sort_values("emitido").drop_duplicates(subset=["emision_dia", "codigo", "fecha"], keep="first")
    ob = ob[ob.n >= MIN_LECTURAS]
    j = pr.merge(ob[["fecha", "codigo", "hrmin", "vmax", "tmax"]].rename(columns={"hrmin": "hrmin_obs", "vmax": "vmax_obs", "tmax": "tmax6_obs"}),
                 on=["fecha", "codigo"])
    if not ext.empty:
        j = j.merge(ext[["fecha", "codigo", "tmax"]].rename(columns={"tmax": "tmax_obs"}), on=["fecha", "codigo"], how="left")
        j["tmax_obs"] = j.tmax_obs.fillna(j.tmax6_obs)
    else:
        j["tmax_obs"] = j.tmax6_obs
    return j


def resumen_riesgo(j=None):
    j = riesgo() if j is None else j
    if j.empty:
        return []
    out = []
    for dia, g in j.groupby("dia"):
        fc, ob = treinta(g.tmax, g.hrmin, g.vmax), treinta(g.tmax_obs, g.hrmin_obs, g.vmax_obs)
        out.append({"dia": int(dia), "n": int(len(g)), "mae_tmax": float((g.tmax - g.tmax_obs).abs().mean()),
                    "mae_hr": float((g.hrmin - g.hrmin_obs).abs().mean()), "mae_v": float((g.vmax - g.vmax_obs).abs().mean()),
                    "sesgo_v": float((g.vmax - g.vmax_obs).mean()), "ocurrio": int(ob.sum()), "previsto": int(fc.sum()),
                    "acertado": int((ob & fc).sum()), "desde": str(g.fecha.min()), "hasta": str(g.fecha.max()), "estaciones": int(g.codigo.nunique())})
    return out


def riesgo_ahora():
    """Lo que la DMC prevé hoy y mañana: estaciones con las tres condiciones y con dos de tres."""
    pr, ext = leer(R_PRON), leer(EXTREMOS)
    if pr.empty:
        return None
    ultimo = pr.emitido.str[:10].max()
    pr = pr[pr.emitido.str[:10] == ultimo].sort_values("emitido").drop_duplicates(subset=["codigo", "fecha"], keep="last")
    nombres = {} if ext.empty else dict(zip(ext.codigo, ext.nombre))
    out = {}
    for dia, g in pr.groupby("dia"):
        cond = (g.tmax > 30).astype(int) + (g.hrmin < 30).astype(int) + (g.vmax > 30).astype(int)
        out[int(dia)] = {"fecha": g.fecha.iloc[0], "tres": [nombres.get(c, c) for c in g.codigo[cond == 3]],
                         "dos": [nombres.get(c, c) for c in g.codigo[cond == 2]], "n": int(len(g))}
    return out


# ---------- página ----------
def num(x, dec=1):
    return "–" if x is None or x != x else f"{x:.{dec}f}".replace(".", ",")


def dia_txt(iso):
    from comun import MESES
    f = dt.date.fromisoformat(str(iso)[:10])
    return f"{f.day} {MESES[f.month - 1]}"


def corto(nombre):
    return nombre.split(",")[0].replace(" Ad.", "").replace(" Ap.", "").strip()


def seccion():
    """Tarjeta de la portada: el pronóstico oficial y el de riesgo de incendio de la DMC frente a lo medido por su red."""
    from comun import d
    res, rr, ahora = resumen(), resumen_riesgo(), riesgo_ahora()
    intro = ('<p class="muted small">La <a href="https://www.meteochile.gob.cl" rel="noopener">Dirección Meteorológica de Chile</a> '
             'publica cada día el pronóstico oficial de 103 localidades, redactado por sus meteorólogos, y un pronóstico de riesgo de '
             'incendio para unas 150 estaciones. Desde el 29 de octubre de 2026 los guardamos y los comparamos con lo que midió su propia '
             'red de estaciones: es la vara contra la que hay que medir todo lo demás. Su modelo WRF se compara hora a hora con los '
             'globales en <a href="zona.html">Tu zona</a>.</p>')
    if res:
        filas = "".join(
            f'<tr><td class="l">{DIAS.get(r["dia"], r["dia"])}</td><td class="num">{num(r["mae_tmax"])} °C</td><td class="num">{num(r["mae_tmin"])} °C</td>'
            f'<td class="num">{r["n"]}</td><td class="l small">'
            f'{(str(r["avisados"]) + " de " + str(r["llovio"]) + " días con lluvia avisados · " + str(r["falsas"]) + " avisos sin lluvia") if r["n_lluvia"] else "–"}</td></tr>'
            for r in res)
        oficial = (f'<h3>Pronóstico oficial</h3><div class="tabla"><table><thead><tr><th class="l">Pronóstico para</th><th>{d("error medio", "Error máxima")}</th>'
                   f'<th>Error mínima</th><th>{d("comparaciones")}</th><th class="l">Lluvia (≥ 1 mm)</th></tr></thead><tbody>{filas}</tbody></table></div>'
                   f'<p class="small muted">Del {dia_txt(res[0]["desde"])} al {dia_txt(max(r["hasta"] for r in res))}, {max(r["lugares"] for r in res)} localidades con estación '
                   f'propia de la DMC. "Hoy" es el pronóstico de la misma mañana (solo máxima). Pocas comparaciones todavía: las cifras cambian día a día.</p>')
    else:
        oficial = ('<h3>Pronóstico oficial</h3><p class="small">Las primeras comparaciones aparecen cuando la DMC publica lo medido de los '
                   'primeros días pronosticados, en uno o dos días.</p>')
    if ahora:
        lineas = []
        for dia in sorted(ahora):
            a = ahora[dia]
            tres = (f'<strong>{len(a["tres"])}</strong> con las tres ({", ".join(corto(x) for x in a["tres"][:8])}{"…" if len(a["tres"]) > 8 else ""})'
                    if a["tres"] else "ninguna con las tres")
            dos = f'{len(a["dos"])} con dos de tres' if a["dos"] else "ninguna con dos de tres"
            lineas.append(f'<li>{"Hoy" if dia == 0 else "Mañana"}: {tres}; {dos}, de {a["n"]} estaciones.</li>')
        previsto = (f'<p class="small">Lo que prevé la DMC para la condición {d("30-30-30", definicion="Más de 30 °C, menos de 30 % de humedad y viento sobre 30 km/h: cuando se juntan las tres, un incendio se propaga muy rápido.")}:</p>'
                    f'<ul class="small">{"".join(lineas)}</ul>')
    else:
        previsto = ""
    if rr:
        filas = "".join(
            f'<tr><td class="l">{DIAS.get(r["dia"], r["dia"])}</td><td class="num">{num(r["mae_tmax"])} °C</td><td class="num">{num(r["mae_hr"], 0)} %</td>'
            f'<td class="num">{num(r["mae_v"], 0)} km/h</td><td class="num">{r["n"]}</td><td class="l small">{r["ocurrio"]} medidos, {r["acertado"]} de ellos previstos · '
            f'{r["previsto"] - r["acertado"]} previstos que no se dieron</td></tr>' for r in rr)
        verif = (f'<div class="tabla"><table><thead><tr><th class="l">Pronóstico para</th><th>Error máxima</th><th>Error humedad mín.</th><th>Error viento máx.</th>'
                 f'<th>{d("comparaciones")}</th><th class="l">Días 30-30-30 (estación-día)</th></tr></thead><tbody>{filas}</tbody></table></div>'
                 f'<p class="small muted">Del {dia_txt(rr[0]["desde"])} al {dia_txt(max(r["hasta"] for r in rr))}, {max(r["estaciones"] for r in rr)} estaciones. Lo medido sale de la '
                 f'misma red (humedad y viento armados con lecturas horarias de 6 h); viento en km/h según los valores del servicio.</p>')
    else:
        verif = '<p class="small muted">La comparación con lo medido aparece cuando se cierre el primer día completo de lecturas.</p>'
    riesgo_html = f'<h3>Riesgo de incendio</h3>{previsto}{verif}'
    return (f'<section class="card" aria-labelledby="dmc-t"><div class="sec-head"><h2 id="dmc-t">Contra el pronóstico oficial</h2>{intro}</div>'
            f'{oficial}{riesgo_html}</section>')


if __name__ == "__main__":
    v = verificar()
    for r in resumen(v if not v.empty else None):
        print(r)
    for r in resumen_riesgo():
        print(r)
    print(riesgo_ahora())
