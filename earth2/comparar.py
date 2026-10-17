"""Compara la extracción por estación de Earth2Studio (earth2/fetch_e2s.py) con la nuestra (GRIB de ECMWF open data
leído con eccodes, punto de grilla más cercano), para la misma corrida de AIFS y los mismos plazos.
Si coinciden (diferencia máxima < 0,05 °C y < 0,05 m/s), fetch_e2s.py puede reemplazar a fetch_aifs.py.
Salida: earth2/data/comparacion_aifs.csv y un resumen en pantalla."""
import datetime as dt, json, os, sys, time, urllib.error, urllib.request
import numpy as np, pandas as pd
import eccodes as ec

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from fetch_e2s import extraer  # noqa: E402

CORRIDA = dt.datetime(2026, 10, 14, 0)
PLAZOS = [0, 6, 12, 24]
B = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"


def leer(url, rango=None, intentos=8):
    """GET con reintentos: el bucket de ECMWF responde 503 Slow Down bajo carga."""
    for i in range(intentos):
        try:
            h = {"Range": f"bytes={rango[0]}-{rango[1]}"} if rango else {}
            return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120).read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            time.sleep(min(60, 2 * 2 ** i))
    raise SystemExit(f"sin respuesta de ECMWF: {url}")


def nuestro(est):
    filas = []
    for h in PLAZOS:
        base = f"{B}/{CORRIDA:%Y%m%d}/{CORRIDA:%H}z/aifs-single/0p25/oper/{CORRIDA:%Y%m%d%H}0000-{h}h-oper-fc"
        idx = [json.loads(l) for l in leer(base + ".index").decode().splitlines() if l.startswith("{")]
        v = {}
        for e in idx:
            if e.get("levtype") == "sfc" and e["param"] in ("2t", "10u", "10v"):
                o, n = int(e["_offset"]), int(e["_length"])
                gid = ec.codes_new_from_message(leer(base + ".grib2", (o, o + n - 1)))
                v[e["param"]] = [ec.codes_grib_find_nearest(gid, la, lo)[0].value for la, lo in zip(est.lat, est.lon)]
                ec.codes_release(gid)
        for i, r in est.reset_index(drop=True).iterrows():
            filas.append({"lead_h": h, "icao": r.icao, "t_ref": v["2t"][i] - 273.15, "w_ref": float(np.hypot(v["10u"][i], v["10v"][i]))})
    return pd.DataFrame(filas)


def main():
    est = pd.read_csv(os.path.join(AQUI, "..", "historico", "estaciones.csv"))
    e2s = extraer("aifs", CORRIDA, PLAZOS, est)
    ref = nuestro(est)
    c = e2s.merge(ref, on=["lead_h", "icao"])
    c["dt"] = c.t_fc - c.t_ref; c["dw"] = c.w_fc - c.w_ref
    os.makedirs(os.path.join(AQUI, "data"), exist_ok=True)
    c.to_csv(os.path.join(AQUI, "data", "comparacion_aifs.csv"), index=False)
    mt, mw = float(c.dt.abs().max()), float(c.dw.abs().max())
    print(f"comparación AIFS {CORRIDA:%Y-%m-%d %Hz}, plazos {PLAZOS}, {len(c)} pares estación-plazo")
    print(f"diferencia máxima: temperatura {mt:.3f} °C, viento {mw:.3f} m/s")
    print("COINCIDEN" if mt < 0.05 and mw < 0.05 else "NO COINCIDEN")
    if mt >= 0.05 or mw >= 0.05:
        print(c.reindex(c.dt.abs().sort_values(ascending=False).index).head(8).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
