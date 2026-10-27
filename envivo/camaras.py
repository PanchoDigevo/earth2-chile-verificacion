"""Cámaras públicas con imagen fija (envivo/camaras.csv): baja cada imagen cuando le toca (cada_min), la reduce a 640 px
y guarda el cuadro actual (<salida>/<id>.jpg) más uno por hora de las últimas 48 h (<archivo>/<id>/AAAAMMDD_HH.jpg), para
poner "lo que la cámara vio" junto a "lo que el modelo decía". Escribe <salida>/camaras.json con la hora de cada cuadro.

Lo llama envivo/actualizar.py en cada vuelta de 5 minutos. Solo cámaras cuya imagen tiene URL estable y se puede leer por
programa (ver docs/camaras_publicas.md); YouTube no sirve para esto. Cada imagen se publica citando la fuente."""
import csv, datetime as dt, hashlib, io, json, os, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "camaras.csv")
UA = {"User-Agent": "earth2-chile-verificacion/camaras (github.com/PanchoDigevo/earth2-chile-verificacion)"}
ANCHO = 640
HORAS_ARCHIVO = 48


def bajar(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


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
    nuevas = 0
    for c in cams:
        e = estado.get(c["id"], {})
        if t - e.get("t", 0) < int(c["cada_min"]) * 60 - 30 and e.get("t"):
            continue
        try:
            b = reducir(bajar(c["url"]))
        except Exception as ex:
            print(f"cámaras: {c['id']} sin imagen ({type(ex).__name__})", flush=True); continue
        h = hashlib.md5(b).hexdigest()[:10]
        if h == e.get("hash"):                        # misma imagen que antes: la cámara no se actualizó
            estado[c["id"]] = {**e, "visto": t}; continue
        open(os.path.join(salida, f"{c['id']}.jpg"), "wb").write(b)
        carpeta = os.path.join(archivo, c["id"]); os.makedirs(carpeta, exist_ok=True)
        hora = os.path.join(carpeta, f"{ahora:%Y%m%d_%H}.jpg")
        if not os.path.exists(hora):                  # el primer cuadro nuevo de cada hora queda en el archivo
            open(hora, "wb").write(b)
        for f in sorted(os.listdir(carpeta))[:-HORAS_ARCHIVO]:
            os.remove(os.path.join(carpeta, f))
        estado[c["id"]] = {"t": t, "hash": h, "visto": t, "kb": len(b) // 1024}
        nuevas += 1
    json.dump({"generado": t, "camaras": estado, "lista": [{k: c[k] for k in ("id", "nombre", "lugar", "lat", "lon", "alt_m", "fuente", "licencia", "cada_min")} for c in cams]},
              open(ruta, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"cámaras: {nuevas} cuadros nuevos de {len(cams)} cámaras", flush=True)


if __name__ == "__main__":
    import sys
    actualizar(sys.argv[1] if len(sys.argv) > 1 else "datos/envivo/camaras", sys.argv[2] if len(sys.argv) > 2 else "datos/camaras_archivo")
