# hero-aipollon — главный герой канала

Модель по референсу mike от 26.10.2026 (`reference.png`): чиби-парень с большой головой, короткий чёрный фейд,
большие карие глаза, густые брови, чёрное худи с карманом-кенгуру и серыми шнурками, чёрные джоггеры,
массивные белые кроссовки. Сделана нами из кода, лицензия CC0.

![превью](preview.jpg)

| файл | что это |
|---|---|
| `../../../../blender/library/hero.py` | **источник**: модель кодом для Blender (позы, ходьба, сидя) |
| `hero-aipollon.glb` | та же модель файлом (для KINEMA / three.js, других программ) |
| `preview.jpg` | превью: 3/4, спереди, сбоку, сзади, лицо (Cycles) |
| `reference.png` | исходная картинка от пользователя |
| `make.py` | пересобирает `.glb` и превью из `hero.py` |

## Как использовать в Blender-ролике

Скопировать `blender/library/hero.py` и `people2.py` в `blender/sets/` проекта (как остальные модули библиотеки), затем:

```python
import hero as H
p = H.hero((x, y, 0), heading, coll=coll, pose='stand')    # stand | still | cheer | point | sit | walk
# ходьба: pose='walk', затем
P = H.walk(p, speed=1.0)
lib.move_root(p, [(x0, y0, 0), (x1, y1, 0)], t0=0.0, speed=1.0)
```

- Рост 1.75 м при `height=1.0` (голова ~40 % роста), вперёд — локальная −Y, корень у ног, как у `people2.person`.
- Замена старого героя (`pcommon.hero`, белая кепка и оранжевое худи): та же сигнатура
  `hero(loc, heading, coll, pose, name, rng)`, части в том же словаре (`thighL`, `upperR`, `head`…).
  Ходить и сидеть — через `H.walk` / `H.sit`: ноги у героя короче, чем у `people2`.
- Цвета в `H.COL`, материалы в `H.mats()`.

## Как использовать .glb

Узлы названы как суставы (`Hero_hips`, `Hero_thighL`, `Hero_shinL`, `Hero_shoeL`, `Hero_upperL`, `Hero_foreL`,
`Hero_head`…), позу можно задавать поворотом узлов. Фейд стрижки — цвета вершин головы (COLOR_0; в three.js
`vertexColors: true` у материала головы). Анимации в файле нет.

## Пересборка

```
blender -b --factory-startup --python assets3d/people/own/hero-aipollon/make.py -- --previews
```
(проверено на bpy 5.1; на ПК Blender 4.5 — та же команда).
