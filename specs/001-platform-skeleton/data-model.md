# Data Model: Platform Skeleton

This story adds no domain tables. The Alembic baseline revision is empty.

## Runtime state

| Name | Store | Shape | Lifetime |
|---|---|---|---|
| `dcs:worker:heartbeat` | Redis string | ISO-8601 UTC timestamp | TTL 30 s, refreshed every 10 s |

## Configuration (environment)

| Variable | Used by | Required | Notes |
|---|---|---|---|
| `DATABASE_URL` | api, worker | yes | async Postgres URL |
| `REDIS_URL` | api, worker | yes | |
| `LOG_LEVEL` | api, worker | no | default `INFO` |
| `API_PORT` / `WEB_PORT` / `POSTGRES_PORT` / `REDIS_PORT` | compose | no | host ports, bound to 127.0.0.1 |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | postgres | yes | example values only in `.env.example` |
| `API_BASE_URL` | web | yes | |

Missing required variables abort startup with an error naming the variable, never its value.

## Translation catalogs

`apps/web/messages/en.json` and `pt-BR.json` share an identical set of flattened keys (enforced by CI).
