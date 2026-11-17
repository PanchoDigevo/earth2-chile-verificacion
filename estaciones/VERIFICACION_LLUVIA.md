# Lluvia pronosticada frente a lluvia medida

Actualizado el 17-11-2026 20:07 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1628 | 108 | 105 | 440 | +0,8 | 666,0 / 1928,3 |
| AIFS | hasta 48 h | 1568 | 108 | 99 | 437 | +0,6 | 661,3 / 1635,4 |
| AIFS | hasta 72 h | 1506 | 84 | 72 | 388 | +0,6 | 443,9 / 1415,1 |
| GFS | hasta 24 h | 1660 | 108 | 95 | 298 | +0,6 | 666,0 / 1606,3 |
| GFS | hasta 48 h | 1594 | 108 | 93 | 239 | +0,4 | 661,3 / 1369,1 |
| GFS | hasta 72 h | 1532 | 84 | 74 | 201 | +0,3 | 445,5 / 926,7 |
| IFS | hasta 24 h | 1628 | 108 | 88 | 348 | +1,0 | 666,0 / 2328,1 |
| IFS | hasta 48 h | 1568 | 108 | 89 | 313 | +0,8 | 661,3 / 1932,9 |
| IFS | hasta 72 h | 1506 | 84 | 69 | 323 | +0,9 | 443,9 / 1782,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
