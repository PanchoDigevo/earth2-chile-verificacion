# Lluvia pronosticada frente a lluvia medida

Actualizado el 21-10-2026 02:14 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 136 | 32 | 32 | 48 | +1,0 | 304,0 / 441,1 |
| AIFS | hasta 48 h | 72 | 32 | 32 | 35 | -0,2 | 302,1 / 285,3 |
| AIFS | hasta 72 h | 12 | 12 | 12 | 0 | -6,2 | 135,0 / 60,7 |
| GFS | hasta 24 h | 136 | 32 | 31 | 75 | +1,7 | 304,0 / 529,6 |
| GFS | hasta 48 h | 72 | 32 | 29 | 28 | -0,6 | 302,1 / 260,8 |
| GFS | hasta 72 h | 12 | 12 | 12 | 0 | -7,2 | 135,0 / 49,1 |
| IFS | hasta 24 h | 136 | 32 | 32 | 48 | +2,1 | 304,0 / 588,7 |
| IFS | hasta 48 h | 72 | 32 | 32 | 30 | +0,8 | 302,1 / 359,8 |
| IFS | hasta 72 h | 12 | 12 | 12 | 0 | +0,6 | 135,0 / 142,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
