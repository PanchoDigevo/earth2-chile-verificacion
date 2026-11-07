# Lluvia pronosticada frente a lluvia medida

Actualizado el 07-11-2026 00:10 (hora de Chile) por `estaciones/verificar_lluvia.py`. Bloques de 6 h del seguimiento
horario (`hindcast/seguimiento/pronosticos.csv`) comparados con la estación DMC más cercana bajo 1.500 m
(mensajes SYNOP, `estaciones/datos/synop/`). Un bloque cuenta como lluvioso desde 1 mm en 6 h.

Estación usada para cada punto:

- Quebrada de Apoquindo (San Carlos de Apoquindo): Aguas Andinas (La Florida) (670 m), a 17 km
- Quebrada de Ramón: Aguas Andinas (La Florida) (670 m), a 13 km
- Santiago (Pudahuel): Pudahuel (aeropuerto) (482 m), a 1 km
- Tobalaba (Las Condes): Aguas Andinas (La Florida) (670 m), a 10 km

| Modelo | Plazo | Bloques | Bloques con lluvia medida | Avisados por el modelo | Falsas alarmas | Error medio (mm) | Lluvia medida / pronosticada |
|---|---|---|---|---|---|---|---|
| AIFS | hasta 24 h | 1014 | 84 | 84 | 350 | +1,0 | 608,8 / 1617,4 |
| AIFS | hasta 48 h | 954 | 84 | 84 | 343 | +0,8 | 604,5 / 1342,1 |
| AIFS | hasta 72 h | 890 | 60 | 60 | 315 | +0,8 | 387,5 / 1143,4 |
| GFS | hasta 24 h | 1048 | 84 | 83 | 257 | +0,8 | 608,8 / 1430,1 |
| GFS | hasta 48 h | 978 | 84 | 81 | 204 | +0,6 | 604,5 / 1226,2 |
| GFS | hasta 72 h | 914 | 60 | 53 | 172 | +0,4 | 388,7 / 773,5 |
| IFS | hasta 24 h | 1018 | 84 | 73 | 303 | +1,4 | 608,8 / 2033,4 |
| IFS | hasta 48 h | 954 | 84 | 77 | 263 | +1,0 | 604,5 / 1536,9 |
| IFS | hasta 72 h | 890 | 60 | 57 | 279 | +1,2 | 387,5 / 1445,0 |

Los pluviómetros miden un punto; el modelo, el promedio de una celda de unos 25 km. Datos de estación provisorios,
sin control de calidad. No es un aviso: las alertas oficiales son de la DMC y SENAPRED.
