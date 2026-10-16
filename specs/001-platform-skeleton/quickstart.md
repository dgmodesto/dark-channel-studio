# Quickstart: Platform Skeleton

Target: all components healthy in under 5 minutes.

## Prerequisites
- Docker with Compose v2
- Git

## Steps
1. Clone the repository and enter it.
2. Copy the example configuration: `cp deploy/.env.example deploy/.env` (PowerShell: `Copy-Item deploy\.env.example deploy\.env`).
3. Start the platform: `docker compose -f deploy/compose.yaml --env-file deploy/.env up -d --build`.
4. Verify health: `curl http://127.0.0.1:8000/health` — expect `"status": "healthy"` and `database`, `redis`, `worker` all `healthy`.
5. Open `http://127.0.0.1:3000` — you are redirected to `/en` or `/pt-BR`; use the language switcher to change language.
6. Run the smoke test: `deploy/scripts/smoke.ps1` (or `smoke.sh`).

## Reset persisted data
`deploy/scripts/reset.ps1` (or `reset.sh`) — asks for confirmation, then removes containers and volumes.

## Validation scenarios
- Stop Postgres (`docker compose stop postgres`) and call `/health`: expect HTTP 503 with `database` unhealthy and a reason code.
- Remove a key from `messages/pt-BR.json` and run `npm run check:translations` in `apps/web`: expect failure naming the key.
- Remove `DATABASE_URL` from the env file and start the API: expect an error naming `DATABASE_URL`, not its value.
