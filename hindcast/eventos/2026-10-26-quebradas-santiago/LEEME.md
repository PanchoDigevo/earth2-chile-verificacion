# Quebradas activadas en Santiago oriente, 26-oct-2026

**Reportes (19:21–19:22 de Chile):** T13: "Se activan quebradas en Camino El Alba" (Las Condes, al pie de la Quebrada de
Apoquindo / San Carlos de Apoquindo). Diputado Cristián Araya: "Se activa quebrada en sector Camino a Farellones kilómetro 8"
(Lo Barnechea). Sin informe oficial todavía (SENAPRED, municipios).

## Qué estaba pronosticado (registrado antes, `hindcast/seguimiento/pronosticos.csv`)

Quebrada de Apoquindo (Q1), bloque de 15 a 21 h del 26-oct, nivel del indicador de quebradas si la lluvia del bloque cayera en 2 h:

| Modelo | Primera corrida en "aviso" o "atención" | Registrado (UTC) | Lluvia del bloque |
|---|---|---|---|
| GFS | 25-oct 06Z: **aviso** (p = 0,59), y en todas las corridas siguientes (atención en la de 26-oct 06Z) | 2026-10-25 11:45 (**~32 h antes**) | 15–24 mm |
| IFS | 26-oct 12Z: **atención** (p = 0,31) | 2026-10-26 20:36 (~45 min antes) | 12,7 mm |
| AIFS | nunca: bajo en todas (p ≤ 0,17) | — | 6–9 mm |

Además: tormentas posibles en Las Condes para la tarde (indicador de 72 h, GFS 00Z del día).

## Qué se midió

- **Rayos (GOES-19 GLM) a menos de 10 km de San Carlos de Apoquindo:** 11, 13 y 12 rayos en los bloques de 10 min de las 18:40, 18:50 y 19:00: una celda de tormenta encima de la precordillera desde unos **40 minutos antes** de la activación. Otro pulso a las 19:40 (18 rayos). Sin salto de rayos (la tasa no llegó a 10 por minuto). Registro en `rayos_glm_30km.csv`.
- **Pluviómetros:** casi nada en el valle: Aguas Andinas (La Florida) 0,8 mm a las 18 h, El Colorado 0,2 mm; San José Guayacán (Cajón del Maipo) 4 y 3 mm. **Ninguna estación con datos en tiempo real está dentro de las quebradas**: la lluvia convectiva que las activó no la midió nadie de la red que leemos.
- Isoterma ~2.950 m (El Colorado +1,3 °C): llovía, no nevaba, en toda la cuenca de la quebrada.

## Lectura

- El ambiente y la lluvia suficiente se vieron con 32 h de anticipación, pero en un solo modelo de tres (GFS). AIFS no lo vio.
- El monitor en vivo habría dicho "con lo medido: bajo", porque las estaciones del valle no ven una celda sobre la precordillera. La tormenta sí se veía en los rayos encima de la quebrada.
- Camino a Farellones km 8 no está entre las quebradas seguidas (solo las quemadas: Apoquindo y Ramón).
- Como con Requínoa, este caso no se usa para calibrar nada: queda como prueba.
