# Lluvia pronosticada frente a lluvia medida

Actualizado el 03-11-2026 15:00 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 824 | 84 | 84 | 294 | +1,0 | 604,0 / 1415,4 |
| AIFS | hasta 48 h | 814 | 84 | 84 | 319 | +0,8 | 602,1 / 1266,1 |
| AIFS | hasta 72 h | 780 | 60 | 60 | 260 | +0,8 | 383,9 / 980,6 |
| GFS | hasta 24 h | 854 | 84 | 83 | 240 | +0,9 | 604,0 / 1372,9 |
| GFS | hasta 48 h | 834 | 84 | 81 | 204 | +0,7 | 602,1 / 1214,7 |
| GFS | hasta 72 h | 780 | 60 | 53 | 166 | +0,5 | 383,9 / 741,4 |
| IFS | hasta 24 h | 824 | 84 | 73 | 248 | +1,3 | 604,0 / 1714,6 |
| IFS | hasta 48 h | 814 | 84 | 77 | 248 | +1,1 | 602,1 / 1488,5 |
| IFS | hasta 72 h | 780 | 60 | 57 | 241 | +1,2 | 383,9 / 1321,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
