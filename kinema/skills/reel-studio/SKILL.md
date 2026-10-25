---
name: reel-studio
description: Make vertical 9:16 reels end-to-end — voiced explainers and first-person stories (Reels/Shorts/TikTok) and music-driven promos — with kinetic captions synced to the voice word-by-word, 90+ animated blocks (UI mockups, terminals, charts, phones), real 3D scenes (MacBook and iPhone 17 Pro models with live screens, cozy rooms, a coffee shop, a shelter, streets with simple people, city, globe, a nuclear blast, imported .blend/.glb models, and a PS1-lowpoly + VHS horror kit with own rigged characters, procedural animation and first-person hands), a lively AI voice-over (Gemini 3.1 Flash TTS via Replicate; free Edge fallback), a clean SFX library with a sound pack, 8 music beds, styles, a branded CTA end card (iPhone flips to the channel's TikTok profile) and an automated QA gate. Use whenever the user wants a ролик / видео / рилс / шортс / объяснялку / историю / промо / монтаж / анимацию для соцсетей, or asks to recreate the style of a reference video.
---

# Reel Studio

A Remotion engine + Python toolchain that turns a topic into a finished, loudness-mastered 1080×1920 MP4.
Everything lives in this skill's folder: `skills/reel-studio/` inside the KINEMA workspace (opened in Claude Code or Codex), or `~/.claude/skills/reel-studio/` for a global install:

| path | what |
|---|---|
| `engine/` | Remotion project (`src/`), assets in `engine/public/` (sfx, music, fx, models, brand, projects) |
| `engine/public/projects/<id>/` | one video: `script.md`, `voice.wav`, `words.json`, `spec.json` |
| `engine/src/brand.json` | the channel for the CTA end card: name, handle, bio, link, avatar, video-grid covers |
| `scripts/` | Python tools — run with `$PY scripts/<tool>.py` |
| `engine/tools/stills.mjs` | fast frame renders + contact sheet + overlap QA (`node tools/stills.mjs …`, run from `engine/`) |
| `references/` | **read before building**: `storyboard.md`, `captions.md`, `blocks.md` (generated catalog), `3d.md`, `styles.md`, `sound.md`, `spec.md`, `qa-checklist.md`, `script-formula.md`, `horror-kit.md` (PS1 + VHS horror reels), `refs/` (style briefs of reference reels) |
| `examples/` | complete projects with sources: `coffee-agent` (first-person story, 38 s), `nuclear-survival` (1:27, survival guide), `aipollon-agent`, `voice-direction`, `voice-demo-v2` |

Shell vars used below: `RS=<this skill folder>`, `PY="$RS/.venv/Scripts/python -I"` on Windows or `PY="$RS/.venv/bin/python -I"` on macOS/Linux.

## 0 · First run: connections (always check before the first reel of a session)

```
$PY $RS/scripts/setup.py --check        # JSON status, exit 1 if something required is missing
```
If `ready` is false, fix `missing_required` before building:
- **Install pieces** (Python packages, `npm install` in `engine/`, ffmpeg, Node 18+) → tell the user to run the installer from the package (`install.ps1` / `install.sh`) or run the missing step yourself (`npm install` in `engine/`, `$PY -m pip install -r requirements.txt`).
- **Keys** (`REPLICATE_API_TOKEN` required for the main voice; `FISH_API_KEY`, `ELEVENLABS_API_KEY` optional) → ask the user to run `python scripts/setup.py` in a terminal (keys are typed hidden). If they paste a key into the chat instead, write it into `$RS/.secrets.env` as `KEY=value` with a file tool — never echo it back, never put it in a command line, URL or log.
- **Channel profile** (name, handle, bio, link, avatar for the end card) → ask the user in chat and save with `$PY $RS/scripts/setup.py --brand name=… handle=… bio=… link=… badge=… avatar=<image path>`.
Never invent a handle, link or follower numbers for the profile.

## Quality bar (non-negotiable)

1. **No AI-template look.** No stock "AI brain" visuals, no emoji in captions, no rainbow gradients, no generic blobs as filler (Shapes3D only as a deliberate accent). Real UI, real numbers, real objects.
2. **Palette:** default style `dusk` — flat dark pastel (warm charcoal, beige type, terracotta/orange accents). No pure white surfaces; light videos use `sand`. Few colours per scene, flat fills over gradients. Aggressive moments use `blaze` (or `brutal`).
3. **Nothing overlaps anything.** Captions never cover blocks; blocks never cover each other unless `overlap: true` on purpose. 3D people never walk through furniture or each other; the camera never enters geometry. The QA gate enforces it — a reel that fails QA is not delivered.
4. **Captions = the voice.** Word-by-word reveal timed from the TTS (±50 ms), one accent per card, short cards (punch ≤ 34 chars, slam ≤ 16), hook card ≤ 7 words. "Aggressive typography" means a lot of interesting things happening on screen: big punch lines, `BigType`, counters, cards, screens.
5. **Rhythm:** something moves every 1.2–4 s (cut, camera move, block entrance, internal event). **No flash cuts — every shot ≥ 1 s** (QA error below `MIN_SHOT`). Land fast actions on the word *inside* a longer shot (Room3D `doorAt`, stepped `days`) instead of a 0.3 s cut.
6. **3D in nearly every scene**, backgrounds full of content, cozy and detailed. First person = a head-cam (`fpv*` cams / `head: true`): no hands in frame, wide fov, never through walls. One recurring hero: `look: {hero: true}` (young guy in a white cap).
7. **Sound is designed, not sprinkled.** No airy noise: transition whooshes, wind, breathing and tape rips are retired. Prefer `"autoSfx": false` + hand-placed cues in `spec.sfx`, mostly from the included pack (`pk-click-ui-button`, `pk-pop-ui-menu`, `pk-digital-data-load-sfx-1`, `pk-digital-digitasl-burst-sfx`, `pk-shimmer-ui-dissolvre-sfx`, `pk-notify-notification-sfx-1`, `pk-notify-system-alert-sfx`, `pk-result-failure`) plus a few clear cinematic hits (nuke-boom, shockwave-hit, door-heavy-close, siren, geiger, dread-rise). Never the same sound twice back to back. Music ducks under the voice; master −14 LUFS / −1 dBTP. Another pack: `$PY $RS/scripts/sfx_library.py import <folder|zip>`.
8. **Voice:** lively, not theatrical; **no whispering**; no long pauses ("not a film"). Never time-stretch, re-pitch or dynamically compress a hosted take.

## The algorithm

**0 · Brief.** Decide mode (`explainer` with voice / `promo` to music), length (explainer 30–60 s, story 35–45 s, promo 15–30 s), style, CTA. If a reference video is given, run `reel-analyze` first and copy its *structure*, then beat it on the quality bar. Ask only for what you cannot infer (product facts).

**1 · Facts.** Concrete numbers, names, UI details. Every 2nd–3rd card should carry a fact or a concrete image.

**2 · Script.** Follow `reel-script` (formula, markup, anti-cliché rules). Write `projects/<id>/script.md`:
```
$PY $RS/scripts/new_project.py <id> --style dusk --music lofi-warm       # skeleton
$PY $RS/scripts/script_lint.py $RS/engine/public/projects/<id>            # must end with LINT OK
```
End voiced reels with the channel CTA (`brand.json → cta`) over the last frames.

**3 · Voice + timings.** Default: **Gemini 3.1 Flash TTS, voice «Algenib»** on Replicate — one call per section with its own English direction (see `examples/coffee-agent/voice_sections.py`): 2 takes per section, pick by Whisper text check + `voice_profile.py`, level each take with static gain (`loudnorm.py … --lufs -16`), glue untouched, then align:
```
$PY $RS/scripts/fish_tts.py --join <project>/voice_raw.wav --parts take1.wav take2.wav …     # glue with short fades
$PY $RS/scripts/tts.py <project> --engine audio --audio <project>/voice_raw.wav --tighten 0.25   # cut silences only + word timings
```
One-take shortcut: `$PY $RS/scripts/tts.py <project> --engine replicate --model gemini --voice Algenib --style "<direction>" --tighten 0.25`.
Direction that works: "native Russian narrator, warm and lively, brisk pace, very short pauses, never whispering" + a per-section mood. Stress: mark risky words `{слово|сл+ово}`, keep `assets/stress_ru.txt` growing; the user's ear decides stress tests.
Alternatives: Fish Audio (`--engine fish --voice <model_id>`, `FISH_API_KEY`; hand-directed with `((cues))` like `examples/voice-direction/`), ElevenLabs (`--engine eleven --voice <id>`), the user's own recording (`--engine audio --audio take.wav`), free Edge voice (`--preset energetic`, no key), `--engine silent --beats …` (promo). When the voice changes, send loudness-matched samples (`voice_audition.py`) and let the user choose by ear. Target 2.3–2.9 words/s in `tts_report.json`.

**4 · Storyboard → `spec.json`.** Read `references/storyboard.md`, `references/blocks.md`, `references/3d.md`. Best done as a small Python builder like `examples/coffee-agent/storyboard.py`. One scene per 1–3 caption cards; anchor everything to words (`"@слово"`, `"@фраза"`, `"@слово#2"`, `"@слово+0.2"`). Per beat: hook → strongest visual (3D or BigType); places → `Room3D` (office, living, bedroom, cafe, studio, library, kitchen, cabin, basement) / `Street3D` / `City3D`; product on a device → `MacBook` / `IPhone17` (live screens, `cam: "toScreen"`); facts → counters, charts, `Bars3D`; process → `ClaudeChat`, terminal, app screens, `Checklist`; punch → `blaze` slam / `BigType`. Vary layouts every 2–3 scenes; never the same block twice in a row.
**CTA end card:** last scene keeps the story's final 3D shot as background (`"dim": 0.55, "dimAt": "@Кстати"`) with a full-frame `IPhone17` layer: `enter: "flip"` (rises showing its back, flips at `flipAt`), `screen: {block: "TikTokProfile", props: {highlightAt: "@шапку"}}` (profile from `brand.json`), camera push-in on the bio. Copy it from `examples/coffee-agent/storyboard.py`.

**5 · Preview + QA loop.**
```
cd $RS/engine && node tools/stills.mjs --props '{"project":"<id>"}' --qa --seconds 1.5,4,7,… --scale 0.4 --out out/<id>_st --sheet out/<id>_sheet.png --cols 8
```
**Read the sheet image** and check it against `references/qa-checklist.md`: heads below the caption band (y > 650 px), nobody blocking the subject, cameras looking at the back/left walls of cut-away rooms (never into the open side), legible screens. Fix → repeat until `QA PASS` and the sheet looks right.

**6 · Final render + QA.**
```
$PY $RS/scripts/render.py <id>            # 60 fps, CRF 16, -14 LUFS master, cover added to brand.json tiles, then qa.py
$PY $RS/scripts/render.py <id> --preview  # 30 fps half-res check of motion & sound
```
Output `engine/out/<id>.mp4`, report `engine/out/<id>_qa.md`, contact sheet `<id>_sheet.png`. Fix every ERROR; justify or fix WARNs.

**7 · Deliver.** The MP4, duration, what's inside, the QA summary; offer variants. Copy good projects into `examples/`.

## Promo mode (music, no voice)
```
$PY $RS/scripts/new_project.py <id> --mode promo --music drive-promo      # or your own track:
$PY $RS/scripts/beats.py my_track.mp3 --out $RS/engine/public/music/my_track.beats.json
$PY $RS/scripts/tts.py $RS/engine/public/projects/<id> --engine silent --beats $RS/engine/public/music/drive-promo.beats.json --every 2
```
Cards land on beats; scenes anchor to `"beat:16"`, `"bar:8"`, `"drop:0"`; slam captions + `camera: punch` on bars; big moments on drops.

## Horror / story reels in PS1 + VHS style (1.5–2 min)
For creepy first-person stories, analog-tape horror, "found footage": read **`references/horror-kit.md`** first.
Templates: `engine/public/projects/podezd` and `engine/public/projects/sosed6` (render as they are; sounds per their `SOUNDS.md`).
The look: lowpoly faceted models, 64–128 px textures, 184×326 render with vertex jitter and dither, VHS overlay (`▶ PLAY` or camcorder `● REC`), `vhs` captions.
Shots are custom three.js scenes in one component per reel (shot ids + `ev` timings from a Python storyboard), 1–2.5 s each, own characters
(T-pose reference → image-to-3D → `rig_chars.py`) posed procedurally (`human.ts`), first-person hands (`fphands.ts`). Check single shots with
`assets/models-src/sosed6/lab.py <shot…> --project <id>`; never deliver a black, floating-object or arm-in-the-lens frame.
Replicate spending is capped at $3 per job (`REPLICATE_JOB=<id>`); ask the user before raising `REPLICATE_CAP_USD`.

## Real 3D models
`MacBook` and `IPhone17` use the included GLBs in `engine/public/models/` (iPhone stands upright, camera plateau at the top). New models (BlenderKit / Sketchfab / any .blend .fbx .obj .glb): `$PY $RS/scripts/import_models.py [folder|file]` — Blender runs headless with `--disable-autoexec`, the display mesh is auto-detected; then `Model3D` with `src`, `screenMaterial`, `rot`. Details: `references/3d.md`.

## When something breaks
- `phrase not found in voiceover` → the anchor differs from `words.json` (spelling/ё, use a shorter anchor or `#2`).
- Device too small or cropped in 9:16 → portrait needs distance; see camera presets in `references/3d.md`.
- Replicate 401 → the token is wrong/expired: `python scripts/setup.py`. 429 → retried automatically. A take blocked by a safety filter → rephrase the line.
- Edge TTS `NoAudioReceived` → transient; re-run.
- Render slow → `--concurrency` = CPU threads / 2, previews at 30 fps, Street3D `people` ≤ 16.

## Related skills
`reel-script` (writing the voiceover), `reel-qa` (checking any video), `reel-analyze` (deconstructing a reference reel).
