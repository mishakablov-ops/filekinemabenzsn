# spec.json reference

```jsonc
{
  "id": "my-reel",
  "mode": "explainer",            // or "promo"
  "style": "dusk",                // see styles.md
  "fps": 60,                      // previews override with --props '{"fps":30}'
  "voice": { "src": "projects/my-reel/voice.wav", "words": "projects/my-reel/words.json", "volume": 1 },
  "words": "projects/my-reel/words.json",       // promo (no voice): cards from tts.py --engine silent
  "music": { "src": "music/pulse-tech.m4a", "volume": 0.13, "duck": 0.5, "beats": "music/pulse-tech.beats.json", "offset": 0, "fadeIn": 0.4, "fadeOut": 1.8 },
  "duration": 20,                 // only when there is no voice (otherwise voice length + tail)
  "tail": 1.2,                    // seconds after the last word
  "captions": { "mode": "editorial", "pos": "top", "tone": "light", "scale": 1, "uppercase": false, "scrim": true },
  "autoSfx": true, "sfxVolume": 1,
  "sfx": [ { "at": "@ноль", "id": "hit-punch", "volume": 0.8 } ],
  "grain": 0.045, "vignette": 0.22,           // default from style
  "scenes": [ SCENE, … ]
}
```

## SCENE
```jsonc
{
  "id": "proof",                    // free label (shows in errors)
  "at": "@слово",                   // first scene: 0. Cut lands 70 ms before the word (picture leads voice)
  "until": "@другое",               // optional; default = next scene start
  "style": "blaze",                 // optional per-scene style
  "bg": "WarmGlow" | { "block": "Room3D", "props": { … }, "dim": 0.5, "dimAt": "@слово" },   // default = style background; dim darkens it so a hero layer (3D phone) pops
  "camera": "push" | { "move": "punch", "amount": 1, "shakeAt": ["@бум"], "focusFrom": 12 },
  "transition": "blur" | { "type": "zoom", "dur": 0.5, "sfx": "whoosh-deep" | false },
  "captions": { "mode": "slam", "pos": "middle", "tone": "light", "scrim": 0.6 } | false,
  "layers": [ LAYER, … ]
}
```
Camera moves: `still push pull pushFast drift panUp panDown panLeft panRight tilt orbit punch`.
Transitions: `cut hardcut fade blur zoom zoomOut push pushDown pushLeft pushRight whip stack iris wipe flash dip cloud glitch slam`.

## LAYER
```jsonc
{
  "block": "Counter",               // see blocks.md
  "props": { … },                   // block props; any key ending in "At" (and at/showAt/strikeAt arrays) accepts anchors
  "at": "@слово",                   // default: scene start
  "until": "@слово-0.15",           // default: scene end
  "pos": "stage" | { "preset": "stage", "x": 60, "y": 940, "w": 960, "h": 520, "dx": 0, "dy": 0, "scale": 1, "rotate": 0 },
  "enter": "rise",                  // none fade rise riseBig drop pop slam zoom blur slideL slideR slideUp slideDown flip flipY swing unfold glitch iris wipe stretch
  "exit": "blur",                   // only when `until` ends it before the scene ends: sink lift zoomOut shrink cut + any enter kind
  "z": 1,
  "sfx": "pop-high" | false,
  "overlap": true                   // intentional overlap: QA will not flag it
}
```
Position presets: `full stage stageHigh stageLow center top upper lower bottom left right topLeft topRight bottomLeft bottomRight`. `stage` follows the caption band automatically.

Timing props inside a background's nested screen (MacBook/IPhone17/Room3D `screen.props`: Terminal `lines[].at`, `pressAt`, NotificationStack `items[].at`…) resolve exactly like layer props: `@слово` anchors or seconds after the scene start.

## Anchors
`@слово`, `@фраза из слов`, `@слово>` (end), `@слово+0.2`, `@слово#2`, `card:4`, `beat:16`, `bar:8`, `drop:0`, `section:<name>`, `end`, plain seconds (absolute for scenes, scene-relative for layers and block props).
Words are matched case-insensitively, ё = е, punctuation ignored; a phrase can span "10 000" style tokens.

## Rendering
- stills + QA: `cd engine && node tools/stills.mjs --comp Reel --props '{"project":"<id>","fps":30}' --every 1 --scale 0.4 --qa --out out/<id>_st --sheet out/<id>_sheet.png`
- final: `$PY $RS/scripts/render.py <id>` (preview: `--preview`)
- live editing UI: `cd engine && npx remotion studio src/index.ts` (composition `Reel`, props `{"project":"<id>"}`), galleries `Gallery-<style>` show every block.
