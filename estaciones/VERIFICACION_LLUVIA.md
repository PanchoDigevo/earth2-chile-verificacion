# Lluvia pronosticada frente a lluvia medida

Actualizado el 27-10-2026 02:31 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 480 | 72 | 72 | 240 | +1,3 | 580,0 / 1212,7 |
| AIFS | hasta 48 h | 416 | 72 | 72 | 244 | +1,1 | 578,1 / 1046,9 |
| AIFS | hasta 72 h | 352 | 48 | 48 | 172 | +1,0 | 359,9 / 700,3 |
| GFS | hasta 24 h | 480 | 72 | 71 | 190 | +1,2 | 580,0 / 1148,5 |
| GFS | hasta 48 h | 416 | 72 | 69 | 133 | +0,5 | 578,1 / 803,3 |
| GFS | hasta 72 h | 352 | 48 | 47 | 92 | +0,1 | 359,9 / 386,9 |
| IFS | hasta 24 h | 480 | 72 | 70 | 196 | +1,9 | 580,0 / 1508,6 |
| IFS | hasta 48 h | 416 | 72 | 71 | 169 | +1,5 | 578,1 / 1198,7 |
| IFS | hasta 72 h | 352 | 48 | 48 | 149 | +1,9 | 359,9 / 1035,5 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
