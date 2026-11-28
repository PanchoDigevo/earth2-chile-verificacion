# Lluvia pronosticada frente a lluvia medida

Actualizado el 27-11-2026 23:21 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 2208 | 108 | 105 | 532 | +0,7 | 666,0 / 2210,4 |
| AIFS | hasta 48 h | 2151 | 108 | 99 | 535 | +0,6 | 661,3 / 1901,4 |
| AIFS | hasta 72 h | 2094 | 84 | 72 | 490 | +0,6 | 443,9 / 1693,0 |
| GFS | hasta 24 h | 2260 | 108 | 95 | 331 | +0,5 | 666,0 / 1722,9 |
| GFS | hasta 48 h | 2190 | 108 | 93 | 269 | +0,4 | 661,3 / 1473,7 |
| GFS | hasta 72 h | 2128 | 84 | 74 | 228 | +0,3 | 445,5 / 1025,4 |
| IFS | hasta 24 h | 2224 | 108 | 88 | 412 | +0,8 | 666,0 / 2553,2 |
| IFS | hasta 48 h | 2164 | 108 | 89 | 376 | +0,7 | 661,3 / 2179,9 |
| IFS | hasta 72 h | 2102 | 84 | 69 | 386 | +0,7 | 443,9 / 1982,9 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
