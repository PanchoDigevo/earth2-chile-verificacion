# Lluvia pronosticada frente a lluvia medida

Actualizado el 20-10-2026 03:32 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 76 | 0 | 0 | 29 | +0,8 | 2,8 / 60,7 |
| AIFS | hasta 48 h | 15 | 0 | 0 | 13 | +1,4 | 0,9 / 22,4 |
| GFS | hasta 24 h | 76 | 0 | 0 | 47 | +2,7 | 2,8 / 207,5 |
| GFS | hasta 48 h | 15 | 0 | 0 | 10 | +2,2 | 0,9 / 34,0 |
| IFS | hasta 24 h | 75 | 0 | 0 | 35 | +1,3 | 2,7 / 100,5 |
| IFS | hasta 48 h | 15 | 0 | 0 | 11 | +1,5 | 0,9 / 22,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
