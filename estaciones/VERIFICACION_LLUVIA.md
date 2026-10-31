# Lluvia pronosticada frente a lluvia medida

Actualizado el 31-10-2026 19:47 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 768 | 84 | 84 | 259 | +0,9 | 604,0 / 1304,9 |
| AIFS | hasta 48 h | 704 | 84 | 84 | 271 | +0,8 | 602,1 / 1131,6 |
| AIFS | hasta 72 h | 640 | 60 | 60 | 191 | +0,7 | 383,9 / 809,7 |
| GFS | hasta 24 h | 768 | 84 | 83 | 216 | +0,9 | 604,0 / 1312,5 |
| GFS | hasta 48 h | 704 | 84 | 81 | 164 | +0,7 | 602,1 / 1099,7 |
| GFS | hasta 72 h | 640 | 60 | 53 | 129 | +0,3 | 383,9 / 591,8 |
| IFS | hasta 24 h | 768 | 84 | 73 | 215 | +1,3 | 604,0 / 1596,3 |
| IFS | hasta 48 h | 704 | 84 | 77 | 201 | +1,0 | 602,1 / 1280,0 |
| IFS | hasta 72 h | 640 | 60 | 57 | 185 | +1,2 | 383,9 / 1159,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
