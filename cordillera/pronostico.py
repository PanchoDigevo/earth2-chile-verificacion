"""Isoterma 0 °C y lluvia en cada cuenca cordillerana (site/cordillera/cuencas.geojson) para las próximas 72 h.

Para cada cuenca y bloque de 3 h, con la corrida de GFS que bajó la verificación:
- isoterma 0 °C media sobre la cuenca (GFS, el único de los tres que la publica);
- línea de nieve: 300 m bajo la isoterma (bajo la isoterma la nieve se derrite al caer; el valor típico usado en Chile
  central es de 200 a 400 m, Garreaud 1992);
- parte de la cuenca que queda bajo la línea de nieve (recibe lluvia y no nieve), con la curva de alturas de la cuenca;
- lluvia media sobre la cuenca, y la lluvia líquida total en millones de m³ (lluvia × área × parte con lluvia).
Además, la lluvia de AIFS e IFS por bloque de 6 h hasta 48 h, de los GRIB que ya bajó la verificación.

Escribe site/datos/cuencas_72h.json. Lo llama verificacion.yml después de los fetch_*.
Uso: python cordillera/pronostico.py"""
import glob, json, os, sys
import numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "verificacion"))
import tormentas_gfs  # noqa: E402
from comun import a_chile  # noqa: E402

DATOS = os.path.join(AQUI, "..", "verificacion", "data")
CUENCAS = os.path.join(AQUI, "..", "site", "cordillera", "cuencas.geojson")
SALIDA = os.path.join(AQUI, "..", "site", "datos", "cuencas_72h.json")
BAJO_ISOTERMA_M = 300
PASO = 0.05                                             # puntos de muestreo dentro de cada cuenca (unos 5 km)
CAMPOS = [("HGT", "0C isotherm"), ("PRATE", "surface")]


def puntos_cuenca(geom):
    from shapely.geometry import shape, Point
    g = shape(geom); x0, y0, x1, y1 = g.bounds
    pts = [(la, lo) for la in np.arange(y0, y1, PASO) for lo in np.arange(x0, x1, PASO) if g.contains(Point(lo, la))]
    return pts or [(g.centroid.y, g.centroid.x)]


def indices(glat, glon, pts):
    lon360 = glon.max() > 180
    out = []
    for la, lo in pts:
        lo2 = lo % 360 if lon360 else lo
        out.append(int(np.argmin((glat - la) ** 2 + (glon - lo2) ** 2)))
    return np.array(out)


def frac_bajo(h, pctl, alturas):
    """Fracción del área de la cuenca bajo la altura h (curva de alturas)."""
    return float(np.interp(h, alturas, pctl) / 100.0)


def gfs(run, cuencas):
    import eccodes as ec
    pasos, mm_prev, idx = {}, {}, {}
    for f in range(3, 73, 3):
        m = tormentas_gfs.mensajes(run, f, CAMPOS)
        if not m or len(m) < 2:
            print(f"cordillera: GFS sin el plazo {f} h; se corta ahí"); break
        v = {}
        for k, b in m.items():
            g = ec.codes_new_from_message(b)
            try:
                if not idx:
                    glat = ec.codes_get_double_array(g, "latitudes"); glon = ec.codes_get_double_array(g, "longitudes")
                    for c in cuencas:
                        idx[c["id"]] = indices(glat, glon, c["pts"])
                todo = ec.codes_get_values(g)
                v[k] = {c["id"]: todo[idx[c["id"]]] for c in cuencas}
            finally:
                ec.codes_release(g)
        for c in cuencas:
            i = c["id"]
            rate = float(np.mean(v[("PRATE", "surface")][i])) * 3600          # mm/h promedio del bloque de GFS
            mm = rate * 3 if f % 6 == 3 else max(0.0, rate * 6 - mm_prev.get(i, 0.0))   # bloque de 3 h (los de 6 h acumulan el anterior)
            mm_prev[i] = mm
            iso = float(np.mean(v[("HGT", "0C isotherm")][i]))
            nieve = iso - BAJO_ISOTERMA_M
            fr = frac_bajo(nieve, c["pctl"], c["alt"])
            pasos.setdefault(i, []).append({"c": a_chile(run + pd.Timedelta(hours=f)).strftime("%Y-%m-%dT%H:%M"), "iso": round(iso), "nieve": round(nieve),
                                            "fr": round(fr, 2), "mm": round(mm, 1), "hm3": round(mm * c["area"] * fr * 0.001, 2)})
    return pasos


def ecmwf(cuencas, run_gfs):
    """{modelo: {cuenca: [{c, mm}]}} de lluvia en bloques de 6 h hasta 48 h, de los GRIB de AIFS, IFS y GFS ya bajados.
    Se omite un archivo de una corrida más de 18 h anterior a la de GFS (quedó de otro día)."""
    import eccodes as ec
    out = {}
    for modelo in ("aifs", "ifs", "gfs"):
        fs = sorted(glob.glob(os.path.join(DATOS, f"{modelo}_*.grib2")))
        if not fs:
            continue
        acum, run, idx = {}, None, {}
        with open(fs[-1], "rb") as fh:
            while True:
                g = ec.codes_grib_new_from_file(fh)
                if g is None:
                    break
                try:
                    if ec.codes_get(g, "shortName") != "tp":
                        continue
                    if not idx:
                        glat = ec.codes_get_double_array(g, "latitudes"); glon = ec.codes_get_double_array(g, "longitudes")
                        idx = {c["id"]: indices(glat, glon, c["pts"]) for c in cuencas}
                        run = pd.Timestamp(f"{ec.codes_get(g, 'dataDate')} {int(ec.codes_get(g, 'dataTime')) // 100:02d}:00")
                    paso = int(ec.codes_get(g, "endStep")); fac = 1000.0 if ec.codes_get(g, "units") == "m" else 1.0
                    val = ec.codes_get_values(g)
                    for c in cuencas:
                        a = acum.setdefault(c["id"], {})
                        a[paso] = max(a.get(paso, 0.0), float(np.mean(val[idx[c["id"]]])) * fac)
                finally:
                    ec.codes_release(g)
        if run is None or run < run_gfs - pd.Timedelta(hours=18):
            continue
        for i, a in acum.items():
            ps = sorted(a)
            out.setdefault(modelo.upper(), {})[i] = [{"c": a_chile(run + pd.Timedelta(hours=p)).strftime("%Y-%m-%dT%H:%M"), "mm": round(max(0.0, a[p] - a[q]), 1)}
                                                     for q, p in zip(ps[:-1], ps[1:])]
    return out


def main():
    if not os.path.exists(CUENCAS):
        raise SystemExit("cordillera: falta site/cordillera/cuencas.geojson (correr cordillera-cuencas.yml)")
    cuencas = []
    for f in json.load(open(CUENCAS, encoding="utf-8"))["features"]:
        p = f["properties"]
        cuencas.append({"id": p["id"], "nombre": p["nombre"], "rio": p["rio"], "area": p["area_km2"], "alt": p["hipso_m"], "pctl": p["hipso_pctl"],
                        "pts": puntos_cuenca(f["geometry"])})
    run = tormentas_gfs.corrida()
    pg = gfs(run, cuencas)
    pm = ecmwf(cuencas, run)
    salida = {"generado": a_chile(pd.Timestamp.now(tz="UTC").tz_localize(None)).strftime("%Y-%m-%dT%H:%M"),
              "corrida_gfs": a_chile(run).strftime("%Y-%m-%dT%H:%M"), "bajo_isoterma_m": BAJO_ISOTERMA_M, "cuencas": {}}
    for c in cuencas:
        salida["cuencas"][c["id"]] = {"nombre": c["nombre"], "rio": c["rio"], "area_km2": c["area"], "pasos": pg.get(c["id"], []),
                                      "lluvia6": {m: v.get(c["id"], []) for m, v in pm.items()}}
        ps = pg.get(c["id"], [])
        if ps:
            print(f"cordillera: {c['nombre']}: isoterma {min(p['iso'] for p in ps):,}–{max(p['iso'] for p in ps):,} m, lluvia GFS 72 h "
                  f"{sum(p['mm'] for p in ps):.0f} mm, lluvia líquida {sum(p['hm3'] for p in ps):.0f} millones de m³")
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    json.dump(salida, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
