# Lluvia pronosticada frente a lluvia medida

Actualizado el 10-11-2026 17:35 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1183 | 90 | 90 | 377 | +0,9 | 623,5 / 1724,3 |
| AIFS | hasta 48 h | 1138 | 96 | 96 | 371 | +0,7 | 628,5 / 1469,8 |
| AIFS | hasta 72 h | 1074 | 72 | 72 | 340 | +0,8 | 411,5 / 1264,4 |
| GFS | hasta 24 h | 1229 | 96 | 95 | 273 | +0,7 | 632,8 / 1543,3 |
| GFS | hasta 48 h | 1162 | 96 | 93 | 220 | +0,6 | 628,5 / 1311,5 |
| GFS | hasta 72 h | 1098 | 72 | 65 | 188 | +0,4 | 412,7 / 866,0 |
| IFS | hasta 24 h | 1183 | 90 | 79 | 318 | +1,3 | 623,5 / 2204,1 |
| IFS | hasta 48 h | 1138 | 96 | 89 | 285 | +1,1 | 628,5 / 1829,0 |
| IFS | hasta 72 h | 1074 | 72 | 69 | 305 | +1,2 | 411,5 / 1695,0 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
