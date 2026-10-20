# Contenedor para correr modelos globales de Earth-2 en una L40S del POD (tarea 5).
# Base: el mismo contenedor de PhysicsNeMo que se usará para entrenar CorrDiff-Chile (trae PyTorch con CUDA).
# Construir desde la raíz del repo:  docker build -f earth2/pod/Dockerfile -t earth2-chile-pod .
# Correr AIFS (con caché de pesos fuera del contenedor):
#   docker run --gpus 1 -v $HOME/earth2_cache:/root/.cache/earth2studio -v $HOME/earth2_datos:/datos \
#     -e EARTH2_DATOS=/datos earth2-chile-pod python earth2/correr_pod.py --modelo aifs --control
FROM nvcr.io/nvidia/physicsnemo/physicsnemo:25.11
WORKDIR /app
RUN pip install --no-cache-dir "earth2studio[data,aifs,sfno]==0.19.0" psutil
# AIFS necesita flash-attn; si la base no la trae, se compila (tarda varios minutos)
RUN python -c "import flash_attn" || pip install --no-cache-dir --no-build-isolation flash-attn
COPY earth2/ earth2/
COPY historico/estaciones.csv historico/estaciones.csv
RUN mkdir -p verificacion/data
