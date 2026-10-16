type Context = { params: Promise<{ runId: string }> };

export async function GET(_: Request, { params }: Context) {
  const { runId } = await params;
  const upstream = await fetch(
    `${process.env.API_BASE_URL ?? "http://127.0.0.1:8000"}/reviews/${encodeURIComponent(runId)}/media/thumbnail`,
    { cache: "no-store" },
  );
  const headers = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  return new Response(upstream.body, { status: upstream.status, headers });
}
