# Баронесса-пулемётчица (`baronessa`)

- **Стиль:** **Мемы** (`styles/02-memy/README.md`), Блендер, полный режим: каждая сцена — клип Blender 30 к/с, сборка KINEMA 60 к/с
- **Длительность:** v2 — 145,8 с, 40 сцен · **Голос:** v1 — Gemini TTS (рассказчик Charon, баронесса Pulcherrima);
  v2 — файлы, которые mike сгенерировал сам и прислал (рассказчик + реплики `Б:`), склейка `engine/voice_v2.py`
- **Статус:** **одобрен** 29.10.2026 («все хорошо»). Финал — `output/baronessa-v2-5-nomusic.mp4` (без фоновой
  музыки: «Gopher Mambo» mike добавляет в TikTok из библиотеки звуков). QA PASS
- **Задание (28.10.2026):** комедийная альтернативная история по мему «Баронесса-пулемётчица», около 2 минут,
  реалистично, не мультяшно, рендер в Blender на ПК. Первый ролик стиля «Мемы». Длительность — для этого ролика, не правило.
- **Мем и ограничения:** `notes/meme.md` (источники, лор, что не берём). Персонаж — по самому мему
  (`hero/meme_ref/meme_photo.png`, mike сообщил согласие человека за мемом), полная фигура.

> **Лицо реального человека.** Этот репозиторий публичный, поэтому кадр мема (`hero/meme_ref/meme_photo.png`), лист референсов (`hero/ref/tpose_c.png`) и модель `baroness_rig.blend` (сделана по лицу человека за мемом) сюда не кладём: они на ПК и в приватном репозитории движка `Wpresser/Algorithm-for-aipollon` (`aipollon/`). Голосовой образец для `engine/clone_baroness.py` в git не хранится нигде.

## Структура

```
baronessa/
  README.md, script.md (v1), script-v2.md (v2, жёсткий юмор-экшн)
  notes/    meme.md (мем, лор, ограничения), status-v2.md (как шла v2)
  hero/     gen_baroness*.py (лист референсов → 3D hyper3d/rodin), rig_baroness.py (скелет с именами костей HeroRig),
            inspect_glb.py, debug_pose.py; ref/tpose_c.png (лист референсов), meme_ref/meme_photo.png (кадр мема)
  blender/  build_pc.py, shots.json (v1), shots_v2.json (v2, 40 сцен); sets/: baroness.py (загрузка модели, позы
            через sila_hero, моргание, lipsync), bar_props.py (PBR-материалы, HDRI, реквизит), bar_sets.py (сцены v1),
            bar_v2.py (Ставка с картой, армия, танк «Биркин-34», залпы, осада, парад…), bar_test.py
  engine/   storyboard.py / storyboard_v2.py (spec.json), voice_sections.py (v1, Gemini), voice_v2.py (v2, файлы mike),
            clone_baroness.py
  tools/    build_timeline*.py, build_spec.py, mix.py, assemble*.ps1, render_clips.ps1, test_stills.ps1,
            setup_blender.ps1, get_polyhaven.py
```

Модель баронессы — `assets3d/people/own/baronessa/baroness_rig.blend` (строка в `assets3d/manifest.csv`; файл — см. выше);
`baroness.py` ищет её в `blender/assets/` на ПК, затем в `assets3d/`. `music_bed.py` совпадает с
`blender/kit/tools/music_bed.py` — на ПК скопировать его в `tools/` перед `assemble*.ps1`.

Не в git: клипы, рендеры, кадры, озвучка, текстуры Poly Haven CC0 (`assets_ph/`, качаются `tools/get_polyhaven.py`).
Фикс движка, найденный в этом ролике (`Math.floor(f)` в громкости музыки, `engine/src/audio/Soundtrack.tsx`), —
в репозитории KINEMA `Wpresser/Algorithm-for-aipollon`.

## Журнал версий
- v1 28.10.2026 — `baronessa-v1.mp4`: «сделал слишком мягко» → v2.
- v2 28–29.10.2026 — `baronessa-v2-1` … `v2-5`: шутка в каждой строке, Ставка с картой брендов, армия баронесс,
  враги-манекены, кинохроника 40-х, PBR и небо Poly Haven, lipsync. v2-5 с музыкой trap-hype + dark-cinematic
  одобрен; mike взял вариант без музыки (`baronessa-v2-5-nomusic.mp4`). Все правки — журнал в `styles/02-memy/README.md`.
