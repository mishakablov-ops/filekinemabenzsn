"""Chatterbox (Resemble AI) on Replicate -> voice takes per section.

python tts_chatterbox.py --takes 2 --variants default,clone [--only s1,s2] [--model resemble-ai/chatterbox-multilingual]
Writes voice/takes/<sid>_<variant>_t<k>.<ext> and voice/takes/manifest.json. Token from ../../.secrets.env (never printed).
"""
import argparse, base64, json, os, pathlib, sys, time, urllib.error, urllib.request

for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = pathlib.Path(__file__).resolve().parents[2]
API = "https://api.replicate.com/v1"

def token():
    for line in (ROOT / ".secrets.env").read_text(encoding="utf-8").splitlines():
        if line.startswith("REPLICATE_API_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no REPLICATE_API_TOKEN in .secrets.env")

TOK = token()

def call(method, url, body=None, extra=None, timeout=130):
    h = {"Authorization": f"Bearer {TOK}", "Content-Type": "application/json", "User-Agent": "kosmos-dlya-vseh/1.0"}
    h.update(extra or {})
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for attempt in range(8):
        try:
            r = urllib.request.Request(url, data=data, method=method, headers=h)
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504):
                last = f"HTTP {e.code}"; time.sleep(4 * (attempt + 1)); continue
            raise SystemExit(f"HTTP {e.code} {url}: {msg[:800]}")
        except Exception as e:
            last = repr(e); time.sleep(4 * (attempt + 1))
    raise SystemExit(f"failed {url}: {last}")

def download(url, dst):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "kosmos-dlya-vseh/1.0"}), timeout=120) as r:
                dst.write_bytes(r.read()); return
        except Exception as e:
            time.sleep(3 * (attempt + 1)); last = e
    raise SystemExit(f"download failed {url}: {last}")

def pick(props, *needles):
    for n in needles:
        for k in props:
            if n in k.lower():
                return k
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="resemble-ai/chatterbox-multilingual")
    ap.add_argument("--sections", default=str(ROOT / "voice" / "sections.json"))
    ap.add_argument("--out", default=str(ROOT / "voice" / "takes"))
    ap.add_argument("--ref", default=str(ROOT / "voice" / "ref_voice.mp3"))
    ap.add_argument("--variants", default="default,clone")
    ap.add_argument("--takes", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--exaggeration", type=float, default=0.55)
    ap.add_argument("--cfg", type=float, default=0.4)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--tag", default="")
    ap.add_argument("--seed0", type=int, default=0)
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

    info = call("GET", f"{API}/models/{a.model}")
    schema = info["latest_version"]["openapi_schema"]["components"]["schemas"]
    props = schema["Input"]["properties"]
    (ROOT / "voice" / f"schema_{a.model.split('/')[-1]}.json").write_text(json.dumps(schema, ensure_ascii=False, indent=1), encoding="utf-8")
    print("model", a.model, "version", info["latest_version"]["id"][:12], "inputs", list(props))
    k_text = pick(props, "text", "prompt")
    k_lang = pick(props, "language", "lang")
    k_ref = pick(props, "reference", "audio_prompt", "audio")
    k_ex = pick(props, "exagg")
    k_cfg = pick(props, "cfg")
    k_temp = pick(props, "temp")
    k_seed = pick(props, "seed")
    lang_val = None
    if k_lang:
        ref = props[k_lang].get("allOf", [{}])[0].get("$ref", "")
        enum = props[k_lang].get("enum") or (schema.get(ref.split("/")[-1], {}).get("enum") if ref else None)
        if enum:
            lang_val = next((e for e in enum if str(e).lower() in ("ru", "russian")), None) or next((e for e in enum if "ru" in str(e).lower()), None)
        else:
            lang_val = "ru"
    print("mapping", dict(text=k_text, lang=k_lang, lang_val=lang_val, ref=k_ref, ex=k_ex, cfg=k_cfg, temp=k_temp, seed=k_seed))
    ref_uri = None
    if k_ref and os.path.exists(a.ref):
        ref_uri = "data:audio/mpeg;base64," + base64.b64encode(pathlib.Path(a.ref).read_bytes()).decode()

    sections = json.load(open(a.sections, encoding="utf-8"))
    only = set(filter(None, a.only.split(",")))
    man_path = out / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else []
    for sec in sections:
        if only and sec["id"] not in only: continue
        for variant in a.variants.split(","):
            if variant == "clone" and not ref_uri: continue
            for t in range(1, a.takes + 1):
                name = f"{sec['id']}_{variant}{a.tag}_t{t}"
                if any(m["name"] == name for m in manifest): continue
                seed = 1000 * t + int(sec["id"][1:]) * 7 + a.seed0
                inp = {k_text: sec["text"]}
                if k_lang and lang_val: inp[k_lang] = lang_val
                if k_ex: inp[k_ex] = a.exaggeration
                if k_cfg: inp[k_cfg] = a.cfg
                if k_temp: inp[k_temp] = a.temperature
                if k_seed: inp[k_seed] = seed
                if variant == "clone": inp[k_ref] = ref_uri
                t0 = time.time()
                p = call("POST", f"{API}/predictions", {"version": info["latest_version"]["id"], "input": inp}, {"Prefer": "wait=60"})
                while p.get("status") not in ("succeeded", "failed", "canceled"):
                    time.sleep(2); p = call("GET", p["urls"]["get"])
                if p["status"] != "succeeded":
                    print("FAILED", name, p.get("error")); continue
                o = p["output"]
                if isinstance(o, list): o = o[0]
                if isinstance(o, dict): o = o.get("audio") or next(iter(o.values()))
                ext = os.path.splitext(o.split("?")[0])[1] or ".wav"
                dst = out / f"{name}{ext}"
                download(o, dst)
                manifest.append({"name": name, "section": sec["id"], "variant": variant, "take": t, "seed": seed,
                                 "file": dst.name, "secs": round(time.time() - t0, 1), "text": sec["text"],
                                 "params": {k: v for k, v in inp.items() if k != k_ref}})
                man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
                print("ok", name, dst.stat().st_size, "bytes", round(time.time() - t0, 1), "s")
    print("DONE", len(manifest), "takes")

if __name__ == "__main__":
    main()
