# Lluvia pronosticada frente a lluvia medida

Actualizado el 24-10-2026 03:24 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 312 | 72 | 72 | 168 | +1,2 | 569,2 / 942,3 |
| AIFS | hasta 48 h | 252 | 72 | 72 | 161 | +0,8 | 567,3 / 765,2 |
| AIFS | hasta 72 h | 188 | 48 | 48 | 104 | +0,7 | 349,1 / 471,5 |
| GFS | hasta 24 h | 312 | 72 | 71 | 139 | +0,9 | 569,2 / 846,4 |
| GFS | hasta 48 h | 252 | 72 | 69 | 83 | -0,3 | 567,3 / 494,8 |
| GFS | hasta 72 h | 188 | 48 | 47 | 39 | -0,5 | 349,1 / 257,1 |
| IFS | hasta 24 h | 312 | 72 | 70 | 146 | +2,1 | 569,2 / 1234,6 |
| IFS | hasta 48 h | 252 | 72 | 71 | 123 | +1,7 | 567,3 / 997,6 |
| IFS | hasta 72 h | 188 | 48 | 48 | 87 | +2,5 | 349,1 / 818,0 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
