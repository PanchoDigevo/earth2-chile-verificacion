"""Exploración de SAAG-WRF 4 km (NCAR RDA d616000) para el dataset de CorrDiff-Chile (tarea 6), sin bajar archivos enteros.

La copia en AWS (s3://saag-wrf) no existe: el registro de AWS la nombra, pero el bucket responde NoSuchBucket y la ficha
oficial de NCAR deja vacío el ARN. Los datos se leen desde NCAR vía OSDF por HTTPS, sin clave:
  https://osdf-director.osg-htc.org/ncar/rda/d616000/hist2D/YYYYMM/wrf2d_d01_YYYY-MM-DD_HH0000.nc   (~736 MB cada hora)
  https://osdf-director.osg-htc.org/ncar/rda/d616000/INVARIANT/wrfconstants_SAAG.nc
Como son HDF5, se abren por HTTP con fsspec + h5py y se leen solo los trozos (chunks) de las variables y la zona que
interesan. Este script mide cuánto se baja de verdad para decidir el plan de la tarea 6.

Uso (en GitHub Actions o una instancia de nube; nunca en el Mac): python entrenamiento/explorar_saag.py [--fecha 2018-01-01T00]"""
import argparse, json, time
import numpy as np

BASE = "https://osdf-director.osg-htc.org/ncar/rda/d616000"
PUNTOS = {"Arica": (-18.35, -70.34), "Las Condes": (-33.40, -70.55), "Punta Arenas": (-53.00, -70.85),
          "Puerto Williams": (-54.93, -67.62), "Cabo de Hornos": (-55.98, -67.27), "Antártica (Teniente Marsh)": (-62.19, -58.99)}
CAJA = dict(lat_n=-17.4, lat_s=-56.2, lon_o=-76.5, lon_e=-66.0)    # Chile continental e insular cercano
BUSCAR = ("T2", "Q2", "U10", "V10", "PSFC", "PREC_ACC_NC", "RAINNC", "RAINC", "PREC", "SWDOWN", "SNOW", "SNOWH", "SR", "LH", "HFX", "TSK")


class Contador:
    """Envuelve un archivo de fsspec para contar los bytes que realmente se leen por la red."""
    def __init__(self, f):
        self.f, self.n = f, 0
    def read(self, *a):
        b = self.f.read(*a); self.n += len(b); return b
    def __getattr__(self, k):
        return getattr(self.f, k)


def abrir(url):
    import fsspec, h5py
    f = Contador(fsspec.filesystem("https", block_size=4 * 2**20).open(url, "rb", cache_type="blockcache"))
    return f, h5py.File(f, "r")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fecha", default="2018-01-01T00"); a = ap.parse_args()
    informe = {}
    t0 = time.time()
    f, h = abrir(f"{BASE}/INVARIANT/wrfconstants_SAAG.nc")
    lat = h["XLAT"][...].squeeze(); lon = h["XLONG"][...].squeeze()
    informe["grilla"] = {"forma": list(lat.shape), "lat": [round(float(lat.min()), 2), round(float(lat.max()), 2)],
                         "lon": [round(float(lon.min()), 2), round(float(lon.max()), 2)],
                         "atributos": {k: (v.decode() if isinstance(v, bytes) else (v.item() if hasattr(v, "item") and np.size(v) == 1 else str(v)))
                                       for k, v in h.attrs.items() if k in ("MAP_PROJ", "MAP_PROJ_CHAR", "DX", "DY", "CEN_LAT", "CEN_LON", "TRUELAT1", "TRUELAT2", "STAND_LON")},
                         "variables_constantes": sorted(h.keys())[:60]}
    pts = {}
    for n, (la, lo) in PUNTOS.items():
        d = (lat - la) ** 2 + (lon - lo) ** 2; i = np.unravel_index(d.argmin(), d.shape)
        borde = i[0] in (0, lat.shape[0] - 1) or i[1] in (0, lat.shape[1] - 1)
        pts[n] = {"km_al_punto_mas_cercano": round(float(np.sqrt(d.min())) * 111, 1), "indice": [int(i[0]), int(i[1])], "en_el_borde": bool(borde)}
    informe["puntos"] = pts
    m = (lat <= CAJA["lat_n"]) & (lat >= CAJA["lat_s"]) & (lon >= CAJA["lon_o"]) & (lon <= CAJA["lon_e"])
    r, c = np.where(m)
    caja = {"filas": [int(r.min()), int(r.max())], "cols": [int(c.min()), int(c.max())]}
    caja["forma"] = [caja["filas"][1] - caja["filas"][0] + 1, caja["cols"][1] - caja["cols"][0] + 1]
    caja["forma_multiplo_32"] = [int(np.ceil(x / 32) * 32) for x in caja["forma"]]
    informe["caja_chile"] = caja
    informe["constantes_bytes_leidos_mb"] = round(f.n / 1e6, 1)

    dia = a.fecha[:10]; hh = a.fecha[11:13]
    url = f"{BASE}/hist2D/{dia[:4]}{dia[5:7]}/wrf2d_d01_{dia}_{hh}0000.nc"
    t1 = time.time(); f2, h2 = abrir(url)
    info = {}
    for k in sorted(h2.keys()):
        ds = h2[k]
        if not hasattr(ds, "shape") or ds.ndim < 2:
            continue
        info[k] = {"forma": list(ds.shape), "chunks": list(ds.chunks) if ds.chunks else None, "compresion": ds.compression,
                   "unidades": (ds.attrs.get("units", b"").decode() if isinstance(ds.attrs.get("units", b""), bytes) else str(ds.attrs.get("units", ""))),
                   "descripcion": (ds.attrs.get("description", b"").decode() if isinstance(ds.attrs.get("description", b""), bytes) else str(ds.attrs.get("description", "")))}
    informe["hora"] = {"url": url, "n_variables_2d": len(info), "metadatos_mb": round(f2.n / 1e6, 1),
                       "variables": {k: v for k, v in info.items() if k in BUSCAR},
                       "todas": sorted(info)}
    leidas = {}
    for k in [x for x in BUSCAR if x in info]:
        n0, s0 = f2.n, time.time()
        v = h2[k][..., caja["filas"][0]:caja["filas"][1] + 1, caja["cols"][0]:caja["cols"][1] + 1]
        leidas[k] = {"mb_bajados": round((f2.n - n0) / 1e6, 1), "segundos": round(time.time() - s0, 1),
                     "min": round(float(np.nanmin(v)), 3), "max": round(float(np.nanmax(v)), 3)}
    informe["lectura_caja_chile"] = leidas
    informe["hora"]["total_mb_bajados"] = round(f2.n / 1e6, 1)
    informe["segundos"] = round(time.time() - t0, 1)
    mb = sum(x["mb_bajados"] for k, x in leidas.items() if k in ("T2", "U10", "V10", "PREC_ACC_NC", "RAINNC", "SWDOWN"))
    informe["estimacion"] = {"mb_por_hora_variables_clave": round(mb, 1),
                             "tb_10_anios_horario": round(mb * 8760 * 10 / 1e6, 2), "tb_10_anios_cada_3h": round(mb * 8760 * 10 / 3 / 1e6, 2),
                             "tb_si_se_bajaran_archivos_enteros_horario": round(736 * 8760 * 10 / 1e6, 1)}
    print(json.dumps(informe, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
