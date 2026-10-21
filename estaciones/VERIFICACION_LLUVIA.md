# Lluvia pronosticada frente a lluvia medida

Actualizado el 21-10-2026 12:33 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 164 | 48 | 48 | 48 | -0,1 | 518,0 / 507,6 |
| AIFS | hasta 48 h | 100 | 48 | 48 | 35 | -1,7 | 516,1 / 345,7 |
| AIFS | hasta 72 h | 36 | 24 | 24 | 0 | -5,5 | 297,9 / 100,7 |
| GFS | hasta 24 h | 164 | 48 | 47 | 75 | +0,6 | 518,0 / 609,9 |
| GFS | hasta 48 h | 100 | 48 | 45 | 31 | -2,0 | 516,1 / 318,9 |
| GFS | hasta 72 h | 36 | 24 | 23 | 0 | -6,2 | 297,9 / 75,1 |
| IFS | hasta 24 h | 164 | 48 | 46 | 57 | +1,5 | 518,0 / 767,1 |
| IFS | hasta 48 h | 100 | 48 | 47 | 42 | +0,6 | 516,1 / 580,0 |
| IFS | hasta 72 h | 36 | 24 | 24 | 9 | +1,5 | 297,9 / 351,7 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
