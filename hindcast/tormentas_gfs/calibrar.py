"""Mide el indicador de tormentas a 72 h contra los rayos del satélite (salidas de prueba_rayos.py) y busca cortes mejores.

Verdad: hubo tormenta si el GLM vio al menos 3 rayos a menos de 25 km de la comuna (un rayo suelto puede ser ruido del
sensor). Se mide por bloque de 3 h y por día-comuna (de 12 UTC a 12 UTC: la tarde y la noche de un día de Chile).

Cortes: se prueban combinaciones de CAPE, CIN y lluvia prevista **solo con los días impares** y se elige la que da el
mayor índice de acierto (CSI = aciertos / (aciertos + falsas alarmas + no anticipadas)); después se mide **con los días
pares**, que no se usaron para elegir. Así el número publicado no está inflado por la elección. El nivel 2 (tormentas
fuertes) no se calibra con rayos, porque los rayos no dicen si hubo granizo, rachas o tornado: se mantiene el criterio
publicado de cizalle sobre el nivel 1 nuevo.

Escribe en esta carpeta: rayos_resumen.csv (cortes actuales y elegidos, en días impares y pares), rayos_cortes.csv (todas las
combinaciones en días impares) y rayos_por_mes.csv.
Uso: python hindcast/tormentas_gfs/calibrar.py salida/"""
import glob, itertools, os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
MIN_RAYOS = 3
ACTUAL = {"cape": 100.0, "cin": -50.0, "lluvia": 0.1}
CAPES = [50, 100, 150, 200, 300, 400, 500, 750]
CINS = [-1000, -100, -50, -25, -10]
LLUVIAS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]


def leer(carpeta):
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(carpeta, "rayos_*.csv.gz")))], ignore_index=True)
    d["obs"] = d.rayos25 >= MIN_RAYOS
    d["impar"] = pd.to_datetime(d.dia).dt.day % 2 == 1
    return d


def marca(d, c):
    return (d.cape >= c["cape"]) & (d.cin >= c["cin"]) & (d.lluvia_mmh >= c["lluvia"])


def puntaje(si, obs):
    a = int((si & obs).sum()); fa = int((si & ~obs).sum()); no = int((~si & obs).sum())
    return {"marcados_pct": round(100 * si.mean(), 1), "tormentas_pct": round(100 * obs.mean(), 1), "aciertos": a, "falsas_alarmas": fa,
            "no_anticipadas": no, "detecta_pct": round(100 * a / max(a + no, 1)), "falsa_alarma_pct": round(100 * fa / max(a + fa, 1)),
            "csi": round(a / max(a + fa + no, 1), 3), "sesgo": round((a + fa) / max(a + no, 1), 2)}


def por_dia(d, si):
    g = d.assign(si=si).groupby(["id", "dia"]).agg(si=("si", "any"), obs=("obs", "any"), impar=("impar", "first"))
    return g


def main(carpeta):
    d = leer(carpeta)
    print(f"{d.dia.nunique()} días, {d.id.nunique()} comunas, {len(d):,} bloques; con tormenta: {100 * d.obs.mean():.1f} %")
    filas = []
    for c, cc, ll in itertools.product(CAPES, CINS, LLUVIAS):
        corte = {"cape": c, "cin": cc, "lluvia": ll}
        g = por_dia(d, marca(d, corte))
        filas.append({**corte, **puntaje(g.si[g.impar], g.obs[g.impar])})
    cortes = pd.DataFrame(filas).sort_values("csi", ascending=False)
    cortes.to_csv(os.path.join(AQUI, "rayos_cortes.csv"), index=False)
    mejor = cortes.iloc[0][["cape", "cin", "lluvia"]].to_dict()
    res = []
    for nombre, corte in (("actual", ACTUAL), ("elegido", mejor)):
        si = marca(d, corte); g = por_dia(d, si)
        for mitad, m_b, m_d in (("impares (para elegir)", d.impar, g.impar), ("pares (prueba)", ~d.impar, ~g.impar)):
            res.append({"cortes": nombre, **corte, "dias": mitad, "escala": "bloque de 3 h", **puntaje(si[m_b], d.obs[m_b])})
            res.append({"cortes": nombre, **corte, "dias": mitad, "escala": "día", **puntaje(g.si[m_d], g.obs[m_d])})
    res = pd.DataFrame(res)
    res.to_csv(os.path.join(AQUI, "rayos_resumen.csv"), index=False)
    si = marca(d, mejor); g = por_dia(d, si).reset_index(); g["mes"] = g.dia.str[:7]
    pm = pd.DataFrame([{"mes": m, **puntaje(x.si, x.obs)} for m, x in g.groupby("mes")])
    pm.to_csv(os.path.join(AQUI, "rayos_por_mes.csv"), index=False)
    print(res.to_string(index=False)); print(pm.to_string(index=False))
    print("\nmejores cortes (días impares):"); print(cortes.head(10).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
