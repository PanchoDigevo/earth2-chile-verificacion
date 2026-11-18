# Lluvia pronosticada frente a lluvia medida

Actualizado el 18-11-2026 19:17 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1692 | 108 | 105 | 463 | +0,8 | 666,0 / 2024,5 |
| AIFS | hasta 48 h | 1632 | 108 | 99 | 457 | +0,6 | 661,3 / 1705,5 |
| AIFS | hasta 72 h | 1570 | 84 | 72 | 402 | +0,7 | 443,9 / 1470,0 |
| GFS | hasta 24 h | 1728 | 108 | 95 | 319 | +0,6 | 666,0 / 1664,6 |
| GFS | hasta 48 h | 1658 | 108 | 93 | 251 | +0,4 | 661,3 / 1401,8 |
| GFS | hasta 72 h | 1596 | 84 | 74 | 213 | +0,3 | 445,5 / 955,8 |
| IFS | hasta 24 h | 1696 | 108 | 88 | 368 | +1,0 | 666,0 / 2391,9 |
| IFS | hasta 48 h | 1632 | 108 | 89 | 329 | +0,8 | 661,3 / 2009,9 |
| IFS | hasta 72 h | 1570 | 84 | 69 | 339 | +0,9 | 443,9 / 1829,1 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
