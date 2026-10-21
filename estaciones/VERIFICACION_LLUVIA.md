# Lluvia pronosticada frente a lluvia medida

Actualizado el 20-10-2026 21:06 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 120 | 16 | 16 | 48 | +1,4 | 62,8 / 227,7 |
| AIFS | hasta 48 h | 56 | 16 | 16 | 35 | +1,8 | 60,9 / 161,5 |
| AIFS | hasta 72 h | 4 | 4 | 4 | 0 | -0,1 | 14,4 / 14,0 |
| GFS | hasta 24 h | 120 | 16 | 15 | 75 | +2,5 | 62,8 / 358,1 |
| GFS | hasta 48 h | 56 | 16 | 13 | 28 | +1,6 | 60,9 / 150,9 |
| GFS | hasta 72 h | 4 | 4 | 4 | 0 | +2,8 | 14,4 / 25,5 |
| IFS | hasta 24 h | 120 | 16 | 16 | 48 | +1,4 | 62,8 / 224,9 |
| IFS | hasta 48 h | 56 | 16 | 16 | 30 | +1,1 | 60,9 / 125,1 |
| IFS | hasta 72 h | 4 | 4 | 4 | 0 | +1,2 | 14,4 / 19,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
