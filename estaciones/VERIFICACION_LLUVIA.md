# Lluvia pronosticada frente a lluvia medida

Actualizado el 16-11-2026 19:29 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1580 | 108 | 105 | 419 | +0,8 | 666,0 / 1875,6 |
| AIFS | hasta 48 h | 1516 | 108 | 99 | 413 | +0,6 | 661,3 / 1582,5 |
| AIFS | hasta 72 h | 1454 | 84 | 72 | 364 | +0,6 | 443,9 / 1362,5 |
| GFS | hasta 24 h | 1612 | 108 | 95 | 277 | +0,6 | 666,0 / 1575,4 |
| GFS | hasta 48 h | 1542 | 108 | 93 | 224 | +0,4 | 661,3 / 1342,8 |
| GFS | hasta 72 h | 1480 | 84 | 74 | 192 | +0,3 | 445,5 / 904,7 |
| IFS | hasta 24 h | 1580 | 108 | 88 | 333 | +1,0 | 666,0 / 2300,3 |
| IFS | hasta 48 h | 1516 | 108 | 89 | 302 | +0,8 | 661,3 / 1902,5 |
| IFS | hasta 72 h | 1454 | 84 | 69 | 312 | +0,9 | 443,9 / 1749,1 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
