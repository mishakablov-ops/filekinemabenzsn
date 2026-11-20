# kinema-extra · своё поверх движка

Файлы канала aipollon, которых нет в общей сборке KINEMA: аватарка и обложки для сетки профиля в концовке
(`TikTokProfile`), два звука. Пути повторяют движок: после `git clone … kinema` скопировать эту папку поверх
(`cp -r kinema-extra/skills kinema/`), тогда обложки лягут в `kinema/skills/reel-studio/engine/public/brand/tiles/`.

Новая обложка ролика → сюда же, в `skills/reel-studio/engine/public/brand/tiles/`.

Профиль канала для концовки — `skills/reel-studio/engine/src/brand.json` (как на ПК). С 28.10.2026 аватар —
`brand/aipollon-avatar-hermes.png` (гравюра «Гермес»), старый `aipollon-avatar.png` в роликах не используется.
Плитки профиля (`brand/tiles/<id>.jpg`, маленькие) и обложки (`cover-<id>.jpg`, кадр ролика 3:4) лежат рядом.

## 30.10.2026: свежий слой — в репозитории движка

Слой канала заново сведён с новым KINEMA (агентские команды `kinema.py`, звуки mike `usr-*`, карточки `NameCard`/`RuleCard`,
переход `ring`, быстрые черновики). Он лежит в `Wpresser/Algorithm-for-aipollon`, папка `aipollon/kinema-extra/`
(полный `engine/src` канала, `brand.json`, обложки, `references/` с разделами канала). После клона движка:
`cp -r kinema/aipollon/kinema-extra/skills kinema/`. Эта папка — старая копия без кода движка; обложки с лицами
реальных людей сюда не кладём.

