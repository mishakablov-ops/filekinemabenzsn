// Local fonts (no network at render time). Every family below has Cyrillic.
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/inter/800.css";
import "@fontsource/inter-tight/500.css";
import "@fontsource/inter-tight/600.css";
import "@fontsource/inter-tight/700.css";
import "@fontsource/inter-tight/800.css";
import "@fontsource/inter-tight/900.css";
import "@fontsource/inter-tight/800-italic.css";
import "@fontsource/playfair-display/400-italic.css";
import "@fontsource/playfair-display/500-italic.css";
import "@fontsource/playfair-display/600-italic.css";
import "@fontsource/playfair-display/700-italic.css";
import "@fontsource/playfair-display/800-italic.css";
import "@fontsource/playfair-display/700.css";
import "@fontsource/playfair-display/900.css";
import "@fontsource/lora/500-italic.css";
import "@fontsource/lora/600-italic.css";
import "@fontsource/unbounded/500.css";
import "@fontsource/unbounded/700.css";
import "@fontsource/unbounded/800.css";
import "@fontsource/unbounded/900.css";
import "@fontsource/onest/400.css";
import "@fontsource/onest/500.css";
import "@fontsource/onest/600.css";
import "@fontsource/onest/700.css";
import "@fontsource/onest/800.css";
import "@fontsource/onest/900.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/700.css";
import "@fontsource/manrope/800.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "@fontsource/jetbrains-mono/700.css";
import "@fontsource/press-start-2p/400.css";


export const F = {
  ui: "Inter, system-ui, sans-serif",
  display: "'Inter Tight', Inter, sans-serif",
  serif: "'Playfair Display', Georgia, serif",
  serif2: "Lora, Georgia, serif",
  wide: "Unbounded, 'Inter Tight', sans-serif",
  grotesk: "Onest, Inter, sans-serif",
  rounded: "Manrope, Inter, sans-serif",
  mono: "'JetBrains Mono', Consolas, monospace",
  pixel: "'Press Start 2P', monospace",
} as const;

export type FontKey = keyof typeof F;

// Faces that must be resident before the first frame is captured. Loading them
// with Cyrillic sample text pulls the cyrillic unicode-range subset too.
const FACES: string[] = [
  "400 40px Inter", "500 40px Inter", "600 40px Inter", "700 40px Inter", "800 40px Inter",
  "500 40px 'Inter Tight'", "600 40px 'Inter Tight'", "700 40px 'Inter Tight'", "800 40px 'Inter Tight'", "900 40px 'Inter Tight'",
  "italic 800 40px 'Inter Tight'",
  "italic 400 40px 'Playfair Display'", "italic 500 40px 'Playfair Display'", "italic 600 40px 'Playfair Display'",
  "italic 700 40px 'Playfair Display'", "italic 800 40px 'Playfair Display'", "700 40px 'Playfair Display'", "900 40px 'Playfair Display'",
  "italic 500 40px Lora", "italic 600 40px Lora",
  "500 40px Unbounded", "700 40px Unbounded", "800 40px Unbounded", "900 40px Unbounded",
  "400 40px Onest", "500 40px Onest", "600 40px Onest", "700 40px Onest", "800 40px Onest", "900 40px Onest",
  "500 40px Manrope", "700 40px Manrope", "800 40px Manrope",
  "400 40px 'JetBrains Mono'", "500 40px 'JetBrains Mono'", "700 40px 'JetBrains Mono'",
  "400 40px 'Press Start 2P'",
];

let loading: Promise<void> | null = null;
export const loadFonts = () => {
  if (typeof document === "undefined") return Promise.resolve();
  if (!loading) {
    const sample = "Аа Яя Ёё Ww 0123 «»—₽★";
    loading = Promise.all(FACES.map((f) => document.fonts.load(f, sample).catch(() => null)))
      .then(() => document.fonts.ready)
      .then(() => undefined);
  }
  return loading;
};
