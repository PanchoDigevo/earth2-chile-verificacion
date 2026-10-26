# Traza Urbana (trazaurbana.cl): qué es, qué usa y qué copiar

Revisado el 26-oct-2026. Sitio de Gerardo Ureta (Ph.D., Universidad Finis Terrae): "laboratorio personal" de analítica urbana. Nació el 8-oct-2026, el día del aluvión de Las Condes, y en dos semanas salió en TVN, Mega, T13, LUN, La Tercera, CNN, Cooperativa. Es la referencia pública que hoy tiene la gente para "¿vivo cerca de una quebrada?".

## Qué es (y qué no es)

- **Mapa de exposición**: las 146 quebradas del PRMS en la RM y las zonas de quebrada, remoción en masa e inundación que declaran los planes reguladores de las otras regiones. Cruzado con el catastro del SII (propiedades por destino), el Censo 2024 (personas por manzana), colegios (MINEDUC) y centros de salud (DEIS). La cifra bandera: 18.267 viviendas y unas 61.000 personas a menos de 100 m de una quebrada del PRMS.
- **Tres reconstrucciones de eventos** (aluvión 8-oct, tormenta 13-oct, sistema frontal 20-21-oct): lluvia del GOES-19 corregida con los pluviómetros de la DMC, rayos del GLM, y un modelo hidráulico del agua sobre la red real de calles (OSM) con el relieve (GEDTM30 / Copernicus GLO-30). Para el aluvión, solo dirección de flujo por el relieve ("no es un modelo hidráulico").
- **Lo que no es**: no pronostica, no monitorea, no emite avisos. Lo repite en cada bloque: "reconstrucción probable, no oficial", "mide cercanía, no riesgo", "exposición no es daño", "no informa la situación actual". Todo es retrospectivo y estático.

## ¿Usa nuestros modelos?

**No.** No usa AIFS, IFS, GFS, ningún modelo de pronóstico ni nada de Earth-2. Tampoco hay nowcasting ni datos en vivo. Comparte con nosotros dos fuentes crudas: los rayos del GOES-19 (GLM) y las estaciones de la DMC. Técnicamente es un solo HTML de ~15 MB con los datos embebidos (sin API ni servidor), mapa tipo MapLibre con imagen satelital de Esri, detrás de Cloudflare.

**Son complementarios, no competencia.** Él responde "dónde cae el agua y quién vive ahí" (calles, casas, personas) para eventos que ya pasaron; nosotros respondemos "qué viene y qué está pasando ahora" (pronóstico a 72 h, rayos en vivo, isoterma, quebradas contra umbrales). El dato que a él le falta es el nuestro, y viceversa: su modelo de calles necesita una lluvia prevista para pasar de reconstrucción a anticipación. Es un candidato natural para colaborar (y ya enlaza al mismo Senapred/DMC que nosotros).

## Prácticas de UI/UX que vale la pena copiar

1. **Una sola pregunta arriba del mapa: "¿Vives cerca de una quebrada?"**, con una caja de dirección y un botón "Usar mi ubicación". La respuesta es una frase con un número: "Esta dirección está a 705 m de la quebrada Grande (O-26, PRMS · Las Condes)", con un medidor de 100 / 200 / 400 m, y recién después "Ver datos de la quebrada". Geocodificación con Nominatim (OSM), gratis.
2. **La verificación es titular, no nota al pie**: "Acierta 12 de los 14 pasos bajo nivel", "con el mismo modelo de la tormenta del 13, sin reajustarlo: una predicción a ciegas". Cada evento tiene las mismas seis secciones: *Qué tan bien calza con lo observado · Quiénes estaban junto al agua · Lo que pasó, hora a hora · Cómo se calculó · Lo que el modelo no explica · Fuentes*.
3. **Honestidad repetida y fechada**: "información pública hasta las 12:50 del 21 de octubre", "exposición no es daño", enlaces a Senapred y la DMC en cada bloque, "la faja de la ordenanza es otra cosa". Un glosario "¿Cómo se leen estas cifras?" bajo cada tabla.
4. **Cada cifra lleva al mapa**: "Ver en el mapa", "Ir a la zona con más agua", "Verlos en el mapa" (colegios, centros de salud). Las tablas de exposición por distancia (≤ 50 m, ≤ 100 m) con botón por celda.
5. **Números con personas, no solo milímetros**: viviendas, personas, mayores de 60, menores de 14, colegios con su matrícula, centros de salud con urgencia. Comparados con la comuna y la región ("26 % frente a 19 % de la RM").
6. **Incertidumbre como alternativas, no como decimales**: botones de escenario ("drenaje de 5 mm/h: la predicción principal · 10 mm/h: la segunda"; "18 mm en una hora · 60 mm en una hora"), y "si el agua hubiese bajado por el ramal norte".
7. **El evento como relato**: control de tiempo "Reproducir el evento" cada 10 o 30 minutos, alternando "lluvia de toda la tarde" y "lluvia y rayos de esos diez minutos"; y un sobrevuelo 3D de 40-70 s por evento, con póster, compartible.
8. **Estado compartible**: la URL guarda zoom y posición (`#14/-33.40/-70.51`), vistas con enlace propio (`?vista=aluvion`), página por evento y por comuna (SEO), botón "Compartir mapa" (WhatsApp, X, LinkedIn, copiar enlace).
9. **Panel con cuatro pestañas** (Resumen · Eventos · Capas · Método) a la izquierda del mapa; en el teléfono, un botón "Panel" que abre una hoja. Capas agrupadas con conteos ("91 zonas · 1.021 km²"), fondo satelital con nombres, 3D, barra de escala, mapa de calor por hexágonos con clases discretas.
10. **Credibilidad a la vista**: cara y credenciales del autor, tira de apariciones en medios con fecha, newsletter, "Contacto" como CTA de negocio. Tema oscuro y titulares con serifa: tono editorial, no de dashboard.

Debilidades que no copiar: 15 MB en una sola página (lento en 4G), exige WebGL, panel muy largo, nada en vivo ni a futuro.

## Qué cambia en nuestro sitio (en este orden)

1. **Respuesta por dirección** en Quebradas y En vivo: "Tu dirección está a X m de la quebrada Y; con lo medido / con lo previsto, nivel Z; hay N rayos encima". Nominatim + nuestras cuencas (ya delimitadas) + el indicador. Es la mitad del valor del sitio de él, y nosotros le sumamos el "ahora" y el "viene".
2. **Plantilla de evento con sus seis secciones**, y "qué tan bien calzó" como titular de cada evento (Requínoa: aviso 35 min antes; quebradas 26-oct: GFS en aviso 32 h antes, celda de rayos encima 40 min antes, pluviómetros del valle en cero).
3. **Cada cifra con "Ver en el mapa"** (comunas con tormenta, cuencas, quebradas).
4. **Escenarios como botones** (hoy ya hay "con lo medido / si cae lo previsto"; extender a "drenaje" y a "ramal").
5. **Compartir**: botones de WhatsApp y copiar enlace con la comuna en la URL (la URL ya guarda la comuna).
6. **Personas, no solo mm**: colegios y centros de salud (MINEDUC y DEIS son abiertos) a menos de 100 m de las quebradas quemadas, y personas por manzana (Censo 2024, INE) para las cuencas con aviso.
7. Más adelante: sobrevuelos de 40 s por evento y páginas por comuna.
