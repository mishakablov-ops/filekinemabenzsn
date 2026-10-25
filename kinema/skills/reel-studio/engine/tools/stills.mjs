// Render many stills in ONE browser session + optional contact sheet.
// node tools/stills.mjs --comp Reel --props '{"project":"demo"}' (--frames 10,40 | --seconds 0.5,2 | --every 1.5) --out DIR [--scale 0.5] [--sheet sheet.png --cols 6]
import { bundle } from "@remotion/bundler";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => (a.startsWith("--") ? [...acc, [a.slice(2), arr[i + 1] && !arr[i + 1].startsWith("--") ? arr[i + 1] : "true"]] : acc), []),
);
const comp = args.comp ?? "Reel";
const inputProps = args.props ? JSON.parse(args.props) : {};
const qaMode = args.qa === "true";
if (qaMode) inputProps.qa = true;
const qaLog = [];
const onBrowserLog = (log) => {
  const text = log.text ?? "";
  if (text.startsWith("QA ")) {
    try {
      qaLog.push(JSON.parse(text.slice(3)));
    } catch {
      qaLog.push({ raw: text });
    }
  } else if (log.type === "error") console.error("[browser]", text.slice(0, 300));
};
const out = path.resolve(args.out ?? path.join(root, "out", "stills"));
const scale = parseFloat(args.scale ?? "0.5");
fs.mkdirSync(out, { recursive: true });

const serveUrl = await bundle({ entryPoint: path.join(root, "src", "index.ts"), publicDir: path.join(root, "public") });
const browser = await openBrowser("chrome", { chromiumOptions: { gl: "angle" } });
const composition = await selectComposition({ serveUrl, id: comp, inputProps, puppeteerInstance: browser, chromiumOptions: { gl: "angle" } });
const { fps, durationInFrames } = composition;
let frames = [];
if (args.frames) frames = args.frames.split(",").map(Number);
else if (args.seconds) frames = args.seconds.split(",").map((s) => Math.round(parseFloat(s) * fps));
else {
  const every = parseFloat(args.every ?? "1");
  for (let t = every / 2; t < durationInFrames / fps; t += every) frames.push(Math.round(t * fps));
}
frames = frames.filter((f) => f >= 0 && f < durationInFrames);
const files = [];
for (const frame of frames) {
  const file = path.join(out, `f${String(frame).padStart(5, "0")}.png`);
  const before = qaLog.length;
  await renderStill({ composition, serveUrl, output: file, frame, inputProps, scale, puppeteerInstance: browser, chromiumOptions: { gl: "angle" }, overwrite: true, onBrowserLog });
  files.push(file);
  for (let k = before; k < qaLog.length; k++) if (qaLog[k].frame < 0) qaLog[k].frame = frame;
  // several measurements per frame (late-loading assets): keep only the LAST issues entry of this frame
  const iss = qaLog.slice(before).filter((q) => q.issues);
  if (iss.length > 1) {
    const keep = iss[iss.length - 1];
    for (let k = qaLog.length - 1; k >= before; k--) if (qaLog[k].issues && qaLog[k] !== keep) qaLog.splice(k, 1);
  }
  process.stdout.write(`frame ${frame} (${(frame / fps).toFixed(2)}s)${qaLog.length > before ? "  ⚠ QA" : ""}\n`);
}
await browser.close({ silent: true });
if (qaMode) {
  fs.writeFileSync(path.join(out, "qa.json"), JSON.stringify(qaLog, null, 1));
  const n = qaLog.reduce((a, q) => a + (q.issues?.length ?? 0) + (q.collisions3d?.length ?? 0) + (q.plan?.length ?? 0), 0);
  console.log(n ? `QA FAIL: ${n} issue(s) in ${qaLog.length} frame(s) -> ${path.join(out, "qa.json")}` : "QA PASS: no overlaps, no collisions, no plan errors");
  for (const q of qaLog.slice(0, 12)) console.log("  ", JSON.stringify(q).slice(0, 240));
}
if (args.sheet && files.length) {
  const cols = parseInt(args.cols ?? "6", 10);
  const rows = Math.ceil(files.length / cols);
  const list = path.join(out, "list.txt");
  const sheet = path.resolve(args.sheet);
  // label each tile with its time
  const tmpDir = path.join(out, "lab");
  fs.mkdirSync(tmpDir, { recursive: true });
  const labeled = files.map((f, i) => {
    const o = path.join(tmpDir, `l${i}.png`);
    execFileSync("ffmpeg", ["-v", "error", "-y", "-i", f, "-vf", "scale=360:-1,pad=iw+4:ih+4:2:2:black", o]);
    return o;
  });
  fs.writeFileSync(list, labeled.map((f) => `file '${f.split(path.sep).join("/")}'`).join("\n"));
  execFileSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, "-vf", `tile=${cols}x${rows}:color=0x202020`, "-frames:v", "1", sheet]);
  console.log("sheet:", sheet);
}
console.log(JSON.stringify({ fps, durationInFrames, frames }));
