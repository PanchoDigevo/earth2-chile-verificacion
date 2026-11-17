# Lluvia pronosticada frente a lluvia medida

Actualizado el 17-11-2026 01:58 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1596 | 108 | 105 | 431 | +0,8 | 666,0 / 1901,8 |
| AIFS | hasta 48 h | 1532 | 108 | 99 | 425 | +0,6 | 661,3 / 1608,3 |
| AIFS | hasta 72 h | 1470 | 84 | 72 | 376 | +0,6 | 443,9 / 1383,9 |
| GFS | hasta 24 h | 1628 | 108 | 95 | 289 | +0,6 | 666,0 / 1594,3 |
| GFS | hasta 48 h | 1558 | 108 | 93 | 230 | +0,4 | 661,3 / 1354,0 |
| GFS | hasta 72 h | 1496 | 84 | 74 | 192 | +0,3 | 445,5 / 912,6 |
| IFS | hasta 24 h | 1596 | 108 | 88 | 345 | +1,0 | 666,0 / 2317,9 |
| IFS | hasta 48 h | 1532 | 108 | 89 | 313 | +0,8 | 661,3 / 1926,0 |
| IFS | hasta 72 h | 1470 | 84 | 69 | 320 | +0,9 | 443,9 / 1769,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
