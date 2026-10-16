# Review API Contract

All errors use `{ "code": "...", "params": {} }`.

## Create a review item

`POST /reviews`

```json
{
  "run_id": "render-123",
  "title": "Coffee episode",
  "video_key": "render-123/render-abc123.mp4",
  "audio_keys": ["render-123/000-voice.mp3"]
}
```

Returns `201` and the persisted review item. Repeating an identical submission is idempotent; reusing a run id with different media returns `409 review.run_exists`. The render worker submits this request after writing a successful output.

## Read the review queue

- `GET /reviews` lists items newest first.
- `GET /reviews/{run_id}` reads one item.
- `GET /reviews/{run_id}/media/video` streams its MP4.
- `GET /reviews/{run_id}/media/audio/{index}` streams one voice track.

Media keys are relative paths restricted to the configured shared storage root.

## Submit a decision

`POST /reviews/{run_id}/decision`

Approve:

```json
{ "decision": "approve", "notes": "" }
```

Request changes:

```json
{ "decision": "request_changes", "notes": "Correct subtitle timing." }
```

Decisions resume the persisted LangGraph thread. The result status is `approved` or `changes_requested`; change notes are preserved in the graph state and review item. Repeating the same decision is idempotent. A conflicting decision returns `409 review.already_decided`; missing notes for a change request returns `422 review.notes_required`.
