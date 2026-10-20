# Tareas pendientes para Code (en orden)

Leer antes `CLAUDE.md` (sección "Capas estándar"). Al terminar cada tarea, marcarla [x], hacer commit y explicarle a Pancho en simple qué se encontró antes de publicar.

## 1. [x] Monitor de océano y deriva (capa estándar)
Detectar cambios de régimen (El Niño, olas de calor marinas) desde datos primarios, nunca desde noticias.
- Diario en GitHub Actions: NOAA OISST v2.1 (0,25°, dominio público, AWS o NCEI) y su climatología 1991–2020. Anomalía de temperatura del mar en cajas costeras frente a cada aeródromo de la costa (Arica, Iquique, Antofagasta, Caldera, La Serena, Santo Domingo, Concepción, Puerto Montt) y en la región Niño 1+2.
- Índices semanales Niño 1+2 y Niño 3.4 de NOAA CPC, guardados como serie.
- Deriva: por estación, sesgo móvil de 30 días vs. el aprendido en 2025; marcar "deriva" sobre un umbral y cruzarla con la anomalía del mar de su caja costera.
- Corrección móvil (últimos 45 días) junto a la fija de 2025, evaluadas sin mirar el futuro; publicar cuál gana por estación.
- En el sitio, sección "Lo que está cambiando": anomalía del mar por tramo de costa, Niño 1+2, estaciones en deriva, con fecha y fuente (NOAA). Lenguaje descriptivo, sin titulares. Si el dato no muestra calentamiento, no se dice.
- Si una fuente no responde, avisar y proponer alternativa (ERA5 SST) antes de improvisar.

## 2. [x] Viento (capa estándar)
- Histórico: extraer viento 10 m (10u, 10v) de AIFS, IFS y GFS, y rachas donde la fuente las publique (revisar qué campo de ráfaga trae cada open data; si no hay, decirlo). METAR histórico: agregar la racha (campo gust de Iowa State).
- Verificar velocidad, dirección y rachas por estación, plazo y mes, igual que la temperatura, con corrección fija y móvil.
- En los cuatro eventos de 2026 y en los incendios de enero 2026 (Biobío/Ñuble, estaciones cercanas): viento y racha pronosticados vs. observados a 72/48/24 h.
- Episodios de viento fuerte (racha > 50 km/h): cuántos anticipó cada modelo.

## 3. [x] Página de escenarios de incendio
- `site/escenarios.html` (pestaña "Escenarios"): cada día AIFS-ENS (50 miembros) desde ECMWF open data en AWS, a 15 días, para comunas prioritarias de CONAF en RM, Valparaíso, O'Higgins, Maule, Ñuble y Biobío.
- Por miembro, índice de peligro meteorológico de incendio (temperatura, humedad, viento, días sin lluvia; FWI si alcanza). Por comuna, probabilidad de superar el umbral cada día (abanico + % de miembros sobre umbral).
- Guardar el histórico diario para mostrar cómo cambia la probabilidad de un mismo día a medida que se acerca.
- Lenguaje de "indicador", nunca "alerta"; enlaces a CONAF y SENAPRED.

## 4. [x] Earth2Studio
- Carpeta `earth2/`: instalar en venv aparte (`~/e2venv-e2s`), corregir la selección por estación de `fetch_e2s.py`, comparar con `fetch_aifs.py` en una corrida y, si coincide, usarlo en el workflow. Probar `earth2studio.data.GOES` y `GOESGLM` para el 13-oct entre 14:00 y 19:00 (hora de Chile).
- Hecho en GitHub Actions (`.github/workflows/earth2.yml`), no en el Mac: Earth2Studio 0.19 pide Python 3.11 y el Mac tiene 3.9. La extracción por estación de `fetch_e2s.py` coincide con la nuestra (AIFS 2026-10-14 00z, 104 pares, diferencia 0,000). GOES-19 y GLM funcionan: 2.640 destellos sobre Santiago entre 14:00 y 19:00, máximo 1.403 entre 16:00 y 17:00, tope de nube a −51,6 °C. El workflow diario sigue con `fetch_aifs.py` hasta que Pancho decida: cambiarlo suma ~2 GB de torch a cada corrida y no mejora la precisión.

---

# Fase 0: dejar Earth-2 andando (agregado 20-oct-2026)

Cinco etapas: correr lo que existe → preparar datos → entrenar → validar → operar. La ruta crítica es datos → entrenamiento → validación. Mismas reglas de siempre: nada de cifras de negocio ni nombres de clientes en este repo; datos pesados y pesos fuera del repo; eventos 2026 nunca en el entrenamiento; explicarle a Pancho en simple qué se encontró antes de seguir con la siguiente tarea.

## 5. [ ] Correr AIFS en las GPUs del POD (etapa 1: correr lo que existe)
Hoy AIFS corre en ECMWF y nosotros solo bajamos su salida. El objetivo es correrlo nosotros en una L40S del POD, que es lo que después alimenta a CorrDiff.
- Contenedor con `earth2studio[aifs]` (Python 3.11) en un nodo L40S del POD; el acceso lo da Guillermo. Si no hay acceso al POD, detenerse y avisar.
- `earth2studio.models.px.AIFS` 4×/día (00/06/12/18z), inicializado con IFS open data (`source="aws"`), a 10 días.
- Guardar solo el recorte de Chile en el POD; exportar por estación al formato de `data/pronostico_puntos.csv` con `modelo="AIFS-POD"`.
- Control: en los mismos pares debe coincidir con el AIFS de ECMWF (diferencias de redondeo). Si no coincide, explicar por qué antes de seguir.
- Medir y anotar en `earth2/workload_pod.md`: GPUs usadas, minutos por corrida, memoria GPU, horas-GPU por día, tráfico de red y almacenamiento. Es la ficha técnica para declarar el workload a NVIDIA (NVCF). Solo datos técnicos.
- Hecho cuando: 7 días seguidos 4×/día en el POD, con los pares visibles en el sitio.
- **Avance 20-oct-2026 (sin acceso al POD todavía):** listo `earth2/correr_pod.py` (AIFS o SFNO desde el análisis de IFS, recorte de Chile, CSV por aeródromo, ficha técnica por corrida y `--control` contra el AIFS de ECMWF), el contenedor `earth2/pod/Dockerfile` y la ficha `earth2/workload_pod.md`. Probado sin GPU con el modelo de persistencia en Actions (`earth2-pod-prueba.yml`). Hallazgos: AIFS 1.1 y SFNO piden ~40 GB y caben en una L40S; FourCastNet 3 pide ~80 GB y no cabe en una sola. El control no puede dar igualdad exacta (ECMWF inicializa con su análisis nativo y puede usar otra versión del checkpoint): la prueba con persistencia dio 0,59 °C de diferencia media ya a plazo 0 (máx. 1,62 °C), por el paso de grilla de AIFS; ese es el piso esperable. Falta: que Guillermo lo corra en el POD (o lo empaquete como función de NVCF), medir la ficha y sumar el modelo al sitio.

## 6. [ ] Dataset de entrenamiento para CorrDiff-Chile (etapa 2: preparar datos)
NVIDIA entrega la receta (PhysicsNeMo `examples/weather/corrdiff`), no un modelo para Chile. El dataset es lo que tenemos que construir.
- Objetivo de alta resolución: SAAG-WRF 4 km horario (`s3://saag-wrf/`, CC-BY 4.0), recortado al dominio de Chile (confirmar la extensión real de SAAG; Magallanes queda al borde). Variables: precipitación, temperatura a 2 m, viento a 10 m (u, v) y radiación si está.
- Entrada gruesa: ERA5 emparejado (`earth2studio.data.ARCO_ERA5`), con las variables que pide la config del ejemplo corrdiff.
- Años: 2012–2021. Si el recorte es lento (los archivos son de toda Sudamérica), partir con 2017–2021 y ampliar después.
- Reservar un año completo (2021) como prueba; no se usa para entrenar.
- Formato Zarr con la estructura que espera el dataloader del ejemplo. Se arma en una instancia de nube sin GPU o en nodos CPU del POD, nunca en el Mac ni en el repo.
- Script reproducible `entrenamiento/preparar_dataset.py` y `entrenamiento/README.md` con tamaño final, tiempos y licencias.
- Hecho cuando: un lote de muestra carga sin errores con el dataloader del ejemplo PhysicsNeMo.

## 7. [ ] Entrenar CorrDiff-Chile v0 (etapa 3: entrenar)
- Contenedor `nvcr.io/nvidia/physicsnemo/physicsnemo:25.11`, ejemplo corrdiff: primero la red de regresión (UNet), luego la de difusión.
- Antes de la corrida completa: corrida corta solo en la zona central (aprox. 30°S a 38°S) para medir horas-GPU por época y estimar el costo total. **Parar y reportarle a Pancho la estimación antes de lanzar la corrida completa** (decide si se usa GPU arrendada o el POD). Referencia publicada: el CorrDiff de Taiwán usó ~21.500 horas en H100.
- Registrar config, semilla, versión del dataset y horas-GPU reales en `entrenamiento/corridas.md`.
- Evaluar en el año reservado: RMSE, MAE y CRPS contra SAAG; línea base ERA5 interpolado bilinealmente; espectros de potencia; dispersión del ensamble. Reportar en simple qué mejora y qué no (extremos y cordillera son el punto débil conocido).
- Pesos fuera del repo; al repo solo configs y métricas.
- Hecho cuando: v0 le gana a ERA5 interpolado en precipitación y temperatura en el año reservado, o queda documentado por qué no.

## 8. [ ] Nowcaster v0 con GOES-19 (etapa 3, en paralelo a la 7)
StormScopeGOES de Earth2Studio está entrenado para EE.UU. (grilla HRRR): es la arquitectura de partida, no el producto.
- Dataset GOES-19 ABI + GLM 2024–2026 sobre Chile central cada 10 min (`earth2studio.data.GOES`, `GOESGLM`). Verdad: lluvia de estaciones (`estaciones/`), más GOES RRQPE e IMERG como apoyo.
- Reentrenar en 8 GPUs; eventos 2026 fuera del entrenamiento.
- Métricas: CSI, POD y FAR a 1, 5 y 10 mm/h, a 30, 60 y 120 min, contra pluviómetros; comparar con persistencia. Si no le gana a persistencia, decirlo.
- Hecho cuando: tabla de métricas explicada en simple.

## 9. [ ] Validación para el gate de febrero (etapa 4: validar)
- Correr CorrDiff v0 y el nowcaster v0 sobre los eventos de `hindcast/eventos/eventos_2026.csv`, a 24 h, 6 h y 1 h de anticipación, con la misma vara de la verificación retroactiva.
- Comparar contra estaciones (`estaciones/`), IFS y AIFS globales, y el WRF operacional de la DMC (6 km) si se consigue su salida (si no, decirlo).
- Criterio: cantidad, lugar y hora, no solo "lluvia sí/no". Para Las Condes, cruzar lluvia × cicatrices de incendio por quebrada (capa de superficie de `hindcast/`).
- Salida: `hindcast/informe_gate.md` y una página en el sitio, en lenguaje de "aviso", que publique también las fallas. El informe lo revisa el asesor meteorológico antes de publicarse.

## 10. [ ] Operación automática en el POD (etapa 5: operar; solo si pasa el gate)
- No arrancar sin luz verde de Pancho después del gate (26-feb-2027).
- Empaquetar CorrDiff-Chile como servicio para NVIDIA Cloud Functions; cadena automática 4×/día: AIFS en el POD (tarea 5) → CorrDiff → productos por estación y polígono → API.
- Monitoreo: aviso interno si una corrida falla o si el error por estación se sale de banda (reusar la capa estándar 5, deriva).
- Reentrenamiento anual documentado en `entrenamiento/corridas.md`.
