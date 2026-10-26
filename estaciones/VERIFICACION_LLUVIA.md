# Lluvia pronosticada frente a lluvia medida

Actualizado el 26-10-2026 03:55 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 432 | 72 | 72 | 200 | +1,0 | 569,2 / 1013,3 |
| AIFS | hasta 48 h | 368 | 72 | 72 | 200 | +0,7 | 567,3 / 841,5 |
| AIFS | hasta 72 h | 304 | 48 | 48 | 137 | +0,6 | 349,1 / 537,0 |
| GFS | hasta 24 h | 432 | 72 | 71 | 166 | +0,8 | 569,2 / 896,1 |
| GFS | hasta 48 h | 368 | 72 | 69 | 105 | -0,1 | 567,3 / 543,6 |
| GFS | hasta 72 h | 304 | 48 | 47 | 74 | -0,1 | 349,1 / 332,0 |
| IFS | hasta 24 h | 428 | 72 | 70 | 170 | +1,7 | 569,2 / 1312,3 |
| IFS | hasta 48 h | 368 | 72 | 71 | 139 | +1,3 | 567,3 / 1055,1 |
| IFS | hasta 72 h | 304 | 48 | 48 | 117 | +1,8 | 349,1 / 894,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
