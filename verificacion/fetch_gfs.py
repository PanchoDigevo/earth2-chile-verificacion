"""Descarga GFS (NOAA, dominio público) desde el bucket público noaa-gfs-bdp-pds en S3: TMP 2 m,
UGRD/VGRD 10 m, APCP y nubosidad total (TCDC) a 0,25°, plazos 0-48 h.
Uso: python fetch_gfs.py              -> última corrida completa disponible
     python fetch_gfs.py 2026-10-13 6 -> corrida específica (fecha, hora UTC)

Cada archivo pgrb2 de GFS pesa ~550 MB; aquí se leen solo los mensajes que interesan, con
peticiones por rangos de bytes guiadas por el índice .idx (igual que hace wgrib2 o Herbie).
La corrida se elige con HEAD a los .idx del plazo 0 y 48 h, con reintentos acotados."""
import os, time, urllib.request
from corridas import STEPS, corrida_pedida

BASE = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
# (variable, nivel) tal como aparecen en el .idx de NCEP.
CAMPOS = [("TMP", "2 m above ground"), ("UGRD", "10 m above ground"), ("VGRD", "10 m above ground"), ("APCP", "surface"),
          ("TCDC", "entire atmosphere")]   # nubosidad total, para el ícono del pronóstico (solo la instantánea, no el promedio de 6 h)
os.makedirs("data", exist_ok=True)


def url_grib(run, step):
    return f"{BASE}/gfs.{run:%Y%m%d}/{run:%H}/atmos/gfs.t{run:%H}z.pgrb2.0p25.f{step:03d}"


def url_indice(run, step):
    return url_grib(run, step) + ".idx"


def leer(url, headers=None, intentos=4, timeout=60):
    """GET con reintentos acotados (espera 20 s entre intentos)."""
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print(f"  intento {i + 1}/{intentos} falló ({e}); reintento en 20 s")
            time.sleep(20)
    raise SystemExit(f"GFS: no se pudo leer {url}")


def rangos(idx_texto):
    """Devuelve [(inicio, fin_o_None)] de los mensajes buscados, a partir del índice .idx.
    Cada línea es num:offset:fecha:variable:nivel:plazo: ; el fin de un mensaje es el offset del siguiente."""
    lineas = [l.split(":") for l in idx_texto.decode().splitlines() if l.strip()]
    out = []
    for i, campos in enumerate(lineas):
        if len(campos) < 6:
            continue
        if (campos[3], campos[4]) in CAMPOS and not (campos[3] == "TCDC" and "ave" in campos[5]):
            inicio = int(campos[1])
            fin = int(lineas[i + 1][1]) - 1 if i + 1 < len(lineas) else None
            out.append((inicio, fin))
    return out


run = corrida_pedida("GFS", url_indice)
name = f"data/gfs_{run:%Y%m%d_%H}.grib2"
if os.path.exists(name):
    print("GFS run:", run, "ya descargado en", name)
    raise SystemExit(0)

t0 = time.time()
tmp = "data/_dl_gfs.grib2"
total = 0
with open(tmp, "wb") as out:
    for step in STEPS:
        partes = rangos(leer(url_indice(run, step)))
        if not partes:
            raise SystemExit(f"GFS: el índice del plazo {step} h no trae los campos esperados")
        for inicio, fin in partes:
            rango = f"bytes={inicio}-" + ("" if fin is None else str(fin))
            datos = leer(url_grib(run, step), headers={"Range": rango})
            out.write(datos); total += len(datos)
        print(f"  plazo {step:2d} h: {len(partes)} mensajes")
os.replace(tmp, name)
print("GFS run:", run, "->", name, f"({total // 1024 // 1024} MB) en", round(time.time() - t0), "s")
