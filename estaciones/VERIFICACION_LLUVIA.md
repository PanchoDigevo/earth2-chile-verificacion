# Lluvia pronosticada frente a lluvia medida

Actualizado el 19-11-2026 10:50 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1736 | 108 | 105 | 478 | +0,8 | 666,0 / 2053,4 |
| AIFS | hasta 48 h | 1680 | 108 | 99 | 475 | +0,6 | 661,3 / 1737,6 |
| AIFS | hasta 72 h | 1618 | 84 | 72 | 426 | +0,7 | 443,9 / 1504,5 |
| GFS | hasta 24 h | 1776 | 108 | 95 | 319 | +0,6 | 666,0 / 1669,4 |
| GFS | hasta 48 h | 1706 | 108 | 93 | 251 | +0,4 | 661,3 / 1408,4 |
| GFS | hasta 72 h | 1644 | 84 | 74 | 213 | +0,3 | 445,5 / 960,3 |
| IFS | hasta 24 h | 1744 | 108 | 88 | 380 | +1,0 | 666,0 / 2422,4 |
| IFS | hasta 48 h | 1680 | 108 | 89 | 338 | +0,8 | 661,3 / 2031,8 |
| IFS | hasta 72 h | 1618 | 84 | 69 | 345 | +0,9 | 443,9 / 1845,0 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
