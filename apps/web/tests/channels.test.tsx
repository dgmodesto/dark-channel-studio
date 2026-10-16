import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import enMessages from "../messages/en.json";
import ptMessages from "../messages/pt-BR.json";
import { ChannelForm } from "../src/components/ChannelForm";
import { ChannelList } from "../src/components/ChannelList";
import type { Channel, Template } from "../src/lib/api";

const channel: Channel = {
  id: "11111111-1111-1111-1111-111111111111",
  name: "English with Ana",
  template_id: "english-a1-a2-br",
  template_version: 1,
  content_language: "en",
  created_at: "2026-10-16T12:00:00Z",
  updated_at: "2026-10-16T12:00:00Z",
};
const template: Template = {
  id: "english-a1-a2-br",
  version: 1,
  name: "English A1/A2 for Brazilian learners",
  content_language: "en",
};

function wrap(locale: "en" | "pt-BR", ui: React.ReactNode) {
  const messages = locale === "en" ? enMessages : ptMessages;
  return render(
    <NextIntlClientProvider locale={locale} messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("ChannelList", () => {
  it("lists channels with their template in English", () => {
    wrap("en", <ChannelList channels={[channel]} deleteAction={vi.fn()} />);
    expect(screen.getByText("English with Ana")).toBeInTheDocument();
    expect(screen.getByText(/english-a1-a2-br/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: enMessages.Channels.delete })).toBeInTheDocument();
  });

  it("localizes labels in pt-BR", () => {
    wrap("pt-BR", <ChannelList channels={[channel]} deleteAction={vi.fn()} />);
    expect(screen.getByRole("button", { name: ptMessages.Channels.delete })).toBeInTheDocument();
  });

  it("shows a localized empty state", () => {
    wrap("pt-BR", <ChannelList channels={[]} deleteAction={vi.fn()} />);
    expect(screen.getByText(ptMessages.Channels.empty)).toBeInTheDocument();
  });
});

describe("ChannelForm", () => {
  it("offers templates and submits the form to the action", async () => {
    const action = vi.fn().mockResolvedValue({ errorCode: null });
    wrap("en", <ChannelForm templates={[template]} action={action} />);
    fireEvent.change(screen.getByLabelText(enMessages.Channels.name), {
      target: { value: "My channel" },
    });
    expect(screen.getByRole("option", { name: template.name })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: enMessages.Channels.create }));
    await waitFor(() => expect(action).toHaveBeenCalled());
    const form = action.mock.calls[0][1] as FormData;
    expect(form.get("name")).toBe("My channel");
    expect(form.get("template_id")).toBe("english-a1-a2-br");
  });

  it("maps an API error code to a localized message", async () => {
    const action = vi.fn().mockResolvedValue({ errorCode: "channel.template_unknown" });
    wrap("pt-BR", <ChannelForm templates={[template]} action={action} />);
    fireEvent.change(screen.getByLabelText(ptMessages.Channels.name), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: ptMessages.Channels.create }));
    expect(
      await screen.findByText(ptMessages.Errors.channel.template_unknown),
    ).toBeInTheDocument();
  });

  it("falls back to a generic message for unknown codes", async () => {
    const action = vi.fn().mockResolvedValue({ errorCode: "something.new" });
    wrap("en", <ChannelForm templates={[template]} action={action} />);
    fireEvent.change(screen.getByLabelText(enMessages.Channels.name), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: enMessages.Channels.create }));
    expect(await screen.findByText(enMessages.Errors.unknown)).toBeInTheDocument();
  });
});
