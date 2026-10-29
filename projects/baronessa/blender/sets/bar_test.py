"""Pose test: the baroness in several poses side by side in a light studio (variant 'poses'), or one close-up ('face')."""
import math

import lib
import sila_hero as SH
import baroness as B


def build(shot, fps):
    lib.world_color('#d9d2c8', 1.0)
    lib.plane((30, 30), mat_=lib.mat('Floor', '#cfc6b8', rough=0.8))
    v = shot.get('variant', 'poses')
    if v == 'face':
        b = B.load(loc=(0, 0, 0))
        SH.key_pose(b, 0, B.P('strict'))
        SH.key_pose(b, shot['dur'], B.P('strict', head=(-12, -4, 0)))
        cam = lib.camera((0.25, -1.1, 1.52), (0, 0, 1.47), lens=60)
    else:
        names = shot.get('poses', ['stand', 'strict', 'hold_gun', 'point', 'hand_up', 'bag'])
        for i, n in enumerate(names):
            b = B.load(loc=((i - (len(names) - 1) / 2) * 0.9, 0, 0), name=f'B{i}')
            SH.key_pose(b, 0, B.P(n))
        cam = lib.camera((1.2, -3.6 - 0.45 * len(names), 1.1), (0, 0, 0.95), lens=44)
    lib.light('AREA', (2.5, -4, 4), energy=900, size=4, color='#FFF1E0')
    lib.light('AREA', (-3, 3, 3), energy=500, size=3, color='#E8EEFF')
    return dict(fill=0.5, exposure=0.2)
