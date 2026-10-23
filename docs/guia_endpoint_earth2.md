# Guía: conectar un endpoint de Earth-2

Para quien tenga acceso a un endpoint de Earth-2 (una función en NVIDIA Cloud Functions, un NIM o un servidor propio) y quiera que su pronóstico se verifique en público junto a AIFS, IFS y GFS.

**Qué modelo correr.** Uno global: cubre todo el planeta y sirve en Chile tal como viene. En una L40S (48 GB) caben AIFS y FourCastNet v2 (SFNO), que piden unos 40 GB según su ficha en Earth2Studio 0.19; FourCastNet 3 (FCN3) pide unos 80 GB y no cabe en una sola L40S. `earth2/correr_pod.py` ya corre AIFS o SFNO desde el análisis de IFS, recorta Chile y deja el CSV por aeródromo: sirve como cuerpo de la función. CorrDiff no sirve todavía: los modelos ya entrenados que publica NVIDIA son de Estados Unidos (y de Taiwán, con licencia no comercial) y no saben nada de Chile. CorrDiff-Chile hay que entrenarlo primero (ver al final).

## Qué hace hoy el sitio

Cuatro veces al día, `.github/workflows/verificacion.yml` baja la última corrida de AIFS, IFS y GFS. Extrae la temperatura a 2 m y el viento a 10 m en los 21 aeródromos de `historico/estaciones.csv` y los compara con lo que miden (METAR). El resultado se publica en https://panchodigevo.github.io/earth2-chile-verificacion/.

Un modelo nuevo solo tiene que entregar sus valores en esos mismos aeródromos. Desde ese momento se verifica igual que los otros, sin cambiar nada más.

## Dónde se conecta

| Pieza | Qué hace | Estado |
|---|---|---|
| `earth2/endpoint.py` | Pide el pronóstico al endpoint, lo lleva a los aeródromos y escribe `verificacion/data/puntos_<MODELO>_<corrida>.csv` | Listo, salvo la función `pedir_pronostico()` |
| Paso "Earth-2" en `verificacion.yml` | Corre `endpoint.py` cuatro veces al día, antes de verificar | Listo; se omite si no hay secreto |
| `verificacion/verify.py` | Lee cualquier `data/puntos_*.csv` y lo verifica como un modelo más | Listo |

## Pasos

1. **Guardar la dirección y la clave como secretos del repo**, nunca en el código ni por chat, porque el repo es público. Lo hace un administrador en GitHub → *Settings → Secrets and variables → Actions*:
   - secreto `EARTH2_URL`: la dirección del endpoint;
   - secreto `EARTH2_API_KEY`: la clave;
   - variable `EARTH2_MODELO`: el nombre corto que verá el público, por ejemplo `FCN3` o `E2`.
2. **Escribir `pedir_pronostico()`** en `earth2/endpoint.py`. Recibe la hora de la corrida y los plazos (0 a 48 h) y debe devolver un `xarray.Dataset` con `t2m` (K), `u10m` y `v10m` (m/s) sobre `lead_time`, `lat` y `lon`, que es el formato estándar de Earth2Studio. Si el endpoint responde un netCDF o Zarr con ese formato, basta abrirlo.
3. **Probar sin esperar al proceso automático.** Con un archivo de salida ya descargado:
   `python earth2/endpoint.py --archivo salida.nc --corrida 2026-10-20T00`
   Esto escribe el CSV con los valores en los aeródromos. Revísalo antes de subir nada.
4. **Lanzar el proceso en GitHub** (Actions → verificacion-diaria → *Run workflow*) y revisar en el registro el paso "Earth-2". Si falla, el resto del sitio sigue funcionando: ese paso no detiene la verificación.
5. **Ver el modelo en el sitio.** Hoy las tablas y el selector del sitio muestran AIFS, IFS y GFS (`MODELOS` y `ORDEN` en `verificacion/render_site.py`). Para que el modelo nuevo aparezca como cuarta opción hay que agregarlo ahí. Conviene hacerlo cuando ya tenga unos días de datos, para no publicar cifras con pocas comparaciones.

## Cómo se llama a la función (contrato con NVCF)

- `POST` a `EARTH2_URL` con `Authorization: Bearer <EARTH2_API_KEY>` y el cuerpo `{"corrida": "2026-10-21T00", "horas": 48}`.
- La corrida tarda ~60 s y el gateway de NVCF corta las conexiones largas. Por eso la primera llamada lanza la corrida y responde `{"estado": "lanzada"}`; `earth2/endpoint.py` repite la misma llamada cada 20 s (hasta 15 min) hasta que la respuesta es el netCDF.
- También entiende las respuestas propias de NVCF: `202` con `NVCF-REQID` (consulta `/v2/nvcf/pexec/status/<id>`) y un resultado grande entregado como enlace (`Location` o `"url"` en el JSON).
- Probado con un servidor que imita ese comportamiento; falta la primera llamada real.

## Qué condición inicial usar

Para que la comparación sea justa, el endpoint debería partir de la misma hora de corrida que los otros modelos (00, 06, 12 o 18 UTC), y de una condición inicial abierta y reproducible: el análisis de GFS o el de IFS. Earth2Studio trae los conectores (`GFS`, `IFS`) para armarla.

## Y el downscaling a 4 km

CorrDiff-Chile, el zoom de 25 a 4 km, es otro caso: no reemplaza a un modelo global, lo afina. Todavía no existe: hay que entrenarlo con PhysicsNeMo (`examples/weather/corrdiff`) usando SAAG-WRF a 4 km como objetivo y ERA5 como entrada (tareas 6 y 7 de `TAREAS.md`). Cuando exista, el mismo esquema sirve: se escribe `puntos_CORRDIFF_<corrida>.csv` con los valores en los aeródromos y se verifica contra el global del que partió. Ahí está la prueba central del proyecto.

## Reglas

- El repo es público: nada de claves, datos con licencia restringida ni información de clientes.
- Lenguaje de "aviso" o "indicador", nunca "alerta": las alertas oficiales son de la DMC y SENAPRED.
- Commits en español. Antes de subir: `git pull --rebase`, porque hay procesos automáticos que escriben en `main` varias veces por hora.
