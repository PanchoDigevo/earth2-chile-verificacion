# Verificación retroactiva (histórico 2025–2026)

En vez de esperar a que pasen los días, miramos hacia atrás: qué decían los modelos globales 24, 48 y 72 h antes, y qué pasó después en los aeródromos de Chile. Todo corre en GitHub Actions (`.github/workflows/historico.yml`); el Mac solo lanza y revisa.

## Pasos

1. **Pronósticos históricos por puntos** (`extraer_puntos.py`). Para cada corrida de 00 y 12 UTC y cada plazo (24, 48, 72 h), baja por rango de bytes solo los dos campos que importan (temperatura a 2 m y precipitación acumulada) y guarda el valor del punto de grilla más cercano a cada estación de `estaciones.csv`. Fuentes: AIFS e IFS desde el archivo de ECMWF en AWS (`ecmwf-forecasts`, CC-BY 4.0; AIFS existe desde feb-2025), GFS desde `noaa-gfs-bdp-pds` (dominio público). No se guardan GRIB: un mes de un modelo son unos 300 KB de CSV.
2. **Observaciones históricas** (`metar_historico.py`). METAR horario de los aeródromos desde el archivo ASOS de Iowa State. Los METAR chilenos no traen milímetros de lluvia (`p01i` viene en cero), pero sí el tiempo presente (RA, DZ, SH, TS…): se usa como "llovió sí/no".
3. **Consolidar** (`consolidar.py`): junta los CSV mensuales en `data/pronosticos.csv.gz` sin duplicar.
4. **Analizar** (`analizar.py`): pares de temperatura, lluvia sí/no, los tres eventos de 2026 (`hindcast/eventos/eventos_2026.csv`), error por plazo, mes y estación, y la **corrección por estación** aprendida solo con 2025 y evaluada solo en 2026. Resultados en `data/resultados/*.csv` y la página `site/historico.html` (`render_historico.py`).

## Cómo lanzarlo

En GitHub → Actions → `historico` → *Run workflow*, con el primer y último mes (`2025-01` a `2026-10`) y los modelos. Cada mes y modelo es un job independiente (matriz); al final un job consolida, analiza y publica. Para rehacer solo el análisis con lo ya guardado: `solo_analizar = true`.

Prueba local pequeña (venv fuera de OneDrive, `~/e2venv`):

    python historico/extraer_puntos.py --modelo gfs --desde 2026-10-08 --hasta 2026-10-08
    python historico/metar_historico.py 2026
    python historico/consolidar.py && python historico/analizar.py
