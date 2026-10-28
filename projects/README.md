# Проекты (ролики)

Одна папка на ролик: `projects/<id>/`, `<id>` латиницей через дефис (как на ПК). Только исходники — рендеры, кадры
и дубли голоса остаются на ПК. Структура папки — [`_template/README.md`](_template/README.md).

| id | тема | стиль | статус | выдача |
|---|---|---|---|---|
| `quiet-evenings` | «Тихие вечера», 40 с | Reel Studio 3D (до разделения стилей) | **одобрен** 21.10.2026 | `quiet-evenings-40s-v5.mp4` |
| `mir-bez-granic` | «Мир без границ», 67 с, 15 сцен | Блендер · Классика | **одобрен** 22.10.2026 | `mir-bez-granic-v2.mp4` |
| `fr-klassika` | прогулка по Франции, город Париж | Блендер (полный) | тест стиля, текущий пайплайн | `fr-klassika-blender-v3.mp4` |
| `fr-gibrid` | Франция | Гибрид | тест | `fr-gibrid.mp4` |
| `edinyi-yazyk`, `edinyi-yazyk-v2` (концовка — `script_end.md`) | «Один язык», реалистичная картинка Poly Haven | Гибрид (тема `fresh`) | выдан 23.10.2026 | `edinyi-yazyk.mp4` |
| `kosmos-dlya-vseh`, `kosmos-dlya-vseh-v2` | «Космос для всех» | Блендер | выдан 24.10.2026 | `kosmos-dlya-vseh-v2.mp4` |
| `posledniy-chelovek` | «Последний человек на Земле», «ты»-история, 64 с, 20 сцен | Гибрид | выдан 26.10.2026 | `posledniy-chelovek.mp4` |
| `posledniy-chelovek-blender` | та же история в реалистичных цветах (голос и титры те же) | Блендер: v1 быстрый, v2 полный | выданы 26.10.2026 | `posledniy-chelovek-blender.mp4`, `posledniy-chelovek-blender-v2.mp4` |
| `sposobnosti` | «Каждому по способности»: всем по суперсиле, история от первого лица, **две части по ~60 с**, герой по фото пользователя | Блендер (полный, 40 клипов) | выдан 28.10.2026 | `sposobnosti-1-v2.mp4`, `sposobnosti-2-v2.mp4` |
| `metro-city` | постоянный город «Метрополис» для всех городских сцен (не ролик, а декорация): план, точки съёмки, карта | Блендер | v1 в работе 26.10.2026 | кадры в общей папке `aipollon/metro/` |

Эталоны «Гибрида» (`coffee-agent`, `nuclear-survival`) и демо движка `demo-promo` — в `kinema/skills/reel-studio/examples/`.

Для Blender-проектов здесь лежат **только файлы, которые отличаются от `blender/kit/`** (остальное восстанавливается
из кита). Модули сцен, которые совпадают с `blender/library/`, тоже не храним: при пересборке их копируют из
библиотеки в `blender/sets/`. Папка `engine/` = то, что на ПК лежало в `reel-studio/engine/public/projects/<id>/`
(spec, words, storyboard); `script.md` — только в корне папки ролика. Обложки — в
`kinema/skills/reel-studio/engine/public/brand/tiles/`.

Чистка 26.10.2026 (просьба пользователя): удалены тесты `fr-test*`, копия `demo-promo`, дубли сценариев, обложек и
модулей, голос Charon «Мира без границ» (выбран Algenib). Всё есть в истории git.
