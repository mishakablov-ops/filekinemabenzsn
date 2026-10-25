"""words.json (voice timings) -> blender/shots.json (shot durations + animation events).

Run in the VM:  python3 build_timeline.py
"""
import json, os, re, sys
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RS = os.path.abspath(os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio'))
PID = os.environ.get('KOSMOS_PID', 'kosmos-dlya-vseh')   # v2: KOSMOS_PID=kosmos-dlya-vseh-v2
RP = os.path.join(RS, 'engine', 'public', 'projects', PID)
W = json.load(open(os.path.join(RP, 'words.json'), encoding='utf-8'))
words = W['words']
LEAD = 0.07   # Reel Studio cuts 70 ms before the anchor word
FPS = 60

def norm(t):
    return re.sub(r'[^0-9a-zа-я%$ ]+', '', t.lower().replace('ё', 'е')).strip()

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

TAIL = 2.2
END = words[-1]['end'] + TAIL

# (id, set, variant, start anchor, extra) -- anchors must match build_spec.py
PLAN = [
    ('sh01_hook', 'orbit', 'hook', 0.0, {}),
    ('sh02_pad', 'spaceport', 'pad', '@Пока', {}),
    ('sh03_ascent', 'spaceport', 'ascent', '@Хотя', {}),
    ('sh04_sunrise', 'orbit', 'sunrise', '@На орбите', {}),
    ('sh05_moon', 'moon', None, '@До Луны', {}),
    ('sh06_mars', 'mars', None, '@До Марса', {'render': {'vol_end': 2500.0}}),
    ('sh07a_eva', 'orbit', 'eva', '@Почти все', {}),
    ('sh07b_earth', 'planet', 'earth', '@Границ', {}),
    ('sh08a_debris', 'planet', 'debris', '@Но вокруг', {}),
    ('sh08b_jam', 'orbit', 'jam', '@Если полетят#2', {}),
    ('sh09a_dream', 'orbit', 'dream', '@Космос для', {}),
    ('sh09b_dump', 'orbit', 'dump', '@Главное', {}),
    ('sh10_final', 'planet', 'final', '@Кстати', {}),
]

def start_of(a):
    if isinstance(a, (int, float)):
        return float(a)
    ph, _, n = a[1:].partition('#')
    return max(0.0, at(ph, int(n or 1)) - LEAD)

if __name__ == '__main__':
    starts = [start_of(p[3]) for p in PLAN]
    ends = starts[1:] + [END]
    shots = []
    for (sid, st, var, a, extra), s0, s1 in zip(PLAN, starts, ends):
        dur = round(s1 - s0 + 0.25, 3)          # small safety tail
        rel = lambda phrase, nth=1, d=0.0: round(at(phrase, nth) - s0 + d, 3)
        ev = {}
        if sid == 'sh04_sunrise':
            ev = {'rise': rel('16', d=-0.1)}
        elif sid == 'sh06_mars':
            ev = {'pulse': rel('сообщение', d=-0.1)}
        d = {'id': sid, 'set': st, 'dur': dur, 'events': ev, 'start': round(s0, 3)}
        if var:
            d['variant'] = var
        d.update(extra)
        shots.append(d)
    json.dump({'fps': FPS, 'shots': shots}, open(os.environ.get('KOSMOS_SHOTS', os.path.join(PROJ, 'blender', 'shots.json')), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for s in shots:
        print(f"{s['id']:14s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
    print('END', round(END, 2), 'frames', int(END * FPS))
