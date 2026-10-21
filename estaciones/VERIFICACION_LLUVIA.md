# Lluvia pronosticada frente a lluvia medida

Actualizado el 21-10-2026 07:32 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 152 | 48 | 48 | 48 | -0,0 | 508,4 / 505,8 |
| AIFS | hasta 48 h | 88 | 48 | 48 | 35 | -1,9 | 506,5 / 338,8 |
| AIFS | hasta 72 h | 24 | 24 | 24 | 0 | -8,2 | 288,3 / 92,6 |
| GFS | hasta 24 h | 152 | 48 | 47 | 75 | +0,6 | 508,4 / 603,3 |
| GFS | hasta 48 h | 88 | 48 | 45 | 28 | -2,2 | 506,5 / 311,4 |
| GFS | hasta 72 h | 24 | 24 | 23 | 0 | -9,2 | 288,3 / 68,2 |
| IFS | hasta 24 h | 152 | 48 | 46 | 48 | +1,5 | 508,4 / 739,5 |
| IFS | hasta 48 h | 88 | 48 | 47 | 30 | +0,4 | 506,5 / 539,8 |
| IFS | hasta 72 h | 24 | 24 | 24 | 0 | +1,6 | 288,3 / 326,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
