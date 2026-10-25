---
name: reel-analyze
description: Deconstruct a reference reel / short / promo video (the user's examples or a competitor's) into a reusable style brief — transcript with word timings and pace, shot lengths and cuts, caption system (position, hierarchy, accents, reveal), backgrounds, block types, transitions, palette, loudness, script formula — and map it onto reel-studio blocks and styles so the next video matches or beats it. Use when the user sends a video and says «сделай так же», «разбери ролик», «в таком стиле», or before recreating a style.
---

# Reel analyze

```
$PY ~/.claude/skills/reel-studio/scripts/analyze_ref.py video.mp4 [--out DIR] [--whisper small|medium]
```
(`$PY` = `~/.claude/skills/reel-studio/.venv/Scripts/python -I` on Windows, `.venv/bin/python -I` on macOS/Linux.) It writes contact sheets (1 frame/s), `transcript.txt` (words + timings), `cuts.txt`, and `report.md` with pace, pauses, shot lengths, dominant colours and brightness.

## Then look — the numbers are not enough
1. Read every `sheet_*.png` in order. Note per second: background family, blocks on screen, caption position/size/hierarchy, accent treatment (serif italic? colour? box?), entrance/exit style, transitions, camera moves.
2. Read `transcript.txt` and write the beat list (hook → … → CTA) with timestamps.
3. Zoom into 2–3 key moments at full resolution: `ffmpeg -ss T -i video.mp4 -frames:v 1 f.png`.
4. Check sound: is there music under the voice, SFX on cuts? (`ffmpeg -i video.mp4 -af ebur128` for loudness; listen-free heuristics: silencedetect gaps.)

## Style brief (write it, keep it short)
- **Format:** duration, words/s, shots/s, loudness.
- **Captions:** mode (editorial/subtitle/slam), band, sizes, accents → reel-studio `captions` settings.
- **Visual system:** backgrounds → styles/bg blocks; mockups → blocks (AppScreen, Terminal, GithubRepo…); 3D → Laptop3D/Phone3D/Globe3D/Room3D…
- **Motion:** transitions & camera → spec names.
- **Script formula:** beat list with timing.
- **Beat it:** 3–5 concrete improvements (e.g. "static shots > 4 s at 0:41 → add camera move", "captions over busy photo → scrim", "no 3D moment in the middle → add City3D dive").

Hand the brief to `reel-studio` (step 4 storyboard). Keep briefs of reference reels in `~/.claude/skills/reel-studio/references/refs/<name>.md` for reuse.
