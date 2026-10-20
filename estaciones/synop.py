"""Lluvia horaria medida en todas las estaciones SYNOP de Chile (bloque 85 de la OMM: de Visviri a Magallanes, Isla de
Pascua y Juan Fernández).

Las estaciones de la Dirección Meteorológica de Chile (DMC) envían cada hora un mensaje SYNOP al Sistema Mundial de
Telecomunicación de la OMM, con la lluvia de la última hora (grupo 6RRR5 de la sección 333) y la temperatura. Las que
tienen observador (Quinta Normal, Pudahuel) informan a las 00/06/12/18 UTC la lluvia de 6 h en vez de la de 1 h.
Los mensajes son datos esenciales de libre intercambio (Resolución 40 de la OMM); se leen desde Ogimet, que los
redistribuye sin clave. Se pide un bloque de 2 días por consulta, con pausas y reintentos acotados.

Guarda un CSV por mes en estaciones/datos/synop/AAAA-MM.csv (una fila por estación y hora; las estaciones están en
catalogo.csv, con nombre, coordenadas y altura):
  wmo, hora_utc, mm_1h, mm_6h, temp_c      (vacío = no informado; 0 = informó que no llovió)

Uso:
  python estaciones/synop.py                    -> agrega las últimas 48 h
  python estaciones/synop.py --desde 2026-10-01 -> rellena desde esa fecha (UTC)
  python estaciones/synop.py --catalogo         -> agrega a catalogo.csv las estaciones chilenas nuevas de Ogimet
No es un aviso; las alertas oficiales son de la DMC y SENAPRED."""
import argparse, csv, datetime as dt, os, re, time, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "catalogo.csv")
CARPETA = os.path.join(AQUI, "datos", "synop")
CAMPOS = ["wmo", "hora_utc", "mm_1h", "mm_6h", "temp_c"]
OGIMET = "https://www.ogimet.com/cgi-bin/getsynop?block={b}&begin={0:%Y%m%d%H}00&end={1:%Y%m%d%H}00"
LISTA = "https://www.ogimet.com/display_stations.php?lang=en&tipo=AND&isyn=&oaci=&nombre=&estado=Chile&Send=Send"
COLUMNAS_CAT = ["red", "codigo", "wmo", "nombre", "lat", "lon", "altura_m", "lectura", "nota"]
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


def descargar(desde, hasta, wmos, bloque="85"):
    """bloque "85" = todo Chile; "855" = zona central (lo que usa la pestaña En vivo)."""
    filas, t = [], desde
    while t < hasta:
        f = min(t + dt.timedelta(days=1), hasta)
        txt = get(OGIMET.format(t, f, b=bloque))
        if txt is None:
            print(f"Ogimet no respondió para {t:%Y-%m-%d %H}–{f:%Y-%m-%d %H} UTC; se reintenta en la próxima corrida", flush=True)
        else:
            filas += [r for r in map(decodificar, txt.splitlines()) if r and r["wmo"] in wmos]
        t = f + dt.timedelta(hours=1)
        if t < hasta:
            time.sleep(5)                            # sin apuro: una consulta cada pocos segundos
    return filas


def archivo(mes):
    return os.path.join(CARPETA, f"{mes}.csv")


def guardar(nuevas):
    """Mezcla los reportes nuevos en el CSV de su mes. Devuelve el total de filas de los meses tocados."""
    por_mes = {}
    for r in nuevas:
        por_mes.setdefault(r["hora_utc"][:7], []).append(r)
    total = 0
    for mes, filas in por_mes.items():
        ruta, previas = archivo(mes), {}
        if os.path.exists(ruta):
            previas = {(r["wmo"], r["hora_utc"]): r for r in csv.DictReader(open(ruta, encoding="utf-8"))}
        for r in filas:
            k = (r["wmo"], r["hora_utc"])
            viejo = previas.get(k, {})
            # una corrección posterior del mensaje reemplaza al anterior, pero no borra lo que ya se tenía
            previas[k] = {c: (r[c] if r.get(c) is not None else viejo.get(c, "")) for c in CAMPOS}
        os.makedirs(CARPETA, exist_ok=True)
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPOS); w.writeheader()
            for k in sorted(previas, key=lambda k: (k[1], k[0])):
                w.writerow({c: ("" if previas[k][c] is None else previas[k][c]) for c in CAMPOS})
        total += len(previas)
    return total


def leer(wmos=None):
    """Todas las filas guardadas (de todos los meses), opcionalmente solo de algunas estaciones."""
    out = []
    for n in sorted(os.listdir(CARPETA)) if os.path.isdir(CARPETA) else []:
        if n.endswith(".csv"):
            out += [r for r in csv.DictReader(open(os.path.join(CARPETA, n), encoding="utf-8")) if wmos is None or r["wmo"] in wmos]
    return out


def recientes(horas=26, bloque="855"):
    """Para la pestaña En vivo: últimas horas de la zona central, sin escribir los CSV."""
    hasta = dt.datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    return descargar(hasta - dt.timedelta(hours=horas), hasta, set(estaciones()), bloque)


def actualizar_catalogo():
    """Agrega a catalogo.csv las estaciones SYNOP chilenas (bloque 85) de la lista de Ogimet que aún no estén.
    Las filas existentes (nombres y notas escritos a mano) no se tocan."""
    import html as h
    t = get(LISTA)
    if not t:
        print("no se pudo leer la lista de estaciones de Ogimet"); return
    t = t.encode("latin-1").decode("utf-8", "replace")
    def grados(x):
        a = re.match(r"(\d+)-(\d+)(?:-(\d+))?([NSEW])", x)
        v = int(a[1]) + int(a[2]) / 60 + int(a[3] or 0) / 3600
        return round(-v if a[4] in "SW" else v, 4)
    filas = list(csv.DictReader(open(CATALOGO, encoding="utf-8")))
    hay, nuevas = {r["wmo"] for r in filas if r["wmo"]}, []
    for fila in t.split("<tr>"):
        m = re.search(r"ind=(85\d{3})", fila)
        if not m or m[1] in hay:
            continue
        w = re.search(r"wigos=0-152-\d-(\d+)", fila)
        fila = re.sub(r'onmouse\w+="[^"]*"', "", fila)          # los textos emergentes traen etiquetas que confunden
        c = [h.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", fila, flags=re.S)]
        c = c[2:]                                                  # WIGOS, índice | OACI, nombre, país, lat, lon, altura
        if len(c) < 6:
            continue
        try:
            la, lo, alt = grados(c[3]), grados(c[4]), int(float(c[5] or 0))
        except Exception:
            continue
        hay.add(m[1])
        nuevas.append({"red": "DMC" if w else "SYNOP", "codigo": w[1] if w else "", "wmo": m[1], "nombre": c[1].strip(" ,"), "lat": la, "lon": lo,
                       "altura_m": alt, "lectura": "synop", "nota": ""})
    synop = [r for r in filas if r["lectura"] == "synop"] + nuevas
    resto = [r for r in filas if r["lectura"] != "synop"]
    synop.sort(key=lambda r: r["wmo"])
    with open(CATALOGO, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=COLUMNAS_CAT); wr.writeheader(); wr.writerows(synop + resto)
    print(f"catálogo: {len(nuevas)} estaciones nuevas; {len(synop)} SYNOP en total")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--desde", help="YYYY-MM-DD (UTC)"); ap.add_argument("--catalogo", action="store_true")
    a = ap.parse_args()
    if a.catalogo:
        actualizar_catalogo(); raise SystemExit
    hasta = dt.datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    desde = dt.datetime.strptime(a.desde, "%Y-%m-%d").replace(tzinfo=UTC) if a.desde else hasta - dt.timedelta(hours=48)
    filas = descargar(desde, hasta, set(estaciones()))
    n = guardar(filas)
    con_lluvia = sum(1 for r in filas if (r["mm_1h"] or 0) > 0 or (r["mm_6h"] or 0) > 0)
    print(f"SYNOP: {len(filas)} reportes de {len({r['wmo'] for r in filas})} estaciones ({con_lluvia} con lluvia); "
          f"{n} filas en los meses tocados de {os.path.relpath(CARPETA)}")
