# Review Metadata Contract

`POST /reviews` keeps the existing review-gate request and adds:

```json
{
  "thumbnail_key": "run-123/thumbnail.svg",
  "description": "SEO description including the template's synthetic-media notice.",
  "tags": ["English", "practice"],
  "synthetic_content_disclosed": true
}
```

The generated title continues to populate `title`. Repeated submissions remain idempotent only when their complete media and SEO metadata match. The `GET /reviews` and `GET /reviews/{run_id}` responses add `thumbnail_url`, `description`, `tags`, and `synthetic_content_disclosed`. Legacy items can have `thumbnail_url: null` and `synthetic_content_disclosed: false`; such items cannot be approved until regenerated with disclosure.

`GET /reviews/{run_id}/media/thumbnail` serves the stored SVG from the confined shared media root. Its Next.js same-origin route is `/api/reviews/{run_id}/media/thumbnail`.
