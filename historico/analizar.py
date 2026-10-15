"""Verificación retroactiva: cruza los pronósticos históricos (data/pronosticos.csv.gz) con el METAR
histórico (data/metar_*.csv.gz) y produce data/resultados/*.csv y, vía render_historico.py, ../site/historico.html.

 1. Pares de temperatura: la observación más cercana (±31 min) a la hora pronosticada.
 2. Lluvia como sí/no: el METAR chileno no trae milímetros, pero sí "está lloviendo" (RA, DZ, SH, TS...).
    Observado = algún reporte con lluvia en las 24 h que terminan en la hora pronosticada.
    Pronosticado = precipitación acumulada en esas 24 h >= 1 mm.
 3. Eventos 2026 (hindcast/eventos/eventos_2026.csv): lo que decía cada modelo 72, 48 y 24 h antes.
 4. Error de temperatura por plazo, por mes y por estación.
 5. Corrección por estación: sesgo medio por estación × modelo × plazo × hora de corrida, aprendido
    SOLO con 2025 y aplicado SOLO a 2026. Se publica el error global vs. el corregido.

Uso: python analizar.py"""
import glob, os, re
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
RES = os.path.join(DATA, "resultados")
EVENTOS = os.path.join(AQUI, "..", "hindcast", "eventos", "eventos_2026.csv")
UMBRAL_LLUVIA_MM = 1.0       # pronóstico de 24 h que cuenta como "va a llover"
UMBRAL_FUERTE_MM = 10.0      # lluvia fuerte
MIN_REPORTES_24H = 12        # reportes METAR mínimos en 24 h para dar por observada la ventana
MIN_PARES_SESGO = 30         # pares mínimos (en 2025) para aprender el sesgo de una celda
ANIO_ENTRENA, ANIO_EVALUA = 2025, 2026

# Estaciones que representan cada zona de evento (aeródromos más cercanos).
ZONAS = {"coquimbo-jul": ["SCSE", "SCAT"], "centrosur-ago": ["SCQP", "SCTC", "SCGE", "SCCH", "SCIE"], "lascondes-oct": ["SCEL", "SCSN"]}
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
    o = obs[["icao", "time", "temp_c"]].sort_values("time")
    pares = pd.merge_asof(p, o, left_on="valid", right_on="time", by="icao", tolerance=pd.Timedelta("31min"), direction="nearest")
    pares = pares.rename(columns={"temp_c": "t_obs"})
    pares["t_err"] = pares.t_fc - pares.t_obs
    horas, n_rep = lluvia_observada(pares, obs)
    pares["horas_lluvia_obs"] = horas; pares["n_rep_24h"] = n_rep
    pares["lluvia_obs"] = np.where(n_rep >= MIN_REPORTES_24H, horas >= 1, np.nan)
    pares["lluvia_fc"] = np.where(pares.tp24_fc.notna(), pares.tp24_fc >= UMBRAL_LLUVIA_MM, np.nan)
    pares["anio"] = pares.valid.dt.year; pares["mes"] = pares.valid.dt.strftime("%Y-%m"); pares["hora_run"] = pares.run.dt.hour
    return pares.drop(columns=["time"])


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
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()
    filas = []
    for e in ev.itertuples(index=False):
        ests = ZONAS.get(e.id, [])
        for dia in pd.date_range(e.inicio, e.fin, freq="D"):
            valid = dia + pd.Timedelta(hours=12)
            sel = pares[(pares.icao.isin(ests)) & (pares.valid == valid)]
            for r in sel.itertuples(index=False):
                filas.append(dict(evento=e.id, zona=e.zona, dia=dia.date(), icao=r.icao, modelo=r.modelo, lead_h=r.lead_h,
                                  tp24_fc=r.tp24_fc, t_fc=r.t_fc, t_obs=r.t_obs, horas_lluvia_obs=r.horas_lluvia_obs,
                                  n_rep_24h=r.n_rep_24h, lluvia_obs=r.lluvia_obs))
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
    for k, df in r.items():
        df.to_csv(os.path.join(RES, f"{k}.csv"), index=False)
    print(r["plazos"].round(2).to_string(index=False))
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
