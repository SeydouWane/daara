// Copie HTMX et les polices dans static/dist : tout est servi par DAARA,
// jamais par un CDN tiers (spec §1.3 principe 4, §10.3).
import { cpSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

const fonts = [
  ["@fontsource-variable/inter", "inter"],
  ["@fontsource-variable/space-grotesk", "space-grotesk"],
].flatMap(([pkg, family]) =>
  ["latin", "latin-ext"].map((subset) => {
    const file = `${family}-${subset}-wght-normal.woff2`;
    return [`node_modules/${pkg}/files/${file}`, `static/dist/fonts/${file}`];
  }),
);

const files = [["node_modules/htmx.org/dist/htmx.min.js", "static/dist/js/htmx.min.js"], ...fonts];

for (const [from, to] of files) {
  mkdirSync(dirname(to), { recursive: true });
  cpSync(from, to);
}
console.log(`vendor: ${files.length} fichiers copiés dans static/dist`);
