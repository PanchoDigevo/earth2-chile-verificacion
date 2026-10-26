"""Elección acotada de la última corrida completa de un modelo, común a fetch_aifs, fetch_ifs y fetch_gfs.

Nunca se usa Client.latest(): mientras un centro publica una corrida, su bucket responde 503 o 404
y los clientes reintentan durante horas. Aquí se pregunta con HEAD (20 s) por el índice del primer
y del último plazo; si ambos responden 200, la corrida está completa."""
import datetime as dt, sys, urllib.request

STEPS = [0, 6, 12, 18, 24, 30, 36, 42, 48]   # cada 6 h hasta 48 h: el pronóstico de Tu zona muestra dos días completos


def existe(url, timeout=20):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def disponible(run, url_indice):
    """True si los índices del primer y del último plazo de la corrida responden 200."""
    return all(existe(url_indice(run, step)) for step in (STEPS[0], STEPS[-1]))


def ultima_corrida(nombre, url_indice, intentos=8):
    """Recorre las corridas 6-horarias hacia atrás (8 intentos = 2 días) y devuelve la primera completa."""
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    run = now.replace(hour=(now.hour // 6) * 6, minute=0, second=0, microsecond=0)
    for _ in range(intentos):
        if disponible(run, url_indice):
            return run
        print(f"{nombre}: corrida {run:%Y-%m-%d %Hz} no disponible aún")
        run -= dt.timedelta(hours=6)
    raise SystemExit(f"ninguna corrida {nombre} completa en los últimos 2 días")


def corrida_pedida(nombre, url_indice, argv=sys.argv):
    """Corrida desde la línea de comandos (fecha, hora UTC) o la última completa."""
    if len(argv) >= 3:
        return dt.datetime.strptime(argv[1], "%Y-%m-%d").replace(hour=int(argv[2]))
    return ultima_corrida(nombre, url_indice)
