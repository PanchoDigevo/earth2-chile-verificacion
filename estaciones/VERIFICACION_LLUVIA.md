# Lluvia pronosticada frente a lluvia medida

Actualizado el 27-10-2026 07:53 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 496 | 84 | 84 | 243 | +1,3 | 598,0 / 1258,3 |
| AIFS | hasta 48 h | 432 | 84 | 84 | 246 | +1,1 | 596,1 / 1084,1 |
| AIFS | hasta 72 h | 368 | 60 | 60 | 176 | +1,0 | 377,9 / 762,7 |
| GFS | hasta 24 h | 496 | 84 | 83 | 191 | +1,3 | 598,0 / 1256,9 |
| GFS | hasta 48 h | 432 | 84 | 81 | 137 | +0,9 | 596,1 / 981,4 |
| GFS | hasta 72 h | 368 | 60 | 53 | 94 | +0,1 | 377,9 / 424,9 |
| IFS | hasta 24 h | 492 | 81 | 70 | 199 | +1,9 | 593,5 / 1520,6 |
| IFS | hasta 48 h | 432 | 84 | 77 | 173 | +1,4 | 596,1 / 1216,7 |
| IFS | hasta 72 h | 368 | 60 | 57 | 152 | +1,9 | 377,9 / 1078,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
