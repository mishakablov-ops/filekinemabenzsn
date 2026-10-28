"""Main hero of «Каждому по способности» from the user's two reference sheets (27.10.2026), the KINEMA way
(assets/models-src/podezd/chars): reference picture in a strict T-pose -> image-to-3D -> own chibi rig (rig_hero.py).

The user rejected a hero built from primitives on 26.10 («не похоже вообще»), so this one is generated from the
reference itself and keeps its look: chibi boy, short fade, big brown eyes, black hoodie with a kangaroo pocket and
grey drawstrings, wide black trousers, white sneakers.

Runs on the PC (Replicate is not reachable from the cloud), with KINEMA's python:
    python -I gen_hero.py ref        -> ref/tpose_a.png, ref/tpose_b.png   (google/nano-banana-pro, ~$0.30 each)
    python -I gen_hero.py mesh a     -> mesh/hero_a.glb                    (hyper3d/rodin, ~$1.50)
Env: KINEMA_RS = path to KINEMA/skills/reel-studio; REPLICATE_JOB is set by the worker job (cap $3 per job).
"""
import base64
import concurrent.futures as cf
import os
import sys
import time
from pathlib import Path

RS = Path(os.environ.get("KINEMA_RS", r"C:\Users\Gigabyte\Documents\aipollon claude\KINEMA\skills\reel-studio"))
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

HERE = Path(__file__).resolve().parent
REF = HERE / "ref"
MESH = HERE / "mesh"
MESH.mkdir(exist_ok=True)


def uri(path):
    """the reference JPEGs are prepared in the cloud (the PC's python has no PIL)"""
    return "data:image/jpeg;base64," + base64.b64encode(Path(path).read_bytes()).decode()


LOOK = (
    "Image 1 is the front view of a stylised 3D chibi character, image 2 is the same character from six angles, image 3 "
    "shows close-ups of his clothes and sneakers. Make a full-body character reference of EXACTLY this character for 3D "
    "modelling and rigging: same face, same big glossy dark-brown eyes with two highlights, same thick straight dark "
    "eyebrows, small nose, small calm smile, same ears, same very short dark buzz-cut hair with a straight front hairline "
    "and a skin fade on the sides and back, same light warm skin, same chibi proportions (big head about 40 percent of the "
    "height, short body, short legs, rounded mitten-like hands with a separate thumb), same matte black hoodie with a "
    "hood, a rectangular kangaroo pocket and two dark grey drawstrings with black tips, ribbed cuffs and hem, same wide "
    "straight black sweatpants falling onto the shoes, same chunky white leather low-top sneakers with perforated toes "
    "and a thick white sole. Front view, the whole figure from the top of the head to the soles visible and centred, "
    "standing straight in a strict T-pose: both arms stretched straight out horizontally to the sides at shoulder height, "
    "elbows straight, palms facing down, legs straight with the feet slightly apart, looking straight ahead. Same soft 3D "
    "render look as the references (smooth vinyl-toy style, soft matte materials), even soft studio light with no hard "
    "shadows, plain light grey seamless background, nothing else in the frame, no text."
)
PROMPT_3D = ("stylised chibi boy toy figure, big head, short buzz-cut hair with fade, black hoodie with kangaroo pocket and "
             "grey drawstrings, wide black sweatpants, chunky white sneakers, T-pose")


def ref(tag):
    f = REF / f"tpose_{tag}.png"
    if f.exists():
        return f"skip {f.name}"
    imgs = [uri(REF / "front.jpg"), uri(REF / "turnaround.jpg"), uri(REF / "details.jpg")]
    err = ""
    for attempt in range(3):
        try:
            f.write_bytes(R.run("google/nano-banana-pro", {"prompt": LOOK, "image_input": imgs, "aspect_ratio": "1:1",
                                                          "resolution": "2K", "output_format": "png",
                                                          "allow_fallback_model": False}, timeout=900))
            return f"OK {f.name} ({f.stat().st_size // 1024} KB)"
        except (SystemExit, ValueError) as e:
            err = str(e)[:300]
            print("retry", tag, err, flush=True)
            time.sleep(5)
    return f"FAILED {tag} {err}"


def run_version(slug, inp, timeout=1800):
    info = R._req("GET", f"{R.API}/models/{slug}")
    ver = info["latest_version"]["id"]
    R.charge(slug)
    try:
        p = R._req("POST", f"{R.API}/predictions", {"version": ver, "input": inp}, wait=True)
    except SystemExit as e:
        if " 402" in str(e) or " 422" in str(e):
            R.refund(slug)
        raise
    t0 = time.time()
    while p.get("status") not in ("succeeded", "failed", "canceled"):
        if time.time() - t0 > timeout:
            raise SystemExit(f"{slug}: timed out")
        time.sleep(3)
        p = R._req("GET", p["urls"]["get"])
    if p["status"] != "succeeded":
        raise SystemExit(f"{slug}: {p['status']} {str(p.get('error'))[:400]}")
    return p["output"]


def fetch(url, dst):
    import urllib.request
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "reel-studio/1.0"}), timeout=300) as r:
        Path(dst).write_bytes(r.read())


def mesh(tag):
    f = MESH / f"hero_{tag}.glb"
    if f.exists():
        return f"skip {f.name}"
    src = REF / f"tpose_{tag}.png"
    out = run_version("hyper3d/rodin", {"images": ["data:image/png;base64," + base64.b64encode(src.read_bytes()).decode()], "prompt": PROMPT_3D, "tapose": True, "quality": "high",
                                         "material": "PBR", "mesh_mode": "Quad", "geometry_file_format": "glb", "seed": 7})
    urls = out if isinstance(out, list) else [out] if isinstance(out, str) else list(out.values()) if isinstance(out, dict) else []
    glb = next((u for u in urls if isinstance(u, str) and u.split("?")[0].endswith(".glb")), None) or (urls[0] if urls else None)
    if not glb:
        return f"FAILED {tag}: no output {str(out)[:300]}"
    fetch(glb, f)
    for u in urls:   # previews Rodin returns next to the model, if any
        if isinstance(u, str) and u.split("?")[0].lower().endswith((".png", ".jpg", ".webp")):
            fetch(u, MESH / f"hero_{tag}_{Path(u.split('?')[0]).name}")
    return f"OK {f.name} ({f.stat().st_size // 1024} KB)"


if __name__ == "__main__":
    step, tags = sys.argv[1], sys.argv[2:]
    if step == "ref":
        with cf.ThreadPoolExecutor(2) as ex:
            for r in ex.map(ref, tags or ["a", "b"]):
                print(r, flush=True)
    elif step == "mesh":
        for t in tags or ["a"]:
            print(mesh(t), flush=True)
