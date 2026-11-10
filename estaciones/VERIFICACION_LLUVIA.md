# Lluvia pronosticada frente a lluvia medida

Actualizado el 10-11-2026 09:56 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1180 | 90 | 90 | 377 | +0,9 | 623,5 / 1723,7 |
| AIFS | hasta 48 h | 1126 | 96 | 96 | 371 | +0,7 | 628,5 / 1466,2 |
| AIFS | hasta 72 h | 1062 | 72 | 72 | 340 | +0,8 | 411,5 / 1260,2 |
| GFS | hasta 24 h | 1217 | 93 | 92 | 273 | +0,7 | 629,5 / 1533,7 |
| GFS | hasta 48 h | 1150 | 96 | 93 | 220 | +0,6 | 628,5 / 1309,4 |
| GFS | hasta 72 h | 1086 | 72 | 65 | 188 | +0,4 | 412,7 / 864,5 |
| IFS | hasta 24 h | 1180 | 90 | 79 | 318 | +1,3 | 623,5 / 2203,8 |
| IFS | hasta 48 h | 1126 | 96 | 89 | 282 | +1,1 | 628,5 / 1820,6 |
| IFS | hasta 72 h | 1062 | 72 | 69 | 302 | +1,2 | 411,5 / 1686,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
