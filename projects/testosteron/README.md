# Каждые 10 секунд у тебя больше тестостерона (`testosteron`)

- **Стиль:** пиксель PIXCINE (движок в `Wpresser/Algorithm-for-aipollon`, `pixcine/`), герой `geroy` и его стадии
- **Длительность:** ~1:30 + CTA · **Голос:** как в «Эскалаторе» — MiniMax speech-2.8-hd `Russian_ReliableMan`, ×1.35
- **Задача mike (09.11.2026):** пиксельный ролик по тренду TikTok «каждые 10 секунд…» (@zovlanderr), больше тестостерона,
  отсылка на Арсена Маркаряна, мемы, «наш стиль», озвучка как в прошлом ролике.
- **Маркарян:** только пародия — пиксельный бородатый «наставник» (`arsen`, подпись «ПАРОДИЯ») и сообщение в чате; без фото и голоса.
- **Статус:** голос записан на ПК 09.11 (91,3 с, Whisper-тайминги в `voice/`), выдан v1 09.11 (`testosteron-v1.mp4`, 1:32, 30 fps, 14 Мбит/с, −14 LUFS); ждёт отзыва mike.

## Как собрать
1. `pixcine/projects/shorts/narration/testosteron/script.md` = `script.md` отсюда.
2. Голос: `python voice_grid.py testosteron` (ключ Replicate из `skills/reel-studio/.secrets.env`; без ключа
   `--placeholder` даёт тишину с расчётными таймингами). Каждая секция встаёт ровно на 0:10, 0:20, …
3. `python build_testo.py` → `engine/public/projects/shorts/testo.json`; стоп-кадры `node tools/stills.mjs --project shorts --ep testo --shots --qa`.
4. `python scripts/mix.py shorts testo`, `node tools/render.mjs --project shorts --ep testo --concurrency 4`.

Файлы движка (overlay `meter`, шапка `beanie`, голуби `pigeons`, предметы `jar`/`razor`, каст, локации `tt_*`, музыка
`t_trap.flac` = `trap-hype.m4a` из KINEMA) — коммит `6b4459e` в ветке `claude/testosteron-pixel` движка.
Доработки после голоса — локальный коммит `5269a4a` той же ветки (не запушен). Копии `build_testo.py`, `voice_grid.py`
и патч движка `pixcine-engine.patch` (git apply в корне движка; потом `python cast_src.py` и `pixchar.py`) лежат в `engine/`.
`voice/words.json` и `voice/sections.json` — тайминги слов и секций настоящего голоса (сам голос в git не кладём).

Рендер в облаке: `PIX_CHROME=<chrome-headless-shell> PIX_GL=swangle node tools/render.mjs …` (те же переменные понимает `stills.mjs`).

## Звук (09.11)
- `t_trap`: тихое интро 0–13 с, дроп на 13,0 с. Бит идёт с первого кадра (offset 13), склейки музыки спрятаны под удары
  уровней (0:20, 0:40, 1:00); в блоке 5 музыка проседает в интро и взрывается дропом ровно на слове «фонк».
- Пауза 5,6–10 с после хука: частое тиканье, отсчёт 3-2-1 «до первой дозы» на груди героя (не на лице), riser в первый уровень.
- Удары уровней −7 дБ и обрезаны до 3 с (хвосты по 6–7 с забивали голос). Титр уходит через 0,8 с после последнего слова.
- Музыка под голосом на 6–10 дБ ниже голоса, в паузах −19…−23 дБ RMS, мастер −14 LUFS.

## Журнал версий
- 09.11 — сценарий v1, 28 планов, пробные кадры на черновых таймингах (`project-files/testosteron/probnye-kadry-v1.jpg`).
- 09.11 вечер — голос «Эскалатора» на ПК, планы пересобраны под него, звук без провалов, рендер v1 в облаке (64 мин), выдан: ПК `aipollon claude\testosteron\testosteron-v1.mp4` (md5 сошёлся) и project-files/testosteron/.
