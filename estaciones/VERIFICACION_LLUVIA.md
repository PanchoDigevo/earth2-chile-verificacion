# Lluvia pronosticada frente a lluvia medida

Actualizado el 18-11-2026 01:54 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1644 | 108 | 105 | 455 | +0,8 | 666,0 / 1980,2 |
| AIFS | hasta 48 h | 1584 | 108 | 99 | 451 | +0,6 | 661,3 / 1687,7 |
| AIFS | hasta 72 h | 1522 | 84 | 72 | 402 | +0,7 | 443,9 / 1461,0 |
| GFS | hasta 24 h | 1680 | 108 | 95 | 313 | +0,6 | 666,0 / 1654,0 |
| GFS | hasta 48 h | 1610 | 108 | 93 | 251 | +0,5 | 661,3 / 1396,6 |
| GFS | hasta 72 h | 1548 | 84 | 74 | 213 | +0,3 | 445,5 / 949,8 |
| IFS | hasta 24 h | 1636 | 108 | 88 | 356 | +1,0 | 666,0 / 2351,2 |
| IFS | hasta 48 h | 1584 | 108 | 89 | 329 | +0,8 | 661,3 / 2004,9 |
| IFS | hasta 72 h | 1522 | 84 | 69 | 339 | +0,9 | 443,9 / 1826,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
