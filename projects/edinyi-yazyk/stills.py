"""Stills + contact sheet + QA log for edinyi-yazyk.
    python -I stills.py 1.0,3.0,...  -> <root>/_sync/edin/stills/*.png + sheet.png + qa.json
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / "AIpollon-Reel-Studio" / "skills" / "reel-studio" / "engine"
out = ROOT / "_sync" / "edin" / "stills"
out.mkdir(parents=True, exist_ok=True)
secs = sys.argv[1] if len(sys.argv) > 1 else "1.6,3.2,5.0,6.3,8.2,10.6,11.9,13.5,16.0,18.5,20.6,22.5,23.9,26.4,27.9,30.0,32.2,34.0,37.6,39.4,41.0,42.6,44.5,46.6,48.2,49.4,51.5"
cmd = ["node", "tools/stills.mjs", "--comp", "Reel", "--props", json.dumps({"project": "edinyi-yazyk"}), "--seconds", secs,
       "--out", str(out), "--scale", "0.5", "--sheet", str(out / "sheet.png"), "--cols", "7", "--qa"]
r = subprocess.run(cmd, cwd=ENG, capture_output=True, text=True, encoding="utf-8", errors="replace")
log = (r.stdout or "") + "\n---stderr---\n" + (r.stderr or "")
(out / "log.txt").write_text(log, encoding="utf-8")
keep = [ln for ln in log.splitlines() if ln.strip() and not ln.strip().startswith(("at ", "columnNumber", "fileName", "functionName", "lineNumber", "{", "}", "},", "frame "))]
print("\n".join(keep[:60]))
print("stills exit", r.returncode)
