# blender-kit — 3D-сцены в Blender на ПК пользователя + сборка в Reel Studio

Полное описание, грабли и правки пользователя: `../references/blender-pipeline.md`.

    bash blender-kit/new_blender_project.sh <id>      # (в VM) создаёт "aipollon claude/<id>/"

Состав:
- `START_WORKER.bat`, `tools/worker/worker.ps1` (в корне репозитория) — окно-исполнитель задач `jobs/queue/*.ps1` (запускает пользователь).
- `blender/lib.py` — материалы, примитивы, свет, камера (`animate_camera`), туман-мешем, люди (`person`, `walk`, `move_root`), машины (`car`, `drive`), заполняющий свет `camera_fill`.
- `blender/sets/` — готовые наборы: globe (границы стран), wall, checkpoint, passport, city, village, military (солдаты, танки, бой), tabletop, pumpjack, **civ** (фон цивилизации).
- `blender/build.py` — `blender -b --factory-startup --python build.py -- --shot <id> [--anim | --times 1,2] [--scale 0.5]`.
- `tools/mkjob.sh`, `tools/stills.sh`, `tools/mkrender.sh` — генераторы задач для исполнителя.
- `tools/build_timeline.py` (слова → shots.json), `tools/build_spec.py` (spec.json Reel Studio), `tools/mix.py` (музыка + звуки + приглушение под голос) — примеры из «Мира без границ», план сцен и якоря менять под новый сценарий.
- `tools/py/` — озвучка (Gemini/MiniMax/ElevenLabs/Chatterbox на Replicate), проверка Whisper, прослушка голосов, свои звуки (`sfx_mbg.py`), карты (`process_map.py`), текстуры (`make_textures.py`), контактный лист (`sheet.py`), стоп-кадры Remotion (`rs_stills.py`).
- `data/` — границы и маски суши для глобуса, `audio/sfx/` — 19 своих звуков, `blender/tex/` — карта Европы, паспорт.
