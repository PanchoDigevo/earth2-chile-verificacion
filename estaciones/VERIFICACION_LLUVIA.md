# Lluvia pronosticada frente a lluvia medida

Actualizado el 01-11-2026 06:40 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 788 | 84 | 84 | 279 | +1,0 | 604,0 / 1389,8 |
| AIFS | hasta 48 h | 724 | 84 | 84 | 291 | +0,8 | 602,1 / 1211,1 |
| AIFS | hasta 72 h | 660 | 60 | 60 | 211 | +0,7 | 383,9 / 875,4 |
| GFS | hasta 24 h | 788 | 84 | 83 | 228 | +0,9 | 604,0 / 1346,6 |
| GFS | hasta 48 h | 724 | 84 | 81 | 177 | +0,8 | 602,1 / 1152,9 |
| GFS | hasta 72 h | 660 | 60 | 53 | 145 | +0,4 | 383,9 / 676,8 |
| IFS | hasta 24 h | 788 | 84 | 73 | 231 | +1,4 | 604,0 / 1671,6 |
| IFS | hasta 48 h | 724 | 84 | 77 | 218 | +1,1 | 602,1 / 1374,1 |
| IFS | hasta 72 h | 660 | 60 | 57 | 201 | +1,3 | 383,9 / 1220,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
