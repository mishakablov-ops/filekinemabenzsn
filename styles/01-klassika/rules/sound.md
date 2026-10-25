# Sound library (53 SFX + 8 music beds)

Base library: noise-based sounds synthesized by `scripts/sfx_gen.py` (whooshes, swipes, impacts, risers, paper/cards, typing, ambiences). The tonal synthetic blips (clicks, pops, ticks, chimes, coins, beeps, glitches) sounded 8-bit and are **retired** (`scripts/sfx_library.py`, list `RETIRED`): files moved to `assets/sfx-retired/`, ids kept as aliases → silence or the imported pack's sound. Music: `scripts/music_gen.py`, loudness-normalised to −16 LUFS, AAC.

**Real sound pack** (the user's): `scripts/sfx_library.py import <folder|zip> [--dry] [--map "name=category"] [--category whoosh]` — category from file/folder names (EN/RU) or the audio itself, trim + fade, 48 kHz stereo, levelled to each category's mixer loudness, peak time measured for cut alignment; then every library id (retired or synthesized) in that category plays the pack sound with the closest length. `--keep-generated` replaces only retired ids. Undo: `sfx_library.py reset-pack`.

## How sound gets placed

- **User rule (2026-10-20): no airy noise.** The synthesized whooshes/swipes on transitions, wind, mask breathing and tape rips read as loud, unclear "air/blizzard". Prefer `"autoSfx": false` + hand-placed cues, mostly from the user's pack (`pk-*`), plus a few clear cinematic hits (nuke-boom, shockwave-hit, door-heavy-close, siren, short geiger, dread-rise). Spread repeats of the same pack sound (never two identical sounds back to back). Reference: `examples/nuclear-survival/spec.json`.
- **Automatic** (spec `autoSfx` default true): every scene transition plays its whoosh/hit with the sound's *peak* aligned to the cut; block entrances play their `sfx`; blocks with internal events (Counter ticks, Terminal typing, Cursor clicks, Checklist ticks, strikes, pings) play them on the exact frame.
- **Manual**: `"sfx": [{ "at": "@слово", "id": "hit-punch", "volume": 0.8 }]` (peak-aligned by default; `alignPeak: false` to start at the anchor).
- Override per layer: `"sfx": "pop-high"` or `"sfx": false`. Per transition: `"transition": { "type": "zoom", "sfx": "whoosh-deep" }`.
- De-clutter: same category within 90 ms is dropped; > 4 sounds per second are softened.
- Mix: voice 1.0 · music 0.12–0.16 ducked to ×0.45–0.5 under speech (attack 80 ms, release 350 ms) · SFX by category gain × `sfxVolume`. Final master −14 LUFS, −1 dBTP.

## Music beds

### User-approved music treatment — 2026-10-21

The user approved `output/quiet-evenings-40s-v5.mp4` as the finished music reference. Follow the standing preferences in [styles.md](styles.md): match the story's emotion, let achievements lift the music gently, keep narration clear (including quieter final phrases), and finish with a smooth fade.

For that reel, the supplied `ssstik.io_1792530637838.mp3` was extended from 37.27675 s to 40 s with a matched phrase and a 0.30 s crossfade, preserving pitch and tempo. The source and arrangement are saved in `engine/public/projects/quiet-evenings/` as `success-user-original.mp3`, `success-user-40s.wav` and `music-arrangement.json`.

Reference mix: prepared bed −16 LUFS; music volume `0.22`, speech duck multiplier `0.40`, attack 80 ms, release 350 ms, fade-in 0.18 s and fade-out 1.25 s. The final approved MP4 measured −14.66 LUFS / −1.39 dBTP, with narration 9.5–18.5 dB above the music by section RMS. These values describe this accepted mix, not a universal preset: adjust to the actual voice and track. Preserve approved visuals and source narration when only replacing music.

### Included beds

| id | bpm | dur | use |
|---|---|---|---|
| `pulse-tech` | 110 | 72.82s | 110 bpm, minor, plucky arps + pumping pads. Default for tech explainers. |
| `lofi-warm` | 84 | 71.57s | 84 bpm swing, e-piano jazz chords, vinyl. Calm, friendly, cozy products. |
| `ambient-air` | 70 | 71.57s | no drums, floating pads + bells. Under voice on light/sky themes. |
| `drive-promo` | 124 | 72.68s | 124 bpm four-on-floor, builds to a drop at bar 17. Energetic promo. |
| `dark-cinematic` | 90 | 67.0s | 90 bpm pulse, minor drone, booms. Problem statements, security, mystery. |
| `bright-pop` | 118 | 68.08s | 118 bpm major, happy plucks + claps. Consumer apps, playful. |
| `minimal-keys` | 96 | 63.0s | 96 bpm e-piano arps, rim clicks. Thoughtful, product walkthroughs. |
| `trap-hype` | 140 | 57.86s | 140 bpm half-time 808 + hat rolls. Aggressive typography promos. |

Each bed has `music/<id>.beats.json` (beats, bars, sections, drops). Your own track: `scripts/beats.py track.mp3`.

## SFX by category

53 playable sounds (8 from the imported pack). Synthetic tonal blips (clicks, pops, ticks, chimes, coins, beeps, glitches) are retired: their ids still work in specs and blocks but play the pack's sound of the same category, or nothing until a pack is imported (`scripts/sfx_library.py import <folder|zip>`). `sfx_library.py status` shows the current mapping.

### whoosh (0)
- also accepted: `whoosh-short` (silent), `whoosh-medium` (silent), `whoosh-long` (silent), `whoosh-up` (silent), `whoosh-down` (silent), `whoosh-airy` (silent), `whoosh-deep` (silent), `whoosh-pan-lr` (silent), `whoosh-pan-rl` (silent), `whoosh-double` (silent), `whoosh-reverse` (silent), `whoosh-cloud` (silent), `whoosh-short-low` (silent), `whoosh-short-high` (silent)

### swipe (0)
- also accepted: `swipe-fast` (silent), `swipe-soft` (silent), `swipe-up` (silent), `swipe-down` (silent), `swipe-paper` (silent), `swipe-tiny` (silent), `swipe-fast-low` (silent), `swipe-fast-high` (silent)

### click (1)
- `pk-click-ui-button` — pack: ui button.MP3 (0.718s, peak 0.019s)
- also accepted: `click-crisp`→`pk-click-ui-button`, `click-soft`→`pk-click-ui-button`, `click-mouse`→`pk-click-ui-button`, `click-trackpad`→`pk-click-ui-button`, `click-button`→`pk-click-ui-button`, `click-glass`→`pk-click-ui-button`, `click-wood`→`pk-click-ui-button`, `click-tiny`→`pk-click-ui-button`, `click-double`→`pk-click-ui-button`, `click-select` (silent), `click-crisp-low`→`pk-click-ui-button`, `click-crisp-high`→`pk-click-ui-button`

### pop (1)
- `pk-pop-ui-menu` — pack: UI Menu.MP3 (0.413s, peak 0.123s)
- also accepted: `pop-soft`→`pk-pop-ui-menu`, `pop-high`→`pk-pop-ui-menu`, `pop-low`→`pk-pop-ui-menu`, `pop-bubble`→`pk-pop-ui-menu`, `pop-bubble-high`→`pk-pop-ui-menu`, `pop-cork`→`pk-pop-ui-menu`, `pop-triple`→`pk-pop-ui-menu`, `pop-plop`→`pk-pop-ui-menu`, `pop-soft-low`→`pk-pop-ui-menu`, `pop-soft-high`→`pk-pop-ui-menu`

### tick (0)
- also accepted: `tick-digital` (silent), `tick-soft` (silent), `tick-wood` (silent), `tick-clock` (silent), `tick-meter` (silent), `tick-roll` (silent), `tick-digital-low` (silent), `tick-digital-high` (silent)

### type (5)
- `typing-short` — short typing burst (~0.5s) (0.629s, peak 0.0s)
- `typing-medium` — typing a phrase (~1.2s) (1.343s, peak 0.0s)
- `typing-long` — typing a sentence (~2.5s) (2.6s, peak 0.0s)
- `typing-fast` — fast confident typing (~1.3s) (1.45s, peak 0.0s)
- `typing-terminal` — type a command then hit enter (1.39s, peak 0.0s)
- also accepted: `key-single` (silent), `key-space` (silent), `key-enter` (silent)

### notify (2)
- `pk-notify-notification-sfx-1` — pack: notification sfx(1).MP3 (1.472s, peak 0.179s)
- `pk-notify-system-alert-sfx` — pack: system alert sfx.MP3 (1.775s, peak 0.153s)
- also accepted: `ding-soft`→`pk-notify-system-alert-sfx`, `ding-bright`→`pk-notify-system-alert-sfx`, `chime-two-up`→`pk-notify-notification-sfx-1`, `chime-two-down`→`pk-notify-system-alert-sfx`, `chime-triad`→`pk-notify-notification-sfx-1`, `chime-glass`→`pk-notify-system-alert-sfx`, `chime-message`→`pk-notify-system-alert-sfx`, `chime-calm`→`pk-notify-system-alert-sfx`, `ping`→`pk-notify-system-alert-sfx`, `ping-sonar`→`pk-notify-system-alert-sfx`, `ding-soft-low`→`pk-notify-system-alert-sfx`, `ding-soft-high`→`pk-notify-notification-sfx-1`

### result (1)
- `pk-result-failure` — pack: failure.MP3 (1.199s, peak 0.239s)
- also accepted: `success-pluck` (silent), `success-chime` (silent), `success-check` (silent), `success-soft` (silent), `success-level` (silent), `success-coin` (silent), `error-buzz`→`pk-result-failure`, `error-down`→`pk-result-failure`, `error-thud`→`pk-result-failure`, `deny-tap`→`pk-result-failure`

### impact (8)
- `hit-soft` — soft hit under a title (2.59s, peak 0.0s)
- `hit-punch` — punchy hit, number lands (2.49s, peak 0.0s)
- `hit-cinematic` — big cinematic boom, reveal (4.49s, peak 0.0s)
- `thud` — short thud, object drops (0.35s, peak 0.0s)
- `hit-sub` — pure sub drop, felt not heard (1.6s, peak 0.0s)
- `heartbeat` — two heartbeat thumps, tension (0.74s, peak 0.0s)
- `nuke-boom` — distant detonation: crack, then a huge rolling rumble (7 s) (10.53s, peak 0.602s)
- `shockwave-hit` — shockwave arriving: roaring wind rush, slam, flying debris (3.5 s) (5.27s, peak 0.719s)
- also accepted: `hit-metal`→`hit-punch`, `hit-glitch`→`hit-punch`

### riser (7)
- `riser-short` — 1s build into a reveal (1.0s, peak 1.0s)
- `riser-medium` — 2s build (2.0s, peak 2.0s)
- `riser-long` — 4s tension build for promos (4.0s, peak 4.0s)
- `riser-tonal` — pitch-rising synth build (2.0s, peak 2.0s)
- `downlifter` — falling sweep after a drop (1.6s, peak 0.0s)
- `downlifter-short` — short release after a hit (0.8s, peak 0.0s)
- `dread-rise` — dark tension swell: low cluster rising into silence (4 s) (6.21s, peak 3.782s)
- also accepted: `riser-noise` (silent), `suck-in` (silent)

### digital (2)
- `pk-digital-data-load-sfx-1` — pack: data load sfx(1).MP3 (0.843s, peak 0.422s)
- `pk-digital-digitasl-burst-sfx` — pack: digitasl burst sfx.MP3 (0.903s, peak 0.162s)
- also accepted: `glitch-short`→`pk-digital-digitasl-burst-sfx`, `glitch-medium`→`pk-digital-digitasl-burst-sfx`, `glitch-long`→`pk-digital-data-load-sfx-1`, `data-blips`→`pk-digital-data-load-sfx-1`, `scan-beep`→`pk-digital-data-load-sfx-1`, `hum-on`→`pk-digital-digitasl-burst-sfx`, `power-off`→`pk-digital-digitasl-burst-sfx`, `modem-chirp`→`pk-digital-digitasl-burst-sfx`

### shimmer (2)
- `reveal-glow` — airy glow reveal (2.69s, peak 0.0s)
- `pk-shimmer-ui-dissolvre-sfx` — pack: UI dissolvre sfx.MP3 (0.789s, peak 0.092s)
- also accepted: `sparkle` (silent), `sparkle-rise`→`pk-shimmer-ui-dissolvre-sfx`, `shimmer-pad`→`pk-shimmer-ui-dissolvre-sfx`, `star` (silent), `magic-wand`→`pk-shimmer-ui-dissolvre-sfx`

### foley (7)
- `geiger-low` — Geiger counter, background level: sparse clicks (3 s) (3.0s, peak 2.615s)
- `geiger-high` — Geiger counter near a hot spot: dense crackle (3 s) (3.0s, peak 0.066s)
- `geiger-rise` — Geiger counter approaching contamination: clicks speed up (4 s) (4.0s, peak 3.804s)
- `crank-wind` — winding a hand-crank radio/flashlight: ratchet clicks (1.6 s) (1.6s, peak 1.247s)
- `door-heavy-close` — heavy steel door slams shut, bolt engages, concrete room (2.5 s) (3.94s, peak 0.024s)
- `door-creak` — slow heavy door creak (2 s) (3.11s, peak 0.669s)
- `switch-click` — flashlight / lantern switch click (0.25 s) (0.26s, peak 0.011s)
- also accepted: `radio-static` (silent), `radio-voice` (silent), `radio-tune` (silent), `steps-concrete` (silent), `steps-debris` (silent), `tape-rip` (silent), `breath-mask` (silent), `can-open` (silent), `water-pour` (silent)

### alarm (2)
- `siren-air-raid` — air-raid siren, rising and falling, city-wide (6 s) (10.59s, peak 0.546s)
- `siren-far` — distant siren over the city, faint (8 s) (11.09s, peak 6.083s)

### ui (6)
- `card-slide` — card slides onto table (0.25s, peak 0.0s)
- `card-flip` — card flips over (0.18s, peak 0.0s)
- `paper-rustle` — paper rustle, document appears (0.5s, peak 0.0s)
- `stamp` — rubber stamp, verdict (0.3s, peak 0.0s)
- `strike` — marker strikethrough scratch (0.28s, peak 0.0s)
- `marker` — highlighter marker swipe (0.35s, peak 0.0s)
- also accepted: `shutter` (silent), `toggle-on` (silent), `toggle-off` (silent), `scroll` (silent), `lock` (silent), `unlock` (silent), `cash` (silent), `zoom-in` (silent), `zoom-out` (silent), `drop-in` (silent), `hover` (silent), `cursor-move` (silent)

### sting (2)
- `tone-bass-drop` — bass drop tone (1.0s, peak 0.0s)
- `tone-rise-short` — short tonal rise into cut (0.5s, peak 0.5s)
- also accepted: `sting-logo` (silent), `sting-soft` (silent), `sting-dark` (silent), `sting-bright` (silent)

### ambience (6)
- `room-tone` — quiet room tone loop, glue under voice (7.0s, peak 0.0s)
- `space-drone` — deep space drone loop, night / planet scenes (10.0s, peak 0.0s)
- `city-hum` — low city hum bed, map / city flyovers (7.0s, peak 0.0s)
- `terminal-hum` — faint computer fan hum (7.0s, peak 0.0s)
- `rumble-distant` — distant rolling rumble, aftershock thunder (6 s) (8.76s, peak 3.426s)
- `bunker-tone` — shelter room tone: low hum, faint vent air, distant creaks (8 s) (8.0s, peak 3.31s)
- also accepted: `air-high` (silent), `wind` (silent), `wind-ash` (silent)

### transition (1)
- `trans-riser-hit` — build then hit, big reveal (4.39s, peak 1.2s)
- also accepted: `trans-whoosh-hit` (silent), `trans-swish-pop` (silent), `trans-glitch-cut`→`trans-whoosh-hit`, `trans-air-sparkle`→`whoosh-airy`, `trans-zoom-through` (silent)

## Голос и звук «Мира без границ» — одобрено пользователем 22.10.2026

- **Голос:** пользователь сначала попросил resemble-ai/chatterbox, но русский у Chatterbox звучит с акцентом. Это касается и стандартного голоса, и клонирования тембра; см. `voice/takes` проекта. После прослушки 8 вариантов пользователь выбрал **Gemini 3.1 Flash TTS «Algenib»**. Промпт: native Russian documentary narrator, warm, pleasant, confident, brisk natural pace, very short pauses, no foreign accent + настроение секции (`blender-kit/tools/py/tts_final.py`). Он говорит неторопливо, около 2 слов/с, поэтому 137 слов ≈ 65 с. Темп не растягивать. Перед сменой голоса снова делать прослушку (`voice_audition2.py`).
- **Звуки:** 19 своих звуков синтезированы под сцены (`blender-kit/tools/py/sfx_mbg.py` → `audio/sfx/`): мотор шлагбаума, хлопок закрытого паспорта, бумага, шаги толпы и гул, плотная толпа, клаксоны, скрип качелей, марш сапог (шаг каждые 0,5 с), двигатель танка, монеты, удар молотка, крошка асфальта, нефтекачалка, далёкая стрельба, далёкий взрыв, огонь, гул ламп, растворение границ, «рисование» линий. Плюс из библиотеки: space-drone, city-hum, hit-sub/soft, thud, riser-medium, marker, rumble-distant, door-creak, reveal-glow и pk-* в концовке.
- **Сведение:** `blender-kit/tools/mix.py` заранее собирает `soundtrack.wav` (музыка + звуки) и сам приглушает музыку под голос: duck ×0.4, атака 80 мс, отпускание 350 мс. В spec: `music.src = soundtrack.wav`, `volume 1`, `duck 1`, `autoSfx false`. Музыка: `ambient-air` (начало) → кроссфейд в `dark-cinematic` (армии и бой) → обратно `ambient-air` с 24-й секунды трека (финал и концовка). Итог: −14.0 LUFS, TP −1.6, голос на 7–8 дБ громче звуковой подложки.
