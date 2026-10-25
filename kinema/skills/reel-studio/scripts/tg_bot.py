"""Telegram bot admin: read its current setup, set the menu (commands + Mini App button), name and descriptions.

    python tg_bot.py info                                  # getMe, webhook, commands, menu button, descriptions (read-only)
    python tg_bot.py menu <spec.json>                      # apply commands / menu button / descriptions from a spec file
Token: TELEGRAM_BOT_TOKEN in reel-studio/.secrets.env (never printed). Never touches the webhook or updates
(the bot's own backend keeps working).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

RS = Path(__file__).resolve().parent.parent


def token() -> str:
    t = os.environ.get("TELEGRAM_BOT_TOKEN")
    f = RS / ".secrets.env"
    if not t and f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                t = line.split("=", 1)[1].strip()
    if not t:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set (.secrets.env)")
    return t


def call(method: str, **params) -> dict:
    url = f"https://api.telegram.org/bot{token()}/{method}"
    data = json.dumps(params).encode() if params else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}") or {"ok": False, "error_code": e.code}


def info() -> None:
    me = call("getMe").get("result", {})
    wh = call("getWebhookInfo").get("result", {})
    out = {
        "bot": {k: me.get(k) for k in ("username", "first_name", "can_join_groups", "supports_inline_queries", "has_main_web_app")},
        # only whether a backend is connected, never the URL secret path
        "webhook": {"set": bool(wh.get("url")), "host": urllib.parse.urlparse(wh.get("url", "")).hostname, "pending": wh.get("pending_update_count"),
                    "last_error": wh.get("last_error_message")},
        "commands_ru": call("getMyCommands", language_code="ru").get("result"),
        "commands": call("getMyCommands").get("result"),
        "menu_button": call("getChatMenuButton").get("result"),
        "name": call("getMyName").get("result"),
        "description": call("getMyDescription").get("result"),
        "short_description": call("getMyShortDescription").get("result"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


def apply_menu(spec_path: str) -> None:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    res = {}
    if "commands" in spec:
        res["commands"] = call("setMyCommands", commands=spec["commands"]).get("ok")
        res["commands_ru"] = call("setMyCommands", commands=spec["commands"], language_code="ru").get("ok")
    if "menu_button" in spec:
        res["menu_button"] = call("setChatMenuButton", menu_button=spec["menu_button"]).get("ok")
    for key, method, field in (("name", "setMyName", "name"), ("description", "setMyDescription", "description"),
                               ("short_description", "setMyShortDescription", "short_description")):
        if key in spec:
            res[key] = call(method, **{field: spec[key]}).get("ok")
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("info", "menu"):
        raise SystemExit(__doc__)
    info() if sys.argv[1] == "info" else apply_menu(sys.argv[2])
