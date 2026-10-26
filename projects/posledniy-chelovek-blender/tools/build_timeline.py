"""words.json (the voice of posledniy-chelovek) -> blender/shots.json for the Blender remake in real colours.

Same scene cuts as the gibrid version (storyboard.py of posledniy-chelovek): a scene per anchor word.
kind 'still' = one Blender frame (PhotoBG zoom/pan in KINEMA), 'clip' = animated Blender clip (VideoBG).
    python3 tools/build_timeline.py [words.json]
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(PROJ, '..', '..'))
WORDS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, 'kinema', 'skills', 'reel-studio', 'engine', 'public', 'projects', 'posledniy-chelovek', 'words.json')
words = json.load(open(WORDS, encoding='utf-8'))['words']
LEAD = 0.07          # KINEMA cuts 70 ms before the anchor word
FPS = 60
TAIL = 1.8           # spec tail after the last word


def norm(t):
    return re.sub(r'[^0-9a-zа-я]+', '', t.lower().replace('ё', 'е'))


TOK = [norm(w['text']) for w in words]


def find(phrase, nth=1):
    parts = [norm(p) for p in phrase.split()]
    hits = 0
    for i in range(len(TOK)):
        if all(i + k < len(TOK) and TOK[i + k] == parts[k] for k in range(len(parts))):
            hits += 1
            if hits == nth:
                return i
    raise SystemExit(f'anchor not found: {phrase}#{nth}')


def at(phrase, nth=1):
    return words[find(phrase, nth)]['start']


END = words[-1]['end'] + TAIL

# (id, set, variant, anchor, kind, still time as a fraction of the shot)
PLAN = [
    ('wake', 'pcity', 'wake', 0.0, 'still'),
    ('count', 'pearth', 'count', '@Исчезли', 'clip'),
    ('you', 'pcity', 'you', '@И это', 'still'),
    ('cafe', 'prooms', 'cafe', '@В кафе', 'still'),
    ('mom', None, None, '@Пишешь', 'reuse'),            # cafe still, blurred, under the phone
    ('blackout', 'pcity', 'blackout', '@Через', 'clip'),
    ('station', 'prooms', 'station', '@Станциям', 'still'),
    ('shops', 'prooms', 'shops', '@Зато', 'still'),
    ('bread', 'prooms', 'bread', '@Хлеб', 'still'),
    ('cans', 'prooms', 'cans', '@А консервы', 'still'),
    ('car', 'pcity', 'car', '@Любая', 'still'),
    ('fuel', 'pcity', 'fuel', '@Но бензин', 'still'),
    ('night', 'pcity', 'night', '@Ночью', 'clip'),
    ('third', 'pcity', 'third', '@Раньше', 'still'),
    ('wolves', 'pcity', 'wolves', '@Через год', 'clip'),
    ('chernobyl', 'pcity', 'chernobyl', '@В зоне', 'still'),
    ('last', 'pearth', 'last', '@Ты последний', 'still'),
    ('room', 'prooms', 'room', '@Сидишь', 'still'),
    ('knock', 'prooms', 'knock', '@И вдруг', 'still'),
    ('cta', 'prooms', 'cta', '@Кстати', 'still'),
]


def start_of(a):
    if isinstance(a, (int, float)):
        return float(a)
    ph, _, n = a[1:].partition('#')
    return max(0.0, at(ph, int(n or 1)) - LEAD)


def build():
    starts = [start_of(p[3]) for p in PLAN]
    ends = starts[1:] + [END]
    shots = []
    for (sid, st, var, a, kind), s0, s1 in zip(PLAN, starts, ends):
        rel = lambda phrase, nth=1, d=0.0: round(at(phrase, nth) - s0 + d, 3)
        ev = {}
        if sid == 'count':
            ev = {'out': rel('8', d=0.1), 'done': rel('один', d=0.1)}
        elif sid == 'blackout':
            ev = {'out': rel('гаснет', d=0.25)}
        elif sid == 'night':
            ev = {'tilt': rel('Млечный', d=-0.35)}
        d = {'id': sid, 'set': st, 'variant': var, 'kind': kind, 'dur': round(s1 - s0 + 0.25, 3), 'start': round(s0, 3),
             'anchor': a, 'events': ev}
        shots.append(d)
    return shots


if __name__ == '__main__':
    shots = build()
    out = os.path.join(PROJ, 'blender', 'shots.json')
    json.dump({'fps': FPS, 'shots': [s for s in shots if s['set']]}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for s in shots:
        print(f"{s['id']:10s} {s['kind']:5s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
    print('END', round(END, 2))
