# Lluvia pronosticada frente a lluvia medida

Actualizado el 23-10-2026 22:00 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 296 | 72 | 72 | 152 | +1,1 | 569,2 / 895,0 |
| AIFS | hasta 48 h | 236 | 72 | 72 | 145 | +0,7 | 567,3 / 736,2 |
| AIFS | hasta 72 h | 172 | 48 | 48 | 101 | +0,7 | 349,1 / 463,8 |
| GFS | hasta 24 h | 300 | 72 | 71 | 139 | +0,9 | 569,2 / 838,6 |
| GFS | hasta 48 h | 236 | 72 | 69 | 80 | -0,3 | 567,3 / 485,8 |
| GFS | hasta 72 h | 172 | 48 | 47 | 39 | -0,6 | 349,1 / 249,8 |
| IFS | hasta 24 h | 296 | 72 | 70 | 131 | +2,1 | 569,2 / 1200,0 |
| IFS | hasta 48 h | 236 | 72 | 71 | 113 | +1,7 | 567,3 / 970,7 |
| IFS | hasta 72 h | 172 | 48 | 48 | 81 | +2,6 | 349,1 / 802,9 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
