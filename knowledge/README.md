# Знания проекта

| файл | что |
|---|---|
| [`aipollon-knowledge.md`](aipollon-knowledge.md) | **короткая выжимка всего**: канал, два стиля, образцы, формат, голос, звук, сценарий, QA, ограничения. Читать в начале каждой задачи |
| [`rules/styles.md`](rules/styles.md) | требования пользователя к оформлению (с датами) |
| [`rules/sound.md`](rules/sound.md) | звук и музыка, одобренные решения |
| [`rules/qa-checklist.md`](rules/qa-checklist.md) | что проверять перед выдачей |
| [`rules/blender-pipeline.md`](rules/blender-pipeline.md) | пайплайн Blender, грабли, полный список правок пользователя |
| [`rules/AGENTS-pc.md`](rules/AGENTS-pc.md), [`rules/CLAUDE-pc.md`](rules/CLAUDE-pc.md) | инструкции, которые лежали в корне папки на ПК (пути в них — ПК-шные, см. таблицу в корневом README) |
| [`reel-studio-pc/SKILL-2026-10-23.md`](reel-studio-pc/SKILL-2026-10-23.md) | SKILL.md старой Reel Studio с ПК — для сравнения с `kinema/skills/reel-studio/SKILL.md` |

Эти файлы — правила **канала aipollon**; они главнее общих правил движка в `kinema/skills/reel-studio/references/`
(там универсальная версия для всех пользователей KINEMA).

## Как пополнять

- Новое явное пожелание пользователя → дописать в нужный `rules/*.md` раздел с датой (`## … — ДД.ММ.ГГГГ`)
  и одну строку в `aipollon-knowledge.md`. Новое главнее старого; старое не стирать, а помечать «отменено ДД.ММ».
- Не переносить сюжет и длительность одного ролика на все будущие задания.
- Пожелание про конкретный стиль → `styles/<стиль>/README.md`.
