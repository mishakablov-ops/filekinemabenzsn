# Каждые 10 секунд у тебя больше тестостерона (`testosteron`)

- **Стиль:** пиксель PIXCINE (движок в `Wpresser/Algorithm-for-aipollon`, `pixcine/`), герой `geroy` и его стадии
- **Длительность:** ~1:30 + CTA · **Голос:** как в «Эскалаторе» — MiniMax speech-2.8-hd `Russian_ReliableMan`, ×1.35
- **Задача mike (09.11.2026):** пиксельный ролик по тренду TikTok «каждые 10 секунд…» (@zovlanderr), больше тестостерона,
  отсылка на Арсена Маркаряна, мемы, «наш стиль», озвучка как в прошлом ролике.
- **Маркарян:** только пародия — пиксельный бородатый «наставник» (`arsen`, подпись «ПАРОДИЯ») и сообщение в чате; без фото и голоса.
- **Статус:** сценарий и раскадровка готовы, пробные кадры на черновых таймингах; ждёт озвучку на ПК.

## Как собрать
1. `pixcine/projects/shorts/narration/testosteron/script.md` = `script.md` отсюда.
2. Голос: `python voice_grid.py testosteron` (ключ Replicate из `skills/reel-studio/.secrets.env`; без ключа
   `--placeholder` даёт тишину с расчётными таймингами). Каждая секция встаёт ровно на 0:10, 0:20, …
3. `python build_testo.py` → `engine/public/projects/shorts/testo.json`; стоп-кадры `node tools/stills.mjs --project shorts --ep testo --shots --qa`.
4. `python scripts/mix.py shorts testo`, `node tools/render.mjs --project shorts --ep testo --concurrency 4`.

Файлы движка (overlay `meter`, шапка `beanie`, голуби `pigeons`, предметы `jar`/`razor`, каст, локации `tt_*`, музыка
`t_trap.flac` = `trap-hype.m4a` из KINEMA) — коммит `6b4459e` в ветке `claude/testosteron-pixel` движка.
Копии `build_testo.py`, `voice_grid.py` и патч движка `pixcine-engine.patch` (git apply в корне движка; потом `python cast_src.py` и `pixchar.py`) лежат в `engine/`.

## Журнал версий
- 09.11 — сценарий v1, 28 планов, пробные кадры на черновых таймингах (`project-files/testosteron/probnye-kadry-v1.jpg`).
