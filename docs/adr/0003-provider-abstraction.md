# ADR-0003: Provider abstraction

- Status: Accepted

## Context
Models, prices and capabilities change quickly. The system must switch or mix providers (chat, TTS, image) without touching pipelines.

## Decision
Define our own protocols (`ChatModel`, `TTS`, `ImageGen`) with usage reporting. Pipelines reference **roles** (e.g. `script_writer`); configuration maps roles to `provider/model`. Adapters wrap vendor SDKs (LangChain only inside chat adapters). A decorator records `cost_event` per call. Start with OpenAI; add others via adapter + config.

## Consequences
- Vendor swaps and A/B model tests are configuration changes.
- We maintain a small adapter layer and price table.
- Provider-specific features are exposed only through optional capability flags.
