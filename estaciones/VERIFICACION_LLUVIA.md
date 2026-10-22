# Lluvia pronosticada frente a lluvia medida

Actualizado el 21-10-2026 22:46 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 192 | 48 | 48 | 76 | +0,3 | 519,2 / 570,3 |
| AIFS | hasta 48 h | 132 | 48 | 48 | 67 | -0,8 | 517,3 / 413,5 |
| AIFS | hasta 72 h | 68 | 24 | 24 | 32 | -2,0 | 299,1 / 160,9 |
| GFS | hasta 24 h | 196 | 48 | 47 | 91 | +0,7 | 519,2 / 646,7 |
| GFS | hasta 48 h | 132 | 48 | 45 | 44 | -1,3 | 517,3 / 343,6 |
| GFS | hasta 72 h | 68 | 24 | 23 | 0 | -3,1 | 299,1 / 88,9 |
| IFS | hasta 24 h | 192 | 48 | 46 | 69 | +1,5 | 519,2 / 806,7 |
| IFS | hasta 48 h | 132 | 48 | 47 | 65 | +1,2 | 517,3 / 681,1 |
| IFS | hasta 72 h | 68 | 24 | 24 | 29 | +1,8 | 299,1 / 423,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
