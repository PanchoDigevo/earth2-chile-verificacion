"""Deriva y corrección móvil (capa estándar 5), desde los pares pronóstico-observación.

- Corrección fija: sesgo medio de 2025 por aeródromo, modelo, plazo y hora de corrida (la misma del Resumen).
- Corrección móvil: sesgo medio de los últimos 45 días, calculado para cada pronóstico solo con observaciones
  anteriores a la hora en que se emitió (sin mirar el futuro).
- Deriva: el error que queda después de la corrección fija, promediado en 30 días. Si pasa de ±1 °C con al menos
  20 comparaciones, el aeródromo está "en deriva": su error típico ya no es el que se aprendió en 2025.
- Cruce con el mar: para los aeródromos de la costa, la anomalía media de 30 días de su caja costera (oceano/data/sst_cajas.csv)
  y la correlación entre ambas series en 2026.

Pares: historico/data (2025 hasta mediados de oct-2026, corridas 00 y 12 UTC) + verificacion/data/verif_puntos.csv
(pipeline diario, solo corridas 00 y 12 UTC para que la serie sea homogénea).
Salidas en oceano/data/: correccion_movil.csv, deriva_estado.csv, deriva_serie.csv.
Uso: python oceano/deriva.py [--variable t|w]   (t = temperatura, por defecto; w = velocidad del viento)"""
import argparse, os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")
HIST = os.path.join(AQUI, "..", "historico")
DIARIO = os.path.join(AQUI, "..", "verificacion", "data", "verif_puntos.csv")
sys.path.insert(0, HIST)

ANIO_FIJO = 2025
VENTANA_MOVIL, MIN_MOVIL = 45, 10
VENTANA_DERIVA, MIN_DERIVA = 30, 20
UMBRAL_DERIVA = {"t": 1.0, "w": 1.5}          # °C para temperatura, m/s para viento
CLAVE = ["modelo", "icao", "lead_h", "hora_run"]
CAJA = {"SCAR": "SCAR", "SCDA": "SCDA", "SCFA": "SCFA", "SCAT": "SCAT", "SCSE": "SCSE", "SCSN": "SCSN", "SCIE": "SCIE", "SCTE": "SCTE"}


def pares(variable="t"):
    import analizar as an
    pron, obs = an.cargar()
    p = an.emparejar(pron, obs)
    err, fc, ob = f"{variable}_err", f"{variable}_fc", f"{variable}_obs"
    if err not in p:
        raise SystemExit(f"los pares históricos no tienen {err}")
    p = p.dropna(subset=[err])[["modelo", "run", "lead_h", "valid", "icao", fc, ob, err]]
    if os.path.exists(DIARIO):
        v = pd.read_csv(DIARIO, parse_dates=["run", "valid"])
        if "modelo" not in v:
            v.insert(0, "modelo", "AIFS")
        v = v[(v.run.dt.hour.isin([0, 12])) & (v.lead_h.isin([24, 48, 72])) & (v.run > p.run.max())]
        if err in v:
            p = pd.concat([p, v.dropna(subset=[err])[p.columns]], ignore_index=True)
    for c in ("run", "valid"):
        p[c] = pd.to_datetime(p[c]).astype("datetime64[ns]")
    p["hora_run"] = p.run.dt.hour
    return p.sort_values(["valid"]).reset_index(drop=True), err


def sesgo_fijo(p, err):
    e = p[p.run.dt.year == ANIO_FIJO].groupby(CLAVE)[err].agg(n_fijo="size", sesgo_fijo="mean").reset_index()
    e = e[e.n_fijo >= 30]
    return p.merge(e, on=CLAVE, how="left")


def sesgo_movil(p, err):
    """Para cada pronóstico (emitido en 'run'), media del error de su grupo con observación en [run − 45 d, run)."""
    mov = np.full(len(p), np.nan); nmov = np.zeros(len(p), dtype=int)
    ventana = np.int64(VENTANA_MOVIL * 86400 * 10 ** 9)
    for _, g in p.groupby(CLAVE, sort=False):
        idx = g.index.values
        v = g.valid.values.astype("int64"); e = g[err].values
        o = np.argsort(v, kind="stable"); vs, es = v[o], e[o]
        cs = np.concatenate([[0.0], np.cumsum(es)])
        r = g.run.values.astype("int64")
        hi = np.searchsorted(vs, r, side="left"); lo = np.searchsorted(vs, r - ventana, side="left")
        n = hi - lo
        with np.errstate(invalid="ignore", divide="ignore"):
            m = (cs[hi] - cs[lo]) / n
        ok = n >= MIN_MOVIL
        mov[idx[ok]] = m[ok]; nmov[idx] = n
    p = p.copy(); p["sesgo_movil"] = mov; p["n_movil"] = nmov
    return p


def evaluar(p, err):
    """MAE sin corregir, con corrección fija y con móvil, en el año siguiente al de la fija, mismas filas para las tres."""
    e = p[(p.run.dt.year > ANIO_FIJO) & p.sesgo_fijo.notna() & p.sesgo_movil.notna()].copy()
    e["e_fija"] = e[err] - e.sesgo_fijo; e["e_movil"] = e[err] - e.sesgo_movil
    mae = lambda s: s.abs().mean()
    porest = e.groupby(["modelo", "lead_h", "icao"]).agg(n=(err, "size"), mae_sin=(err, mae), mae_fija=("e_fija", mae), mae_movil=("e_movil", mae)).reset_index()
    dif = porest.mae_fija - porest.mae_movil
    porest["gana"] = np.where(dif > 0.05, "móvil", np.where(dif < -0.05, "fija", "empate"))
    total = e.groupby(["modelo", "lead_h"]).agg(n=(err, "size"), mae_sin=(err, mae), mae_fija=("e_fija", mae), mae_movil=("e_movil", mae)).reset_index()
    return porest, total


def deriva(p, err, variable):
    """Serie diaria del error residual (después de la corrección fija) promediado en 30 días, a 24 h."""
    r = p[(p.lead_h == 24) & p.sesgo_fijo.notna() & (p.run.dt.year > ANIO_FIJO)].copy()
    r["res"] = r[err] - r.sesgo_fijo
    r["fecha"] = r.valid.dt.normalize()
    d = r.groupby(["modelo", "icao", "fecha"]).res.agg(["sum", "count"]).reset_index()
    filas = []
    for (m, i), g in d.groupby(["modelo", "icao"]):
        g = g.set_index("fecha").asfreq("D").fillna({"sum": 0, "count": 0})
        s = g["sum"].rolling(f"{VENTANA_DERIVA}D").sum(); c = g["count"].rolling(f"{VENTANA_DERIVA}D").sum()
        x = pd.DataFrame({"modelo": m, "icao": i, "fecha": g.index, "res30": (s / c.replace(0, np.nan)).values, "n30": c.values.astype(int)})
        filas.append(x)
    serie = pd.concat(filas, ignore_index=True)
    serie["deriva"] = (serie.res30.abs() >= UMBRAL_DERIVA[variable]) & (serie.n30 >= MIN_DERIVA)
    return serie


def cruce_mar(serie):
    ruta = os.path.join(DATA, "sst_cajas.csv")
    if not os.path.exists(ruta):
        return serie.assign(sst_anom30=np.nan), {}
    s = pd.read_csv(ruta, parse_dates=["fecha"])
    s = s[s.caja.isin(CAJA.values())].pivot_table(index="fecha", columns="caja", values="anom").sort_index().asfreq("D")
    s30 = s.rolling("30D", min_periods=15).mean()
    # el satélite llega con 1 a 2 días de retraso: se arrastra el último valor hasta 5 días para cruzar con la deriva de hoy
    s30 = s30.reindex(pd.date_range(s30.index.min(), max(s30.index.max(), serie.fecha.max()), freq="D")).ffill(limit=5)
    out = serie.copy(); out["sst_anom30"] = np.nan
    corr = {}
    for icao, caja in CAJA.items():
        if caja not in s30:
            continue
        m = out.icao == icao
        out.loc[m, "sst_anom30"] = s30[caja].reindex(out.loc[m, "fecha"]).values
        for mod in out.modelo.unique():
            x = out[m & (out.modelo == mod)].dropna(subset=["res30", "sst_anom30"])
            if len(x) >= 90:
                corr[(mod, icao)] = round(float(np.corrcoef(x.res30, x.sst_anom30)[0, 1]), 2)
    return out, corr


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--variable", default="t", choices=["t", "w"])
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    suf = "" if a.variable == "t" else "_viento"
    p, err = pares(a.variable)
    p = sesgo_movil(sesgo_fijo(p, err), err)
    porest, total = evaluar(p, err)
    porest.to_csv(os.path.join(DATA, f"correccion_movil{suf}.csv"), index=False)
    total.to_csv(os.path.join(DATA, f"correccion_movil_total{suf}.csv"), index=False)
    serie, corr = cruce_mar(deriva(p, err, a.variable))
    serie.to_csv(os.path.join(DATA, f"deriva_serie{suf}.csv"), index=False, float_format="%.3f")
    estado = serie.dropna(subset=["res30"]).sort_values("fecha").groupby(["modelo", "icao"]).tail(1).copy()
    estado["corr_sst"] = [corr.get((m, i)) for m, i in zip(estado.modelo, estado.icao)]
    estado.to_csv(os.path.join(DATA, f"deriva_estado{suf}.csv"), index=False, float_format="%.3f")
    print(f"pares: {len(p)} ({p.run.min():%Y-%m-%d} a {p.run.max():%Y-%m-%d}); variable {a.variable}")
    print(total.round(2).to_string(index=False))
    en = estado[estado.deriva]
    print(f"en deriva al {estado.fecha.max():%Y-%m-%d}: {len(en)} de {len(estado)} combinaciones modelo-aeródromo")
    if len(en):
        print(en[["modelo", "icao", "res30", "n30", "sst_anom30", "corr_sst"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
