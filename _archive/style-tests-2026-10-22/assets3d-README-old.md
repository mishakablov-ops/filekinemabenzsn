# assets3d — библиотека бесплатных 3D-ассетов для Blender-сцен

Все ассеты под лицензией **CC0** (можно использовать в коммерческих роликах без указания автора).
Источники: Kenney (kenney.nl), Quaternius (quaternius.com, зеркало автора на opengameart.org),
Poly Haven (polyhaven.com: модели и HDRI), ambientCG (ambientcg.com: PBR-текстуры).

Структура:
- `people/`    — люди с анимациями (Quaternius, Kenney animated characters)
- `vehicles/`  — машины, автобусы, поезда, лодки
- `city/`      — здания, дороги, уличные мелочи, промышленность
- `nature/`    — деревья, кусты, трава, камни
- `interior/`  — мебель, посуда, техника, еда
- `animals/`   — животные (Quaternius)
- `props/`     — прочие предметы Poly Haven
- `hdri/`      — небо: `urban`, `sunset`, `sky` (Poly Haven, 2k .hdr)
- `textures/`  — PBR-материалы ambientCG (1K-JPG) по категориям
- `manifest.csv` — что откуда скачано
- `_tools/download_assets.ps1` — скачивание (повторный запуск докачивает недостающее; `-Only kenney,hdri` и т. п.)

Внутри каждой категории подпапка источника: `kenney/`, `quaternius/`, `polyhaven/`.
Kenney и Quaternius — стилизованный low-poly (FBX/OBJ/GLB/blend), Poly Haven — фотореалистичные .blend с текстурами 1k.
