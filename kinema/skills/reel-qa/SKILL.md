---
name: reel-qa
description: Quality-check a short vertical video (any MP4, or a reel-studio project) before publishing — format, loudness (−14 LUFS), black/frozen frames, silences, cut rhythm, caption pace, overlaps between captions and blocks, 3D collisions — produce a report and a contact sheet, review it visually, and fix the project. Use when the user asks to проверить ролик / QA / почему ролик плохой / что улучшить, and always before delivering a reel-studio render.
---

# Reel QA

Tools live in `~/.claude/skills/reel-studio` (`RS`). Python `$PY`: `$RS/.venv/Scripts/python -I` (Windows) or `$RS/.venv/bin/python -I` (macOS/Linux).

## 1. Automated report
```
$PY $RS/scripts/qa.py path/to/video.mp4 [--project <id>]
```
- Without `--project`: format, loudness, black, freeze, silence, rhythm, contact sheet — works for ANY video (also competitors' / reference reels).
- With `--project`: also caption pace from `words.json` and the engine's layout QA (renders frames every 0.5 s with `qa:true`; overlaps are drawn in magenta and listed).
Outputs `<video>_qa.md`, `<video>_qa.json`, `<video>_sheet.png`. Exit code 1 = FAIL.

## 2. Visual review (always)
Read `<video>_sheet.png` (1 tile per 1.5 s) and go through `$RS/references/qa-checklist.md` → "Visual review". For suspicious moments render exact frames:
```
cd $RS/engine && node tools/stills.mjs --comp Reel --props '{"project":"<id>","fps":30}' --seconds 3.2,7.9 --scale 0.5 --out out/check --sheet out/check.png --qa
```
For a plain MP4: `ffmpeg -ss 7.9 -i video.mp4 -frames:v 1 frame.png` and read it.

## 3. Fix loop (reel-studio projects)
Map each finding to a fix (table in qa-checklist.md), edit `spec.json` / `script.md`, re-run stills QA, then re-render with `scripts/render.py <id>`. Never deliver with ERRORs; report remaining WARNs with a reason.

## 4. Report to the user
Status (PASS/FAIL), the 3–5 most important findings in plain words, what was fixed, file paths.
