# Brief del sitio (UI/UX)

Fuente de verdad para cualquier cambio de diseño del sitio público https://panchodigevo.github.io/earth2-chile-verificacion/. Texto público: sin cifras de negocio ni nombres de clientes. El mensaje de fondo está en `docs/narrativa_sitio.md`.

## Qué es

Un sitio público que mide, todos los días y a la vista, qué tan bien pronostican el tiempo en Chile los mejores modelos globales (AIFS, la IA de ECMWF; IFS de ECMWF y GFS de NOAA), muestra dónde se les escapa la geografía chilena, y muestra cómo la mejoran las capas chilenas a medida que existen: hoy, una corrección por estación y un indicador de flujo de detritos por quebrada en Santiago oriente.

## Para quién, en orden de prioridad

1. **Autoridades y equipos de gestión de riesgo** (gobierno central, municipios, SENAPRED). No son meteorólogos. Llegan por un enlace que alguien les mandó o que les muestran en una reunión, con dos o tres minutos de atención, a veces en el teléfono. Quieren saber si esto sirve para decidir mejor y si se puede confiar.
2. **Técnicos** (meteorólogos, DMC, academia, el asesor del proyecto). Quieren el método, los números exactos, las fuentes y el código, y buscan los límites.
3. **Prensa y público interesado.** Quieren entender un evento concreto (el aluvión de Las Condes, el frontal de Coquimbo) y ver su zona.

## El mensaje en 30 segundos

El pronóstico global, incluso el de IA, ve Chile en cuadrados de 25 km. En la costa norte, la Patagonia y la precordillera se equivoca por varios grados y no sabe dónde se concentra la lluvia. Lo medimos en público todos los días. Una primera corrección local ya reduce el error entre 19 y 28 %, según el modelo. Para las quebradas quemadas de Santiago oriente, mostramos cuál se acerca a un umbral de flujo de detritos con la lluvia prevista.

## Qué debe poder hacer cada visitante

- Entender la brecha en 10 segundos, sin leer párrafos.
- Encontrar su zona: su estación o su quebrada.
- Entender cada número donde aparece, sin ir a otra sección ni saber qué es MAE, dNBR o PropHM23.
- Confiar: ver la fecha de actualización, el método, las fuentes, el código abierto y los límites dichos con franqueza.
- Ver qué decían los modelos antes de los eventos de 2026.
- Probar un escenario ("¿y si cayeran 30 mm en dos horas?") y ver qué cambia.

## La portada (desde el 26-oct-2026)

Producto primero: el visitante busca su comuna y ve el tiempo de ahora y de hoy sin bajar. Debajo, la confianza (cifras cortas) y la prueba (25 contra 4 km y el mapa del error). Todo lo demás es una puerta a su pestaña. El estándar a superar es la app del tiempo del teléfono; lo que la supera aquí es la duda a la vista y la verificación pública.

## Reglas que no se negocian

- Lenguaje de **aviso** o **indicador**, nunca "alerta". Las alertas oficiales son de la DMC y de SENAPRED, y siempre se enlazan.
- Las cifras con pocos datos se marcan como preliminares y no se presentan como resultados.
- Coma decimal y unidades en cada número (°C, mm, km², %).
- Marca propia; sin logos ni material de marca de NVIDIA.
- Funciona en teléfono, en modo oscuro y sin conexión rápida.

## Límites técnicos

Sitio estático en GitHub Pages, generado por Python cuatro veces al día (`verificacion/render_site.py`, `historico/render_historico.py`) más una página estática con Leaflet (`site/quebradas.html`). Sin servidor ni base de datos: toda la interacción ocurre en el navegador con los JSON y GeoJSON publicados. La navegación común está en `verificacion/comun.py`.

## Hechos que el sitio tiene para contar (octubre de 2026)

- Error medio de temperatura a 24 h en 2026: AIFS 1,46 °C, IFS 1,73 °C, GFS 2,13 °C. La IA gana a los modelos físicos en todos los plazos, también en 2025.
- Corrección por estación aprendida con 2025 y aplicada a 2026: AIFS baja a 1,17 °C (19 % menos), IFS a 1,28 °C (26 %), GFS a 1,53 °C (28 %). Arica pasa de 2,41 a 0,84 °C; Iquique de 2,33 a 0,91 °C.
- Eventos: en el frontal del centro-sur los tres modelos marcaron lluvia 72 h antes en todos los casos; en Coquimbo, AIFS en 11 de 12, GFS en 8 de 12.
- Quebrada de Apoquindo: 10,8 km², 46,5 % de su superficie quemada en el verano de 2026.
