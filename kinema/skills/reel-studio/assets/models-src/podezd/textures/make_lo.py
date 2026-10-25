"""PS1-style textures: shrink the 2048 px seamless photos to chunky 64-128 px tiles (what the PSX look samples, nearest filter).

    python -I make_lo.py [project] [name=size ...]      e.g.  python -I make_lo.py podezd brick_white=128 wallpaper=96
reads  engine/public/projects/<project>/tex/<name>.jpg   (made by gen_textures.py)
writes engine/public/projects/<project>/tex_lo/<name>.png  (64 px by default; busy patterns 96-128 so they still read)
"""
import sys
from pathlib import Path

from PIL import Image

RS = Path(__file__).resolve().parents[4]
args = sys.argv[1:]
project = args[0] if args and "=" not in args[0] else "podezd"
sizes = {"brick_white": 128, "carpet": 128, "wallpaper": 96}
sizes.update({k: int(v) for k, v in (a.split("=") for a in args if "=" in a)})
src = RS / "engine" / "public" / "projects" / project / "tex"
dst = src.parent / "tex_lo"
dst.mkdir(exist_ok=True)
for f in sorted(src.glob("*.jpg")):
    n = sizes.get(f.stem, 64)
    # box-filter down (averages the photo detail away), keep it RGB; the engine samples it with NearestFilter
    Image.open(f).convert("RGB").resize((n, n), Image.BOX).save(dst / f"{f.stem}.png")
    print(f"{f.stem}: {n}px")
