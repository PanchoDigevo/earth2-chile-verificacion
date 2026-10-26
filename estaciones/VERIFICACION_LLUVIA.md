# Lluvia pronosticada frente a lluvia medida

Actualizado el 26-10-2026 11:31 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 448 | 72 | 72 | 209 | +1,0 | 569,2 / 1030,6 |
| AIFS | hasta 48 h | 384 | 72 | 72 | 212 | +0,8 | 567,3 / 856,7 |
| AIFS | hasta 72 h | 320 | 48 | 48 | 140 | +0,6 | 349,1 / 547,7 |
| GFS | hasta 24 h | 448 | 72 | 71 | 166 | +0,7 | 569,2 / 897,6 |
| GFS | hasta 48 h | 384 | 72 | 69 | 105 | -0,1 | 567,3 / 544,2 |
| GFS | hasta 72 h | 320 | 48 | 47 | 74 | -0,1 | 349,1 / 332,0 |
| IFS | hasta 24 h | 448 | 72 | 70 | 170 | +1,7 | 569,2 / 1312,6 |
| IFS | hasta 48 h | 384 | 72 | 71 | 139 | +1,3 | 567,3 / 1055,5 |
| IFS | hasta 72 h | 320 | 48 | 48 | 117 | +1,7 | 349,1 / 895,9 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
