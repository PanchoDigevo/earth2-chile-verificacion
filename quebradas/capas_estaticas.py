"""Capas estáticas del visor de quebradas (Santiago oriente): se calculan en GitHub Actions y se publican como
GeoJSON liviano en site/quebradas/. Todas las fuentes son abiertas y sin clave.

  pendiente   Copernicus DEM GLO-30 (AWS) -> clases de pendiente >15°, >25°, >35°        pendiente.geojson
  cicatrices  Sentinel-2 L2A (Earth Search STAC, AWS) -> dNBR dic-2025 vs feb-2026      cicatrices.geojson
  cuencas     HydroBASINS nivel 12 (HydroSHEDS) recortado a la precordillera, con
              estadísticas por cuenca (área, pendiente media, % quemado, prop. HM23)     cuencas.geojson
  cauces      OpenStreetMap (Overpass) waterways con nombre; da nombre a las cuencas     cauces.geojson
  remociones  Catastro de remociones en masa de SERNAGEOMIN (ArcGIS REST), con respaldo
              propio si el servicio no responde                                          remociones.geojson

Uso: python capas_estaticas.py [pendiente|cicatrices|cauces|remociones|cuencas|todo]
(cuencas necesita pendiente y cicatrices ya calculadas: usa los rásteres intermedios de data/)."""
import csv, io, json, os, sys, time, urllib.parse, urllib.request, zipfile
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, "data")                      # rásteres intermedios (ignorados por git)
SALIDA = os.path.join(AQUI, "..", "site", "quebradas")
os.makedirs(DATA, exist_ok=True); os.makedirs(SALIDA, exist_ok=True)

# Área de interés: precordillera de Santiago oriente (Lo Barnechea, Las Condes, La Reina, Peñalolén).
AOI = (-70.62, -33.55, -70.35, -33.28)      # lon_min, lat_min, lon_max, lat_max
UTM = "EPSG:32719"
DEM_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S34_00_W071_00_DEM/"
           "Copernicus_DSM_COG_10_S34_00_W071_00_DEM.tif")
STAC = "https://earth-search.aws.element84.com/v1/search"
PRE, POST = ("2025-11-20T00:00:00Z/2026-01-05T23:59:59Z"), ("2026-02-01T00:00:00Z/2026-03-10T23:59:59Z")
HYBAS_URL = "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_sa_lev12_v1c.zip"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter", "https://z.overpass-api.de/api/interpreter"]
SERNAGEOMIN = ("https://sdngsig.sernageomin.cl/gissdng/rest/services/Remociones_en_masa_Chile/"
               "Remociones_en_Masa_Chile/MapServer")
UA = {"User-Agent": "earth2-chile-verificacion/quebradas (github.com/PanchoDigevo/earth2-chile-verificacion)"}

CLASES_PEND = [(15, 25, "15-25"), (25, 35, "25-35"), (35, 90, ">35")]
DNBR_MODERADA, DNBR_ALTA = 0.27, 0.66        # Key & Benson (2006), umbrales usados por el USGS
PEND_HM = 23.0                               # pendiente de referencia del modelo USGS (PropHM23)
ELEV_MIN_CUENCA = 1000.0                     # una cuenca es "precordillera" si su cota máxima supera esto
ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF", GDAL_HTTP_MAX_RETRY="5",
           GDAL_HTTP_RETRY_DELAY="5", AWS_NO_SIGN_REQUEST="YES")


def get(url, datos=None, headers=None, timeout=300, intentos=4):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, data=datos, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print(f"  intento {i + 1} falló ({e}); espero {15 * (i + 1)} s", flush=True); time.sleep(15 * (i + 1))
    return None


def redondear(obj, nd=4):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, (list, tuple)):
        return [redondear(x, nd) for x in obj]
    if isinstance(obj, dict):
        return {k: (redondear(v, nd) if k == "coordinates" or isinstance(v, (list, dict)) else v) for k, v in obj.items()}
    return obj


def escribir_geojson(nombre, features, extra=None):
    features = [{**f, "geometry": redondear(f["geometry"])} for f in features]
    fc = {"type": "FeatureCollection", "features": features, **(extra or {})}
    ruta = os.path.join(SALIDA, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{nombre}: {len(features)} elementos, {os.path.getsize(ruta) // 1024} KB", flush=True)


def poligonizar(clase_arr, transform, crs, campo, etiquetas, min_ha=0.5, tol=0.00025):
    """Convierte un ráster de clases (0 = nada) en polígonos WGS84 simplificados."""
    from rasterio import features
    from rasterio.warp import transform_geom
    from shapely.geometry import shape, mapping
    feats = []
    for geom, val in features.shapes(clase_arr.astype("uint8"), mask=clase_arr > 0, transform=transform, connectivity=8):
        g = shape(transform_geom(crs, "EPSG:4326", geom))
        ha = g.area * 111320 * 110574 * np.cos(np.radians(AOI[1])) / 10000
        if ha < min_ha:
            continue
        g = g.simplify(tol, preserve_topology=True)
        if g.is_empty:
            continue
        feats.append({"type": "Feature", "properties": {campo: etiquetas[int(val)], "ha": round(ha, 1)}, "geometry": mapping(g)})
    return feats


# ---------- 1. pendiente ----------
def dem():
    """Ventana del DEM sobre el AOI: (z, transform). Se guarda en data/dem.npz para reutilizar."""
    cache = os.path.join(DATA, "dem.npz")
    if os.path.exists(cache):
        d = np.load(cache); from rasterio.transform import Affine
        return d["z"], Affine(*d["tr"][:6])
    import rasterio
    from rasterio.windows import from_bounds
    with rasterio.Env(**ENV), rasterio.open(DEM_URL) as src:
        win = from_bounds(*AOI, src.transform)
        z = src.read(1, window=win).astype("float32"); tr = src.window_transform(win)
    np.savez(cache, z=z, tr=np.array(tr)[:6])
    return z, tr


def pendiente_grados(z, tr):
    lat0 = (AOI[1] + AOI[3]) / 2
    dx_m = abs(tr.a) * 111320 * np.cos(np.radians(lat0)); dy_m = abs(tr.e) * 110574
    gy, gx = np.gradient(z, dy_m, dx_m)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype("float32")


def capa_pendiente():
    z, tr = dem()
    s = pendiente_grados(z, tr)
    np.save(os.path.join(DATA, "pendiente.npy"), s)
    from rasterio import Affine
    h2, w2 = (s.shape[0] // 2) * 2, (s.shape[1] // 2) * 2
    s60 = s[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2).mean(axis=(1, 3))
    tr60 = Affine(tr.a * 2, tr.b, tr.c, tr.d, tr.e * 2, tr.f)
    clases = np.zeros(s60.shape, dtype="uint8")
    for i, (a, b, _) in enumerate(CLASES_PEND, start=1):
        clases[(s60 >= a) & (s60 < b)] = i
    feats = poligonizar(clases, tr60, "EPSG:4326", "clase", {i: c for i, (_, _, c) in enumerate(CLASES_PEND, start=1)}, min_ha=2.0, tol=0.0004)
    escribir_geojson("pendiente.geojson", feats, {"fuente": "Copernicus DEM GLO-30 (ESA, abierto), pendiente en grados", "clases": [c for _, _, c in CLASES_PEND]})


# ---------- 2. cicatrices de incendio (dNBR) ----------
def escenas(periodo):
    cuerpo = json.dumps({"collections": ["sentinel-2-l2a"], "bbox": list(AOI), "datetime": periodo, "limit": 100}).encode()
    r = get(STAC, cuerpo, {"Content-Type": "application/json"})
    feats = json.loads(r)["features"] if r else []
    por_tile = {}
    for f in feats:
        p = f["properties"]
        if p.get("eo:cloud_cover", 100) > 40:
            continue
        por_tile.setdefault(p.get("grid:code"), []).append(f)
    # hasta 3 escenas menos nubosas por tesela
    return {t: sorted(fs, key=lambda f: f["properties"]["eo:cloud_cover"])[:3] for t, fs in por_tile.items()}


def grilla_objetivo():
    """Grilla común a 20 m en UTM 19S que cubre el AOI."""
    from rasterio.warp import transform_bounds
    from rasterio.transform import from_origin
    x0, y0, x1, y1 = transform_bounds("EPSG:4326", UTM, *AOI)
    x0, y1 = np.floor(x0 / 20) * 20, np.ceil(y1 / 20) * 20
    w, h = int(np.ceil((x1 - x0) / 20)), int(np.ceil((y1 - y0) / 20))
    return from_origin(x0, y1, 20, 20), w, h


def nbr_en_grilla(escena, tr, w, h):
    """NBR = (B8A − B12)/(B8A + B12) de una escena, reproyectado a la grilla común y enmascarado con SCL."""
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.windows import from_bounds
    from rasterio.transform import array_bounds
    bounds = array_bounds(h, w, tr)
    bandas = {}
    with rasterio.Env(**ENV):
        for k in ("nir08", "swir22", "scl"):
            with rasterio.open(escena["assets"][k]["href"]) as src:
                dst = np.zeros((h, w), dtype="float32")
                try:
                    win = from_bounds(*bounds, src.transform)
                    arr = src.read(1, window=win, boundless=True, fill_value=0).astype("float32")
                    reproject(arr, dst, src_transform=src.window_transform(win), src_crs=src.crs, dst_transform=tr, dst_crs=UTM,
                              resampling=Resampling.nearest if k == "scl" else Resampling.bilinear, src_nodata=0, dst_nodata=0)
                except Exception as e:
                    print("   no se pudo leer", k, e); return None
                bandas[k] = dst
    scl = bandas["scl"]
    valido = ~np.isin(scl, [0, 1, 3, 6, 8, 9, 10, 11]) & (bandas["nir08"] > 0) & (bandas["swir22"] > 0)
    nbr = np.where(valido, (bandas["nir08"] - bandas["swir22"]) / np.maximum(bandas["nir08"] + bandas["swir22"], 1), np.nan)
    return nbr.astype("float32")


def nbr_periodo(periodo, etiqueta):
    tr, w, h = grilla_objetivo()
    pila = []
    for tile, fs in escenas(periodo).items():
        for f in fs:
            print(f"  {etiqueta}: {f['id']} nubes {f['properties']['eo:cloud_cover']:.0f}%", flush=True)
            a = nbr_en_grilla(f, tr, w, h)
            if a is not None:
                pila.append(a)
    if not pila:
        raise SystemExit(f"sin escenas utilizables para {etiqueta}")
    return np.nanmedian(np.stack(pila), axis=0), tr, w, h


def capa_cicatrices():
    pre, tr, w, h = nbr_periodo(PRE, "pre (dic-2025)")
    post, _, _, _ = nbr_periodo(POST, "post (feb-2026)")
    dnbr = (pre - post).astype("float32")
    np.savez(os.path.join(DATA, "dnbr.npz"), dnbr=dnbr, tr=np.array(tr)[:6], w=w, h=h)
    clases = np.zeros(dnbr.shape, dtype="uint8")
    clases[(dnbr >= DNBR_MODERADA) & (dnbr < DNBR_ALTA)] = 1
    clases[dnbr >= DNBR_ALTA] = 2
    feats = poligonizar(clases, tr, UTM, "severidad", {1: "moderada", 2: "alta"}, min_ha=0.5, tol=0.0002)
    escribir_geojson("cicatrices.geojson", feats, {"fuente": "Sentinel-2 L2A (ESA/Copernicus vía Earth Search, AWS), dNBR = NBR pre − NBR post",
                                                   "pre": PRE, "post": POST, "umbrales": {"moderada": DNBR_MODERADA, "alta": DNBR_ALTA}})
    print(f"  dNBR: {float(np.nanmean(dnbr)):.3f} medio; moderada {int((clases == 1).sum()) * 0.04:.0f} ha, alta {int((clases == 2).sum()) * 0.04:.0f} ha")


# ---------- 3. cauces OSM ----------
def capa_cauces():
    q = ('[out:json][timeout:120];(way["waterway"~"stream|river|canal"](%f,%f,%f,%f););out geom;' % (AOI[1], AOI[0], AOI[3], AOI[2]))
    d = None
    for url in OVERPASS:
        r = get(url, urllib.parse.urlencode({"data": q}).encode(), {"Content-Type": "application/x-www-form-urlencoded"}, timeout=200, intentos=2)
        if r and r[:1] == b"{":
            d = json.loads(r); break
        print("  Overpass no disponible en", url, flush=True)
    if d is None:
        print("  Overpass no respondió; se conserva cauces.geojson anterior si existe"); return
    feats = []
    for e in d.get("elements", []):
        if e.get("type") != "way" or "geometry" not in e:
            continue
        coords = [[p["lon"], p["lat"]] for p in e["geometry"]]
        if len(coords) < 2:
            continue
        t = e.get("tags", {})
        if not t.get("name") and t.get("waterway") != "stream":
            continue
        from shapely.geometry import LineString, mapping as _mapping
        geom = _mapping(LineString(coords).simplify(0.0001, preserve_topology=True))
        feats.append({"type": "Feature", "properties": {"nombre": t.get("name", ""), "tipo": t.get("waterway", "")}, "geometry": geom})
    escribir_geojson("cauces.geojson", feats, {"fuente": "OpenStreetMap (ODbL), waterway=stream/river/canal"})


# ---------- 4. remociones en masa ----------
def capa_remociones():
    feats = []
    bbox = "%f,%f,%f,%f" % (AOI[0] - 0.1, AOI[1] - 0.1, AOI[2] + 0.1, AOI[3] + 0.1)
    for capa in range(0, 6):
        url = (f"{SERNAGEOMIN}/{capa}/query?where=1%3D1&geometry={bbox}&geometryType=esriGeometryEnvelope&inSR=4326"
               f"&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&outSR=4326&f=geojson")
        r = get(url, timeout=120, intentos=2)
        if not r or r[:1] != b"{":
            break
        d = json.loads(r)
        for f in d.get("features", []):
            if f.get("geometry") and f["geometry"].get("type") == "Point":
                p = {k: v for k, v in f["properties"].items() if v not in (None, "", " ")}
                feats.append({"type": "Feature", "properties": {"fuente": "SERNAGEOMIN", "capa": capa, **p}, "geometry": f["geometry"]})
        if not d.get("features"):
            break
    if feats:
        escribir_geojson("remociones.geojson", feats, {"fuente": "Catastro de remociones en masa, SERNAGEOMIN (ArcGIS REST)"}); return
    # respaldo: catálogo propio (prensa, SENAPRED) mientras el servicio no responda
    propio = os.path.join(AQUI, "remociones_propio.csv")
    if os.path.exists(propio):
        for r in csv.DictReader(open(propio, encoding="utf-8")):
            feats.append({"type": "Feature", "properties": {"fuente": r["fuente"], "fecha": r["fecha"], "lugar": r["lugar"], "tipo": r["tipo"], "nota": r["nota"]},
                          "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]}})
    escribir_geojson("remociones.geojson", feats, {"fuente": "Catálogo propio (prensa, SENAPRED); el servicio de SERNAGEOMIN no respondió"})


# ---------- 5. cuencas ----------
def leer_hybas():
    """HydroBASINS SA nivel 12: polígonos que intersectan el AOI. Devuelve lista de (props, shapely geom)."""
    import shapefile
    from shapely.geometry import shape
    cache = os.path.join(DATA, "hybas_sa_lev12_v1c.zip")
    if not os.path.exists(cache):
        print("  bajando HydroBASINS (72 MB)...", flush=True)
        r = get(HYBAS_URL, timeout=900, intentos=3)
        if not r:
            raise SystemExit("no se pudo bajar HydroBASINS")
        open(cache, "wb").write(r)
    z = zipfile.ZipFile(cache)
    nombres = {n.rsplit(".", 1)[1].lower(): n for n in z.namelist() if n.lower().endswith((".shp", ".dbf", ".shx"))}
    sf = shapefile.Reader(shp=io.BytesIO(z.read(nombres["shp"])), dbf=io.BytesIO(z.read(nombres["dbf"])), shx=io.BytesIO(z.read(nombres["shx"])))
    campos = [f[0] for f in sf.fields[1:]]
    out = []
    for i in range(len(sf)):
        s = sf.shape(i)
        bx = s.bbox
        if bx[2] < AOI[0] or bx[0] > AOI[2] or bx[3] < AOI[1] or bx[1] > AOI[3]:
            continue
        out.append((dict(zip(campos, sf.record(i))), shape(s.__geo_interface__)))
    print(f"  HydroBASINS: {len(out)} cuencas tocan el AOI", flush=True)
    return out


def capa_cuencas():
    from rasterio import features
    from rasterio.warp import reproject, Resampling, transform_geom
    from shapely.geometry import mapping, LineString, Point
    from shapely.ops import unary_union
    z, tr = dem()
    s = pendiente_grados(z, tr)
    d = np.load(os.path.join(DATA, "dnbr.npz")); dnbr, tr20 = d["dnbr"], d["tr"]
    from rasterio.transform import Affine
    tr20 = Affine(*tr20[:6])
    # pendiente reproyectada a la grilla de 20 m del dNBR, para PropHM23
    s20 = np.zeros(dnbr.shape, dtype="float32")
    reproject(s, s20, src_transform=tr, src_crs="EPSG:4326", dst_transform=tr20, dst_crs=UTM, resampling=Resampling.bilinear)
    quemado = np.nan_to_num(dnbr) >= DNBR_MODERADA
    # cauces con nombre para bautizar cuencas
    cauces = []
    try:
        for f in json.load(open(os.path.join(SALIDA, "cauces.geojson"), encoding="utf-8"))["features"]:
            if f["properties"].get("nombre"):
                cauces.append((f["properties"]["nombre"], LineString(f["geometry"]["coordinates"])))
    except Exception:
        pass
    overrides = []
    try:
        for r in csv.DictReader(open(os.path.join(AQUI, "nombres_cuencas.csv"), encoding="utf-8")):
            overrides.append((Point(float(r["lon"]), float(r["lat"])), r["nombre"], r.get("nota", "")))
    except FileNotFoundError:
        pass
    feats = []
    for props, g in leer_hybas():
        m30 = features.rasterize([(mapping(g), 1)], out_shape=z.shape, transform=tr, fill=0, dtype="uint8").astype(bool)
        if m30.sum() < 20:
            continue
        zmax = float(z[m30].max())
        if zmax < ELEV_MIN_CUENCA:
            continue
        g_utm = transform_geom("EPSG:4326", UTM, mapping(g))
        m20 = features.rasterize([(g_utm, 1)], out_shape=dnbr.shape, transform=tr20, fill=0, dtype="uint8").astype(bool)
        area_km2 = float(props.get("SUB_AREA", g.area * 111.32 * 110.57 * np.cos(np.radians(AOI[1]))))
        pct_q = float(quemado[m20].mean() * 100) if m20.any() else 0.0
        prop_hm23 = float((quemado[m20] & (s20[m20] >= PEND_HM)).mean()) if m20.any() else 0.0
        dnbr_medio = float(np.nanmean(np.where(m20, dnbr, np.nan))) if m20.any() and np.isfinite(dnbr[m20]).any() else 0.0
        nombres = sorted({n for n, l in cauces if l.intersects(g)}, key=lambda n: (not n.lower().startswith("quebrada"), n))
        manual = [(n, nota) for pt, n, nota in overrides if g.contains(pt)]
        nombre = manual[0][0] if manual else (nombres[0] if nombres else f"Cuenca {int(props['HYBAS_ID']) % 10000}")
        feats.append({"type": "Feature", "properties": {
            "id": int(props["HYBAS_ID"]), "nombre": nombre, "nota": manual[0][1] if manual else "",
            "cauces": nombres[:6], "area_km2": round(area_km2, 2), "elev_min": round(float(z[m30].min())), "elev_max": round(zmax),
            "pend_media": round(float(s[m30].mean()), 1), "frac_pend23": round(float((s[m30] >= PEND_HM).mean()), 3),
            "pct_quemado": round(pct_q, 1), "prop_hm23": round(prop_hm23, 4), "dnbr_medio": round(max(dnbr_medio, 0.0), 3)},
            "geometry": mapping(g.simplify(0.0002, preserve_topology=True))})
    escribir_geojson("cuencas.geojson", feats, {"fuente": "HydroBASINS nivel 12 (HydroSHEDS, CC-BY 4.0) + estadísticas propias sobre Copernicus DEM y dNBR Sentinel-2",
                                                "regla": "USGS post-incendio (Staley et al. 2017, modelo M1): PropHM23 = fracción quemada (moderada/alta) con pendiente ≥ 23°"})


if __name__ == "__main__":
    que = sys.argv[1] if len(sys.argv) > 1 else "todo"
    pasos = {"pendiente": capa_pendiente, "cicatrices": capa_cicatrices, "cauces": capa_cauces, "remociones": capa_remociones, "cuencas": capa_cuencas}
    for k in (list(pasos) if que == "todo" else [que]):
        t0 = time.time(); print(f"== {k} ==", flush=True); pasos[k](); print(f"   {round(time.time() - t0)} s", flush=True)
