"""Shot lengths and in-shot events of «Канал без лица» from the voice word timings.

    python build_timeline.py WORDS_JSON [SHOTS_JSON]       (SHOTS_JSON default: ../blender/shots.json)

Each 3D clip starts where KINEMA starts playing it: the scene cuts 0.07 s before its anchor word (the same anchors as
engine/storyboard.py) and its video begins half a transition earlier, so the clip starts LEAD = 0.07 + tin/2 before the
word and lasts until the next anchor plus 0.5 s for the transition; k09 also carries the like/sub card (voice end +
TAIL). Events (notification pings, typing, check marks, the thumb) land on their words, in seconds from the clip start,
so picture and voice stay in sync. Pure Python, runs anywhere.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAIL = 3.2                     # the like/sub card after the last word (storyboard.py uses the same)
OVER = 0.5                     # clip runs past the next cut (transition overlap)

# shot -> anchor phrase (display text, like the storyboard "@..." anchors); None = 0 s
ANCHORS = [("k01", None), ("k1b", "В ТикТоке"), ("k02", "А где просмотры"), ("k03", "баннеры"), ("k04", "Но реклама"),
           ("k05", "С KINEMA"), ("k5c", "Плюсы"), ("k5s", "Одно действие"), ("k06", "а скоро"), ("k07", "Один вечер"),
           ("k08", "Не шаришь"), ("k09", "Кто напишет")]
# the scene transition into each shot (storyboard.py uses the same) and KINEMA's transition lengths (transitions/index.tsx)
TRANS = {"k01": "cut", "k1b": "whip", "k02": "push", "k03": "zoom", "k04": "dip", "k05": "blur", "k5c": "push",
         "k5s": "zoom", "k06": "whip", "k07": "dip", "k08": "whip", "k09": "zoom"}
TIN = {"cut": 0.0, "fade": 0.4, "blur": 0.5, "zoom": 0.55, "push": 0.5, "whip": 0.3, "dip": 0.6}
PICTURE_LEAD = 0.07            # KINEMA cuts this much before the anchor word (core/plan.ts)


def lead(sid):
    return 0.0 if sid == "k01" else PICTURE_LEAD + TIN[TRANS[sid]] / 2


def norm(s):
    s = s.lower().replace("ё", "е")
    s = re.sub(r"[«»\"“”„'’`.,!?…:;()\[\]{}*_=~^|/\\—–-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class Words:
    def __init__(self, path):
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        self.words = d["words"]
        self.toks = [norm(w["text"]) for w in self.words]
        self.dur = float(d.get("duration") or self.words[-1]["end"])

    def find(self, phrase, after=0.0, occ=1):
        want = norm(phrase).split()
        seen = 0
        for i, w in enumerate(self.words):
            if w["start"] < after - 0.05:
                continue
            pieces = " ".join(self.toks[i:i + len(want) + 2]).split()
            if pieces[:len(want) - 1] == want[:-1] and len(pieces) >= len(want) and pieces[len(want) - 1].startswith(want[-1]):
                seen += 1
                if seen == occ:
                    k = i
                    got = 0
                    while got < len(want):           # last word of the phrase (a display token may hold 2 words)
                        got += len(self.toks[k].split())
                        k += 1
                    return w["start"], self.words[k - 1]["end"]
        raise SystemExit(f"anchor not found: {phrase!r} after {after:.2f}s")


def main(words_path, shots_path):
    W = Words(words_path)
    starts = []
    for sid, ph in ANCHORS:
        starts.append(0.0 if ph is None else W.find(ph, starts[-1] if starts else 0.0)[0])
    end = W.dur + TAIL
    S = json.loads(Path(shots_path).read_text(encoding="utf-8"))
    by = {s["id"]: s for s in S["shots"]}
    ev = {}
    t = lambda ph, a, edge=0: W.find(ph, a)[edge]               # noqa: E731
    a = {sid: st - lead(sid) for (sid, _), st in zip(ANCHORS, starts)}          # clip zero, seconds
    ev["k02"] = {"ping": t("реклама", a["k02"]) - a["k02"]}
    ev["k03"] = {"n1": 0.1, "n2": t("интеграции", a["k03"]) - a["k03"], "n3": t("партнёрки", a["k03"]) - a["k03"]}
    tt = t("фразу", a["k05"], 1) - a["k05"]
    ev["k05"] = {"typed": tt, **{f"s{k}": t(ph, a["k05"]) - a["k05"] + 0.25
                                 for k, ph in enumerate(["сценарий", "голос", "3D-сцены", "субтитры"])}}
    ev["k5c"] = {f"p{k}": t(ph, a["k5c"]) - a["k5c"] for k, ph in enumerate(["камеры", "монтажёра", "выделяется"])}
    ev["k08"] = {"thumb": t("за тебя", a["k08"]) - a["k08"] - 0.3}
    ev["k09"] = {"typed": t("канал", a["k09"], 1) - a["k09"]}
    for i, (sid, _) in enumerate(ANCHORS):
        nxt = starts[i + 1] + OVER if i + 1 < len(ANCHORS) else end + 0.3
        s = by[sid]
        s["start"] = round(a[sid], 3)
        s["dur"] = round(nxt - a[sid], 2)
        s["events"] = {k: round(v, 3) for k, v in ev.get(sid, {}).items()}
    S["ends"] = {"1": round(end, 2)}
    Path(shots_path).write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding="utf-8")
    for s in S["shots"]:
        print(f"{s['id']} start {s['start']:6.2f}  dur {s['dur']:5.2f}  {s['events']}")
    print(f"voice {W.dur:.2f} s, video {end:.2f} s, frames at 30 fps: {sum(round(s['dur'] * 30) for s in S['shots'])}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(HERE.parent / "blender" / "shots.json"))
