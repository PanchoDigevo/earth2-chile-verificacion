# Lluvia pronosticada frente a lluvia medida

Actualizado el 22-11-2026 12:38 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1912 | 108 | 105 | 511 | +0,8 | 666,0 / 2134,5 |
| AIFS | hasta 48 h | 1848 | 108 | 99 | 511 | +0,6 | 661,3 / 1825,8 |
| AIFS | hasta 72 h | 1786 | 84 | 72 | 466 | +0,7 | 443,9 / 1614,7 |
| GFS | hasta 24 h | 1944 | 108 | 95 | 331 | +0,5 | 666,0 / 1705,9 |
| GFS | hasta 48 h | 1874 | 108 | 93 | 263 | +0,4 | 661,3 / 1440,9 |
| GFS | hasta 72 h | 1812 | 84 | 74 | 228 | +0,3 | 445,5 / 991,7 |
| IFS | hasta 24 h | 1912 | 108 | 88 | 399 | +1,0 | 666,0 / 2509,3 |
| IFS | hasta 48 h | 1848 | 108 | 89 | 362 | +0,8 | 661,3 / 2110,4 |
| IFS | hasta 72 h | 1786 | 84 | 69 | 373 | +0,8 | 443,9 / 1928,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
