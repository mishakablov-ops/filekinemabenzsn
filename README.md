# aipollon · рабочая база

Облачное хранилище проекта **aipollon** (вертикальные ролики 9:16 для Reels/Shorts/TikTok, канал `@videopollon`).
С 25.10.2026 Claude работает **с этим репозиторием**, а не с файлами на ПК: всё новое (3D-модели, стили, правила,
исходники роликов) добавляется сюда, по папкам ниже. Файлы на ПК удаляются **только по прямой команде пользователя**.

## Карта

| папка | что лежит | кто меняет |
|---|---|---|
| `kinema/` | движок KINEMA (Remotion + three.js + Python). **В git не хранится**: свежая сборка — в репозитории [`Wpresser/Algorithm-for-aipollon`](https://github.com/Wpresser/Algorithm-for-aipollon); перед работой `git clone https://github.com/Wpresser/Algorithm-for-aipollon kinema` и скопировать поверх слой канала из него же: `cp -r kinema/aipollon/kinema-extra/skills kinema/` (код движка канала, обложки; сведён с новым KINEMA 30.10.2026) | обновляется в репозитории движка |
| [`kinema-extra/`](kinema-extra/) | своё поверх движка: аватарка, обложки для концовки, два звука | Claude, новая обложка = новый файл |
| [`knowledge/`](knowledge/) | знания и правила канала: выжимка, правила оформления, звука, QA, Blender-пайплайн, **продвижение по файлу маркетолога** (`rules/marketing.md`, с 30.10.2026) | Claude, при каждом новом пожелании пользователя |
| [`skills/`](skills/) | тексты скиллов `/gibrid` и `/blender` (что делать по шагам) | Claude, при изменении процесса |
| [`styles/`](styles/) | стили роликов: описание, правила, шаблон для нового стиля | Claude, новый стиль = новая папка по шаблону |
| [`blender/`](blender/) | blender-kit (lib.py, базовые сцены, инструменты, воркер) и библиотека готовых сцен из кода | Claude |
| [`assets3d/`](assets3d/) | 3D-файлы (glb/gltf/blend/fbx), небо HDRI, текстуры + `manifest.csv` с лицензиями | Claude, по одной записи в манифест на каждую модель |
| [`projects/`](projects/) | исходники каждого ролика: сценарий, spec.json, words.json, сцены Blender, задачи воркера | Claude, одна папка на ролик |
| [`output/`](output/) | каталог готовых роликов (сами MP4 в git не хранятся) | Claude, строка на каждую выдачу |
| [`tools/`](tools/) | общие утилиты: окно-воркер `START_WORKER.bat` для ПК | редко |

## Главные правила хранения

1. **Ничего в одну кучу.** Каждый файл кладётся в свою папку по таблице выше; в каждой папке есть README с правилами.
2. **Новые версии — новыми файлами** (`-v2`, `-v3`), старые не перезаписывать, если пользователь не просил.
3. **Только то, что помогает делать следующие ролики** (пользователь, 26.10.2026): правила, код, модели, референсы,
   сценарии и раскадровки. Дубли, видео, тестовые и отклонённые материалы, устаревшие копии правил не хранить — уроки
   из них переносить в правила, старое состояние достаётся из истории git. Модуль, который совпадает с
   `blender/library/`, в проект не копировать.
4. **Тяжёлое не в git**: MP4-рендеры, кадры `renders/`, дубли голоса, Blender-установка остаются на ПК
   (`.gitignore`). Ограничение GitHub — 100 МБ на файл; модели и звуки до ~20 МБ хранить можно.
5. **Секреты** (`.secrets.env`, токены Replicate и т. п.) никогда не коммитить.
6. Где ПК ещё нужен: рендер Blender и Remotion идёт на ПК пользователя (RTX 3060) через `START_WORKER.bat`.
   Облако готовит файлы здесь → пользователь делает `git pull` на ПК (или Claude передаёт архив) → воркер рендерит.

## Соответствие старых путей на ПК (`C:\Users\Gigabyte\Documents\aipollon claude`)

| на ПК | здесь |
|---|---|
| `AIpollon-Reel-Studio/skills/reel-studio/` | `kinema/skills/reel-studio/` (новая версия движка) |
| `AIpollon-Reel-Studio/skills/reel-studio/references/` (правила канала) | `knowledge/rules/` (главнее общих `kinema/.../references/`) |
| `AIpollon-Reel-Studio/skills/reel-studio/blender-kit/` | `blender/kit/` |
| `AIpollon-Reel-Studio/skills/reel-studio/engine/public/projects/<id>/` | `projects/<id>/engine/` |
| `<id>/` (проекты Blender в корне) | `projects/<id>/` (только файлы, отличные от `blender/kit/`) |
| `styles/` | `styles/` |
| `AGENTS.md`, `CLAUDE.md`, `aipollon-knowledge.md` | `CLAUDE.md`, `knowledge/rules/AGENTS-pc.md`, `knowledge/aipollon-knowledge.md` |
| `START_WORKER.bat`, `worker/` | `tools/worker/` |
| `output/*.mp4` | остаётся на ПК, список в `output/README.md` |
