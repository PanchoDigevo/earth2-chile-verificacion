# Lluvia pronosticada frente a lluvia medida

Actualizado el 23-11-2026 19:53 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1964 | 108 | 105 | 520 | +0,8 | 666,0 / 2157,9 |
| AIFS | hasta 48 h | 1904 | 108 | 99 | 523 | +0,6 | 661,3 / 1851,9 |
| AIFS | hasta 72 h | 1842 | 84 | 72 | 478 | +0,6 | 443,9 / 1641,1 |
| GFS | hasta 24 h | 1996 | 108 | 95 | 331 | +0,5 | 666,0 / 1717,6 |
| GFS | hasta 48 h | 1930 | 108 | 93 | 263 | +0,4 | 661,3 / 1455,7 |
| GFS | hasta 72 h | 1868 | 84 | 74 | 228 | +0,3 | 445,5 / 1007,0 |
| IFS | hasta 24 h | 1964 | 108 | 88 | 399 | +0,9 | 666,0 / 2510,5 |
| IFS | hasta 48 h | 1904 | 108 | 89 | 362 | +0,8 | 661,3 / 2111,6 |
| IFS | hasta 72 h | 1842 | 84 | 69 | 373 | +0,8 | 443,9 / 1930,6 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
