# Lluvia pronosticada frente a lluvia medida

Actualizado el 22-10-2026 11:03 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 212 | 48 | 48 | 96 | +0,4 | 519,2 / 609,2 |
| AIFS | hasta 48 h | 148 | 48 | 48 | 83 | -0,5 | 517,3 / 437,8 |
| AIFS | hasta 72 h | 84 | 24 | 24 | 38 | -1,5 | 299,1 / 174,9 |
| GFS | hasta 24 h | 212 | 48 | 47 | 103 | +0,7 | 519,2 / 666,1 |
| GFS | hasta 48 h | 148 | 48 | 45 | 52 | -1,1 | 517,3 / 358,8 |
| GFS | hasta 72 h | 84 | 24 | 23 | 0 | -2,5 | 299,1 / 91,9 |
| IFS | hasta 24 h | 212 | 48 | 46 | 87 | +1,5 | 519,2 / 840,3 |
| IFS | hasta 48 h | 148 | 48 | 47 | 74 | +1,3 | 517,3 / 707,0 |
| IFS | hasta 72 h | 84 | 24 | 24 | 32 | +1,6 | 299,1 / 431,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
