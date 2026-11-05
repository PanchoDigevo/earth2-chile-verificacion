# Lluvia pronosticada frente a lluvia medida

Actualizado el 05-11-2026 12:46 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 935 | 84 | 84 | 329 | +1,0 | 606,4 / 1562,3 |
| AIFS | hasta 48 h | 874 | 84 | 84 | 319 | +0,8 | 602,1 / 1267,8 |
| AIFS | hasta 72 h | 814 | 60 | 60 | 280 | +0,8 | 385,1 / 1043,9 |
| GFS | hasta 24 h | 968 | 84 | 83 | 257 | +0,8 | 606,4 / 1418,1 |
| GFS | hasta 48 h | 898 | 84 | 81 | 204 | +0,7 | 602,1 / 1216,9 |
| GFS | hasta 72 h | 838 | 60 | 53 | 172 | +0,4 | 386,3 / 763,3 |
| IFS | hasta 24 h | 935 | 84 | 73 | 285 | +1,5 | 606,4 / 1992,3 |
| IFS | hasta 48 h | 874 | 84 | 77 | 248 | +1,0 | 602,1 / 1492,8 |
| IFS | hasta 72 h | 814 | 60 | 57 | 255 | +1,2 | 385,1 / 1380,6 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
