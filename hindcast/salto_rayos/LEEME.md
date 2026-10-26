# Prueba del salto de rayos (aviso "tormenta intensificándose")

Algoritmo y umbrales publicados (Schultz et al. 2009, 2011), sin ajustar a ningún evento chileno: `envivo/salto_rayos.py`.
Días probados: los que tuvieron tormenta (TS) en el METAR de algún aeródromo entre Iquique y Concepción desde abril de 2025
(`salto-rayos-prueba.yml`). Cada aviso se contrastó a mano con prensa, SENAPRED (vía resúmenes de OPS) y la DMC: columna
`que_paso` de `avisos.csv`. "Sin reportes" no es lo mismo que "sin daño": es el techo de las falsas alarmas.

## Resultado al 26-oct-2026 (27 días)

- 117 marcas en bruto, 94 sobre Argentina (la caja de En vivo llega a 68° W): ya no se marcan. Quedan **23 avisos en Chile, en 10 de los 27 días**; 17 días sin ninguno.
- **8 con tiempo severo en la ventana** (tornado de Requínoa ×2, aluvión de San Carlos de Apoquindo del 8-oct a ~14 km, granizo en Lo Barnechea, Maipú/Padre Hurtado, sur de Santiago y Los Ángeles, granizo e inundaciones en Talca).
- **4 probables** con la hora sin precisar (Mulchén, Alto Biobío, Colina, Yerbas Buenas).
- **2 no atribuibles** al chubasco (crecida del Mapocho, daño por el frente en Lampa).
- **9 sin reportes**: a lo más 39 % de falsas alarmas, parecido al 36 % de EE.UU.

## Lo que no marcó

- **13-oct, ~16:30, Estación Central:** tornado EF0 (preliminar de la DMC). El aviso más cercano fue Colina, a ~33 km.
- **28 y 29-ago, Biobío, Ñuble, costa:** 16 tornados y trombas en 48 h. Ningún aviso esos días: son tormentas de invierno, bajas y con pocos rayos, que el salto de rayos casi no ve. Para esas, el aviso útil es el ambiente a 72 h (`hindcast/tormentas_gfs/`).
- **21-oct, ~14:00, Retiro (Maule):** tornado EF0/EF1. Ese día no estaba en la prueba porque ningún aeródromo informó tormenta; se prueba aparte.

Conclusión provisoria: el salto de rayos sirve para tormentas de verano y primavera con mucha actividad eléctrica (granizo, aluviones por chubasco, tornados como el de Requínoa); no sirve para los tornados de invierno con pocos rayos. Por eso van los dos avisos.
