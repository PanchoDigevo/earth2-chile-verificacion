# Earth-2 Chile · verificación y hindcast

Repositorio del piloto **Earth-2 Chile** (Digevo): inteligencia climática con IA sobre Chile a escala kilométrica.

- `verificacion/` — pipeline diario: baja tres pronósticos globales a 0,25° (AIFS, la IA de ECMWF; IFS, el modelo físico de ECMWF, ambos CC-BY 4.0; y GFS de NOAA, dominio público), los compara con observaciones horarias de 25 aeródromos chilenos (METAR, reportados por la DMC) y publica el error por plazo, por estación y por modelo: la IA frente al modelo físico. Corre 4 veces al día en GitHub Actions.
- `site/` — página pública generada por el pipeline (GitHub Pages).
- `hindcast/` — eventos de 2026: lo que se veía antes (lluvia), la superficie de ese momento (incendios, pendiente, suelo) y lo que pasó (catálogos).

Primer resultado (14-oct-2026, 77 pares): error medio de temperatura 1,2–1,5 °C a 0–24 h; sesgo frío de –3 °C en Iquique, Arica y Balmaceda, donde la grilla de 25 km mezcla mar y tierra. Esa es la brecha que el downscaling a 2–4 km (CorrDiff-Chile) debe cerrar.

## Correr local
    python -m venv .venv && . .venv/bin/activate
    pip install -r verificacion/requirements.txt
    cd verificacion && python fetch_metar.py && python fetch_aifs.py && python fetch_ifs.py && python fetch_gfs.py && python verify.py

Cada `fetch_*.py` acepta una corrida explícita (`python fetch_gfs.py 2026-10-14 12`). Los pronósticos en las estaciones quedan en `data/pronostico_puntos.csv`, los pares en `data/verif_puntos.csv` (columna `modelo`) y el resumen en `data/verif_resumen.csv`.

Licencias de datos: ECMWF open data CC-BY 4.0 (atribuir a ECMWF); NOAA GFS y NOAA/AWC METAR dominio público. Aviso: información de apoyo a la decisión; no sustituye las alertas oficiales de la DMC ni de SENAPRED.

## Conectar un endpoint de Earth-2

Para verificar en público un modelo propio (por ejemplo un endpoint de NVIDIA Earth-2) junto a AIFS, IFS y GFS, ver [docs/guia_endpoint_earth2.md](docs/guia_endpoint_earth2.md). El conector está en `earth2/endpoint.py` y se activa al configurar el secreto `EARTH2_URL`.
