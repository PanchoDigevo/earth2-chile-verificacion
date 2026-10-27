# Lluvia pronosticada frente a lluvia medida

Actualizado el 27-10-2026 13:50 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 512 | 84 | 84 | 243 | +1,3 | 599,2 / 1258,3 |
| AIFS | hasta 48 h | 448 | 84 | 84 | 246 | +1,1 | 597,3 / 1084,5 |
| AIFS | hasta 72 h | 384 | 60 | 60 | 176 | +1,0 | 379,1 / 765,4 |
| GFS | hasta 24 h | 512 | 84 | 83 | 191 | +1,3 | 599,2 / 1256,9 |
| GFS | hasta 48 h | 448 | 84 | 81 | 137 | +0,9 | 597,3 / 982,6 |
| GFS | hasta 72 h | 384 | 60 | 53 | 95 | +0,1 | 379,1 / 431,1 |
| IFS | hasta 24 h | 512 | 84 | 73 | 200 | +1,9 | 599,2 / 1554,4 |
| IFS | hasta 48 h | 448 | 84 | 77 | 173 | +1,4 | 597,3 / 1216,9 |
| IFS | hasta 72 h | 384 | 60 | 57 | 155 | +1,8 | 379,1 / 1082,9 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
