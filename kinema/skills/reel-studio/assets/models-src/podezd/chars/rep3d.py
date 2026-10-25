"""Replicate helpers for community models (version-pinned predictions) + a probe of image-to-3D models."""
import json
import sys
import time
import urllib.request
from pathlib import Path

RS = Path(__file__).resolve().parents[4]  # the reel-studio folder (assets/models-src/<project>/<dir>/this.py)
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

API = R.API


def model_info(slug):
    try:
        return R._req("GET", f"{API}/models/{slug}")
    except SystemExit as e:
        return {"error": str(e)[:200]}


def run_version(slug, inp, timeout=1800):
    info = R._req("GET", f"{API}/models/{slug}")
    ver = info["latest_version"]["id"]
    R.charge(slug)  # spend cap (see replicate_tts.charge)
    try:
        p = R._req("POST", f"{API}/predictions", {"version": ver, "input": inp}, wait=True)
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
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "reel-studio/1.0"}), timeout=300) as r:
        Path(dst).write_bytes(r.read())


if __name__ == "__main__":
    for slug in sys.argv[1:]:
        i = model_info(slug)
        if "error" in i:
            print(slug, "->", i["error"][:120])
            continue
        lv = i.get("latest_version") or {}
        props = (((lv.get("openapi_schema") or {}).get("components") or {}).get("schemas") or {}).get("Input", {}).get("properties", {})
        print(slug, "| runs", i.get("run_count"), "| inputs:", ", ".join(list(props)[:18]))
