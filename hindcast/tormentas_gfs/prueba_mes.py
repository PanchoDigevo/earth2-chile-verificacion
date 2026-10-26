"""Prueba del indicador de tormentas a 72 h (verificacion/tormentas_gfs.py) contra los METAR que informan tormenta.

Para cada día del mes toma la corrida de GFS de las 00 UTC y sus plazos de 12 a 36 h cada 3 h (de las 12 UTC del día a las
12 UTC del siguiente: tarde y noche de Chile), calcula el nivel en 11 aeródromos de Chile central y sur, y lo empareja con
los METAR de ese aeródromo: hubo tormenta si algún reporte entre 1,5 h antes y 1,5 h después trae TS (tormenta en el
aeródromo o en sus cercanías, VCTS). Guarda prueba_MES.csv; juntar.py calcula aciertos y falsas alarmas.

Corre en GitHub Actions (tormentas-gfs-prueba.yml), un mes por trabajo.
Uso: python hindcast/tormentas_gfs/prueba_mes.py 2026-01 salida/"""
import io, os, sys, urllib.request
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "verificacion"))
import tormentas_gfs  # noqa: E402

AERODROMOS = pd.DataFrame([
    ("SCVM", -32.950, -71.479), ("SCSN", -33.656, -71.615), ("SCEL", -33.393, -70.786), ("SCTB", -33.456, -70.547),
    ("SCRG", -34.174, -70.776), ("SCIC", -34.966, -71.217), ("SCCH", -36.583, -72.031), ("SCIE", -36.773, -73.063),
    ("SCGE", -37.403, -72.422), ("SCQP", -38.925, -72.648), ("SCTC", -38.766, -72.637)], columns=["id", "lat", "lon"])
IEM = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?{est}&data=wxcodes&year1={a1}&month1={m1}&day1=1"
       "&year2={a2}&month2={m2}&day2=2&tz=Etc/UTC&format=onlycomma&latlon=no&missing=empty&report_type=3&report_type=4")


def metar(mes):
    a2, m2 = (mes.year + 1, 1) if mes.month == 12 else (mes.year, mes.month + 1)
    url = IEM.format(est="&".join(f"station={i}" for i in AERODROMOS.id), a1=mes.year, m1=mes.month, a2=a2, m2=m2)
    with urllib.request.urlopen(url, timeout=300) as r:
        m = pd.read_csv(io.BytesIO(r.read()))
    m["valid"] = pd.to_datetime(m.valid)
    m["ts"] = m.wxcodes.fillna("").str.contains("TS")
    return m


def main(mes_txt, salida):
    os.makedirs(salida, exist_ok=True)
    mes = pd.Timestamp(mes_txt + "-01")
    m = metar(mes)
    filas = []
    for dia in pd.date_range(mes, mes + pd.offsets.MonthEnd(0)):
        if dia >= pd.Timestamp.now().normalize() - pd.Timedelta(days=1):
            break
        f = tormentas_gfs.calcular(dia, AERODROMOS, plazos=range(12, 37, 3))
        if not f:
            continue
        d = pd.concat(f, ignore_index=True)
        for r in d.itertuples(index=False):
            x = m[(m.station == r.id) & (m.valid > r.valid - pd.Timedelta(minutes=90)) & (m.valid <= r.valid + pd.Timedelta(minutes=90))]
            filas.append({**r._asdict(), "metar": len(x), "ts": int(x.ts.any())})
        print(dia.date(), "listo", flush=True)
    pd.DataFrame(filas).to_csv(os.path.join(salida, f"prueba_{mes_txt}.csv"), index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
