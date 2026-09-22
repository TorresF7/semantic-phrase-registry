#!/usr/bin/env bash
# Hook Stop.
# Se ejecuta cuando el agente termina de responder.
# Verifica de forma determinista que el proyecto sigue en verde.
#
# Código de salida 2 = bloquea y devuelve el mensaje al agente para que lo
# corrija. Cualquier otro código deja pasar.
#
# Esto existe porque una instrucción en CLAUDE.md se cumple la mayoría de las
# veces; un hook se cumple siempre.
#
# Excepciones deliberadas:
#   - Si el último commit es `test(...)`, los tests en rojo NO bloquean: es la
#     fase roja del ciclo test-primero y el agente tiene que poder parar ahí
#     para preguntar o para que la persona revise los tests.
#   - Si este hook ya bloqueó una vez en este turno (`stop_hook_active`), deja
#     pasar: si no, un fallo que el agente no puede arreglar lo dejaría en bucle.

set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# --- Evitar el bucle -------------------------------------------------------
ENTRADA=$(cat 2>/dev/null || true)
case "$ENTRADA" in
  *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) exit 0 ;;
esac

PROBLEMAS=""
AVISOS=""

# --- Nada que verificar todavía -------------------------------------------
if [ ! -d backend/app ]; then
  exit 0
fi

# --- ¿Estamos en fase roja declarada? -------------------------------------
FASE_ROJA=0
if git log -1 --pretty=%s 2>/dev/null | grep -qE '^test(\(|:)'; then
  FASE_ROJA=1
fi

# --- Herramientas: si falta una y ya hay proyecto, avisar, no callar ------
falta() {
  AVISOS="${AVISOS}
[aviso] No encuentro '$1' en el PATH: esa comprobación se omitió. ¿Está activado el entorno virtual?"
}

# --- Lint ------------------------------------------------------------------
if command -v ruff >/dev/null 2>&1; then
  if ! SALIDA_RUFF=$(ruff check backend 2>&1); then
    PROBLEMAS="${PROBLEMAS}

[ruff] Hay errores de lint sin corregir:
${SALIDA_RUFF}"
  fi
else
  falta ruff
fi

# --- Tipos -----------------------------------------------------------------
if [ -f backend/pyproject.toml ]; then
  if command -v mypy >/dev/null 2>&1; then
    if ! SALIDA_MYPY=$(cd backend && mypy app 2>&1); then
      PROBLEMAS="${PROBLEMAS}

[mypy] Hay errores de tipado:
${SALIDA_MYPY}"
    fi
  else
    falta mypy
  fi
fi

# --- Tests rápidos ---------------------------------------------------------
# Solo la suite que no necesita nada levantado. Código 5 = no se recolectó
# ningún test: no es un fallo (ocurre justo después del andamiaje).
if [ -d backend/tests ]; then
  if command -v pytest >/dev/null 2>&1; then
    SALIDA_PYTEST=$(cd backend && pytest -m "not slow and not integration" -q --no-header 2>&1)
    CODIGO_PYTEST=$?
    if [ "$CODIGO_PYTEST" -ne 0 ] && [ "$CODIGO_PYTEST" -ne 5 ]; then
      if [ "$FASE_ROJA" -eq 1 ]; then
        AVISOS="${AVISOS}
[pytest] Tests en rojo, permitido porque el último commit es 'test(...)'. El siguiente commit debe dejarlos en verde."
      else
        PROBLEMAS="${PROBLEMAS}

[pytest] Hay tests en rojo:
$(printf '%s\n' "$SALIDA_PYTEST" | tail -30)"
      fi
    fi
  else
    falta pytest
  fi
fi

# --- Tests silenciados -----------------------------------------------------
if [ -d backend/tests ]; then
  SILENCIADOS=$(grep -rnE "pytest\.mark\.(skip|xfail)|@skip\b|\bxfail\(" backend/tests 2>/dev/null || true)
  if [ -n "$SILENCIADOS" ]; then
    PROBLEMAS="${PROBLEMAS}

[constitución art. 3] Hay tests silenciados. Un test no se desactiva para que
la suite pase; se corrige el test o el código:
${SILENCIADOS}"
  fi
fi

# --- Dirección de las dependencias (constitución art. 2) ------------------
# domain/ y application/ no importan adapters/ de ninguna forma, ni librerías
# de infraestructura. La búsqueda es por línea de import, así que no hace falta
# que ninguna de las dos carpetas exista todavía.
if [ -d backend/app/domain ] || [ -d backend/app/application ]; then
  FUGAS=$(grep -rnE \
    "^\s*(from|import)\s+(app\.)?adapters|^\s*from\s+app\s+import\s+.*\badapters\b|^\s*from\s+\.+\s*adapters|^\s*(from|import)\s+(fastapi|sqlalchemy|sentence_transformers|torch|psycopg|pgvector|alembic|starlette)\b" \
    backend/app/domain backend/app/application 2>/dev/null || true)
  if [ -n "$FUGAS" ]; then
    PROBLEMAS="${PROBLEMAS}

[constitución art. 2] El dominio o la aplicación importan infraestructura. La
dependencia debe entrar por un puerto:
${FUGAS}"
  fi
fi

# --- Frontend --------------------------------------------------------------
if [ -f frontend/package.json ] && [ -d frontend/src ]; then
  if command -v npx >/dev/null 2>&1 && [ -d frontend/node_modules ]; then
    if ! SALIDA_TSC=$(cd frontend && npx --no-install tsc --noEmit 2>&1); then
      PROBLEMAS="${PROBLEMAS}

[tsc] Hay errores de tipos en el frontend:
$(printf '%s\n' "$SALIDA_TSC" | tail -30)"
    fi
  else
    falta "tsc (frontend/node_modules)"
  fi
  if [ -d frontend/src/components ]; then
    FETCH=$(grep -rn "fetch(" frontend/src/components 2>/dev/null || true)
    if [ -n "$FETCH" ]; then
      PROBLEMAS="${PROBLEMAS}

[patrones] Un componente llama a fetch() directamente. Solo api/cliente.ts habla con la red:
${FETCH}"
    fi
  fi
fi

# --- Resultado -------------------------------------------------------------
if [ -n "$AVISOS" ]; then
  echo "${AVISOS}" >&2
fi

if [ -n "$PROBLEMAS" ]; then
  echo "El trabajo no puede cerrarse todavía:${PROBLEMAS}" >&2
  exit 2
fi

exit 0
