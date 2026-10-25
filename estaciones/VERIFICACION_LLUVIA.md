# Lluvia pronosticada frente a lluvia medida

Actualizado el 24-10-2026 22:36 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 364 | 72 | 72 | 200 | +1,2 | 569,2 / 1013,3 |
| AIFS | hasta 48 h | 300 | 72 | 72 | 200 | +0,9 | 567,3 / 841,3 |
| AIFS | hasta 72 h | 236 | 48 | 48 | 137 | +0,8 | 349,1 / 537,0 |
| GFS | hasta 24 h | 364 | 72 | 71 | 166 | +0,9 | 569,2 / 895,8 |
| GFS | hasta 48 h | 300 | 72 | 69 | 105 | -0,1 | 567,3 / 542,7 |
| GFS | hasta 72 h | 236 | 48 | 47 | 74 | -0,1 | 349,1 / 332,0 |
| IFS | hasta 24 h | 364 | 72 | 70 | 170 | +2,0 | 569,2 / 1312,2 |
| IFS | hasta 48 h | 300 | 72 | 71 | 139 | +1,6 | 567,3 / 1054,7 |
| IFS | hasta 72 h | 236 | 48 | 48 | 117 | +2,3 | 349,1 / 894,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
