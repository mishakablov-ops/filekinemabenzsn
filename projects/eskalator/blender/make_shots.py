"""words.json (KINEMA tts.py) -> shots.json: где начинается каждый план и сколько кадров рендерить.
python make_shots.py words.json shots.json
План режется за 0.12 с до первого слова своей фразы; рендер берёт +0.35 с запаса под переход-смаз."""
import json, sys

CUES = [  # план -> номер карточки (фразы) в words.json, с которой он начинается
    ('S01', 0), ('S02', 1), ('S03', 2), ('S04', 3), ('S05', 4), ('S06', 6), ('S07', 7), ('S08', 8),
    ('S09', 9), ('S10', 11), ('S11', 13), ('S12', 14), ('S13', 15), ('S14', 16), ('S15', 17), ('S16', 18),
    ('S17', 20), ('S18', 22), ('S19', 23), ('S20', 24), ('S20B', 25), ('S21', 26),
]
LEAD, HANDLE, TAIL = 0.12, 0.35, 0.7

w = json.load(open(sys.argv[1], encoding='utf-8'))
cards, words = w['cards'], w['words']
starts = [0.0 if k == 0 else max(0.0, cards[c]['start'] - LEAD) for k, (_, c) in enumerate(CUES)]
end_all = w['duration'] + TAIL
shots = []
for k, (sid, c) in enumerate(CUES):
    st = starts[k]
    en = starts[k + 1] if k + 1 < len(CUES) else end_all
    c_end = CUES[k + 1][1] if k + 1 < len(CUES) else len(cards)
    text = ' '.join(words[i]['text'] for cc in range(c, c_end) for i in cards[cc]['words'])
    shots.append(dict(id=sid, start=round(st, 3), end=round(en, 3), dur=round(en - st + HANDLE, 3), text=text))
json.dump(dict(fps=30, duration=round(end_all, 3), shots=shots), open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for s in shots:
    print(f"{s['id']:5s} {s['start']:6.2f}-{s['end']:6.2f} ({s['dur']:.2f}s)  {s['text']}")
print('frames', sum(int(round(s['dur'] * 30)) for s in shots))
