#!/usr/bin/env bash
# Hook PostToolUse (Edit|Write|MultiEdit).
# Formatea y corrige automáticamente SOLO el archivo que se acaba de editar.
# No bloquea nunca: su trabajo es ahorrar ruido, no interrumpir.
#
# Por qué solo ese archivo y no todo el proyecto: si tras cada edición se
# corrigiera todo backend/, entre dos ediciones consecutivas ruff borraría un
# import que todavía no se usa (F401) y reformatearía archivos que el agente
# ya leyó, obligándolo a releerlos. Por lo mismo F401 queda fuera del --fix.

set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# El hook recibe por stdin un JSON con tool_input.file_path. Se extrae sin
# depender de jq, que puede no estar instalado.
ENTRADA=$(cat 2>/dev/null || true)
# Las barras de Windows llegan escapadas como \\ dentro del JSON; se pasan a /.
ARCHIVO=$(printf '%s' "$ENTRADA" \
  | sed -nE 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' \
  | head -1 \
  | tr '\\\\' '/' \
  | sed -E 's|//+|/|g')

[ -n "$ARCHIVO" ] && [ -f "$ARCHIVO" ] || exit 0

case "$ARCHIVO" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      ruff format "$ARCHIVO" >/dev/null 2>&1
      ruff check --fix --unfixable F401 "$ARCHIVO" >/dev/null 2>&1
    fi
    ;;
  *.ts|*.tsx|*.css)
    if [ -f frontend/package.json ] && [ -d frontend/node_modules ] && command -v npx >/dev/null 2>&1; then
      (cd frontend && npx --no-install prettier --write "$ARCHIVO" >/dev/null 2>&1)
    fi
    ;;
esac

exit 0
