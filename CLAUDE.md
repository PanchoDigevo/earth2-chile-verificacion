# Earth-2 Chile — contexto técnico para Claude Code

**Este repo es público.** El contexto de negocio (estrategia, cifras, socios, conversaciones con terceros) está en `CLAUDE.local.md` y en la carpeta `privado/`, que no se versionan y solo existe en la copia de trabajo de Pancho. Léelo si existe. Nunca subas a este repo el caso de negocio, cifras, nombres de clientes ni correspondencia.

## Qué es

Inteligencia climática con IA para Chile a escala kilométrica (lluvia, temperatura, viento, nieve, radiación, niebla, riesgo de incendio, oleaje), usando la plataforma abierta NVIDIA Earth-2 (Earth2Studio, PhysicsNeMo, CorrDiff, SFNO/FourCastNet) y datos abiertos. Marca propia, "powered by NVIDIA Earth-2"; sin logos ni material de marca de NVIDIA.

- Lenguaje: **"aviso" o "pronóstico de impacto", nunca "alerta"**. La alerta oficial es atribución de la DMC y SENAPRED; cada aviso enlaza a ella. Es apoyo a la decisión.
- Pancho (dueño del proyecto) no es especialista técnico: explica en simple y propone un paso a la vez.

## Qué hay aquí

- `verificacion/` — pipeline diario: AIFS, IFS (ECMWF) y GFS (NOAA), los tres a 0,25°, vs METAR de 25 aeródromos chilenos; genera `site/`. Corre en GitHub Actions 4×/día (`.github/workflows/verificacion.yml`). `corridas.py` elige la última corrida completa con HEAD a los índices (nunca `Client.latest()`); `verify.py` guarda los pronósticos por estación en `data/pronostico_puntos.csv` y empareja con METAR cuando llega la observación; los pares llevan columna `modelo`.
- `site/` — página pública en GitHub Pages.
- `hindcast/` — eventos 2026 en tres capas: lluvia (ERA5 + pronósticos históricos IFS/GFS/AIFS a 24-48-72 h), superficie (Sentinel-2 dNBR de incendios, DEM 30 m, quebradas OSM, humedad de suelo), verdad (SERNAGEOMIN, SENAPRED). Lógica tipo USGS post-incendio: intensidad de lluvia × severidad de quema × pendiente × suelo.
- `docs/chile_natural_earth_10m.json` — contorno de Chile (Natural Earth, dominio público) para mapas.

## Narrativa del sitio

El texto público de la portada está en `docs/narrativa_sitio.md`. Es la fuente de verdad del mensaje: el sitio no dice que AIFS sea malo, dice que 25 km no alcanza para la geografía chilena y que la capa chilena (CorrDiff 4 km + corrección por estación + satélite y superficie) se va a medir en esta misma página contra el global. `verify.py` debe insertar este texto arriba, antes de las tablas, con el aviso final al pie.

## Próximos pasos técnicos

1. Sitio: serie de 30 días, precipitación; estaciones DMC cuando haya token. (IFS y GFS ya se comparan; el mapa ya colorea por error y modelo.)
2. Hindcast: catálogo de eventos (`hindcast/eventos/`), capa de lluvia, capa de superficie para RM y V Región, cruce con la verdad. Resultado: "de N eventos, M marcados con X h de anticipación".
3. Página de aviso simulado: cómo se ve el mensaje para un municipio.
4. Capa de superficie y mapa de quebradas quemadas (primera venta, sin GPU): Sentinel-2 dNBR del verano 2026 sobre Santiago oriente (incendio de enero sobre San Carlos de Apoquindo, ~1.012 ha), DEM Copernicus 30 m → pendiente, cauces OSM/DGA, humedad SMAP, catálogo de remociones en masa de SERNAGEOMIN. Salida: GeoJSON de cuencas de quebrada con quema × pendiente × historial, publicado en `site/quebradas.html` sobre el mapa de Natural Earth + teselas abiertas. Luego, umbral de intensidad-duración tipo USGS por cuenca para el aviso. Eventos: `hindcast/eventos/eventos_2026.csv`.
5. CorrDiff-Chile (downscaling 25 → 4 km) con SAAG-WRF 4 km + ERA5, en GPUs L40S con PhysicsNeMo. No bloquea los puntos anteriores.

## Dónde corre cada cosa

- GitHub Actions: lo liviano y diario.
- Instancia de nube sin GPU o nodos CPU del POD: hindcast pesado y preparación de datasets (ERA5, SAAG en `s3://saag-wrf/`, Sentinel-2). Solo resultados vuelven al repo.
- GPUs L40S del POD: entrenamiento (contenedor `nvcr.io/nvidia/physicsnemo/physicsnemo:25.11`, ejemplo `examples/weather/corrdiff`) y, en fase 1, inferencia vía NVIDIA Cloud Functions.
- El Mac de Pancho solo orquesta: sin GPU NVIDIA, red lenta, VM de 4 GB.

## Convenciones y trampas

- venv fuera de OneDrive (`~/e2venv`): dentro de OneDrive los instaladores fallan al borrar temporales.
- `ecmwf-opendata` con `source="aws"`; el servidor directo de ECMWF devuelve 429.
- En la VM del Mac los procesos mueren al terminar cada comando (máx. 3 min).
- METAR: `aviationweather.gov/api/data/metar?ids=...&format=json&hours=48`, sin clave. NOAA ISD se cortó en ago-2025.
- API DMC requiere usuario y token (portal de Servicios Climáticos).
- Licencias: ERA5 y ECMWF open data CC-BY 4.0 (atribuir); NOAA dominio público; SAAG-WRF CC-BY 4.0; Sentinel-2 abierto; Earth-2 Apache 2.0 / NVIDIA Open Model License. Evitar CorrDiff Taiwán (CC-BY-NC-ND) y cBottle/DLESyM.
- Hold-out: los eventos 2026 nunca entran al entrenamiento. Comparar también contra el WRF operacional de la DMC (6 km).
- Cosmos de NVIDIA no aplica (video sintético, no pronóstico).
- Commits en español. No subir GRIB, netCDF, Zarr ni datos crudos.
