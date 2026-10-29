# Earth-2 Chile — contexto técnico para Claude Code

**Este repo es público.** El contexto de negocio (estrategia, cifras, socios, conversaciones con terceros) está en `CLAUDE.local.md` y en la carpeta `privado/`, que no se versionan y solo existe en la copia de trabajo de Pancho. Léelo si existe. Nunca subas a este repo el caso de negocio, cifras, nombres de clientes ni correspondencia.

## Qué es

Inteligencia climática con IA para Chile a escala kilométrica (lluvia, temperatura, viento, nieve, radiación, niebla, riesgo de incendio, oleaje), usando la plataforma abierta NVIDIA Earth-2 (Earth2Studio, PhysicsNeMo, CorrDiff, SFNO/FourCastNet) y datos abiertos. Marca propia, "powered by NVIDIA Earth-2"; sin logos ni material de marca de NVIDIA.

- Lenguaje: **"aviso" o "pronóstico de impacto", nunca "alerta"**. La alerta oficial es atribución de la DMC y SENAPRED; cada aviso enlaza a ella. Es apoyo a la decisión.
- Pancho (dueño del proyecto) no es especialista técnico: explica en simple y propone un paso a la vez.

## Qué hay aquí

- `verificacion/` — pipeline diario: AIFS, IFS (ECMWF) y GFS (NOAA), los tres a 0,25°, vs METAR de 25 aeródromos chilenos; genera `site/`. Corre en GitHub Actions 4×/día (`.github/workflows/verificacion.yml`). `corridas.py` elige la última corrida completa con HEAD a los índices (nunca `Client.latest()`); `verify.py` guarda los pronósticos por estación en `data/pronostico_puntos.csv` y empareja con METAR cuando llega la observación; los pares llevan columna `modelo`. La referencia oficial es la DMC (`fetch_dmc.py`, desde el 29-oct-2026): su modelo WRF entra como modelo externo "WRF-DMC" y su pronóstico redactado se verifica aparte (`dmc_oficial.py`); siempre se presenta como la vara, nunca como competencia.
- `site/` — página pública en GitHub Pages.
- `estaciones/` — lluvia medida: SYNOP horarios de las 141 estaciones de Chile (bloque OMM 85, casi todas EMA de la DMC; un CSV por mes en `estaciones/datos/synop/`), vía Ogimet (`synop.py`, sin clave), API de la DMC con secretos `DMC_USUARIO`/`DMC_TOKEN` (`dmc.py`, sin ellos no hace nada) y verificación de los bloques de 6 h del seguimiento (`verificar_lluvia.py`). Corre cada hora (`estaciones.yml`). La red en tiempo real de la DGA pide captcha: no se lee automáticamente (no saltarse el captcha; hay que pedir acceso a la DGA). Estaciones en `estaciones/catalogo.csv`.
- `hindcast/` — eventos 2026 en tres capas: lluvia (ERA5 + pronósticos históricos IFS/GFS/AIFS a 24-48-72 h), superficie (Sentinel-2 dNBR de incendios, DEM 30 m, quebradas OSM, humedad de suelo), verdad (SERNAGEOMIN, SENAPRED). Lógica tipo USGS post-incendio: intensidad de lluvia × severidad de quema × pendiente × suelo.
- `earth2/` — cómo usamos Earth2Studio (dependencia, no copia): conectores de datos sin GPU (`AIFS_FX`, `IFS_FX`, `GFS_FX`, `IEM_ASOS`, `GOES`, `GOESGLM`, `ARCO_ERA5`) y, con GPU, `AIFS`, `StormScopeGOES` (nowcaster base) y CorrDiff. `earth2/fetch_e2s.py` reemplaza a `fetch_aifs.py` cuando se valide (revisar la selección por estación con `sel`, está esbozada).
- `docs/chile_natural_earth_10m.json` — contorno de Chile (Natural Earth, dominio público) para mapas.

## Narrativa del sitio

El texto público de la portada está en `docs/narrativa_sitio.md`. Es la fuente de verdad del mensaje: el sitio no dice que AIFS sea malo, dice que 25 km no alcanza para la geografía chilena y que la capa chilena (CorrDiff 4 km + corrección por estación + satélite y superficie) se va a medir en esta misma página contra el global. `verify.py` debe insertar este texto arriba, antes de las tablas, con el aviso final al pie.

## Capas estándar (higiene: van siempre, en todo producto)

1. Atmósfera: AIFS/IFS/GFS y AIFS-ENS (escenarios), luego CorrDiff-Chile a 4 km.
2. Superficie: cicatrices de incendio (Sentinel-2), pendiente (DEM 30 m), cauces, humedad del suelo, catálogo SERNAGEOMIN.
3. **Océano y costa**: Chile tiene más de 4.000 km de costa; el mar define camanchaca, lluvias de El Niño, marejadas, salmón y pesca. Diario: anomalía de temperatura del mar (NOAA OISST v2.1, 0,25°, contra climatología 1991–2020) en cajas costeras frente a cada aeródromo de la costa y en Niño 1+2; índices semanales Niño 1+2 y 3.4 de NOAA CPC. Oleaje/marejadas cuando se sume un modelo de olas.
4. **Viento**: velocidad, dirección y rachas a 10 m, verificados igual que la temperatura (diario e histórico). Las rachas importan más que el promedio (incendios, líneas eléctricas, salmoneras, puertos, faenas). Vientos locales que el global a 25 km no resuelve: puelche, raco, terral, viento blanco; es donde más rinde el downscaling por terreno.
5. Deriva: sesgo móvil de 30 días por estación contra el aprendido; la corrección se evalúa fija (2025) y móvil (45 días) sin mirar el futuro.
6. **Tormentas y tiempo severo** (desde el tornado de Requínoa, 26-oct-2026): dos avisos. Para planificar, el ambiente a 72 h por comuna con ingredientes de GFS (`verificacion/tormentas_gfs.py`: CAPE, CIN, disparador, cizalle). Para reaccionar, el salto de rayos del GOES-19 cada 5 minutos (`envivo/salto_rayos.py`, algoritmo 2σ de Schultz et al.), con aviso en portada, Tu zona, Pronóstico y En vivo (`verificacion/tormenta_vivo.py`). Los umbrales son los publicados; **nunca se calibran con un evento raro** (lo marcaría por construcción y esconde las falsas alarmas): los eventos sirven de prueba y las falsas alarmas se miden en días comunes (`hindcast/salto_rayos/`, `hindcast/tormentas_gfs/`).

Regla: los cambios de régimen (El Niño, olas de calor marinas) se detectan desde datos primarios, nunca desde noticias. Si un dato no lo muestra, el sitio no lo dice.

## Próximos pasos técnicos

1. Sitio: serie de 30 días, precipitación (ya hay lluvia medida en `estaciones/`); más estaciones DMC cuando haya token; acceso a la DGA. (IFS y GFS ya se comparan; el mapa ya colorea por error y modelo.)
2. Hindcast: catálogo de eventos (`hindcast/eventos/`), capa de lluvia, capa de superficie para RM y V Región, cruce con la verdad. Resultado: "de N eventos, M marcados con X h de anticipación".
3. Página de aviso simulado: cómo se ve el mensaje para un municipio.
4. Capa de superficie y mapa de quebradas quemadas (primera venta, sin GPU): Sentinel-2 dNBR del verano 2026 sobre Santiago oriente (incendio de enero sobre San Carlos de Apoquindo, ~1.012 ha), DEM Copernicus 30 m → pendiente, cauces OSM/DGA, humedad SMAP, catálogo de remociones en masa de SERNAGEOMIN. Salida: GeoJSON de cuencas de quebrada con quema × pendiente × historial, publicado en `site/quebradas.html` sobre el mapa de Natural Earth + teselas abiertas. Luego, umbral de intensidad-duración tipo USGS por cuenca para el aviso. Eventos: `hindcast/eventos/eventos_2026.csv`.
5. CorrDiff-Chile (downscaling 25 → 4 km) con SAAG-WRF 4 km + ERA5, en GPUs L40S con PhysicsNeMo. No bloquea los puntos anteriores.
   **Hay que entrenarlo: no existe un CorrDiff para Chile.** Los CorrDiff preentrenados de NVIDIA son de EE.UU. y Taiwán y no sirven para inferencia sobre Chile. Lo que corre hoy sobre Chile son modelos globales (AIFS, IFS, GFS bajados ya calculados; FourCastNet cuando lo corramos). Todo texto público (sitio, README, presentaciones) debe decirlo así: CorrDiff-Chile "por entrenar", nunca como algo que ya corre. El bloque "En qué etapa estamos" (`ETAPAS` en `verificacion/comun.py`) se actualiza cuando cambia una etapa.

## Dónde corre cada cosa

- GitHub Actions: lo liviano y diario.
- Instancia de nube sin GPU o nodos CPU del POD: hindcast pesado y preparación de datasets (ERA5, SAAG-WRF desde NCAR vía OSDF —la copia `s3://saag-wrf` del registro de AWS no existe—, Sentinel-2; ver `entrenamiento/README.md`). Solo resultados vuelven al repo.
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

## Ramas y registro de cambios

- Una sola rama de trabajo: `main`. Todo cambio se sube ahí (`git pull --rebase` antes, porque los bots commitean varias veces por hora). Si una tarea larga necesita rama propia, se fusiona en `main` y se borra apenas termina; ningún workflow escucha ramas distintas de `main`.
- `datos-en-vivo` no es rama de trabajo: la reescribe `envivo.yml` cada 10 min con los datos de la pestaña En vivo. No tocarla.
- Cada cambio visible para Pancho (pestaña, capa, workflow, conector) se anota en `CAMBIOS.md` en el mismo commit: fecha, qué cambió y dónde verlo. Los commits automáticos de los bots no se anotan.
