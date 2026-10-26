"""Junta las salidas de prueba_dia.py: agrupa los saltos de una misma tormenta (a menos de 40 km y 30 minutos del anterior)
en un solo aviso, le pone la comuna más cercana y escribe avisos.csv y resumen.csv en esta carpeta.

Cada aviso queda con la columna "que_paso" vacía: se llena a mano con lo que informen SENAPRED, la DMC o la prensa
(granizo, rachas, tornado, nada). Con eso se calcula cuántos avisos tuvieron daño y cuántos fueron falsa alarma.

Uso: python hindcast/salto_rayos/juntar.py salida/"""
import datetime as dt, glob, json, os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "envivo"))
from salto_rayos import km  # noqa: E402


def main(d):
    com = pd.read_csv(os.path.join(AQUI, "..", "..", "verificacion", "comunas.csv"))
    res = pd.DataFrame([json.load(open(f)) for f in sorted(glob.glob(os.path.join(d, "resumen_*.json")))])
    s = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(d, "saltos_*.csv")))], ignore_index=True)
    s["t"] = pd.to_datetime(s.hora_utc)
    s = s.sort_values("t").reset_index(drop=True)
    avisos = []                                           # cada uno: dict con primer y último salto
    for _, r in s.iterrows():
        p = (r.lat, r.lon)
        for a in avisos:
            if (r.t - a["ultimo"]) <= pd.Timedelta(minutes=30) and km(p, a["pos"]) <= 40:
                a["ultimo"] = r.t; a["pos"] = p; a["saltos"] += 1; a["tasa_max"] = max(a["tasa_max"], r.tasa_por_min)
                break
        else:
            avisos.append({"inicio": r.t, "ultimo": r.t, "pos0": p, "pos": p, "saltos": 1, "tasa_max": r.tasa_por_min})
    filas = []
    for a in avisos:
        dist = np.array([km(a["pos0"], (la, lo)) for la, lo in zip(com.lat, com.lon)])
        c = com.iloc[int(dist.argmin())]
        filas.append({"inicio_utc": a["inicio"].strftime("%Y-%m-%d %H:%M"),
                      "hora_chile": (a["inicio"] - pd.Timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                      "lat": a["pos0"][0], "lon": a["pos0"][1], "comuna_cercana": c.nombre, "region": c.region,
                      "km_a_comuna": round(float(dist.min())), "saltos": a["saltos"], "tasa_max_por_min": a["tasa_max"],
                      "que_paso": ""})
    av = pd.DataFrame(filas)
    previo = os.path.join(AQUI, "avisos.csv")
    if os.path.exists(previo):                            # no pisar lo anotado a mano
        old = pd.read_csv(previo, dtype=str).fillna("")
        nota = dict(zip(old.inicio_utc + old.comuna_cercana, old.que_paso))
        av["que_paso"] = [nota.get(i + c, "") for i, c in zip(av.inicio_utc, av.comuna_cercana)]
    av.to_csv(previo, index=False)
    av["dia"] = av.inicio_utc.str[:10]
    res = res.merge(av.groupby("dia").size().rename("avisos").reset_index(), on="dia", how="left").fillna({"avisos": 0})
    res["avisos"] = res.avisos.astype(int)
    res.to_csv(os.path.join(AQUI, "resumen.csv"), index=False)
    print(res.to_string(index=False))
    print(f"\n{len(av)} avisos en {len(res)} días; días con al menos uno: {(res.avisos > 0).sum()}")


if __name__ == "__main__":
    main(sys.argv[1])
