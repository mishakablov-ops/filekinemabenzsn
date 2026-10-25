---
name: reel-script
description: Write voiceover scripts for short vertical videos (Reels/Shorts/TikTok explainers and music promos) in Russian or English — strong hook in the first 2 seconds, concrete numbers, no AI clichés («давайте разберёмся», «не просто X, а Y», «революционный»), caption-card markup for kinetic subtitles, then lint it. Use when the user asks for a сценарий / текст для ролика / озвучку / закадр / хук, or as step 2 of the reel-studio pipeline.
---

# Reel script

Read `~/.claude/skills/reel-studio/references/script-formula.md` first — it has the measured structure (2.7 words/s, 45 s ≈ 115 words), hook patterns, banned phrases and the markup.

## Steps
1. **Gather facts** (numbers, names, exact commands, prices). No fact → no sentence. Never invent numbers; if a fact is unknown, ask or phrase without it.
2. **Pick the arc** from script-formula.md (explainer / news / promo). Write the beat list first (one line per beat), then sentences.
3. **Write cards:** one caption card per line, `подводка // ударная часть`, one accent per card (`*курсив*`, `[цвет]`, `==плашка==`, `~~зачёркнуто~~`), numbers as `{88|восемьдесят восемь}` when the voice must read them in words, `%slam` for punches.
4. **Cut 20 %.** Remove every word that the picture already says. Kill adjectives without facts.
5. **Lint:** `$PY ~/.claude/skills/reel-studio/scripts/script_lint.py <project_dir or script.md>` (Python: `.venv/Scripts/python -I` (Windows) or `.venv/bin/python -I` (macOS/Linux) inside `~/.claude/skills/reel-studio`) → fix until `LINT OK`; handle warnings consciously.
6. **Read-aloud test:** 2.7 words/s; no card < 0.5 s or > 3 s; the hook is understood without the picture.

## Voice notes
- **Stress (ударение).** Any word a TTS might misstress gets a mark for the voice only: `{по косточкам|по к+осточкам}` ("+" before the stressed vowel; it reaches Fish as a combining acute — ко́сточкам — never as "+", which Fish reads as «плюс»). Common offenders are fixed automatically from `reel-studio/assets/stress_ru.txt` — add every new one the user catches.
- **Always hand-direct** (the user approved this over automatic direction): follow `reel-studio/examples/voice-direction/script.md`.
- **Direct the voice like a voice-over session.** `voice_direct.py` already adds: rise on the hook, rising intonation on questions, a beat before the punchline, `[emphasis]` on accent words, warm CTA. Add `((cue))` where the meaning needs a different colour: `((worried))` on the pain word, `((playful))` on a joke, `((fast))` on lists, `((long pause))` before a reveal, `((shouting, very excited))` on the slam answer, `((whispering))` on a secret, `((smiling))` on the CTA. Cues never reach captions. 1–2 per card at most; check `voice_direct.py <project>` output before generating.
- Default voice: `tts.py --preset energetic` (Dmitry, raised and livelier, accent words lifted — so mark the 1–2 words per card that carry the meaning with *…* / […] / ==…==; they are the words the voice stresses). Presets `andrew` / `remy` are multilingual voices reading Russian (may carry a light accent — let the user judge), `calm` for serious topics. Female: `--voice ru-RU-SvetlanaNeural --preset calm`.
- Better voice: ElevenLabs (`--engine eleven`, needs `ELEVENLABS_API_KEY`) or the user's own recording (`--engine audio --audio take.wav`, alignment is automatic).
- Pauses: `<0.3>` inline; a blank line = 0.45 s paragraph pause. Use pauses before punches («Сколько стоит? <0.25> Нисколько.»).

## Output
`script.md` in `engine/public/projects/<id>/` (create with `scripts/new_project.py`). Show the user the final script text (without markup) before voicing if they asked to review it.
