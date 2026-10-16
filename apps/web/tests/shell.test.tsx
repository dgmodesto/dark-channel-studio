import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";
import enMessages from "../messages/en.json";
import ptMessages from "../messages/pt-BR.json";
import { Shell } from "../src/components/Shell";

function renderShell(locale: "en" | "pt-BR", messages: typeof enMessages) {
  return render(
    <NextIntlClientProvider locale={locale} messages={messages}>
      <Shell />
    </NextIntlClientProvider>,
  );
}

describe("Shell", () => {
  it("renders in English from the catalog", () => {
    renderShell("en", enMessages);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Dark Channel Studio");
    expect(screen.getByText(enMessages.Nav.channels)).toBeInTheDocument();
    expect(screen.getByText(enMessages.App.tagline)).toBeInTheDocument();
  });

  it("renders in Brazilian Portuguese from the catalog", () => {
    renderShell("pt-BR", ptMessages);
    expect(screen.getByText("Calendário")).toBeInTheDocument();
    expect(screen.getByText(ptMessages.App.tagline)).toBeInTheDocument();
    expect(screen.queryByText(enMessages.App.tagline)).not.toBeInTheDocument();
  });
});
