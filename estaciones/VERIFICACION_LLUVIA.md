# Lluvia pronosticada frente a lluvia medida

Actualizado el 30-10-2026 18:42 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 708 | 84 | 84 | 243 | +0,9 | 599,2 / 1263,5 |
| AIFS | hasta 48 h | 644 | 84 | 84 | 246 | +0,8 | 597,3 / 1088,4 |
| AIFS | hasta 72 h | 580 | 60 | 60 | 176 | +0,7 | 379,1 / 774,3 |
| GFS | hasta 24 h | 708 | 84 | 83 | 191 | +0,9 | 599,2 / 1262,1 |
| GFS | hasta 48 h | 644 | 84 | 81 | 137 | +0,6 | 597,3 / 994,0 |
| GFS | hasta 72 h | 580 | 60 | 53 | 101 | +0,1 | 379,1 / 452,9 |
| IFS | hasta 24 h | 708 | 84 | 73 | 200 | +1,4 | 599,2 / 1567,3 |
| IFS | hasta 48 h | 644 | 84 | 77 | 182 | +1,0 | 597,3 / 1242,0 |
| IFS | hasta 72 h | 580 | 60 | 57 | 176 | +1,3 | 379,1 / 1132,4 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
