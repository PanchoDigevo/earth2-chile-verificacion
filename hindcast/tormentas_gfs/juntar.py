"""Junta las pruebas mensuales del indicador de tormentas (prueba_mes.py) y calcula, por nivel, cuántas tormentas
informadas por los METAR anticipó (acierto) y cuántas veces marcó sin que hubiera tormenta (falsa alarma).

Se mide de dos formas: por bloque de 3 h en cada aeródromo y por día en cada aeródromo (marcó en algún bloque de la tarde y
noche / hubo tormenta en alguno). Escribe resumen.csv y pares.csv (sin las filas sin METAR) en esta carpeta.
Uso: python hindcast/tormentas_gfs/juntar.py salida/"""
import glob, os, sys
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))


def tabla(d, nombre):
    out = []
    for n in (1, 2):
        si = d.nivel >= n
        a, fa, pe = int((si & d.ts).sum()), int((si & ~d.ts).sum()), int((~si & d.ts).sum())
        out.append({"escala": nombre, "nivel": n, "casos": len(d), "tormentas_metar": int(d.ts.sum()), "marcados": int(si.sum()),
                    "aciertos": a, "falsas_alarmas": fa, "no_marcadas": pe,
                    "detecta_pct": round(100 * a / max(a + pe, 1)), "falsa_alarma_pct": round(100 * fa / max(a + fa, 1)),
                    "frecuencia_base_pct": round(100 * d.ts.mean(), 1)})
    return out


def main(carpeta):
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(carpeta, "prueba_*.csv")))], ignore_index=True)
    d = d[d.metar > 0].copy()
    d["ts"] = d.ts.astype(bool)
    d["valid"] = pd.to_datetime(d.valid)
    d["dia"] = (d.valid - pd.Timedelta(hours=12)).dt.date          # de 12 UTC a 12 UTC: la tarde y noche de un día de Chile
    por_dia = d.groupby(["id", "dia"]).agg(nivel=("nivel", "max"), ts=("ts", "any")).reset_index()
    res = pd.DataFrame(tabla(d, "bloque de 3 h") + tabla(por_dia, "día"))
    res.to_csv(os.path.join(AQUI, "resumen.csv"), index=False)
    d.to_csv(os.path.join(AQUI, "pares.csv"), index=False, date_format="%Y-%m-%d %H:%M")
    print(res.to_string(index=False))
    print(f"\n{d.dia.nunique()} días, {d.id.nunique()} aeródromos, {len(d)} bloques con METAR")


if __name__ == "__main__":
    main(sys.argv[1])
