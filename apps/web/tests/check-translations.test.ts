import { describe, expect, it } from "vitest";
// @ts-expect-error plain ESM script without types
import { checkDirectory, compareCatalogs } from "../scripts/check-translations.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

describe("translation parity", () => {
  it("passes for the real catalogs", () => {
    expect(checkDirectory(path.join(__dirname, "..", "messages"))).toEqual([]);
  });

  it("names the missing key and locale", () => {
    const problems = compareCatalogs({
      en: { A: { b: "x", c: "y" } },
      "pt-BR": { A: { b: "x" } },
    });
    expect(problems).toEqual([{ locale: "pt-BR", key: "A.c" }]);
  });

  it("detects a key removed from a catalog on disk", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "i18n-"));
    fs.writeFileSync(path.join(dir, "en.json"), JSON.stringify({ a: "1", b: "2" }));
    fs.writeFileSync(path.join(dir, "pt-BR.json"), JSON.stringify({ a: "1" }));
    expect(checkDirectory(dir)).toEqual([{ locale: "pt-BR", key: "b" }]);
  });
});
