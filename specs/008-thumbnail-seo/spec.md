# Feature Specification: Thumbnail and SEO

**Feature Branch**: `us-008-thumbnail-seo` (board story US-008)
**Status**: Implemented

## User Story

As the channel owner, I want each rendered script to receive a repeatable template-based thumbnail and search metadata, with synthetic-media disclosure enabled by default, so the material is ready for human review before publishing.

## Acceptance Scenarios

1. Given a script topic and its niche template, when metadata is generated, then the title, description, and tags follow that template's configured limits and CTA.
2. Given the same template and topic, when a thumbnail is rendered more than once, then its SVG bytes are identical and user text is escaped.
3. Given a template with required synthetic disclosure, when metadata is generated, then its disclosure statement is present and marked disclosed.
4. Given the render worker completes, when it submits the item for review, then its thumbnail and SEO metadata are retained alongside the existing human approval gate.

## Requirements

- SEO and thumbnail generation are deterministic and use versioned niche template data; no provider call or cost event is needed.
- Synthetic-content disclosure is required by the template schema and must be included in generated description.
- Thumbnail headline text is short, escaped SVG text using template-supplied styling.
- Metadata and thumbnail are persisted with the review item and exposed through the review queue; publishing remains blocked on explicit human approval.
- API errors keep the existing stable `{code, params}` shape and the dashboard remains bilingual.
