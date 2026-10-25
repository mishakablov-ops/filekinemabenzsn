# Script formula (Russian voiceover reels)

Measured on the reference reels: 50–80 s, **2.6–2.8 words/s**, first word at 0.0–0.3 s, sentences of 5–12 words, a number every 2–3 sentences, identical outro.

## Explainer skeleton (45 s ≈ 110–120 words)
| # | beat | job | example (topic: a free app-cloning skill) |
|---|---|---|---|
| 1 | **Hook** (≤ 2.5 s, ≤ 7 words) | name the viewer's pain or a surprising fact as a question/claim | «Бесит какое-то *приложение?*» |
| 2 | **Promise** | what is now possible, concretely | «Теперь можно собрать своё такое же — только без того, за что его ругают.» |
| 3 | **Proof** | who made it + one hard number | «Это умеют 11 бесплатных скиллов, и за неделю у них больше тысячи звёзд.» |
| 4–7 | **How it works** (3–4 beats) | one action per sentence, each with a visible object or number | «Читает справку, цены, карточку в сторе…», «Получается карта из 18 экранов…» |
| 8 | **Honesty / limit** | what it does NOT do — builds trust | «Код и логотип оригинала он не трогает.» |
| 9 | **Twist / second feature** | the unexpected part | «А над тем, зачем вообще копия, думает скилл-предприниматель.» |
| 10 | **Price punch** | «Сколько стоит? Нисколько.» (slam) | |
| 11 | **Action** | exact words to type / where to get it | «Скажите Claude: „поставь geo-sleuth“ — он всё установит сам.» |
| 12 | **Outro / CTA** | the channel's fixed CTA | «Этот ролик собрал ИИ-агент. Хотите такие же? Ссылка в шапке профиля.» |

## Hooks that work (adapt the pattern, not the words)
- pain question: «Бесит, что …?» · «Устали …?»
- impossible fact with number: «Claude нашёл, где стоит печка в поле, с точностью до двух метров.»
- before/after: «Раньше на это уходил вечер. Теперь — минута.»
- direct address + object: «В чёлке MacBook поселился зверёк.»
- counter-intuitive: «Самое ценное в отзывах — не единицы, а тройки.»

## Sentence rules
- Subject → verb → object. Active voice. Present tense for demos.
- 5–12 words per sentence; split anything longer. One idea per caption card.
- Concrete nouns you can SHOW (экран, отзыв, звезда, тротуар) — every card must have something to animate.
- Numbers as digits in captions: `{11|одиннадцать}`, `{1,2k|тысяча двести}`, `{±2 м|плюс-минус два метра}`.
- Spoken brand names the way people say them: `{Claude Code|клод код}`, `{GitHub|гитхаб}` if the voice stumbles.
- Quote speech in «ёлочках»; the slang/cliché inside quotes is allowed (lint skips it).

## Banned (lint enforces)
давайте разберёмся · в современном мире · это не просто X, а Y · революционный · инновационный · уникальный · погрузимся · откройте для себя · задумывались ли вы · в этом видео · сегодня мы · всем привет · является / осуществляет / данный · стоит/важно отметить · ключевой · таким образом · на самом деле · буквально · невероятный · emoji · more than 2 «!» · dashes every other sentence (AI tell).

## Card splitting (how lines become captions)
Write one caption card per line: `подводка // ударная часть`. The punch is what the eye must catch; the lead is the setup.
```
Теперь можно собрать // своё ==такое же==
только без того, // за что его *ругают.*
```
- Accent ONE word per card (`*serif*`, `[colour]`, `==box==`, `~~strike~~`).
- Punch ≤ 34 characters; slam cards (`%slam`) ≤ 16 and ideally one word.
- Put the number on the punch side.

## Promo (music, no voice) — 15–30 s
3–6 word cards, one per bar (or per 2 beats in fast sections):
```
%slam [Ноль] кода
%slam ==Один== промпт
%slam Готовый *ролик*
%slam Под ваш / бит
%slam Бесплатно
```
Big claims land on drops; product shot on the first drop; CTA on the last bar.

## Before TTS
Run `script_lint.py`. Then read the script aloud mentally at 2.7 words/s: if any card would sit < 0.5 s or > 3 s, re-split.
