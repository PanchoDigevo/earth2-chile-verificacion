# Tornado en Requínoa (O'Higgins), 26-oct-2026

Reporte: video publicado a las 17:48 de Chile (20:48 UTC) desde Villa Jardín de Requínoa: torbellino que levanta polvo y techumbres. Sin informe oficial todavía (DMC/SENAPRED).

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
