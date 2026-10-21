# Lluvia pronosticada frente a lluvia medida

Actualizado el 21-10-2026 19:41 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 180 | 48 | 48 | 64 | +0,1 | 519,2 / 534,3 |
| AIFS | hasta 48 h | 116 | 48 | 48 | 51 | -1,3 | 517,3 / 371,2 |
| AIFS | hasta 72 h | 52 | 24 | 24 | 16 | -3,3 | 299,1 / 127,4 |
| GFS | hasta 24 h | 180 | 48 | 47 | 75 | +0,5 | 519,2 / 615,5 |
| GFS | hasta 48 h | 116 | 48 | 45 | 31 | -1,7 | 517,3 / 323,1 |
| GFS | hasta 72 h | 52 | 24 | 23 | 0 | -4,2 | 299,1 / 82,0 |
| IFS | hasta 24 h | 180 | 48 | 46 | 57 | +1,4 | 519,2 / 776,0 |
| IFS | hasta 48 h | 116 | 48 | 47 | 49 | +0,7 | 517,3 / 595,1 |
| IFS | hasta 72 h | 52 | 24 | 24 | 13 | +1,3 | 299,1 / 365,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
