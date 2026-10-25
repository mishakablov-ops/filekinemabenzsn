# KINEMA — instructions for the AI agent working in this folder

This folder is **KINEMA**, a video engine: you (Claude Code, Codex, Cursor or any coding agent) turn a topic into a finished
vertical reel (MP4 1080×1920, 60 fps) — script, voice-over, word-synced captions, 3D scenes, sound, branded end card, QA.
The user talks to you in Russian; answer in Russian.

## Layout
| path | what |
|---|---|
| `skills/reel-studio/SKILL.md` | **the main algorithm — read it fully before making a video** |
| `skills/reel-studio/references/` | storyboard, captions, blocks catalog, 3D, styles, sound, spec format, QA checklist |
| `skills/reel-studio/examples/` | finished projects with sources (`coffee-agent` is the best template) |
| `skills/reel-studio/engine/` | the renderer (Remotion + three.js); projects in `engine/public/projects/<id>/`, results in `engine/out/` |
| `skills/reel-studio/scripts/` | Python tools (setup, voice, lint, render, QA) |
| `skills/reel-script/`, `skills/reel-qa/`, `skills/reel-analyze/` | writing scripts, checking a video, deconstructing a reference reel |

`RS` below = `skills/reel-studio`. Python: `RS/.venv/Scripts/python -I` (Windows) or `RS/.venv/bin/python -I` (macOS/Linux).

## First run (when `RS/.venv` or `RS/engine/node_modules` is missing, or the user says «установи / настрой»)
1. Install in place (needs network — ask the user to allow it if your sandbox blocks network):
   - Windows: `powershell -ExecutionPolicy Bypass -File install.ps1 -NoWizard`
   - macOS / Linux: `bash install.sh --no-wizard`
2. Check: `RS/.venv/... RS/scripts/setup.py --check` → JSON with `missing_required`.
3. Missing keys: ask the user to run `python skills/reel-studio/scripts/setup.py` in a terminal (keys are typed hidden). If they paste a key into the chat, write it to `RS/.secrets.env` as `KEY=value` with a file edit — never echo it, never put it in a command line, URL or log. Keys: `REPLICATE_API_TOKEN` (required, main voice), `FISH_API_KEY`, `ELEVENLABS_API_KEY` (optional).
4. Missing channel profile: ask for name, handle, bio, link and an avatar image, then
   `setup.py --brand name=… handle=… bio=… link=… avatar=<path>`. Never invent a handle, link or numbers.

## Making a video
Follow `RS/SKILL.md` step by step: brief → facts → script (`script_lint.py` must pass) → voice (`tts.py`) →
storyboard `spec.json` (a small Python builder like `examples/coffee-agent/storyboard.py`) → stills + QA loop
(`engine/tools/stills.mjs --qa`, look at the contact sheet) → `render.py <id>` → deliver `engine/out/<id>.mp4` with the QA summary.
Long renders (minutes) — run them in the background if your tool allows it.
Horror / creepy story series (PS1 lowpoly + VHS, 1.5–2 min): read `RS/references/horror-kit.md`; the templates
`RS/engine/public/projects/podezd` and `…/sosed6` render as they are (`render.py podezd`). Their sounds are not
shipped — the user adds them by the list in each project's `SOUNDS.md`; missing sounds are skipped, never invented.
Replicate spending is capped at $3 per job (`REPLICATE_JOB=<id>`); ask the user before raising `REPLICATE_CAP_USD`.

## Non-negotiable quality rules (details in SKILL.md)
- Nothing overlaps; 3D people never clip through furniture; the camera never enters geometry.
- Every shot ≥ 1 s; something moves every 1.2–4 s; 3D in nearly every scene; dark warm palette by default.
- Captions are word-exact to the voice; lively voice, no whispering, no long pauses; never time-stretch a voice take.
- No airy noise SFX; cues mostly from the included pack; master −14 LUFS.
- A render that fails `qa.py` is not delivered.

## Safety
Never print or commit `.secrets.env`. Do not send the user's keys, e-mail or files to any service except the ones the pipeline uses (Replicate, Fish Audio, ElevenLabs).
