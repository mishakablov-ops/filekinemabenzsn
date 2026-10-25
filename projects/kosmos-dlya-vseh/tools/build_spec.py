"""Reel Studio spec.json for 'kosmos-dlya-vseh': Blender clips as full-frame VideoBG, editorial captions with the
sunrise-gold accent (style 'orbit'), CTA: the channel's TikTok profile on an iPhone 17 in Cosmic Orange."""
import json, os, sys
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RS = os.path.abspath(os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio'))
PID = os.environ.get('KOSMOS_PID', 'kosmos-dlya-vseh')
RP = os.path.join(RS, 'engine', 'public', 'projects', PID)
B = f'projects/{PID}'
sys.path.insert(0, os.path.dirname(__file__))
from build_timeline import PLAN   # noqa: E402  (same anchors as the shot timing)

anchors = {sid: a for sid, _, _, a, _ in PLAN}
shots = json.load(open(os.environ.get('KOSMOS_SHOTS', os.path.join(PROJ, 'blender', 'shots.json')), encoding='utf-8'))['shots']
k = lambda t, pos, target, fov=30, ease=None: dict({'t': t, 'pos': pos, 'target': target, 'fov': fov}, **({'ease': ease} if ease else {}))
TILES = [f'{B}/cover.jpg', 'brand/tiles/cover-edinyi-yazyk.jpg', 'brand/tiles/cover-coffee-agent.jpg', 'brand/tiles/cover-nuclear.jpg',
         'brand/tiles/fr-gibrid.jpg', 'projects/mir-bez-granic/cover.jpg', 'brand/tiles/quiet-evenings.jpg',
         'brand/tiles/cover-fr-klassika.jpg', 'brand/tiles/fr-test-1.jpg']
scenes = []
for s in shots:
    a = anchors[s['id']]
    sc = {'id': s['id'], 'at': a if a else 0, 'transition': 'cut', 'camera': 'still',
          'bg': {'block': 'VideoBG', 'props': {'src': f"{B}/clips/{s['id']}.mp4", 'zoom': [1.0, 1.0]}}}
    if s['id'] == 'sh10_final':
        sc['bg'].update({'dim': 0.55, 'dimAt': '@Кстати'})
        sc['layers'] = [{'block': 'IPhone17', 'pos': 'full', 'enter': 'none', 'sfx': False, 'props': {
            'enter': 'flip', 'flipAt': '@нейросеть', 'flipDur': 1.2, 'float': True, 'shadow': 0, 'color': '#D9822B',
            'screen': {'block': 'TikTokProfile', 'props': {
                'dark': True, 'name': 'aipollon', 'handle': 'videopollon', 'badge': 'Verified business',
                'bio': 'Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻',
                'link': 'https://t.me/aipollonvideo', 'avatar': 'brand/aipollon-avatar.png',
                'tiles': TILES, 'pinned': 1, 'highlightAt': '@шапке'}},
            'cam': [k(0, [0, 2.3, 10.8], [0, 2.25, 0]), k(1.6, [0.35, 2.32, 10.4], [0, 2.25, 0]),
                    k(2.6, [0, 2.53, 5.4], [0, 2.53, 0], ease='inOut'), k(6, [0, 2.5, 5.1], [0, 2.5, 0])]}}]
        sc['captions'] = {'mode': 'editorial', 'pos': 'top', 'scrim': 0.85}
    scenes.append(sc)
spec = {
    'id': PID, 'mode': 'explainer', 'style': 'orbit', 'fps': 60,
    'voice': {'src': f'{B}/voice.wav', 'words': f'{B}/words.json', 'volume': 1},
    'music': {'src': f'{B}/soundtrack.wav', 'volume': 1.0, 'duck': 1.0, 'offset': 0, 'fadeIn': 0.05, 'fadeOut': 0.9},
    'tail': 2.1, 'autoSfx': False, 'sfx': [],
    'grain': 0.02, 'vignette': 0.14,
    'captions': {'mode': 'editorial', 'pos': 'top', 'uppercase': False, 'scale': 1, 'scrim': 0.8},
    'scenes': scenes,
}
json.dump(spec, open(os.path.join(RP, 'spec.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('spec scenes', len(scenes))
