# Lluvia pronosticada frente a lluvia medida

Actualizado el 06-11-2026 20:29 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1002 | 84 | 84 | 341 | +1,0 | 608,8 / 1603,3 |
| AIFS | hasta 48 h | 938 | 84 | 84 | 331 | +0,8 | 604,5 / 1320,8 |
| AIFS | hasta 72 h | 874 | 60 | 60 | 302 | +0,8 | 387,5 / 1109,3 |
| GFS | hasta 24 h | 1032 | 84 | 83 | 257 | +0,8 | 608,8 / 1428,0 |
| GFS | hasta 48 h | 962 | 84 | 81 | 204 | +0,6 | 604,5 / 1224,1 |
| GFS | hasta 72 h | 898 | 60 | 53 | 172 | +0,4 | 388,7 / 771,3 |
| IFS | hasta 24 h | 1002 | 84 | 73 | 300 | +1,4 | 608,8 / 2028,0 |
| IFS | hasta 48 h | 938 | 84 | 77 | 263 | +1,0 | 604,5 / 1533,3 |
| IFS | hasta 72 h | 874 | 60 | 57 | 276 | +1,2 | 387,5 / 1430,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
