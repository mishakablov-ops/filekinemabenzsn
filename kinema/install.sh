#!/usr/bin/env bash
# KINEMA — установка для macOS / Linux
#   bash install.sh               ставит всё прямо в эту папку + мастер подключения
#   bash install.sh --no-wizard   без вопросов (так ставит агент: Claude Code, Codex…)
#   bash install.sh --global      дополнительно ставит скиллы в ~/.claude/skills
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RS="$HERE/skills/reel-studio"
WIZARD=1; GLOBAL=0
for a in "$@"; do
  case "$a" in --no-wizard) WIZARD=0 ;; --global) GLOBAL=1 ;; esac
done
echo; echo "=== KINEMA: установка ==="; echo

# 0. по желанию — копия скиллов для Claude Code во всех папках (ключи, профиль и проекты при обновлении сохраняются)
if [ "$GLOBAL" = 1 ]; then
  SKILLS="$HOME/.claude/skills"; GRS="$SKILLS/reel-studio"; mkdir -p "$SKILLS"
  KEEP=(".secrets.env" "engine/src/brand.json" "engine/public/brand"); TMP="$(mktemp -d)"
  if [ -d "$GRS" ]; then for k in "${KEEP[@]}"; do [ -e "$GRS/$k" ] && { mkdir -p "$TMP/$(dirname "$k")"; cp -R "$GRS/$k" "$TMP/$k"; }; done; fi
  for s in reel-studio reel-script reel-qa reel-analyze; do mkdir -p "$SKILLS/$s"; cp -R "$HERE/skills/$s/." "$SKILLS/$s/"; done
  for k in "${KEEP[@]}"; do [ -e "$TMP/$k" ] && { rm -rf "$GRS/$k"; cp -R "$TMP/$k" "$GRS/$k"; }; done
  rm -rf "$TMP"; RS="$GRS"
  echo "Скиллы скопированы в $SKILLS"
fi

# 1. Python 3.10+ и окружение
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Нужен Python 3.10+ (https://www.python.org)"; exit 1; }
[ -x "$RS/.venv/bin/python" ] || { echo "Создаю окружение Python…"; "$PY" -m venv "$RS/.venv"; }
echo "Ставлю пакеты Python (распознавание речи, голос)…"
"$RS/.venv/bin/python" -m pip install --upgrade pip -q
"$RS/.venv/bin/python" -m pip install -q -r "$RS/requirements.txt"

# 2. Node.js 18+ и движок
command -v node >/dev/null || { echo "Нужен Node.js 18+ (https://nodejs.org, версия LTS)"; exit 1; }
NV="$(node --version | sed 's/^v//; s/\..*//')"
[ "$NV" -ge 18 ] || { echo "Node.js $NV слишком старый — нужен 18+"; exit 1; }
echo "Ставлю движок рендера (npm, это пара минут)…"
( cd "$RS/engine" && (npm ci --no-audit --no-fund || npm install --no-audit --no-fund) && (npx remotion browser ensure || true) )

# 3. ffmpeg
command -v ffmpeg >/dev/null || { echo; echo "ffmpeg не найден: macOS — brew install ffmpeg, Ubuntu/Debian — sudo apt install ffmpeg"; }

# 4. мастер подключения (ключи, канал, звуки)
if [ "$WIZARD" = 1 ]; then "$RS/.venv/bin/python" "$RS/scripts/setup.py"; else "$RS/.venv/bin/python" "$RS/scripts/setup.py" --check || true; fi
echo; echo "Готово. Откройте эту папку в Claude Code или Codex и напишите: «сделай ролик про …»"; echo
