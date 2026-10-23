# Lluvia pronosticada frente a lluvia medida

Actualizado el 22-10-2026 22:52 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 240 | 57 | 57 | 115 | +0,7 | 531,8 / 707,5 |
| AIFS | hasta 48 h | 180 | 60 | 60 | 103 | +0,1 | 534,1 / 554,7 |
| AIFS | hasta 72 h | 116 | 36 | 36 | 58 | -0,3 | 315,9 / 285,0 |
| GFS | hasta 24 h | 244 | 60 | 59 | 118 | +0,8 | 536,0 / 726,8 |
| GFS | hasta 48 h | 180 | 60 | 57 | 66 | -0,6 | 534,1 / 417,3 |
| GFS | hasta 72 h | 116 | 36 | 35 | 13 | -1,4 | 315,9 / 151,5 |
| IFS | hasta 24 h | 240 | 57 | 55 | 102 | +1,7 | 531,8 / 943,4 |
| IFS | hasta 48 h | 180 | 60 | 59 | 90 | +1,6 | 534,1 / 827,7 |
| IFS | hasta 72 h | 116 | 36 | 36 | 48 | +1,8 | 315,9 / 525,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
