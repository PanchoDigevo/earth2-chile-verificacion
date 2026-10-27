# Cámaras públicas de Chile: inventario verificado (26 y 27-oct-2026)

Para el gemelo digital: la imagen real del lugar junto al pronóstico y a los escenarios. Se verificó cada URL (código 200 y
que la imagen cambie). Lo que importa es que la imagen se pueda leer por programa y se actualice; el video en vivo es
secundario.

## Lo que sirve de inmediato (imagen fija, sin clave, legible por programa)

| Lugar | URL de la imagen | Cada cuánto | Nota |
|---|---|---|---|
| Valle Nevado, La Fourchette / Piscina / Hotel Puerta del Sol | `https://cams.opensnow.com/latest/4278/720.webp`, `/4279/`, `/4280/` | ~3-10 min | WebP, `Last-Modified` real. Sin términos explícitos (OpenSnow). |
| Portillo, Laguna del Inca | `https://ipcamlive.com/player/snapshot.php?alias=laguna` (redirige al JPG) | cuadro actual | ~40 KB. |
| Nevados de Chillán, Plaza Tata | `https://ipcamlive.com/player/snapshot.php?alias=plazatata` | cuadro actual | Otras (`pistanovicios`) apagadas fuera de temporada. |
| Corralco, hotel | `https://ipcamlive.com/player/snapshot.php?alias=hotel` | cuadro actual | `recornisa`, `vista1600`, `zcbski` apagadas. |
| Cerro Paranal (ESO), panorámica y 8 presets | `https://www.eso.org/public/archives/static/pano/latest/pano_PV_960x.jpg`, `/POI/460x/preset_1..7,99.jpg` | ~1 h | ESO autoriza embeber con la URL. Mejor base legal. |
| La Silla, cielo completo | `https://allsky-dk154.asu.cas.cz/AllSkyCurrentImage.JPG` | ~2 min | Nubosidad nocturna del norte. |
| ALMA (NRAO), Chajnantor | `https://public.nrao.edu/wp-content/uploads/nrao/almawebcam/latest/pano_PV_960x.jpg` | no verificado | Mismo archivo en 10 min; la copia en ESO está congelada desde 2020. |

## Ampliación: streams de YouTube como imagen fija (~45 cámaras)

Todo stream en vivo de YouTube tiene una miniatura que se renueva cada ~5 min: `https://i.ytimg.com/vi/<ID>/maxresdefault_live.jpg`
(verificado 200 para todos los IDs de abajo). Para un cuadro exacto: `yt-dlp`/`ffmpeg`. Los IDs cambian cuando el canal
reinicia el stream (Ledrium lo hace): hay que resolver el ID vigente por canal (`/streams` u oEmbed) antes de pedir la miniatura.
Términos: YouTube no autoriza explícitamente este uso; solo **sanantonioimagen** lo permite citando la fuente.

- **Marejadas UV** (Universidad de Valparaíso, sistema de alerta de marejadas): Las Torpederas `MIHl7F_0ayo`, Reñaca `F57ENlfm-ww`, Playa Acapulco `gW7OTeLXrI4`, Av. Perú `ysqxSxIqiq0`, Pichilemu `oneTQy8PWGA`, Mejillones `0rJ4TKsW_Ng`, Rapa Nui `DRZkCLZ7g-o`.
- **sanantonioimagen** (uso permitido citando): Puerto San Antonio `ulBAncoXWws`, San Antonio `C6x5KQnE3Nc`, Barros Luco `tuWK78rNoII`, Llolleo `U9YCYQe-VvE`, desembocadura del Maipo `Uh2A0nVoqxc`, Cartagena `obYSVVM7RB0`, El Quisco `VX8MquqY_Ks`, `1oItHarYYgI`.
- **Ledrium** (empresa chilena de videovigilancia e IA; solo YouTube, sin sitio de cámaras): Canal San Carlos `FZnNn2VwSlc`, Tobalaba/MUT `ErUOGtBXhgY`, Costanera Center `UpHOS_enhjI`, Thayer Ojeda/Los Leones `vXKn4qUQFMA`. El `z-JFz7LCXRk` terminó en agosto; lo reemplazó `FZnNn2VwSlc`.
- **Valle Nevado**: Piscina `uyt8JsITTac`, Puerta del Sol `tmS73xQ4zVc`, La Fourchette `tWNxInShxZI`, Góndola `qd2Zr8gE8Sw`. **La Parva**: `rV6JR-lvNQk`, `LYq7Zt-O81Y`, `Dkx-_pSWjZw`, `IXJ24EBzO_s`, `85IzX2kG90o`, `4SjBn7MXbaQ`. **El Colorado / Farellones**: `FWidaf7LWPY`, `9aFWhm5XRJo`, `7Rva7xDRzz4`.
- Ciudades: ConceCam `RhdmP5017VM` (Concepción), Manupuntocl `5jPpMkg5daM` y PortalMedios `INirmzQY8eg` (Valparaíso), Viña CAM `XXA2S4Ky5jA`, Santiago Skyline `_Nrt155MExU`, SantiagoCam `bgmR3W4eXic`, Los Andes `HirKZqakDIA`, Punta Arenas `J0TFvlqWqzA`, Chiguayante `7qp1v_XpjxQ`, San Fernando `YgFU1wbVlS4`, Faro La Serena `-WURM2xspdc` (municipal).

## Lo que no existe o no se puede usar

- **UOCT / Transporte Informa**: 85 fichas de cámaras (RM, Valparaíso, Biobío, Coquimbo) pero **sin imagen ni stream público**; las grabaciones solo salen por oficio a Fiscalía o policías. Único endpoint vivo: semáforos (`api.uoct.cl/api/v1/junction/general-info`).
- **MOP / Vialidad / pasos fronterizos, concesionarias (Costanera Norte, Central, Vespucio, 68, 78), DGAC, DMC, CEAZA, SERNAGEOMIN (OVDAS pide login), CONAF, puertos, DIRECTEMAR**: ninguna publica cámaras.
- **Municipios**: Las Condes (3.390 cámaras), Providencia, Vitacura, Lo Barnechea, Viña, Valparaíso: sin portal público. Solo La Serena (faro, YouTube).
- **Windy Webcams API**: probablemente el mayor volumen agregado, pero exige clave, crédito y enlace a Windy en cada imagen, y URLs con token que vence a los 10 min (gratis). **SkylineWebcams** (17 en Chile), webcamtaxi, EarthCam: bloquean bots, sin API.

## Mejor solución para el piloto

1. **Núcleo legible por programa y sin clave (12-15 imágenes):** OpenSnow Valle Nevado (3), ipcamlive Portillo, Chillán y Corralco (3), ESO Paranal (9), La Silla (1). Se bajan cada 10 min desde Actions a una rama de datos, igual que los rayos.
2. **Ampliación a ~45 puntos con miniaturas de YouTube**, priorizando sanantonioimagen (permiso) y Marejadas UV (institución pública), y pidiendo permiso a Ledrium, Valle Nevado y La Parva para usar sus cuadros (con cita).
3. **Para cada cámara, el gemelo cruza la imagen con**: lluvia y nubosidad previstas, línea de nieve e isoterma, viento y rayos de ese punto; y guarda "lo que la cámara vio" junto a "lo que el modelo decía" 24 y 48 h antes: verificación visual.
4. **Primer lugar icónico**: Valle Nevado (3 imágenes cada pocos minutos, 4 streams, cuenca del Mapocho ya delimitada, nieve e isoterma ya calculadas). Segundo: la costa de Valparaíso-San Antonio (Marejadas UV + sanantonioimagen, permiso explícito), cuando sumemos oleaje.
5. **Para un cliente**: sus propias cámaras (una faena o municipio tiene decenas) entran por el mismo camino: una URL de imagen cada N minutos. No hace falta streaming.
