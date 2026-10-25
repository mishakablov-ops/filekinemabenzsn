"""Lint a voiceover script (script.md) before spending time on TTS/render.

    python script_lint.py <project_dir | script.md> [--mode explainer|promo]

Catches: weak/long hook, AI-template clichés, bureaucratic Russian, emoji, overused dashes and
exclamations, overlong caption cards, more than one accent per card, unbalanced markup, numbers the
TTS will misread, missing CTA, repeated words, overall length. Exit code 1 if there are errors.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from script_parse import parse_script, spoken_text  # noqa: E402

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

WPS = 2.7  # measured on the reference reels (ru-RU-DmitryNeural +6% is the same pace)

CLICHES = {
    # phrase -> (severity, why)
    "давайте разберемся": ("error", "AI/YouTube-шаблон, сразу к делу"),
    "давайте разберёмся": ("error", "AI/YouTube-шаблон, сразу к делу"),
    "в современном мире": ("error", "пустая вводная"),
    "в эпоху": ("warn", "пустая вводная"),
    "это не просто": ("error", "шаблон «не просто X, а Y»"),
    "не просто": ("warn", "часто шаблон «не просто X, а Y»"),
    "революцион": ("error", "рекламный штамп"),
    "инновацион": ("error", "рекламный штамп"),
    "уникальн": ("warn", "пустой эпитет — покажи, чем именно"),
    "погрузимся": ("error", "AI-штамп"),
    "окунемся": ("error", "AI-штамп"),
    "окунёмся": ("error", "AI-штамп"),
    "откройте для себя": ("error", "рекламный штамп"),
    "раскройте": ("warn", "штамп"),
    "задумывались ли вы": ("error", "шаблонный хук"),
    "представьте себе": ("warn", "шаблонный хук — лучше факт"),
    "в этом видео": ("error", "не говори о видео — говори о деле"),
    "сегодня мы": ("error", "шаблонное вступление"),
    "всем привет": ("error", "теряет первые 2 секунды"),
    "друзья,": ("warn", "обращение-пустышка"),
    "ставь лайк": ("warn", "CTA-штамп; используй конкретный CTA"),
    "подписывайтесь": ("warn", "CTA-штамп; используй конкретный CTA"),
    "невероятн": ("warn", "эмоция без факта"),
    "максимально": ("warn", "канцелярит/вода"),
    "является": ("warn", "канцелярит"),
    "осуществля": ("error", "канцелярит"),
    "данный": ("warn", "канцелярит"),
    "следует отметить": ("error", "канцелярит"),
    "стоит отметить": ("error", "канцелярит"),
    "важно отметить": ("error", "канцелярит"),
    "ключев": ("warn", "AI-штамп «ключевой»"),
    "таким образом": ("warn", "связка из эссе"),
    "в целом": ("warn", "вода"),
    "по сути": ("warn", "вода"),
    "на самом деле": ("warn", "вода"),
    "буквально": ("warn", "вода"),
    "game changer": ("error", "штамп"),
    "let's dive": ("error", "AI-штамп"),
    "delve": ("error", "AI-штамп"),
    "unlock": ("warn", "AI-штамп"),
    "seamless": ("warn", "AI-штамп"),
    "leverage": ("warn", "AI-штамп"),
    "elevate": ("warn", "AI-штамп"),
    "in today's world": ("error", "пустая вводная"),
}
CTA_WORDS = ["ссылк", "в шапке", "шапку", "заходи", "профил", "подпиш", "скажите", "напишите", "поставь", "скачай", "забирай", "коммент", "сохрани", "переходи", "жми", "в профиле", "бесплатн"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
STOP = set("и в во не на что как это с со к по из за от до а но он она они мы вы я его её их ты же ли бы у о об для при над под там тут так все всё уже еще ещё был была были будет есть".split())


def lint(path: Path, mode: str = "explainer"):
    src = path.read_text(encoding="utf-8")
    issues: list[tuple[str, int, str]] = []
    lines = src.splitlines()

    def add(sev, ln, msg):
        issues.append((sev, ln, msg))

    for i, raw in enumerate(lines, 1):
        l = raw.strip()
        if not l or l.startswith("#"):
            continue
        # text inside «ёлочки» is a quotation (e.g. mocking a cliché) — don't flag it
        low = re.sub(r"«[^»]*»", "", l).lower().replace("ё", "е")
        for k, (sev, why) in CLICHES.items():
            if k.replace("ё", "е") in low:
                add(sev, i, f"«{k}» — {why}")
        if EMOJI.search(l):
            add("error", i, "эмодзи в сценарии (TTS их читает/ломает, в титрах выглядит как шаблон)")
        for mk, name in (("==", "==выделение=="), ("~~", "~~зачёркивание~~"), ("__", "__обводка__"), ("!!", "!!красный!!"), ("++", "++зелёный++")):
            if l.count(mk) % 2:
                add("error", i, f"несбалансированная разметка {name}")
        if re.sub(r"\{[^}]*\}", "", l).count("*") % 2:
            add("error", i, "несбалансированная разметка *курсив*")
        if l.count("[") != l.count("]"):
            add("error", i, "несбалансированные [ ]")
        if re.search(r"\d+[.,]?\d*\s*[kк]\b", l) and "{" not in l:
            add("warn", i, "«1.2k» TTS прочтёт плохо — используй {1,2k|тысяча двести}")
        if re.search(r"\b\d{4,}\b", re.sub(r"\{[^}]*\}", "", l)):
            add("warn", i, "длинное число без {показ|произношение} — проверь, как его прочтёт голос")

    cards = parse_script(src)
    if not cards:
        add("error", 0, "пустой сценарий")
        return issues, {}
    # --- per card checks
    for c in cards:
        punch = " ".join(t.display for t in c.toks if t.role == "punch")
        lead = " ".join(t.display for t in c.toks if t.role == "lead")
        styled_groups = 0
        prev = None
        for t in c.toks:
            key = tuple(t.style)
            if t.style and key != prev:
                styled_groups += 1
            prev = key if t.style else None
        mode_c = c.mode or ("slam" if mode == "promo" else "editorial")
        max_p = 16 if mode_c == "slam" else 34
        if len(punch) > max_p:
            add("warn", 0, f"карточка {c.i}: ударная строка {len(punch)} симв > {max_p} — разбей на две карточки: «{punch[:40]}…»")
        if len(lead) > 46:
            add("warn", 0, f"карточка {c.i}: подводка {len(lead)} симв > 46")
        if styled_groups > 1:
            add("warn", 0, f"карточка {c.i}: {styled_groups} акцента — оставь один, иначе акцент теряется")
    # --- whole script
    words = [w for c in cards for t in c.toks for w in t.spoken]
    n = len(words)
    pauses = sum(t.pause_after for c in cards for t in c.toks)
    est = n / WPS + pauses
    sentences = re.split(r"(?<=[.!?…])\s+", " ".join(spoken_text(c.toks) for c in cards))
    first = cards[0]
    hook_words = len([w for t in first.toks for w in t.spoken])
    if hook_words > 8:
        add("warn", 1, f"хук {hook_words} слов — первая карточка должна читаться за ≤2.5 с (≤7 слов)")
    if mode == "explainer" and not (est >= 20 and est <= 80):
        add("warn", 0, f"оценка длительности {est:.0f} с — для Reels/Shorts держи 30–75 с")
    long_s = [s for s in sentences if len(s.split()) > 18]
    for s in long_s:
        add("warn", 0, f"длинное предложение ({len(s.split())} слов): «{s[:60]}…» — режь на два")
    dashes = src.count("—")
    if dashes > max(3, n // 40):
        add("warn", 0, f"тире: {dashes} — частые «—» выдают AI-текст")
    excl = re.sub(r"!!(.+?)!!", r"\1", src).count("!")  # !!x!! is red-word markup, not exclamation
    if excl > 2:
        add("warn", 0, f"восклицательных знаков: {excl} — интонация от фактов, не от «!»")
    tail = " ".join(spoken_text(c.toks) for c in cards[-3:]).lower()
    if mode == "explainer" and not any(k in tail for k in CTA_WORDS):
        add("warn", 0, "нет конкретного CTA в последних карточках (что сделать зрителю?)")
    content = [re.sub(r"[^\wё-]", "", w.lower()) for w in words]
    cnt = Counter(w for w in content if len(w) > 3 and w not in STOP)
    for w, k in cnt.items():
        if k > 3:
            add("warn", 0, f"слово «{w}» повторяется {k} раз")
    digits = sum(1 for c in cards for t in c.toks if re.search(r"\d", t.display))
    if mode == "explainer" and digits == 0:
        add("warn", 0, "ни одной цифры — конкретные числа сильно повышают удержание")
    stats = dict(cards=len(cards), words=n, est_seconds=round(est, 1), hook_words=hook_words, digits=digits)
    return issues, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--mode", default="explainer", choices=["explainer", "promo"])
    a = ap.parse_args()
    p = Path(a.path)
    if p.is_dir():
        p = p / "script.md"
    issues, stats = lint(p, a.mode)
    errs = [x for x in issues if x[0] == "error"]
    for sev, ln, msg in sorted(issues, key=lambda x: (x[0] != "error", x[1])):
        print(f"{'ERROR' if sev == 'error' else 'warn '} {('L' + str(ln)) if ln else '   '}  {msg}")
    print(f"\n{stats}")
    print("LINT FAIL" if errs else "LINT OK" + (" (with warnings)" if issues else ""))
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
