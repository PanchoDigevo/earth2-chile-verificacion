# Lluvia pronosticada frente a lluvia medida

Actualizado el 20-10-2026 09:03 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 88 | 0 | 0 | 32 | +0,8 | 2,8 / 70,0 |
| AIFS | hasta 48 h | 24 | 0 | 0 | 19 | +1,3 | 0,9 / 32,3 |
| GFS | hasta 24 h | 88 | 0 | 0 | 59 | +2,5 | 2,8 / 222,5 |
| GFS | hasta 48 h | 24 | 0 | 0 | 13 | +1,8 | 0,9 / 43,0 |
| IFS | hasta 24 h | 88 | 0 | 0 | 35 | +1,2 | 2,8 / 106,4 |
| IFS | hasta 48 h | 24 | 0 | 0 | 17 | +1,4 | 0,9 / 34,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
