# Storyboard: from script beats to scenes

The script is a list of caption cards with word timings. A **scene** covers 1–3 cards (1.2–4 s). Each scene = background + 0–3 layers + camera + incoming transition. Everything is anchored to spoken words, so picture and voice stay locked whatever the TTS pace.

## 1. Beat → visual (pick the strongest that is TRUE for the topic)

| beat in the script | best visuals (blocks) | notes |
|---|---|---|
| Hook / pain («Бесит…?», «Монтаж занимает вечер?») | Room3D with a person (evening), NotificationStack of complaints, PhotoBG of the real thing, Street3D | first frame must already move; no logo intro |
| «Now there is X» / reveal | Laptop3D `open:true` + `cam:zoomScreen` into a Terminal/ClaudeChat, Phone3D `enterSpin` | the device's screen is live HTML — show the actual action |
| What it does / steps | Terminal lines, ClaudeChat typing, AppScreen inside Phone, Steps, CodeEditor | 1 action per card, anchors on the verbs |
| Number / proof | Counter (steps 136→1.2k), StatSlam, KPIs, GithubRepo star roll + ring, BarChart, Donut, LineChart | say the number in voice AND show it big |
| Comparison / before-after | CompareSplit, PricingCards, ScoreCard, StrikeList | strike exactly on the spoken word |
| Scale / "everywhere" | Globe3D arcs+markers, City3D dive, Street3D drone, Terrain3D reveal | 3D wow moments: 1 per 10–15 s |
| People / everyday use | Room3D presets (office/living/cafe/bedroom/studio), Scene3D (people wave/think/cheer/type), Street3D walkers | dark pastel, nobody overlaps anything (QA checks 3D collisions) |
| Twist / punch / price «Нисколько» | `style: "blaze"` scene, slam caption, `camera: "punch"`, `transition: "slam"`, Marquee band, BigType, Extruded | max 1–2 aggressive moments per explainer; promos can be all-aggressive |
| Install / how to get it | Terminal `prompt` + `ok`, Steps, Toast «Готово» | |
| CTA | Phone with SocialProfile + Cursor tapping the link (`pressAt`), or EmailCard/Toast | the last card stays ≥ 1.2 s |

## 2. Rhythm rules
- Scene length 1.2–4 s; a new visual event at least every ~1.5 s inside a scene (layer entrance, counter, typing, cursor, camera move).
- Alternate scene families: UI-card scene → 3D scene → typographic scene → UI… Never the same block in two consecutive scenes.
- Fast montage bursts are allowed for lists («комнаты, улицы, люди»): 0.5–0.8 s per scene with `whip`/`cut`.
- Transitions: default from style (dusk/ember: `blur`). Use `zoom` into/out of devices, `push` for "next step", `whip` for bursts, `slam`/`cut` for punches, `cloud` for dreamy/sky stories, `stack` for card-like progressions. Max ~0.6 s.
- Camera: `push` (default calm), `drift` (photo/3D), `punch` (aggressive: bumps on caption hits), `tilt` (UI cards), `still` for 3D blocks that move their own camera.

## 3. Layout grid (1080×1920) — why nothing overlaps
- Caption bands: `top` y 250–630 (default), `middle` 760–1160, `lower` 1180–1470.
- `pos: "stage"` automatically becomes the free area for the scene's caption band (with 40–50 px of air): top→ y 680–1500; lower→ 180–1140; middle→ 1150–1530. A `%top`/`%lower` directive on the scene's first script line moves the stage too.
- Platform safe zones: keep text out of y < 200 and y > 1500 and the right 140 px below y 900.
- Two blocks in one scene: split the stage vertically (`{"preset":"stage","h":280}` + `{"x":60,"y":940,"w":960,"h":520}`) or horizontally (`left` x 60–580 / `right` x 500–1020 → reduce widths so ink boxes don't touch).
- Overlays that SHOULD sit on top (Cursor, Callout) are flagged ⚑ in blocks.md; anything else intentional needs `"overlap": true`.
- Full-frame 3D/photo backgrounds get an automatic dark scrim behind the caption band (`captions.scrim` to tune / disable).
- When a layer must leave before the next one arrives in the same spot: `"until": "@слово-0.15", "exit": "blur"`.

## 4. Anchors cheat-sheet
`"at": "@слово"` start of the next occurrence (search starts at the scene start) · `"@фраза из слов"` · `"@слово>"` end of the word · `"@слово+0.3"` / `"-0.1"` offsets · `"@слово#2"` second occurrence · numbers = seconds (relative to the scene for layers) · `"card:4"` · promo: `"beat:16"`, `"bar:8"`, `"drop:0"`, `"section:drop"`.
Block props ending in `At` (strikeAt, checkAt, pressAt, selectAt, ringAt, starsAt …) take the same anchors.

## 5. A complete scene (copy-paste)
```json
{ "id": "proof", "at": "@звёзд", "transition": "push", "camera": "push",
  "layers": [
    { "block": "GithubRepo", "props": { "owner": "you", "repo": "replica-skill", "stars": [136, 1200], "starsAt": "@тысячи", "ring": "stars", "ringAt": "@тысячи+0.6" } }
  ] }
```
Background defaults to the style's (`dusk`: flat warm charcoal). Override with `"bg": "WarmGlow"` or `{ "block": "Room3D", "props": {…} }`.

## 6. Good arcs (adapt, don't copy)
**Tool explainer (45 s):** pain hook (3D room / complaints) → reveal on a device (zoom into screen) → 3–4 "how it works" beats with UI + numbers → scale moment in 3D → limitation/honesty beat → price punch (blaze) → install line in terminal → CTA phone.
**News / discovery (35 s):** striking fact with number (StatSlam) → where/who (Globe3D marker / Street3D) → why it matters (CompareSplit) → what to do (Steps) → CTA.
**Promo (20 s, music):** 3 slam words on the first bars → product on device on the first drop → 3 feature cards on beats → price/offer slam → logo/CTA on the last bar.
