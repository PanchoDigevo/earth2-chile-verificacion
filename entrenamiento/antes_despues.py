"""Antes y después: la lluvia de una tormenta real de Chile vista a 25 km (ERA5, lo que ve un modelo global) y a 4 km
(SAAG-WRF, la simulación de referencia con la que se entrenará CorrDiff-Chile). Genera las imágenes y los datos de la
página site/zoom.html. No es el resultado de CorrDiff-Chile, que todavía no existe: es lo que tiene que aprender.

Lee solo los trozos necesarios (como preparar_dataset.py): SAAG desde NCAR vía OSDF y ERA5 de la copia ARCO de Google.
Corre en GitHub Actions (.github/workflows/antes-despues.yml); nunca en el Mac.

Uso: python entrenamiento/antes_despues.py --desde 2021-01-29T12 --hasta 2021-01-31T12 --nombre "..." """
import argparse, datetime as dt, json, os, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from preparar_dataset import ARCO, SAAG, constantes, era5, h5_http, recorte  # noqa: E402

SALIDA = os.path.join(AQUI, "..", "site", "zoom")
CHILE = os.path.join(AQUI, "..", "docs", "chile_natural_earth_10m.json")
NIVELES = [0, 1, 5, 10, 20, 30, 50, 75, 100, 150, 250]
COLORES = ["#ffffff00", "#e3eef9", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b", "#041c42"]
PUNTOS = [("Valparaíso", -33.05, -71.62), ("Santiago centro", -33.45, -70.66), ("Las Condes (Apoquindo)", -33.40, -70.51),
          ("San José de Maipo", -33.64, -70.35), ("Farellones", -33.35, -70.31)]


def saag_hora(t):
    for intento in range(3):
        try:
            h = h5_http(f"{SAAG}/hist2D/{t:%Y%m}/wrf2d_d01_{t:%Y-%m-%d_%H}0000.nc")
            return recorte(h["PREC_ACC_NC"])
        except Exception as e:
            err = e
    print(f"SAAG {t}: {type(err).__name__} {err}", flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2021-01-29T12"); ap.add_argument("--hasta", default="2021-01-31T12")
    ap.add_argument("--nombre", default="Lluvia de verano en Chile central, 29 al 31 de enero de 2021")
    ap.add_argument("--caja", default="-32.9,-34.4,-71.9,-69.8", help="lat norte, lat sur, lon oeste, lon este")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    t0 = dt.datetime.strptime(a.desde, "%Y-%m-%dT%H"); t1 = dt.datetime.strptime(a.hasta, "%Y-%m-%dT%H")
    horas = [t0 + dt.timedelta(hours=h) for h in range(1, int((t1 - t0).total_seconds() // 3600) + 1)]   # lluvia de (t0, t1]
    ln, ls, lo, le = [float(x) for x in a.caja.split(",")]
    xlat, xlon, fijas = constantes(); hgt = fijas[0]

    with ThreadPoolExecutor(8) as ex:
        campos = list(ex.map(saag_hora, horas))
    ok = [c for c in campos if c is not None]
    fino = np.sum(ok, axis=0) * len(horas) / max(len(ok), 1)
    print(f"SAAG: {len(ok)}/{len(horas)} horas; máximo {fino.max():.0f} mm", flush=True)

    e5 = era5()["total_precipitation"].sel(time=slice(np.datetime64(horas[0]), np.datetime64(horas[-1])),
                                            latitude=slice(ln + 1.5, ls - 1.5), longitude=slice(lo + 360 - 1.5, le + 360 + 1.5))
    grueso = e5.sum("time").values * 1000.0
    glat, glon = e5.latitude.values, e5.longitude.values - 360
    print(f"ERA5: {e5.sizes['time']} horas; máximo {grueso.max():.0f} mm", flush=True)

    cmap = ListedColormap(COLORES); norm = BoundaryNorm(NIVELES, cmap.N)
    anillos = json.load(open(CHILE))
    asp = 1 / np.cos(np.radians((ln + ls) / 2))

    def mapa(ruta, dibujar):
        fig = plt.figure(figsize=(6.4, 6.4 * (ln - ls) * asp / (le - lo)), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(lo, le); ax.set_ylim(ls, ln); ax.set_aspect(asp); ax.axis("off")
        dibujar(ax)
        ax.contour(xlon, xlat, hgt, levels=[1000, 2000, 3000, 4000], colors="#5a6977", linewidths=0.5, alpha=0.6)
        for anillo in anillos:
            xy = np.array(anillo); ax.plot(xy[:, 0], xy[:, 1], color="#17212b", lw=0.9)
        for n, la, lon_ in PUNTOS:
            ax.plot(lon_, la, "o", ms=3.5, color="#d03b3b", mec="white", mew=0.8)
        fig.savefig(ruta, transparent=True); plt.close(fig)

    os.makedirs(SALIDA, exist_ok=True)
    dlat, dlon = abs(glat[1] - glat[0]), abs(glon[1] - glon[0])
    lat_b = np.concatenate([glat - dlat / 2 * np.sign(glat[1] - glat[0]), [glat[-1] + dlat / 2 * np.sign(glat[1] - glat[0])]])
    lon_b = np.concatenate([glon - dlon / 2, [glon[-1] + dlon / 2]])
    mapa(os.path.join(SALIDA, "era5_25km.png"), lambda ax: ax.pcolormesh(lon_b, lat_b, grueso, cmap=cmap, norm=norm, shading="flat"))
    mapa(os.path.join(SALIDA, "saag_4km.png"), lambda ax: ax.pcolormesh(xlon, xlat, fino, cmap=cmap, norm=norm, shading="nearest"))

    def en(la, lon_):
        i = np.unravel_index(((xlat - la) ** 2 + (xlon - lon_) ** 2).argmin(), xlat.shape)
        j, k = np.abs(glat - la).argmin(), np.abs(glon - lon_).argmin()
        return {"mm_4km": round(float(fino[i]), 1), "mm_25km": round(float(grueso[j, k]), 1), "altura_m": round(float(hgt[i]))}
    caja4 = (xlat <= ln) & (xlat >= ls) & (xlon >= lo) & (xlon <= le)
    caja25 = np.ix_((glat <= ln) & (glat >= ls), (glon >= lo) & (glon <= le))
    datos = {"nombre": a.nombre, "desde_utc": a.desde, "hasta_utc": a.hasta, "horas": len(horas), "horas_saag": len(ok),
             "caja": [ln, ls, lo, le], "niveles": NIVELES, "colores": COLORES,
             "max_4km": round(float(fino[caja4].max()), 1), "max_25km": round(float(grueso[caja25].max()), 1),
             "puntos": [{"nombre": n, **en(la, lon_)} for n, la, lon_ in PUNTOS],
             "fuentes": {"4km": "SAAG-WRF, NCAR RDA d616000 (Liu et al. 2025), CC BY 4.0",
                         "25km": "ERA5 de ECMWF/Copernicus (copia ARCO de Google), CC BY 4.0"}}
    json.dump(datos, open(os.path.join(SALIDA, "datos.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: datos[k] for k in ("max_4km", "max_25km", "puntos")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
