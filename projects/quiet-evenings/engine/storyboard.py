"""Build the 40-second fictional short 'Тихие вечера' from its aligned narration."""
import json
import math
import re
from pathlib import Path

P = Path(__file__).resolve().parent
HERO = {"hero": True}
PI = math.pi


def key(t, pos, target, fov=44):
    return {"t": t, "pos": pos, "target": target, "fov": fov, "ease": "inOut"}


def person(pose, pos, seed=1, rot=0, look=None):
    return {"pose": pose, "pos": pos, "rotY": rot, "seed": seed, "look": look or HERO}


def room(preset, cam, people, lights="evening", screen=None, dim=0):
    props = {"preset": preset, "cam": cam, "people": people, "lights": lights, "build": False}
    if screen:
        props["screen"] = screen
    return {"block": "Room3D", "props": props, "dim": dim}


def layer(block, props, pos="stage", **kw):
    return {"block": block, "props": props, "pos": pos, "enter": "rise", "sfx": False, **kw}


def shot(id, at, bg, layers=None, transition="blur", **kw):
    return {"id": id, "at": at, "bg": bg, "camera": "still", "transition": {"type": transition, "dur": 0.3, "sfx": False}, "layers": layers or [], **kw}


def office(day=False, wide=False, live=True, pose="type", walk=False):
    cam = ([key(0, [9, 7.5, 11], [0, 2.65, -0.4], 34), key(4, [8.1, 6.8, 10], [0, 2.65, -0.4], 34)] if wide else
           [key(0, [4.3, 2.45, 3.4], [0.25, 1.65, -1.35], 46), key(4, [4.0, 2.25, 3.1], [0.25, 1.65, -1.35], 46)])
    hero = person(pose, [0.3, 0, -1.0], rot=PI)
    if walk:
        hero = {**person("phone", [1.8, 0, 0.3], rot=PI), "walkTo": [1.3, 0, -0.4], "walkDur": 0.8}
    return room("office", cam, [hero], "day" if day else "night", screen=CODE if live else None)


FRIENDS = [
    {"type": "person", **person("cheer", [-0.85, 0, -0.2], 4, 0.3, {"shirt": "#768E9B", "hairStyle": "short"})},
    {"type": "person", **person("wave", [0.7, 0, -0.1], 6, -0.4, {"shirt": "#A68393", "hairStyle": "long"})},
    {"type": "person", **person("phone", [0, 0, 1.0], 8, 0.15, {"shirt": "#A4A57B", "hairStyle": "short"})},
]


def party(later=False):
    people = [dict(p) for p in FRIENDS]
    if later:
        for p in people:
            p["pose"] = "phone" if p["seed"] != 4 else "think"
    else:
        people[0].update({"walkTo": [-0.55, 0, -0.8], "walkDur": 1.25})
    return {"block": "Scene3D", "props": {
        "look": "night" if not later else "dusk", "lights": "night" if not later else "soft", "pop": False,
        "cam": [key(0, [3.4, 3.3, 8.0], [0, 2.5, 0], 42), key(4, [2.7, 3.0, 7.4], [0, 2.45, 0], 42)],
        "objects": [
            {"type": "rug", "pos": [0, 0, 0], "w": 5, "d": 5, "color": "#343A43"},
            {"type": "bench", "pos": [-1.2, 0, -1.8]},
            {"type": "tree", "pos": [-2.8, 0, -2.1], "s": 1.3},
            {"type": "tree", "pos": [2.5, 0, -2.2], "s": 1.5},
            {"type": "streetlamp", "pos": [1.9, 0, -1.6], "on": True},
            *people,
        ],
    }}


CODE = {"block": "CodeEditor", "props": {"file": "product.ts", "code": "const idea = await research();\nconst product = await build(idea);\nawait test(product);\nawait ship(product);", "typeFrom": 1,
        "marks": [{"line": 3, "kind": "hl", "at": 0.7}], "w": 1280, "h": 840}}


def mac(screen, cam="hero"):
    return {"block": "MacBook", "props": {"cam": cam, "screen": screen, "enter": "none", "spin": 2}}


def build():
    scenes = [
        shot("the-joke", 0, office(), transition="cut"),
        shot("friday-friends", "@Пятница", party(), transition="push"),
        shot("stays-home", "@Он остаётся", office(wide=True, walk=True, live=False), transition="cut"),
        shot("paid-development", "@Днём", mac(CODE, "toScreen"), transition="zoom"),
        shot("books-and-business", "@Вечером", room("library", [key(0, [2.8, 2.0, 3.5], [0.15, 1.7, -0.7], 48), key(5, [2.3, 1.9, 3], [0.15, 1.7, -0.7], 48)], [person("read", [0.12, 0, -0.68], rot=0.35)]),
             [layer("Chips", {"items": ["Маркетинг", "Продажи", "Экономика"]}, {"x": 80, "y": 700, "w": 900, "h": 150}, at="@Маркетинг")]),
        shot("learning-ai", "@Искусственный", mac({"block": "ClaudeChat", "props": {
            "dark": True, "greeting": "Учиться. Пробовать. Повторять.", "type": "Как проверить спрос на продукт?", "typeAt": 0.1,
            "sendAt": 0.9, "replyAt": 1.2, "reply": "Поговори с будущими клиентами. Собери прототип. Проверь гипотезу.", "cps": 48}}, "hero"), transition="zoom"),
        shot("failure-and-rebuild", "@Первый проект", office(pose="react"), [layer("Terminal", {
            "title": "Попытка за попыткой", "w": 880, "h": 350, "welcome": False, "size": 27, "lines": [
                {"kind": "text", "text": "Первая версия: не сработало", "at": 0.1},
                {"kind": "prompt", "text": "Разобраться и переделать", "at": "@Второй", "cps": 48},
                {"kind": "ok", "text": "Следующая попытка", "at": "@переделать"}]}, {"x": 80, "y": 1260, "w": 900, "h": 350})], transition="cut"),
        shot("quiet-progress", "@Но каждую", room("library", "shelves", [], dim=0.25), [layer("Checklist", {
            "title": "Навыки складываются", "items": ["Разработка", "Маркетинг и продажи", "Экономика и ИИ"], "checkAt": [0.1, 0.7, 1.3]}, {"x": 80, "y": 800, "w": 900, "h": 550})]),
        shot("another-party", "@Пока", party(), [layer("Notification", {"app": "Старый чат", "time": "Пятница", "text": "Ну что, сегодня опять гулять?"}, {"x": 100, "y": 1270, "w": 880, "h": 210})], transition="push"),
        shot("first-client", "@у него появляется", office(day=True, pose="celebrate", live=False), [layer("Notification", {
            "app": "Первый клиент", "title": "Договорились", "text": "Готов оплатить. Когда начнём?"}, {"x": 80, "y": 1300, "w": 880, "h": 200})], transition="zoom"),
        shot("own-product", "@Потом второй", {"block": "IPhone17", "props": {"enter": "none", "float": True, "screen": {"block": "AppScreen", "props": {"sections": [
            {"type": "header", "app": "СВОЙ ПРОДУКТ", "title": "От идеи к делу"},
            {"type": "card", "name": "Первые клиенты", "sub": "Первые реальные задачи"},
            {"type": "rows", "rows": [{"label": "Прототип", "value": "Готов"}, {"label": "Клиенты", "value": "Есть"}, {"label": "Следующий шаг", "value": "Команда"}]},
            {"type": "button", "label": "Начать работу", "pressAt": "@продукт"}]}}}}, transition="zoom"),
        shot("five-years", "@Проходит", {"block": "City3D", "props": {"look": "warm", "cam": "orbit", "blocks": 3, "downtown": 1.2}, "dim": 0.4},
             [layer("BigType", {"lines": ["5 ЛЕТ", "СПУСТЯ"], "treatment": ["mark", "solid"], "at": [0, 0.25], "enter": "wipe", "maxSize": 240, "upper": True}, {"x": 70, "y": 680, "w": 940, "h": 600})], transition="cut", captions=False),
        shot("his-team", "@У него команда", {"block": "Scene3D", "props": {
            "look": "dusk", "lights": "soft", "pop": False,
            "cam": [key(0, [3.8, 3.5, 8.5], [0, 1.7, -0.5], 42), key(4, [3.4, 3.3, 8.1], [0, 1.7, -0.5], 42)],
            "objects": [
                {"type": "rug", "pos": [0, 0, -0.5], "w": 5.5, "d": 4},
                {"type": "desk", "pos": [-1.35, 0, -1.7], "w": 1.5},
                {"type": "desk", "pos": [1.35, 0, -1.7], "w": 1.5},
                {"type": "monitor", "pos": [-1.35, 0, -1.8]},
                {"type": "monitor", "pos": [1.35, 0, -1.8]},
                {"type": "chair", "pos": [-1.35, 0, -0.8], "rotY": PI},
                {"type": "chair", "pos": [1.35, 0, -0.8], "rotY": PI},
                {"type": "person", **person("type", [-1.35, 0, -0.8], 5, PI, {"shirt": "#7D998C"})},
                {"type": "person", **person("type", [1.35, 0, -0.8], 7, PI, {"shirt": "#A78C9D", "hairStyle": "bun"})},
                {"type": "person", **person("talk", [0, 0, 0.8], 1, 0.25)},
                {"type": "plant", "pos": [-2.7, 0, -2.0], "s": 1.3},
                {"type": "shelf", "pos": [0, 0, -3], "w": 1.2},
            ]}}, transition="push"),
        shot("home-for-parents", "@деньги", room("kitchen", [key(0, [4.1, 3.15, 5.2], [0.1, 1.85, 0.5], 49), key(3, [3.8, 3.0, 5.0], [0.1, 1.85, 0.5], 49)], [
            person("talk", [-0.8, 0, 0.75], rot=1.0),
            person("listen", [0.0, 0, 1.35], 15, PI, {"hair": "#B5B0A5", "shirt": "#879A88", "hairStyle": "short"}),
            person("listen", [0.8, 0, 1.35], 16, PI, {"hair": "#BBB2A7", "shirt": "#AA8992", "hairStyle": "bun"}),
        ], lights="day")),
        shot("same-old-chat", "@В старом", party(later=True), [layer("NotificationStack", {"items": [
            {"app": "Старый чат", "text": "Работа достала.", "at": 0.2},
            {"app": "Старый чат", "text": "Надо что-то менять…", "at": "@Надо"}]}, {"x": 100, "y": 1160, "w": 880, "h": 380})], transition="cut"),
        shot("must-be-lucky", "@Теперь", office(day=True), transition="zoom"),
        shot("aipollon-profile", "@Он помнит", {**room("library", [key(0, [2.8, 2.0, 3.5], [0.15, 1.7, -0.7], 48), key(5, [2.4, 1.9, 3.2], [0.15, 1.7, -0.7], 48)], [person("read", [0.12, 0, -0.68], rot=0.35)], dim=0.7), "dimAt": "@каждый"},
             [layer("IPhone17", {"enter": "flip", "flipAt": 0.25, "flipDur": 0.65, "float": True, "shadow": 0,
                 "screen": {"block": "CreatorProfile", "props": {"highlightAt": "@выбирал", "tapAt": "@учиться"}},
                 "cam": [key(0, [0, 2.1, 10.8], [0, 2.05, 0], 30), key(4.5, [0.08, 2.23, 8.9], [0, 2.23, 0], 30)]}, "full", enter="none", at="@Он помнит+0.45")],
             transition="blur", captions={"mode": "editorial", "pos": "top", "scrim": 0.85}),
    ]
    spec = {
        "id": "quiet-evenings", "mode": "explainer", "style": "dusk", "fps": 60, "duration": 40, "depthLook": True,
        "voice": {"src": "projects/quiet-evenings/voice.wav", "words": "projects/quiet-evenings/words.json", "volume": 1},
        "music": {"src": "projects/quiet-evenings/success-user-40s.wav", "volume": 0.22, "duck": 0.40, "offset": 0, "fadeIn": 0.18, "fadeOut": 1.25},
        "autoSfx": False, "grain": 0.022, "vignette": 0.15,
        "captions": {"mode": "editorial", "pos": "top", "uppercase": False, "scale": 1, "scrim": 0.8},
        "sfx": [{"at": a, "id": s, "volume": v, "alignPeak": False} for a, s, v in [
            ("@Пятница", "pk-pop-ui-menu", 0.55),
            ("@дома", "pk-click-ui-button", 0.4),
            ("@код", "typing-short", 0.45),
            ("@книги", "paper-rustle", 0.45),
            ("@интеллект", "pk-digital-data-load-sfx-1", 0.5),
            ("@провалился", "pk-result-failure", 0.5),
            ("@больше", "pk-shimmer-ui-dissolvre-sfx", 0.5),
            ("@первый клиент", "pk-notify-notification-sfx-1", 0.6),
            ("@собственный", "pk-click-ui-button", 0.5),
            ("@Проходит", "hit-sub", 0.45),
            ("@команда", "pk-shimmer-ui-dissolvre-sfx", 0.5),
            ("@В старом", "pk-notify-system-alert-sfx", 0.45),
            ("@учиться", "pk-click-ui-button", 0.5),
            ("@Начни", "hit-soft", 0.5),
        ]],
        "scenes": scenes,
    }
    (P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Built {len(scenes)} scenes, exactly {spec['duration']} seconds")


if __name__ == "__main__":
    build()
