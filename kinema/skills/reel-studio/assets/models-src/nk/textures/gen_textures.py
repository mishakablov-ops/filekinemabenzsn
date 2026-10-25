"""Seamless photo textures for the nk-escape sets (JSA, barracks), one look for everything.

    python -I gen_textures.py [name ...]   -> raw/<name>.png (generated) -> ../../../../engine/public/projects/nk-escape/tex/<name>.jpg + <name>_n.png
Generated with google/nano-banana-pro via Replicate (key from reel-studio/.secrets.env). Post: seam blend so it tiles,
2048 px JPEG albedo, normal map from luminance.
"""
import concurrent.futures as cf
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
RS = Path(__file__).resolve().parents[4]  # the reel-studio folder (assets/models-src/<project>/<dir>/this.py)
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

RAW = HERE / "raw"
OUT = RS / "engine" / "public" / "projects" / "nk-escape" / "tex"
RAW.mkdir(exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Seamless tileable texture, photographed straight on with flat even overcast light, no shadows, no perspective, "
        "no objects, no text, no logos, no border, realistic photo detail, muted natural colours. Subject: ")
JOBS = {
    "concrete": BASE + "weathered grey poured concrete surface, faint form lines, water stains, fine hairline cracks, slight dirt.",
    "gravel": BASE + "compacted grey crushed-stone gravel ground seen from above, small angular stones, some dust.",
    "asphalt": BASE + "old worn dark grey asphalt road surface seen from above, coarse aggregate, a few patched cracks.",
    "metal_blue": BASE + "vertical corrugated sheet-metal wall painted light sky blue, slightly faded paint, a few small scratches, ribs running vertically.",
    "metal_grey": BASE + "vertical corrugated sheet-metal wall painted light silver grey, slightly faded paint, a few small scratches, ribs running vertically.",
    "granite": BASE + "light grey granite block masonry facade, large rectangular cut stone blocks with thin mortar joints.",
    "plaster_green": BASE + "old painted plaster wall, pale institutional green paint, worn patches, light stains.",
    "dry_grass": BASE + "dry autumn grass and bare soil ground seen from above, yellow-brown, a few fallen leaves.",
    "floor_paint": BASE + "worn painted concrete floor, faded dark red-brown paint, scuffs, seen from above.",
}


def seam_fix(a: np.ndarray) -> np.ndarray:
    """crossfade with a half-offset copy across the edges so the image tiles"""
    h, w, _ = a.shape
    b = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.minimum(xx, w - 1 - xx) / (w * 0.18)
    dy = np.minimum(yy, h - 1 - yy) / (h * 0.18)
    m = np.clip(np.minimum(dx, dy), 0, 1)[..., None]  # 0 at the edges -> use the offset copy there
    m = m * m * (3 - 2 * m)
    return a * m + b * (1 - m)


def normal_map(a: np.ndarray, strength: float = 2.2) -> np.ndarray:
    lum = (a @ np.array([0.299, 0.587, 0.114], np.float32)) / 255.0
    hgt = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * strength
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * strength
    n = np.stack([-dx, dy, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def make(name: str) -> str:
    raw = RAW / f"{name}.png"
    if not raw.exists():
        for attempt in range(3):
            try:
                raw.write_bytes(R.run("google/nano-banana-pro", {"prompt": JOBS[name], "aspect_ratio": "1:1", "resolution": "2K",
                                                                 "output_format": "png", "allow_fallback_model": False}))
                break
            except (SystemExit, ValueError) as e:
                print("retry", name, str(e)[:120], flush=True)
                time.sleep(5)
    if not raw.exists():
        return f"FAILED {name}"
    a = np.asarray(Image.open(raw).convert("RGB").resize((2048, 2048), Image.LANCZOS)).astype(np.float32)
    a = seam_fix(a)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT / f"{name}.jpg", quality=90)
    Image.fromarray(normal_map(a)).resize((1024, 1024), Image.LANCZOS).save(OUT / f"{name}_n.png")
    return f"OK {name}"


if __name__ == "__main__":
    names = sys.argv[1:] or list(JOBS)
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(make, names):
            print(r, flush=True)
