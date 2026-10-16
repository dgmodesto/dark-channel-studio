# Contract: Health

## `GET /health`

Returns overall and per-component status. Always returns a complete body.

- `200` — API is up and all required dependencies (`database`, `redis`) are healthy.
- `503` — at least one required dependency is unhealthy.

The `worker` component is informational: an unhealthy worker is reported but does not change the HTTP status.

```json
{
  "status": "healthy",
  "components": {
    "api":      { "status": "healthy" },
    "database": { "status": "healthy", "latency_ms": 3 },
    "redis":    { "status": "healthy", "latency_ms": 1 },
    "worker":   { "status": "healthy", "last_heartbeat": "2026-10-16T14:00:00Z" }
  }
}
```

Unhealthy component example (reason is a code, never localized text):

```json
{ "status": "unhealthy", "reason": "timeout" }
```

Reason codes: `timeout`, `connection_refused`, `error`, `no_heartbeat`.

`status` values: `healthy`, `unhealthy`. Overall `status` is `unhealthy` when any required dependency is unhealthy.

## Error envelope (all API errors)

```json
{ "code": "config.missing", "params": { "name": "DATABASE_URL" } }
```

No human-readable localized message is returned.

## Worker heartbeat

Redis key `dcs:worker:heartbeat`, ISO-8601 UTC timestamp, TTL 30 s, refreshed every 10 s.
