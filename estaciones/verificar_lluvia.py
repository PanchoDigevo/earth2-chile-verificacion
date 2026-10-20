"""Verifica el pronóstico de lluvia del seguimiento horario contra la lluvia medida en las estaciones DMC.

Para cada punto del seguimiento (hindcast/seguimiento/pronosticos.csv: quebradas quemadas, Tobalaba, Pudahuel) toma
la estación SYNOP más cercana bajo 1.500 m (la de cordillera mide mal la nieve y es otro clima) y compara cada bloque
de 6 h pronosticado con lo medido en ese mismo bloque: el total de 6 h que informan las estaciones con observador, o la
suma de las 6 lluvias horarias si llegaron las 6. Los bloques sin las 6 horas no se comparan.

Escribe estaciones/verificacion_lluvia.csv (una fila por modelo, corrida, bloque y punto) y
estaciones/VERIFICACION_LLUVIA.md (resumen por modelo y plazo). Solo biblioteca estándar.

Uso: python estaciones/verificar_lluvia.py"""
import csv, datetime as dt, json, math, os
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
PRONOS = os.path.join(RAIZ, "hindcast", "seguimiento", "pronosticos.csv")
SALIDA = os.path.join(AQUI, "verificacion_lluvia.csv")
RESUMEN = os.path.join(AQUI, "VERIFICACION_LLUVIA.md")
AEROPUERTOS = {"SCTB": (-33.456, -70.547), "SCEL": (-33.393, -70.786)}
ALTURA_MAX = 1500
UMBRAL = 1.0          # mm en 6 h: desde aquí un bloque cuenta como "con lluvia"
UTC = dt.timezone.utc
try:
    from zoneinfo import ZoneInfo
    CL = ZoneInfo("America/Santiago")
except Exception:
    CL = dt.timezone(dt.timedelta(hours=-3))


def km(a, b):
    r = math.pi / 180
    h = math.sin((b[0] - a[0]) * r / 2) ** 2 + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin((b[1] - a[1]) * r / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def centros():
    """Centro de cada cuenca (promedio de los vértices del contorno exterior) y los aeródromos."""
    out = dict(AEROPUERTOS)
    cu = json.load(open(os.path.join(RAIZ, "site", "quebradas", "cuencas.geojson"), encoding="utf-8"))
    for f in cu["features"]:
        g = f["geometry"]
        anillos = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        v = [c for a in anillos for c in a]
        out[f"Q{f['properties']['id']}"] = (sum(c[1] for c in v) / len(v), sum(c[0] for c in v) / len(v))
    return out


def estacion_para(p, est):
    cand = [(km(p, (float(e["lat"]), float(e["lon"]))), w) for w, e in est.items() if float(e["altura_m"]) < ALTURA_MAX]
    return min(cand)


def observado(obs, wmo, fin_utc):
    """Lluvia medida en las 6 h que terminan en fin_utc, o None si faltan datos."""
    o = obs.get(wmo, {})
    r = o.get(fin_utc)
    if r and r["mm_6h"] != "":
        return float(r["mm_6h"])
    horas = [o.get(fin_utc - dt.timedelta(hours=k)) for k in range(6)]
    if all(h and h["mm_1h"] != "" for h in horas):
        return round(sum(float(h["mm_1h"]) for h in horas), 1)
    return None


def main():
    import synop
    est = synop.estaciones()
    obs = defaultdict(dict)
    for r in synop.leer(set(est)):
        obs[r["wmo"]][dt.datetime.strptime(r["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)] = r
    pts, elegida, filas = centros(), {}, []
    for r in csv.DictReader(open(PRONOS, encoding="utf-8")):
        p = r["punto"]
        if p not in pts:
            continue
        if p not in elegida:
            elegida[p] = estacion_para(pts[p], est)
        d, wmo = elegida[p]
        fin = dt.datetime.strptime(r["bloque_fin_chile"], "%Y-%m-%d %H:%M").replace(tzinfo=CL).astimezone(UTC)
        ob = observado(obs, wmo, fin)
        if ob is None:
            continue
        filas.append({"modelo": r["modelo"], "corrida_utc": r["corrida_utc"], "plazo_h": r["plazo_h"],
                      "bloque_inicio_chile": r["bloque_inicio_chile"], "bloque_fin_chile": r["bloque_fin_chile"],
                      "punto": p, "nombre": r["nombre"], "estacion": est[wmo]["nombre"], "wmo": wmo, "dist_km": round(d, 1),
                      "pronostico_mm": r["mm_6h"], "observado_mm": ob})
    campos = ["modelo", "corrida_utc", "plazo_h", "bloque_inicio_chile", "bloque_fin_chile", "punto", "nombre", "estacion",
              "wmo", "dist_km", "pronostico_mm", "observado_mm"]
    with open(SALIDA, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); w.writerows(filas)

    # resumen por modelo y plazo (24 h = plazos 6 a 24; 48 h = 30 a 48; 72 h = 54 a 72)
    g = defaultdict(list)
    for f in filas:
        g[(f["modelo"], (int(f["plazo_h"]) - 1) // 24 * 24 + 24)].append((float(f["pronostico_mm"]), f["observado_mm"]))
    ahora = dt.datetime.now(UTC).astimezone(CL)
    lin = ["# Lluvia pronosticada frente a lluvia medida", "",
           f"Actualizado el {ahora:%d-%m-%Y %H:%M} (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento",
           f"horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo {ALTURA_MAX:,} m".replace(",", "."),
           f"(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde {UMBRAL:g} mm en 6 h.", "",
           "Estación usada para cada punto:", ""]
    nom = {r["punto"]: r["nombre"] for r in filas}
    for p, (d, wmo) in sorted(elegida.items()):
        lin.append(f"- {nom.get(p, p)}: {est[wmo]['nombre']} ({est[wmo]['altura_m']} m), a {d:.0f} km")
    lin += ["", "| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |",
            "|---|---|---|---|---|---|---|---|"]
    for (m, pl), v in sorted(g.items()):
        llov = [x for x in v if x[1] >= UMBRAL]
        av = sum(1 for x in llov if x[0] >= UMBRAL)
        fa = sum(1 for x in v if x[0] >= UMBRAL and x[1] < UMBRAL)
        err = sum(x[0] - x[1] for x in v) / len(v)
        sp, so = sum(x[0] for x in v), sum(x[1] for x in v)
        lin.append(f"| {m} | hasta {pl} h | {len(v)} | {len(llov)} | {av} | {fa} | {err:+.1f} | {so:.1f} / {sp:.1f} |".replace(".", ","))
    if not g:
        lin.append("| – | – | 0 | – | – | – | – | – |")
    lin += ["", "Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,",
            "sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED."]
    open(RESUMEN, "w", encoding="utf-8").write("\n".join(lin) + "\n")
    print("\n".join(lin))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, AQUI)
    main()
