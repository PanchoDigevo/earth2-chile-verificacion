"""Lluvia horaria medida en las estaciones automáticas de la DMC de la Región Metropolitana y la cordillera central.

Las estaciones de la Dirección Meteorológica de Chile (DMC) envían cada hora un mensaje SYNOP al Sistema Mundial de
Telecomunicación de la OMM, con la lluvia de la última hora (grupo 6RRR5 de la sección 333) y la temperatura. Las que
tienen observador (Quinta Normal, Pudahuel) informan a las 00/06/12/18 UTC la lluvia de 6 h en vez de la de 1 h.
Los mensajes son datos esenciales de libre intercambio (Resolución 40 de la OMM); se leen desde Ogimet, que los
redistribuye sin clave. Se pide un bloque de 2 días por consulta, con pausas y reintentos acotados.

Guarda estaciones/datos/synop_horario.csv (una fila por estación y hora, solo las estaciones de catalogo.csv):
  wmo, hora_utc, mm_1h, mm_6h, temp_c      (vacío = no informado; 0 = informó que no llovió)

Uso:
  python estaciones/synop.py                    -> agrega las últimas 48 h
  python estaciones/synop.py --desde 2026-10-01 -> rellena desde esa fecha (UTC)
No es un aviso; las alertas oficiales son de la DMC y SENAPRED."""
import argparse, csv, datetime as dt, os, re, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "catalogo.csv")
CSV = os.path.join(AQUI, "datos", "synop_horario.csv")
CAMPOS = ["wmo", "hora_utc", "mm_1h", "mm_6h", "temp_c"]
OGIMET = "https://www.ogimet.com/cgi-bin/getsynop?block=855&begin={0:%Y%m%d%H}00&end={1:%Y%m%d%H}00"
UA = {"User-Agent": "earth2-chile-verificacion/estaciones (+https://github.com/PanchoDigevo/earth2-chile-verificacion)"}
UTC = dt.timezone.utc


def estaciones():
    """Estaciones SYNOP del catálogo: {wmo: fila}."""
    return {r["wmo"]: r for r in csv.DictReader(open(CATALOGO, encoding="utf-8")) if r["lectura"] == "synop"}


def get(url, intentos=3, espera=20, timeout=60):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                t = r.read().decode("latin-1")
            if "#" in t[:200] and "AAXX" not in t:      # Ogimet responde con un aviso cuando se le pide demasiado
                raise RuntimeError(t[:200].strip())
            return t
        except Exception as e:
            print(f"sin respuesta ({i + 1}/{intentos}): {e}", flush=True)
            if i + 1 < intentos:
                time.sleep(espera * (i + 1))
    return None


def mm(rrr):
    """Código 3590 de la OMM: 001-988 mm, 990 traza, 991-999 décimas; 000 sin lluvia."""
    if "/" in rrr:
        return None
    r = int(rrr)
    return 0.0 if r in (0, 990) else round((r - 990) / 10, 1) if r > 990 else float(r)


def decodificar(linea):
    """Una línea de Ogimet ("85565,2026,10,13,20,00,AAXX 13201 85565 ...") -> dict o None."""
    p = linea.strip().split(",", 6)
    if len(p) < 7 or "AAXX" not in p[6] or "NIL" in p[6]:
        return None
    hora = dt.datetime(*map(int, p[1:6]), tzinfo=UTC)
    g = p[6].rstrip("=").split()
    try:
        g = g[g.index(p[0]) + 1:]                    # grupos después del indicativo de la estación
    except ValueError:
        return None
    s1, s3 = [], []
    sec = 1
    for x in g:
        if x in ("333", "555", "444", "222"):
            sec = int(x[0]); continue
        (s1 if sec == 1 else s3 if sec == 3 else []).append(x)
    out = {"wmo": p[0], "hora_utc": f"{hora:%Y-%m-%d %H:%M}", "mm_1h": None, "mm_6h": None, "temp_c": None}
    for x in s1[2:]:                                 # se saltan iRixhVV y Nddff
        if len(x) != 5:
            continue
        if x[0] == "1" and x[1] in "01" and "/" not in x[2:]:
            out["temp_c"] = (-1 if x[1] == "1" else 1) * int(x[2:]) / 10
        elif x[0] == "6" and x[4] == "1":
            out["mm_6h"] = mm(x[1:4])
    seis = [x for x in s3 if len(x) == 5 and x[0] == "6"]
    if seis:                                         # el último grupo 6 de la sección 3 (antes van los de radiación)
        x = seis[-1]
        if x[4] == "5":
            out["mm_1h"] = mm(x[1:4])
        elif x[4] == "1" and out["mm_6h"] is None:
            out["mm_6h"] = mm(x[1:4])
    return out


def descargar(desde, hasta, wmos):
    filas, t = [], desde
    while t < hasta:
        f = min(t + dt.timedelta(days=2), hasta)
        txt = get(OGIMET.format(t, f))
        if txt is None:
            print(f"Ogimet no respondió para {t:%Y-%m-%d %H}–{f:%Y-%m-%d %H} UTC; se reintenta en la próxima corrida", flush=True)
        else:
            filas += [r for r in map(decodificar, txt.splitlines()) if r and r["wmo"] in wmos]
        t = f + dt.timedelta(hours=1)
        if t < hasta:
            time.sleep(5)                            # sin apuro: una consulta cada pocos segundos
    return filas


def guardar(nuevas):
    previas = {}
    if os.path.exists(CSV):
        previas = {(r["wmo"], r["hora_utc"]): r for r in csv.DictReader(open(CSV, encoding="utf-8"))}
    for r in nuevas:
        k = (r["wmo"], r["hora_utc"])
        viejo = previas.get(k, {})
        # una corrección posterior del mensaje reemplaza al anterior, pero no borra lo que ya se tenía
        previas[k] = {c: (r[c] if r.get(c) is not None else viejo.get(c, "")) for c in CAMPOS}
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS); w.writeheader()
        for k in sorted(previas, key=lambda k: (k[1], k[0])):
            w.writerow({c: ("" if previas[k][c] is None else previas[k][c]) for c in CAMPOS})
    return len(previas)


def recientes(horas=26):
    """Para la pestaña En vivo: últimas horas de las estaciones del catálogo, sin escribir el CSV."""
    hasta = dt.datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    return descargar(hasta - dt.timedelta(hours=horas), hasta, set(estaciones()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--desde", help="YYYY-MM-DD (UTC)"); a = ap.parse_args()
    hasta = dt.datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    desde = dt.datetime.strptime(a.desde, "%Y-%m-%d").replace(tzinfo=UTC) if a.desde else hasta - dt.timedelta(hours=48)
    filas = descargar(desde, hasta, set(estaciones()))
    n = guardar(filas)
    con_lluvia = sum(1 for r in filas if (r["mm_1h"] or 0) > 0 or (r["mm_6h"] or 0) > 0)
    print(f"SYNOP: {len(filas)} reportes leídos ({con_lluvia} con lluvia); {n} filas en {os.path.relpath(CSV)}")
