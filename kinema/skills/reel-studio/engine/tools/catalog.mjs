// Build the block catalog (references/blocks.md + blocks.json) straight from the registry,
// so the docs can never drift from the code.   node tools/catalog.mjs
import { build } from "esbuild";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const outFile = path.join(root, "out", "catalog-bundle.mjs");
fs.mkdirSync(path.dirname(outFile), { recursive: true });

// stub browser-only / asset imports so the registry can be evaluated in node
const stub = {
  name: "stub",
  setup(b) {
    b.onResolve({ filter: /\.(css|png|jpg|woff2?)$/ }, (a) => ({ path: a.path, namespace: "stub" }));
    b.onLoad({ filter: /.*/, namespace: "stub" }, () => ({ contents: "export default {}", loader: "js" }));
  },
};
await build({
  entryPoints: [path.join(root, "src", "blocks", "index.ts")],
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: outFile,
  plugins: [stub],
  jsx: "automatic",
  logLevel: "error",
  external: ["three", "react", "react-dom", "remotion", "@remotion/*", "@react-three/*", "topojson-client"],
  loader: { ".json": "json" },
});
globalThis.window = globalThis.window ?? {};
const { REGISTRY } = await import(pathToFileURL(outFile).href);
const cats = {};
for (const [id, d] of Object.entries(REGISTRY)) (cats[d.cat] ??= []).push([id, d]);
const order = ["text", "ui", "device", "social", "data", "map", "3d", "bg", "fx"];
const title = { text: "Typography & captions-adjacent", ui: "UI cards & app mockups", device: "Devices (2D)", social: "Social", data: "Data", map: "Maps", "3d": "3D scenes", bg: "Backgrounds", fx: "FX" };
let md = `# Block catalog (${Object.keys(REGISTRY).length} blocks)\n\nGenerated from \`engine/src/blocks\` by \`node tools/catalog.mjs\`. Use in spec.json as \`{ "block": "<Name>", "props": {…} }\`.\n\nLegend: **pos** default position preset · **enter** default entrance (self = animates itself) · **sfx** entrance sound · ⚑ overlay (allowed to sit on top of other blocks).\n`;
const json = [];
for (const c of order) {
  if (!cats[c]) continue;
  md += `\n## ${title[c] ?? c}\n\n`;
  for (const [id, d] of cats[c]) {
    md += `### ${id}${d.overlay ? " ⚑" : ""}\n${d.desc}\n\n`;
    md += `- pos: \`${d.pos ?? "stage"}\` · enter: \`${d.self ? "self" : d.enter ?? "theme"}\` · sfx: \`${d.sfx === undefined ? "-" : d.sfx}\`${d.events ? " · has internal sound events" : ""}\n`;
    if (d.example) md += `- example: \`${JSON.stringify({ block: id, props: d.example })}\`\n`;
    md += "\n";
    json.push({ id, cat: d.cat, desc: d.desc, pos: d.pos, overlay: !!d.overlay, example: d.example ?? null });
  }
}
const refDir = path.resolve(root, "..", "references");
fs.writeFileSync(path.join(refDir, "blocks.md"), md);
fs.writeFileSync(path.join(refDir, "blocks.json"), JSON.stringify(json, null, 1));
console.log(`catalog: ${json.length} blocks -> references/blocks.md`);
