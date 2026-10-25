"""Reel Studio spec.json for '__PROJECT__': Blender clips as full-frame VideoBG, captions, CTA end card."""
import json, os
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RS = os.path.abspath(os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio'))
RP = os.path.join(RS, 'engine', 'public', 'projects', '__PROJECT__')
B = 'projects/__PROJECT__'
anchors = {'sh01_globe_hook': 0, 'sh03_wall': '@И больше', 'sh04_gate_lift': '@Первыми', 'sh05_passport': '@Паспорт',
           'sh06_crowd': '@Потом', 'sh07_globe_arcs': '@Это почти', 'sh08_city_grow': '@По оценкам', 'sh09a_city_crush': '@Но сначала',
           'sh09b_village': '@и пустые', 'sh10_army': '@Армии', 'sh11_state': '@Но кто', 'sh12_globe_redraw': '@Скорее',
           'sh12b_oil': '@языкам', 'sh12c_battle': '@И за', 'sh13_final': '@Границы#3'}
shots = json.load(open(os.path.join(PROJ, 'blender', 'shots.json'), encoding='utf-8'))['shots']
k = lambda t, pos, target, fov=30, ease='inOut': {'t': t, 'pos': pos, 'target': target, 'fov': fov, 'ease': ease}
scenes = []
for s in shots:
    sc = {'id': s['id'], 'at': anchors[s['id']], 'transition': 'cut', 'camera': 'still',
          'bg': {'block': 'VideoBG', 'props': {'src': f"{B}/clips/{s['id']}.mp4", 'zoom': [1.0, 1.0]}}}
    if s['id'] == 'sh13_final':
        sc['bg'].update({'dim': 0.6, 'dimAt': '@Кстати'})
        sc['layers'] = [{'block': 'IPhone17', 'pos': 'full', 'enter': 'none', 'sfx': False, 'at': '@Кстати+0.3', 'props': {
            'enter': 'flip', 'flipAt': 0.25, 'flipDur': 0.65, 'float': True, 'shadow': 0,
            'screen': {'block': 'TikTokProfile', 'props': {
                'dark': True, 'name': 'aipollon', 'handle': 'videopollon', 'badge': 'Verified business',
                'bio': 'Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻',
                'link': 'https://t.me/aipollonvideo', 'avatar': 'brand/aipollon-avatar.png',
                'tiles': [f'{B}/cover.jpg', 'brand/tiles/quiet-evenings.jpg'] + [''] * 7, 'pinned': 1,
                'highlightAt': '@шапку'}},
            'cam': [k(0, [0, 2.1, 10.8], [0, 2.05, 0]), k(4.5, [0.08, 2.23, 8.9], [0, 2.23, 0])]}}]
        sc['captions'] = {'mode': 'editorial', 'pos': 'top', 'scrim': 0.85}
    scenes.append(sc)
spec = {
    'id': '__PROJECT__', 'mode': 'explainer', 'style': 'dusk', 'fps': 60,
    'voice': {'src': f'{B}/voice.wav', 'words': f'{B}/words.json', 'volume': 1},
    'music': {'src': f'{B}/soundtrack.wav', 'volume': 1.0, 'duck': 1.0, 'offset': 0, 'fadeIn': 0.05, 'fadeOut': 0.9},
    'tail': 2.1, 'autoSfx': False, 'sfx': [],
    'grain': 0.02, 'vignette': 0.14,
    'captions': {'mode': 'editorial', 'pos': 'top', 'uppercase': False, 'scale': 1, 'scrim': 0.8},
    'scenes': scenes,
}
json.dump(spec, open(os.path.join(RP, 'spec.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('spec scenes', len(scenes))
