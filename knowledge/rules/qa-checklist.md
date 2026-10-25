# QA checklist

Before reviewing a reel, read the user's saved presentation requirements in [styles.md](styles.md), especially the section updated 2026-10-21. Automated layout checks do not detect every internal UI or animation defect.

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

## Mandatory checks learned from the user's corrections

1. **Book:** inspect the lift, middle, landing and any loop boundary. The page stays attached to the spine and never moves below the page stack or outside the covers when resting.
2. **Devices:** inspect both sides and intermediate turn angles. The UI fills the display, follows its real contour and perspective, preserves its aspect ratio, and never covers the casing or a foreground person.
3. **Hands and seating:** verify hand contact with the book, phone and keyboard; no hands through the desk, floating props, people beside their chairs or feet without support.
4. **Avatar:** compare with the supplied original. Check the complete circular crop, centring and actual source dimensions; no displaced black crescent or distorted image. Do not regenerate the user's artwork.
5. **Terminal:** inspect the first line, typing, result and scrolling. The header remains separate, all required rows fit, and the result appears after the command finishes typing. An outer block overlap check alone is insufficient.
6. **Final MP4:** reproduce each user-reported moment in the encoded deliverable and inspect the relevant region at a readable size. Keep the corrected scenes' targeted regression checks alongside the ordinary QA gate.
7. **Music:** check the finished mix at the opening, achievements, quieter final speech and ending. The music follows the story, words remain clear, phrase extensions have smooth joins, and the ending fades naturally. Use the user-approved v5 music treatment documented in [sound.md](sound.md) as a reference when appropriate.

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
