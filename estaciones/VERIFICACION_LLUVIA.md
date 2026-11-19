# Lluvia pronosticada frente a lluvia medida

Actualizado el 19-11-2026 19:24 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1744 | 108 | 105 | 484 | +0,8 | 666,0 / 2063,1 |
| AIFS | hasta 48 h | 1696 | 108 | 99 | 487 | +0,7 | 661,3 / 1765,2 |
| AIFS | hasta 72 h | 1634 | 84 | 72 | 440 | +0,7 | 443,9 / 1540,8 |
| GFS | hasta 24 h | 1788 | 108 | 95 | 319 | +0,6 | 666,0 / 1676,6 |
| GFS | hasta 48 h | 1722 | 108 | 93 | 251 | +0,4 | 661,3 / 1414,7 |
| GFS | hasta 72 h | 1660 | 84 | 74 | 216 | +0,3 | 445,5 / 967,5 |
| IFS | hasta 24 h | 1756 | 108 | 88 | 383 | +1,0 | 666,0 / 2428,2 |
| IFS | hasta 48 h | 1696 | 108 | 89 | 344 | +0,8 | 661,3 / 2041,4 |
| IFS | hasta 72 h | 1634 | 84 | 69 | 351 | +0,9 | 443,9 / 1858,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
