import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import enMessages from "../messages/en.json";
import ptMessages from "../messages/pt-BR.json";
import { ReviewQueue } from "../src/components/ReviewQueue";
import type { Review } from "../src/lib/api";

const review: Review = {
  run_id: "render-123",
  title: "Coffee episode",
  video_url: "/reviews/render-123/media/video",
  audio_urls: ["/reviews/render-123/media/audio/0"],
  status: "awaiting_review",
  notes: "",
  created_at: "2026-10-16T12:00:00Z",
  updated_at: "2026-10-16T12:00:00Z",
};

function wrap(locale: "en" | "pt-BR", ui: React.ReactNode) {
  const messages = locale === "en" ? enMessages : ptMessages;
  return render(
    <NextIntlClientProvider locale={locale} messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("ReviewQueue", () => {
  it("offers accessible video/audio players and localized decisions", () => {
    wrap("en", <ReviewQueue reviews={[review]} action={vi.fn()} />);
    expect(
      screen.getByLabelText(enMessages.Review.videoLabel.replace("{title}", review.title)),
    ).toHaveAttribute("controls");
    expect(
      screen.getByLabelText(enMessages.Review.audioLabel.replace("{number}", "1")),
    ).toHaveAttribute("controls");
    expect(screen.getByRole("button", { name: enMessages.Review.approve })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: enMessages.Review.requestChanges }),
    ).toBeInTheDocument();
  });

  it("submits notes when requesting changes", async () => {
    const action = vi.fn().mockResolvedValue({ error: false });
    wrap("pt-BR", <ReviewQueue reviews={[review]} action={action} />);
    fireEvent.change(screen.getByLabelText(ptMessages.Review.notesLabel), {
      target: { value: "Ajustar a legenda." },
    });
    fireEvent.click(screen.getByRole("button", { name: ptMessages.Review.requestChanges }));
    await waitFor(() => expect(action).toHaveBeenCalled());
    const data = action.mock.calls[0][1] as FormData;
    expect(data.get("run_id")).toBe("render-123");
    expect(data.get("decision")).toBe("request_changes");
    expect(data.get("notes")).toBe("Ajustar a legenda.");
  });

  it("requires change notes before submitting a request", () => {
    const action = vi.fn();
    wrap("en", <ReviewQueue reviews={[review]} action={action} />);
    fireEvent.click(screen.getByRole("button", { name: enMessages.Review.requestChanges }));
    expect(screen.getByRole("alert")).toHaveTextContent(enMessages.Review.notesRequired);
    expect(action).not.toHaveBeenCalled();
  });

  it("shows a localized empty state", () => {
    wrap("pt-BR", <ReviewQueue reviews={[]} action={vi.fn()} />);
    expect(screen.getByText(ptMessages.Review.empty)).toBeInTheDocument();
  });

  it("reports a media loading error", () => {
    wrap("en", <ReviewQueue reviews={[review]} action={vi.fn()} />);
    fireEvent.error(
      screen.getByLabelText(enMessages.Review.videoLabel.replace("{title}", review.title)),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(enMessages.Review.mediaError);
  });
});
