"""Verificación retroactiva: cruza los pronósticos históricos (data/pronosticos.csv.gz) con el METAR
histórico (data/metar_*.csv.gz) y produce data/resultados/*.csv y, vía render_historico.py, ../site/historico.html.

 1. Pares de temperatura: la observación más cercana (±31 min) a la hora pronosticada.
 2. Lluvia como sí/no: el METAR chileno no trae milímetros, pero sí "está lloviendo" (RA, DZ, SH, TS...).
    Observado = algún reporte con lluvia en las 24 h que terminan en la hora pronosticada.
    Pronosticado = precipitación acumulada en esas 24 h >= 1 mm.
 3. Eventos 2026 (hindcast/eventos/eventos_2026.csv): lo que decía cada modelo 72, 48 y 24 h antes. El "día" del evento
    va de las 12 UTC de ese día a las 12 UTC del siguiente (8 o 9 de la mañana en Chile), para captar la lluvia de la tarde y la noche.
 4. Error de temperatura por plazo, por mes y por estación.
 5. Corrección por estación: sesgo medio por estación × modelo × plazo × hora de corrida, aprendido
    SOLO con 2025 y aplicado SOLO a 2026. Se publica el error global vs. el corregido.
 6. Viento (capa estándar 4): velocidad a 10 m (desde u y v) contra el METAR más cercano (±31 min); dirección con
    error circular, solo con viento observado de 2 m/s o más; ráfaga del modelo (IFS 10fg, máxima de las 6 h previas;
    GFS GUST; AIFS no la publica) contra la mayor ráfaga o viento reportado en las 6 h previas a la hora válida.
    Episodios de viento fuerte: ventanas de 6 h con ráfaga observada sobre 50 km/h; un modelo lo anticipó si su ráfaga
    pronosticada para esa ventana pasaba de 50 km/h.

Uso: python analizar.py"""
import glob, os, re
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
RES = os.path.join(DATA, "resultados")
EVENTOS = os.path.join(AQUI, "..", "hindcast", "eventos", "eventos_2026.csv")
UMBRAL_LLUVIA_MM = 1.0       # pronóstico de 24 h que cuenta como "va a llover"
UMBRAL_FUERTE_MM = 10.0      # lluvia fuerte
UMBRAL_RAFAGA = 50 / 3.6     # 50 km/h en m/s
VIENTO_MIN_DIR = 2.0         # m/s: bajo esto la dirección observada no es confiable
MIN_REPORTES_24H = 12        # reportes METAR mínimos en 24 h para dar por observada la ventana
MIN_PARES_SESGO = 30         # pares mínimos (en 2025) para aprender el sesgo de una celda
ANIO_ENTRENA, ANIO_EVALUA = 2025, 2026

# Estaciones que representan cada zona de evento (aeródromos más cercanos).
ZONAS = {"coquimbo-jul": ["SCSE", "SCAT"], "centrosur-ago": ["SCQP", "SCTC", "SCGE", "SCCH", "SCIE"], "lascondes-oct": ["SCTB", "SCEL", "SCSN"],
         "santiago-13oct": ["SCTB", "SCEL", "SCSN"], "incendios-ene": ["SCCH", "SCIE", "SCGE"]}
RE_LLUVIA = re.compile(r"(RA|DZ|SN|GR|GS|PL|UP)")


def reporta_lluvia(wx):
    """True si algún grupo de tiempo presente (no 'VC', en la vecindad) indica precipitación."""
    if not isinstance(wx, str):
        return False
    return any(RE_LLUVIA.search(tok) and not tok.startswith("VC") for tok in wx.split())


def cargar():
    pron = pd.read_csv(os.path.join(DATA, "pronosticos.csv.gz"), parse_dates=["run", "valid"])
    obs = pd.concat([pd.read_csv(f, parse_dates=["time"]) for f in sorted(glob.glob(os.path.join(DATA, "metar_*.csv.gz")))], ignore_index=True)
    obs = obs.dropna(subset=["temp_c"]).sort_values("time")
    # misma resolución de fecha en ambas tablas (pandas 3 puede inferir "s" o "us" y merge_asof exige igualdad)
    for df, col in ((pron, "run"), (pron, "valid"), (obs, "time")):
        df[col] = df[col].astype("datetime64[ns]")
    obs["lluvia"] = obs.wx.map(reporta_lluvia)
    return pron, obs


def tp_24h(pron):
    """Precipitación de las 24 h que terminan en cada plazo: acumulado(plazo) − acumulado(plazo − 24)."""
    p = pron.sort_values(["modelo", "run", "icao", "lead_h"]).copy()
    g = p.groupby(["modelo", "run", "icao"], sort=False)
    prev_tp = g.tp_fc.shift(); prev_lead = g.lead_h.shift()
    p["tp24_fc"] = np.where(p.lead_h == 24, p.tp_fc, np.where(prev_lead == p.lead_h - 24, p.tp_fc - prev_tp, np.nan))
    p["tp24_fc"] = p.tp24_fc.clip(lower=0)
    return p


def lluvia_observada(pron, obs):
    """Para cada fila: horas con reporte de lluvia y número de reportes en las 24 h previas a 'valid'."""
    horas = np.full(len(pron), np.nan); n_rep = np.zeros(len(pron))
    icaos = pron.icao.values; valids = pron.valid.values.astype("datetime64[ns]").astype("int64")
    for icao, g in obs.groupby("icao"):
        idx = np.where(icaos == icao)[0]
        if not len(idx):
            continue
        t = g.time.values.astype("datetime64[ns]").astype("int64"); r = g.lluvia.values.astype(int)
        o = np.argsort(t); t, r = t[o], r[o]
        cum = np.concatenate([[0], np.cumsum(r)])
        v = valids[idx]
        hi = np.searchsorted(t, v, side="right"); lo = np.searchsorted(t, v - 24 * 3600 * 10 ** 9, side="right")
        n_rep[idx] = hi - lo; horas[idx] = cum[hi] - cum[lo]
    return horas, n_rep


def emparejar(pron, obs):
    p = tp_24h(pron).sort_values("valid")
    cols = ["icao", "time", "temp_c"] + [c for c in ("wspd_ms", "wdir") if c in obs]
    o = obs[cols].sort_values("time")
    pares = pd.merge_asof(p, o, left_on="valid", right_on="time", by="icao", tolerance=pd.Timedelta("31min"), direction="nearest")
    pares = pares.rename(columns={"temp_c": "t_obs", "wspd_ms": "w_obs", "wdir": "d_obs"})
    pares["t_err"] = pares.t_fc - pares.t_obs
    pares = viento(pares, obs)
    horas, n_rep = lluvia_observada(pares, obs)
    pares["horas_lluvia_obs"] = horas; pares["n_rep_24h"] = n_rep
    pares["lluvia_obs"] = np.where(n_rep >= MIN_REPORTES_24H, horas >= 1, np.nan)
    pares["lluvia_fc"] = np.where(pares.tp24_fc.notna(), pares.tp24_fc >= UMBRAL_LLUVIA_MM, np.nan)
    pares["anio"] = pares.valid.dt.year; pares["mes"] = pares.valid.dt.strftime("%Y-%m"); pares["hora_run"] = pares.run.dt.hour
    return pares.drop(columns=["time"])


def viento(pares, obs):
    """Velocidad, dirección y ráfaga del modelo contra el METAR. Si el pronóstico no trae u y v, deja NaN."""
    for c in ("u_fc", "v_fc", "g_fc", "w_obs", "d_obs"):
        if c not in pares:
            pares[c] = np.nan
    pares["w_fc"] = np.hypot(pares.u_fc, pares.v_fc)
    pares["d_fc"] = (270 - np.degrees(np.arctan2(pares.v_fc, pares.u_fc))) % 360     # dirección de donde viene
    pares["w_err"] = pares.w_fc - pares.w_obs
    dd = ((pares.d_fc - pares.d_obs + 180) % 360) - 180
    pares["d_err"] = np.where(pares.w_obs >= VIENTO_MIN_DIR, dd, np.nan)
    # mayor ráfaga (o viento, si no hubo ráfaga significativa) reportada en las 6 h previas a la hora válida
    g = obs[["icao", "time"]].copy()
    rafaga = obs["gust_ms"] if "gust_ms" in obs else pd.Series(np.nan, index=obs.index)
    g["max_g"] = np.fmax(rafaga.astype(float), obs["wspd_ms"].astype(float) if "wspd_ms" in obs else np.nan)
    g = g.dropna(subset=["max_g"])
    trozos = []
    for icao, x in g.groupby("icao"):
        x = x.sort_values("time").set_index("time")
        r = x.max_g.rolling("6h").agg(["max", "count"])
        trozos.append(pd.DataFrame({"icao": icao, "time": r.index, "g_obs6": r["max"].values, "n_obs6": r["count"].values}))
    if trozos:
        gg = pd.concat(trozos).sort_values("time")
        gg["time"] = gg.time.astype("datetime64[ns]")
        pares = pd.merge_asof(pares.sort_values("valid"), gg, left_on="valid", right_on="time", by="icao",
                              tolerance=pd.Timedelta("61min"), direction="backward", suffixes=("", "_g")).drop(columns=["time_g"], errors="ignore")
        pares.loc[pares.n_obs6 < 4, "g_obs6"] = np.nan          # al menos 4 reportes en la ventana
    else:
        pares["g_obs6"] = np.nan
    pares["g_err"] = pares.g_fc - pares.g_obs6
    return pares


def resumen_viento(pares, por):
    t = pares.dropna(subset=["w_err"])
    if t.empty:
        return pd.DataFrame()
    r = t.groupby(por).agg(n=("w_err", "size"), w_mae=("w_err", mae), w_sesgo=("w_err", "mean"),
                           d_n=("d_err", "count"), d_mae=("d_err", mae), g_n=("g_err", "count"), g_mae=("g_err", mae),
                           g_sesgo=("g_err", "mean")).reset_index()
    return r


def episodios(pares, por):
    """Ventanas de 6 h con ráfaga observada sobre 50 km/h: cuántas anticipó cada modelo (ráfaga pronosticada ≥ 50 km/h)."""
    d = pares.dropna(subset=["g_obs6", "g_fc"]).copy()
    if d.empty:
        return pd.DataFrame()
    d["obs"] = d.g_obs6 >= UMBRAL_RAFAGA; d["fc"] = d.g_fc >= UMBRAL_RAFAGA
    c = d.groupby(por).agg(ventanas=("obs", "size"), episodios=("obs", "sum"), anticipados=("obs", lambda x: int((x & d.loc[x.index, "fc"]).sum())),
                           en_falso=("fc", lambda x: int((x & ~d.loc[x.index, "obs"]).sum()))).reset_index()
    c["pod"] = c.anticipados / c.episodios.replace(0, np.nan)
    c["far"] = c.en_falso / (c.anticipados + c.en_falso).replace(0, np.nan)
    return c


def eventos_viento(pares):
    """Viento y ráfaga pronosticados vs. observados en los días de cada evento (horas válidas 00 y 12 UTC)."""
    try:
        ev = pd.read_csv(EVENTOS, parse_dates=["inicio", "fin"])
    except Exception:
        return pd.DataFrame()
    filas = []
    for e in ev.itertuples(index=False):
        ests = ZONAS.get(e.id, [])
        validos = [d + pd.Timedelta(hours=h) for d in pd.date_range(e.inicio, e.fin, freq="D") for h in (24, 36)]
        sel = pares[pares.icao.isin(ests) & pares.valid.isin(validos)]
        if sel.empty:
            continue
        r = sel.groupby(["modelo", "lead_h"]).agg(w_fc_max=("w_fc", "max"), w_obs_max=("w_obs", "max"),
                                                  g_fc_max=("g_fc", "max"), g_obs_max=("g_obs6", "max"), n=("w_fc", "count")).reset_index()
        r.insert(0, "evento", e.id)
        filas.append(r)
    return pd.concat(filas, ignore_index=True) if filas else pd.DataFrame()


def mae(e):
    return e.abs().mean()


def resumen_temp(pares, por):
    t = pares.dropna(subset=["t_err"])
    return t.groupby(por).agg(n=("t_err", "size"), mae=("t_err", mae), sesgo=("t_err", "mean")).reset_index()


def contingencia(pares, por):
    d = pares.dropna(subset=["lluvia_obs", "lluvia_fc"]).copy()
    d["lluvia_obs"] = d.lluvia_obs.astype(bool); d["lluvia_fc"] = d.lluvia_fc.astype(bool)
    d["acierto"] = d.lluvia_obs & d.lluvia_fc; d["falla"] = d.lluvia_obs & ~d.lluvia_fc
    d["falsa"] = ~d.lluvia_obs & d.lluvia_fc; d["negativo"] = ~d.lluvia_obs & ~d.lluvia_fc
    c = d.groupby(por).agg(n=("acierto", "size"), aciertos=("acierto", "sum"), fallas=("falla", "sum"),
                            falsas=("falsa", "sum"), negativos=("negativo", "sum")).reset_index()
    c["pod"] = c.aciertos / (c.aciertos + c.fallas).replace(0, np.nan)          # de las veces que llovió, cuántas se avisó
    c["far"] = c.falsas / (c.aciertos + c.falsas).replace(0, np.nan)            # de los avisos, cuántos fueron en falso
    c["frec_obs"] = (c.aciertos + c.fallas) / c.n
    return c


def eventos(pares):
    try:
        ev = pd.read_csv(EVENTOS, parse_dates=["inicio", "fin"])
    except (FileNotFoundError, pd.errors.ParserError) as e:
        print("catálogo de eventos no legible, se omite la sección:", e)
        return pd.DataFrame(), pd.DataFrame()
    filas = []
    for e in ev.itertuples(index=False):
        ests = ZONAS.get(e.id, [])
        for dia in pd.date_range(e.inicio, e.fin, freq="D"):
            valid = dia + pd.Timedelta(hours=36)   # ventana del día: de las 12 UTC de ese día a las 12 UTC del siguiente
            sel = pares[(pares.icao.isin(ests)) & (pares.valid == valid)]
            for r in sel.itertuples(index=False):
                filas.append(dict(evento=e.id, zona=e.zona, dia=dia.date(), icao=r.icao, modelo=r.modelo, lead_h=r.lead_h,
                                  tp24_fc=r.tp24_fc, t_fc=r.t_fc, t_obs=r.t_obs, horas_lluvia_obs=r.horas_lluvia_obs,
                                  n_rep_24h=r.n_rep_24h, lluvia_obs=r.lluvia_obs, lluvia_fc=r.lluvia_fc))
    det = pd.DataFrame(filas)
    if det.empty:
        return det, pd.DataFrame()
    res = contingencia(det, ["evento", "modelo", "lead_h"])
    return det, res


def correccion(pares):
    """Sesgo por estación × modelo × plazo × hora de corrida aprendido en ANIO_ENTRENA; evaluado en ANIO_EVALUA."""
    t = pares.dropna(subset=["t_err"])
    entrena = t[t.anio == ANIO_ENTRENA]; evalua = t[t.anio == ANIO_EVALUA].copy()
    if entrena.empty or evalua.empty:
        return pd.DataFrame(), pd.DataFrame(), evalua
    clave = ["modelo", "icao", "lead_h", "hora_run"]
    sesgos = entrena.groupby(clave).agg(n_entrena=("t_err", "size"), sesgo=("t_err", "mean")).reset_index()
    sesgos = sesgos[sesgos.n_entrena >= MIN_PARES_SESGO]
    evalua = evalua.merge(sesgos, on=clave, how="left")
    evalua["t_fc_corr"] = evalua.t_fc - evalua.sesgo.fillna(0.0)
    evalua["t_err_corr"] = evalua.t_fc_corr - evalua.t_obs
    con = evalua.dropna(subset=["sesgo"])  # solo celdas con corrección aprendida, para comparar lo mismo con lo mismo
    por_plazo = con.groupby(["modelo", "lead_h"]).agg(n=("t_err", "size"), mae_global=("t_err", mae), mae_corregido=("t_err_corr", mae),
                                                     sesgo_global=("t_err", "mean"), sesgo_corregido=("t_err_corr", "mean")).reset_index()
    por_estacion = con.groupby(["modelo", "lead_h", "icao"]).agg(n=("t_err", "size"), mae_global=("t_err", mae), mae_corregido=("t_err_corr", mae)).reset_index()
    return por_plazo, por_estacion, evalua


def main():
    os.makedirs(RES, exist_ok=True)
    pron, obs = cargar()
    pares = emparejar(pron, obs)
    pares.to_csv(os.path.join(DATA, "pares.csv.gz"), index=False, compression="gzip")
    print(f"pares: {len(pares)} ({pares.t_err.notna().sum()} con temperatura observada), modelos {sorted(pares.modelo.unique())}, "
          f"{pares.valid.min():%Y-%m-%d} a {pares.valid.max():%Y-%m-%d}")

    r = {}
    r["plazos"] = resumen_temp(pares, ["modelo", "lead_h"])
    r["plazos_anio"] = resumen_temp(pares, ["anio", "modelo", "lead_h"])
    r["mensual"] = resumen_temp(pares, ["mes", "modelo", "lead_h"])
    r["estaciones"] = resumen_temp(pares, ["modelo", "lead_h", "icao"])
    r["lluvia"] = contingencia(pares, ["modelo", "lead_h"])
    r["lluvia_anio"] = contingencia(pares, ["anio", "modelo", "lead_h"])
    r["eventos_detalle"], r["eventos_resumen"] = eventos(pares)
    r["correccion_plazos"], r["correccion_estaciones"], evalua = correccion(pares)
    r["viento_plazos"] = resumen_viento(pares, ["modelo", "lead_h"])
    r["viento_mensual"] = resumen_viento(pares, ["mes", "modelo", "lead_h"])
    r["viento_estaciones"] = resumen_viento(pares, ["modelo", "lead_h", "icao"])
    r["rachas_episodios"] = episodios(pares, ["modelo", "lead_h"])
    r["rachas_estaciones"] = episodios(pares, ["modelo", "lead_h", "icao"])
    r["eventos_viento"] = eventos_viento(pares)
    for k, df in r.items():
        df.to_csv(os.path.join(RES, f"{k}.csv"), index=False)
    print(r["plazos"].round(2).to_string(index=False))
    if not r["viento_plazos"].empty:
        print(); print(r["viento_plazos"].round(2).to_string(index=False))
    if not r["rachas_episodios"].empty:
        print(); print(r["rachas_episodios"].round(2).to_string(index=False))
    if not r["correccion_plazos"].empty:
        print(); print(r["correccion_plazos"].round(2).to_string(index=False))
    else:
        print("corrección: pendiente (hace falta tener 2025 y 2026)")

    import sys
    sys.path.insert(0, AQUI)
    from render_historico import render
    render(pares, r)


if __name__ == "__main__":
    main()
