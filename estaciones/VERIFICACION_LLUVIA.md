# Lluvia pronosticada frente a lluvia medida

Actualizado el 31-10-2026 12:29 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 752 | 84 | 84 | 243 | +0,9 | 601,6 / 1276,4 |
| AIFS | hasta 48 h | 688 | 84 | 84 | 255 | +0,7 | 599,7 / 1106,8 |
| AIFS | hasta 72 h | 624 | 60 | 60 | 179 | +0,7 | 381,5 / 789,7 |
| GFS | hasta 24 h | 752 | 84 | 83 | 204 | +0,9 | 601,6 / 1292,9 |
| GFS | hasta 48 h | 688 | 84 | 81 | 152 | +0,7 | 599,7 / 1064,1 |
| GFS | hasta 72 h | 624 | 60 | 53 | 117 | +0,3 | 381,5 / 556,7 |
| IFS | hasta 24 h | 752 | 84 | 73 | 203 | +1,3 | 601,6 / 1577,4 |
| IFS | hasta 48 h | 688 | 84 | 77 | 186 | +1,0 | 599,7 / 1258,0 |
| IFS | hasta 72 h | 624 | 60 | 57 | 178 | +1,2 | 381,5 / 1143,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
