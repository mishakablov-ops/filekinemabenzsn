"""words.json (voice timings) -> blender/shots.json (shot durations + animation events) and the Reel Studio spec.json.

Run in the VM:  python3 build_timeline.py
"""
import json, os, re, sys
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RS = os.path.abspath(os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio'))
PID = 'mir-bez-granic'
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
    # fallback: prefix match on the first token
    for i, t in enumerate(TOK):
        if t.startswith(parts[0][:5]):
            return i
    raise SystemExit(f'anchor not found: {phrase}')

def at(phrase, nth=1, end=False):
    i = find(phrase, nth)
    if end:
        i += len(phrase.split()) - 1
        return words[i]['end']
    return words[i]['start']

total = W.get('duration') or words[-1]['end']
TAIL = 2.2
END = words[-1]['end'] + TAIL

# (id, set, variant, start anchor, extra)
plan = [
    ('sh01_globe_hook', 'globe', 'hook', 0.0, {}),
    ('sh03_wall', 'wall', None, '@И больше', {}),
    ('sh04_gate_lift', 'checkpoint', 'lift', '@Первыми', {}),
    ('sh05_passport', 'passport', None, '@Паспорт', {}),
    ('sh06_crowd', 'checkpoint', 'crowd', '@Потом', {'people': 70}),
    ('sh07_globe_arcs', 'globe', 'arcs', '@Это почти', {}),
    ('sh08_city_grow', 'city', 'grow', '@По оценкам', {'render': {'vol_end': 900.0}}),
    ('sh09a_city_crush', 'city', 'crush', '@Но сначала', {'people': 170}),
    ('sh09b_village', 'village', None, '@и пустые', {}),
    ('sh10_army', 'military', 'march', '@Армии', {}),
    ('sh11_state', 'tabletop', None, '@Но кто', {}),
    ('sh12_globe_redraw', 'globe', 'redraw', '@Скорее', {}),
    ('sh12b_oil', 'pumpjack', None, '@рекам', {}),
    ('sh12c_battle', 'military', 'battle', '@И за', {}),
    ('sh13_final', 'checkpoint', 'final', '@Границы', {}),
]

def start_of(a):
    if isinstance(a, (int, float)):
        return float(a)
    return max(0.0, at(a[1:]) - LEAD)

starts = [start_of(p[3]) for p in plan]
ends = starts[1:] + [END]
shots = []
for (sid, st, var, a, extra), s0, s1 in zip(plan, starts, ends):
    dur = round(s1 - s0 + 0.25, 3)          # small safety tail
    rel = lambda phrase, nth=1, d=0.0: round(at(phrase, nth) - s0 + d, 3)
    ev = {}
    if sid == 'sh01_globe_hook':
        ev = {'dissolve': rel('исчезли', d=0.1), 'redraw': rel('Сто', d=-0.05), 'redraw_end': rel('карте', d=0.3)}
    elif sid == 'sh04_gate_lift':
        ev = {'lift': rel('поднимаются', d=-0.1)}
    elif sid == 'sh05_passport':
        ev = {'close': rel('не', d=-0.15), 'slide': rel('как'), 'schengen': rel('Шенгена', d=-0.25)}
    elif sid == 'sh07_globe_arcs':
        ev = {'start': 0.1}
    elif sid == 'sh08_city_grow':
        ev = {'grow': 0.2}
    elif sid == 'sh11_state':
        ev = {'roads': rel('починит', d=-0.15), 'judge': rel('рассудит', d=-0.35), 'gavel': rel('спор', d=-0.05)}
    elif sid == 'sh12_globe_redraw':
        ev = {'start': rel('нарисуют', d=-0.1), 'span': max(1.0, dur - 1.6)}
    elif sid == 'sh12c_battle':
        ev = {'blasts': [0.35, rel('линию', d=0.0), rel('воевать', d=0.05)]}
    d = {'id': sid, 'set': st, 'dur': dur, 'events': ev, 'start': round(s0, 3)}
    if var:
        d['variant'] = var
    d.update(extra)
    shots.append(d)
json.dump({'fps': FPS, 'shots': shots}, open(os.path.join(PROJ, 'blender', 'shots.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for s in shots:
    print(f"{s['id']:20s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
print('END', round(END, 2), 'frames', int(END * FPS))
