# Lluvia pronosticada frente a lluvia medida

Actualizado el 15-11-2026 20:07 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1516 | 108 | 105 | 401 | +0,8 | 666,0 / 1813,0 |
| AIFS | hasta 48 h | 1452 | 108 | 99 | 389 | +0,6 | 661,3 / 1521,3 |
| AIFS | hasta 72 h | 1390 | 84 | 72 | 352 | +0,6 | 443,9 / 1320,0 |
| GFS | hasta 24 h | 1548 | 108 | 95 | 277 | +0,6 | 666,0 / 1564,2 |
| GFS | hasta 48 h | 1478 | 108 | 93 | 224 | +0,5 | 661,3 / 1337,4 |
| GFS | hasta 72 h | 1416 | 84 | 74 | 192 | +0,3 | 445,5 / 900,8 |
| IFS | hasta 24 h | 1516 | 108 | 88 | 329 | +1,1 | 666,0 / 2285,8 |
| IFS | hasta 48 h | 1452 | 108 | 89 | 289 | +0,8 | 661,3 / 1874,6 |
| IFS | hasta 72 h | 1390 | 84 | 69 | 311 | +0,9 | 443,9 / 1740,9 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
