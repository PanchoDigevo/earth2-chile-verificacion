"""Prueba del indicador de tormentas a 72 h contra los rayos del satélite: para cada día de una quincena toma GFS 00 UTC
(plazos 12 a 36 h cada 3 h), calcula los ingredientes y el nivel en cada comuna de la caja de En vivo (28,5°S a 38,5°S)
y cuenta los rayos GOES-19 GLM a menos de 25 km de la comuna entre 1,5 h antes y 1,5 h después de cada plazo.

Guarda los ingredientes además del nivel, para poder probar otros cortes sin volver a bajar nada (calibrar.py).
Corre en GitHub Actions (tormentas-rayos-prueba.yml), una quincena por trabajo.
Uso: python hindcast/tormentas_gfs/prueba_rayos.py 2026-01 1 salida/     (1 = días 1 a 15, 2 = del 16 al final)"""
import concurrent.futures as cf, datetime as dt, os, re, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "verificacion"))
sys.path.insert(0, os.path.join(AQUI, "..", "salto_rayos"))
import tormentas_gfs  # noqa: E402
import prueba_dia as glm  # noqa: E402

RADIO_KM = 25


def comunas():
    c = pd.read_csv(os.path.join(AQUI, "..", "..", "verificacion", "comunas.csv"))
    return c[(c.lat <= glm.LAT1 - 0.3) & (c.lat >= glm.LAT0 + 0.3) & (c.lon >= glm.LON0 + 0.3)][["id", "lat", "lon"]].reset_index(drop=True)


def rayos_dia(dia):
    """Rayos (lat, lon, t) de 10:30 UTC del día a 13:30 UTC del siguiente."""
    t0 = pd.Timestamp(dia).tz_localize("UTC") + pd.Timedelta(hours=10)
    claves = []
    for h in range(28):
        t = t0 + pd.Timedelta(hours=h)
        xml = glm.get(f"{glm.GLM}/?list-type=2&prefix=GLM-L2-LCFA/{t:%Y}/{t.timetuple().tm_yday:03d}/{t:%H}/")
        claves += re.findall(r"<Key>([^<]+)</Key>", xml.decode()) if xml else []
    out, faltan = [], 0
    with cf.ThreadPoolExecutor(32) as ex:
        for r in ex.map(glm.rayos_de, claves):
            if r is None:
                faltan += 1
            else:
                out += r
    return np.array(out, dtype=float).reshape(-1, 3), len(claves), faltan


def main(mes, parte, salida):
    os.makedirs(salida, exist_ok=True)
    c = comunas()
    ini = pd.Timestamp(mes + "-01")
    fin = ini + pd.offsets.MonthEnd(0)
    dias = pd.date_range(ini, ini + pd.Timedelta(days=14)) if parte == "1" else pd.date_range(ini + pd.Timedelta(days=15), fin)
    filas = []
    for dia in dias:
        if dia >= pd.Timestamp.now().normalize() - pd.Timedelta(days=1):
            break
        g = tormentas_gfs.calcular(dia, c, plazos=range(12, 37, 3))
        if not g:
            continue
        d = pd.concat(g, ignore_index=True)
        r, n, faltan = rayos_dia(dia)
        if n < 4000 or faltan > n * 0.05:                     # día con huecos en el GLM: no se usa
            print(dia.date(), f"GLM incompleto ({n} archivos, {faltan} fallidos); se omite", flush=True); continue
        cos = np.cos(np.radians(c.lat.values.mean()))
        conteo = []
        for v in sorted(d.valid.unique()):
            tv = pd.Timestamp(v).tz_localize("UTC").timestamp()
            x = r[(r[:, 2] > tv - 5400) & (r[:, 2] <= tv + 5400)]
            if len(x):
                dist = 111.2 * np.hypot(x[:, None, 0] - c.lat.values[None, :], (x[:, None, 1] - c.lon.values[None, :]) * cos)
                k = (dist <= RADIO_KM).sum(axis=0)
            else:
                k = np.zeros(len(c), dtype=int)
            conteo.append(pd.DataFrame({"valid": v, "id": c.id.values, "rayos25": k}))
        d = d.merge(pd.concat(conteo), on=["valid", "id"])
        filas.append(d.drop(columns=["run"]).assign(dia=dia.strftime("%Y-%m-%d")))
        print(dia.date(), f"listo: {len(r)} rayos en la caja", flush=True)
    if filas:
        pd.concat(filas).to_csv(os.path.join(salida, f"rayos_{mes}_{parte}.csv.gz"), index=False, date_format="%Y-%m-%d %H:%M")


if __name__ == "__main__":
    main(*sys.argv[1:4])
