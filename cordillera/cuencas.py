"""Cuencas cordilleranas de Chile central y su curva de alturas (hipsometría): la base para saber, con la isoterma 0 °C
de cada momento, qué parte de la cuenca recibe lluvia en vez de nieve.

Cada cuenca es todo lo que drena hacia una estación fluviométrica de la DGA (cordillera/salidas_rios.csv), delimitada con
el Copernicus DEM GLO-90 (ESA, abierto, en AWS) y pysheds, igual que las quebradas (quebradas/capas_estaticas.py).
Escribe site/cordillera/cuencas.geojson: polígono simplificado, área, altura media y la altura de cada percentil de
área (0, 2, ..., 100 %): la fracción de la cuenca bajo una altura h se lee interpolando en esa curva.

Corre en GitHub Actions (cordillera-cuencas.yml); se rehace solo si cambia salidas_rios.csv.
Uso: python cordillera/cuencas.py"""
import csv, json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "quebradas"))
import capas_estaticas as q  # noqa: E402  (hidrologia, celda_km2, ENV, redondear)

SALIDA = os.path.join(AQUI, "..", "site", "cordillera")
CAJA = (-71.45, -36.35, -69.70, -32.25)                # lon_min, lat_min, lon_max, lat_max
TESELA = "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_{la}_00_{lo}_00_DEM/Copernicus_DSM_COG_30_{la}_00_{lo}_00_DEM.tif"
RADIO_KM = 2.5                                          # la salida se ajusta a la celda de mayor acumulación en este radio
PCTL = list(range(0, 101, 2))


def dem():
    import rasterio
    from rasterio.merge import merge
    teselas = []
    for la in range(int(np.floor(CAJA[1])), int(np.ceil(CAJA[3]))):
        for lo in range(int(np.floor(CAJA[0])), int(np.ceil(CAJA[2]))):
            teselas.append(TESELA.format(la=f"S{-la:02d}", lo=f"W{-lo:03d}"))
    with rasterio.Env(**q.ENV):
        fuentes = [rasterio.open(t) for t in teselas]
        z, tr = merge(fuentes, bounds=CAJA, nodata=-9999.0)
        for f in fuentes:
            f.close()
    return z[0].astype("float32"), tr


def salidas():
    return [r for r in csv.DictReader(open(os.path.join(AQUI, "salidas_rios.csv"), encoding="utf-8"))]


def main():
    from rasterio import features
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    os.makedirs(SALIDA, exist_ok=True)
    t0 = time.time(); z, tr = dem()
    print(f"DEM {z.shape} en {time.time() - t0:.0f} s", flush=True)
    grid, fdir, acc, _ = q.hidrologia(np.where(z < -100, 0, z), tr)
    cell = q.celda_km2(tr, z.shape[0])
    acc_km2 = acc * cell[:, None]
    print(f"hidrología en {time.time() - t0:.0f} s", flush=True)
    feats = []
    for s in salidas():
        lat, lon = float(s["lat"]), float(s["lon"])
        c0, r0 = ~tr * (lon, lat); r0, c0 = int(r0), int(c0)
        n = int(RADIO_KM / (abs(tr.e) * 110.574))
        ven = acc_km2[r0 - n:r0 + n + 1, c0 - n:c0 + n + 1]
        dr, dc = np.unravel_index(int(np.argmax(ven)), ven.shape); r, c = r0 - n + dr, c0 - n + dc
        m = np.asarray(grid.catchment(x=c, y=r, fdir=fdir, xytype="index")).astype(bool)
        area = float((m * cell[:, None]).sum())
        alt = z[m]; peso = np.broadcast_to(cell[:, None], z.shape)[m]
        orden = np.argsort(alt); acum = np.cumsum(peso[orden]) / peso.sum()
        hipso = [round(float(np.interp(p / 100, acum, alt[orden]))) for p in PCTL]
        poli = unary_union([shape(g) for g, v in features.shapes(m.astype("uint8"), mask=m, transform=tr) if v == 1])
        poli = poli.simplify(0.004, preserve_topology=True)
        ref = float(s["area_ref_km2"]) if s.get("area_ref_km2") else None
        print(f"{s['nombre']}: {area:,.0f} km² (referencia aprox. {ref or '–'}), altura media {np.average(alt, weights=peso):,.0f} m,"
              f" mediana {hipso[25]:,} m, máx. {hipso[-1]:,} m; salida ajustada {111.2 * np.hypot((r - r0) * abs(tr.e), (c - c0) * abs(tr.a)):.1f} km", flush=True)
        feats.append({"type": "Feature", "geometry": q.redondear(mapping(poli), 3),
                      "properties": {"id": s["id"], "nombre": s["nombre"], "rio": s["rio"], "estacion": s["estacion"],
                                     "region": s["region"], "area_km2": round(area), "area_ref_km2": ref,
                                     "alt_media_m": round(float(np.average(alt, weights=peso))), "hipso_pctl": PCTL, "hipso_m": hipso}})
    json.dump({"type": "FeatureCollection", "fuente": "Copernicus DEM GLO-90 (ESA, abierto) y pysheds; salidas en estaciones fluviométricas de la DGA",
               "features": feats}, open(os.path.join(SALIDA, "cuencas.geojson"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(feats)} cuencas en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
