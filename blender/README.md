# Blender

| папка | что |
|---|---|
| [`kit/`](kit/) | **blender-kit** — основа каждого Blender-проекта: `blender/lib.py` (материалы, примитивы, свет, камера, туман, люди, машины), `blender/sets/` (базовые сцены: globe, wall, checkpoint, passport, city, village, military, tabletop, pumpjack, civ), `blender/build.py`, `tools/` (таймлайн, spec, микс, задачи воркера, стоп-кадры), `data/` (границы стран), `audio/sfx/` (свои звуки), `worker/`. Подробно — [`kit/README.md`](kit/README.md) |
| [`library/`](library/) | **библиотека готовых сцен и моделей из кода**, собранная в роликах: люди, Париж, космос. Пополняется после каждого ролика |

Новый проект: `bash blender/kit/new_blender_project.sh <id>` (на ПК создаёт рабочую папку `<id>/`),
затем нужные модули из `library/` копируются в `blender/sets/` проекта.
Правила картинки — `styles/blender/README.md`, грабли — `knowledge/rules/blender-pipeline.md`.

Улучшили что-то общее в `lib.py` или базовой сцене — правим в `kit/` и пишем строку в журнал ниже.

## Журнал kit
- 22.10.2026 — состояние «Мир без границ» (тег `style-01-klassika-2026-10-22`).
- 25.10.2026 — перенесён в репозиторий без изменений.
