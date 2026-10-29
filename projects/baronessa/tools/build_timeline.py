"""words.json -> blender/shots.json for «Баронесса-пулемётчица» (full mode: every scene is an animated Blender clip,
set 'bar_sets', variant = scene type), cut 70 ms before the anchor word; events are times inside the shot.
    python -I tools/build_timeline.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
PUB = os.path.join(PROJ, '..', 'KINEMA', 'skills', 'reel-studio', 'engine', 'public', 'projects', 'baronessa')
LEAD = 0.07
FPS = 30
TAIL = 2.4

PLAN = [
    ('c01', 'album', 0.0), ('c02', 'studio', '@А теперь'),
    ('c03', 'street1918', '@1918'), ('c04', 'crib', '@Её первое слово'), ('c05', 'dustbag', '@Её первое слово#2'),
    ('c06', 'zipper', '@В 5'), ('c07', 'queue', '@В 10'),
    ('c08', 'crate', '@Взрослой'), ('c09', 'gun', '@Пулемёт'), ('c10', 'tags', '@600'), ('c11', 'sale', '@Ни одной'),
    ('c12', 'castle', '@Первым'), ('c13', 'gates', '@Баронесса не'), ('c14', 'check', '@А чек'),
    ('c15', 'surrender', '@Графство сдалось'),
    ('c16', 'fortress', '@Потом'), ('c17', 'calendar', '@40'), ('c18', 'balloon', '@Скидку в'), ('c19', 'wall', '@Мы не'),
    ('c20', 'list', '@Только лист'),
    ('c21', 'salecity', '@А в год'), ('c22', 'enter', '@она взяла'), ('c23', 'keys', '@Город'),
    ('c24', 'hall', '@Над ратушей'), ('c25', 'flag', '@Оранжевый'),
    ('c26', 'capital', '@Так родилась'), ('c27', 'palace', '@Столица'), ('c28', 'shrine', '@Святыня'),
    ('c29', 'motto', '@Девиз'), ('c30', 'passport', '@У каждого'), ('c31', 'passbag', '@А у каждого'),
    ('c32', 'swamp', '@Говорят'), ('c33', 'fitting', '@Зашла'), ('c34', 'promise', '@Я вернусь'),
    # 28.10 mike: «в конце убери правду, оставь про лайк и шапку профиля» (album_gone/monitor/comments are out)
    ('c38', 'cta', '@Если'), ('c39', 'approve', '@Баронесса одобряет'),
]

EVENTS = {
    'c02': {'flash': ('настоящей', 1, -0.1)},
    'c05': {'word': ('пыльник', 1, 0.0)},
    'c06': {'zip': ('По звуку', 1, 0.0)},
    'c08': {'open': ('оружие', 1, -0.3)},
    'c09': {'fire': ('стреляет', 1, 0.0)},
    'c15': {'give': ('сдалось', 1, -0.1)},
    'c20': {'unroll': ('лист', 1, 0.0)},
    'c23': {'keys': ('ключи', 1, 0.0), 'cash': ('кассы', 1, 0.0), 'bags': ('пыльники', 1, 0.0)},
    'c24': {'raise': ('флаг', 1, -0.4)},
    'c28': {'reveal': ('сумка', 1, -0.2)},
    'c29': {'motto': ('Береги', 1, -0.1)},
    'c31': {'in': ('свой', 1, -0.3)},
    'c33': {'in': ('примерочную', 1, -0.2), 'out': ('вышла', 1, -0.3)},
    'c39': {'nod': ('одобряет', 1, 0.0)},
}


def norm(t):
    return re.sub(r'[^0-9a-zа-я]+', '', t.lower().replace('ё', 'е'))


def main():
    words = json.load(open(os.path.join(PUB, 'words.json'), encoding='utf-8'))['words']
    tok = [norm(w['text']) for w in words]

    def find(phrase, nth=1):
        parts = [norm(p) for p in phrase.split()]
        hits = 0
        for i in range(len(tok)):
            if all(i + k < len(tok) and tok[i + k] == parts[k] for k in range(len(parts))):
                hits += 1
                if hits == nth:
                    return i
        raise SystemExit(f'anchor not found: {phrase}#{nth}  tokens: {" ".join(tok)}')

    def at(phrase, nth=1):
        return words[find(phrase, nth)]['start']

    def start_of(a):
        if isinstance(a, (int, float)):
            return float(a)
        ph, _, n = a[1:].partition('#')
        return max(0.0, at(ph, int(n or 1)) - LEAD)

    end = words[-1]['end'] + TAIL
    starts = [start_of(p[2]) for p in PLAN]
    ends = starts[1:] + [end]
    out = os.path.join(PROJ, 'blender', 'shots.json')
    old = {}
    if os.path.exists(out):
        old = {s['id']: s for s in json.load(open(out, encoding='utf-8'))['shots']}
    shots = []
    for (sid, var, a), s0, s1 in zip(PLAN, starts, ends):
        evs = {k: round(at(ph, n) - s0 + d, 3) for k, (ph, n, d) in EVENTS.get(sid, {}).items()}
        s = {'id': sid, 'set': 'bar_sets', 'variant': var, 'kind': 'clip', 'dur': round(s1 - s0 + 0.25, 3),
             'start': round(s0, 3), 'anchor': a, 'events': evs}
        for k, v in old.get(sid, {}).items():
            if k not in s:
                s[k] = v
        shots.append(s)
    json.dump({'fps': FPS, 'end': round(end, 3), 'shots': shots}, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1)
    for s in shots:
        print(f"{s['id']} {s['variant']:11s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
    print('END', round(end, 2), 'frames', sum(round(s['dur'] * FPS) for s in shots))


if __name__ == '__main__':
    main()
