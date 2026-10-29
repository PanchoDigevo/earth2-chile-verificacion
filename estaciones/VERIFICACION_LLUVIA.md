# Lluvia pronosticada frente a lluvia medida

Actualizado el 29-10-2026 16:12 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 644 | 84 | 84 | 243 | +1,0 | 599,2 / 1260,2 |
| AIFS | hasta 48 h | 584 | 84 | 84 | 246 | +0,8 | 597,3 / 1085,8 |
| AIFS | hasta 72 h | 520 | 60 | 60 | 176 | +0,7 | 379,1 / 768,8 |
| GFS | hasta 24 h | 648 | 84 | 83 | 191 | +1,0 | 599,2 / 1257,2 |
| GFS | hasta 48 h | 584 | 84 | 81 | 137 | +0,7 | 597,3 / 983,8 |
| GFS | hasta 72 h | 520 | 60 | 53 | 95 | +0,1 | 379,1 / 433,8 |
| IFS | hasta 24 h | 644 | 84 | 73 | 200 | +1,5 | 599,2 / 1558,7 |
| IFS | hasta 48 h | 584 | 84 | 77 | 176 | +1,1 | 597,3 / 1228,9 |
| IFS | hasta 72 h | 520 | 60 | 57 | 164 | +1,4 | 379,1 / 1110,2 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
