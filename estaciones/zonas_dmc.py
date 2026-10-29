"""Cruce fijo entre las comunas (verificacion/comunas.csv) y las zonas de pronóstico de la DMC. Se corre a mano, una vez,
o cuando la DMC cambie sus zonas; necesita shapely (en el venv local ~/e2venv). Bajadas que no se guardan en el repo:

  - Límites comunales de la Biblioteca del Congreso Nacional (BCN), vía geoBoundaries CHL ADM3 (CC BY 3.0 IGO).
  - Zonas y regiones del Sistema de Alerta Meteorológica de la DMC (AAA/coordenadas_zonas_DMC_v3.geojson y
    coordenadas_regiones_DMC.geojson): 87 zonas (litoral, valle, precordillera, cordillera...) y 18 regiones.

Escribe en estaciones/:
  dmc_zonas_comunas.csv   id, nombre, region_dmc, zona, fraccion: qué parte del área de cada comuna cae en cada zona
                          (desde 2 %), y centro=1 si el punto de la comuna (su cabecera, de Wikidata) está en esa zona.
  comunas_muestras.csv    id, lat, lon, zona: hasta 40 puntos repartidos dentro de cada comuna, más su cabecera, con la zona DMC
                          de cada punto, para cruzar
                          en cada hora los avisos que la DMC dibuja como polígono libre (dmc_avisos.py, sin shapely).

Uso: ~/e2venv/bin/python estaciones/zonas_dmc.py"""
import csv, json, os, unicodedata, urllib.request

import numpy as np
from shapely.geometry import Point, shape
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
COMUNAS = os.path.join(AQUI, "..", "verificacion", "comunas.csv")
BCN = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/CHL/ADM3/geoBoundaries-CHL-ADM3_simplified.geojson"
DMC = "https://archivos.meteochile.gob.cl/portaldmc/AAA/{}.geojson"
ALIAS = {"comuna de camarones": "camarones", "san vicente de tagua tagua": "san vicente", "la calera": "calera",
         "llay llay": "llaillay"}
MIN_FRACCION, MUESTRAS = 0.02, 40


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace("'", "").replace("-", " ").strip()
    return ALIAS.get(s, s)


def bajar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    bcn = {norm(f["properties"]["shapeName"]): shape(f["geometry"]).buffer(0) for f in bajar(BCN)["features"]}
    zonas = [(f["properties"]["indice"], shape(f["geometry"]).buffer(0)) for f in bajar(DMC.format("coordenadas_zonas_DMC_v3"))["features"]]
    regiones = [(f["properties"]["indice"], shape(f["geometry"]).buffer(0)) for f in bajar(DMC.format("coordenadas_regiones_DMC"))["features"]]
    filas, muestras, sin = [], [], []
    rng = np.random.default_rng(0)
    for c in csv.DictReader(open(COMUNAS, encoding="utf-8")):
        punto = Point(float(c["lon"]), float(c["lat"]))
        geo = bcn.get(norm(c["nombre"]))
        if geo is None:                                   # sin límite: solo su punto
            sin.append(c["nombre"]); geo = punto.buffer(0.03)
        reg = max(regiones, key=lambda r: r[1].intersection(geo).area)[0] if any(r[1].intersects(geo) for r in regiones) else ""
        area = geo.area
        for z, g in zonas:
            if not g.intersects(geo):
                continue
            fr = g.intersection(geo).area / area
            centro = int(g.buffer(0.005).contains(punto))
            if fr >= MIN_FRACCION or centro:
                filas.append({"id": c["id"], "nombre": c["nombre"], "region_dmc": reg, "zona": z, "fraccion": round(fr, 3), "centro": centro})
        # puntos al azar dentro del límite, para los polígonos libres
        x0, y0, x1, y1 = geo.bounds
        pts = [punto]
        for _ in range(4000):
            if len(pts) > MUESTRAS:
                break
            p = Point(rng.uniform(x0, x1), rng.uniform(y0, y1))
            if geo.contains(p):
                pts.append(p)
        cerca = [(z, g) for z, g in zonas if g.intersects(geo.buffer(0.01))]
        muestras += [{"id": c["id"], "lat": round(p.y, 4), "lon": round(p.x, 4),
                      "zona": next((z for z, g in cerca if g.contains(p)), "")} for p in pts]
    with open(os.path.join(AQUI, "dmc_zonas_comunas.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "nombre", "region_dmc", "zona", "fraccion", "centro"]); w.writeheader(); w.writerows(filas)
    with open(os.path.join(AQUI, "comunas_muestras.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "lat", "lon", "zona"]); w.writeheader(); w.writerows(muestras)
    print(f"{len({f['id'] for f in filas})} comunas en {len({f['zona'] for f in filas})} zonas ({len(filas)} cruces); "
          f"{len(muestras)} puntos de muestra; sin límite comunal: {', '.join(sin) or 'ninguna'}")


if __name__ == "__main__":
    main()
