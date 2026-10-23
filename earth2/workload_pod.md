# Ficha técnica del workload en el POD (tarea 5)

Para declarar el workload a NVIDIA (NVCF). Solo datos técnicos: nada de cifras de negocio.

## Qué corre

- Modelo global de Earth-2 en una GPU L40S: **FourCastNet 3 (FCN3)**, desplegado por Guillermo en NVCF y cargado en 48 GB (su ficha en Earth2Studio dice ~80 GB; falta medir la inferencia a 10 días); **AIFS-Single 1.1** como control contra el AIFS que publica ECMWF; **SFNO** como alternativa (~40 GB).
- El modelo corre dentro del contenedor: la entrada global (~72 canales, ~285 MB) supera el límite de 270 MB del gateway de NVCF, así que no puede viajar por la red; la petición es una fecha y la respuesta, el recorte de Chile, ~3 MB.
- La función responde en dos tiempos: la corrida tarda ~60 s y el gateway corta conexiones largas, así que la primera llamada la lanza (`{"estado": "lanzada"}`) y se vuelve a llamar cada 20 s hasta recibir el netCDF.
- Condición inicial: análisis de IFS de ECMWF open data en AWS (0,25°). Alcance: 10 días en pasos de 6 h (40 pasos).
- 4 veces al día: corridas de 00, 06, 12 y 18 UTC.
- Script: `earth2/correr_pod.py`; contenedor: `earth2/pod/Dockerfile`. Cada corrida escribe su ficha en `earth2/workload/<MODELO>_<corrida>.json`.

## Cómo llegan los resultados al sitio

Dos caminos; el primero es el que está armando Guillermo:
1. **Función de NVCF**: corre `pronosticar()` y devuelve el recorte de Chile (netCDF, unos 2 a 10 MB). GitHub Actions lo baja con `earth2/endpoint.py` (secretos `EARTH2_URL`, `EARTH2_API_KEY`, variable `EARTH2_MODELO`).
2. **Trabajo programado en el POD**: corre `correr_pod.py` y sube a `main` solo el CSV por aeródromo (`verificacion/data/puntos_<MODELO>_<corrida>.csv`) y la ficha JSON, con un token de despliegue del repo.

## Medidas (se llenan con las primeras corridas reales)

| Medida | FCN3 | AIFS | SFNO |
|---|---|---|---|
| GPUs por corrida | 1 L40S | 1 L40S | 1 L40S |
| Minutos por corrida (10 días) | ~1 (Guillermo, por confirmar) | por medir | por medir |
| Memoria GPU máxima (GB) | carga en 48 (ficha: ~80) | por medir (ficha: ~40) | por medir (ficha: ~40) |
| Horas-GPU por día (4 corridas) | por medir | por medir | por medir |
| Tráfico de red por corrida (GB) | por medir | por medir | por medir |
| Respuesta: recorte de Chile (MB) | ~3 | por medir | por medir |
| Pesos del modelo en disco (GB) | por medir | por medir | por medir |

## Control (AIFS)

Con `--control`, el script compara en los mismos aeródromos y plazos con el AIFS que publica ECMWF. No se espera igualdad exacta: ECMWF inicializa con su análisis a resolución nativa y puede usar otra versión del checkpoint; aquí partimos del análisis publicado a 0,25°. A plazo 0 no es cero: la prueba sin GPU del 20-oct-2026 (persistencia, corrida 12 UTC) dio 0,59 °C de diferencia media en temperatura (máximo 1,62 °C) y 0,41 m/s en viento entre el análisis de IFS a 0,25° y el plazo 0 del AIFS de ECMWF, porque AIFS pasa el análisis por su propia grilla y vuelve a 0,25°, y en terreno abrupto eso mueve el valor. Ese es el piso. Con AIFS en el POD, a 24 y 48 h se espera una diferencia del orden de ese piso, chica frente al error contra las estaciones (1,5 °C de media en 2026). Si es mucho mayor, se explica antes de seguir.
