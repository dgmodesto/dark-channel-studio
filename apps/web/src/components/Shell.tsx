import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

const NAV_KEYS = ["channels", "pipeline", "calendar", "metrics"] as const;

export function Shell() {
  const t = useTranslations();
  return (
    <header className="shell">
      <h1>{t("App.name")}</h1>
      <p>{t("App.tagline")}</p>
      <nav aria-label="main">
        <ul>
          {NAV_KEYS.map((key) => (
            <li key={key}>
              {key === "channels" ? (
                <Link href="/channels">{t(`Nav.${key}`)}</Link>
              ) : (
                <span aria-disabled="true" title={t("Placeholder.comingSoon")}>
                  {t(`Nav.${key}`)}
                </span>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
