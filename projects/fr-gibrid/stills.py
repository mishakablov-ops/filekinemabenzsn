"""Stills + contact sheet + QA log for fr-gibrid (node is called with a list, so the JSON props survive Windows quoting).
    python -I stills.py 1.0,3.0,...  -> <root>/_sync/frg_stills/*.png + sheet.png + qa.json
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / "AIpollon-Reel-Studio" / "skills" / "reel-studio" / "engine"
out = ROOT / "_sync" / "frg_stills"
out.mkdir(parents=True, exist_ok=True)
secs = sys.argv[1] if len(sys.argv) > 1 else "1.0,3.0,4.6,6.9,8.2,10.5,13.0,14.6,16.0,17.6"
cmd = ["node", "tools/stills.mjs", "--comp", "Reel", "--props", json.dumps({"project": "fr-gibrid"}), "--seconds", secs,
       "--out", str(out), "--scale", "0.5", "--sheet", str(out / "sheet.png"), "--cols", "6", "--qa"]
r = subprocess.run(cmd, cwd=ENG, capture_output=True, text=True, encoding="utf-8", errors="replace")
log = (r.stdout or "") + "\n---stderr---\n" + (r.stderr or "")
(out / "log.txt").write_text(log, encoding="utf-8")
keep = [ln for ln in log.splitlines() if ln.strip() and not ln.strip().startswith(("at ", "columnNumber", "fileName", "functionName", "lineNumber", "{", "}", "},"))]
print("\n".join(keep[:60]))
print("stills exit", r.returncode)
