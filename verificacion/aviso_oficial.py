"""Aviso de una alerta oficial vigente (SENAPRED o DMC), arriba del Resumen y de Tu zona.

El texto y la fecha de vencimiento viven en site/aviso_oficial.json, que se edita a mano cuando hay una alerta
oficial (fuente: senapred.cl/alertas y meteochile.gob.cl). Pasada la fecha "vigente_hasta", el aviso deja de
mostrarse solo, en la siguiente actualización del sitio. Quebradas lo lee directamente en el navegador.
Este proyecto no emite alertas: solo informa y enlaza las oficiales."""
import datetime as dt
import json
import os

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "aviso_oficial.json")

CSS = """
.aviso-oficial{border:1px solid var(--medio);border-left:6px solid var(--medio);background:color-mix(in srgb,var(--medio) 12%,var(--surface));
  border-radius:var(--radius);padding:14px 16px;display:grid;gap:6px}
.aviso-oficial strong.t{font-family:var(--font-display);font-size:17px}
.aviso-oficial p{max-width:80ch;margin:0}
.aviso-oficial .enlaces{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:15px}
"""


def leer():
    try:
        a = json.load(open(RUTA, encoding="utf-8"))
        if dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(a["vigente_hasta"]):
            return a
    except Exception:
        pass
    return None


def html(extra=""):
    a = leer()
    if not a:
        return ""
    enlaces = "".join(f'<a href="{e["url"]}" rel="noopener">{e["texto"]}</a>' for e in a.get("enlaces", []))
    return (f'<section class="aviso-oficial" role="status" aria-label="Alerta oficial vigente"><strong class="t">{a["titulo"]}</strong>'
            f'<p>{a["texto"]}</p>{extra}<div class="enlaces">{enlaces}</div></section>')
