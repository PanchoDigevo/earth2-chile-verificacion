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
NIVELES_T = [-12, -9, -6, -3, 0, 3, 6, 9, 12, 15, 18]
COLORES_T = ["#08306b", "#2171b5", "#6baed6", "#c6dbef", "#f2f0f7", "#fee6ce", "#fdae6b", "#f16913", "#d94801", "#7f2704"]
AERODROMOS = [("Pudahuel (aeropuerto)", "SCEL", -33.393, -70.786), ("Tobalaba (Las Condes)", "SCTB", -33.456, -70.548),
              ("Santo Domingo (costa)", "SCSN", -33.656, -71.614)]
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


def metar(icao, t):
    """Temperatura medida en el aeródromo a esa hora (±30 min), del archivo METAR de Iowa State."""
    import csv, io, urllib.request
    a, b = t - dt.timedelta(minutes=30), t + dt.timedelta(minutes=30)
    url = (f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station={icao}&data=tmpc&year1={a:%Y}&month1={a.month}&day1={a.day}"
           f"&hour1={a.hour}&minute1={a.minute}&year2={b:%Y}&month2={b.month}&day2={b.day}&hour2={b.hour}&minute2={b.minute}"
           f"&tz=Etc/UTC&format=onlycomma&latlon=no&missing=empty&report_type=3")
    try:
        filas = [r for r in csv.DictReader(io.StringIO(urllib.request.urlopen(url, timeout=60).read().decode())) if r.get("tmpc")]
        return float(filas[0]["tmpc"]) if filas else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2021-01-29T12"); ap.add_argument("--hasta", default="2021-01-31T12")
    ap.add_argument("--nombre", default="Lluvia de verano en Chile central, 29 al 31 de enero de 2021")
    ap.add_argument("--caja", default="-32.9,-34.4,-71.9,-69.8", help="lat norte, lat sur, lon oeste, lon este")
    ap.add_argument("--variable", choices=["lluvia", "temp"], default="lluvia", help="lluvia acumulada (desde-hasta) o temperatura a la hora 'desde'")
    ap.add_argument("--observado", default="", help='lo que midió una estación en el mismo periodo, "Nombre;lat;lon;mm;fuente"')
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    t0 = dt.datetime.strptime(a.desde, "%Y-%m-%dT%H"); t1 = dt.datetime.strptime(a.hasta, "%Y-%m-%dT%H")
    horas = [t0 + dt.timedelta(hours=h) for h in range(1, int((t1 - t0).total_seconds() // 3600) + 1)]   # lluvia de (t0, t1]
    ln, ls, lo, le = [float(x) for x in a.caja.split(",")]
    xlat, xlon, fijas = constantes(); hgt = fijas[0]

    caja_e5 = dict(latitude=slice(ln + 1.5, ls - 1.5), longitude=slice(lo + 360 - 1.5, le + 360 + 1.5))
    if a.variable == "temp":
        horas = [t0]
        h = h5_http(f"{SAAG}/hist2D/{t0:%Y%m}/wrf2d_d01_{t0:%Y-%m-%d_%H}0000.nc")
        fino = recorte(h["T2"]) - 273.15; ok = [fino]
        e5 = era5()["2m_temperature"].sel(time=np.datetime64(t0)).sel(**caja_e5)
        grueso = e5.values - 273.15
        niveles, colores, unidad = NIVELES_T, COLORES_T, "°C"
    else:
        with ThreadPoolExecutor(8) as ex:
            campos = list(ex.map(saag_hora, horas))
        ok = [c for c in campos if c is not None]
        fino = np.sum(ok, axis=0) * len(horas) / max(len(ok), 1)
        e5 = era5()["total_precipitation"].sel(time=slice(np.datetime64(horas[0]), np.datetime64(horas[-1]))).sel(**caja_e5)
        grueso = e5.sum("time").values * 1000.0
        niveles, colores, unidad = NIVELES, COLORES, "mm"
    glat, glon = e5.latitude.values, e5.longitude.values - 360
    print(f"SAAG {len(ok)}/{len(horas)} horas; ERA5 listo. Rango 4 km {fino.min():.1f} a {fino.max():.1f}; 25 km {grueso.min():.1f} a {grueso.max():.1f} {unidad}", flush=True)

    cmap = ListedColormap(colores); norm = BoundaryNorm(niveles, cmap.N, extend="both" if a.variable == "temp" else "neither")
    anillos = json.load(open(CHILE))
    asp = 1 / np.cos(np.radians((ln + ls) / 2))

    def mapa(ruta, dibujar):
        fig = plt.figure(figsize=(6.4, 6.4 * (ln - ls) * asp / (le - lo)), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(lo, le); ax.set_ylim(ls, ln); ax.set_aspect(asp); ax.axis("off")
        dibujar(ax)
        ax.contour(xlon, xlat, hgt, levels=[1000, 2000, 3000, 4000], colors="#5a6977", linewidths=0.5, alpha=0.6)
        for anillo in anillos:
            xy = np.array(anillo); ax.plot(xy[:, 0], xy[:, 1], color="#17212b", lw=0.9)
        for n, la, lon_ in (PUNTOS if a.variable == "lluvia" else [(n, la, lo_) for n, _, la, lo_ in AERODROMOS] + PUNTOS[3:]):
            ax.plot(lon_, la, "o", ms=3.5, color="#d03b3b" if a.variable == "lluvia" else "#17212b", mec="white", mew=0.8)
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
    puntos = [{"nombre": n, **en(la, lon_)} for n, la, lon_ in PUNTOS]
    if a.variable == "temp":
        puntos = [{"nombre": n, **en(la, lon_), "medido": metar(icao, t0), "icao": icao} for n, icao, la, lon_ in AERODROMOS] + \
                 [{"nombre": n, **en(la, lon_)} for n, la, lon_ in PUNTOS[3:]]
    caja4 = (xlat <= ln) & (xlat >= ls) & (xlon >= lo) & (xlon <= le)
    caja25 = np.ix_((glat <= ln) & (glat >= ls), (glon >= lo) & (glon <= le))
    datos = {"nombre": a.nombre, "variable": a.variable, "unidad": unidad, "desde_utc": a.desde, "hasta_utc": a.hasta,
             "horas": len(horas), "horas_saag": len(ok), "caja": [ln, ls, lo, le], "niveles": niveles, "colores": colores,
             "max_4km": round(float(fino[caja4].max()), 1), "max_25km": round(float(grueso[caja25].max()), 1),
             "min_4km": round(float(fino[caja4].min()), 1), "min_25km": round(float(grueso[caja25].min()), 1),
             "puntos": puntos,
             "observado": (lambda o: {"nombre": o[0], **en(float(o[1]), float(o[2])), "mm_medido": float(o[3]), "fuente": o[4]}
                           if len(o) == 5 else None)(a.observado.split(";")),
             "fuentes": {"4km": "SAAG-WRF, NCAR RDA d616000 (Liu et al. 2025), CC BY 4.0",
                         "25km": "ERA5 de ECMWF/Copernicus (copia ARCO de Google), CC BY 4.0",
                         "medido": "METAR de la DGAC, archivo de Iowa State University (IEM)"}}
    json.dump(datos, open(os.path.join(SALIDA, "datos.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: datos[k] for k in ("max_4km", "max_25km", "puntos")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
