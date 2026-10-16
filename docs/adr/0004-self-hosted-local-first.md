# ADR-0004: Self-hosted, local-first

- Status: Accepted

## Context
Single owner, personal tool, sensitive OAuth tokens, large media files, and a desire for low fixed cost.

## Decision
Ship as a Docker Compose stack (api, worker, web, Postgres, Redis) with media on local disk per channel/video. Secrets via `.env`/Docker secrets; OAuth tokens encrypted at rest. Scheduled publishing uses YouTube's native `publishAt`, so the machine need not be on at publish time. No multi-tenant features.

## Consequences
- Full data ownership and near-zero hosting cost.
- Backups and uptime are the owner's responsibility; storage is behind an interface so object storage can be added later.
- Security posture relies on localhost/VPN exposure by default.
