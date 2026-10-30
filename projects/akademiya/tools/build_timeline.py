"""words.json of an episode -> blender/shots.json for «Академия героев» (akademiya).

Full mode: every scene is an animated Blender clip (set 'akad', module akad_e<ep>, variant = scene), cut 70 ms before
its anchor word. Events are times inside the shot (seconds) taken from the words, so actions land on the voice.
    python3 tools/build_timeline.py [KINEMA engine/public/projects dir] [episode]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(PROJ, '..'))
PUB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'KINEMA', 'skills', 'reel-studio', 'engine', 'public', 'projects')
EP = sys.argv[2] if len(sys.argv) > 2 else '3'
LEAD = 0.07
FPS = 30
TAIL = {'3': 2.6}            # the ending stays on screen a bit (calm «скоро в профиле»)

# (id, variant, anchor) ; anchor '@word(s)[#n]' or 0.0
PLAN = {
    '3': [
        ('c00', 'board', 0.0),                 # hook: «я получил ноль»
        ('c00b', 'first', '@И меня'),          # flash-forward: «и меня взяли первым»
        ('c01', 'letter', '@После урагана'),
        ('c02', 'gate', '@Академию открыли'),
        ('c03', 'opened', '@для тех'),
        ('c04', 'saul', '@Директор'),
        ('c05', 'nospeak', '@С ним'),
        ('c06', 'arena', '@Экзамен'),
        ('c07', 'bus', '@Си-Джей'),
        ('c08', 'tons', '@А это'),
        ('c09', 'cesar', '@Сезар'),
        ('c10', 'denise', '@Дениз'),
        ('c11', 'askyou', '@А меня'),
        ('c12', 'laugh', '@Я показал'),
        ('c12b', 'zero', '@На табло'),
        ('c12c', 'laugh2', '@Все смеялись'),
        ('c13', 'golem', '@И тут'),
        ('c14', 'stands', '@Он пошёл'),
        ('c15', 'toward', '@Я пошёл'),
        ('c16', 'crumble', '@И голем'),
        ('c17', 'emmet', '@На трибуне'),
        ('c18', 'secret', '@Сорок лет'),
        ('c19', 'mine', '@А тут'),
        ('c19b', 'why', '@Почему'),
        ('c19c', 'rule', '@Правило'),
        ('c20', 'evening', '@Вечером'),
        ('c21', 'burn', '@Моя сила'),
        ('c21b', 'calm', '@А рядом'),
        ('c22', 'rest', '@Следующая'),
    ],
}

# events: shot id -> {name: (phrase, nth, delta)} ; time = start of the phrase - shot start + delta
EVENTS = {
    'c00': {'zero': ('ноль', 1, 0.0)},
    'c01': {'catch': ('письмо', 1, -0.25)},
    'c05': {'up': ('С ним', 1, 0.0)},
    'c07': {'lift': ('поднял', 1, -0.1)},
    'c09': {'go': ('пробежал', 1, 0.0)},
    'c10': {'stop': ('остановила', 1, 0.0)},
    'c12': {'shrug': ('ничего', 1, -0.15)},
    'c12b': {'zero': ('ноль', 2, 0.0)},
    'c13': {'rise': ('контроля', 1, 0.0)},
    'c16': {'hit': ('рассыпался', 1, -0.1)},
    'c17': {'up': ('встал', 1, -0.1)},
    'c18': {'go': ('учеников', 1, -0.3)},
    'c19': {'point': ('Этот', 1, -0.1)},
    'c19b': {'ask': ('Почему', 1, -0.05)},
    'c19c': {'rule': ('Правило', 1, 0.0)},
    'c20': {'cough': ('закашлялся', 1, 0.0)},
}


def norm(t):
    return re.sub(r'[^0-9a-zа-я]+', '', t.lower().replace('ё', 'е'))


def build(ep):
    words = json.load(open(os.path.join(PUB, f'akademiya-{ep}', 'words.json'), encoding='utf-8'))['words']
    words = [w for w in words if norm(w['text'])]            # caption-only marks ('/', '»') are not words
    tok = [norm(w['text']) for w in words]

    def find(phrase, nth=1):
        parts = [norm(p) for p in phrase.split()]
        hits = 0
        for i in range(len(tok)):
            if all(i + k < len(tok) and tok[i + k] == parts[k] for k in range(len(parts))):
                hits += 1
                if hits == nth:
                    return i
        raise SystemExit(f'anchor not found: {phrase}#{nth} (episode {ep})')

    def at(phrase, nth=1):
        return words[find(phrase, nth)]['start']

    def start_of(a):
        if isinstance(a, (int, float)):
            return float(a)
        ph, _, n = a[1:].partition('#')
        return max(0.0, at(ph, int(n or 1)) - LEAD)

    plan = PLAN[ep]
    end = words[-1]['end'] + TAIL[ep]
    starts = [start_of(p[2]) for p in plan]
    ends = starts[1:] + [end]
    shots = []
    for (sid, var, a), s0, s1 in zip(plan, starts, ends):
        ev = {k: round(at(ph, n) - s0 + d, 3) for k, (ph, n, d) in EVENTS.get(sid, {}).items()}
        shots.append({'id': sid, 'set': 'akad', 'variant': var, 'kind': 'clip', 'part': ep,
                      'dur': round(s1 - s0 + 0.25, 3), 'start': round(s0, 3), 'anchor': a, 'events': ev})
    return shots, end


if __name__ == '__main__':
    out = os.path.join(PROJ, 'blender', 'shots.json')
    old = {}
    if os.path.exists(out):
        old = {s['id']: s for s in json.load(open(out, encoding='utf-8'))['shots']}
    shots, end = build(EP)
    for s in shots:   # hand-set fields (camera, place, samples) survive a rebuild
        for k, v in old.get(s['id'], {}).items():
            if k not in s:
                s[k] = v
    json.dump({'fps': FPS, 'ends': {EP: round(end, 3)}, 'shots': shots}, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1)
    for s in shots:
        print(f"{s['id']:5s} {s['variant']:9s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
    print('END', round(end, 3), 'total frames', sum(round(s['dur'] * FPS) for s in shots))
