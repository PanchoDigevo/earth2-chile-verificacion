"""Verifica el pronóstico oficial de la DMC (data/dmc_oficial.csv, de fetch_dmc.py) contra lo medido en el aeródromo de cada
localidad: mínima y máxima del día (METAR, en hora de Chile) y si llovió (≥ 1 mm en la estación SYNOP del aeródromo, la misma
pareja que usa lluvia.py; el "día" de lluvia va de las 03 h a las 03 h siguientes, por los bloques de 6 h del SYNOP).

Un pronóstico se cuenta por día de anticipación: 0 es el mismo día (la DMC publica solo la máxima), 1 es mañana... hasta 4.
De cada día de emisión se usa la última redacción. La mínima se compara si hay al menos 3 METAR entre las 02 y las 09 h, la
máxima si hay 3 entre las 12 y las 19 h. Cada comparación queda en data/verif_dmc_oficial.csv y no se recalcula.

seccion() arma la tarjeta "Contra el pronóstico oficial" de la portada. Uso: python dmc_oficial.py (lo llama verify.py)."""
import datetime as dt, os
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "data", "dmc_oficial.csv")
OBS = os.path.join(AQUI, "data", "metar_obs.csv")
SALIDA = os.path.join(AQUI, "data", "verif_dmc_oficial.csv")
TZ = "America/Santiago"
UMBRAL = 1.0
DIAS = {0: "Hoy", 1: "Mañana", 2: "En 2 días", 3: "En 3 días", 4: "En 4 días"}
COLS = ["emision", "dia", "indice", "ciudad", "icao", "fecha", "tmin_fc", "tmax_fc", "lluvia_fc", "tmin_obs", "tmax_obs", "mm_obs"]


def extremos_observados():
    """{(icao, fecha local): (tmin, tmax)} con None donde faltan METAR en las horas de la mínima o la máxima."""
    o = pd.read_csv(OBS, usecols=["icao", "time", "temp_c"], parse_dates=["time"]).dropna(subset=["temp_c"])
    o["local"] = o.time.dt.tz_convert(TZ)
    o["fecha"] = o.local.dt.date.astype(str); o["hora"] = o.local.dt.hour
    out = {}
    for (icao, fecha), g in o.groupby(["icao", "fecha"]):
        noche, tarde = g[(g.hora >= 2) & (g.hora <= 9)], g[(g.hora >= 12) & (g.hora <= 19)]
        out[(icao, fecha)] = (float(noche.temp_c.min()) if len(noche) >= 3 else None,
                              float(tarde.temp_c.max()) if len(tarde) >= 3 else None)
    return out


def lluvia_observada(fechas):
    """{(icao, fecha): mm} medidos por la estación SYNOP de cada aeródromo (03 h a 03 h hora de Chile), si están los 4 bloques."""
    import lluvia
    obs = lluvia.leer_obs()
    par = lluvia.parejas(obs)
    out = {}
    for fecha in fechas:
        fin = dt.datetime.fromisoformat(fecha).replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=30)   # 06 UTC del día siguiente
        for icao, p in par.items():
            mm = lluvia.medido_24h(obs, p["wmo"], fin)
            if mm is not None:
                out[(icao, fecha)] = mm
    return out


def verificar():
    """Empareja los pronósticos oficiales de días ya terminados con lo medido y acumula data/verif_dmc_oficial.csv."""
    if not os.path.exists(ENTRADA):
        return pd.DataFrame(columns=COLS)
    p = pd.read_csv(ENTRADA, dtype=str).fillna("")
    p = p[p.icao != ""]
    hoy = pd.Timestamp.now(TZ).strftime("%Y-%m-%d")
    p = p[p.fecha < hoy].copy()
    p["emision_dia"] = p.emision.str[:10]
    p = p.sort_values("emision").drop_duplicates(subset=["emision_dia", "indice", "fecha"], keep="last")
    hechas = set()
    if os.path.exists(SALIDA):
        viejo = pd.read_csv(SALIDA, dtype=str).fillna("")
        hechas = set(zip(viejo.emision, viejo.indice, viejo.fecha))
    else:
        viejo = pd.DataFrame(columns=COLS)
    p = p[[(e, i, f) not in hechas for e, i, f in zip(p.emision, p.indice, p.fecha)]]
    if p.empty:
        return viejo
    ext = extremos_observados()
    try:
        ll = lluvia_observada(sorted(set(p.fecha)))
    except Exception as e:
        print("DMC oficial: sin lluvia medida ->", type(e).__name__, e); ll = {}
    filas = []
    for r in p.itertuples(index=False):
        tmin_o, tmax_o = ext.get((r.icao, r.fecha), (None, None))
        mm = ll.get((r.icao, r.fecha))
        if tmin_o is None and tmax_o is None and mm is None:
            continue
        filas.append({"emision": r.emision, "dia": int(r.dia), "indice": r.indice, "ciudad": r.ciudad, "icao": r.icao, "fecha": r.fecha,
                      "tmin_fc": r.tmin, "tmax_fc": r.tmax, "lluvia_fc": r.lluvia, "tmin_obs": tmin_o, "tmax_obs": tmax_o, "mm_obs": mm})
    nuevo = pd.concat([viejo, pd.DataFrame(filas, columns=COLS)]).drop_duplicates(subset=["emision", "indice", "fecha"], keep="last")
    nuevo = nuevo.sort_values(["fecha", "dia", "icao"])
    nuevo.to_csv(SALIDA, index=False)
    print(f"DMC oficial: {len(filas)} comparaciones nuevas, {len(nuevo)} en total")
    return nuevo


def resumen(v=None):
    """Por día de anticipación: comparaciones y error de la máxima y la mínima, aciertos de lluvia."""
    if v is None:
        try:
            v = pd.read_csv(SALIDA)
        except Exception:
            return []
    if v.empty:
        return []
    for c in ("tmin_fc", "tmax_fc", "tmin_obs", "tmax_obs", "mm_obs", "lluvia_fc"):
        v[c] = pd.to_numeric(v[c], errors="coerce")
    out = []
    for dia, g in v.groupby("dia"):
        tmax = (g.tmax_fc - g.tmax_obs).dropna(); tmin = (g.tmin_fc - g.tmin_obs).dropna()
        l = g.dropna(subset=["mm_obs", "lluvia_fc"])
        llovio, aviso = l.mm_obs >= UMBRAL, l.lluvia_fc == 1
        out.append({"dia": int(dia), "n_tmax": int(len(tmax)), "mae_tmax": round(float(tmax.abs().mean()), 1) if len(tmax) else None,
                    "bias_tmax": round(float(tmax.mean()), 1) if len(tmax) else None,
                    "n_tmin": int(len(tmin)), "mae_tmin": round(float(tmin.abs().mean()), 1) if len(tmin) else None,
                    "n_lluvia": int(len(l)), "llovio": int(llovio.sum()), "avisados": int((llovio & aviso).sum()),
                    "falsas": int((~llovio & aviso).sum()), "aciertos": int((llovio == aviso).sum()),
                    "desde": str(g.fecha.min()), "hasta": str(g.fecha.max()), "lugares": int(g.icao.nunique())})
    return out


def num(x, dec=1):
    return "–" if x is None or x != x else f"{x:.{dec}f}".replace(".", ",")


def seccion():
    """Tarjeta de la portada: el pronóstico oficial de la DMC frente a lo medido, por día de anticipación."""
    from comun import d
    res = resumen()
    intro = ('<p class="muted small">La <a href="https://www.meteochile.gob.cl" rel="noopener">Dirección Meteorológica de Chile</a> '
             'publica cada día el pronóstico oficial de 103 localidades, redactado por sus meteorólogos. Desde el 29 de octubre de 2026 '
             'lo guardamos y lo comparamos con lo que midió el aeródromo de cada ciudad: es la vara contra la que hay que medir todo lo '
             'demás. Su modelo WRF se compara hora a hora con los globales en <a href="zona.html">Tu zona</a>.</p>')
    if not res:
        cuerpo = '<p class="small">Las primeras comparaciones aparecen cuando terminan los primeros días pronosticados, en uno o dos días.</p>'
    else:
        filas = []
        for r in res:
            lluvia = (f'{r["avisados"]} de {r["llovio"]} días con lluvia avisados · {r["falsas"]} avisos sin lluvia' if r["n_lluvia"]
                      else "–")
            filas.append(f'<tr><td class="l">{DIAS.get(r["dia"], r["dia"])}</td><td class="num">{num(r["mae_tmax"])} °C</td>'
                         f'<td class="num">{num(r["mae_tmin"])} °C</td><td class="num">{max(r["n_tmax"], r["n_tmin"], r["n_lluvia"])}</td>'
                         f'<td class="l small">{lluvia}</td></tr>')
        desde, hasta, lugares = res[0]["desde"], max(r["hasta"] for r in res), max(r["lugares"] for r in res)
        cuerpo = (f'<div class="tabla"><table><thead><tr><th class="l">Pronóstico para</th><th>{d("error medio", "Error máxima")}</th>'
                  f'<th>Error mínima</th><th>{d("comparaciones")}</th><th class="l">Lluvia (≥ 1 mm)</th></tr></thead><tbody>{"".join(filas)}</tbody></table></div>'
                  f'<p class="small muted">Del {desde} al {hasta}, {lugares} ciudades con aeródromo. "Hoy" es el pronóstico publicado la misma mañana '
                  f'(solo máxima). Pocas comparaciones todavía: las cifras cambian día a día.</p>')
    return (f'<section class="card" aria-labelledby="dmc-t"><div class="sec-head"><h2 id="dmc-t">Contra el pronóstico oficial</h2>{intro}</div>'
            f'{cuerpo}</section>')


if __name__ == "__main__":
    v = verificar()
    for r in resumen(v if not v.empty else None):
        print(r)
