# Lluvia pronosticada frente a lluvia medida

Actualizado el 31-10-2026 23:31 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 780 | 84 | 84 | 271 | +1,0 | 604,0 / 1365,8 |
| AIFS | hasta 48 h | 720 | 84 | 84 | 287 | +0,8 | 602,1 / 1202,2 |
| AIFS | hasta 72 h | 656 | 60 | 60 | 207 | +0,7 | 383,9 / 867,7 |
| GFS | hasta 24 h | 784 | 84 | 83 | 228 | +0,9 | 604,0 / 1345,8 |
| GFS | hasta 48 h | 720 | 84 | 81 | 176 | +0,8 | 602,1 / 1149,3 |
| GFS | hasta 72 h | 656 | 60 | 53 | 144 | +0,4 | 383,9 / 673,6 |
| IFS | hasta 24 h | 780 | 84 | 73 | 227 | +1,3 | 604,0 / 1656,4 |
| IFS | hasta 48 h | 720 | 84 | 77 | 217 | +1,1 | 602,1 / 1371,5 |
| IFS | hasta 72 h | 656 | 60 | 57 | 201 | +1,3 | 383,9 / 1219,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
