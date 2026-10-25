"""Seamless photo textures for the podezd horror sets (Khrushchyovka stairwell, booth, flat, basement).

    python -I gen_textures.py [name ...]   -> raw/<name>.png (generated) -> ../../../../engine/public/projects/podezd/tex/<name>.jpg + <name>_n.png
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
OUT = RS / "engine" / "public" / "projects" / "podezd" / "tex"
RAW.mkdir(exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Seamless tileable texture, photographed straight on with flat even light, no shadows, no perspective, "
        "no objects, no text, no letters, no logos, no graffiti, no border, realistic photo detail, muted natural colours. Subject: ")
FLAT = ("Flat straight-on photo filling the whole frame edge to edge, even soft light, no perspective, no shadows, no text. Subject: ")
JOBS = {
    "wall_green": BASE + "old Soviet apartment stairwell wall painted with glossy dark olive-green oil paint, chipped spots showing grey plaster, scuffs and fine scratches, slightly dirty.",
    "whitewash": BASE + "old whitewashed lime plaster wall, dirty off-white with grey-yellow water stains, fine cracks, slightly uneven surface.",
    "terrazzo": BASE + "worn grey Soviet terrazzo (mosaic concrete) stair surface with small light and dark stone chips, polished by feet, dusty, small chips.",
    "metlakh": BASE + "Soviet metlakh floor tiles seen from above: small square unglazed ceramic tiles about 10 cm, alternating beige and brick-red checker pattern, worn, dirty grout, a few cracked tiles.",
    "brick_white": BASE + "facade of an old Soviet five-storey building made of white silicate bricks, greyish, dirt streaks, thin grey mortar joints, bricks laid in running bond.",
    "leatherette": BASE + "brown padded leatherette door upholstery with a diamond quilted pattern held by small brass upholstery nails, worn and slightly torn in places.",
    "parquet": BASE + "old Soviet herringbone oak parquet floor seen from above, worn amber varnish, scratches and dark gaps.",
    "wallpaper": BASE + "faded Soviet 1980s paper wallpaper, beige with a subtle brown vertical floral pattern, slightly stained and yellowed.",
    "concrete_damp": BASE + "damp dark basement concrete wall, black mould patches, rusty water streaks, white efflorescence, wet sheen.",
    "metal_paint": BASE + "old sheet metal painted grey-green, paint peeling and flaking, rust spots and streaks.",
    "wood_dark": BASE + "old dark brown varnished wooden furniture panel, scratched and worn varnish, wood grain running vertically.",
    "tiles_blue": BASE + "Soviet bathroom wall: small square pale blue glazed ceramic tiles about 15 cm, dirty white grout, a few chipped tiles.",
}
FLAT_JOBS = {"carpet": FLAT + "a whole Soviet wall rug (kovyor) with an ornate red, burgundy and dark blue oriental medallion pattern and a patterned border, slightly faded."}
JOBS.update(FLAT_JOBS)

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
    a = seam_fix(a) if name not in FLAT_JOBS else a
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT / f"{name}.jpg", quality=90)
    Image.fromarray(normal_map(a)).resize((1024, 1024), Image.LANCZOS).save(OUT / f"{name}_n.png")
    return f"OK {name}"


if __name__ == "__main__":
    names = sys.argv[1:] or list(JOBS)
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(make, names):
            print(r, flush=True)
