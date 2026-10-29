"""Download the CC0 Poly Haven textures and sky used by «Баронесса» v2 (mike 29.10: «качественные ресурсы, не пластик»,
approved the download). 2k JPG maps (diffuse, normal GL, roughness) and one 2k HDRI into baronessa/assets_ph/<id>/.
    python -I tools/get_polyhaven.py
"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets_ph')
TEX = ['brown_mud_leaves_01', 'cobblestone_floor_001', 'brick_4', 'wood_table_worn', 'marble_01', 'aerial_grass_rock',
       'brown_leather', 'painted_plaster_wall']
HDRI = ['belfast_sunset_puresky']
UA = {'User-Agent': 'aipollon-reel/1.0'}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def main():
    for t in TEX:
        d = os.path.join(OUT, t)
        os.makedirs(d, exist_ok=True)
        files = json.loads(get(f'https://api.polyhaven.com/files/{t}'))
        for key, short in (('Diffuse', 'diff'), ('nor_gl', 'nor'), ('Rough', 'rough')):
            if key not in files:
                continue
            url = files[key]['2k']['jpg']['url']
            dst = os.path.join(d, f'{short}.jpg')
            if not os.path.exists(dst):
                open(dst, 'wb').write(get(url))
            print('ok', t, short, os.path.getsize(dst) // 1024, 'KB', flush=True)
    for h in HDRI:
        d = os.path.join(OUT, h)
        os.makedirs(d, exist_ok=True)
        files = json.loads(get(f'https://api.polyhaven.com/files/{h}'))
        url = files['hdri']['2k']['hdr']['url']
        dst = os.path.join(d, 'sky.hdr')
        if not os.path.exists(dst):
            open(dst, 'wb').write(get(url))
        print('ok', h, os.path.getsize(dst) // 1024, 'KB', flush=True)


if __name__ == '__main__':
    main()
