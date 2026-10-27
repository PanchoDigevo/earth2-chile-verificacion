"""Cámaras públicas con imagen fija (envivo/camaras.csv): baja cada imagen cuando le toca (cada_min), la reduce a 640 px
y guarda el cuadro actual (<salida>/<id>.jpg) y, si la cámara tiene archivar=1, un cuadro cada 3 horas de las últimas 48 h
(<archivo>/<id>/AAAAMMDD_HH.jpg), para poner "lo que la cámara vio" junto a "lo que el modelo decía". Escribe
<salida>/camaras.json con la hora de cada cuadro y <archivo>/index.json con las horas guardadas.

Tipos de URL:
- una imagen directa (JPG/WebP con URL estable);
- `dgac:<OACI>/<cámara>`: cámaras de aeródromos del IFIS de la DGAC (aipchile.dgac.gob.cl/camara): el nombre del archivo
  cambia en cada toma, así que se lee la página del aeródromo y se saca la última imagen de esa cámara (Norte, Sur, Este…).
  Son ~93 cámaras en 50 aeródromos, una imagen cada 10 minutos, sin clave; se citan como "DGAC, IFIS".

Lo llama el ciclo de 5 minutos de envivo.yml. YouTube no sirve para esto (bloquea a los servidores). Cada imagen se publica
citando la fuente; ver docs/camaras_publicas.md."""
import csv, datetime as dt, hashlib, io, json, os, re, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "camaras.csv")
UA = {"User-Agent": "earth2-chile-verificacion/camaras (github.com/PanchoDigevo/earth2-chile-verificacion)"}
DGAC = "https://aipchile.dgac.gob.cl"
ANCHO = 640
HORAS_ARCHIVO, PASO_ARCHIVO_H = 48, 3
_paginas = {}


def bajar(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def resolver(url):
    """URL real de la imagen. Para dgac:<OACI>/<cámara>, la última imagen de esa cámara en la página del aeródromo."""
    if not url.startswith("dgac:"):
        return url
    oaci, cam = url[5:].split("/", 1)
    if oaci not in _paginas:
        _paginas[oaci] = bajar(f"{DGAC}/camara_ubicacion/show/designador/{oaci}").decode("utf-8", "replace")
    m = re.search(r"camara/ftp/[^/\"']+/" + re.escape(cam) + r"/[^\"' ]+\.jpg", _paginas[oaci], re.I)
    if not m:
        raise LookupError(f"sin imagen para {oaci}/{cam}")
    return f"{DGAC}/{m.group(0)}"


def reducir(b):
    from PIL import Image
    im = Image.open(io.BytesIO(b)); im.load()
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if im.width > ANCHO:
        im = im.resize((ANCHO, round(im.height * ANCHO / im.width)))
    out = io.BytesIO(); im.save(out, "JPEG", quality=80, optimize=True)
    return out.getvalue()


def actualizar(salida, archivo):
    os.makedirs(salida, exist_ok=True); os.makedirs(archivo, exist_ok=True)
    ruta = os.path.join(salida, "camaras.json")
    try:
        estado = json.load(open(ruta, encoding="utf-8")).get("camaras", {})
    except Exception:
        estado = {}
    ahora = dt.datetime.now(dt.timezone.utc); t = int(ahora.timestamp())
    cams = list(csv.DictReader(open(CSV, encoding="utf-8")))
    nuevas, fallas = 0, []
    for c in cams:
        e = estado.get(c["id"], {})
        if e.get("t") and t - e["t"] < int(c["cada_min"]) * 60 - 30:
            continue
        try:
            b = reducir(bajar(resolver(c["url"])))
        except Exception as ex:
            fallas.append(f"{c['id']} ({type(ex).__name__})"); continue
        h = hashlib.md5(b).hexdigest()[:10]
        if h == e.get("hash"):                        # misma imagen que antes: la cámara no se actualizó
            estado[c["id"]] = {**e, "visto": t}; continue
        open(os.path.join(salida, f"{c['id']}.jpg"), "wb").write(b)
        if c.get("archivar", "0") == "1" and ahora.hour % PASO_ARCHIVO_H == 0:
            carpeta = os.path.join(archivo, c["id"]); os.makedirs(carpeta, exist_ok=True)
            hora = os.path.join(carpeta, f"{ahora:%Y%m%d_%H}.jpg")
            if not os.path.exists(hora):              # el primer cuadro nuevo de cada hora de archivo
                open(hora, "wb").write(b)
            for f in sorted(os.listdir(carpeta))[:-(HORAS_ARCHIVO // PASO_ARCHIVO_H)]:
                os.remove(os.path.join(carpeta, f))
        estado[c["id"]] = {"t": t, "hash": h, "visto": t, "kb": len(b) // 1024}
        nuevas += 1
    indice = {d: sorted(f[:-4] for f in os.listdir(os.path.join(archivo, d))) for d in os.listdir(archivo) if os.path.isdir(os.path.join(archivo, d)) and not d.startswith(".")}
    json.dump({"generado": t, "paso_h": PASO_ARCHIVO_H, "horas": indice}, open(os.path.join(archivo, "index.json"), "w", encoding="utf-8"), separators=(",", ":"))
    campos = ("id", "nombre", "lugar", "lat", "lon", "alt_m", "comuna", "cuenca", "fuente", "licencia", "cada_min", "archivar", "grupo")
    json.dump({"generado": t, "camaras": estado, "lista": [{k: c.get(k, "") for k in campos} for c in cams]},
              open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"cámaras: {nuevas} cuadros nuevos de {len(cams)} cámaras" + (f"; sin imagen: {', '.join(fallas[:8])}{'…' if len(fallas) > 8 else ''}" if fallas else ""), flush=True)


if __name__ == "__main__":
    import sys
    actualizar(sys.argv[1] if len(sys.argv) > 1 else "datos/envivo/camaras", sys.argv[2] if len(sys.argv) > 2 else "datos/camaras_archivo")
