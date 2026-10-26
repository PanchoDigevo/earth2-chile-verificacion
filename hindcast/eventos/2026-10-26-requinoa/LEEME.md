# Tornado en Requínoa (O'Higgins), 26-oct-2026

Reporte: video publicado a las 17:48 de Chile (20:48 UTC) desde Villa Jardín de Requínoa: torbellino que levanta polvo y techumbres. A las 18:05 la Red Geocientífica de Chile (@RedGeoChile, en X) publicó más videos y lo calificó como **tornado EF-2**: es su clasificación preliminar, no una oficial. Sin informe oficial todavía (DMC/SENAPRED).

Es un evento muy poco común en Chile central. Por eso **este caso no se usa para calibrar nada**: los umbrales vienen de la literatura y este registro solo sirve de prueba (regla de hold-out de 2026).

## Qué vio el sistema

**Rayos (GOES-19 GLM), a menos de 50 km de Requínoa, por cada 10 minutos (UTC):**
19:40 → 26 · 19:50 → 71 · 20:00 → 103 · 20:10 → 182 · 20:20 → 222 · 20:30 → 157 · 20:40 → 178 · 20:50 → 245 · 21:00 → 129.
Un "salto de rayos" de ×8 en 40 minutos, que empezó unos 30-40 minutos antes del reporte. Registro guardado en `rayos_glm_100km.csv` (la ventana en vivo solo guarda 90 minutos: no hay datos antes de las 19:35 UTC).

**Pronóstico por comuna publicado a las 14:42 de Chile:** 16 mm en el bloque de 15 a 21 h, anunciados por los tres modelos; viento medio bajo (3 km/h): un tornado no se ve en el viento medio de 25 km.

**Ingredientes en GFS para las 21 UTC en Requínoa** (`ingredientes_gfs.py`):

| Corrida (antelación) | CAPE sup. | CIN | Índice de levantamiento | Cizalle 10 m–500 hPa | Cizalle 10 m–850 hPa | Helicidad 0-3 km |
|---|---|---|---|---|---|---|
| 25-oct 12Z (33 h) | 587 J/kg | −3 | −1,9 | 33 kt | 4 kt | 81 m²/s² |
| 26-oct 00Z (21 h) | 605 (824 a 50 km) | −1 | −3,7 | 27 kt | 3 kt | 101 |
| 26-oct 06Z (15 h) | 267 (683 a 50 km) | −9 | −1,8 | 32 kt | 6 kt | 89 |

Lectura: desde 33 h antes, ambiente inestable para Chile central, sin tapa (CIN ≈ 0) y con cizalle profundo moderado: tormentas eléctricas probables, algunas organizadas. El cizalle bajo (0-1,5 km) es débil, lo que no favorece tornados de supercelda clásicos; a 25 km un tornado no se pronostica, se anticipa el ambiente. (Helicidad de GFS con convención del hemisferio norte: en el sur, la rotación ciclónica es negativa.)

## Salto de rayos con el algoritmo publicado (sin ajustar)

`envivo/salto_rayos.py`, algoritmo 2σ de Schultz et al. (2009, 2011) con sus umbrales (≥ 10 rayos/min y aumento > 2σ de los 10 minutos previos), sobre los 90 minutos de rayos que guardaba En vivo a las 21:10 UTC más `rayos_glm_100km.csv`:

- **Requínoa:** salto a las 20:10, 20:12 y 20:14 UTC (17:10–17:14 de Chile), 34 a 38 minutos antes del primer video. Otro a las 20:46 y 21:02, ya hacia Rengo.
- **Las Condes:** sin salto. Ahí se oyó un trueno y se vio un relámpago a eso de las 17:10–17:20 de Chile; el satélite contó unos 80 rayos a menos de 20 km en esos 20 minutos (cuenta también los rayos entre nubes, que no se oyen), pero la tormenta no llegó a 10 rayos por minuto. Es el caso que no debe marcar. Registro en `rayos_glm_las_condes_100km.csv`.
- **Las Condes, segunda tormenta (18:10–19:00 de Chile):** Pancho la sintió en Las Condes cerca de las 19:00. El satélite la ubicó encima, a unos 3 km, con 12 a 16 rayos cada 10 minutos a menos de 20 km (menos de 2 por minuto). Sin salto, así que sin aviso. Es otra tormenta común que no debe marcar, salvo que aparezcan reportes de daño.
- **Cauquenes (Maule):** salto a las 19:58–20:18 UTC. No sabemos si hizo daño; si no, es una falsa alarma.

Cuántas veces marca en días de tormenta comunes se mide en `hindcast/salto_rayos/` (27 días con tormenta en algún aeródromo desde abril de 2025).
