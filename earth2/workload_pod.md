# Ficha técnica del workload en el POD (tarea 5)

Para declarar el workload a NVIDIA (NVCF). Solo datos técnicos: nada de cifras de negocio.

## Qué corre

- Modelo global de Earth-2 en una GPU L40S: **AIFS-Single 1.1** (control contra el AIFS que publica ECMWF) y, después, **FourCastNet v2 (SFNO)**. Ambos piden unos 40 GB de memoria de GPU según su ficha en Earth2Studio 0.19, así que caben en una L40S de 48 GB. FourCastNet 3 pide unos 80 GB: no cabe en una sola L40S.
- Condición inicial: análisis de IFS de ECMWF open data en AWS (0,25°). Alcance: 10 días en pasos de 6 h (40 pasos).
- 4 veces al día: corridas de 00, 06, 12 y 18 UTC.
- Script: `earth2/correr_pod.py`; contenedor: `earth2/pod/Dockerfile`. Cada corrida escribe su ficha en `earth2/workload/<MODELO>_<corrida>.json`.

## Cómo llegan los resultados al sitio

Dos caminos; el primero es el que está armando Guillermo:
1. **Función de NVCF**: corre `pronosticar()` y devuelve el recorte de Chile (netCDF, unos 2 a 10 MB). GitHub Actions lo baja con `earth2/endpoint.py` (secretos `EARTH2_URL`, `EARTH2_API_KEY`, variable `EARTH2_MODELO`).
2. **Trabajo programado en el POD**: corre `correr_pod.py` y sube a `main` solo el CSV por aeródromo (`verificacion/data/puntos_<MODELO>_<corrida>.csv`) y la ficha JSON, con un token de despliegue del repo.

## Medidas (se llenan con las primeras corridas reales)

| Medida | AIFS | SFNO |
|---|---|---|
| GPUs por corrida | 1 L40S | 1 L40S |
| Minutos por corrida (10 días) | por medir | por medir |
| Memoria GPU máxima (GB) | por medir (ficha: ~40) | por medir (ficha: ~40) |
| Horas-GPU por día (4 corridas) | por medir | por medir |
| Tráfico de red por corrida (GB) | por medir | por medir |
| Recorte de Chile por corrida (MB) | por medir | por medir |
| Pesos del modelo en disco (GB) | por medir | por medir |

## Control (AIFS)

Con `--control`, el script compara en los mismos aeródromos y plazos con el AIFS que publica ECMWF. No se espera igualdad exacta: ECMWF inicializa con su análisis a resolución nativa y puede usar otra versión del checkpoint; aquí partimos del análisis publicado a 0,25°. A plazo 0 deben coincidir casi del todo (es el mismo análisis); a 24 y 48 h se espera una diferencia chica frente al error contra las estaciones. Si no es así, se explica antes de seguir.
