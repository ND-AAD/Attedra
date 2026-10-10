#!/usr/bin/env bash
# Runs the conformance suite against a disposable PostgreSQL container.
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE="postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336"  # postgres:18 (18.6)
NAME="attedra-conformance-$$"
PORT="${ATTEDRA_PG_PORT:-55432}"
docker run --rm -d --name "$NAME" -e POSTGRES_PASSWORD=attedra -e POSTGRES_DB=attedra -p "$PORT:5432" "$IMAGE" >/dev/null
trap 'docker stop "$NAME" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 1 60); do
  if docker exec "$NAME" pg_isready -U postgres -d attedra >/dev/null 2>&1; then break; fi
  sleep 1
done
sleep 1
export ATTEDRA_DSN="postgresql://postgres:attedra@localhost:${PORT}/attedra"
export ATTEDRA_IMAGE="$IMAGE"
uv run --no-project --python 3.12 --with "psycopg[binary]==3.3.6" python conformance/run.py "$@"
