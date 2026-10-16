export type Channel = {
  id: string;
  name: string;
  template_id: string;
  template_version: number;
  content_language: string;
  created_at: string;
  updated_at: string;
};

export type Template = {
  id: string;
  version: number;
  name: string;
  content_language: string;
};

export type Review = {
  run_id: string;
  title: string;
  video_url: string;
  audio_urls: string[];
  status: "awaiting_review" | "approved" | "changes_requested";
  notes: string;
  created_at: string;
  updated_at: string;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; code: string };

function baseUrl() {
  return process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
}

async function call<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${baseUrl()}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
      ...init,
    });
    if (res.status === 204) return { ok: true, data: undefined as T };
    const body = await res.json();
    if (!res.ok) return { ok: false, code: String(body?.code ?? "http.unknown") };
    return { ok: true, data: body as T };
  } catch {
    return { ok: false, code: "api.unreachable" };
  }
}

export const listChannels = () => call<Channel[]>("/channels");
export const listTemplates = () => call<Template[]>("/templates");
export const listReviews = () => call<Review[]>("/reviews");
export const decideReview = (
  runId: string,
  decision: "approve" | "request_changes",
  notes: string,
) =>
  call<Review>(`/reviews/${encodeURIComponent(runId)}/decision`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ decision, notes }),
  });
export const createChannel = (name: string, templateId: string) =>
  call<Channel>("/channels", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name, template_id: templateId }),
  });
export const deleteChannel = (id: string) =>
  call<void>(`/channels/${encodeURIComponent(id)}`, { method: "DELETE" });
