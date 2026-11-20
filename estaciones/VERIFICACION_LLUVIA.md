# Lluvia pronosticada frente a lluvia medida

Actualizado el 20-11-2026 00:55 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1776 | 108 | 105 | 502 | +0,8 | 666,0 / 2109,3 |
| AIFS | hasta 48 h | 1712 | 108 | 99 | 499 | +0,7 | 661,3 / 1795,9 |
| AIFS | hasta 72 h | 1650 | 84 | 72 | 453 | +0,7 | 443,9 / 1580,5 |
| GFS | hasta 24 h | 1808 | 108 | 95 | 331 | +0,6 | 666,0 / 1703,8 |
| GFS | hasta 48 h | 1738 | 108 | 93 | 263 | +0,4 | 661,3 / 1436,3 |
| GFS | hasta 72 h | 1676 | 84 | 74 | 228 | +0,3 | 445,5 / 987,8 |
| IFS | hasta 24 h | 1776 | 108 | 88 | 399 | +1,0 | 666,0 / 2501,3 |
| IFS | hasta 48 h | 1712 | 108 | 89 | 356 | +0,8 | 661,3 / 2092,0 |
| IFS | hasta 72 h | 1650 | 84 | 69 | 367 | +0,9 | 443,9 / 1913,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
