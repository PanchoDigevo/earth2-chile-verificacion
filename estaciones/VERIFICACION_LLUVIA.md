# Lluvia pronosticada frente a lluvia medida

Actualizado el 06-11-2026 08:26 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 968 | 84 | 84 | 329 | +1,0 | 606,4 / 1571,3 |
| AIFS | hasta 48 h | 910 | 84 | 84 | 319 | +0,7 | 602,1 / 1278,9 |
| AIFS | hasta 72 h | 846 | 60 | 60 | 283 | +0,8 | 385,1 / 1056,2 |
| GFS | hasta 24 h | 1004 | 84 | 83 | 257 | +0,8 | 606,4 / 1422,2 |
| GFS | hasta 48 h | 934 | 84 | 81 | 204 | +0,7 | 602,1 / 1221,0 |
| GFS | hasta 72 h | 870 | 60 | 53 | 172 | +0,4 | 386,3 / 769,7 |
| IFS | hasta 24 h | 959 | 84 | 73 | 288 | +1,5 | 606,4 / 1998,4 |
| IFS | hasta 48 h | 910 | 84 | 77 | 251 | +1,0 | 602,1 / 1498,9 |
| IFS | hasta 72 h | 846 | 60 | 57 | 261 | +1,2 | 385,1 / 1390,8 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
