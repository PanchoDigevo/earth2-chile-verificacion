"""Salto de rayos (lightning jump): una tormenta cuya tasa de rayos se dispara suele estar intensificándose, y en EE.UU. el
salto antecede en promedio unos 20-30 minutos al granizo, las rachas dañinas o un tornado.

Algoritmo "2σ" de Schultz, Petersen y Carey (2009, J. Appl. Meteor. Climatol. 48; 2011, Wea. Forecasting 26), con sus
parámetros publicados, sin ajustar a ningún evento chileno:
- tasa de rayos en intervalos de 2 minutos (rayos por minuto);
- DFRDT = cambio de la tasa entre intervalos consecutivos (rayos/min²);
- hay salto cuando DFRDT supera 2 desviaciones estándar de los DFRDT de los 10 minutos previos (5 intervalos)
  y la tasa es de al menos 10 rayos por minuto (umbral mínimo del estudio).
En EE.UU. acertó el 79 % de los eventos severos con 36 % de falsas alarmas (Schultz et al. 2011). Chile no tiene un
registro de eventos severos con el que medirlo: ver hindcast/salto_rayos/ para lo que se mide aquí.

Las "tormentas" se aproximan con cuadros de 0,3° (unos 30 km), sumando una grilla de 0,1° en vecindarios de 3×3; se
informa solo el máximo local, para no repetir la misma tormenta. El GLM ve menos rayos que las redes en tierra de los
estudios, así que el umbral de 10 por minuto es exigente, no laxo."""
import math
import numpy as np

PASO_S = 120          # intervalos de 2 minutos
HISTORIA = 5          # 10 minutos de historia para la desviación estándar
SIGMAS = 2.0
TASA_MIN = 10.0       # rayos por minuto
CELDA = 0.1


def detectar(rayos, fin=None, desde=None):
    """rayos: lista de (lat, lon, t_unix). Devuelve los saltos [{lat, lon, t, tasa, dfrdt, sigma}] (t = fin del intervalo),
    uno por tormenta e intervalo, en orden de tiempo."""
    if not rayos:
        return []
    a = np.asarray(rayos, dtype=float)
    t0 = (a[:, 2].min() // PASO_S) * PASO_S
    fin = a[:, 2].max() if fin is None else fin
    n = int((fin - t0) // PASO_S) + 1
    i = np.floor(a[:, 0] / CELDA).astype(int); j = np.floor(a[:, 1] / CELDA).astype(int)
    i0, j0 = i.min() - 1, j.min() - 1
    g = np.zeros((n, i.max() - i0 + 2, j.max() - j0 + 2))
    k = ((a[:, 2] - t0) // PASO_S).astype(int)
    ok = k < n
    np.add.at(g, (k[ok], i[ok] - i0, j[ok] - j0), 1)
    # suma de 3×3 vecinos: la "tormenta" alrededor de cada cuadro
    s = sum(np.roll(np.roll(g, di, 1), dj, 2) for di in (-1, 0, 1) for dj in (-1, 0, 1))
    tasa = s / (PASO_S / 60)                                  # rayos por minuto
    dfrdt = np.diff(tasa, axis=0, prepend=0) / (PASO_S / 60)  # rayos/min²
    salida = []
    for kk in range(HISTORIA + 1, n):
        if desde is not None and t0 + (kk + 1) * PASO_S < desde:
            continue
        hist = dfrdt[kk - HISTORIA:kk]
        sig = hist.std(axis=0)
        cand = (tasa[kk] >= TASA_MIN) & (dfrdt[kk] > SIGMAS * sig) & (sig > 0)
        if not cand.any():
            continue
        # máximo local de la tasa entre los candidatos (una sola marca por tormenta)
        loc = tasa[kk] >= np.max([np.roll(np.roll(tasa[kk], di, 0), dj, 1) for di in (-1, 0, 1) for dj in (-1, 0, 1)], axis=0)
        for ii, jj in zip(*np.where(cand & loc)):
            salida.append({"lat": round((ii + i0 + 0.5) * CELDA, 2), "lon": round((jj + j0 + 0.5) * CELDA, 2),
                           "t": int(t0 + (kk + 1) * PASO_S), "tasa": round(float(tasa[kk, ii, jj]), 1),
                           "dfrdt": round(float(dfrdt[kk, ii, jj]), 1), "sigma": round(float(sig[ii, jj]), 1)})
    return salida


def km(a, b):
    return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians(a[0])))
