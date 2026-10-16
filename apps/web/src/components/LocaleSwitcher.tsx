"use client";

import { useLocale, useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";

export function LocaleSwitcher() {
  const t = useTranslations("Locale");
  const locale = useLocale();
  const pathname = usePathname();

  return (
    <nav aria-label={t("label")} className="locale-switcher">
      <ul>
        {routing.locales.map((l) => (
          <li key={l}>
            {l === locale ? (
              <span aria-current="true">{t(l)}</span>
            ) : (
              <Link href={pathname} locale={l} hrefLang={l}>
                {t(l)}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}
