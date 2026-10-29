"""The baroness of «Баронесса-пулемётчица» (style «Мемы», 28.10.2026): text -> realistic T-pose reference -> image-to-3D.

The meme's face belongs to a real person, so this is an ORIGINAL face: only the costume and the manner are the meme's
(garrison cap, tailored khaki jacket, strict 1940s updo, stern look). Same route as sposobnosti/hero/gen_hero.py.

Runs on the PC with KINEMA's python:
    python -I gen_baroness.py ref a b      -> ref/tpose_a.png, ref/tpose_b.png   (google/nano-banana-pro, ~$0.30 each)
    python -I gen_baroness.py mesh a       -> mesh/baroness_a.glb                (hyper3d/rodin, ~$1.50)
Env: REPLICATE_JOB caps the spend at $3 per job.
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
REF.mkdir(exist_ok=True)
MESH.mkdir(exist_ok=True)

LOOK = (
    "Photorealistic full-body character reference for 3D scanning and rigging of an ORIGINAL fictional woman (not any "
    "real or famous person): a stern aristocratic lady of about 50 with realistic adult proportions (height 1.68 m, head "
    "about one eighth of the height), a strong jaw, high cheekbones, thin pressed lips, a severe unsmiling look straight "
    "into the camera, light warm skin with natural texture, dark brown hair pinned in a strict 1940s rolled updo. "
    "She wears a khaki wool garrison cap (side cap) tilted to her right with a small gold handbag-shaped badge, a "
    "tailored khaki wool officer-style tunic with a stand-up collar, gold buttons, two breast pockets and a brown leather "
    "belt with a gold buckle, a straight khaki skirt to just below the knee, dark stockings and polished brown leather "
    "lace-up boots. No real military insignia, no medals, no logos, no text. Front view, the whole figure from the top of "
    "the cap to the soles visible and centred, standing straight in a strict T-pose: both arms stretched straight out "
    "horizontally to the sides at shoulder height, elbows straight, palms facing down, fingers together, legs straight "
    "with the feet slightly apart, looking straight ahead. Even soft studio light with no hard shadows, plain light grey "
    "seamless background, nothing else in the frame."
)
PROMPT_3D = ("realistic stern woman about 50, khaki garrison cap, khaki officer tunic with gold buttons and leather belt, "
             "khaki skirt below the knee, brown leather boots, 1940s updo, T-pose")


def ref(tag):
    f = REF / f"tpose_{tag}.png"
    if f.exists():
        return f"skip {f.name}"
    err = ""
    for attempt in range(3):
        try:
            f.write_bytes(R.run("google/nano-banana-pro", {"prompt": LOOK, "aspect_ratio": "1:1", "resolution": "2K",
                                                          "output_format": "png", "allow_fallback_model": False},
                                timeout=900))
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
    f = MESH / f"baroness_{tag}.glb"
    if f.exists():
        return f"skip {f.name}"
    src = REF / f"tpose_{tag}.png"
    out = run_version("hyper3d/rodin", {"images": ["data:image/png;base64," + base64.b64encode(src.read_bytes()).decode()],
                                         "prompt": PROMPT_3D, "tapose": True, "quality": "high", "material": "PBR",
                                         "mesh_mode": "Quad", "geometry_file_format": "glb", "seed": 7})
    urls = out if isinstance(out, list) else [out] if isinstance(out, str) else list(out.values()) if isinstance(out, dict) else []
    glb = next((u for u in urls if isinstance(u, str) and u.split("?")[0].endswith(".glb")), None) or (urls[0] if urls else None)
    if not glb:
        return f"FAILED {tag}: no output {str(out)[:300]}"
    fetch(glb, f)
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
