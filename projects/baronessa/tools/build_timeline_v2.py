"""words.json -> blender/shots.json for «Баронесса-пулемётчица» (full mode: every scene is an animated Blender clip,
set 'bar_sets', variant = scene type), cut 70 ms before the anchor word; events are times inside the shot.
    python -I tools/build_timeline.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
PUB = os.path.join(PROJ, '..', 'KINEMA', 'skills', 'reel-studio', 'engine', 'public', 'projects', 'baronessa-v2')
LEAD = 0.07
FPS = 30
TAIL = 2.4

PLAN = [   # v2 (29.10.2026): humour-action, the army, the war map
    ('d01', 'hook', 0.0), ('d02', 'night_map', '@За одну ночь'), ('d03', 'coupon_rain', '@Без единого'),
    ('d04', 'hq_ext', '@Год сорок'), ('d05', 'hq_map', '@Ставка'), ('d06', 'hq_chek', '@Товарищи'),
    ('d07', 'hq_faint', '@Один генерал'), ('d08', 'army', '@Через сутки'), ('d09', 'identical', '@Все одинаковые'),
    ('d10', 'tank', '@Танки'), ('d11', 'tank_queue', '@Очередь на танк'), ('d12', 'load', '@Пулемёты'),
    ('d13', 'castle', '@Первый удар'), ('d13b', 'strike_map', '@Стрелка'), ('d14', 'heels', '@Медленно'), ('d15', 'fire', '@Огонь'),
    ('d16', 'volley', '@Шесть тысяч'), ('d17', 'wallet', '@У врага'), ('d18', 'chek_gate', '@А чек'),
    ('d19', 'surrender', '@Графство сдаётся'), ('d20', 'siege', '@Крепость Эрмес'), ('d21', 'balloon', '@Враг предлагает'),
    ('d22', 'insult', '@Минус пятьдесят#2'), ('d23', 'boutique', '@На сорок первый'), ('d24', 'assault', '@Эрмесовка'), ('d24b', 'army', '@Баронессы идут'),
    ('d25', 'wall_cap', '@Стена тоже'), ('d26', 'parachutes', '@С неба'), ('d27', 'no_retreat', '@Ни шагу'),
    ('d28', 'city_gives', '@Город сдаёт'), ('d29', 'map_orange', '@К утру'), ('d29b', 'map_all', '@Луивиттония'), ('d30', 'market', '@Кроме рынка'),
    ('d31', 'textbook', '@Запишите'), ('d32', 'parade', '@Так родилась'), ('d33', 'strict1', '@Строгая'),
    ('d34', 'strict2', '@Полная'), ('d35', 'strict3', '@Непобедимая'), ('d36', 'cta', '@Если поржал'),
    ('d37', 'dismiss', '@Свободны'),
]

EVENTS = {
    'd07': {'faint': ('обморок', 1, -0.5)},
    'd19': {'give': ('сдаётся', 1, -0.1)},
    'd28': {'keys': ('ключи', 1, 0.0), 'cash': ('кассы', 1, 0.0), 'bags': ('последний', 1, 0.0),
            'size': ('размер', 1, -0.3)},
}

def norm_line(s):
    s = re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", s)
    s = re.sub(r"[=~\[\]*]|//", " ", s)
    return [w for w in (norm(x) for x in s.split()) if w]


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
    out = os.path.join(PROJ, 'blender', 'shots_v2.json')
    old = {}
    if os.path.exists(out):
        old = {s['id']: s for s in json.load(open(out, encoding='utf-8'))['shots']}
    shots = []
    for (sid, var, a), s0, s1 in zip(PLAN, starts, ends):
        evs = {k: round(at(ph, n) - s0 + d, 3) for k, (ph, n, d) in EVENTS.get(sid, {}).items()}
        s = {'id': sid, 'set': 'bar_v2', 'variant': var, 'kind': 'clip', 'dur': round(s1 - s0 + 0.25, 3),
             'start': round(s0, 3), 'anchor': a, 'events': evs}
        for k, v in old.get(sid, {}).items():
            if k not in s:
                s[k] = v
        shots.append(s)
    json.dump({'fps': FPS, 'end': round(end, 3), 'shots': shots}, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1)
    # mike 29.10: «чтобы у неё рот под реплики открывался» -> the baroness's word intervals inside each shot
    bar_lines = [norm_line(l[2:]) for l in open(os.path.join(PROJ, 'script-v2.md'), encoding='utf-8').read().splitlines()
                 if l.startswith('Б:')]
    spans, i = [], 0
    for line in bar_lines:
        n = len(line)
        while i + n <= len(tok) and tok[i:i + n] != line:
            i += 1
        if i + n <= len(tok):
            spans.append((words[i]['start'], words[i + n - 1]['end']))
            i += n
    for s in shots:
        s0, s1 = s['start'], s['start'] + s['dur']
        m = [[round(max(a, s0) - s0, 3), round(min(b, s1) - s0, 3)] for a, b in spans if b > s0 and a < s1]
        if m:
            s['mouth'] = m
            s['voice_offset'] = s['start']
    json.dump({'fps': FPS, 'end': round(end, 3), 'shots': shots}, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1)
    print('MOUTH', {s['id']: s['mouth'] for s in shots if 'mouth' in s})
    for s in shots:
        print(f"{s['id']} {s['variant']:11s} start={s['start']:6.2f} dur={s['dur']:5.2f} {s['events']}")
    print('END', round(end, 2), 'frames', sum(round(s['dur'] * FPS) for s in shots))


if __name__ == '__main__':
    main()
