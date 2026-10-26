# QA posledniy-chelovek.mp4 (26.10.2026)

Отчёт `scripts/qa.py` (облако, без видеокарты):


- duration 64.62s · 1080x1920 @ 60 fps · loudness -14.1 LUFS, TP -1.9
- shots 4 · average shot length 16.15s
- captions: 131 words, 2.09 w/s, 25 cards, longest card 3.9s
- layout: failed to run: 
💡 Get help for this issue at https://remotion.dev/docs/troubleshooting/webgl2-context


- **WARN** [rhythm] average shot 16.2s — too static for a reel (aim 1.2–4 s; add scene changes / camera moves)
- **WARN** [layout] failed to run: 
💡 Get help for this issue at https://remotion.dev/docs/troubleshooting/webgl2-context

## Разбор предупреждений

- **rhythm** — ложное: детектор склеек видит 4 «шота», потому что переходы мягкие (blur/zoom/dip) и сцены тёмные. На деле 20 сцен по якорям, средняя 3,2 с (от 1,7 до 7,6 с, концовка самая длинная).
- **layout** — qa.py запущен без `REMOTION_GL=swangle`, WebGL не поднялся. Та же проверка раскладки прошла в `stills.py` (`stills.mjs --qa`): 40 кадров, начало и конец каждой сцены, **QA PASS: no overlaps, no collisions, no plan errors**.

## Своя проверка

- 36 кадров из готового MP4 (0,6–63,8 с): титры не закрывают героя, айфон, монитор и счётчики; огни городов гаснут на «8 миллиардов», счётчик доходит до «1 человек на Земле»; «Не доставлено» в чате; Млечный Путь виден; концовка: синий айфон разворачивается к тёмному профилю, рамка на шапке.
- Звук: −14,1 LUFS, true peak −1,9 dBTP, LRA 3 LU, провалов тишины длиннее 0,8 с нет.
