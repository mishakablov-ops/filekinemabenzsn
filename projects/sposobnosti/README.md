# Каждому по способности (`sposobnosti`, две части)

- **Стиль:** Блендер, полный режим (каждая из 40 сцен — анимированный клип Blender 4.5 Eevee, 30 к/с, ролик 60 к/с)
- **Длительность:** часть 1 ≈ 60 с (20 сцен), часть 2 ≈ 60 с (20 сцен) · **Голос:** Gemini 3.1 Flash TTS «Algenib»
  (по секциям, 2 дубля, выбор по Whisper; `engine/voice_sections.py`)
- **Статус:** в работе
- **Задание (28.10.2026):** «Сделай, короче, видос на тему, что будет, если каждый человек получит по одной способности.
  Введи историю от лица главного героя, референсы тебе скинул в двух фотках. Сделай ролик на две части, каждый по минуте.
  /blender». Две части по минуте — только для этого ролика.
- **Герой:** по двум фото пользователя: лист референсов (nano-banana-pro) → 3D (hyper3d/rodin) → скелет `HeroRig`
  (`hero/gen_hero.py`, `hero/rig_hero.py`), модель `assets3d/people/own/sposobnosti-hero/hero_rig.blend`.
  Первый герой из примитивов отвергнут: «не похоже вообще».

## Факты и источники

| в сценарии | источник |
|---|---|
| 8 миллиардов людей | ООН, World Population Prospects 2024: ≈ 8,2 млрд в 2025 году — https://population.un.org/wpp/ |
| машина ≈ 1,5 т | снаряжённая масса легковых машин гольф-класса 1,2–1,6 т (данные производителей) |
| ≈ 100 000 рейсов в день | ATAG, Aviation: Benefits Beyond Borders — https://aviationbenefits.org/ |
| молния ≈ 300 млн вольт | NOAA / National Weather Service — https://www.weather.gov/safety/lightning-power |
| ветер больше 250 км/ч | шкала Саффира — Симпсона, категория 5: от 252 км/ч — https://www.nhc.noaa.gov/aboutsshws.php |
| ураган за сутки — в 200 раз больше всех электростанций | NOAA AOML, Hurricane FAQ («How much energy does a hurricane release?») — https://www.aoml.noaa.gov/hrd-faq/ |

## Сюжет и сцены

Часть 1 (`a01`–`a20`): ночью всем досталось по суперсиле → утро во дворе (сосед летит, бабушка поднимает машину
взглядом, курьер телепортируется) → город без пробок, полгорода в воздухе, пустой аэропорт (вид из зала, табло
«ОТМЕНЕН») → герой весь день ищет свою силу (лавочка, кружка) → вечером сосед над его головой падает в кусты → рядом
с героем чужие силы гаснут → «восемь миллиардов суперлюдей и один обычный» → утром стук в дверь, «вторая часть уже
в профиле» (айфон с профилем, новая плитка «ЧАСТЬ 2»).

Часть 2 (`b01`–`b20`): за героем приходят люди в форме → за неделю мир сломался (невидимки чистят магазины, парень
с молниями оставил район без света, 300 млн вольт) → человек-погода закрутил над городом ураган (250 км/ч, ×200) →
героя высаживают на краю бури, ветер вокруг него стихает, рука на плечо — ураган исчезает → очередь у его двери →
«самая нужная сила — быть обычным» → «а какую выбрал бы ты?» → концовка «это видео сделала нейросеть» с айфоном.

Места в «Метрополисе» — из генератора `metro_spots.py` (`tools/places.py`), камеры и цели — в `blender/shots.json`.

## Как собрать

1. Голос на ПК: `python -I engine/voice_sections.py 1` и `2` → `KINEMA/.../engine/public/projects/sposobnosti-{1,2}/`
   (`voice.wav`, `words.json`, `voice_manifest.json`).
2. `python3 tools/build_timeline.py` → `blender/shots.json` (сцены на якорных словах, события по словам).
3. Стоп-кадры и клипы — задачи воркера: `python3 tools/mkjob.py NAME still|clip SCALE shot[:t[:tag]] …`
   (`blender/build_pc.py`: `--ts 0.3,0.85` — несколько кадров одной сборки; `--mp4 … --fps 30 --samples 24` — клип).
4. Клипы `a*` → `engine/public/projects/sposobnosti-1/clips/`, `b*` → `sposobnosti-2/clips/`.
5. `python3 engine/storyboard.py` → `spec.json` обеих частей. Обложки частей — кадр самого ролика на хуке, 3:4
   (`jobs/415_assemble.ps1`: часть 1 — 2,9 с, часть 2 — 1,25 с, `jobs/bg_416_cover2.ps1`; на 1,6 с уже идёт переход в b02),
   в `engine/public/brand/tiles/cover-sposobnosti-{1,2}.jpg` — они же плитки «ЧАСТЬ 2» в профиле на концовках.
6. Проверка наложений по стоп-кадрам раз в секунду (`tools/rs_stills.py … --every 1 --qa --sheet`), затем
   `render.py sposobnosti-1` и `sposobnosti-2` (`jobs/418_render_final.ps1`, сам вызывает `qa.py`).

## Структура

```
sposobnosti/
  README.md, script-1.md, script-2.md
  hero/     gen_hero.py (лист референсов и 3D по фото), rig_hero.py (скелет HeroRig)
  blender/  build_pc.py, shots.json; sets/: sila.py (город, места, люди), sila_hero.py (герой и позы),
            sila_fx.py (ауры, облака, дождь, молнии, вихрь, самолёты), sila_sets.py (комнаты, аэропорт, ТЭЦ),
            sila_p1.py / sila_p2.py (сцены частей 1 и 2)
  engine/   storyboard.py (spec.json обеих частей), voice_sections.py
  tools/    build_timeline.py, places.py, mkjob.py, get_nasa_tex.py (карты Земли NASA на ПК)
  jobs/     задачи воркера 400–…
```

## Журнал версий
- v1 28.10.2026 — в работе.
