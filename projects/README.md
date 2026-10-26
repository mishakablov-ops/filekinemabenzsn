# Проекты (ролики)

Одна папка на ролик: `projects/<id>/`, `<id>` латиницей через дефис (как на ПК). Только исходники — рендеры, кадры
и дубли голоса остаются на ПК. Структура папки — [`_template/README.md`](_template/README.md).

| id | тема | стиль | статус | выдача |
|---|---|---|---|---|
| `quiet-evenings` | «Тихие вечера», 40 с | Reel Studio 3D (до разделения стилей) | **одобрен** 21.10.2026 | `quiet-evenings-40s-v5.mp4` |
| `mir-bez-granic` | «Мир без границ», 67 с, 15 сцен | Блендер · Классика | **одобрен** 22.10.2026 | `mir-bez-granic-v2.mp4` |
| `fr-klassika` | прогулка по Франции, город Париж | Блендер (полный) | тест стиля, текущий пайплайн | `fr-klassika-blender-v3.mp4` |
| `fr-test`, `fr-test-1`, `fr-test-1b` | Франция, тесты | Блендер (быстрый режим в `1b`) | тест | `styles/test/` в общей папке |
| `fr-gibrid` | Франция | Гибрид | тест | `fr-gibrid.mp4` |
| `edinyi-yazyk`, `edinyi-yazyk-v2`, `edinyi-yazyk-v2-end` | «Один язык», реалистичная картинка Poly Haven | Гибрид (тема `fresh`) | выдан 23.10.2026 | `edinyi-yazyk.mp4` |
| `kosmos-dlya-vseh`, `kosmos-dlya-vseh-v2` | «Космос для всех» | Блендер | выдан 24.10.2026 | `kosmos-dlya-vseh-v2.mp4` |
| `posledniy-chelovek` | «Последний человек на Земле», «ты»-история, 64 с, 20 сцен | Гибрид | выдан 26.10.2026 | `posledniy-chelovek.mp4` |
| `posledniy-chelovek-blender` | та же история в реалистичных цветах (голос и титры те же) | Блендер (быстрый) | выдан 26.10.2026 | `posledniy-chelovek-blender.mp4` |
| `demo-promo` | демо движка | — | пример | — |

Эталоны «Гибрида» (`coffee-agent`, `nuclear-survival`) — в `kinema/skills/reel-studio/examples/`.

Для Blender-проектов здесь лежат **только файлы, которые отличаются от `blender/kit/`** (остальное восстанавливается
из кита). Папка `engine/` = то, что на ПК лежало в `reel-studio/engine/public/projects/<id>/` (script, spec, words).
