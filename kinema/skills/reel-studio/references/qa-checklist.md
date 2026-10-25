# QA checklist

## Automated (must pass)
| gate | tool | pass |
|---|---|---|
| script | `script_lint.py` | `LINT OK` (no clichés, hook ≤ 7 words, cards short, one accent, CTA, numbers) |
| voice | `tts_report.json` | 2.4–2.9 words/s, first word < 0.35 s, no pause > 0.8 s |
| plan | `stills.mjs --qa` | no `plan` errors (unknown blocks, anchors not found) |
| layout | `stills.mjs --qa` (every 0.5 s) | 0 overlaps caption×block / block×block / caption×3D device (projected bounds + live screens), 0 off-screen, 0 3D collisions; re-measured after late-loading models |
| format | `qa.py` | 1080×1920, h264 yuv420p, 60 fps, AAC 48 kHz |
| loudness | `qa.py` | −14 ±1 LUFS, true peak ≤ −1 dBTP |
| dead air | `qa.py` | no black frames, no frozen picture ≥ 1.5 s, no audio gap ≥ 0.8 s |
| rhythm | `qa.py` | average shot 1.2–4 s |

## Visual review — open the contact sheet and check every tile
1. **Hook (first 2 s):** something moves and the first caption is readable at 0.5 s. No logo, no fade from black.
2. **Legibility:** every caption has contrast (busy bg → scrim on); no word clipped; no orphan word on the last line; accents are the meaningful words.
3. **Layout:** nothing touches the caption band; blocks centred in their area; ≥ 60 px side margins; nothing in the bottom 420 px except deliberate CTAs.
4. **Palette:** style colours only; no pure-white panels; one accent colour per frame; red/green only for bad/good.
5. **Variety:** no two consecutive scenes with the same block or same background; at least one 3D moment per 15 s in explainers.
6. **Sync:** strikes/checks/counters/clicks hit on their words (look at the tiles around the anchors with `--seconds`).
7. **3D:** devices fully in frame (or intentionally cropped), screens readable, people not floating or intersecting, cameras not inside walls.
8. **End:** CTA visible ≥ 1.2 s after the last word, final frame clean (no half transition).

## Fix recipes
| symptom | fix |
|---|---|
| caption × block overlap | move the block to `stage` / give it `{preset:"stage", h:…}`; or shorten the card; or `"captions": {"pos": "lower"}` and move the block up |
| block × block overlap | split the stage (top/bottom or left/right with smaller `w`), or `until`+`exit` the first block |
| off-screen | reduce `w`/`size` props, use the right preset, check 3D camera distance |
| static > 4 s | add a camera move, split the scene, add a timed layer (Counter/Toast/Cursor) |
| text unreadable on 3D | `"captions": {"scrim": 0.9}` or change the camera preset |
| anchor not found | look at `words.json` texts, use a shorter/unique word or `#2` |
| loudness off | always render through `render.py` (it masters to −14 LUFS) |
| too fast / slow speech | `tts.py --rate +10%…+24% --gap 0.12…0.25` |
| voice flat / sleepy | default `--preset energetic`; more: `--widen 1.9 --emph 2.5`; compare with `voice_audition.py` + `voice_profile.py --ref <reference reels>` (target f0 ≈ 150–160 Hz, range ≈ 16 st) |
| SFX sounds cheap / 8-bit | never re-enable retired ids; import a real pack: `sfx_library.py import <folder>` |
