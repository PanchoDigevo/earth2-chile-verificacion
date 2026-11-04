# Lluvia pronosticada frente a lluvia medida

Actualizado el 04-11-2026 08:29 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 878 | 84 | 84 | 329 | +1,1 | 606,4 / 1561,1 |
| AIFS | hasta 48 h | 818 | 84 | 84 | 319 | +0,8 | 602,1 / 1266,9 |
| AIFS | hasta 72 h | 804 | 60 | 60 | 280 | +0,8 | 385,1 / 1043,9 |
| GFS | hasta 24 h | 908 | 84 | 83 | 257 | +0,9 | 606,4 / 1417,8 |
| GFS | hasta 48 h | 842 | 84 | 81 | 204 | +0,7 | 602,1 / 1216,9 |
| GFS | hasta 72 h | 824 | 60 | 53 | 172 | +0,5 | 386,3 / 763,3 |
| IFS | hasta 24 h | 874 | 84 | 73 | 282 | +1,6 | 606,4 / 1986,4 |
| IFS | hasta 48 h | 818 | 84 | 77 | 248 | +1,1 | 602,1 / 1490,1 |
| IFS | hasta 72 h | 804 | 60 | 57 | 255 | +1,2 | 385,1 / 1380,6 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
