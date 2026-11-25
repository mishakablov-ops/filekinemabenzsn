"""Постобработка v5 заранее (неон, мультик, полутон, аниме) — пока рендерятся 3D-стили."""
import os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble_v5 as A
jobs = []
for i, (name, f0, cnt, kind, step) in enumerate(A.SEGS):
    if kind in ('neon', 'ink', 'halftone', 'anime'):
        for f in range(f0, f0 + cnt + A.T):
            jobs.append((kind, f, f - f0))
# сначала по кадру каждого стиля — для проверки
first = [j for j in jobs if j[1] in (40, 165, 225, 470)]
rest = [j for j in jobs if j not in first]
with ThreadPoolExecutor(int(os.environ.get('JOBS', 2))) as ex:
    for _ in ex.map(lambda j: A.post(*j), first): pass
    print('first ok', flush=True)
    for _ in ex.map(lambda j: A.post(*j), rest): pass
print('POST_DONE', len(jobs), flush=True)
