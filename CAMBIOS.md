# Cambios

Lo hecho, en orden inverso y en simple. Los commits automáticos (verificación, escenarios, océano, seguimiento) no aparecen aquí; para el detalle, `git log --no-merges`.

Sitio: https://panchodigevo.github.io/earth2-chile-verificacion/

## 23-oct-2026

- **FCN3 listo para aparecer en el sitio:** en Tu zona, "Últimos días" suma una tarjeta por cada modelo de Earth-2 corrido por nosotros (FCN3, AIFS-POD, SFNO) apenas tenga pares, con su origen y la marca "pocas todavía" bajo 30 comparaciones. Las tablas históricas no cambian. Botón de prueba en Actions: `earth2-endpoint-prueba` llama a la función de NVCF y muestra los valores, sin subir nada.
- **FCN3 en el POD:** Guillermo desplegó FourCastNet 3 en NVCF y cargó en una L40S de 48 GB. `correr_pod.py` lo corre (`--modelo fcn3`, ahora por defecto) y el Dockerfile instala makani y torch-harmonics desde GitHub sin dependencias, con un candado para no reemplazar el torch de PhysicsNeMo. Se corrige lo que decía antes: FCN3 sí cabe.
- **Conector Earth-2 listo para la función de NVCF de Guillermo** (`earth2/endpoint.py`): manda la corrida, recibe `{"estado": "lanzada"}` y vuelve a preguntar cada 20 s hasta que llega el netCDF (tope 15 min). El paso del workflow tiene tope de 16 min y el entorno ya abre netCDF en memoria (`h5netcdf`, `h5py`, `scipy`). Se activa al cargar los secretos.

## 20-oct-2026

- **Tarea 5 lista para el POD** (`earth2/correr_pod.py`, `earth2/pod/Dockerfile`, `earth2/workload_pod.md`): corre AIFS o FourCastNet v2 (SFNO) en una L40S, recorta Chile, deja el CSV por aeródromo y la ficha técnica para NVIDIA, y se compara con el AIFS de ECMWF. Probado sin GPU con persistencia (`earth2-pod-prueba.yml`). FourCastNet 3 pide ~80 GB y no cabe en una L40S. `endpoint.py` ya no inventa valores para aeródromos fuera del recorte.
- **Qué corre hoy y qué hay que entrenar, dicho claro:** bloque "En qué etapa estamos" en la portada y en Método (funciona hoy / siguiente: FourCastNet / por entrenar: CorrDiff-Chile). La narrativa ya no dice "lo entrenamos" como si el zoom a 4 km existiera: NVIDIA solo publica CorrDiff para EE.UU. y Taiwán, y el de Chile hay que entrenarlo. Mismo ajuste en README, guía del endpoint, `earth2/README.md` y CLAUDE.md.
- **Faena minera Collahuasi en Escenarios** (`escenarios/faenas.csv`): 20°59′S 68°38′W, 4.400 m, comuna de Pica, primero en la pestaña. Con los 50 escenarios de AIFS-ENS, la probabilidad diaria de viento fuerte (≥ 50 km/h), nevada (≥ 2 cm), chubasco convectivo (indicio de tormenta) y frío extremo (≤ −10 °C de madrugada, llevado a 4.400 m). Se nombra por el lugar, que es público (decisión de Pancho).
- **Corrección en Escenarios de incendio:** con la corrida de 12 UTC se tomaba la hora de las 03 de Chile en vez de media tarde, así que la regla 30-30-30 casi nunca podía cumplirse. Ahora se toman siempre las 18 UTC. La lluvia diaria ya no depende de adivinar la unidad.

## 20-oct-2026

- **La lluvia, en milímetros, en la verificación diaria** (`verificacion/lluvia.py`, lo llama `verify.py` 4 veces al día): la lluvia de 24 h que pronosticaron AIFS, IFS y GFS el día anterior se compara con los milímetros del pluviómetro de la DMC en cada aeródromo (SYNOP de `estaciones/`), desde el 1-oct. En 23 aeródromos la estación está en el mismo aeródromo; Tobalaba usa Quinta Normal (12,6 km), y Pucón y Base Frei no tienen pluviómetro cerca. Un día cuenta como lluvioso desde 1 mm: días con lluvia avisados, falsas alarmas, aciertos de sí o no y error medio en mm. Se ve en Resumen («Y la lluvia, en milímetros»), en Tu zona (ficha de cada aeródromo con sus últimos días y tabla «La lluvia en cada aeródromo») y se explica en Método («Lluvia en milímetros en cada aeródromo»). Preliminar hasta juntar 30 días. Comparaciones en `verificacion/data/verif_lluvia.csv`.
- **Pluviómetro de Aguas Andinas (La Florida) fuera de la comparación:** entre el 6 y el 7-oct midió 11 mm cuando el resto del valle midió de 45 a 75 mm. Lo siguen usando el seguimiento de las quebradas y la pestaña En vivo; conviene revisarlo.

## 19-oct-2026

- **Lluvia medida en estaciones** (`estaciones/`, `estaciones.yml` cada hora): lluvia horaria y temperatura de las 141 estaciones SYNOP de Chile (casi todas automáticas de la DMC, de Visviri a Diego Ramírez, Isla de Pascua y Juan Fernández; mensajes de la OMM sin clave), desde el 1-oct, un CSV por mes en `estaciones/datos/synop/`. Se compara con cada bloque de 6 h del seguimiento de pronósticos en `estaciones/VERIFICACION_LLUVIA.md`. En la pestaña En vivo: tarjeta con lo medido en las estaciones más cercanas a Apoquindo (la primera es Aguas Andinas, La Florida, a 16 km), columna «Medido» en la tabla de pronósticos y temperatura en El Colorado (2.750 m) frente a la isoterma 0 °C de GFS. Explicado en Método («Lluvia medida en estaciones»).
- **API de la DMC lista** (`estaciones/dmc.py`): se activa al cargar los secretos `DMC_USUARIO` y `DMC_TOKEN`; sin ellos no hace nada. **La red en tiempo real de la DGA no se puede leer de forma automática:** sus tablas piden captcha. Las estaciones de interés (Quebrada de Ramón, Quebrada de Macul, Antupirén, Cerro Calán, Valle Echaurren Norte y otras) quedan anotadas en `estaciones/catalogo.csv` para cuando la DGA dé acceso.
- **En vivo más confiable:** GitHub se saltaba la actualización cada 10 min (en 1,5 h no corrió ninguna). Ahora cada corrida actualiza cada 5 min durante casi 6 h, y la página avisa en ámbar cuando los datos tienen más de 20 min de atraso; el total de rayos cuenta solo los de los últimos 90 min.
- **Todo consolidado en `main`.** Se fusionó y borró la rama `capas-estandar`; los workflows de océano, escenarios y Earth2Studio ahora escuchan `main`.
- **Pestaña En vivo** (`envivo.html`): rayos GOES-19 de los últimos 90 min, METAR de Tobalaba, Pudahuel, El Bosque y Viña, y la lluvia que espera cada modelo para Apoquindo. Se actualiza cada 10 min (`envivo.yml`, datos en la rama `datos-en-vivo`).
- **Seguimiento horario de pronósticos** (`seguimiento.yml`): guarda cada corrida nueva de AIFS, IFS y GFS para las quebradas quemadas, Tobalaba y Pudahuel en `hindcast/seguimiento/pronosticos.csv`, y el registro previo del evento del 20-oct en `hindcast/eventos/prerregistro/2026-10-20-rm/`.
- **Aviso de alerta oficial** (`site/aviso_oficial.json`): la Alerta Amarilla de SENAPRED para la RM, arriba de Resumen, Tu zona y Quebradas. Se apaga sola el 22-oct a las 09:00.
- **Conector para un endpoint de Earth-2** (`earth2/endpoint.py`, guía en `docs/guia_endpoint_earth2.md`): se activa al cargar los secretos `EARTH2_URL` y `EARTH2_API_KEY`. Falta escribir `pedir_pronostico()`.
- **Earth2Studio probado en Actions:** extrae por estación lo mismo que nuestro proceso y lee GOES y GLM del 13-oct (2.640 rayos en Santiago). El workflow diario sigue con `fetch_aifs.py`.
- **Escenarios de incendio** (pestaña Escenarios): AIFS-ENS de 50 miembros a 15 días; descargas en paralelo y tope de 3 h.
- **Viento verificado 2025-2026:** velocidad, dirección, ráfagas y episodios, con corrección fija y móvil.
- **El Niño:** qué significan los valores, qué ha implicado para Chile y qué se ha puesto en marcha, con fuente y separado de los datos.
- Guillermo Barraza (`guillebarrazav`) invitado con permiso de escritura.

## 16-oct-2026

- **Rediseño UX** según el brief (`docs/brief_sitio.md`) y una auditoría independiente: pestañas Resumen, Tu zona, Eventos 2026, Quebradas y Método.
- **Lo que está cambiando:** mar frente a la costa (OISST), índices Niño (CPC) y aeródromos en deriva (`oceano.yml`, diario).
- Viento en el histórico y en cada evento; incendios de enero de 2026 en el catálogo.

## 15-oct-2026

- **Visor de quebradas de Santiago oriente:** cicatrices de incendio (Sentinel-2), pendiente, cuencas, cauces, remociones y el indicador USGS por cuenca, 4 veces al día.
- Cuarto evento del histórico: tormenta del 13-oct-2026 en Santiago.
- Portada con mapa y tabla por estación desde el histórico 2025-2026.

## 14-oct-2026

- Repo público, Pages y verificación diaria de AIFS, IFS y GFS contra METAR en 21 aeródromos.
- Verificación retroactiva 2025-2026 y corrección por estación aprendida en 2025.
