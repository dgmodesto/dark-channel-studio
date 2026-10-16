#!/usr/bin/env bash
# Destroys containers AND volumes (all local data). Usage: deploy/scripts/reset.sh
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose --env-file .env down -v --remove-orphans
