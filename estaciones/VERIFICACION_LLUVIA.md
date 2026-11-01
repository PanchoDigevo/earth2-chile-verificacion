# Lluvia pronosticada frente a lluvia medida

Actualizado el 01-11-2026 13:22 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 797 | 84 | 84 | 279 | +1,0 | 604,0 / 1392,8 |
| AIFS | hasta 48 h | 736 | 84 | 84 | 291 | +0,8 | 602,1 / 1213,8 |
| AIFS | hasta 72 h | 672 | 60 | 60 | 211 | +0,7 | 383,9 / 877,5 |
| GFS | hasta 24 h | 797 | 84 | 83 | 228 | +0,9 | 604,0 / 1348,7 |
| GFS | hasta 48 h | 736 | 84 | 81 | 180 | +0,8 | 602,1 / 1162,2 |
| GFS | hasta 72 h | 672 | 60 | 53 | 145 | +0,4 | 383,9 / 683,1 |
| IFS | hasta 24 h | 797 | 84 | 73 | 231 | +1,3 | 604,0 / 1671,6 |
| IFS | hasta 48 h | 736 | 84 | 77 | 218 | +1,1 | 602,1 / 1375,0 |
| IFS | hasta 72 h | 672 | 60 | 57 | 201 | +1,2 | 383,9 / 1223,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
