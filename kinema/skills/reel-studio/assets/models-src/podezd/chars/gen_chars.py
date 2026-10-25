"""Characters for the podezd horror reel, made from scratch:
  1) a full-body T-pose reference picture per character (an A-pose first try is kept in apose/: arms too close to the body to rig) (google/nano-banana-pro),
  2) image -> textured quad mesh in T/A pose (hyper3d/rodin, Gen-2),
  3) rig + weights in Blender (rig_chars.py), animated procedurally in the engine (engine/src/three/human.ts).

    python -I gen_chars.py ref [name ...]    -> ref/<name>.png
    python -I gen_chars.py mesh [name ...]   -> mesh/<name>.glb
"""
import concurrent.futures as cf
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rep3d  # noqa: E402

HERE = Path(__file__).resolve().parent
R = rep3d.R
REF = HERE / "ref"
MESH = HERE / "mesh"
REF.mkdir(exist_ok=True)
MESH.mkdir(exist_ok=True)

LOOK = ("Full-body character reference for 3D rigging, front view, whole figure from the top of the head to the feet visible and "
        "centred, standing straight in a strict T-pose: both arms stretched straight out horizontally to the sides at shoulder "
        "height, elbows straight, palms facing down, fingers together and straight, legs straight with feet about 30 cm apart, "
        "looking straight ahead, neutral face. Photorealistic, even soft studio lighting with no hard shadows, plain light grey "
        "seamless background, nothing else in the frame. ")
CHARS = {
    "serega": LOOK + "A Russian man about 38, stocky, unshaven, tired puffy face, short dark hair, wearing a faded grey stretched "
                     "tank top, dark blue tracksuit trousers with two white side stripes, worn brown house slippers.",
    "lyuda": LOOK + "A Russian woman about 55, plump, short permed reddish-brown hair, wearing a faded blue-and-pink floral cotton "
                    "housecoat down to the knees with a belt, thick beige tights, worn house slippers.",
    "ded": LOOK + "A thin Russian old man about 72, bald with grey stubble, wearing an old brown knitted cardigan over a checked "
                  "flannel shirt, baggy grey trousers, worn house slippers.",
    "valya": LOOK + "A heavy-set Russian woman about 72, grey hair under a dark red floral headscarf tied under the chin, wearing a "
                    "dark green knitted cardigan over a dark brown dress below the knees, thick brown tights, black felt house shoes.",
    "him": LOOK + "A horror creature: an extremely tall, emaciated, pale grey humanoid, hairless smooth body like a mannequin with "
                  "no genitals and no clothes, visible ribs and collarbones, very long thin arms reaching below the knees, long bony "
                  "fingers, long thin legs, small bald head with a smooth featureless face and faint sunken eye sockets, no mouth.",
}
PROMPT = {
    "serega": "realistic Russian man in a grey tank top and blue tracksuit trousers, house slippers, T-pose",
    "lyuda": "realistic Russian woman in a floral cotton housecoat, beige tights, house slippers, T-pose",
    "ded": "realistic old man in a brown knitted cardigan, checked shirt, grey trousers, slippers, T-pose",
    "valya": "realistic old woman in a red floral headscarf, green knitted cardigan, brown dress, brown tights, T-pose",
    "him": "extremely tall emaciated pale grey hairless humanoid creature with very long thin arms and fingers, T-pose",
}
HEIGHT = {"serega": 1.76, "lyuda": 1.62, "ded": 1.70, "valya": 1.58, "him": 2.55}


def ref(name):
    f = REF / f"{name}.png"
    if f.exists():
        return f"skip {f.name}"
    for attempt in range(3):
        try:
            f.write_bytes(R.run("google/nano-banana-pro", {"prompt": CHARS[name], "aspect_ratio": "1:1", "resolution": "2K",
                                                          "output_format": "png", "allow_fallback_model": False}))
            return f"OK {f.name}"
        except (SystemExit, ValueError) as e:
            err = str(e)[:160]
            time.sleep(5)
    return f"FAILED {name} {err}"


def mesh(name):
    f = MESH / f"{name}.glb"
    if f.exists():
        return f"skip {f.name}"
    import base64
    uri = "data:image/png;base64," + base64.b64encode((REF / f"{name}.png").read_bytes()).decode()
    out = rep3d.run_version("hyper3d/rodin", {"images": [uri], "prompt": PROMPT[name], "tapose": True, "quality": "high", "material": "PBR",
                                               "mesh_mode": "Quad", "geometry_file_format": "glb", "seed": 7})
    urls = out if isinstance(out, list) else [out] if isinstance(out, str) else list(out.values()) if isinstance(out, dict) else []
    glb = next((u for u in urls if isinstance(u, str) and u.split("?")[0].endswith(".glb")), None) or (urls[0] if urls else None)
    if not glb:
        return f"FAILED {name}: no output {str(out)[:200]}"
    rep3d.fetch(glb, f)
    return f"OK {f.name} ({f.stat().st_size // 1024} KB)"


if __name__ == "__main__":
    step, names = sys.argv[1], sys.argv[2:] or list(CHARS)
    fn = {"ref": ref, "mesh": mesh}[step]
    with cf.ThreadPoolExecutor(3) as ex:
        for r in ex.map(fn, names):
            print(r, flush=True)
