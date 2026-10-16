import { getTranslations } from "next-intl/server";

type Component = { status: "healthy" | "unhealthy"; reason?: string };
type Health = { status: "healthy" | "unhealthy"; components: Record<string, Component> };

async function fetchHealth(): Promise<Health | null> {
  const base = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${base}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(2000),
    });
    return (await res.json()) as Health;
  } catch {
    return null;
  }
}

export async function StatusCard() {
  const t = await getTranslations("Status");
  const health = await fetchHealth();

  return (
    <section aria-labelledby="status-title" className="status-card">
      <h2 id="status-title">{t("title")}</h2>
      {health === null ? (
        <p data-status="unreachable">{t("unreachable")}</p>
      ) : (
        <>
          <p data-status={health.status}>{t(health.status)}</p>
          <ul>
            {Object.entries(health.components).map(([name, c]) => (
              <li key={name} data-status={c.status}>
                {t(`component.${name}` as never)}:{" "}
                {c.status === "healthy" ? t("componentHealthy") : t("componentUnhealthy")}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
