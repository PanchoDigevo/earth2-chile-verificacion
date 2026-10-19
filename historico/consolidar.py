"""Junta los CSV parciales de data/puntos/ en data/pronosticos.csv.gz, sin duplicar (modelo, run, lead_h, icao)."""
import glob, os
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "data", "pronosticos.csv.gz")
CLAVE = ["modelo", "run", "lead_h", "icao"]

partes = []
if os.path.exists(SALIDA):            # lo anterior primero: las filas nuevas (p. ej. con viento) reemplazan a las viejas
    partes.append(pd.read_csv(SALIDA))
for f in sorted(glob.glob(os.path.join(AQUI, "data", "puntos", "*.csv"))):
    try:
        partes.append(pd.read_csv(f))
    except pd.errors.EmptyDataError:
        print("vacío, se omite:", os.path.basename(f))
if not partes:
    raise SystemExit("nada que consolidar")
df = pd.concat(partes, ignore_index=True).drop_duplicates(subset=CLAVE, keep="last")
df = df.sort_values(["modelo", "run", "lead_h", "icao"])
df.to_csv(SALIDA, index=False, compression="gzip")
print(f"pronosticos.csv.gz: {len(df)} filas, modelos {sorted(df.modelo.unique())}, corridas {df.run.min()} a {df.run.max()}")
