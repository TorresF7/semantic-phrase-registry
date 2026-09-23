# --- Etapa 1: dependencias en un entorno virtual ---------------------------
FROM python:3.11-slim AS dependencias

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Solo pyproject.toml y el lockfile: esta capa se reconstruye únicamente si
# cambian las dependencias, no cada vez que cambia el código. torch se instala
# primero y desde el índice de CPU: el de PyPI arrastra CUDA y supera los 5 GB
# (plan §9). requirements.lock fija también las transitivas (CH-05, D-42).
COPY pyproject.toml requirements.lock ./
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); print('\n'.join(d['project']['dependencies']))" > requisitos.txt \
    && grep '^torch==' requisitos.txt > torch.txt \
    && grep -v '^torch==' requisitos.txt > resto.txt \
    && pip install --index-url https://download.pytorch.org/whl/cpu -c requirements.lock -r torch.txt \
    && pip install -c requirements.lock -r resto.txt

# --- Etapa 2: imagen de ejecución ------------------------------------------
FROM python:3.11-slim

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/app/.cache/huggingface

# El directorio del caché se crea con dueño `app` ANTES de `USER app`: si no,
# el volumen nace con dueño root y la descarga del modelo falla (plan §9).
RUN useradd --create-home --uid 1000 app \
    && mkdir -p "$HF_HOME" \
    && chown -R app:app /home/app/.cache

COPY --from=dependencias /opt/venv /opt/venv

WORKDIR /srv
COPY --chown=app:app app ./app
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations

USER app
EXPOSE 8000

# El esquema se migra antes de aceptar peticiones. `exec` deja a uvicorn como
# proceso principal para que reciba las señales de parada.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
