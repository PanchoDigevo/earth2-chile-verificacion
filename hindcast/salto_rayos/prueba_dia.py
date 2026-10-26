"""Prueba del salto de rayos sobre un día completo: baja los rayos GOES-19 GLM de las 12 UTC del día a las 06 UTC del día
siguiente (tarde y noche de Chile) en la misma caja de la pestaña En vivo, corre envivo/salto_rayos.py y guarda cada salto.

Corre en GitHub Actions (salto-rayos-prueba.yml), un día por trabajo: son unos 3.000 archivos por día. Los rayos crudos no
se guardan; solo los saltos (saltos_DIA.csv) y un resumen del día (resumen_DIA.json).

Uso: python hindcast/salto_rayos/prueba_dia.py --dia 2026-10-26 --salida salida/"""
import argparse, concurrent.futures as cf, datetime as dt, json, os, re, sys, urllib.request
import netCDF4, numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "envivo"))
import salto_rayos  # noqa: E402
from actualizar import LAT0, LAT1, LON0, LON1, GLM, inicio  # noqa: E402

UA = {"User-Agent": "earth2-chile-verificacion/prueba-salto"}


def get(url, intentos=4):
    for _ in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception:
            pass
    return None


def rayos_de(clave):
    b = get(f"{GLM}/{clave}")
    if not b:
        return None
    try:
        d = netCDF4.Dataset("glm", memory=b); la, lo = np.asarray(d["flash_lat"][:]), np.asarray(d["flash_lon"][:]); d.close()
    except Exception:
        return None
    m = (la >= LAT0) & (la <= LAT1) & (lo >= LON0) & (lo <= LON1)
    t = inicio(clave).timestamp()
    return [(float(a), float(o), t) for a, o in zip(la[m], lo[m])]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dia", required=True); ap.add_argument("--salida", required=True)
    a = ap.parse_args(); os.makedirs(a.salida, exist_ok=True)
    t0 = dt.datetime.fromisoformat(a.dia).replace(hour=12, tzinfo=dt.timezone.utc)
    claves = []
    for h in range(18):
        t = t0 + dt.timedelta(hours=h)
        xml = get(f"{GLM}/?list-type=2&prefix=GLM-L2-LCFA/{t:%Y}/{t.timetuple().tm_yday:03d}/{t:%H}/")
        claves += re.findall(r"<Key>([^<]+)</Key>", xml.decode()) if xml else []
    rayos, fallidos = [], 0
    with cf.ThreadPoolExecutor(32) as ex:
        for r in ex.map(rayos_de, claves):
            if r is None:
                fallidos += 1
            else:
                rayos += r
    print(f"{a.dia}: {len(claves)} archivos ({fallidos} fallidos), {len(rayos)} rayos en la caja", flush=True)
    saltos = salto_rayos.detectar(rayos, fin=(t0 + dt.timedelta(hours=18)).timestamp())
    with open(os.path.join(a.salida, f"saltos_{a.dia}.csv"), "w") as f:
        f.write("hora_utc,lat,lon,tasa_por_min,dfrdt,sigma\n")
        for s in saltos:
            f.write(f"{dt.datetime.fromtimestamp(s['t'], dt.timezone.utc):%Y-%m-%d %H:%M},{s['lat']},{s['lon']},{s['tasa']},{s['dfrdt']},{s['sigma']}\n")
    # tormentas fuertes del día: intervalos de 2 min con 10 rayos/min o más, para saber cuánta tormenta hubo
    json.dump({"dia": a.dia, "archivos": len(claves), "fallidos": fallidos, "rayos": len(rayos), "saltos": len(saltos)},
              open(os.path.join(a.salida, f"resumen_{a.dia}.json"), "w"))
    print(f"{a.dia}: {len(saltos)} saltos", flush=True)


if __name__ == "__main__":
    main()
