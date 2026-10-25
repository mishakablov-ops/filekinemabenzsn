# Звуки для примера «Сосед с шестого этажа»

Пример рендерится и без них — движок просто пропустит отсутствующие файлы. Чтобы звучало как в оригинале,
положите свои mp3 в `engine/public/projects/sosed6/sfx-src/` с такими именами
(бесплатные звуки: pixabay.com/sound-effects, freesound.org с лицензией CC0 — проверяйте лицензию каждого файла):

| файл | что это |
|---|---|
| `drone.mp3` | низкий тёмный гул, 25+ секунд (фон всего ролика) |
| `steps_above.mp3` | шаги сверху, через потолок, глухо |
| `floor_creak.mp3` | скрип паркета / половиц |
| `clock_tick.mp3` | тиканье настенных часов |
| `vhs_tape.mp3` | видеокассета: вставили, зажевало, щелчок кнопки |
| `steps_concrete.mp3` | шаги по бетонной лестнице |
| `lamp_buzz.mp3` | гудение лампы в подъезде |
| `breath_scared.mp3` | испуганное дыхание |
| `heartbeat.mp3` | сердцебиение |
| `mailbox.mp3` | почтовый ящик открыли-закрыли |
| `pages.mp3` | шелест бумаги / фотографии |
| `door_lock.mp3` | дверной замок |
| `phone_beeps.mp3` | гудки телефона |
| `scream_long.mp3` | долгий крик (финал) |
| `stinger.mp3` | резкий хоррор-удар (финал) |
| `furniture_drag_muf.mp3`, `child_cry_muf.mp3` | «через потолок»: сделайте из обычных `furniture_drag.mp3` и `child_cry.mp3` командой ниже |

```
ffmpeg -i furniture_drag.mp3 -af "lowpass=f=700,lowpass=f=900,aecho=0.8:0.6:45|90:0.35|0.2,volume=2.2" furniture_drag_muf.mp3
ffmpeg -i child_cry.mp3 -af "lowpass=f=700,lowpass=f=900,aecho=0.8:0.6:45|90:0.35|0.2,volume=6" child_cry_muf.mp3
```

Тайминги звуков задаёт `assets/models-src/sosed6/storyboard.py` (параметр `from` — с какой секунды файла играть).
Если ваш файл начинается с тишины, поправьте `from` и пересоберите: `python -I storyboard.py`.
