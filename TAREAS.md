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

## 2. [ ] Viento (capa estándar)
- Histórico: extraer viento 10 m (10u, 10v) de AIFS, IFS y GFS, y rachas donde la fuente las publique (revisar qué campo de ráfaga trae cada open data; si no hay, decirlo). METAR histórico: agregar la racha (campo gust de Iowa State).
- Verificar velocidad, dirección y rachas por estación, plazo y mes, igual que la temperatura, con corrección fija y móvil.
- En los cuatro eventos de 2026 y en los incendios de enero 2026 (Biobío/Ñuble, estaciones cercanas): viento y racha pronosticados vs. observados a 72/48/24 h.
- Episodios de viento fuerte (racha > 50 km/h): cuántos anticipó cada modelo.

## 3. [ ] Página de escenarios de incendio
- `site/escenarios.html` (pestaña "Escenarios"): cada día AIFS-ENS (50 miembros) desde ECMWF open data en AWS, a 15 días, para comunas prioritarias de CONAF en RM, Valparaíso, O'Higgins, Maule, Ñuble y Biobío.
- Por miembro, índice de peligro meteorológico de incendio (temperatura, humedad, viento, días sin lluvia; FWI si alcanza). Por comuna, probabilidad de superar el umbral cada día (abanico + % de miembros sobre umbral).
- Guardar el histórico diario para mostrar cómo cambia la probabilidad de un mismo día a medida que se acerca.
- Lenguaje de "indicador", nunca "alerta"; enlaces a CONAF y SENAPRED.

## 4. [ ] Earth2Studio
- Carpeta `earth2/`: instalar en venv aparte (`~/e2venv-e2s`), corregir la selección por estación de `fetch_e2s.py`, comparar con `fetch_aifs.py` en una corrida y, si coincide, usarlo en el workflow. Probar `earth2studio.data.GOES` y `GOESGLM` para el 13-oct entre 14:00 y 19:00 (hora de Chile).
