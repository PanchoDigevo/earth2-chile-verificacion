# Lluvia pronosticada frente a lluvia medida

Actualizado el 24-10-2026 15:20 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 335 | 72 | 72 | 181 | +1,2 | 569,2 / 965,1 |
| AIFS | hasta 48 h | 272 | 72 | 72 | 173 | +0,8 | 567,3 / 787,1 |
| AIFS | hasta 72 h | 208 | 48 | 48 | 109 | +0,7 | 349,1 / 484,6 |
| GFS | hasta 24 h | 336 | 72 | 71 | 142 | +0,9 | 569,2 / 856,6 |
| GFS | hasta 48 h | 272 | 72 | 69 | 93 | -0,2 | 567,3 / 511,9 |
| GFS | hasta 72 h | 208 | 48 | 47 | 51 | -0,4 | 349,1 / 275,6 |
| IFS | hasta 24 h | 335 | 72 | 70 | 152 | +2,1 | 569,2 / 1270,4 |
| IFS | hasta 48 h | 272 | 72 | 71 | 130 | +1,7 | 567,3 / 1025,8 |
| IFS | hasta 72 h | 208 | 48 | 48 | 98 | +2,5 | 349,1 / 866,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
