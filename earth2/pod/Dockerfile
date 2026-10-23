# Contenedor para correr modelos globales de Earth-2 en una L40S del POD (tarea 5): FCN3, SFNO o AIFS.
# Base: el mismo contenedor de PhysicsNeMo que se usará para entrenar CorrDiff-Chile (trae PyTorch optimizado con CUDA).
# Construir desde la raíz del repo:  docker build -f earth2/pod/Dockerfile -t earth2-chile-pod .
# Correr (con caché de pesos fuera del contenedor):
#   docker run --gpus 1 -v $HOME/earth2_cache:/root/.cache/earth2studio -v $HOME/earth2_datos:/datos \
#     -e EARTH2_DATOS=/datos earth2-chile-pod python earth2/correr_pod.py --modelo fcn3
FROM nvcr.io/nvidia/physicsnemo/physicsnemo:25.11
WORKDIR /app

# Candado: pip no puede reemplazar el torch de la base. Sin esto, una dependencia que pide torch sin fijar versión lo
# desinstala y baja otro de PyPI con todo CUDA (~15 GB de más). Si algo choca, la construcción falla en vez de cambiarlo.
RUN pip freeze | grep -i -E "^(torch|torchvision|torchaudio)==" > /tmp/candado.txt && cat /tmp/candado.txt

RUN pip install --no-cache-dir -c /tmp/candado.txt "earth2studio[data]==0.19.0" psutil

# makani no está en PyPI y torch-harmonics de PyPI no es el que fija Earth2Studio 0.19.0 ([tool.uv.sources]):
# se instalan desde esos commits, sin dependencias (si no, piden torch sin versión).
RUN pip install --no-cache-dir --no-deps "git+https://github.com/NVIDIA/makani.git@b38fcb2799d7dbc146fa60459f3f9823394a8bf1" \
 && pip install --no-cache-dir --no-deps --no-build-isolation "git+https://github.com/NVIDIA/torch-harmonics.git@a632ca748a12bd9f74dbc1e00653317810991f74"

# El resto de los extras fcn3, sfno y aifs, con el candado puesto.
RUN pip install --no-cache-dir -c /tmp/candado.txt "ruamel.yaml>=0.18.14" "scipy>=1.10.0" "pynvml>=12.0.0" moviepy \
    "anemoi-models==0.5.1" "earthkit-regrid==0.4.0" "ecmwf-opendata>=0.3.29"
# AIFS necesita flash-attn; si la base no la trae, se compila contra el torch de la base (tarda varios minutos)
RUN python -c "import flash_attn" || pip install --no-cache-dir --no-build-isolation -c /tmp/candado.txt flash-attn

# Comprobación: torch sigue siendo el de la base y los modelos importan
RUN python -c "import torch, makani, torch_harmonics; from earth2studio.models.px import FCN3, SFNO, AIFS; print('torch', torch.__version__, 'cuda', torch.version.cuda)" \
 && pip freeze | grep -i -E "^(torch|torchvision|torchaudio)==" | diff - /tmp/candado.txt

COPY earth2/ earth2/
COPY historico/estaciones.csv historico/estaciones.csv
RUN mkdir -p verificacion/data
