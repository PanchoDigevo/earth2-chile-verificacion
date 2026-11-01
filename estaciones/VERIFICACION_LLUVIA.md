# Lluvia pronosticada frente a lluvia medida

Actualizado el 01-11-2026 17:48 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 812 | 84 | 84 | 288 | +1,0 | 604,0 / 1406,3 |
| AIFS | hasta 48 h | 752 | 84 | 84 | 300 | +0,8 | 602,1 / 1228,4 |
| AIFS | hasta 72 h | 688 | 60 | 60 | 223 | +0,7 | 383,9 / 892,4 |
| GFS | hasta 24 h | 816 | 84 | 83 | 234 | +0,9 | 604,0 / 1360,5 |
| GFS | hasta 48 h | 752 | 84 | 81 | 180 | +0,8 | 602,1 / 1170,9 |
| GFS | hasta 72 h | 688 | 60 | 53 | 151 | +0,5 | 383,9 / 696,0 |
| IFS | hasta 24 h | 812 | 84 | 73 | 240 | +1,3 | 604,0 / 1688,7 |
| IFS | hasta 48 h | 752 | 84 | 77 | 230 | +1,1 | 602,1 / 1397,4 |
| IFS | hasta 72 h | 688 | 60 | 57 | 213 | +1,3 | 383,9 / 1246,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
