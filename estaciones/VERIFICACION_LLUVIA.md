# Lluvia pronosticada frente a lluvia medida

Actualizado el 24-10-2026 18:08 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 348 | 72 | 72 | 194 | +1,2 | 569,2 / 999,8 |
| AIFS | hasta 48 h | 284 | 72 | 72 | 185 | +0,9 | 567,3 / 810,2 |
| AIFS | hasta 72 h | 220 | 48 | 48 | 121 | +0,7 | 349,1 / 506,2 |
| GFS | hasta 24 h | 348 | 72 | 71 | 154 | +0,9 | 569,2 / 874,6 |
| GFS | hasta 48 h | 284 | 72 | 69 | 96 | -0,2 | 567,3 / 522,4 |
| GFS | hasta 72 h | 220 | 48 | 47 | 60 | -0,2 | 349,1 / 296,0 |
| IFS | hasta 24 h | 344 | 72 | 70 | 161 | +2,1 | 569,2 / 1289,0 |
| IFS | hasta 48 h | 284 | 72 | 71 | 133 | +1,7 | 567,3 / 1039,9 |
| IFS | hasta 72 h | 220 | 48 | 48 | 110 | +2,4 | 349,1 / 882,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
