import { NextRequest } from "next/server";
import createMiddleware from "next-intl/middleware";
import { describe, expect, it } from "vitest";
import { routing } from "../src/i18n/routing";

const handle = createMiddleware(routing);

function request(path: string, acceptLanguage?: string) {
  return new NextRequest(`http://localhost:3000${path}`, {
    headers: acceptLanguage ? { "accept-language": acceptLanguage } : {},
  });
}

describe("locale negotiation", () => {
  it("redirects root to pt-BR when the browser prefers it", () => {
    const res = handle(request("/", "pt-BR,pt;q=0.9,en;q=0.8"));
    expect(res.headers.get("location")).toContain("/pt-BR");
  });

  it("redirects root to en when the browser prefers English", () => {
    const res = handle(request("/", "en-US,en;q=0.9"));
    expect(res.headers.get("location")).toContain("/en");
  });

  it("falls back to en for an unsupported language", () => {
    const res = handle(request("/", "fr-FR,fr;q=0.9"));
    expect(res.headers.get("location")).toContain("/en");
  });

  it("falls back to en when no preference is sent", () => {
    const res = handle(request("/"));
    expect(res.headers.get("location")).toContain("/en");
  });
});
