# Hindcast de eventos 2026

Objetivo: mostrar qué se habría avisado 72, 48, 24, 6 y 1 h antes de cada evento, y cruzarlo con lo que de verdad pasó.

- `eventos/` — catálogo de eventos (fecha, lugar, qué pasó, fuentes): Coquimbo 14–24 jul, centro-sur 30 jul–2 ago, Las Condes 8 oct.
- `lluvia/` — capa atmosférica: ERA5 (lo ocurrido), pronósticos históricos IFS/GFS/AIFS desde las réplicas de AWS (lo que se veía antes).
- `superficie/` — capa de superficie: cicatrices de incendio del verano 2026 (Sentinel-2 dNBR), DEM 30 m, quebradas (OSM), humedad de suelo.
- `verdad/` — catálogo de remociones en masa (SERNAGEOMIN), informes SENAPRED, prensa: la lista de qué quebradas bajaron.

Lo pesado (ERA5 y Sentinel-2) se procesa en una instancia de nube sin GPU; aquí quedan scripts, catálogos y resultados (mapas y tablas), no los datos crudos.
