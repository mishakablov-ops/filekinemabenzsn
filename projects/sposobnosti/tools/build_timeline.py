"""words.json of both parts -> blender/shots.json for «Каждому по способности» (one file, ids a01.. and b01..).

Full mode: every scene is an animated Blender clip (set 'sila', variant = scene type), cut 70 ms before its anchor word.
Events are times inside the shot (seconds) taken from the words, so actions land on the voice.
    python3 tools/build_timeline.py [KINEMA engine/public/projects dir]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(PROJ, '..', '..'))
PUB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'kinema', 'skills', 'reel-studio', 'engine', 'public', 'projects')
LEAD = 0.07
FPS = 30
TAIL = {'1': 2.6, '2': 1.8}          # part 1: the profile card with «ЧАСТЬ 2» stays a bit longer

# (id, variant, anchor) ; anchor '@word(s)[#n]' or 0.0
PLAN = {
    '1': [
        ('a01', 'night', 0.0),
        ('a02', 'earth', '@Каждый'),
        ('a03', 'crowd', '@8'),
        ('a04', 'window', '@Я выглянул'),
        ('a05', 'flyer', '@Сосед сверху'),
        ('a06', 'granny', '@Бабушка'),
        ('a07', 'car', '@А машина'),
        ('a08', 'courier', '@Курьер'),
        ('a09', 'empty', '@К обеду'),
        ('a10', 'flyers', '@Полгорода'),
        ('a11', 'planes', '@Обычно'),
        ('a12', 'airport', '@А сегодня'),
        ('a13', 'search', '@А я весь'),
        ('a14', 'bench', '@Прыгнул'),
        ('a15', 'mug', '@Час'),
        ('a16', 'evening', '@Вечером'),
        ('a17', 'crash', '@И вдруг'),
        ('a18', 'realize', '@Тогда'),
        ('a19', 'ordinary', '@Восемь миллиардов суперлюдей'),
        ('a20', 'knock', '@А утром'),
    ],
    '2': [
        ('b01', 'door', 0.0),
        ('b02', 'agents', '@Люди'),
        ('b03', 'broken', '@За неделю'),
        ('b04', 'shop', '@Невидимки'),
        ('b05', 'sparky', '@Парень'),
        ('b06', 'volts', '@А в одной'),
        ('b07', 'stormman', '@Но самый'),
        ('b08', 'hurricane', '@Он закрутил'),
        ('b09', 'wind', '@Ветер'),
        ('b10', 'eye', '@Такой ураган'),
        ('b11', 'power', '@в 200'),
        ('b12', 'dropped', '@Меня высадили'),
        ('b13', 'walk', '@Я пошёл'),
        ('b14', 'hand', '@Я положил'),
        ('b15', 'vanish', '@И ураган'),
        ('b16', 'queue', '@Теперь'),
        ('b17', 'struggle', '@Те кто'),
        ('b18', 'calm', '@Самая нужная'),
        ('b19', 'you', '@А какую'),
        ('b20', 'cta', '@Кстати'),
    ],
}

# events: shot id -> {name: (phrase, nth, delta)} ; time = start of the phrase - shot start + delta
EVENTS = {
    'a01': {'gift': ('суперсилу', 1, -0.2)},
    'a02': {'one': ('Одну', 1, 0.0), 'forever': ('Навсегда', 1, 0.0)},
    'a03': {'second': ('восемь', 1, 0.0)},
    'a05': {'fly': ('летит', 1, -0.3)},
    'a06': {'lift': ('поднимает', 1, -0.1)},
    'a08': {'vanish': ('исчезает', 1, 0.1), 'appear': ('стоит', 1, -0.1)},
    'a09': {},
    'a11': {},
    'a12': {'empty': ('пустые', 1, 0.0)},
    'a14': {'jump': ('взлететь', 1, -0.15), 'fall': ('Упал', 1, -0.05)},
    'a16': {'over': ('над', 1, 0.0)},
    'a17': {'crash': ('рухнул', 1, 0.0)},
    'a18': {'wave': ('гаснут', 1, -0.35), 'others': ('чужие', 1, 0.0)},
    'a19': {'one': ('И один', 1, 0.0)},
    'a20': {'knock': ('постучали', 1, 0.0)},
    'b01': {'open': ('пришли', 1, -0.5)},
    'b02': {'need': ('Ты нам', 1, 0.0)},
    'b05': {'zap': ('молниями', 1, 0.0), 'out': ('света', 1, -0.1)},
    'b06': {'strike': ('молнии', 1, -0.15)},
    'b07': {'raise': ('управляет', 1, 0.0)},
    'b08': {},
    'b12': {'edge': ('бури', 1, 0.0)},
    'b13': {'calm': ('стихал', 1, 0.0)},
    'b14': {'touch': ('плечо', 1, -0.3)},
    'b15': {'gone': ('исчез', 1, -0.15)},
    'b17': {},
    'b18': {'touch': ('нужная', 1, 0.0), 'still': ('быть', 1, 0.0)},
    'b19': {'turn': ('ты', 2, -0.8)},
}


def norm(t):
    return re.sub(r'[^0-9a-zа-я]+', '', t.lower().replace('ё', 'е'))


def build(part):
    words = json.load(open(os.path.join(PUB, f'sposobnosti-{part}', 'words.json'), encoding='utf-8'))['words']
    tok = [norm(w['text']) for w in words]

    def find(phrase, nth=1):
        parts = [norm(p) for p in phrase.split()]
        hits = 0
        for i in range(len(tok)):
            if all(i + k < len(tok) and tok[i + k] == parts[k] for k in range(len(parts))):
                hits += 1
                if hits == nth:
                    return i
        raise SystemExit(f'anchor not found: {phrase}#{nth} (part {part})')

    def at(phrase, nth=1):
        return words[find(phrase, nth)]['start']

    def start_of(a):
        if isinstance(a, (int, float)):
            return float(a)
        ph, _, n = a[1:].partition('#')
        return max(0.0, at(ph, int(n or 1)) - LEAD)

    plan = PLAN[part]
    end = words[-1]['end'] + TAIL[part]
    starts = [start_of(p[2]) for p in plan]
    ends = starts[1:] + [end]
    shots = []
    for (sid, var, a), s0, s1 in zip(plan, starts, ends):
        ev = {k: round(at(ph, n) - s0 + d, 3) for k, (ph, n, d) in EVENTS.get(sid, {}).items()}
        shots.append({'id': sid, 'set': 'sila', 'variant': var, 'kind': 'clip', 'part': part,
                      'dur': round(s1 - s0 + 0.25, 3), 'start': round(s0, 3), 'anchor': a, 'events': ev})
    return shots, end


if __name__ == '__main__':
    out = os.path.join(PROJ, 'blender', 'shots.json')
    old = {}
    if os.path.exists(out):
        old = {s['id']: s for s in json.load(open(out, encoding='utf-8'))['shots']}
    allshots, ends = [], {}
    for part in ('1', '2'):
        shots, ends[part] = build(part)
        for s in shots:   # hand-set fields (camera, place, samples) survive a rebuild
            for k, v in old.get(s['id'], {}).items():
                if k not in s:
                    s[k] = v
        allshots += shots
    json.dump({'fps': FPS, 'ends': {k: round(v, 3) for k, v in ends.items()}, 'shots': allshots}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for s in allshots:
        print(f"{s['id']} {s['variant']:10s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
    print('ENDS', ends, 'total frames', sum(round(s['dur'] * FPS) for s in allshots))
