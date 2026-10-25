"""Reel Studio setup: check what is connected and ask for what is missing (keys, channel profile, sound pack).

    python setup.py              interactive wizard in a terminal (keys are typed hidden, never printed)
    python setup.py --check      status as JSON; exit code 1 when something REQUIRED is missing
    python setup.py --brand name=... handle=... bio=... link=... badge=... avatar=<image file>   (non-secret, for the agent)

Keys live in reel-studio/.secrets.env (KEY=value lines, never committed, never printed):
    REPLICATE_API_TOKEN   required for the main voice (Gemini 3.1 Flash TTS «Algenib») — replicate.com/account/api-tokens
    FISH_API_KEY          optional: Fish Audio voices (API credit) — fish.audio → API Keys
    ELEVENLABS_API_KEY    optional: ElevenLabs voices
Without any key the free Microsoft Edge voice still works (`tts.py --preset energetic`).
"""
from __future__ import annotations

import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

RS = Path(__file__).resolve().parent.parent
ENGINE = RS / "engine"
SECRETS = RS / ".secrets.env"
BRAND = ENGINE / "src" / "brand.json"
AVATAR = ENGINE / "public" / "brand" / "avatar.jpg"
PY = sys.executable

KEYS = [
    ("REPLICATE_API_TOKEN", True, "голос по умолчанию (Gemini 3.1 · Algenib) через Replicate", "https://replicate.com/account/api-tokens"),
    ("FISH_API_KEY", False, "голоса Fish Audio (нужен API-баланс)", "https://fish.audio → API Keys"),
    ("ELEVENLABS_API_KEY", False, "голоса ElevenLabs", "https://elevenlabs.io → Profile → API key"),
]


# ------------------------------------------------------------------ secrets file
def read_secrets() -> dict[str, str]:
    out: dict[str, str] = {}
    if SECRETS.exists():
        for line in SECRETS.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def write_secret(key: str, value: str) -> None:
    lines = SECRETS.read_text(encoding="utf-8").splitlines() if SECRETS.exists() else ["# Reel Studio keys — never share or commit this file"]
    lines = [ln for ln in lines if not ln.startswith(key + "=")] + [f"{key}={value}"]
    SECRETS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(SECRETS, 0o600)
    except OSError:
        pass


def verify_replicate(token: str) -> bool | None:
    """True = token works, False = rejected, None = could not check (offline)."""
    req = urllib.request.Request("https://api.replicate.com/v1/account", headers={"Authorization": f"Bearer {token}", "User-Agent": "reel-studio-setup"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        return False if e.code in (401, 403) else None
    except Exception:
        return None


# ------------------------------------------------------------------ checks
def tool_version(cmd: list[str]) -> str | None:
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        r = subprocess.run([exe] + cmd[1:], capture_output=True, text=True, timeout=20)
        return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else "ok"
    except Exception:
        return None


def check() -> dict:
    s = read_secrets()
    env = {k: bool(os.environ.get(k) or s.get(k)) for k, *_ in KEYS}
    py_ok = {}
    for mod in ("numpy", "faster_whisper", "edge_tts"):
        try:
            __import__(mod)
            py_ok[mod] = True
        except Exception:
            py_ok[mod] = False
    node = tool_version(["node", "--version"])
    brand = json.loads(BRAND.read_text(encoding="utf-8")) if BRAND.exists() else {}
    st = {
        "python": sys.version.split()[0],
        "python_packages": py_ok,
        "ffmpeg": bool(tool_version(["ffmpeg", "-version"])) and bool(tool_version(["ffprobe", "-version"])),
        "node": node,
        "engine_installed": (ENGINE / "node_modules" / "remotion").exists(),
        "keys": env,
        "brand": {k: bool(brand.get(k)) for k in ("name", "handle", "bio", "link")} | {"avatar": AVATAR.exists()},
        "models": sorted(p.name for p in (ENGINE / "public" / "models").glob("*.glb")),
        "sfx_pack": any(p.name.startswith("pk-") for p in (ENGINE / "public" / "sfx").rglob("*.wav")),
    }
    missing = []
    if sys.version_info < (3, 10):
        missing.append("Python 3.10+")
    missing += [f"pip: {m}" for m, ok in py_ok.items() if not ok]
    if not st["ffmpeg"]:
        missing.append("ffmpeg + ffprobe в PATH")
    if not node:
        missing.append("Node.js 18+")
    if not st["engine_installed"]:
        missing.append("npm install в engine/")
    missing += [k for k, req, *_ in KEYS if req and not env[k]]
    missing += [f"brand.{k}" for k in ("name", "handle", "link") if not st["brand"][k]]
    st["missing_required"] = missing
    st["ready"] = not missing
    return st


# ------------------------------------------------------------------ brand
def set_brand(fields: dict[str, str]) -> None:
    brand = json.loads(BRAND.read_text(encoding="utf-8")) if BRAND.exists() else {}
    for k in ("name", "handle", "badge", "bio", "link", "cta"):
        if k in fields:
            v = fields[k].strip()
            brand[k] = v.lstrip("@") if k == "handle" else v
    if fields.get("avatar"):
        src = Path(fields["avatar"]).expanduser()
        if not src.exists():
            raise SystemExit(f"аватар не найден: {src}")
        AVATAR.parent.mkdir(parents=True, exist_ok=True)
        # centre square, 512 px, jpg — ffmpeg reads png/jpg/webp/heic(if built in)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vf",
                        "crop='min(iw,ih)':'min(iw,ih)',scale=512:512", "-q:v", "2", str(AVATAR)], check=True)
        brand["avatar"] = "brand/avatar.jpg"
    brand.setdefault("tiles", [])
    BRAND.write_text(json.dumps(brand, ensure_ascii=False, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ wizard
def ask(prompt: str, default: str = "") -> str:
    v = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return v or default


def wizard() -> None:
    print("\n=== Reel Studio · подключение ===\n")
    st = check()
    print(f"Python {st['python']} · ffmpeg {'ок' if st['ffmpeg'] else 'НЕТ'} · Node {st['node'] or 'НЕТ'} · движок {'ок' if st['engine_installed'] else 'не установлен'}")
    if not st["ffmpeg"]:
        print("  ffmpeg: Windows — `winget install Gyan.FFmpeg`, macOS — `brew install ffmpeg`, Linux — `sudo apt install ffmpeg`")
    if not st["node"]:
        print("  Node.js 18+: https://nodejs.org (LTS)")

    print("\n— Ключи (вводятся скрыто, хранятся только в .secrets.env на этом компьютере) —")
    for key, required, what, where in KEYS:
        have = st["keys"][key]
        tag = "обязательно" if required else "по желанию"
        print(f"\n{key} ({tag}): {what}\n  где взять: {where}")
        if have and ask("  уже подключён. Заменить? (y/N)", "n").lower() != "y":
            continue
        val = getpass.getpass("  вставьте ключ (Enter — пропустить): ").strip()
        if not val:
            print("  пропущено" + (" — без него голос по умолчанию недоступен (будет бесплатный Edge-голос)" if required else ""))
            continue
        if key == "REPLICATE_API_TOKEN":
            ok = verify_replicate(val)
            print("  ключ работает ✓" if ok else "  Replicate отклонил ключ — проверьте его" if ok is False else "  не удалось проверить (нет сети) — сохраняю")
            if ok is False:
                continue
        write_secret(key, val)
        print("  сохранено ✓")

    print("\n— Ваш канал (для финальной заставки: айфон с вашим профилем TikTok) —")
    brand = json.loads(BRAND.read_text(encoding="utf-8")) if BRAND.exists() else {}
    fields = {
        "name": ask("Имя профиля (крупно, как в TikTok)", brand.get("name", "")),
        "handle": ask("Ник без @", brand.get("handle", "")),
        "badge": ask("Подпись после ника (например Verified business, можно пусто)", brand.get("badge", "")),
        "bio": ask("Описание профиля (шапка)", brand.get("bio", "")),
        "link": ask("Ссылка в профиле", brand.get("link", "")),
        "cta": ask("Фраза-подводка в конце роликов", brand.get("cta", "Кстати, этот ролик собрал агент. Хочешь так же? Тебе в шапку профиля.")),
    }
    av = ask("Путь к аватарке (jpg/png; Enter — оставить текущую)", "")
    if av:
        fields["avatar"] = av.strip('"')
    set_brand(fields)
    print("  профиль сохранён ✓")

    print("\n— Звуки —")
    print("  В комплекте уже есть пак интерфейсных звуков. Свой пак можно добавить в любой момент:")
    pack = ask("  папка или .zip с вашими звуками (Enter — пропустить)", "")
    if pack:
        subprocess.run([PY, "-I", str(RS / "scripts" / "sfx_library.py"), "import", pack.strip('"')])

    st = check()
    print("\n=== Готово ===" if st["ready"] else "\n=== Осталось подключить ===")
    for m in st["missing_required"]:
        print("  •", m)
    if st["ready"]:
        print("Откройте Claude Code и напишите: «сделай ролик про …»")


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--check":
        st = check()
        print(json.dumps(st, ensure_ascii=False, indent=1))
        sys.exit(0 if st["ready"] else 1)
    if args and args[0] == "--brand":
        set_brand(dict(a.split("=", 1) for a in args[1:] if "=" in a))
        print("brand saved:", BRAND)
        return
    wizard()


if __name__ == "__main__":
    main()
