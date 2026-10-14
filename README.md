# Earth-2 Chile · verificación y hindcast

Repositorio del piloto **Earth-2 Chile** (Digevo): inteligencia climática con IA sobre Chile a escala kilométrica.

- `verificacion/` — pipeline diario: baja el pronóstico de IA de ECMWF (AIFS, 0,25°, CC-BY 4.0), lo compara con observaciones horarias de 25 aeródromos chilenos (METAR, reportados por la DMC) y publica el error por plazo y por estación. Corre 4 veces al día en GitHub Actions.
- `site/` — página pública generada por el pipeline (GitHub Pages).
- `hindcast/` — eventos de 2026: lo que se veía antes (lluvia), la superficie de ese momento (incendios, pendiente, suelo) y lo que pasó (catálogos).

Primer resultado (14-oct-2026, 77 pares): error medio de temperatura 1,2–1,5 °C a 0–24 h; sesgo frío de –3 °C en Iquique, Arica y Balmaceda, donde la grilla de 25 km mezcla mar y tierra. Esa es la brecha que el downscaling a 2–4 km (CorrDiff-Chile) debe cerrar.

## Correr local
    python -m venv .venv && . .venv/bin/activate
    pip install -r verificacion/requirements.txt
    cd verificacion && python fetch_metar.py && python fetch_aifs.py && python verify.py

Licencias de datos: ECMWF open data CC-BY 4.0 (atribuir a ECMWF); NOAA/AWC METAR dominio público. Aviso: información de apoyo a la decisión; no sustituye las alertas oficiales de la DMC ni de SENAPRED.
