# Как жить, если ты тупой (`kak-zhit-tupoy`)

- **Стиль:** пиксель PIXCINE 9:16 (движок `Wpresser/Algorithm-for-aipollon`, `pixcine/`), формат одобренного «Тестостерона» v2
- **Длительность:** 76 с · **Голос:** MiniMax speech-2.8-hd «Russian_ReliableMan» ×1.35 (озвучка на ПК, `voice_grid.py tupoy --grid 0.1`)
- **Задача mike (11.11.2026):** «как жить если ты тупой, сделай резче», юмор, не познавательный («нам конкуренты не нужны»),
  места: дом, магазин, школа, улица. К v1 сценария: «тик ток не основная тема», «сделай смешное епта, можешь маты». На v2: «делай грязь».
- **Статус:** сценарий v2 принят, озвучка готова, рендер в облаке.

## Сборка
- Сценарий голоса `script.md` → `pixcine/projects/shorts/narration/tupoy/script.md`; тайминги `voice/words.json`, `voice/sections.json`
  (сам голос в git не кладём; на ПК `D:\aipollon\KINEMA\pixcine\projects\shorts\narration\tupoy\`).
- Каст и движок: `engine/pixcine-engine.patch` (новые куклы vitek_w, uchitel, uchitel_s, ohrannik, odnokl; оверлей `feed` — лента
  коротких видео на пиксельном телефоне; voice_grid: буфер дорожки при малой сетке). Затем `python cast_src.py` и `pixchar.py`.
- Раскадровка `engine/build_tupoy.py` (36 планов: зимняя улица со столбом, ванная, кухня, класс, вход в магазин «ОТ СЕБЯ»).
  `python build_tupoy.py`, `scripts/mix.py shorts tupoy`, `tools/render.mjs --project shorts --ep tupoy`.
- Урок: куклы крупные, крупный план = камера ≥3,4 м от лица и угол ≥42° (в `ks()` это `MIN_D`), иначе лицо во весь кадр.
  Мат: в голосе и титрах без звёздочек (mike: «делай грязь»).

## Журнал версий
- script-v1 11.11 — отправлен mike.
- script-v2 11.11 — mike: «тик ток не основная тема», «сделай смешное», «можешь маты». Герой Витёк, сквозной хук со столбом.
- 11.11 — «делай грязь»: озвучка на ПК, 36 планов, рендер.
