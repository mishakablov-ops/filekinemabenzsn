"""Download the NASA Earth maps spacekit.earth() needs (public domain, NASA Visible Earth) into
kosmos-dlya-vseh/blender/tex/nasa on the PC, where pearth.py looks for them:
  earth_day_8k.jpg  Blue Marble NG, July 2004, topography + bathymetry (21600 map scaled to 8192x4096)
  night_8k.jpg      Black Marble 2016, 3 km (scaled to 8192x4096)
  clouds_2048.jpg   Blue Marble clouds, 2048x1024
    blender -b --factory-startup --python get_nasa_tex.py -- <tex/nasa dir>
(runs in Blender: its Python has no Pillow, so the maps are scaled with bpy images.)
"""
import os
import sys
import urllib.request

import bpy

BASE = 'https://eoimages.gsfc.nasa.gov/images/imagerecords/'
FILES = {
    'earth_day_8k.jpg': (['73000/73751/world.topo.bathy.200407.3x21600x10800.jpg',
                          '73000/73751/world.topo.bathy.200407.3x5400x2700.jpg'], 8192),
    'night_8k.jpg': (['144000/144898/BlackMarble_2016_3km.jpg', '144000/144898/BlackMarble_2016_01deg.jpg'], 8192),
    'clouds_2048.jpg': (['57000/57747/cloud_combined_2048.jpg'], None),
}


def fetch(url, path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as r, open(path, 'wb') as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    return os.path.getsize(path)


def main(out):
    os.makedirs(out, exist_ok=True)
    for name, (urls, w) in FILES.items():
        dst = os.path.join(out, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 100000:
            print('have', name, os.path.getsize(dst))
            continue
        tmp = dst[:-4] + '_dl.jpg'
        for u in urls:
            try:
                n = fetch(BASE + u, tmp)
                print('got', u, n)
                break
            except Exception as e:  # noqa: BLE001
                print('fail', u, e)
        else:
            continue
        im = bpy.data.images.load(tmp)
        if w and im.size[0] > w:
            im.scale(w, w // 2)
        im.file_format = 'JPEG'
        im.save(filepath=dst, quality=92)
        print('saved', name, tuple(im.size), os.path.getsize(dst))
        bpy.data.images.remove(im)
        os.remove(tmp)


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1])
