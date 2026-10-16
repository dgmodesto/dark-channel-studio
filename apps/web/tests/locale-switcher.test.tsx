import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import enMessages from "../messages/en.json";

let currentPath = "/channels";
vi.mock("../src/i18n/navigation", () => ({
  usePathname: () => currentPath,
  Link: ({ href, locale, children, ...rest }: { href: string; locale: string; children: React.ReactNode }) => (
    <a href={`/${locale}${href === "/" ? "" : href}`} {...rest}>
      {children}
    </a>
  ),
}));

import { LocaleSwitcher } from "../src/components/LocaleSwitcher";

describe("LocaleSwitcher", () => {
  it("links to the same path in the other locale", () => {
    currentPath = "/channels";
    render(
      <NextIntlClientProvider locale="en" messages={enMessages}>
        <LocaleSwitcher />
      </NextIntlClientProvider>,
    );
    expect(screen.getByRole("link", { name: "Português (Brasil)" })).toHaveAttribute(
      "href",
      "/pt-BR/channels",
    );
    expect(screen.getByText("English")).toHaveAttribute("aria-current", "true");
  });
});
