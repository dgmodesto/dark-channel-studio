import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export function flatten(obj, prefix = "") {
  return Object.entries(obj).flatMap(([k, v]) =>
    v !== null && typeof v === "object" ? flatten(v, `${prefix}${k}.`) : [`${prefix}${k}`],
  );
}

export function compareCatalogs(catalogs) {
  const keySets = Object.fromEntries(
    Object.entries(catalogs).map(([locale, c]) => [locale, new Set(flatten(c))]),
  );
  const all = new Set(Object.values(keySets).flatMap((s) => [...s]));
  const problems = [];
  for (const [locale, keys] of Object.entries(keySets)) {
    for (const key of [...all].sort()) {
      if (!keys.has(key)) problems.push({ locale, key });
    }
  }
  return problems;
}

export function checkDirectory(dir) {
  const catalogs = {};
  for (const file of fs.readdirSync(dir).filter((f) => f.endsWith(".json"))) {
    catalogs[path.basename(file, ".json")] = JSON.parse(
      fs.readFileSync(path.join(dir, file), "utf8"),
    );
  }
  return compareCatalogs(catalogs);
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const dir = process.argv[2] ?? path.join(here, "..", "messages");
  const problems = checkDirectory(dir);
  if (problems.length > 0) {
    for (const p of problems) console.error(`Missing key "${p.key}" in locale "${p.locale}"`);
    process.exit(1);
  }
  console.log("Translation catalogs are in sync.");
}
