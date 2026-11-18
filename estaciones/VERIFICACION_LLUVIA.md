# Lluvia pronosticada frente a lluvia medida

Actualizado el 18-11-2026 11:30 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1680 | 108 | 105 | 463 | +0,8 | 666,0 / 2018,4 |
| AIFS | hasta 48 h | 1616 | 108 | 99 | 457 | +0,6 | 661,3 / 1698,5 |
| AIFS | hasta 72 h | 1554 | 84 | 72 | 402 | +0,7 | 443,9 / 1463,3 |
| GFS | hasta 24 h | 1712 | 108 | 95 | 319 | +0,6 | 666,0 / 1664,6 |
| GFS | hasta 48 h | 1642 | 108 | 93 | 251 | +0,5 | 661,3 / 1401,8 |
| GFS | hasta 72 h | 1580 | 84 | 74 | 213 | +0,3 | 445,5 / 955,8 |
| IFS | hasta 24 h | 1680 | 108 | 88 | 368 | +1,0 | 666,0 / 2389,8 |
| IFS | hasta 48 h | 1616 | 108 | 89 | 329 | +0,8 | 661,3 / 2007,8 |
| IFS | hasta 72 h | 1554 | 84 | 69 | 339 | +0,9 | 443,9 / 1828,5 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
