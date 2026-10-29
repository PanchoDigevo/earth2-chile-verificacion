"""Pestaña Pronóstico (site/pronostico.html): el tiempo que viene en cada comuna de Chile, como lo espera cualquier persona
(ahora, próximas 48 horas, 15 días), armado con lo que este sitio ya verifica.

- Comunas: verificacion/comunas.csv (352, desde Wikidata). El pronóstico es el del punto de grilla de 25 km que contiene a la comuna.
- 48 h: data/pronostico_comunas.csv (última corrida de AIFS, IFS, GFS y los modelos propios de Earth-2). Un solo pronóstico: el
  promedio de los modelos, cada uno ajustado con el error que tuvo, a esa hora del día en los últimos 30 días, en un aeródromo que
  cae en el MISMO cuadrado de 0,25° que la comuna (el error es del cuadrado: Tobalaba falla −6,5 °C en la tarde porque su cuadrado
  mezcla ciudad y cordillera, y eso no vale para La Cisterna, en otro cuadrado). Sin aeródromo en el cuadrado, va sin ajuste.
- 15 días: site/datos/pronostico_15d.json, que escribe escenarios/escenarios.py con los 50 escenarios de AIFS-ENS.
- Ahora: la última medición de la estación más cercana (aeródromos por METAR, estaciones DMC por SYNOP), hasta 30 km y 3 horas.
Escribe site/datos/pronostico_48h.json (lo lee el navegador) y site/pronostico.html."""
import glob, json, os
import numpy as np, pandas as pd
import tormenta_vivo
import monitor_lluvia
import aviso_oficial
from comun import JS_DEF, a_chile, aviso, nav, num, pie

AQUI = os.path.dirname(os.path.abspath(__file__))
DIAS_SESGO, MIN_SESGO = 30, 10
KM_AHORA, HORAS_AHORA = 30.0, 3.0
celda = lambda lat, lon: (int(round(float(lat) * 4)), int(round(float(lon) * 4)))   # cuadrado de 0,25° (AIFS, IFS y GFS)


def km(lat1, lon1, lat2, lon2):
    la1, la2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def observaciones_ahora(ahora_n):
    """Última medición por estación en las últimas HORAS_AHORA horas: [{nombre, lat, lon, t, hora_chile}]."""
    out = []
    try:
        o = pd.read_csv(os.path.join(AQUI, "data", "metar_obs.csv"), parse_dates=["time"])
        o["time"] = o.time.dt.tz_localize(None)
        o = o.dropna(subset=["temp_c"]).sort_values("time").groupby("icao").tail(1)
        o = o[o.time >= ahora_n - pd.Timedelta(hours=HORAS_AHORA)]
        from render_site import nombre          # mismos nombres cortos que el resto del sitio
        for r in o.itertuples(index=False):
            out.append({"nombre": nombre(r.icao, r.name)[0], "lat": float(r.lat), "lon": float(r.lon),
                        "t": round(float(r.temp_c), 1), "w": None if pd.isna(r.wspd_kt) else round(float(r.wspd_kt) * 1.852), "hora": a_chile(r.time).strftime("%H:%M")})
    except Exception as e:
        print("pronóstico: sin METAR para 'ahora':", type(e).__name__, e)
    try:
        cat = pd.read_csv(os.path.join(AQUI, "..", "estaciones", "catalogo.csv")).dropna(subset=["lat", "lon", "wmo"])
        cat["wmo"] = cat.wmo.astype(int).astype(str)
        archivos = sorted(glob.glob(os.path.join(AQUI, "..", "estaciones", "datos", "synop", "*.csv")))[-2:]
        s = pd.concat([pd.read_csv(f, dtype={"wmo": str}) for f in archivos], ignore_index=True) if archivos else pd.DataFrame()
        if not s.empty:
            s["hora_utc"] = pd.to_datetime(s.hora_utc); s = s.dropna(subset=["temp_c"])
            s = s[s.hora_utc >= ahora_n - pd.Timedelta(hours=HORAS_AHORA)].sort_values("hora_utc").groupby("wmo").tail(1)
            s = s.merge(cat[["wmo", "nombre", "lat", "lon"]], on="wmo")
            for r in s.itertuples(index=False):
                out.append({"nombre": r.nombre, "lat": float(r.lat), "lon": float(r.lon), "t": round(float(r.temp_c), 1), "w": None,
                            "hora": a_chile(r.hora_utc).strftime("%H:%M")})
    except Exception as e:
        print("pronóstico: sin SYNOP para 'ahora':", type(e).__name__, e)
    return out


def sesgos(pts, ahora_n):
    """Error medio por (modelo, icao, hora UTC) en los últimos DIAS_SESGO días, con al menos MIN_SESGO pares; y coordenadas por icao."""
    if pts is None or pts.empty:
        return pd.DataFrame(columns=["modelo", "icao", "h", "sesgo"]), pd.DataFrame(columns=["icao", "lat", "lon"])
    v = pts[pts.valid >= ahora_n - pd.Timedelta(days=DIAS_SESGO)].dropna(subset=["t_err"]).copy()
    v["h"] = v.valid.dt.hour
    sg = v.groupby(["modelo", "icao", "h"]).t_err.agg(["mean", "size"]).reset_index()
    sg = sg[sg["size"] >= MIN_SESGO].rename(columns={"mean": "sesgo"})[["modelo", "icao", "h", "sesgo"]]
    coords = pts.groupby("icao").agg(lat=("lat", "first"), lon=("lon", "first")).reset_index()
    return sg, coords


def tormentas(ahora_n):
    """{id: DataFrame(valid, nivel)} de data/tormentas_comunas.csv (tormentas_gfs.py), desde ahora hasta 72 h."""
    try:
        t = pd.read_csv(os.path.join(AQUI, "data", "tormentas_comunas.csv"))
    except Exception:
        return {}
    t["valid"] = pd.to_datetime(t.valid, format="mixed")
    t = t[(t.valid > ahora_n - pd.Timedelta(hours=3)) & (t.valid <= ahora_n + pd.Timedelta(hours=72))]
    return {k: g[["valid", "nivel"]] for k, g in t.groupby("id")}


def datos_48h(est, pts, ahora):
    ahora_n = ahora.tz_localize(None) if ahora.tzinfo else ahora
    com = pd.read_csv(os.path.join(AQUI, "comunas.csv"))
    try:
        pr = pd.read_csv(os.path.join(AQUI, "data", "pronostico_comunas.csv"))
    except Exception:
        return None
    for c in ("run", "valid"):
        pr[c] = pd.to_datetime(pr[c], format="mixed")
    pr = pr[~pr.modelo.str.endswith(("SIMULADO", "PRUEBA")) & (pr.modelo != "PERSISTENCIA")]
    ult = pr.groupby("modelo").run.max()
    pr = pr[pr.run == pr.modelo.map(ult)].sort_values(["modelo", "id", "lead_h"]).copy()
    pr["p6"] = pr.groupby(["modelo", "id"]).tp_fc.diff().clip(lower=0)
    pr["ph"] = pr.groupby(["modelo", "id"]).lead_h.diff()
    pr = pr[(pr.valid >= ahora_n - pd.Timedelta(hours=2)) & (pr.valid <= ahora_n + pd.Timedelta(hours=50))]
    pr["h"] = pr.valid.dt.hour
    if "nub_fc" not in pr.columns:
        pr["nub_fc"] = np.nan

    sg, coords = sesgos(pts, ahora_n)
    est_por_icao = {e["icao"]: e for e in est}
    # aeródromo en el mismo cuadrado de 0,25° que cada comuna (para el ajuste y la confianza); si hay dos, el más cercano
    cerca = {}
    if not coords.empty:
        por_celda = {}
        for r in coords.itertuples(index=False):
            por_celda.setdefault(celda(r.lat, r.lon), []).append(r)
        for c in com.itertuples(index=False):
            cand = por_celda.get(celda(c.lat, c.lon), [])
            if cand:
                dist = [float(km(c.lat, c.lon, r.lat, r.lon)) for r in cand]
                i = int(np.argmin(dist)); cerca[c.id] = (cand[i].icao, dist[i])
    pr["icao"] = pr.id.map(lambda k: cerca.get(k, (None, None))[0])
    pr = pr.merge(sg, on=["modelo", "icao", "h"], how="left")
    pr["aj"] = pr.sesgo.notna()
    pr["tc"] = pr.t_fc - pr.sesgo.fillna(0.0)

    torm = tormentas(ahora_n)
    obs = observaciones_ahora(ahora_n)
    olat = np.array([o["lat"] for o in obs]); olon = np.array([o["lon"] for o in obs])
    pasos_por_id = {}
    for k, g in pr.groupby("id"):
        pasos = []
        for t, x in g.groupby("valid"):
            ll = x.p6.dropna()
            pasos.append({"c": a_chile(t).strftime("%Y-%m-%dT%H:%M"), "t": round(float(x.tc.mean()), 1),
                          "tmin": round(float(x.tc.min()), 1), "tmax": round(float(x.tc.max()), 1),
                          "p": None if ll.empty else round(float(ll.mean()), 1), "pn": int((ll >= 1).sum()), "nm": int(len(x)),
                          "ph": None if x.ph.dropna().empty else int(x.ph.dropna().max()),
                          "w": None if x.w_fc.dropna().empty else round(float(x.w_fc.mean()) * 3.6), "aj": int(x.aj.sum()),
                          "nb": None if x.nub_fc.dropna().empty else int(round(float(x.nub_fc.mean())))})
            tr = torm.get(k)
            if tr is not None:                    # nivel de tormenta en el bloque de 6 h que termina en este paso
                n = tr[(tr.valid > t - pd.Timedelta(hours=6)) & (tr.valid <= t)].nivel
                if len(n) and n.max() > 0:
                    pasos[-1]["tr"] = int(n.max())
        pasos_por_id[k] = pasos
    salida = {}
    for c in com.itertuples(index=False):
        if c.id not in pasos_por_id:
            continue
        d = {"n": c.nombre, "r": c.region, "pasos": pasos_por_id[c.id]}
        tr = torm.get(c.id)
        if tr is not None and (tr.nivel > 0).any():   # resumen de 72 h por día de Chile: nivel máximo y entre qué horas
            x = tr[tr.nivel > 0].assign(cl=lambda z: z.valid.map(a_chile))
            d["tr72"] = [{"f": f, "n": int(g.nivel.max()), "desde": int(g.cl.min().hour), "hasta": int(g.cl.max().hour)}
                         for f, g in x.groupby(x.cl.map(lambda z: z.strftime("%Y-%m-%d")))]
        if c.id in cerca:
            icao, dist = cerca[c.id]; e = est_por_icao.get(icao, {})
            m = (e.get("m") or {}).get("AIFS", {})
            d["est"] = {"icao": icao, "nombre": e.get("nombre", icao), "km": round(dist), "g": m.get("g"), "c": m.get("c")}
            b = sg[(sg.icao == icao) & (sg.modelo == "AIFS")].set_index("h").sesgo
            d["aj15"] = {"tmax": round(float(b[18]), 1) if 18 in b.index else None, "tmin": round(float(b[6]), 1) if 6 in b.index else None}
        if len(obs):
            dd = km(c.lat, c.lon, olat, olon); i = int(np.argmin(dd))
            if dd[i] <= KM_AHORA:
                o = obs[i]; d["obs"] = {"t": o["t"], "w": o["w"], "hora": o["hora"], "nombre": o["nombre"], "km": round(float(dd[i]))}
        salida[c.id] = d
    return {"generado": a_chile(ahora_n).strftime("%Y-%m-%dT%H:%M"), "corridas": {m: a_chile(t).strftime("%Y-%m-%dT%H:%M") for m, t in ult.items()},
            "modelos": sorted(ult.index), "comunas": salida}


ICONOS_JS = r"""
  // Ícono del cielo, sin inventar: sale de la nubosidad total de los modelos (%) y de la lluvia prevista (mm).
  const CIELO = (nb, mm, h) => {
    const noche = h != null && (h >= 21 || h < 7);
    if (mm != null && mm >= 1) return {k: 'lluvia', t: 'Lluvia'};
    if (mm != null && mm >= 0.2) return {k: 'llovizna', t: 'Llovizna'};
    if (nb == null) return null;
    if (nb < 25) return {k: noche ? 'luna' : 'sol', t: 'Despejado'};
    if (nb < 60) return {k: noche ? 'luna-nube' : 'sol-nube', t: 'Parcial'};
    if (nb < 85) return {k: 'nube', t: 'Mayormente nublado'};
    return {k: 'nubes', t: 'Nublado'};
  };
  // Con tormentas posibles en el bloque (ingredientes de GFS, tormentas_gfs.py), el ícono es de tormenta.
  const CIELO_P = (p, h) => p.tr ? {k: p.tr >= 2 ? 'tormenta-f' : 'tormenta', t: p.tr >= 2 ? 'Tormentas fuertes posibles' : 'Tormentas posibles'} : CIELO(p.nb, p.p, h);
  const SVG = {
    sol: '<circle cx="12" cy="12" r="4.2" class="i-sol"/><path class="i-sol" d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/>',
    luna: '<path class="i-luna" d="M19 14.5A7.5 7.5 0 0 1 9.5 5a7.5 7.5 0 1 0 9.5 9.5z"/>',
    nube: '<path class="i-nube" d="M7 18h10.5a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 7.3 10 4 4 0 0 0 7 18z"/>',
    nubes: '<path class="i-nube i-gris" d="M7 18h10.5a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 7.3 10 4 4 0 0 0 7 18z"/><path class="i-nube" d="M9 8.5A4.5 4.5 0 0 1 17.6 7"/>',
    'sol-nube': '<circle cx="8.5" cy="8.5" r="3.2" class="i-sol"/><path class="i-sol" d="M8.5 2.5v1.5M2.5 8.5H4M4.3 4.3l1 1M12.7 4.3l-1 1"/><path class="i-nube" d="M9 19h9a3 3 0 0 0 .3-6 4.7 4.7 0 0 0-8.9-.8A3.4 3.4 0 0 0 9 19z"/>',
    'luna-nube': '<path class="i-luna" d="M13 6.2A5 5 0 0 1 6.2 13 5 5 0 1 0 13 6.2z"/><path class="i-nube" d="M9 19h9a3 3 0 0 0 .3-6 4.7 4.7 0 0 0-8.9-.8A3.4 3.4 0 0 0 9 19z"/>',
    llovizna: '<path class="i-nube" d="M7 14.5h10.5a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 7.3 6.5 4 4 0 0 0 7 14.5z"/><path class="i-gota" d="M10 17.5v1.5M14 17.5v1.5"/>',
    lluvia: '<path class="i-nube" d="M7 13.5h10.5a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 7.3 5.5 4 4 0 0 0 7 13.5z"/><path class="i-gota" d="M8.5 16l-1 3M12.5 16l-1 3M16.5 16l-1 3"/>',
    tormenta: '<path class="i-nube i-gris" d="M7 13.5h10.5a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 7.3 5.5 4 4 0 0 0 7 13.5z"/><path class="i-rayo" d="M12.5 13l-2.5 4.5h3l-2 4.5"/>',
    'tormenta-f': '<path class="i-nube i-gris" d="M7 13.5h10.5a3.5 3.5 0 0 0 .4-7A5.5 5.5 0 0 0 7.3 5.5 4 4 0 0 0 7 13.5z"/><path class="i-rayo i-fuerte" d="M12.5 13l-2.5 4.5h3l-2 4.5"/>'
  };
  const icono = (c, tam) => c ? `<svg class="cielo" viewBox="0 0 24 24" width="${tam || 26}" height="${tam || 26}" role="img" aria-label="${c.t}"><title>${c.t}</title>${SVG[c.k]}</svg>` : '';
"""

CSS_ICONOS = """
.cielo{display:inline-block;vertical-align:middle;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;overflow:visible}
.cielo .i-sol{stroke:var(--sol);fill:none} .cielo circle.i-sol{fill:color-mix(in srgb,var(--sol) 35%,transparent)}
.cielo .i-luna{stroke:var(--muted);fill:color-mix(in srgb,var(--muted) 18%,transparent)}
.cielo .i-nube{stroke:var(--muted);fill:var(--surface)} .cielo .i-gris{fill:color-mix(in srgb,var(--muted) 22%,var(--surface))}
.cielo .i-gota{stroke:var(--lluvia);stroke-width:2}
.cielo .i-rayo{stroke:var(--medio);stroke-width:2.2} .cielo .i-fuerte{stroke:var(--alto)}
.tormenta-72{margin:4px 0 0;padding:8px 12px;border-left:4px solid var(--medio);background:color-mix(in srgb,var(--medio) 10%,var(--surface));border-radius:6px;font-size:15px}
.tormenta-72.fuerte{border-left-color:var(--alto);background:color-mix(in srgb,var(--alto) 10%,var(--surface))}
.tormenta-72[hidden]{display:none}
:root{--sol:#e0a100}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--sol:#f2c14e}}
:root[data-theme="dark"]{--sol:#f2c14e}
"""


CSS = """
.buscar{position:relative;max-width:520px}
.buscar input{width:100%;font:17px var(--font-body);padding:12px 14px 12px 40px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--fg)}
.buscar input:focus{outline:2px solid var(--accent);outline-offset:1px}
.buscar svg{position:absolute;left:14px;top:50%;transform:translateY(-50%);width:18px;height:18px;stroke:var(--muted);fill:none;stroke-width:2}
.buscar ul{position:absolute;left:0;right:0;top:calc(100% + 6px);margin:0;padding:6px;list-style:none;background:var(--surface);border:1px solid var(--line);
  border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.14);max-height:320px;overflow:auto;z-index:20}
.buscar li{padding:10px 12px;border-radius:8px;cursor:pointer;display:flex;justify-content:space-between;gap:12px}
.buscar li:hover,.buscar li[aria-selected="true"]{background:var(--accent-soft)}
.buscar li .r{color:var(--muted);font-size:13px}
.sugeridas{display:flex;flex-wrap:wrap;gap:8px}
.sugeridas button{font:14px var(--font-body);padding:7px 12px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--fg);cursor:pointer;min-height:38px}
.ahora{display:grid;gap:14px}
.ahora .top{display:flex;flex-wrap:wrap;align-items:flex-end;gap:14px 28px}
.ahora .temp{font-family:var(--font-display);font-size:72px;font-weight:600;line-height:1;letter-spacing:-.03em}
.ahora .temp small{font-size:28px;font-weight:500;color:var(--muted);letter-spacing:0}
.ahora .mm{display:grid;gap:3px;font-size:15px}
.ahora .mm b{font-size:22px;font-family:var(--font-display);font-weight:600}
.ahora .fuente{font-size:13px;color:var(--muted)}
.hoy{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:15px}
.hoy span svg{width:16px;height:16px;vertical-align:-3px;stroke:var(--muted);fill:none;stroke-width:1.8;margin-right:4px}
.hoy span.llueve svg{stroke:var(--lluvia)}
.horas{display:flex;gap:4px;overflow-x:auto;padding-bottom:6px;scroll-snap-type:x proximity}
.hora{flex:0 0 76px;scroll-snap-align:start;display:grid;gap:5px;text-align:center;padding:10px 4px;border-radius:10px;border:1px solid var(--line-soft)}
.hora .h{font:12px var(--font-data);color:var(--muted)}
.hora .d{font:600 11px var(--font-body);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.hora .t{font-family:var(--font-display);font-size:20px;font-weight:600}
.hora .ll{font-size:12.5px;color:var(--muted);min-height:16px}
.hora .ll.si{color:var(--lluvia);font-weight:600}
.hora .v{font-size:12px;color:var(--muted)}
.graf svg{width:100%;height:auto;display:block;overflow:visible}
.graf .eje{font:11px var(--font-data);fill:var(--muted)} .graf .grid{stroke:var(--line-soft)} .graf .sep{stroke:var(--line)}
.graf .banda{fill:var(--accent-soft)} .graf .lin{fill:none;stroke:var(--accent);stroke-width:2}
.graf .pt{fill:var(--accent);stroke:var(--surface);stroke-width:2} .graf .barra{fill:var(--lluvia)} .graf .etq{font:600 12px var(--font-data);fill:var(--fg)}
.graf .hit{fill:transparent;cursor:crosshair} .graf .guia{stroke:var(--muted);stroke-dasharray:3 3}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,.12);min-width:150px;z-index:5}
.tip b{display:block;margin-bottom:2px}
.quince{display:grid;gap:0}
.q-fila{display:grid;grid-template-columns:5.2em 30px 3.6em 3em 1fr 3em 4.2em;align-items:center;gap:8px;padding:9px 0;border-top:1px solid var(--line-soft);font-size:15px}
.q-fila:first-child{border-top:0}
.q-fila .dia{font-weight:600} .q-fila .dia small{display:block;font-weight:400;color:var(--muted);font-size:12px}
.q-fila .pl{font:12.5px var(--font-data);color:var(--muted);display:flex;align-items:center;gap:3px}
.q-fila .pl.si{color:var(--lluvia);font-weight:600} .q-fila .pl svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:1.8}
.q-fila .mn{text-align:right;color:var(--muted);font-family:var(--font-data)} .q-fila .mx{font-family:var(--font-data);font-weight:600}
.q-fila .vi{font:12.5px var(--font-data);color:var(--muted);text-align:right}
.rango{position:relative;height:10px;border-radius:5px;background:var(--line-soft)}
.rango i{position:absolute;top:0;bottom:0;border-radius:5px}
.rango .amplio{background:var(--accent-soft)} .rango .centro{background:var(--accent)}
.q-pie{font-size:13px;color:var(--muted)}
.confianza-txt{margin:0;padding:10px 12px;border-radius:8px;background:var(--accent-soft);font-size:14.5px}
.estado{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13.5px;color:var(--muted);margin:0}
.estado span::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--bueno);margin-right:6px;vertical-align:1px}
.estado span.atrasado{color:var(--fg);font-weight:600} .estado span.atrasado::before{background:var(--medio)}
.estado span.sin::before{background:var(--sin)}
.vacio{color:var(--muted)}
:root{--lluvia:#3b7dd8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--lluvia:#6fa6f0}}
:root[data-theme="dark"]{--lluvia:#6fa6f0}
.ahora .cielo-txt{display:flex;align-items:center;gap:8px;font-size:17px;font-weight:600}
.hora .ic{display:flex;justify-content:center;min-height:26px}
.q-fila .ic{display:flex;justify-content:center}
@media (max-width:560px){.ahora .temp{font-size:58px} .q-fila{grid-template-columns:4.2em 26px 3em 2.4em 1fr 2.4em;font-size:14px} .q-fila .vi{display:none}}
"""

CSS = CSS + CSS_ICONOS


JS = r"""
<script>
(function(){
  const LISTA = window.COMUNAS, DIA = ['domingo','lunes','martes','miércoles','jueves','viernes','sábado'], DIA3 = ['dom','lun','mar','mié','jue','vie','sáb'];
  const n = (v, d=0) => v == null ? '–' : Number(v).toLocaleString('es-CL', {minimumFractionDigits:d, maximumFractionDigits:d}).replace('-', '−');
  const sinTilde = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const fecha = s => { const [f, h] = s.split('T'); const [a, m, d] = f.split('-').map(Number); return {f, h: Number((h || '00').slice(0, 2)), d: new Date(a, m - 1, d)}; };
  const ICO = {gota: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5c3.2 4.3 5.5 7.4 5.5 10.2a5.5 5.5 0 0 1-11 0c0-2.8 2.3-5.9 5.5-10.2z"/></svg>',
               viento: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8"/></svg>',
               sol: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'};
  let D48 = null, D15 = null, sel = null;
""" + ICONOS_JS + r"""
  const $ = id => document.getElementById(id);

  // ---- buscador ----
  const inp = $('buscar'), ul = $('resultados');
  let activo = -1, hits = [];
  function render() {
    ul.innerHTML = hits.map((c, i) => `<li role="option" aria-selected="${i === activo}" data-id="${c.id}"><span>${c.n}</span><span class="r">${c.r}</span></li>`).join('');
    ul.hidden = !hits.length;
  }
  inp.addEventListener('input', () => {
    const q = sinTilde(inp.value.trim());
    hits = q ? LISTA.filter(c => sinTilde(c.n).includes(q) || sinTilde(c.r).includes(q)).sort((a, b) => (sinTilde(b.n).startsWith(q) - sinTilde(a.n).startsWith(q)) || (b.p - a.p)).slice(0, 8) : [];
    activo = hits.length ? 0 : -1; render();
  });
  inp.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowDown') { activo = Math.min(activo + 1, hits.length - 1); render(); ev.preventDefault(); }
    else if (ev.key === 'ArrowUp') { activo = Math.max(activo - 1, 0); render(); ev.preventDefault(); }
    else if (ev.key === 'Enter' && hits[activo]) { elegir(hits[activo].id); ev.preventDefault(); }
    else if (ev.key === 'Escape') { ul.hidden = true; }
  });
  ul.addEventListener('mousedown', ev => { const li = ev.target.closest('li'); if (li) { elegir(li.dataset.id); ev.preventDefault(); } });
  document.addEventListener('click', ev => { if (!ev.target.closest('.buscar')) ul.hidden = true; });
  document.querySelectorAll('.sugeridas button').forEach(b => b.addEventListener('click', () => elegir(b.dataset.id)));

  function elegir(id) {
    const c = LISTA.find(x => x.id === id); if (!c) return;
    sel = id; inp.value = ''; ul.hidden = true; hits = [];
    try { localStorage.setItem('comuna', id); } catch (e) {}
    if (location.hash.slice(1) !== id) history.replaceState(null, '', '#' + id);
    pintar();
  }

  // ---- pintar ----
  function pintar() {
    const c = LISTA.find(x => x.id === sel); if (!c) return;
    $('c-nombre').textContent = c.n; $('c-region').textContent = c.r;
    const d = D48 && D48.comunas[sel];
    pintarAhora(c, d); pintarHoras(d); pintarGrafico(d); pintarConfianza(d); pintarQuince(d); estado();
    if (window.avisosDMC) window.avisosDMC.comuna(sel, c.n);
  }
  function diasDe(pasos) {
    const hoy = new Date(); hoy.setHours(0, 0, 0, 0); const g = {};
    pasos.forEach(p => { const f = fecha(p.c); (g[f.f] = g[f.f] || {f, pasos: []}).pasos.push(p); });
    return Object.values(g).sort((a, b) => a.f.d - b.f.d).map(x => {
      const ts = x.pasos.map(p => p.t), ll = x.pasos.filter(p => p.p != null), mm = ll.reduce((s, p) => s + p.p, 0);
      return {dif: Math.round((x.f.d - hoy) / 864e5), max: Math.max(...ts), min: Math.min(...ts), mm, nm: Math.max(...x.pasos.map(p => p.nm)),
              pn: Math.max(0, ...ll.map(p => p.pn)), w: x.pasos.some(p => p.w != null) ? Math.max(...x.pasos.map(p => p.w || 0)) : null, n: x.pasos.length};
    });
  }
  function pintarAhora(c, d) {
    const o = d && d.obs, ds = d ? diasDe(d.pasos) : [], hoy = ds.find(x => x.dif === 0) || ds[0] || null, q = quinceHoy();
    $('ahora-temp').innerHTML = o ? `${n(o.t)}<small>°C</small>` : (hoy ? `${n(hoy.max)}<small>° máx.</small>` : '–');
    const p0 = d && d.pasos.length ? d.pasos[0] : null, c0 = p0 ? CIELO_P(p0, fecha(p0.c).h) : null;
    $('ahora-cielo').innerHTML = c0 ? `${icono(c0, 34)}<span>${c0.t}</span>` : '';
    $('ahora-fuente').textContent = o ? `Medido a las ${o.hora} en ${o.nombre}${o.km > 2 ? ', a ' + n(o.km) + ' km' : ''}` : 'Sin estación cerca que mida ahora; se muestra el pronóstico';
    const max = q ? q.tmax[1] : (hoy ? hoy.max : null), min = q ? q.tmin[1] : (hoy ? hoy.min : null);
    $('hoy-max').textContent = n(max) + '°'; $('hoy-min').textContent = n(min) + '°';
    const mm = hoy ? hoy.mm : (q ? q.ll[0] : 0), prob = q ? q.p1 : null;
    $('hoy-lluvia').className = mm >= 1 ? 'llueve' : '';
    $('hoy-lluvia').innerHTML = ICO.gota + (mm >= 1 ? `<strong>${n(mm, mm < 10 ? 1 : 0)} mm</strong> hoy` + (prob != null ? ` · ${n(prob)} % de probabilidad` : (hoy && hoy.pn ? ` · lo anuncian ${hoy.pn} de ${hoy.nm} modelos` : '')) : 'Sin lluvia importante hoy');
    $('hoy-viento').innerHTML = ICO.viento + `Viento hasta ${n(hoy ? hoy.w : (q ? q.v[1] : null))} km/h`;
    pintarTormenta(d);
  }
  // Tormentas en las próximas 72 h: por día, desde los ingredientes de GFS (inestabilidad, tapa, disparador y cizalle).
  function pintarTormenta(d) {
    const box = $('tormenta-72'), tr = (d && d.tr72) || []; box.hidden = !tr.length; if (!tr.length) return;
    const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
    const dia = x => { const f = new Date(x.f + 'T12:00'), k = Math.round((f - hoy) / 864e5) ; return k === 0 ? 'hoy' : k === 1 ? 'mañana' : DIA3[f.getDay()].toLowerCase() + ' ' + f.getDate(); };
    const franja = x => x.desde === x.hasta ? `cerca de las ${x.desde} h` : `entre las ${x.desde} y las ${x.hasta} h`;
    const fuerte = tr.some(x => x.n >= 2);
    box.className = 'tormenta-72' + (fuerte ? ' fuerte' : '');
    box.innerHTML = `${icono({k: fuerte ? 'tormenta-f' : 'tormenta', t: 'Tormentas'}, 22)} <strong>${fuerte ? 'Tormentas, algunas fuertes, posibles' : 'Tormentas posibles'}</strong>: ` +
      tr.map(x => `${dia(x)} ${franja(x)}${x.n >= 2 ? ' (fuertes posibles)' : ''}`).join('; ') +
      `. <span class="muted">Es el ambiente que ve el modelo a 25 km, no el lugar exacto de cada tormenta; si se forma una, el satélite la sigue en <a href="envivo.html">En vivo</a>. <a href="metodo.html#tormentas">Cómo se calcula</a>.</span>`;
  }
  function pintarHoras(d) {
    const box = $('horas');
    if (!d || !d.pasos.length) { box.innerHTML = '<p class="vacio">Sin pronóstico de 48 horas para esta comuna todavía.</p>'; return; }
    let ultDia = '';
    box.innerHTML = d.pasos.map(p => { const f = fecha(p.c), nuevo = f.f !== ultDia; ultDia = f.f;
      return `<div class="hora"><div class="d">${nuevo ? DIA3[f.d.getDay()] + ' ' + f.d.getDate() : '&nbsp;'}</div><div class="h">${String(f.h).padStart(2, '0')}:00</div><div class="ic">${icono(CIELO_P(p, f.h))}</div>
        <div class="t">${n(p.t)}°</div><div class="ll ${p.p >= 0.5 ? 'si' : ''}">${p.p == null ? '' : p.p >= 0.5 ? n(p.p, 1) + ' mm' : 'seco'}</div><div class="v">${p.w == null ? '' : n(p.w) + ' km/h'}</div></div>`; }).join('');
  }
  function pintarGrafico(d) {
    const caja = $('graf'); caja.innerHTML = ''; if (!d || d.pasos.length < 2) return;
    const pasos = d.pasos, W = 720, H = 268, ml = 34, mr = 10, mt = 22, hT = 150, gap = 40, hP = 48;
    const xs = pasos.map(p => fecha(p.c)), T = f => f.d.getTime() + f.h * 36e5, t0 = T(xs[0]), t1 = T(xs[xs.length - 1]);
    const X = i => ml + (W - ml - mr) * ((T(xs[i]) - t0) / Math.max(t1 - t0, 1));
    const lo = Math.floor(Math.min(...pasos.map(p => p.tmin)) - 1), hi = Math.ceil(Math.max(...pasos.map(p => p.tmax)) + 1);
    const Y = v => mt + hT * (1 - (v - lo) / Math.max(hi - lo, 1));
    const pmax = Math.max(5, ...pasos.map(p => p.p || 0)), yP0 = mt + hT + gap + hP, YP = v => yP0 - hP * v / pmax;
    let o = ''; const paso = (hi - lo) > 12 ? 5 : (hi - lo) > 6 ? 2 : 1;
    for (let v = Math.ceil(lo / paso) * paso; v <= hi; v += paso) o += `<line class="grid" x1="${ml}" x2="${W - mr}" y1="${Y(v)}" y2="${Y(v)}"/><text class="eje" x="${ml - 6}" y="${Y(v) + 4}" text-anchor="end">${n(v)}°</text>`;
    const primeros = {}; xs.forEach((f, i) => { if (!(f.f in primeros)) primeros[f.f] = i; });
    Object.values(primeros).forEach(i => { const f = xs[i]; if (i > 0) o += `<line class="sep" x1="${X(i)}" x2="${X(i)}" y1="${mt - 14}" y2="${yP0}"/>`; o += `<text class="eje" x="${X(i) + 4}" y="${mt - 6}">${DIA3[f.d.getDay()]} ${f.d.getDate()}</text>`; });
    o += `<path class="banda" d="M${pasos.map((p, i) => `${X(i)},${Y(p.tmax)}`).join('L')}L${pasos.map((p, i) => `${X(i)},${Y(p.tmin)}`).reverse().join('L')}Z"/>`;
    o += `<path class="lin" d="M${pasos.map((p, i) => `${X(i)},${Y(p.t)}`).join('L')}"/>`;
    pasos.forEach((p, i) => o += `<circle class="pt" cx="${X(i)}" cy="${Y(p.t)}" r="3.5"/>`);
    const iMax = pasos.reduce((a, p, i) => p.t > pasos[a].t ? i : a, 0), iMin = pasos.reduce((a, p, i) => p.t < pasos[a].t ? i : a, 0);
    [iMax, iMin].forEach(i => o += `<text class="etq" x="${X(i)}" y="${Y(pasos[i].t) + (i === iMax ? -9 : 18)}" text-anchor="middle">${n(pasos[i].t)}°</text>`);
    o += `<text class="eje" x="${ml - 6}" y="${yP0 - hP + 4}" text-anchor="end">${n(pmax)}</text><text class="eje" x="${ml - 6}" y="${yP0 + 4}" text-anchor="end">0</text>`;
    o += `<text class="eje" x="${ml}" y="${yP0 - hP - 10}">Lluvia, en mm cada 6 h</text><line class="grid" x1="${ml}" x2="${W - mr}" y1="${yP0}" y2="${yP0}"/>`;
    const bw = Math.max(6, (W - ml - mr) / pasos.length * 0.5);
    pasos.forEach((p, i) => { if (p.p > 0.05) o += `<rect class="barra" x="${X(i) - bw / 2}" y="${YP(p.p)}" width="${bw}" height="${yP0 - YP(p.p)}" rx="3"/>`; });
    pasos.forEach((p, i) => { o += `<text class="eje" x="${X(i)}" y="${yP0 + 14}" text-anchor="middle">${String(xs[i].h).padStart(2, '0')}h</text>`;
      const a = i ? (X(i) + X(i - 1)) / 2 : ml, b = i < pasos.length - 1 ? (X(i) + X(i + 1)) / 2 : W - mr;
      o += `<rect class="hit" data-i="${i}" x="${a}" y="${mt}" width="${b - a}" height="${yP0 - mt}"/>`; });
    o += `<line class="guia" id="guia" x1="0" x2="0" y1="${mt}" y2="${yP0}" visibility="hidden"/>`;
    caja.innerHTML = `<svg viewBox="0 0 ${W} ${H + 8}" role="img" aria-label="Temperatura y lluvia de las próximas 48 horas">${o}</svg>`;
    const svg = caja.querySelector('svg'), t = document.createElement('div'); t.className = 'tip'; t.hidden = true; caja.style.position = 'relative'; caja.appendChild(t);
    const guia = svg.querySelector('#guia');
    svg.querySelectorAll('.hit').forEach(r => {
      const mostrar = () => { const i = +r.dataset.i, p = pasos[i], f = xs[i], x = +r.getAttribute('x') + +r.getAttribute('width') / 2;
        guia.setAttribute('x1', X(i)); guia.setAttribute('x2', X(i)); guia.setAttribute('visibility', 'visible');
        t.innerHTML = `<b>${DIA[f.d.getDay()]} ${f.d.getDate()}, ${String(f.h).padStart(2, '0')}:00</b>${n(p.t, 1)} °C <span class="muted">(modelos: ${n(p.tmin, 1)} a ${n(p.tmax, 1)})</span><br>` +
          (p.p != null ? `Lluvia: ${n(p.p, 1)} mm${p.ph ? ' en ' + p.ph + ' h' : ''}<br>` : '') + (p.w != null ? `Viento: ${n(p.w)} km/h` : '');
        t.hidden = false; const bw2 = caja.clientWidth, px = x / W * bw2; t.style.left = Math.min(Math.max(px - 80, 0), bw2 - 170) + 'px'; t.style.top = '0px'; };
      r.addEventListener('mouseenter', mostrar); r.addEventListener('click', mostrar);
      r.addEventListener('mouseleave', () => { t.hidden = true; guia.setAttribute('visibility', 'hidden'); });
    });
  }
  function pintarConfianza(d) {
    const e = d && d.est, box = $('confianza');
    if (!e) { box.innerHTML = '<strong>Qué tan confiable es aquí:</strong> no hay un aeródromo en el mismo cuadrado de 25 km que permita medir el error del modelo en esta comuna, así que este pronóstico va sin ajuste local.'; return; }
    const aj = d.pasos.reduce((s, x) => s + x.aj, 0), tot = d.pasos.reduce((s, x) => s + x.nm, 0);
    box.innerHTML = `<strong>Qué tan confiable es aquí:</strong> se ajusta con lo medido en ${e.nombre}, a ${n(e.km)} km, en el mismo cuadrado de 25 km del modelo` +
      (e.g != null ? `, donde en 2026 el pronóstico de temperatura para el día siguiente se equivocó en promedio ${n(e.g, 1)} °C` + (e.c != null ? ` y ${n(e.c, 1)} °C con el ajuste.` : '.') : '.') +
      (aj < tot ? ` Esta vez se pudo ajustar ${aj} de ${tot} valores.` : '') + (e.g >= 2.5 ? ' Es de los lugares donde más se equivocan los modelos globales: tómalo con cautela.' : '');
  }
  function quinceHoy() { const q = D15 && D15.comunas[sel]; if (!q) return null; const hoy = new Date(); const f = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`; return q.find(x => x.f === f) || null; }
  function pintarQuince(d) {
    const box = $('quince'), q = D15 && D15.comunas[sel];
    if (!q || !q.length) { box.innerHTML = '<p class="vacio">Los 15 días se calculan una vez al día; todavía no están para esta comuna.</p>'; $('quince-pie').textContent = ''; return; }
    const aj = d && d.aj15 ? d.aj15 : {}, bx = aj.tmax || 0, bn = aj.tmin || 0;
    const dias = q.map(x => ({f: fecha(x.f), tx: x.tmax.map(v => v - bx), tn: x.tmin[1] == null ? null : x.tmin.map(v => v - bn), p1: x.p1, ll: x.ll, v: x.v, nub: x.nub}));
    const lo = Math.floor(Math.min(...dias.map(x => x.tn ? x.tn[0] : x.tx[0]))), hi = Math.ceil(Math.max(...dias.map(x => x.tx[2])));
    const pos = v => 100 * (v - lo) / Math.max(hi - lo, 1);
    const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
    box.innerHTML = dias.map(x => { const dif = Math.round((x.f.d - hoy) / 864e5), nom = dif === 0 ? 'Hoy' : dif === 1 ? 'Mañana' : DIA3[x.f.d.getDay()][0].toUpperCase() + DIA3[x.f.d.getDay()].slice(1);
      const a = x.tn ? x.tn[0] : x.tx[0], b = x.tx[2], a2 = x.tn ? x.tn[1] : x.tx[1], b2 = x.tx[1];
      return `<div class="q-fila"><div class="dia">${nom}<small>${x.f.d.getDate()}/${x.f.d.getMonth() + 1}</small></div><div class="ic">${icono(CIELO(x.nub, x.ll[0], 15), 22)}</div>
        <div class="pl ${x.p1 >= 30 ? 'si' : ''}">${x.p1 >= 10 ? ICO.gota + n(x.p1) + '%' : ''}</div>
        <div class="mn">${x.tn ? n(x.tn[1]) + '°' : '–'}</div>
        <div class="rango" title="Entre ${n(a)} y ${n(b)} °C en el 80 % de los escenarios"><i class="amplio" style="left:${pos(a)}%;right:${100 - pos(b)}%"></i><i class="centro" style="left:${pos(a2)}%;right:${100 - pos(b2)}%"></i></div>
        <div class="mx">${n(x.tx[1])}°</div><div class="vi">${n(x.v[1])} km/h</div></div>`; }).join('');
    $('quince-pie').textContent = `Corrida del ensamble: ${D15.corrida.replace('T', ' ').replace('Z', ' UTC')}. Cada barra va de la mínima a la máxima; la parte clara muestra entre qué valores quedan el 80 % de los ${D15.miembros} escenarios. ` +
      `La probabilidad de lluvia es la parte de los escenarios con 1 mm o más en el día.` + (bx || bn ? ' Máximas y mínimas ajustadas con el error local de la tarde y la madrugada.' : '');
  }

  // ---- estado: a qué hora es cada dato, y en ámbar si está atrasado ----
  function estado() {
    const d = D48 && D48.comunas[sel], ahora = Date.now(), partes = [];
    const edad = s => { const [f, h] = s.split('T'); const [a, m, dd] = f.split('-').map(Number); const [hh, mi] = h.split(':').map(Number); return (ahora - new Date(a, m - 1, dd, hh, mi)) / 36e5; };
    const hace = e => e < 1 ? `hace ${Math.round(e * 60)} min` : `hace ${n(e, e < 10 ? 1 : 0)} h`;
    if (d && d.obs) partes.push(`<span>Medición: ${d.obs.hora} en ${d.obs.nombre}</span>`);
    else partes.push('<span class="sin">Sin medición cercana reciente</span>');
    if (D48) { const e = edad(D48.generado); partes.push(`<span class="${e > 8 ? 'atrasado' : ''}">Pronóstico 48 h: ${D48.generado.slice(11)} (${hace(e)})${e > 8 ? ' · atrasado' : ''}</span>`); }
    else partes.push('<span class="sin">Pronóstico 48 h: sin datos</span>');
    if (D15) { const c = D15.corrida.replace('Z', ''); const e = (ahora - new Date(c + 'Z')) / 36e5; partes.push(`<span class="${e > 36 ? 'atrasado' : ''}">15 días: corrida del ${c.slice(8, 10)}/${c.slice(5, 7)} ${c.slice(11, 16)} UTC${e > 36 ? ' · atrasada' : ''}</span>`); }
    else partes.push('<span class="sin">15 días: sin datos</span>');
    $('estado').innerHTML = partes.join('');
  }

  // ---- arranque ----
  const inicial = location.hash.slice(1) || (function(){ try { return localStorage.getItem('comuna'); } catch (e) { return null; } })() || 'Q188002';
  sel = LISTA.find(x => x.id === inicial) ? inicial : 'Q188002';
  pintar();
  fetch('datos/pronostico_48h.json?t=' + Math.floor(Date.now() / 3e5)).then(r => r.ok ? r.json() : null).then(j => { D48 = j; if (j) $('actualizado').textContent = `Pronóstico del ${j.generado.replace('T', ' ')} (hora de Chile), con la última corrida de ${j.modelos.join(', ')}.`; pintar(); }).catch(() => {});
  fetch('datos/pronostico_15d.json?t=' + Math.floor(Date.now() / 36e5)).then(r => r.ok ? r.json() : null).then(j => { D15 = j; pintar(); }).catch(() => {});
  window.addEventListener('hashchange', () => { const id = location.hash.slice(1); if (LISTA.find(x => x.id === id)) { sel = id; pintar(); } });
})();
</script>"""


def pagina(head, escribir, est, pts, ahora):
    com = pd.read_csv(os.path.join(AQUI, "comunas.csv"))
    d48 = datos_48h(est, pts, ahora)
    carpeta = os.path.join(AQUI, "..", "site", "datos"); os.makedirs(carpeta, exist_ok=True)
    if d48:
        json.dump(d48, open(os.path.join(carpeta, "pronostico_48h.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    lista = json.dumps([{"id": r.id, "n": r.nombre, "r": r.region, "p": int(r.pob)} for r in com.itertuples(index=False)], ensure_ascii=False)
    sugeridas = "".join(f'<button type="button" data-id="{r.id}">{r.nombre}</button>' for r in com.sort_values("pob", ascending=False).head(8).itertuples(index=False))
    html = f"""{head("Pronóstico · Earth-2 Chile", "El tiempo que viene en tu comuna: ahora, las próximas 48 horas y 15 días, con los modelos globales ajustados con lo que se mide en Chile y con su margen de duda a la vista.")}
<body>
{nav("pronostico")}
<div class="wrap">
{tormenta_vivo.html()}
{monitor_lluvia.aviso()}
<header>
  <div class="eyebrow">Pronóstico</div>
  <h1>¿Qué tiempo viene en tu comuna?</h1>
  <p class="lead">Las próximas 48 horas y 15 días, con los modelos globales ajustados con lo que se mide en Chile. Y, a diferencia de otros pronósticos, te decimos cuánta duda hay.</p>
  <div class="buscar"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <input id="buscar" type="search" placeholder="Escribe tu comuna" autocomplete="off" aria-label="Buscar comuna" aria-controls="resultados" role="combobox" aria-expanded="false">
    <ul id="resultados" role="listbox" hidden></ul></div>
  <div class="sugeridas" aria-label="Comunas más consultadas">{sugeridas}</div>
</header>

<p class="estado" id="estado" aria-live="polite"><span class="sin">Cargando…</span></p>

{aviso_oficial.html(modo="comuna")}

<section class="card ahora" aria-live="polite">
  <div><h2 id="c-nombre"></h2><p class="muted" id="c-region"></p></div>
  <div class="top"><div class="temp" id="ahora-temp">–</div><div class="cielo-txt" id="ahora-cielo"></div>
    <div class="mm"><span>Hoy</span><span><b id="hoy-max">–</b> <span class="muted">máx.</span> &nbsp; <b id="hoy-min">–</b> <span class="muted">mín.</span></span></div></div>
  <p class="fuente" id="ahora-fuente"></p>
  <div class="hoy"><span id="hoy-lluvia"></span><span id="hoy-viento"></span></div>
  <p class="tormenta-72" id="tormenta-72" hidden></p>
</section>

<section class="card">
  <div class="sec-head"><h2>Próximas 48 horas</h2><p class="muted">Cada 6 horas, en hora de Chile. Es nuestro pronóstico: la combinación de los modelos, cada uno corregido con su error reciente donde hay un aeródromo en el mismo cuadrado de 25 km.</p></div>
  <div class="horas" id="horas"></div>
  <figure class="graf" style="margin:0"><figcaption class="small muted">La banda muestra entre qué valores quedan los distintos modelos: cuanto más ancha, más dudoso.</figcaption><div id="graf"></div></figure>
  <p class="confianza-txt" id="confianza"></p>
</section>

<section class="card">
  <div class="sec-head"><h2>15 días</h2><p class="muted">Con los 50 escenarios del ensamble de IA de ECMWF. Cada día trae su margen: no un número seco, sino entre qué valores puede quedar.</p></div>
  <div class="quince" id="quince"></div>
  <p class="q-pie" id="quince-pie"></p>
</section>

<details><summary>Cómo se arma este pronóstico</summary><div class="body">
  <p>Cada comuna recibe el valor del cuadrado de 25 km que la contiene en los modelos globales (AIFS, IFS y GFS; y los modelos de Earth-2 que corramos nosotros, cuando los haya). Si en ese cuadrado hay un aeródromo, a cada modelo le restamos el error que tuvo ahí en los últimos 30 días, a esa misma hora del día, y promediamos; el error es del cuadrado, así que no se traslada a comunas de otros cuadrados. El rango entre modelos es la banda de duda. Para 15 días usamos los 50 escenarios de AIFS-ENS: la máxima es la temperatura de las 15 h de Chile y la mínima la de las 03 h, así que son aproximadas.</p>
  <p>Lo que no sabe este pronóstico: la diferencia de altura entre tu comuna y el cuadrado de 25 km (en cordillera y costa puede ser grande), el viento de quebradas y laderas, y la nubosidad. Es lo que va a aprender el zoom a 4 km que estamos por entrenar. Este pronóstico se mide todos los días en <a href="zona.html">Tu zona</a>.</p>
  <p class="small muted" id="actualizado"></p>
</div></details>
{aviso()}
{pie(ahora)}
</div>
<script>window.COMUNAS = {lista};</script>
{JS}
{JS_DEF}
</body>
</html>
"""
    return escribir("pronostico.html", html)
