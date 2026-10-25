// Phone-size screenshots of the shop (any URL) with the engine's headless Chrome.
//   node shots.mjs <url> <outDir> [y1,y2,...]      (run from reel-studio/engine so @remotion/renderer resolves)
import { openBrowser } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";

const [url, out = "shots", ys = "0"] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const browser = await openBrowser("chrome", { chromiumOptions: { gl: "angle" } });
const page = await browser.newPage(() => null, () => null);
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
await page.goto({ url, timeout: 60000 });
await new Promise((r) => setTimeout(r, 3500));
for (const y of ys.split(",").map(Number)) {
  await page.evaluate(`window.scrollTo(0, ${y}); window.dispatchEvent(new Event('scroll')); 1`);
  await new Promise((r) => setTimeout(r, 1500));
  const file = path.join(out, `shop-${String(y).padStart(4, "0")}.png`);
  const { value } = await page._client().send("Page.captureScreenshot", { format: "png" });
  const data = value.data;
  fs.writeFileSync(file, Buffer.from(data, "base64"));
  console.log(file);
}
await browser.close({ silent: true });
