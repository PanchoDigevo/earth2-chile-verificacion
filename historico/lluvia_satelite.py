"""Lluvia observada por satélite (mm) en las estaciones de cada evento, para los días de hindcast/eventos/eventos_2026.csv.

Fuente principal: GPM IMERG Late diario V07 (NASA GES DISC, 0,1°, día calendario UTC). Requiere un token de Earthdata
en la variable de entorno EARTHDATA_TOKEN (gratis en urs.earthdata.nasa.gov → Generate Token).
Si no hay token, usa PERSIANN-CCS diario (CHRS, UC Irvine, 0,04°, público sin login).

Salida: data/resultados/lluvia_satelite_eventos.csv con evento, dia, icao, fuente, mm.
Uso: python lluvia_satelite.py"""
import csv, gzip, io, os, re, sys, time, urllib.error, urllib.request
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
EVENTOS = os.path.join(AQUI, "..", "hindcast", "eventos", "eventos_2026.csv")
SALIDA = os.path.join(AQUI, "data", "resultados", "lluvia_satelite_eventos.csv")
sys.path.insert(0, AQUI)
from analizar import ZONAS  # noqa: E402

IMERG_DIR = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.07/{y}/{m:02d}/"
PERSIANN = "https://persiann.eng.uci.edu/CHRSdata/PERSIANN-CCS/daily/rgccs1d{yy}{ddd:03d}.bin.gz"
TOKEN = os.environ.get("EARTHDATA_TOKEN", "").strip()


def get(url, headers=None, intentos=4):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "earth2-chile-verificacion/historico", **(headers or {})})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                print("  HTTP", e.code, url); return None
            time.sleep(10 * (i + 1))
        except Exception as e:
            print("  reintento", i + 1, e); time.sleep(10 * (i + 1))
    return None


def estaciones():
    return {r["icao"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(os.path.join(AQUI, "estaciones.csv")))}


def imerg_dia(dia, puntos):
    """mm del día calendario UTC en cada punto, desde IMERG Late diario. Devuelve None si no se pudo."""
    listado = get(IMERG_DIR.format(y=dia.year, m=dia.month))
    if not listado:
        return None
    m = re.search(rf'href="(3B-DAY-L\.MS\.MRG\.3IMERG\.{dia:%Y%m%d}-S000000-E235959\.V\d\w\.nc4)"', listado.decode("utf-8", "replace"))
    if not m:
        print("  IMERG: no hay archivo para", dia.date()); return None
    datos = get(IMERG_DIR.format(y=dia.year, m=dia.month) + m.group(1), headers={"Authorization": f"Bearer {TOKEN}"})
    if not datos:
        return None
    import netCDF4
    ds = netCDF4.Dataset("imerg", memory=datos)
    lat = ds["lat"][:]; lon = ds["lon"][:]; p = ds["precipitation"][0]  # (lon, lat) en mm/día
    out = {}
    for icao, (la, lo) in puntos.items():
        i = int(np.abs(lon - lo).argmin()); j = int(np.abs(lat - la).argmin())
        v = p[i, j]
        out[icao] = None if np.ma.is_masked(v) or v < 0 else float(v)
    ds.close()
    return out


def persiann_dia(dia, puntos):
    """mm del día (00 UTC a 00 UTC) desde PERSIANN-CCS: grilla 0,04°, 3000 filas (60N→60S) × 9000 columnas (0→360E)."""
    ddd = int(dia.strftime("%j")); yy = dia.strftime("%y")
    datos = get(PERSIANN.format(yy=yy, ddd=ddd))
    if not datos:
        return None
    raw = gzip.decompress(datos)
    a = np.frombuffer(raw, dtype=">f4").reshape(3000, 9000)
    out = {}
    for icao, (la, lo) in puntos.items():
        fila = int((60.0 - la) / 0.04); col = int(((lo + 360.0) % 360.0) / 0.04)
        v = a[min(max(fila, 0), 2999), min(max(col, 0), 8999)]
        out[icao] = None if v < 0 else float(v)
    return out


def main():
    ev = pd.read_csv(EVENTOS, parse_dates=["inicio", "fin"])
    est = estaciones()
    fuente = "IMERG Late V07 (NASA)" if TOKEN else "PERSIANN-CCS (CHRS)"
    print("fuente:", fuente)
    filas = []
    for e in ev.itertuples(index=False):
        puntos = {i: est[i] for i in ZONAS.get(e.id, []) if i in est}
        for dia in pd.date_range(e.inicio, e.fin, freq="D"):
            mm = (imerg_dia(dia, puntos) if TOKEN else None) or persiann_dia(dia, puntos)
            if mm is None:
                print(" ", e.id, dia.date(), "sin datos"); continue
            for icao, v in mm.items():
                filas.append(dict(evento=e.id, dia=dia.date(), icao=icao, fuente=fuente if (TOKEN and mm is not None) else "PERSIANN-CCS (CHRS)", mm=v))
            print(" ", e.id, dia.date(), {k: (None if v is None else round(v, 1)) for k, v in mm.items()})
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    pd.DataFrame(filas).to_csv(SALIDA, index=False)
    print("salida:", SALIDA, len(filas), "filas")


if __name__ == "__main__":
    main()
