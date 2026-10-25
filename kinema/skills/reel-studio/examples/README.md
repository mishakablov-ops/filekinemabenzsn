# Examples (complete sources)

Each folder is a full project: `script.md` (voiceover / on-screen text with markup), `spec.json` (storyboard), `words.json` (word timings), `voice.wav` (if voiced). To re-render or remix one:

```
cp -r examples/<name> engine/public/projects/<new-id>      # then edit spec.json "id" and paths "projects/<new-id>/…"
.venv/Scripts/python -I scripts/render.py <new-id>
```

| example | mode | style | what it shows |
|---|---|---|---|
| `demo-explainer` | voice, 41 s | dusk | 3D room hook → the user's MacBook with a live terminal (`toScreen` dive) → strike-through clichés → waveform → counter + notification + donut + phone → 3D montage (city / café / street / people) → sounds chips + counter → QA checklist → pricing → `blaze` slam «Нисколько» with marquee → MacBook result → iPhone 17 Pro CTA |
| `voice-demo-v2` | voice, 21.5 s | dusk | **current quality bar**: 3D in 7 of 8 scenes (office with a person, MacBook terminal dive, exploded app in CSS-3D depth, evening street with people, studio, dark-warm city `look:"dusk"`, hex tunnel slam), uppercase aggressive captions, the user's SFX pack cued on key words, Fish voice hand-directed |
| `voice-direction` | voice, 20 s | — | **the approved voice & delivery**: Fish «Мужской Профессиональный213», hand-directed script with `((cues))` and a stress fix; `approved-take.mp3` is the reference every voiced reel should match |
| `podezd` → `engine/public/projects/podezd` | voice, 1:57 | PS1 + VHS | **horror kit**: Khrushchyovka stairwell, 5 own rigged characters (neighbours facing corners, the concierge, a creature), torch-lit first person, phone, descent below the basement, cliffhanger + iPhone CTA with a new «ЧАСТЬ 2» tile. Renders as is (`render.py podezd`); sounds per its `SOUNDS.md`; builders in `assets/models-src/podezd/` |
| `sosed6` → `engine/public/projects/sosed6` | voice, 1:45 | PS1 + VHS | **57 shots ≤ 2.5 s**: ceiling footprints and crack, attic hatch with claw marks, camcorder night (`● REC`, the walker and the steps above 3 s later), audio-track insert, mailbox 24, a photo taken out and turned over by hand, 1974 photo with 6 floors, face match, handwriting insert, peephole. `vhs` captions. Builders in `assets/models-src/sosed6/` (`storyboard.py`, `voice_sections.py`, `lab.py`) |
| `nk-escape` (code only) | voice, 50 s | night | first-person escape story built from `engine/src/three/nk*.ts(x)` and `assets/models-src/nk/storyboard.py`. Its soldiers/jeep/checkpoint models are third-party (Sketchfab CC BY + Mixamo) and are **not** included — bring your own models to render it |
| `demo-promo` | music, 21 s | blaze | trap 140 bpm, music offset so the drop lands at 6.86 s; one slam card per bar; tunnel / smoke / grid floor / glow backgrounds; MacBook on the drop; screen grid, city, waveform, room, checklist, marquee, iPhone CTA |

Rendered results: `engine/out/<name>.mp4` + `<name>_qa.md` + `<name>_sheet.png`.
