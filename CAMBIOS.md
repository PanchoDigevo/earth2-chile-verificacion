# Cambios

Lo hecho, en orden inverso y en simple. Los commits automáticos (verificación, escenarios, océano, seguimiento) no aparecen aquí; para el detalle, `git log --no-merges`.

Sitio: https://panchodigevo.github.io/earth2-chile-verificacion/

## 19-oct-2026

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
