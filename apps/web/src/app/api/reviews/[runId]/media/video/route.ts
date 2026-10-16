type Context = { params: Promise<{ runId: string }> };

export async function GET(request: Request, { params }: Context) {
  const { runId } = await params;
  const range = request.headers.get("range");
  const upstream = await fetch(
    `${process.env.API_BASE_URL ?? "http://127.0.0.1:8000"}/reviews/${encodeURIComponent(runId)}/media/video`,
    { headers: range ? { range } : undefined, cache: "no-store" },
  );
  const headers = new Headers();
  for (const name of ["accept-ranges", "content-length", "content-range", "content-type"]) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers });
}
