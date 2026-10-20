"""Lluvia de 24 h pronosticada por AIFS, IFS y GFS en cada aeródromo frente a los milímetros medidos por la estación
SYNOP de la DMC en el mismo lugar (los METAR chilenos no informan milímetros).

Pareja de cada aeródromo: la estación SYNOP que transmite lluvia más cercana, a menos de RADIO_KM y con menos de
DESNIVEL_M de diferencia de altura (casi siempre la del mismo aeródromo, a menos de 1 km), salvo las de EXCLUIDAS.
Sin pareja, no se compara.

Lluvia medida en 24 h: los cuatro bloques de 6 h que terminan en la hora válida; cada bloque es el total de 6 h que
informan las estaciones con observador o la suma de las 6 lluvias horarias (estaciones/verificar_lluvia.py). Si falta
un bloque, ese día no se compara. Lluvia pronosticada: acumulado al plazo menos acumulado 24 h antes, en el punto de
grilla más cercano. Fuentes del pronóstico: data/pronostico_puntos.csv (columna tp_fc, pipeline diario) y
historico/data/pronosticos.csv.gz (corridas de 00 y 12 UTC desde el 1-oct-2026, cuando empiezan los SYNOP).

Escribe data/verif_lluvia.csv (se acumula: los pronósticos diarios se podan a los 4 días). Un día cuenta como
lluvioso desde UMBRAL mm. Para el sitio, un "día" es la lluvia de las 12 UTC a las 12 UTC (9 de la mañana en hora
de verano) pronosticada a 24 h por la corrida de 12 UTC del día anterior: una comparación por día, sin solapes.
Uso: python lluvia.py   (también lo llama verify.py)"""
import csv, math, os, sys
import datetime as dt
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTACIONES = os.path.join(AQUI, "..", "estaciones")
sys.path.insert(0, ESTACIONES)
import synop                                       # noqa: E402
from verificar_lluvia import observado, km         # noqa: E402

AERODROMOS = os.path.join(AQUI, "..", "historico", "estaciones.csv")
HIST = os.path.join(AQUI, "..", "historico", "data", "pronosticos.csv.gz")
PRON = os.path.join(AQUI, "data", "pronostico_puntos.csv")
SALIDA = os.path.join(AQUI, "data", "verif_lluvia.csv")
CLAVE = ["modelo", "run", "lead_h", "icao"]
RADIO_KM, DESNIVEL_M = 15, 150
UMBRAL = 1.0
# Pluviómetros que no se usan, con el motivo (se muestra en Método).
EXCLUIDAS = {"85565": "entre el 6 y el 7 de octubre de 2026 midió 11 mm, cuando las demás estaciones del valle de Santiago midieron "
                      "de 45 a 75 mm, y durante ese temporal su lluvia horaria fue bajando de a una décima: se excluye hasta revisarlo"}
DESDE = "2026-09-30"                               # los SYNOP guardados empiezan el 1-oct-2026
UTC = dt.timezone.utc


def parejas(obs=None):
    """{icao: {wmo, estacion, km, altura_m, elev}} con la estación SYNOP que le corresponde a cada aeródromo."""
    est = synop.estaciones()
    if obs is None:
        obs = leer_obs(est)
    transmiten = {w for w, o in obs.items() if any(r["mm_1h"] != "" or r["mm_6h"] != "" for r in o.values())}
    out = {}
    for a in csv.DictReader(open(AERODROMOS, encoding="utf-8")):
        p, elev = (float(a["lat"]), float(a["lon"])), float(a["elev"] or 0)
        cand = sorted((km(p, (float(e["lat"]), float(e["lon"]))), w) for w, e in est.items()
                      if w in transmiten and w not in EXCLUIDAS and abs(float(e["altura_m"] or 0) - elev) < DESNIVEL_M)
        if cand and cand[0][0] < RADIO_KM:
            d, w = cand[0]
            out[a["icao"]] = {"wmo": w, "estacion": est[w]["nombre"], "km": round(d, 1), "altura_m": int(float(est[w]["altura_m"])), "elev": int(elev)}
    return out


def leer_obs(est=None):
    est = est or synop.estaciones()
    obs = {}
    for r in synop.leer(set(est)):
        obs.setdefault(r["wmo"], {})[dt.datetime.strptime(r["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)] = r
    return obs


def medido_24h(obs, wmo, fin):
    """mm en las 24 h que terminan en fin (UTC), o None si falta alguno de los cuatro bloques de 6 h."""
    bloques = [observado(obs, wmo, fin - dt.timedelta(hours=6 * k)) for k in range(4)]
    return None if any(b is None for b in bloques) else round(sum(bloques), 1)


def pronosticos():
    """Acumulados por (modelo, corrida, estación) desde el pipeline diario y el histórico -> lluvia de 24 h por plazo."""
    partes = []
    if os.path.exists(HIST):
        h = pd.read_csv(HIST, usecols=["modelo", "run", "lead_h", "icao", "tp_fc"])
        partes.append(h[h.run >= DESDE])
    if os.path.exists(PRON):
        p = pd.read_csv(PRON)
        if "tp_fc" in p.columns:
            partes.append(p[["modelo", "run", "lead_h", "icao", "tp_fc"]])
    if not partes:
        return pd.DataFrame(columns=CLAVE + ["mm_fc"])
    a = pd.concat(partes).dropna(subset=["tp_fc"]).drop_duplicates(subset=CLAVE, keep="last")
    a["run"] = pd.to_datetime(a.run)
    prev = a.assign(lead_h=a.lead_h + 24)[CLAVE + ["tp_fc"]].rename(columns={"tp_fc": "tp_prev"})
    a = a.merge(prev, on=CLAVE, how="left")
    a.loc[a.lead_h == 24, "tp_prev"] = 0.0          # el acumulado parte en cero al inicio de la corrida
    a = a.dropna(subset=["tp_prev"])
    a["mm_fc"] = (a.tp_fc - a.tp_prev).clip(lower=0).round(1)
    return a[CLAVE + ["mm_fc"]]


def verificar():
    """Empareja pronóstico y medición y acumula data/verif_lluvia.csv. Devuelve la tabla completa."""
    est = synop.estaciones()
    obs = leer_obs(est)
    par = parejas(obs)
    pr = pronosticos()
    pr = pr[pr.icao.isin(par)]
    filas = []
    for r in pr.itertuples(index=False):
        valid = r.run + pd.Timedelta(hours=int(r.lead_h))
        p = par[r.icao]
        mo = medido_24h(obs, p["wmo"], valid.to_pydatetime().replace(tzinfo=UTC))
        if mo is not None:
            filas.append({"modelo": r.modelo, "run": r.run, "lead_h": int(r.lead_h), "valid": valid, "icao": r.icao,
                          "wmo": p["wmo"], "estacion": p["estacion"], "km": p["km"], "mm_fc": r.mm_fc, "mm_obs": mo})
    nuevo = pd.DataFrame(filas, columns=["modelo", "run", "lead_h", "valid", "icao", "wmo", "estacion", "km", "mm_fc", "mm_obs"])
    if os.path.exists(SALIDA):
        nuevo = pd.concat([pd.read_csv(SALIDA, parse_dates=["run", "valid"], dtype={"wmo": str}), nuevo])
    nuevo["run"] = pd.to_datetime(nuevo.run); nuevo["valid"] = pd.to_datetime(nuevo.valid)
    out = nuevo.drop_duplicates(subset=CLAVE, keep="last").sort_values(["valid", "modelo", "icao"])
    out.to_csv(SALIDA, index=False)
    print(f"lluvia: {len(out)} comparaciones de 24 h ({len(par)} aeródromos con estación SYNOP; "
          f"{(out.mm_obs >= UMBRAL).sum()} con lluvia medida) en {os.path.relpath(SALIDA)}")
    return out


def dias(v=None):
    """Una comparación por día: corrida de 12 UTC a 24 h (lluvia de 12 a 12 UTC)."""
    if v is None:
        try:
            v = pd.read_csv(SALIDA, parse_dates=["run", "valid"], dtype={"wmo": str})
        except Exception:
            return pd.DataFrame()
    return v[(v.lead_h == 24) & (v.run.dt.hour == 12)].copy()


def cuentas(g):
    """Tabla de aciertos y errores de un grupo de días."""
    llovio, aviso = g.mm_obs >= UMBRAL, g.mm_fc >= UMBRAL
    err = g.mm_fc - g.mm_obs
    return {"n": int(len(g)), "llovio": int(llovio.sum()), "avisados": int((llovio & aviso).sum()),
            "falsas": int((~llovio & aviso).sum()), "aciertos": int((llovio == aviso).sum()),
            "mae": round(float(err.abs().mean()), 2) if len(g) else None,
            "mae_lluvia": round(float(err[llovio].abs().mean()), 2) if llovio.any() else None,
            "medido": round(float(g.mm_obs.sum()), 1), "pronosticado": round(float(g.mm_fc.sum()), 1)}


if __name__ == "__main__":
    os.chdir(AQUI)
    v = verificar()
    for m, g in dias(v).groupby("modelo"):
        print(m, cuentas(g))
