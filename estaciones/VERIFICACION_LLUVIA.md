# Lluvia pronosticada frente a lluvia medida

Actualizado el 25-11-2026 00:21 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 2024 | 108 | 105 | 532 | +0,8 | 666,0 / 2193,3 |
| AIFS | hasta 48 h | 1984 | 108 | 99 | 535 | +0,6 | 661,3 / 1890,6 |
| AIFS | hasta 72 h | 1922 | 84 | 72 | 490 | +0,6 | 443,9 / 1683,4 |
| GFS | hasta 24 h | 2076 | 108 | 95 | 331 | +0,5 | 666,0 / 1722,5 |
| GFS | hasta 48 h | 2010 | 108 | 93 | 269 | +0,4 | 661,3 / 1473,1 |
| GFS | hasta 72 h | 1948 | 84 | 74 | 228 | +0,3 | 445,5 / 1021,9 |
| IFS | hasta 24 h | 2024 | 108 | 88 | 412 | +0,9 | 666,0 / 2545,2 |
| IFS | hasta 48 h | 1984 | 108 | 89 | 376 | +0,8 | 661,3 / 2170,0 |
| IFS | hasta 72 h | 1922 | 84 | 69 | 386 | +0,8 | 443,9 / 1976,1 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
