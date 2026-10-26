# Последний человек на Земле (`posledniy-chelovek`)

- **Стиль:** гибрид («ты»-история: зритель и есть последний человек)
- **Длительность:** 64,6 с (голос 62,7 с, 131 слово, 2,1 слова/с), 20 сцен · **Голос:** Gemini 3.1 Flash TTS «Algenib»
- **Статус:** выдан 26.10.2026 (`posledniy-chelovek.mp4`: общая папка проекта `aipollon/posledniy-chelovek/`, на ПК — `output/`)
- **Задание (26.10.2026):** «сделай мне историю на тему, что будет если на земле пропадут все люди и останется только
  1 человек, обращайся к зрителю, будто это он /gibrid»

## Факты и источники

| в ролике | источник |
|---|---|
| 8 миллиардов людей | ООН, World Population Prospects 2024: 8,2 млрд — https://news.un.org/en/story/2024/07/1151971 |
| свет гаснет через несколько часов, станциям нужны люди | А. Вейсман, «Мир без нас» (2007); History, «Life After People» (2008) |
| хлеб плесневеет за неделю («7 дней» — верхняя граница) | USDA FoodKeeper: магазинный хлеб при комнатной температуре 2–4 дня; с консервантами до ~7 дней — https://www.healthline.com/nutrition/how-long-does-bread-last |
| консервы до пяти лет | USDA FSIS: низкокислотные консервы 2–5 лет (неповреждённые безопасны и дольше) |
| бензин портится за 3–6 месяцев («полгода») | AAA — https://cluballiance.aaa.com/the-extra-mile/advice/car/how-to-keep-gas-from-going-bad |
| треть людей не видит Млечный Путь | Falchi et al., *Science Advances*, 10.06.2016, «The new world atlas of artificial night sky brightness» |
| волков в зоне Чернобыля в 7 раз больше, чем в заповедниках | Deryabina et al., *Current Biology* 25(19), R824–R826, 2015 |

## Сюжет по сценам

Пустая утренняя улица («Ты просыпаешься. Людей нет.») → Земля из космоса, огни городов гаснут, счётчик 8 000 000 000 → 1 →
герой один среди брошенных машин → кафе, остывающий кофе → чат с мамой «Не доставлено» → вечерний город гаснет окнами →
пульт ТЭЦ «Аварийный останов» → «все магазины твои» → 7 дней до плесени, 5 лет консервам → «любая машина твоя» →
6 месяцев бензину → чёрный город и Млечный Путь → 33 % людей его не видели → волки на улице → 1× / 7× Чернобыль →
тёмная Земля с меткой «ТЫ» → пустая комната, «Тишина» → дверь, «стучат» → концовка: айфон (тёмно-синий) разворачивается
к тёмному профилю TikTok.

## Что появилось в движке ради этого ролика (KINEMA, 26.10.2026)

- `Street3D`: `stopped` (машины стоят как бросили, у каждой второй открыта водительская дверь), `lightsOut` (окна, фонари
  и фары гаснут за ~1,2 с по слову), `stars` (ночное небо и полоса Млечного Пути), `wolves[]` (low-poly волки рысью),
  у `walkers` есть `rotY`.
- `Globe3D look "dusk"` (тёплая тёмная Земля) + `cities` / `citiesOut`: огни ~140 городов гаснут по одному.
- `ChatScreen`: мессенджер, сообщение «Отправка…» → красный «!» и «Не доставлено» по слову (`failAt`).
- `TikTokProfile dark: true` — тёмная тема профиля; `IPhone17 color` (перенесено с ПК) перекрашивает корпус.
- `Counter labelSize`, `Bars3D cam` ключами, у строки `status` в `Terminal` есть `hint: ""` (без «esc to interrupt»).
- `dotTexture()` в `three/core.tsx`: круглые мягкие точки для `PointsMaterial` (без неё звёзды и огни квадратные).
- Звуки `door-knock` (три удара в деревянную дверь) и `wolf-howl` (вой двух волков) в `scripts/sfx_extra.py`.
- Рендер без видеокарты: `REMOTION_GL=swangle` для `render.py` и `tools/stills.mjs`.

## Структура

```
posledniy-chelovek/
  README.md, script.md, cover.jpg (обложка 540×720 для сетки профиля)
  engine/   storyboard.py → spec.json, voice_sections.py (голос по секциям), stills.py (лист кадров), words.json, tts_report.json
  voice/    manifest.json: оценки Whisper всех дублей и выбранный (сами wav — на ПК)
  jobs/     300_posledniy_voice.ps1 — голос на ПК (301–303 — та же задача повторно после исправлений)
  qa/       qa.md
```

Повторить: `python -I projects/posledniy-chelovek/engine/storyboard.py` (нужны `words.json` и `voice.wav` в
`kinema/skills/reel-studio/engine/public/projects/posledniy-chelovek/`), затем `stills.py`, затем
`REMOTION_GL=swangle python -I kinema/skills/reel-studio/scripts/render.py posledniy-chelovek --concurrency 4`.

## Журнал версий
- v1 26.10 — 64,6 с, 20 сцен, 64 МБ. QA PASS (см. `qa/qa.md`). Голос: 18 дублей (на концовку 4: в двух первых Whisper не узнал «нейросеть»), ~$0,54.
  Отзыв пользователя: ждём.
