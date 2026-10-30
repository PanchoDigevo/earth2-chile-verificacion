"""Verificación retroactiva en la red de estaciones automáticas de la DMC, con el mismo método que los aeródromos
(analizar.py): pares de temperatura a la hora pronosticada (±31 min), error por estación, y corrección por estación
× modelo × plazo × hora de corrida aprendida SOLO con 2025 y evaluada SOLO en 2026. Suma el viento medio de 10 minutos.

Entradas (de historico-dmc.yml): data/puntos_dmc/*.csv (pronósticos de extraer_puntos.py --puntos estaciones_dmc.csv) y
data/dmc_obs/AAAA-MM.csv.gz (dmc_historico.py: 00, 06, 12 y 18 UTC). Salidas en data/resultados/:
  dmc_estaciones.csv              modelo, lead_h, icao, n, mae, sesgo                (2025-2026)
  dmc_correccion_estaciones.csv   modelo, lead_h, icao, n, mae_global, mae_corregido (2026)
  dmc_correccion_plazos.csv       igual, por modelo y plazo
  dmc_viento_estaciones.csv       modelo, lead_h, icao, n, w_mae, w_sesgo            (m/s)
Los pronósticos consolidados (data/pronosticos_dmc.csv.gz) quedan como artefacto del flujo, no en el repo (pesan); cada
corrida parte del consolidado anterior y le suma sus partes, así se pueden completar partes sueltas (input "solo").

Uso: python analizar_dmc.py"""
import glob, os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import analizar as A                                   # mismas funciones y umbrales que los aeródromos

DATA = os.path.join(AQUI, "data")
RES = os.path.join(DATA, "resultados")
CONSOLIDADO = os.path.join(DATA, "pronosticos_dmc.csv.gz")


def cargar():
    # lo consolidado de la corrida anterior primero y las partes nuevas después: en un duplicado gana lo nuevo
    partes = [pd.read_csv(CONSOLIDADO)] if os.path.exists(CONSOLIDADO) else []
    partes += [pd.read_csv(f) for f in sorted(glob.glob(os.path.join(DATA, "puntos_dmc", "*.csv")))]
    if not partes:
        sys.exit("sin pronósticos en data/puntos_dmc ni data/pronosticos_dmc.csv.gz")
    pron = pd.concat(partes, ignore_index=True).drop_duplicates(subset=["modelo", "run", "lead_h", "icao"], keep="last")
    pron.to_csv(CONSOLIDADO, index=False, compression="gzip")
    for c in ("run", "valid"):
        pron[c] = pd.to_datetime(pron[c], format="mixed").astype("datetime64[ns]")
    obs = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(DATA, "dmc_obs", "*.csv.gz")))], ignore_index=True)
    obs["time"] = pd.to_datetime(obs.time).astype("datetime64[ns]")
    obs = obs.dropna(subset=["temp_c"]).sort_values("time")
    return pron, obs


def main():
    os.makedirs(RES, exist_ok=True)
    pron, obs = cargar()
    p = pron.sort_values("valid")
    pares = pd.merge_asof(p, obs[["icao", "time", "temp_c", "viento_ms"]], left_on="valid", right_on="time", by="icao",
                          tolerance=pd.Timedelta("31min"), direction="nearest")
    pares["t_err"] = pares.t_fc - pares.temp_c
    pares["t_obs"] = pares.temp_c
    pares["w_fc"] = np.hypot(pares.u_fc, pares.v_fc)
    pares["w_err"] = pares.w_fc - pares.viento_ms
    pares["anio"] = pares.valid.dt.year; pares["hora_run"] = pares.run.dt.hour
    print(f"pares DMC: {len(pares)} ({pares.t_err.notna().sum()} con temperatura), {pares.icao.nunique()} estaciones, "
          f"{pares.valid.min():%Y-%m-%d} a {pares.valid.max():%Y-%m-%d}")
    r = {"dmc_estaciones": A.resumen_temp(pares, ["modelo", "lead_h", "icao"])}
    r["dmc_correccion_plazos"], r["dmc_correccion_estaciones"], _ = A.correccion(pares)
    v = pares.dropna(subset=["w_err"])
    r["dmc_viento_estaciones"] = v.groupby(["modelo", "lead_h", "icao"]).agg(
        n=("w_err", "size"), w_mae=("w_err", lambda e: e.abs().mean()), w_sesgo=("w_err", "mean")).reset_index()
    for k, df in r.items():
        df.to_csv(os.path.join(RES, f"{k}.csv"), index=False)
    if not r["dmc_correccion_plazos"].empty:
        print(r["dmc_correccion_plazos"].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
