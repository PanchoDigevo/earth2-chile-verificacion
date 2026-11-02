# Lluvia pronosticada frente a lluvia medida

Actualizado el 02-11-2026 05:13 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 824 | 84 | 84 | 294 | +1,0 | 604,0 / 1415,4 |
| AIFS | hasta 48 h | 784 | 84 | 84 | 313 | +0,8 | 602,1 / 1246,3 |
| AIFS | hasta 72 h | 720 | 60 | 60 | 236 | +0,7 | 383,9 / 912,9 |
| GFS | hasta 24 h | 844 | 84 | 83 | 240 | +0,9 | 604,0 / 1371,1 |
| GFS | hasta 48 h | 784 | 84 | 81 | 189 | +0,7 | 602,1 / 1185,9 |
| GFS | hasta 72 h | 720 | 60 | 53 | 160 | +0,5 | 383,9 / 714,3 |
| IFS | hasta 24 h | 824 | 84 | 73 | 248 | +1,3 | 604,0 / 1714,6 |
| IFS | hasta 48 h | 784 | 84 | 77 | 246 | +1,1 | 602,1 / 1475,7 |
| IFS | hasta 72 h | 720 | 60 | 57 | 229 | +1,3 | 383,9 / 1293,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
