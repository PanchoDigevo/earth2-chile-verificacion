# Lluvia pronosticada frente a lluvia medida

Actualizado el 29-10-2026 23:53 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 660 | 84 | 84 | 243 | +1,0 | 599,2 / 1261,1 |
| AIFS | hasta 48 h | 600 | 84 | 84 | 246 | +0,8 | 597,3 / 1086,5 |
| AIFS | hasta 72 h | 536 | 60 | 60 | 176 | +0,7 | 379,1 / 770,9 |
| GFS | hasta 24 h | 664 | 84 | 83 | 191 | +1,0 | 599,2 / 1260,9 |
| GFS | hasta 48 h | 600 | 84 | 81 | 137 | +0,7 | 597,3 / 990,7 |
| GFS | hasta 72 h | 536 | 60 | 53 | 98 | +0,1 | 379,1 / 444,2 |
| IFS | hasta 24 h | 664 | 84 | 73 | 200 | +1,5 | 599,2 / 1566,6 |
| IFS | hasta 48 h | 600 | 84 | 77 | 182 | +1,1 | 597,3 / 1240,3 |
| IFS | hasta 72 h | 536 | 60 | 57 | 176 | +1,4 | 379,1 / 1131,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
