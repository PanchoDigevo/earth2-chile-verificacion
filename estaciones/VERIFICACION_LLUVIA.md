# Lluvia pronosticada frente a lluvia medida

Actualizado el 27-10-2026 21:42 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 544 | 84 | 84 | 243 | +1,2 | 599,2 / 1258,3 |
| AIFS | hasta 48 h | 480 | 84 | 84 | 246 | +1,0 | 597,3 / 1084,5 |
| AIFS | hasta 72 h | 416 | 60 | 60 | 176 | +0,9 | 379,1 / 766,6 |
| GFS | hasta 24 h | 544 | 84 | 83 | 191 | +1,2 | 599,2 / 1256,9 |
| GFS | hasta 48 h | 480 | 84 | 81 | 137 | +0,8 | 597,3 / 982,6 |
| GFS | hasta 72 h | 416 | 60 | 53 | 95 | +0,1 | 379,1 / 431,1 |
| IFS | hasta 24 h | 540 | 84 | 73 | 200 | +1,8 | 599,2 / 1556,4 |
| IFS | hasta 48 h | 480 | 84 | 77 | 176 | +1,3 | 597,3 / 1225,6 |
| IFS | hasta 72 h | 416 | 60 | 57 | 164 | +1,7 | 379,1 / 1104,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
