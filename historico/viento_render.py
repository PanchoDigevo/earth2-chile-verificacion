"""Piezas de viento para las páginas Eventos y Método (capa estándar 4). Lee historico/data/resultados/viento_*.csv,
rachas_*.csv y eventos_viento.csv, y oceano/data/correccion_movil_total_viento.csv. Todo en km/h para el lector."""
import os
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(AQUI, "data", "resultados")
OCE = os.path.join(AQUI, "..", "oceano", "data")
ORDEN = ["AIFS", "IFS", "GFS"]
KMH = 3.6


def leer(ruta):
    try:
        return pd.read_csv(ruta)
    except Exception:
        return pd.DataFrame()


def ordenar(df):
    if df.empty or "modelo" not in df:
        return df
    df = df.copy(); df["_o"] = df.modelo.map({m: i for i, m in enumerate(ORDEN)})
    return df.sort_values(["_o"] + [c for c in ("lead_h",) if c in df]).drop(columns="_o")


def bloque_evento(ev, num, titulo="¿Y el viento?"):
    """Tabla compacta: viento y ráfaga máximos pronosticados vs. observados en los aeródromos de la zona, por anticipación."""
    v = leer(os.path.join(RES, "eventos_viento.csv"))
    if v.empty or "evento" not in v:
        return ""
    v = v[v.evento == ev]
    if v.empty or v.w_fc_max.isna().all():
        return ""
    obs_w, obs_g = v.w_obs_max.max(), v.g_obs_max.max()
    filas = []
    for m in ORDEN:
        celdas = []
        for l in (72, 48, 24):
            x = v[(v.modelo == m) & (v.lead_h == l)]
            if x.empty:
                celdas.append("<td class='num'>–</td>"); continue
            w, g = x.w_fc_max.iloc[0], x.g_fc_max.iloc[0]
            celdas.append(f"<td class='num'>{num(w * KMH, 0)}{'' if pd.isna(g) else f' / {num(g * KMH, 0)}'}</td>")
        filas.append(f"<tr><td class='l'>{m}</td>{''.join(celdas)}</tr>")
    return (f"<h3>{titulo}</h3><p class='small muted'>Viento máximo pronosticado / ráfaga máxima pronosticada en los aeródromos de la zona "
            f"(km/h, a las 21 y a las 9 de cada día). Observado: viento de hasta {num(obs_w * KMH, 0)} km/h y ráfagas de hasta "
            f"{num(obs_g * KMH, 0)} km/h. AIFS no publica ráfagas.</p>"
            "<div class='tabla'><table class='matriz'><thead><tr><th class='l'>Modelo</th><th>72 h antes</th><th>48 h antes</th><th>24 h antes</th></tr></thead>"
            f"<tbody>{''.join(filas)}</tbody></table></div>")


def seccion_metodo(tabla, num, entero, signo, d):
    vp = ordenar(leer(os.path.join(RES, "viento_plazos.csv")))
    if vp.empty:
        return ""
    f_vp = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{entero(x.n)}</td>"
            f"<td class='num'>{num(x.w_mae * KMH, 1, ' km/h')}</td><td class='num'>{signo(x.w_sesgo * KMH, 1, ' km/h')}</td>"
            f"<td class='num'>{num(x.d_mae, 0, '°')}</td><td class='num'>{'–' if pd.isna(x.g_mae) else num(x.g_mae * KMH, 1, ' km/h')}</td></tr>"
            for x in vp.itertuples(index=False)]
    ep = ordenar(leer(os.path.join(RES, "rachas_episodios.csv")))
    f_ep = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{entero(x.episodios)}</td>"
            f"<td class='num'>{entero(x.anticipados)} ({num(100 * x.pod, 0)} %)</td><td class='num'>{entero(x.en_falso)}</td></tr>"
            for x in ep.itertuples(index=False)] if not ep.empty else []
    mt = ordenar(leer(os.path.join(OCE, "correccion_movil_total_viento.csv")))
    f_mt = [f"<tr><td class='l'>{x.modelo}</td><td class='num'>{int(x.lead_h)} h</td><td class='num'>{num(x.mae_sin * KMH, 1)}</td>"
            f"<td class='num'>{num(x.mae_fija * KMH, 1)}</td><td class='num'>{num(x.mae_movil * KMH, 1)}</td></tr>"
            for x in mt.itertuples(index=False)] if not mt.empty else []
    ve = leer(os.path.join(RES, "viento_estaciones.csv"))
    extra = ""
    if not ve.empty:
        a = ve[(ve.modelo == "AIFS") & (ve.lead_h == 24)].sort_values("w_mae", ascending=False).head(3)
        extra = "Donde más se equivoca la IA con el viento a 24 h: " + ", ".join(f"{r.icao} ({num(r.w_mae * KMH, 0)} km/h)" for r in a.itertuples(index=False)) + "."
    return f"""<section class="card">
  <div class="sec-head"><h2>Viento</h2>
  <p class="muted">Velocidad del viento a 10 m (promedio de 10 minutos), dirección y ráfagas, en 2025 y 2026, con las mismas estaciones y horas que la temperatura. AIFS no publica ráfagas; IFS publica la ráfaga máxima de las 6 horas previas y GFS una ráfaga instantánea. La dirección se evalúa solo con viento observado de 7 km/h o más. {extra}</p></div>
  {tabla(["Modelo", "Plazo", "Comparaciones", "Error medio velocidad", "Sesgo velocidad", "Error medio dirección", "Error medio ráfaga"], f_vp)}
  <h3>Episodios de viento fuerte</h3>
  <p class="small muted">Ventanas de 6 horas con ráfaga observada de más de 50 km/h en algún aeródromo, y cuántas anticipó cada modelo con su ráfaga pronosticada.</p>
  {tabla(["Modelo", "Anticipación", "Episodios", "Anticipados", "Avisos en falso"], f_ep) if f_ep else "<p class='small muted'>Sin datos de ráfagas todavía.</p>"}
  {('<details><summary>Corrección fija o móvil del viento</summary><div class="body">' + tabla(["Modelo", "Plazo", "Sin corregir (km/h)", "Corrección 2025", "Corrección 45 días"], f_mt) + '</div></details>') if f_mt else ''}
</section>"""
