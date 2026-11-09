# Lluvia pronosticada frente a lluvia medida

Actualizado el 09-11-2026 19:40 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1133 | 84 | 84 | 353 | +0,9 | 608,8 / 1624,9 |
| AIFS | hasta 48 h | 1082 | 84 | 84 | 343 | +0,7 | 604,5 / 1342,1 |
| AIFS | hasta 72 h | 1018 | 60 | 60 | 315 | +0,7 | 387,5 / 1144,0 |
| GFS | hasta 24 h | 1175 | 84 | 83 | 257 | +0,7 | 608,8 / 1430,1 |
| GFS | hasta 48 h | 1106 | 84 | 81 | 204 | +0,6 | 604,5 / 1226,2 |
| GFS | hasta 72 h | 1042 | 60 | 53 | 172 | +0,4 | 388,7 / 773,5 |
| IFS | hasta 24 h | 1133 | 84 | 73 | 303 | +1,3 | 608,8 / 2036,1 |
| IFS | hasta 48 h | 1082 | 84 | 77 | 266 | +0,9 | 604,5 / 1540,5 |
| IFS | hasta 72 h | 1018 | 60 | 57 | 285 | +1,0 | 387,5 / 1456,1 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
