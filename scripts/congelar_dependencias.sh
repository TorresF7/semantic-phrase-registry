#!/usr/bin/env bash
# Genera backend/requirements.lock (CH-05, D-42): todas las dependencias del
# backend, directas y transitivas, de ejecución y de desarrollo.
#
# Se congela dentro de python:3.11-slim en linux/amd64, la misma plataforma de
# la imagen y de CI, también si se ejecuta desde otra máquina. torch se
# instala primero y desde el índice de CPU, en su propia llamada, igual que en
# el Dockerfile: con el índice por defecto arrastra CUDA (plan §9). Su línea no
# va al lockfile: en Linux el índice de CPU la publica como 2.14.0+cpu y en
# Windows como 2.14.0, y PyPI no tiene la +cpu, así que la restricción rompería
# la instalación local. torch ya queda fijado por el == de pyproject.toml, y
# sus dependencias sí van al lockfile (D-42).
#
# Cuándo ejecutarlo: al cambiar una versión en backend/pyproject.toml, o si una
# versión fijada deja de estar disponible en el índice. El lockfile no se
# edita a mano.
#
# Uso, desde la raíz del repositorio: bash scripts/congelar_dependencias.sh

set -euo pipefail

raiz="$(cd "$(dirname "$0")/.." && pwd)"
# En Git Bash, Docker Desktop necesita la ruta con letra de unidad (D:/...).
backend="$(cd "$raiz/backend" && (pwd -W 2>/dev/null || pwd))"
torch="$(grep -o '"torch==[^"]*"' "$raiz/backend/pyproject.toml" | tr -d '"')"
destino="$raiz/backend/requirements.lock"

# Solo se copian pyproject.toml y app/ a /tmp: la instalación editable escribe
# metadatos junto a pyproject.toml, el directorio montado es de solo lectura, y
# el resto de backend/ (el .venv local, entre otros) no hace falta.
MSYS_NO_PATHCONV=1 docker run --rm --platform linux/amd64 \
  -v "$backend:/src:ro" \
  -e PIP_DISABLE_PIP_VERSION_CHECK=1 \
  -e PIP_NO_CACHE_DIR=1 \
  -e PIP_ROOT_USER_ACTION=ignore \
  -e TORCH="$torch" \
  python:3.11-slim sh -c '
    set -e
    mkdir /tmp/backend
    cp -r /src/pyproject.toml /src/app /tmp/backend/
    cd /tmp/backend
    pip install --quiet --index-url https://download.pytorch.org/whl/cpu "$TORCH" >&2
    pip install --quiet -e ".[dev]" >&2
    echo "# Generado por scripts/congelar_dependencias.sh (CH-05, D-42). No editar a mano."
    echo "# Python 3.11, linux/amd64. Se usa con: pip install -c requirements.lock ..."
    echo "# torch no aparece: lo fija pyproject.toml y viene del índice de CPU (D-43)."
    # A un archivo y no por tubería: el sh del contenedor (dash) no tiene
    # pipefail, y un pip freeze cortado a medias pasaría por grep sin error.
    pip freeze --exclude-editable > /tmp/freeze.txt
    grep -v "^torch==" /tmp/freeze.txt
  ' > "$destino.tmp"

mv "$destino.tmp" "$destino"
echo "Escrito $destino ($(grep -vc '^#' "$destino") paquetes)."
