# Lluvia pronosticada frente a lluvia medida

Actualizado el 17-11-2026 11:51 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1616 | 108 | 105 | 431 | +0,8 | 666,0 / 1903,1 |
| AIFS | hasta 48 h | 1552 | 108 | 99 | 425 | +0,6 | 661,3 / 1609,0 |
| AIFS | hasta 72 h | 1490 | 84 | 72 | 376 | +0,6 | 443,9 / 1386,4 |
| GFS | hasta 24 h | 1648 | 108 | 95 | 289 | +0,6 | 666,0 / 1596,1 |
| GFS | hasta 48 h | 1578 | 108 | 93 | 230 | +0,4 | 661,3 / 1355,9 |
| GFS | hasta 72 h | 1516 | 84 | 74 | 192 | +0,3 | 445,5 / 913,8 |
| IFS | hasta 24 h | 1616 | 108 | 88 | 345 | +1,0 | 666,0 / 2320,9 |
| IFS | hasta 48 h | 1552 | 108 | 89 | 313 | +0,8 | 661,3 / 1927,5 |
| IFS | hasta 72 h | 1490 | 84 | 69 | 320 | +0,9 | 443,9 / 1771,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
