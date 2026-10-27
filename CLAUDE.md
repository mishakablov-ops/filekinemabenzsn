# Инструкции для Claude

Это рабочая база проекта aipollon. Отвечать пользователю по-русски.

1. В начале любой задачи прочитай `README.md` (карта папок) и `knowledge/aipollon-knowledge.md`.
   Движка `kinema/` в git нет: если папки нет, `git clone https://github.com/Wpresser/Algorithm-for-aipollon kinema`
   и `cp -r kinema-extra/skills kinema/` (аватарка и обложки канала).
   При расхождении главнее: свежие пожелания пользователя → `knowledge/rules/*` → `styles/<стиль>/README.md` →
   общие правила движка `kinema/AGENTS.md`, `kinema/skills/reel-studio/SKILL.md` и `references/`.
2. Стиль ролика: `/gibrid` → `skills/gibrid/SKILL.md`, `/blender` → `skills/blender/SKILL.md`. Если стиль не назван — спроси.
3. Новый ролик — новая папка `projects/<id>/` по `projects/_template/README.md`. Готовый MP4 — строка в `output/README.md`.
4. Новая 3D-модель: из кода → `blender/library/` (+ строка в его README); файлом → `assets3d/<категория>/<источник>/`
   + строка в `assets3d/manifest.csv` (источник, лицензия, автор). Только CC0 / CC-BY (с указанием автора).
5. Новый стиль — по шаблону `styles/_template/README.md`, строка в `styles/README.md`.
6. Новое пожелание пользователя — сразу записать в `knowledge/aipollon-knowledge.md` и в нужный файл `knowledge/rules/`
   или `styles/`, с датой. Не переносить сюжет и длительность одного ролика на все будущие.
7. Ничего не класть в корень и не сваливать в одну папку. MP4, кадры, дубли голоса и секреты в git не коммитить.
8. Удалять файлы на ПК пользователя только по его прямой команде.
