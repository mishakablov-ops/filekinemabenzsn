# Статус v2 (29.10.2026, остановлено по лимиту)

> **Итог:** v2 доделана и одобрена 29.10.2026 — `output/baronessa-v2-5-nomusic.mp4`. Ниже — как было на момент остановки.

Готово:
- Сценарий `script-v2.md`; озвучка из файлов mike (narr_v2 + bar_v2) склеена `engine/voice_v2.py` → KINEMA проект `baronessa-v2` (voice.wav, words.json, 2:25).
- Сцены v2: `blender/sets/bar_v2.py` (Ставка+карта с растеканием оранжевого, армия instancing, танк «Биркин-34», залпы, осада, штурм, парашюты, рынок, учебник, парад, крупные планы).
- Таймлайн: `tools/build_timeline_v2.py` → `blender/shots_v2.json` (40 сцен, 145.6 с).
- Poly Haven CC0 текстуры + HDRI скачаны в `assets_ph/` (одобрено mike), подключены в `bar_props.pbr/hdri_world` (M() по префиксам, wood/marble/leather/cobbles).
- Пробные кадры v2 отрендерены без ошибок (`stills/v2/`), ДО подключения PBR/HDRI — их ещё не смотрел.

Дальше:
1. Перерендерить пробные кадры (`tools/test_stills.ps1 -Shots shots_v2.json -Out stills\v2 -Scale 0.35`), посмотреть лист, поправить.
2. Превью кадров mike; предупредить про рендер (~2,5 ч).
3. Рендер клипов: `render_clips.ps1` сейчас читает blender/shots.json → добавить параметр shots_v2.json и папку clips_v2.
4. storyboard для baronessa-v2 (агрессивная музыка trap-hype/dark-cinematic, звуки mbg-gunfire-far/explosion-far/march-boots/tank-engine), сборка, QA, `output/baronessa-v2.mp4`.
