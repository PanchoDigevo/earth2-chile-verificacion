"""Indicador de flujo de detritos por cuenca, recalculado 4 veces al día dentro del pipeline de verificación.

Entradas (todas ya presentes cuando corre verify.py):
  site/quebradas/cuencas.geojson          estadísticas estáticas por cuenca (prop_hm23, dnbr_medio, pendiente, % quemado)
  verificacion/data/aifs_*.grib2, gfs_*.grib2   última corrida: precipitación acumulada (tp / APCP) a 6 y 24 h
  verificacion/data/metar_obs.csv         METAR crudo de SCTB y SCEL: horas con lluvia reportada en los últimos 7 días
Salida: site/quebradas/indicador.json

Regla (documentada en la página): modelo USGS post-incendio M1 (Staley et al. 2017),
  P = 1 / (1 + exp(−X)),  X = −3,63 + 0,41·(PropHM23·I) + 0,67·(dNBR·I) + 0,70·(KF·I)
  I = intensidad de lluvia en mm/h (en el USGS, la de 15 min). Aquí I = lluvia de la ventana / 2 h, es decir, se supone
  que la lluvia de 6 h cae concentrada en 2 h (supuesto conservador para convección de precordillera).
  KF (erodabilidad del suelo) no existe para Chile: se usa 0,25, valor típico de suelos coluviales; es un supuesto.
  Humedad antecedente: no está en el modelo USGS; se agrega un factor 1 + 0,02·(horas con lluvia en 7 días), tope 1,4.
Niveles del indicador: bajo (P < 0,2), atención (0,2 a 0,5), aviso de impacto (P ≥ 0,5). Nunca "alerta": eso es de la DMC y SENAPRED.
Cuencas con menos de 1 % de su superficie quemada y empinada (PropHM23 < 0,01) quedan como "sin_quema": la regla es para
laderas quemadas y en ellas el resultado lo dominaría el supuesto de suelo (KF), no la quema.
Para cada cuenca quemada se publica además la lluvia en 2 h que la llevaría a atención y a aviso (inversa de la regla)."""
import csv, datetime as dt, glob, json, os, re

AQUI = os.path.dirname(os.path.abspath(__file__))
SITE_Q = os.path.join(AQUI, "..", "site", "quebradas")
VDATA = os.path.join(AQUI, "..", "verificacion", "data")
CENTRO = (-33.42, -70.50)          # lat, lon del centro del área (precordillera de Las Condes)
KF = 0.25
B0, B1, B2, B3 = -3.63, 0.41, 0.67, 0.70
HORAS_CONCENTRACION = 2.0
UMBRALES = (0.2, 0.5)
PROP_MIN = 0.01
RE_LLUVIA = re.compile(r"(?<![A-Z])(?:[-+]?)(?:SH|TS|FZ)?(?:RA|DZ|SN|GR|GS|PL|UP)(?![A-Z])")


def probabilidad(mm, horas, prop_hm23, dnbr, factor_ant=1.0):
    """P del modelo USGS M1 con la lluvia 'mm' concentrada en 'horas'."""
    import math
    i = (mm / horas) * factor_ant
    x = B0 + B1 * (prop_hm23 or 0.0) * i + B2 * (dnbr or 0.0) * i + B3 * KF * i
    if math.isnan(x):
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def lluvia_umbral(p_obj, prop_hm23, dnbr, factor_ant=1.0, horas=HORAS_CONCENTRACION):
    """mm en 'horas' que llevan la probabilidad a p_obj (inversa del modelo M1)."""
    import math
    coef = B1 * (prop_hm23 or 0.0) + B2 * (dnbr or 0.0) + B3 * KF
    i = (math.log(p_obj / (1 - p_obj)) - B0) / coef
    return max(0.0, i * horas / factor_ant)


def nivel(p):
    return "bajo" if p < UMBRALES[0] else "atencion" if p < UMBRALES[1] else "aviso"


def lluvia_pronosticada():
    """mm acumulados a 6 y 24 h en el punto de grilla más cercano al centro, por modelo (AIFS, GFS)."""
    out = {}
    try:
        import eccodes as ec
    except ImportError:
        return out
    for modelo, patron, clave in (("AIFS", "aifs_*.grib2", "tp"), ("GFS", "gfs_*.grib2", "tp")):
        archivos = sorted(glob.glob(os.path.join(VDATA, patron)))
        if not archivos:
            continue
        f = archivos[-1]
        corrida = os.path.basename(f).split("_", 1)[1].replace(".grib2", "")
        acum = {}
        with open(f, "rb") as fh:
            while True:
                gid = ec.codes_grib_new_from_file(fh)
                if gid is None:
                    break
                try:
                    if ec.codes_get(gid, "shortName") != clave:
                        continue
                    paso = int(ec.codes_get(gid, "endStep"))
                    v = ec.codes_grib_find_nearest(gid, CENTRO[0], CENTRO[1])[0].value
                    if ec.codes_get(gid, "units") == "m":
                        v *= 1000.0
                    acum[paso] = max(acum.get(paso, 0.0), float(v))
                finally:
                    ec.codes_release(gid)
        if acum:
            out[modelo] = {"corrida": corrida, "mm6": round(acum.get(6, 0.0), 1), "mm24": round(acum.get(24, 0.0), 1), "mm48": round(acum.get(48, 0.0), 1)}
    return out


def horas_lluvia_7d():
    """Horas con algún reporte de lluvia (RA, SHRA, TSRA, DZ...) en SCTB o SCEL en los últimos 7 días."""
    ruta = os.path.join(VDATA, "metar_obs.csv")
    if not os.path.exists(ruta):
        return {}
    desde = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    horas = {}
    for r in csv.DictReader(open(ruta, encoding="utf-8")):
        if r["icao"] not in ("SCTB", "SCEL"):
            continue
        try:
            t = dt.datetime.fromisoformat(r["time"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if t < desde:
            continue
        raw = r.get("raw", "")
        cuerpo = raw.split(" RMK")[0]
        if RE_LLUVIA.search(cuerpo):
            horas.setdefault(r["icao"], set()).add(t.strftime("%Y-%m-%d %H"))
    return {k: len(v) for k, v in horas.items()}


def main():
    try:
        cuencas = json.load(open(os.path.join(SITE_Q, "cuencas.geojson"), encoding="utf-8"))["features"]
    except FileNotFoundError:
        print("sin cuencas.geojson todavía; el indicador se calcula cuando existan las capas estáticas"); return
    pron = lluvia_pronosticada()
    ruta_salida = os.path.join(SITE_Q, "indicador.json")
    if not pron and os.path.exists(ruta_salida):
        previo = json.load(open(ruta_salida, encoding="utf-8"))
        pron = previo.get("lluvia_prevista") or {}
        if not pron:
            print("sin GRIB de modelos ni lluvia previa: se conserva el indicador.json anterior"); return
        print("sin GRIB en este job: se recalcula con la lluvia prevista del indicador anterior")
    h7 = horas_lluvia_7d()
    horas7 = max(h7.values()) if h7 else 0
    factor_ant = min(1.4, 1.0 + 0.02 * horas7)
    ref = pron.get("AIFS") or pron.get("GFS") or {}
    mm6 = max((m["mm6"] for m in pron.values()), default=0.0)     # el más lluvioso de los modelos, por prudencia
    mm24 = max((m["mm24"] for m in pron.values()), default=0.0)
    filas = []
    for f in cuencas:
        p = f["properties"]
        p6 = probabilidad(mm6, HORAS_CONCENTRACION, p["prop_hm23"], p["dnbr_medio"], factor_ant)
        p24 = probabilidad(mm24, HORAS_CONCENTRACION * 4, p["prop_hm23"], p["dnbr_medio"], factor_ant)
        p_ref = max(p6, p24)
        quemada = (p.get("prop_hm23") or 0.0) >= PROP_MIN
        filas.append({"id": p["id"], "nombre": p["nombre"], "p6": round(p6, 3), "p24": round(p24, 3), "p": round(p_ref, 3),
                      "nivel": nivel(p_ref) if quemada else "sin_quema",
                      "mm_atencion": round(lluvia_umbral(UMBRALES[0], p["prop_hm23"], p["dnbr_medio"], factor_ant), 1) if quemada else None,
                      "mm_aviso": round(lluvia_umbral(UMBRALES[1], p["prop_hm23"], p["dnbr_medio"], factor_ant), 1) if quemada else None})
    salida = {
        "generado": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "lluvia_prevista": pron, "mm6": mm6, "mm24": mm24, "horas_lluvia_7d": h7, "factor_antecedente": round(factor_ant, 2),
        "parametros": {"KF": KF, "beta": [B0, B1, B2, B3], "horas_concentracion": HORAS_CONCENTRACION, "umbrales": UMBRALES, "prop_min": PROP_MIN},
        "cuencas": filas,
    }
    os.makedirs(SITE_Q, exist_ok=True)
    with open(os.path.join(SITE_Q, "indicador.json"), "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=0)
    n = {k: sum(1 for r in filas if r["nivel"] == k) for k in ("bajo", "atencion", "aviso", "sin_quema")}
    print(f"indicador: lluvia prevista 6 h {mm6} mm, 24 h {mm24} mm ({', '.join(pron) or 'sin modelos'}); horas de lluvia 7 d {h7}; cuencas {n}")


if __name__ == "__main__":
    main()
