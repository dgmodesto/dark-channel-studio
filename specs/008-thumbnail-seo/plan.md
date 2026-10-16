# Implementation Plan: Thumbnail and SEO

**Spec**: [spec.md](spec.md)

## Design

Keep the feature deterministic and provider-independent in `dcs-niche-templates`: validated template data defines SEO limits, disclosure text, and thumbnail colors/label/text length. The render worker derives metadata from the incoming topic and script manifest, writes an SVG thumbnail to its shared local media store, and submits metadata with the existing review item. The API persists and streams the thumbnail and exposes metadata to the bilingual review UI. Review/approval remains the only publish gate.

## Constitution Check

- I: approval remains required; metadata does not publish autonomously.
- III/IV: no provider dependency; all niche-specific rules stay in template data.
- V: pure generation/API/UI tests cover reproducibility, disclosure, escaping and review visibility.
- VI: deterministic work makes no billable provider calls.
- VII/VIII: local media storage, path-confined access, API codes and localized UI.

## Complexity Tracking

No new service or dependency. SVG is used as the deterministic image format to avoid adding an image-generation provider or runtime library.
