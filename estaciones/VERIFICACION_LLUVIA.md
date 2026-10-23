# Lluvia pronosticada frente a lluvia medida

Actualizado el 23-10-2026 04:54 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 256 | 69 | 69 | 119 | +0,9 | 560,9 / 794,8 |
| AIFS | hasta 48 h | 196 | 72 | 72 | 107 | +0,4 | 567,3 / 637,8 |
| AIFS | hasta 72 h | 132 | 48 | 48 | 62 | +0,0 | 349,1 / 355,7 |
| GFS | hasta 24 h | 260 | 72 | 71 | 122 | +0,9 | 569,2 / 807,3 |
| GFS | hasta 48 h | 196 | 72 | 69 | 70 | -0,5 | 567,3 / 460,8 |
| GFS | hasta 72 h | 132 | 48 | 47 | 17 | -1,1 | 349,1 / 206,6 |
| IFS | hasta 24 h | 256 | 69 | 67 | 106 | +1,7 | 560,9 / 1006,1 |
| IFS | hasta 48 h | 196 | 72 | 71 | 94 | +1,7 | 567,3 / 899,4 |
| IFS | hasta 72 h | 132 | 48 | 48 | 52 | +2,5 | 349,1 / 685,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
