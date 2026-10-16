# ADR-0005: Internationalization (en, pt-BR) from day one

- Status: Accepted

## Context
Docs and code are English (portfolio); the owner and first audience are Brazilian. Retrofitting i18n is costly.

## Decision
Use **next-intl** with `en` and `pt-BR` catalogs, locale-prefixed routes, ICU formatting, and a CI check for missing keys. The backend returns error codes and params, not localized text. Channel **content language** is a separate setting from UI language.

## Consequences
- Every UI string goes through the catalog from the first screen.
- Small ongoing translation cost; adding locales later is catalog-only.
