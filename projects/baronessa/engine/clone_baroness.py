"""The baroness's lines in Igor's own voice (mike 28.10: «голос баронессы скопируй с реальной жизни», Igor approved;
the sample is the voice message mike put in Downloads -> hero/voice_ref/igor_sample.mp3). Chatterbox multilingual
instant clone, one take per line (budget), Whisper check; files land in takes/clone/ for voice_sections.py --clone.
    python -I engine/clone_baroness.py
"""
import base64
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RS = Path(os.environ.get("KINEMA_RS", r"C:\Users\Gigabyte\Documents\aipollon claude\KINEMA\skills\reel-studio"))
sys.path.insert(0, str(RS / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
for line in (HERE / ".secrets.env").read_text(encoding="utf-8").splitlines():
    if line.startswith("REPLICATE_API_TOKEN="):
        os.environ["REPLICATE_API_TOKEN"] = line.split("=", 1)[1].strip()
os.environ.setdefault("REPLICATE_JOB", "baronessa-clone")
os.environ.setdefault("REPLICATE_CAP_USD", "0.3")
import replicate_tts as R  # noqa: E402
import voice_sections as V  # noqa: E402

R.PRICE_USD.setdefault("resemble-ai/chatterbox-multilingual", 0.05)
SAMPLE = HERE / "hero" / "voice_ref" / "igor_sample.mp3"
OUT = RS / "engine" / "public" / "projects" / "baronessa" / "takes" / "clone"
# mike 28.10: the first clone was «очень по иишному с просадами» -> calm mode: less exaggeration, lower temperature,
# slower guidance (fewer pitch dips)
CALM = "--calm" in sys.argv
if CALM:
    OUT = OUT.parent / "clone_calm"


def run_version(slug, inp, timeout=600):
    """community models take POST /v1/predictions with a version (not /models/.../predictions)"""
    import time
    import urllib.request
    ver = R._req("GET", f"{R.API}/models/{slug}")["latest_version"]["id"]
    R.charge(slug)
    p = R._req("POST", f"{R.API}/predictions", {"version": ver, "input": inp}, wait=True)
    t0 = time.time()
    while p.get("status") not in ("succeeded", "failed", "canceled"):
        if time.time() - t0 > timeout:
            raise SystemExit(f"{slug}: timed out")
        time.sleep(2)
        p = R._req("GET", p["urls"]["get"])
    if p["status"] != "succeeded":
        raise SystemExit(f"{slug}: {p['status']} {str(p.get('error'))[:300]}")
    out = p["output"]
    out = out[0] if isinstance(out, list) else out
    with urllib.request.urlopen(urllib.request.Request(out, headers={"User-Agent": "reel-studio/1.0"}), timeout=120) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = "data:audio/mpeg;base64," + base64.b64encode(SAMPLE.read_bytes()).decode()
    for sid, sec, role, text in V.segments():
        if role != "b":
            continue
        key = sec + "b" + V.hashlib.md5(text.encode()).hexdigest()[:6]
        f = OUT / f"{key}.wav"
        if not f.exists():
            par = dict(exaggeration=0.3, cfg_weight=0.35, temperature=0.45) if CALM else \
                dict(exaggeration=0.6, cfg_weight=0.5, temperature=0.7)
            b = run_version("resemble-ai/chatterbox-multilingual", dict(text=text, language="ru", reference_audio=ref,
                                                                    **par),
                      timeout=600)
            f.write_bytes(b)
        sc = V.score(text, f)
        print(f"{key} match {sc['match']} {sc['dur']}s :: {sc['hyp']}", flush=True)


if __name__ == "__main__":
    main()
