# Dataset de entrenamiento de CorrDiff-Chile (tarea 6)

CorrDiff aprende a pasar de un mapa de 25 km a uno de 4 km viendo pares de la misma hora: **entrada** ERA5 (25 km) y **respuesta** SAAG-WRF (4 km). NVIDIA entrega la receta (PhysicsNeMo, `examples/weather/corrdiff`); el dataset chileno lo armamos aquí.

## Fuentes

| Pieza | Fuente | Acceso | Licencia |
|---|---|---|---|
| Objetivo 4 km | SAAG-WRF, NCAR RDA d616000 (Liu et al. 2025), 2001-2022, horario | HTTPS vía OSDF: `https://osdf-director.osg-htc.org/ncar/rda/d616000/hist2D/YYYYMM/wrf2d_d01_YYYY-MM-DD_HH0000.nc` | CC BY 4.0; citar con el formato de NCAR |
| Entrada 25 km | ERA5 de ECMWF, copia ARCO de Google | Zarr público `gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3` | CC BY 4.0 (atribuir ECMWF/Copernicus) |
| Campos fijos | Relieve y máscara tierra-mar de SAAG (`INVARIANT/wrfconstants_SAAG.nc`) | igual que SAAG | igual que SAAG |

**La copia de SAAG en AWS no existe.** El registro de AWS nombra `s3://saag-wrf`, pero el bucket responde `NoSuchBucket` y la ficha oficial de NCAR deja vacío su ARN. Los datos se leen desde NCAR.

## Qué se encontró (23-oct-2026)

- **Cada hora de SAAG pesa ~736 MB** (toda Sudamérica, 207 variables). Bajar 10 años enteros serían ~64 TB. Pero los archivos son HDF5 en trozos de 1.014 × 736 puntos: se lee solo lo de Chile y solo las variables útiles, **~27 MB por hora** para 8 variables (`explorar_saag.py`, `saag-explorar.yml`).
- **Grilla:** Lambert conforme de 4 km, 2.027 × 1.471 puntos. Chile, de Arica (18,4° S) al Cabo de Hornos (56° S), cabe en filas 27-1146 y columnas 267-618: **1.120 × 352 puntos**, múltiplos de 32 como pide la red. Arica, Las Condes, Punta Arenas y Puerto Williams quedan a 1-3 km de un punto de la grilla. **La base antártica queda fuera de SAAG.**
- **ERA5 de altura es caro:** en la copia de Google cada variable de altura trae los 37 niveles juntos en un trozo global de ~80 MB por hora; una de superficie pesa ~2-3 MB. Por eso la versión 0 usa solo **superficie**: t2m, u10m, v10m, u100m, v100m, msl, tcwv. Además son las que entregan AIFS y FCN3, los modelos que alimentarán a CorrDiff-Chile al pronosticar (FCN3 no trae lluvia; AIFS trae tcw, casi igual a tcwv).
- **Muestra cargada con el cargador real:** 6 horas del 1-ene-2018 armadas en Actions (`dataset-muestra.yml`) y leídas con `_ZarrDataset` de PhysicsNeMo v1.3.0 (`datasets/cwb.py`): objetivo `(8, 1120, 352)`, entrada `(9, 1120, 352)`, sin NaN, normalizado con media ~0 y desviación ~1. Ocupa ~15 MB por muestra en disco.

## Canales

- **Salida (8):** temperatura a 2 m, viento u y v a 10 m, viento máximo a 10 m (rachas), lluvia de la última hora, nieve de la última hora, humedad específica a 2 m, radiación solar.
- **Entrada (9):** las 7 de ERA5 de superficie interpoladas bilinealmente a la grilla de SAAG, más relieve y máscara tierra-mar a 4 km.

## Plan del dataset completo

| | Valor |
|---|---|
| Años | 2012-2021, cada 2 horas (43.800 muestras; el README de CorrDiff recomienda 50.000 o más) |
| Prueba | 2021 completo (4.380 muestras), nunca en el entrenamiento; los eventos de 2026 tampoco (SAAG termina en 2022) |
| Descarga | ~1,2 TB de SAAG + ~0,8 TB de ERA5 |
| Disco final | ~0,65 TB en Zarr |
| Tiempo | ~20 s por muestra y proceso; con 32 procesos, ~18 horas |
| Dónde | nodos CPU del POD (o una instancia de nube sin GPU), nunca el Mac |

Comando: `python entrenamiento/preparar_dataset.py --desde 2012-01-01T00 --hasta 2021-12-31T22 --cada 2 --salida /datos/corrdiff_chile.zarr --procesos 32`

## Para entrenar (tarea 7)

- Cargador `cwb` del ejemplo corrdiff: `++dataset.data_path=/datos/corrdiff_chile.zarr ++dataset.img_shape_x=1120 ++dataset.img_shape_y=352 ++dataset.ds_factor=1`. Con `ds_factor` mayor que 1 el cargador degrada el objetivo.
- El cargador `cwb` separa entrenamiento y prueba por el año 2021, que está fijo en su código: calza con este plan.
- Pendientes conocidos: la lluvia tiene una distribución muy asimétrica y la normalización simple (media y desviación) puede no bastar, así que conviene probar una transformación logarítmica; la red `normal` atiende a resolución 28, pensada para 448 × 448, y hay que revisar su ajuste para 1.120 × 352; los parches de la difusión deben ser cuadrados y múltiplos de 32.
- Se entrena en las GPUs L40S del POD, en horas valle, con una corrida corta previa en la zona central para medir horas-GPU (tarea 7).
