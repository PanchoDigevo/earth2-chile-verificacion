import sys, urllib.request, numpy as np, eccodes as ec, math
G = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
QUIERO = [("CAPE", "surface"), ("CAPE", "180-0 mb above ground"), ("CIN", "surface"), ("HLCY", "3000-0 m above ground"), ("LFTX", "surface"),
          ("GUST", "surface"), ("UGRD", "10 m above ground"), ("VGRD", "10 m above ground"), ("UGRD", "500 mb"), ("VGRD", "500 mb"),
          ("UGRD", "850 mb"), ("VGRD", "850 mb")]
LA, LO = -34.28, -70.82
def rango(idx, var, niv):
    L = [l.split(":") for l in idx.splitlines() if l]
    for i, c in enumerate(L):
        if c[3] == var and c[4] == niv and "ave" not in c[5] and "max" not in c[5]:
            return int(c[1]), int(L[i + 1][1]) - 1
def leer(run, hh, f):
    base = f"{G}/gfs.{run}/{hh}/atmos/gfs.t{hh}z.pgrb2.0p25.f{f:03d}"
    idx = urllib.request.urlopen(base + ".idx", timeout=60).read().decode()
    out = {}
    for var, niv in QUIERO:
        r = rango(idx, var, niv)
        if not r: continue
        b = urllib.request.urlopen(urllib.request.Request(base, headers={"Range": f"bytes={r[0]}-{r[1]}"}), timeout=120).read()
        g = ec.codes_new_from_message(b)
        la = ec.codes_get_double_array(g, "latitudes"); lo = ec.codes_get_double_array(g, "longitudes"); v = ec.codes_get_values(g)
        dist = np.hypot(la - LA, (lo - (LO % 360)) * math.cos(math.radians(LA)))
        cerca = dist < 0.5          # ~50 km
        out[(var, niv)] = (float(v[np.argmin(dist)]), float(v[cerca].max()), float(v[cerca].min()))
        ec.codes_release(g)
    return out
for run, hh, f, nombre in [("20251025", "12", 33, "ayer 09:00 (33 h antes)"), ("20261025", "12", 33, "ayer 09:00 (33 h antes)"), ("20261026", "00", 21, "hoy 21:00 (-3) (21 h antes)"), ("20261026", "06", 15, "hoy 03:00 (15 h antes)")][1:]:
    try:
        o = leer(run, hh, f)
    except Exception as e:
        print(nombre, "error", e); continue
    g = lambda k, i=0: o.get(k, (np.nan,) * 3)[i]
    u10, v10 = g(("UGRD", "10 m above ground")), g(("VGRD", "10 m above ground")); u5, v5 = g(("UGRD", "500 mb")), g(("VGRD", "500 mb")); u8, v8 = g(("UGRD", "850 mb")), g(("VGRD", "850 mb"))
    print(f"GFS {run} {hh}Z, válido 21 UTC (18:00 Chile) — corrida de {nombre}")
    print(f"   CAPE superficie {g(('CAPE','surface')):.0f} J/kg (máx. 50 km {g(('CAPE','surface'),1):.0f}) | CAPE capa 180 hPa {g(('CAPE','180-0 mb above ground')):.0f} | CIN {g(('CIN','surface')):.0f}")
    print(f"   Helicidad 0-3 km {g(('HLCY','3000-0 m above ground')):.0f} m²/s² (más negativa a 50 km {g(('HLCY','3000-0 m above ground'),2):.0f}) | índice de levantamiento {g(('LFTX','surface')):.1f}")
    print(f"   Cizalle 10 m-500 hPa {math.hypot(u5-u10, v5-v10)*1.944:.0f} kt | 10 m-850 hPa {math.hypot(u8-u10, v8-v10)*1.944:.0f} kt | ráfaga {g(('GUST','surface'))*3.6:.0f} km/h (máx. {g(('GUST','surface'),1)*3.6:.0f})")
