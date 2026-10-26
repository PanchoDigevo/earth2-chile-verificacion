# Prueba del indicador de tormentas a 72 h

`verificacion/tormentas_gfs.py` con sus cortes publicados, sobre GFS 00 UTC (plazos 12 a 36 h) de oct-2025 a oct-2026, en
10 aeródromos de Valparaíso a La Araucanía, contra los METAR que informan tormenta (TS o VCTS) a ±1,5 h (`tormentas-gfs-prueba.yml`).

## Resultado (390 días, 3.806 días-aeródromo)

| Nivel | Marcados | Tormentas en el METAR | Anticipadas | Marcas sin tormenta en el METAR |
|---|---|---|---|---|
| Tormentas posibles | 368 días-aeródromo (10 %) | 39 (1 % de los días) | 31 (79 %) | 337 (92 %) |
| Tormentas fuertes posibles | 92 (2 %) | 39 | 11 (28 %) | 81 (88 %) |

Detecta casi 8 de cada 10 tormentas informadas, pero la gran mayoría de sus marcas no tiene tormenta en ese METAR. Dos
cosas inflan esa cifra: el METAR solo ve unos 15 km alrededor de la pista, y varios aeródromos chilenos informan tormenta
de forma irregular (39 días-aeródromo en un año es poco). Para medirlo bien hace falta una verdad más completa: los rayos
del GLM a menos de 25 km de cada punto, cada día del año. Mientras tanto, el indicador se muestra como ambiente
("posibles") dentro del pronóstico, nunca como aviso destacado.
