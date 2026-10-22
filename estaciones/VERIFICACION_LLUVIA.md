# Lluvia pronosticada frente a lluvia medida

Actualizado el 22-10-2026 15:45 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 224 | 48 | 48 | 108 | +0,5 | 519,2 / 632,6 |
| AIFS | hasta 48 h | 164 | 48 | 48 | 99 | -0,3 | 517,3 / 472,0 |
| AIFS | hasta 72 h | 100 | 24 | 24 | 54 | -0,9 | 299,1 / 207,3 |
| GFS | hasta 24 h | 224 | 48 | 47 | 113 | +0,8 | 519,2 / 691,1 |
| GFS | hasta 48 h | 164 | 48 | 45 | 64 | -0,8 | 517,3 / 385,5 |
| GFS | hasta 72 h | 100 | 24 | 23 | 13 | -1,8 | 299,1 / 121,5 |
| IFS | hasta 24 h | 224 | 48 | 46 | 96 | +1,5 | 519,2 / 855,9 |
| IFS | hasta 48 h | 164 | 48 | 47 | 86 | +1,3 | 517,3 / 727,8 |
| IFS | hasta 72 h | 100 | 24 | 24 | 44 | +1,6 | 299,1 / 455,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
