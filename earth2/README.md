# Earth-2 en este repo

El botón "Comenzar en GitHub" de la página de NVIDIA lleva a **Earth2Studio** (github.com/NVIDIA/earth2studio, Apache 2.0). No copiamos su código: se instala como dependencia (`pip install earth2studio`, versión 0.19.0 al 15-oct-2026) y se usa desde aquí. Los pesos de los modelos viven en Hugging Face (huggingface.co/nvidia) y se descargan solos la primera vez.

## Qué nos sirve ya, sin GPU (conectores de datos)

Earth2Studio trae listos los mismos conectores que escribimos a mano, con caché y descarga asíncrona:

| Nuestro script | Conector Earth2Studio | Nota |
| --- | --- | --- |
| `verificacion/fetch_aifs.py` | `earth2studio.data.AIFS_FX`, `IFS_FX`, `AIFS_ENS_FX` | `source="aws"` por defecto, igual que nosotros |
| GFS por bytes | `earth2studio.data.GFS_FX` | |
| METAR Iowa (`historico/metar_historico.py`) | `earth2studio.data.IEM_ASOS` | la misma fuente |
| ERA5 para entrenar | `earth2studio.data.ARCO_ERA5`, `NCAR_ERA5` | |
| GOES-19 cada 10 min y rayos | `earth2studio.data.GOES`, `GOESGLM` | para el 13-oct y el nowcasting |

`earth2/fetch_e2s.py` es el reemplazo de `fetch_aifs.py` sobre estos conectores: mismas estaciones, misma salida CSV, para que `verify.py` no cambie.

## Qué nos sirve con GPU (fase de entrenamiento e inferencia, L40S)

- `earth2studio.models.px.AIFS` / `AIFS2`: correr AIFS nosotros mismos (extra `aifs`: anemoi, flash-attn).
- `earth2studio.models.px.StormScopeGOES`: nowcaster de 0–6 h sobre imágenes GOES a 3 km cada 10 min. Está entrenado para EE.UU. (grilla HRRR); es el punto de partida para el nowcaster chileno, no el producto final.
- `earth2studio.models.dx.CorrDiff`: downscaling. Los pesos públicos son de Taiwán (licencia no comercial) → CorrDiff-Chile se entrena con PhysicsNeMo (`examples/weather/corrdiff`) y se carga aquí.

## Instalar

    pip install earth2studio            # datos, sin GPU (trae torch CPU; ~2 GB)
    pip install "earth2studio[aifs]"    # para correr AIFS en GPU
