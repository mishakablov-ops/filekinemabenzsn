"""Build the distributable package (what buyers install): skills without keys, personal data or build junk.

    python build_release.py <out_dir> [--zip <file.zip>]

<out_dir> must be empty (a fresh `git clone` of the release repo is fine: `.git` is kept).
Layout:  README.md · AGENTS.md · CLAUDE.md · install.ps1 · install.sh · .gitignore · skills/{reel-studio, reel-script, reel-qa, reel-analyze}
The buyer opens this folder in Claude Code / Codex as the working folder; install.* sets it up in place.
The channel profile is reset to empty placeholders (the buyer's setup wizard fills it). Every text file is scanned
for tokens, personal paths and e-mail addresses; the build fails if anything is found.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

RS = Path(__file__).resolve().parent.parent
SKILLS = RS.parent
TEMPLATES = RS / "release"

FILES = ["SKILL.md", "README.md", "requirements.txt", ".secrets.env.example", "assets/stress_ru.txt",
         "engine/package.json", "engine/package-lock.json", "engine/tsconfig.json", "engine/remotion.config.ts"]
DIRS = ["references", "scripts", "assets/sfx-packs", "engine/src", "engine/tools", "engine/public/music", "engine/public/sfx",
        "engine/public/fx", "engine/public/projects/demo-promo"]
MODEL_EXT = {".glb", ".json", ".md"}
EXAMPLE_EXT = {".md", ".json", ".py", ".txt"}
SKIP_PARTS = {"__pycache__", ".venv", "node_modules", "out", ".git"}
# finished reels shipped as ready-to-render templates: only what they need (no takes, no 2K textures, no sound packs)
TEMPLATE_PROJECTS = {
    "podezd": ["spec.json", "words.json", "voice.wav", "script.md", "SOUNDS.md", "part2_cover.jpg", "models/*.glb", "tex_lo/*.png"],
    "sosed6": ["spec.json", "words.json", "voice.wav", "script.md", "SOUNDS.md", "part2_cover.jpg", "photo1974.jpg", "man_face.jpg", "hero_face.jpg"],
}
PROFILE_KEYS = ("name", "handle", "badge", "bio", "link", "avatar", "tiles", "stats")


def strip_profile(node):
    """TikTokProfile screens in shipped specs fall back to the buyer's brand.json: drop the seller's channel."""
    if isinstance(node, dict):
        if node.get("block") == "TikTokProfile" and isinstance(node.get("props"), dict):
            for k in PROFILE_KEYS:
                node["props"].pop(k, None)
        for v in node.values():
            strip_profile(v)
    elif isinstance(node, list):
        for v in node:
            strip_profile(v)
    return node
TEXT_EXT = {".md", ".py", ".json", ".ts", ".tsx", ".mjs", ".js", ".txt", ".ps1", ".sh", ".example", ".gitignore", ".yml", ".yaml", ""}

PLACEHOLDER_BRAND = {"name": "", "handle": "", "badge": "", "bio": "", "link": "", "avatar": "brand/avatar.jpg", "tiles": [],
                     "cta": "Кстати, этот ролик собрал агент. Хочешь так же? Тебе в шапку профиля."}

LEAKS = [
    (re.compile(r"r8_[A-Za-z0-9]{20,}"), "Replicate token"),
    (re.compile(r"(REPLICATE_API_TOKEN|FISH_API_KEY|ELEVENLABS_API_KEY)[ \t]*=[ \t]*[A-Za-z0-9_\-]{8,}"), "key value"),
    (re.compile(r"sk_[A-Za-z0-9]{24,}"), "secret key"),
    (re.compile(r"[A-Za-z]:\\\\?Users\\\\?[^\\\s\"']+\\\\?\.claude", re.I), "personal Windows path"),
    (re.compile(r"/(Users|home)/[^/\s\"']+/\.claude"), "personal home path"),
    (re.compile(r"[A-Za-z0-9._%+-]+@(gmail|yandex|mail|outlook|icloud)\.[a-z]{2,}", re.I), "e-mail address"),
]


def copy_tree(src: Path, dst: Path, ext: set[str] | None = None) -> int:
    n = 0
    for f in src.rglob("*"):
        if f.is_dir() or SKIP_PARTS & set(f.relative_to(src).parts):
            continue
        if ext is not None and f.suffix.lower() not in ext:
            continue
        t = dst / f.relative_to(src)
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, t)
        n += 1
    return n


def scan(root: Path) -> list[str]:
    bad = []
    for f in root.rglob("*"):
        if f.is_dir() or ".git" in f.relative_to(root).parts:
            continue
        if f.name == ".secrets.env":
            bad.append(f"{f.relative_to(root)}: secrets file")
            continue
        if f.suffix.lower() not in TEXT_EXT or f.stat().st_size > 5_000_000:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for rx, what in LEAKS:
            m = rx.search(text)
            if m:
                bad.append(f"{f.relative_to(root)}: {what} «{m.group(0)[:12]}…»")
    return bad


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    out = Path(args[0]).resolve()
    zip_to = Path(args[args.index("--zip") + 1]).resolve() if "--zip" in args else None
    out.mkdir(parents=True, exist_ok=True)
    if [p for p in out.iterdir() if p.name != ".git"]:
        raise SystemExit(f"{out} is not empty — use a fresh folder (a fresh git clone is fine)")

    dst = out / "skills" / "reel-studio"
    n = 0
    for rel in FILES:
        if (RS / rel).exists():
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RS / rel, dst / rel)
            n += 1
    for rel in DIRS:
        if (RS / rel).exists():
            n += copy_tree(RS / rel, dst / rel)
    n += copy_tree(RS / "engine" / "public" / "models", dst / "engine" / "public" / "models", MODEL_EXT) if (RS / "engine/public/models").exists() else 0
    # models dir: only top-level files (src/ holds .blend sources)
    for f in (dst / "engine" / "public" / "models").rglob("*"):
        if f.is_file() and f.parent != dst / "engine" / "public" / "models":
            f.unlink()
    n += copy_tree(RS / "examples", dst / "examples", EXAMPLE_EXT)
    (dst / "engine" / "public" / "projects").mkdir(parents=True, exist_ok=True)
    # template reels (horror kit) + their builders (scripts only: no downloads, no Blender sources, no one-off patches)
    for pid, pats in TEMPLATE_PROJECTS.items():
        src = RS / "engine" / "public" / "projects" / pid
        for pat in pats:
            for f in src.glob(pat):
                t = dst / "engine" / "public" / "projects" / pid / f.relative_to(src)
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, t)
                n += 1
    for f in (RS / "assets" / "models-src").rglob("*"):
        rel = f.relative_to(RS / "assets" / "models-src")
        if f.is_file() and f.suffix in (".py", ".md") and not f.name.startswith("patch_") and not SKIP_PARTS & set(rel.parts):
            t = dst / "assets" / "models-src" / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, t)
            n += 1
    # every shipped spec: the end card shows the buyer's channel (brand.json), not ours
    for f in list((dst / "examples").rglob("spec.json")) + list((dst / "engine" / "public" / "projects").rglob("spec.json")):
        f.write_text(json.dumps(strip_profile(json.loads(f.read_text(encoding="utf-8"))), ensure_ascii=False, indent=1), encoding="utf-8")

    # channel profile -> empty placeholders + neutral avatar (setup.py asks the buyer)
    (dst / "engine" / "src" / "brand.json").write_text(json.dumps(PLACEHOLDER_BRAND, ensure_ascii=False, indent=1), encoding="utf-8")
    av = dst / "engine" / "public" / "brand" / "avatar.jpg"
    av.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x3A2E26:s=512x512", "-frames:v", "1", str(av)], check=True)

    for s in ("reel-script", "reel-qa", "reel-analyze"):
        if (SKILLS / s).exists():
            n += copy_tree(SKILLS / s, out / "skills" / s)

    shutil.copy2(TEMPLATES / "README.md", out / "README.md")
    shutil.copy2(TEMPLATES / "AGENTS.md", out / "AGENTS.md")   # Codex, Cursor and other agents
    shutil.copy2(TEMPLATES / "CLAUDE.md", out / "CLAUDE.md")   # Claude Code (imports AGENTS.md)
    shutil.copy2(TEMPLATES / "install.sh", out / "install.sh")
    # Windows PowerShell 5.1 needs a BOM to read Cyrillic correctly
    (out / "install.ps1").write_text((TEMPLATES / "install.ps1").read_text(encoding="utf-8"), encoding="utf-8-sig")
    (out / ".gitattributes").write_text("*.sh text eol=lf\n*.ps1 text eol=crlf\n*.glb binary\n*.wav binary\n*.m4a binary\n*.MP3 binary\n*.mp3 binary\n*.jpg binary\n*.png binary\n*.webp binary\n", encoding="utf-8")
    (out / ".gitignore").write_text(".secrets.env\n.replicate_budget.json\n.venv/\nnode_modules/\n**/engine/out/\n**/engine/public/projects/*/\n!**/engine/public/projects/demo-promo/\n!**/engine/public/projects/podezd/\n!**/engine/public/projects/sosed6/\n**/engine/public/projects/*/sfx-src/\n__pycache__/\n*.pyc\n", encoding="utf-8")

    bad = scan(out)
    if bad:
        print("LEAKS FOUND — package rejected:")
        for b in bad:
            print("  ", b)
        raise SystemExit(1)

    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file() and ".git" not in f.relative_to(out).parts)
    print(f"package: {out}  ({n} files, {size / 1e6:.1f} MB) · leak scan clean")
    if zip_to:
        with zipfile.ZipFile(zip_to, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in sorted(out.rglob("*")):
                if f.is_file() and ".git" not in f.relative_to(out).parts:
                    z.write(f, Path(out.name) / f.relative_to(out))
        print(f"zip: {zip_to} ({zip_to.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
