# Captions

Captions are generated from `words.json` (from `tts.py`) — one **card** per script line, revealed word-by-word exactly when each word is spoken (blur → sharp, 0.3 s, starting 0.1 s before the word).

## Card anatomy (editorial mode)
```
           Теперь можно собрать          <- lead: small, muted (46 px)
          своё ==такое же==              <- punch: big, bold (fitted 64–112 px), one accent
```
Script line: `Теперь можно собрать // своё ==такое же==`. Without `//` the whole line is punch.

## Markup (script.md and Title/Bubble/Highlight props)
| markup | look |
|---|---|
| `*слово*` | serif italic (Playfair) — the editorial accent, also for quotes «…» |
| `[слово]` | accent colour |
| `==слово==` | highlighter box sweeping in (accent bg, dark text) |
| `~~слово~~` | red line strikes through right after the word is spoken |
| `^слово^` | second accent colour |
| `__слово__` | outlined letters |
| `!!слово!!` / `++слово++` | negative red / positive green |
| `/` | forced line break inside the punch |
| `{88\|восемьдесят восемь}` | caption shows `88`, voice says the words |
| `<0.4>` | pause after the previous word (seconds) |
| blank line | paragraph pause 0.45 s |

Rule: **one accent per card.** Accent the word that carries the meaning (a number, the object, the emotion), never a function word.

## Modes (per video in `spec.captions.mode`, per scene in `scene.captions.mode`, per line with `%mode`)
| mode | when | look |
|---|---|---|
| `editorial` | default explainers | lead + punch, top band, centered |
| `subtitle` | screen recordings / footage on top (style `night`, `terminal`) | 2–5 words, one line, lower band |
| `slam` | punches, promos (`blaze`, `brutal`) | 1–2 words per line, each line fitted to the frame width (up to 300 px), slams in with overshoot + blur, camera punch on every chunk |
| `stack` | lists, manifestos (`neon`) | lines accumulate, mixed solid / outline / serif treatments |
| `karaoke` | quotes, lyrics | whole sentence dim, current word lit |
| `vhs` | horror / analog tape stories (PS1 + VHS look, see `references/horror-kit.md`) | pixel font (Press Start 2P), letters typed at 12 fps, square blue plates that grow frame by frame (no rounded corners), yellow accent words, hard cut out. `{"mode": "vhs", "pos": "top", "uppercase": true}` |
| `none` | silent montage | — |

Line directives: `%slam`, `%stack`, `%sub`, `%karaoke`, `%edit` and positions `%top %upper %middle %lower %bottom`, e.g. `%slam %middle ==Нисколько.==`. A position directive also moves the scene's stage away from the caption.
Slam cards hold until the next card (hard cut) and are sized so their lines never exceed the caption band. Serif-italic slam lines stay lowercase for contrast with the caps.

## Position
Style default (dusk/ember/sand/cinema: `top`; night/terminal: `lower`; blaze/brutal/neon: `middle`). Per scene: `"captions": { "pos": "lower" }`. Hide for a scene: `"captions": false`.
Tone follows the scene style; force with `"tone": "light" | "dark"`. Busy backgrounds (3D, photo, video, shader) get an automatic scrim; `"scrim": 0.6` or `false` to tune.

## Length limits (lint + QA enforce)
- punch ≤ 34 characters (slam ≤ 16), lead ≤ 46
- hook card ≤ 7 words
- a card must be on screen ≥ 0.35 s; cards hold until the next card (max 2.2 s after the last word)
- short function words (в, и, на, не, что…) are glued to the next word — no orphans at line ends

## Voice direction cues (not captions)
`((cue))` anywhere in a script line — e.g. `((excited)) Хотите своё приложение?` or `Сколько стоит? ((long pause)) // !!Нисколько!!` — is removed from captions and from the spoken words and becomes an inline `[cue]` tag for Fish Audio / ElevenLabs v3 / Inworld (see `scripts/voice_direct.py`). A cue at the end of a line follows the last word.
