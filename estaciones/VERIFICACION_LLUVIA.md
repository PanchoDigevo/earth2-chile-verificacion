# Lluvia pronosticada frente a lluvia medida

Actualizado el 19-10-2026 22:40 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 72 | 0 | 0 | 28 | +0,8 | 2,4 / 57,3 |
| AIFS | hasta 48 h | 12 | 0 | 0 | 11 | +1,6 | 0,6 / 19,7 |
| GFS | hasta 24 h | 72 | 0 | 0 | 44 | +2,8 | 2,4 / 203,3 |
| GFS | hasta 48 h | 12 | 0 | 0 | 10 | +2,7 | 0,6 / 32,5 |
| IFS | hasta 24 h | 68 | 0 | 0 | 35 | +1,4 | 2,4 / 98,3 |
| IFS | hasta 48 h | 12 | 0 | 0 | 11 | +1,8 | 0,6 / 22,3 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
