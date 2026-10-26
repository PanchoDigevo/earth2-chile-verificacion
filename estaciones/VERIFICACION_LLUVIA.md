# Lluvia pronosticada frente a lluvia medida

Actualizado el 26-10-2026 17:07 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 460 | 72 | 72 | 221 | +1,1 | 569,2 / 1072,0 |
| AIFS | hasta 48 h | 400 | 72 | 72 | 228 | +0,9 | 567,3 / 920,3 |
| AIFS | hasta 72 h | 336 | 48 | 48 | 156 | +0,8 | 349,1 / 603,0 |
| GFS | hasta 24 h | 460 | 72 | 71 | 170 | +0,7 | 569,2 / 908,5 |
| GFS | hasta 48 h | 400 | 72 | 69 | 117 | +0,0 | 567,3 / 574,0 |
| GFS | hasta 72 h | 336 | 48 | 47 | 83 | +0,0 | 349,1 / 361,8 |
| IFS | hasta 24 h | 460 | 72 | 70 | 180 | +1,7 | 569,2 / 1330,4 |
| IFS | hasta 48 h | 400 | 72 | 71 | 153 | +1,3 | 567,3 / 1090,9 |
| IFS | hasta 72 h | 336 | 48 | 48 | 133 | +1,9 | 349,1 / 979,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
