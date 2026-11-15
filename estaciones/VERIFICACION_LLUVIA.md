# Lluvia pronosticada frente a lluvia medida

Actualizado el 15-11-2026 14:57 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1499 | 108 | 105 | 397 | +0,8 | 660,6 / 1801,2 |
| AIFS | hasta 48 h | 1436 | 108 | 99 | 383 | +0,6 | 656,1 / 1509,6 |
| AIFS | hasta 72 h | 1374 | 84 | 72 | 352 | +0,6 | 438,7 / 1311,4 |
| GFS | hasta 24 h | 1532 | 108 | 95 | 277 | +0,6 | 660,8 / 1563,0 |
| GFS | hasta 48 h | 1462 | 108 | 93 | 224 | +0,5 | 656,1 / 1335,9 |
| GFS | hasta 72 h | 1400 | 84 | 74 | 192 | +0,3 | 440,3 / 899,0 |
| IFS | hasta 24 h | 1499 | 108 | 88 | 329 | +1,1 | 660,6 / 2280,8 |
| IFS | hasta 48 h | 1436 | 108 | 89 | 289 | +0,8 | 656,1 / 1874,3 |
| IFS | hasta 72 h | 1374 | 84 | 69 | 311 | +0,9 | 438,7 / 1739,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
