---
name: blender
description: Сделать вертикальный ролик aipollon в стиле «Блендер» — все 3D-сцены строятся кодом и рендерятся в Blender 4.5 (Eevee) на ПК пользователя, KINEMA собирает поверх титры, звук и концовку. Как «Мир без границ».
---

# /blender — ролик в стиле «Блендер»

Одобренный образец: `mir-bez-granic-v2.mp4` («Мир без границ», 67 с, 22.10.2026); текущая версия пайплайна —
проект `projects/fr-klassika/` (Париж, люди `people2.py`, исправления 22–23.10.2026).
Как должно выглядеть: **`styles/blender/README.md`** и `styles/01-klassika/README.md`.
Пайплайн, грабли и все правки пользователя: **`knowledge/rules/blender-pipeline.md`** — прочитать целиком.
Общие правила: `knowledge/aipollon-knowledge.md`, `knowledge/rules/styles.md`, `sound.md`, `qa-checklist.md`.

## Режим рендера — выбрать до начала

1. **Полный Blender** (по умолчанию): каждая сцена анимированный клип, ~1–3 с/кадр, минута ролика ≈ 1,5–2 ч.
2. **Быстрый**: из Blender стоп-кадры (`--times … --scale 1.25`) + движение камеры в монтаже (`PhotoBG` zoom/pan),
   анимируются только ключевые «живые» планы (пример `projects/fr-test-1b/`), ~15 мин против ~45. Предлагать, когда важна скорость.

## Шаги

1. **Проект.** `projects/<id>/` по `projects/_template/README.md`. Рабочая папка на ПК:
   `bash blender/kit/new_blender_project.sh <id>`; для городских сцен с новыми людьми — от `projects/fr-klassika/`.
   Нужные готовые сцены взять из `blender/library/` (копировать в `blender/sets/` проекта — модули импортируют друг друга по имени).
2. **Факты → сценарий** → `script_lint.py` до `LINT OK` (хук ≤ 7 слов, Algenib ≈ 2 слова/с, факт каждые 2–3 предложения).
3. **Голос** Gemini «Algenib», 2 дубля на секцию, Whisper, −16 LUFS → `words.json`.
4. **Таймлайн.** `tools/build_timeline.py` → `blender/shots.json` → сцены в `blender/sets/<set>.py`.
5. **Картинка (правила).** Модели только из кода (`blender/kit/blender/lib.py`, `blender/library/`), матовые формы.
   Светлые сцены, минимум теней: `lib.camera_fill()`, экспозиция +0.35…0.6, туман только мешем `lib.fog_box`.
   Тёплое вечернее небо. Город, а не одна улица (`paris.py`). Улицы живые, но не перегруженные (`people2.py`).
   На фоне признаки цивилизации (`civ.py`). Люди и конфликты стилизованно, без крови.
   Камера двумя ключами на сцену, ~44 мм при «1x», `clip_start` ≥ 0.1 (на облётах 1.0). Не класть плоскости одной высоты внахлёст.
6. **Стоп-кадры** `tools/stills.sh` и контактный лист — смотреть самому до рендера.
7. **Рендер** на ПК: задачи в `jobs/queue/` (пользователь запускает `START_WORKER.bat`), `tools/mkrender.sh`,
   клипы для Remotion `-bf 0 -g 30 -keyint_min 30`. `.ps1` с кириллицей — UTF-8 с BOM.
8. **Сборка** `tools/mix.py` (свои звуки `sfx_mbg.py`, `soundtrack.wav`) → `tools/build_spec.py` → `render.py` в KINEMA →
   `qa.py` → 20+ кадров из готового MP4. Титры editorial сверху, концовка `TikTokProfile` (`dark: true`) на `IPhone17`.
   «Оформление как в гибриде» → разметку титров и звуки взять из `styles/gibrid/README.md`.
9. **Выдача** отдельным файлом с новой версией. Исходники проекта (только отличия от `blender/kit/`) — в `projects/<id>/`,
   строка — в `output/README.md`. Новые удачные модели — в `blender/library/` с описанием. Новые правки пользователя —
   в `knowledge/rules/blender-pipeline.md` и `styles/blender/README.md` с датой.

## Грабли Blender (кратко)

World Volume в Eevee Next гасит небо → туман мешем; небо через `TexCoord.Generated`; кириллица — `arialbd.ttf`;
частые ключи в `lib.animate_camera` дают рывки; `clip_start` 0.02 → асфальт проступает сквозь тротуар
(«лаги дороги», 23.10.2026). Из облака нет доступа к download.blender.org и replicate.com — всё через воркер на ПК.
