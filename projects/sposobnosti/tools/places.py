"""Places in «Метрополис» for the city scenes of sposobnosti: one new place per story location (metro_spots), shared by
the shots that happen there (the hero's street in Boro, the park, the evening street, the storm avenue...).
Writes cam / target / lens / preset / place into blender/shots.json and logs the places (spots_used.json).
    python3 tools/places.py [--log]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.abspath(os.path.join(PROJ, '..', '..', 'blender', 'library')))
import metro_spots as MS  # noqa: E402

STORM = {'sun_E': 0.9, 'zen': '#59626C', 'mid': '#7C858D', 'fog': '#7F878E', 'dens': 0.0011, 'fogh': 900.0, 'lit': 0.2,
         'street': 0.6, 'neon': 0.7, 'glow': 0.0, 'exposure': 0.35, 'traffic': 0.3}
# place: (kind, preset, over)
PLACES = {
    'sky_night': ('aerial', 'night', None),
    'morning_ave': ('avenue', 'golden', None),
    'home': ('borough', 'day', None),
    'noon': ('aerial', 'day', {'traffic': 0.0}),
    'towers': ('lookup', 'day', None),
    'jets': ('skyline', 'day', None),
    'park': ('park', 'golden', None),
    'eve': ('street', 'dusk', None),
    'chaos': ('aerial', 'day', {'sun_E': 2.5, 'fog': '#A49A8E', 'dens': 0.0006, 'zen': '#6C7884', 'mid': '#A9A196'}),
    'dark_st': ('street', 'night', None),
    'needle': ('skyline', 'night', None),
    'roof': ('rooftop', 'day', STORM),
    'storm_sky': ('skyline', 'day', STORM),
    'storm_st': ('street', 'day', STORM),
    'storm_ave': ('avenue', 'day', STORM),
    'gold': ('skyline', 'golden', None),
}
SHOT_PLACE = {
    'a01': 'sky_night', 'a03': 'morning_ave', 'a06': 'home', 'a07': 'home', 'a08': 'home', 'a09': 'noon', 'a10': 'towers',
    'a11': 'jets', 'a13': 'park', 'a14': 'park', 'a16': 'eve', 'a17': 'eve', 'a18': 'eve', 'a19': 'eve',
    'b03': 'chaos', 'b05': 'dark_st', 'b06': 'needle', 'b07': 'roof', 'b08': 'storm_sky', 'b09': 'storm_st', 'b10': 'storm_sky',
    'b12': 'storm_ave', 'b13': 'storm_ave', 'b14': 'storm_ave', 'b15': 'storm_ave', 'b16': 'home', 'b17': 'home',
    'b18': 'home', 'b19': 'home', 'b20': 'gold',
}

if __name__ == '__main__':
    path = os.path.join(PROJ, 'blender', 'shots.json')
    data = json.load(open(path, encoding='utf-8'))
    used = MS.load_used()
    got = {}
    for name, (kind, preset, over) in PLACES.items():
        s = MS.make_spot(kind, f'sposobnosti/{name}', preset, used + [dict(cam=o['cam']) for o in got.values()])
        got[name] = s
        print(f"{name:12s} {kind:9s} {preset:7s} cam={s['cam']} target={s['target']} lens={s['lens']}  {s['desc']}")
    for sh in data['shots']:
        pl = SHOT_PLACE.get(sh['id'])
        if not pl:
            continue
        s = got[pl]
        sh.update(place=pl, cam=s['cam'], target=s['target'], lens=s['lens'], preset=s['preset'])
        over = PLACES[pl][2]
        if over:
            sh['over'] = over
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if '--log' in sys.argv:
        MS.log_used(list(got.values()), 'sposobnosti')
        print('logged', len(got))
