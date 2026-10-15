"""Elementos comunes a las tres páginas del sitio (portada, histórico, quebradas): barra de navegación superior.
Se importa desde render_site.py y render_historico.py; site/quebradas.html (estática) lleva el mismo HTML y CSS copiados
de aquí. Si cambias algo, actualiza también quebradas.html."""

SECCIONES = [("hoy", "./", "Hoy"), ("historico", "historico.html", "Histórico 2025–26"), ("quebradas", "quebradas.html", "Quebradas")]

CSS_NAV = """
.topnav{position:sticky;top:0;z-index:1100;background:var(--surface);border-bottom:1px solid var(--line)}
.topnav .in{max-width:1400px;margin:0 auto;padding-inline:16px;display:flex;align-items:center;gap:16px;min-height:52px;overflow-x:auto;scrollbar-width:none}
.topnav .in::-webkit-scrollbar{display:none}
.topnav .marca{font-family:var(--font-display);font-weight:600;font-size:15px;color:var(--fg);text-decoration:none;white-space:nowrap;letter-spacing:-.01em}
.topnav .marca small{color:var(--muted);font-weight:500;font-size:13px;margin-left:8px}
.topnav .tabs{display:flex;gap:2px;margin-left:auto}
.topnav .tabs a{display:inline-flex;align-items:center;height:52px;padding:0 12px;color:var(--muted);text-decoration:none;font-weight:600;font-size:14.5px;border-bottom:3px solid transparent;white-space:nowrap}
.topnav .tabs a:hover{color:var(--fg)}
.topnav .tabs a.activa{color:var(--fg);border-bottom-color:var(--accent)}
.topnav .tabs a:focus-visible{outline:2px solid var(--accent);outline-offset:-4px;border-radius:4px}
@media (max-width:520px){.topnav .marca small{display:none}.topnav .tabs a{padding:0 9px;font-size:14px}}
"""


def nav(activa):
    tabs = []
    for clave, href, titulo in SECCIONES:
        extra = ' class="activa" aria-current="page"' if clave == activa else ""
        tabs.append(f'<a href="{href}"{extra}>{titulo}</a>')
    return ('<nav class="topnav" aria-label="Secciones del sitio"><div class="in">'
            '<a class="marca" href="./">Earth-2 Chile<small>verificación pública</small></a>'
            f'<div class="tabs">{"".join(tabs)}</div></div></nav>')
