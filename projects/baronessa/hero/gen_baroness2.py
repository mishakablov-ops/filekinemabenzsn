"""Baroness v2 (28.10.2026, mike: «сделай лицо Синяка», «сделай её очень толстой», Igor approved): the meme's own face
from the old sepia photo mike sent (meme_ref/meme_photo.png, cropped from his screen recording), a very plump body,
the same costume. Same route as gen_baroness.py: reference in T-pose (nano-banana-pro) -> hyper3d/rodin.
    python -I gen_baroness2.py ref c d     -> ref/tpose_c.png, ref/tpose_d.png
    python -I gen_baroness2.py mesh c      -> mesh/baroness_c.glb
"""
import base64
import concurrent.futures as cf
import sys
import time
from pathlib import Path

import gen_baroness as G

HERE = Path(__file__).resolve().parent
PHOTO = HERE / "meme_ref" / "meme_photo.png"

LOOK = (
    "Image 1 is an old sepia family-album portrait of a character from a popular internet meme (the 'baroness'). Make a "
    "photorealistic full-body colour character reference of EXACTLY this character for 3D scanning and rigging: keep the "
    "same face as in image 1 (very round, heavy, wide face with full cheeks and a double chin, the same dark eyes under "
    "straight dark brows, the same small nose, the same full, firmly closed lips, the same stern unsmiling expression), "
    "the same shoulder-length dark brown hair with soft waves, the same khaki garrison cap (side cap) worn on top of the "
    "head. A VERY plump, heavy, obese body (wide shoulders, big round belly and hips, thick arms and legs), height about "
    "1.70 m, realistic adult proportions. She wears a tailored khaki wool officer-style tunic with a turn-down collar, a "
    "khaki shirt and tie, gold buttons, two breast pockets and a brown leather belt with a gold buckle tight over the "
    "belly, a straight khaki skirt to just below the knee, dark stockings and polished brown leather lace-up boots. No "
    "medals, no insignia, no logos, no text. Front view, the whole figure from the top of the cap to the soles visible "
    "and centred, standing straight in a strict T-pose: both arms stretched straight out horizontally to the sides at "
    "shoulder height, elbows straight, palms facing down, legs straight with the feet slightly apart, looking straight "
    "ahead. Even soft studio light with no hard shadows, plain light grey seamless background, nothing else in the frame."
)
PROMPT_3D = ("realistic very plump stern woman, round heavy face, khaki garrison cap, khaki officer tunic with tie, gold "
             "buttons and leather belt, khaki skirt below the knee, brown leather boots, T-pose")


def ref(tag):
    f = G.REF / f"tpose_{tag}.png"
    if f.exists():
        return f"skip {f.name}"
    img = "data:image/png;base64," + base64.b64encode(PHOTO.read_bytes()).decode()
    err = ""
    for attempt in range(2):
        try:
            f.write_bytes(G.R.run("google/nano-banana-pro", {"prompt": LOOK, "image_input": [img], "aspect_ratio": "1:1",
                                                            "resolution": "2K", "output_format": "png",
                                                            "allow_fallback_model": False}, timeout=900))
            return f"OK {f.name} ({f.stat().st_size // 1024} KB)"
        except (SystemExit, ValueError) as e:
            err = str(e)[:300]
            print("retry", tag, err, flush=True)
            time.sleep(5)
    return f"FAILED {tag} {err}"


if __name__ == "__main__":
    step, tags = sys.argv[1], sys.argv[2:]
    if step == "ref":
        with cf.ThreadPoolExecutor(2) as ex:
            for r in ex.map(ref, tags or ["c", "d"]):
                print(r, flush=True)
    elif step == "mesh":
        G.PROMPT_3D = PROMPT_3D
        for t in tags or ["c"]:
            print(G.mesh(t), flush=True)
