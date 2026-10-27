"""Bandas de altura del relieve entre Santiago y la cordillera, para pintar la nieve sobre el terreno 3D del Gemelo:
polígonos de cada franja de 100 m (de 600 a 6.000 m) desde el Copernicus DEM GLO-90, simplificados.

Escribe site/cordillera/bandas_santiago.geojson: cada polígono lleva {"h": altura base de la banda}. En la página, la nieve es
el relleno blanco de las bandas con h ≥ línea de nieve del escenario. Corre en cordillera-cuencas.yml.
Uso: python cordillera/bandas.py"""
import json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(AQUI, "..", "quebradas"))
import cuencas  # noqa: E402  (dem con teselas GLO-90)
import capas_estaticas as q  # noqa: E402

SALIDA = os.path.join(AQUI, "..", "site", "cordillera", "bandas_santiago.geojson")
CAJA = (-70.95, -33.95, -69.85, -32.90)        # lon_min, lat_min, lon_max, lat_max: Santiago y la cordillera que se ve desde la ciudad
PASO = 100
H0, H1 = 600, 6100
TOL = 0.0012                                    # ~120 m de simplificación: suficiente para verlo en 3D, liviano para el navegador


def main():
    from rasterio import features
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    t0 = time.time()
    cuencas.CAJA = CAJA
    z, tr = cuencas.dem()
    z = np.where(z < -100, 0, z)
    print(f"DEM {z.shape} en {time.time() - t0:.0f} s", flush=True)
    banda = np.clip(((z - H0) // PASO).astype("int16"), -1, (H1 - H0) // PASO)
    feats = []
    for g, v in features.shapes(banda, mask=banda >= 0, transform=tr, connectivity=8):
        feats.append((int(v), shape(g)))
    por_h = {}
    for v, g in feats:
        por_h.setdefault(v, []).append(g)
    salida = []
    for v in sorted(por_h):
        poli = unary_union(por_h[v]).simplify(TOL, preserve_topology=True)
        polis = list(poli.geoms) if hasattr(poli, "geoms") else [poli]
        for p in polis:
            if p.area < 1e-6:                   # manchas de menos de ~1 ha
                continue
            salida.append({"type": "Feature", "geometry": q.redondear(mapping(p), 4), "properties": {"h": H0 + v * PASO}})
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    json.dump({"type": "FeatureCollection", "fuente": "Copernicus DEM GLO-90 (ESA, abierto); bandas de 100 m", "features": salida},
              open(SALIDA, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"{len(salida)} polígonos, {os.path.getsize(SALIDA) // 1024} KB en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
