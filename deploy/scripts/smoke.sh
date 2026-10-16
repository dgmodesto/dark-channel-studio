#!/usr/bin/env bash
# Starts the stack and waits until /health is healthy. Usage: deploy/scripts/smoke.sh
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env
docker compose --env-file .env up -d --build
API_PORT="$(grep -E '^API_PORT=' .env | cut -d= -f2)"
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${API_PORT:-8000}/health" | grep -q '"status":"healthy"'; then
    echo "OK: platform healthy"
    exit 0
  fi
  sleep 2
done
echo "FAIL: platform did not become healthy" >&2
docker compose --env-file .env ps
exit 1
