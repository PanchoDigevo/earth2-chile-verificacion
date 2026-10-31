# Lluvia pronosticada frente a lluvia medida

Actualizado el 30-10-2026 22:47 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 724 | 84 | 84 | 243 | +0,9 | 599,2 / 1274,4 |
| AIFS | hasta 48 h | 660 | 84 | 84 | 255 | +0,8 | 597,3 / 1103,9 |
| AIFS | hasta 72 h | 596 | 60 | 60 | 179 | +0,7 | 379,1 / 787,5 |
| GFS | hasta 24 h | 724 | 84 | 83 | 204 | +1,0 | 599,2 / 1289,0 |
| GFS | hasta 48 h | 660 | 84 | 81 | 152 | +0,7 | 597,3 / 1060,4 |
| GFS | hasta 72 h | 596 | 60 | 53 | 117 | +0,3 | 379,1 / 555,2 |
| IFS | hasta 24 h | 724 | 84 | 73 | 203 | +1,4 | 599,2 / 1576,8 |
| IFS | hasta 48 h | 660 | 84 | 77 | 186 | +1,0 | 597,3 / 1257,2 |
| IFS | hasta 72 h | 596 | 60 | 57 | 178 | +1,3 | 379,1 / 1143,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
