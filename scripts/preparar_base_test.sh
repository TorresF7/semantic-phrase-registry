#!/usr/bin/env bash
# Crea y migra la base de los tests de integración (banco_frases_test).
#
# Idempotente: si la base ya existe, solo aplica las migraciones pendientes.
# Requiere `docker compose up -d db` y el entorno del backend activado.
#
#   bash scripts/preparar_base_test.sh

set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
usuario="${POSTGRES_USER:-banco}"
base_test="banco_frases_test"
url_test="${TEST_DATABASE_URL:-postgresql+psycopg://banco:banco@localhost:5432/${base_test}}"

cd "$raiz"

existe="$(docker compose exec -T db psql -U "$usuario" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname = '${base_test}'")"
if [[ "$existe" != "1" ]]; then
    docker compose exec -T db createdb -U "$usuario" "$base_test"
    echo "Base ${base_test} creada."
fi

# env.py lee DATABASE_URL: aquí apunta a la base de test solo para este proceso.
cd backend
DATABASE_URL="$url_test" alembic upgrade head
echo "Base ${base_test} migrada."
