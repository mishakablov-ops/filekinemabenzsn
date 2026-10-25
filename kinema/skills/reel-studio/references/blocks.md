# Block catalog (116 blocks)

Generated from `engine/src/blocks` by `node tools/catalog.mjs`. Use in spec.json as `{ "block": "<Name>", "props": {…} }`.

Legend: **pos** default position preset · **enter** default entrance (self = animates itself) · **sfx** entrance sound · ⚑ overlay (allowed to sit on top of other blocks).

## Typography & captions-adjacent

### Title
Headline with blur-in words; markup *italic* [accent] ==mark== / linebreak. `at` = per-word anchors.

- pos: `center` · enter: `self` · sfx: `null`
- example: `{"block":"Title","props":{"text":"Собери *своё* / приложение [за вечер]","lead":"Теперь можно"}}`

### Kicker
Small uppercase label chip with glowing dot.

- pos: `top` · enter: `pop` · sfx: `pop-high`
- example: `{"block":"Kicker","props":{"text":"Новый скилл"}}`

### Counter
Rolling number; `steps:[{at,value}]` for 136→1.2k jumps; icon:'star'; format space|k|pct; label with plural forms «звезда|звезды|звёзд».

- pos: `center` · enter: `pop` · sfx: `null` · has internal sound events
- example: `{"block":"Counter","props":{"from":0,"to":1200,"format":"k","icon":"star","label":"звёзд на GitHub"}}`

### StrikeList
List whose items get red strike-throughs at anchors (strikeAt).

- pos: `center` · enter: `theme` · sfx: `null` · has internal sound events
- example: `{"block":"StrikeList","props":{"items":["Код","Логотип","Тексты"],"strikeAt":[1.2,1.6,2]}}`

### ArrowList
List where focus moves down: active item big with →, previous ones fade.

- pos: `center` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"ArrowList","props":{"items":["Код","Логотип","Тексты"]}}`

### Quote
Quote card in serif italic with author.

- pos: `center` · enter: `rise` · sfx: `paper-rustle`
- example: `{"block":"Quote","props":{"text":"Нравится, но клиенты забывают про запись","author":"отзыв в App Store"}}`

### Typewriter
Text typed character by character with caret.

- pos: `center` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"Typewriter","props":{"text":"найди, где это снято"}}`

### Pill
Rounded pill with optional counting number: «18 экранов».

- pos: `bottom` · enter: `pop` · sfx: `pop-soft`
- example: `{"block":"Pill","props":{"value":18,"text":"экранов"}}`

### Chips
Tags popping in with stagger.

- pos: `center` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"Chips","props":{"items":["Reels","Shorts","TikTok","YouTube"],"accentIdx":[0]}}`

### BigType
AGGRESSIVE: giant lines fitted to full width. enter slam|letters|rise|split|wipe; treatment solid|outline|mark|serif|accent; echo outlines.

- pos: `center` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"BigType","props":{"lines":["Ноль","кода","100%"],"treatment":["solid","outline","mark"]}}`

### Marquee
AGGRESSIVE: endless tilted text band(s); cross:true for an X of two bands.

- pos: `center` · enter: `self` · sfx: `-`
- example: `{"block":"Marquee","props":{"text":"бесплатно","cross":true}}`

### Extruded
AGGRESSIVE: pseudo-3D extruded word, slow tilt.

- pos: `center` · enter: `self` · sfx: `hit-punch`
- example: `{"block":"Extruded","props":{"text":"FREE"}}`

### LetterRoll
Slot-machine letters rolling into a word.

- pos: `center` · enter: `self` · sfx: `tick-roll`
- example: `{"block":"LetterRoll","props":{"text":"СКИЛЛ"}}`

### WordSwap
One slot cycling through words under a lead line.

- pos: `center` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"WordSwap","props":{"lead":"для","words":["дизайнеров","кодеров","всех"]}}`

### MaskText
Giant word filled with an image (image-in-type).

- pos: `center` · enter: `slam` · sfx: `hit-soft`

### Highlight
Paragraph with marker sweeps over chosen words at anchors.

- pos: `center` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"Highlight","props":{"text":"Агент читает отзывы и ищет повторяющиеся жалобы","marks":[{"word":"отзывы"},{"word":"жалобы"}]}}`

### StatSlam
AGGRESSIVE: giant stat slammed in with unit and label.

- pos: `center` · enter: `self` · sfx: `hit-punch`
- example: `{"block":"StatSlam","props":{"value":"2","unit":"м","label":"точность"}}`


## UI cards & app mockups

### Notification
iOS-style notification banner: app, icon, time, title, text, stars.

- pos: `stage` · enter: `drop` · sfx: `ding-soft`
- example: `{"block":"Notification","props":{"app":"Slotra · новый отзыв","text":"Доплата за каждого сотрудника. Серьёзно?","stars":1}}`

### NotificationStack
Notifications dropping in one by one (items[].at anchors).

- pos: `stage` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"NotificationStack","props":{"items":[{"app":"Slotra · новый отзыв","text":"Доплата за каждого сотрудника","stars":1},{"app":"Slotra · новый отзыв","text":"Клиенты забывают про запись","stars":2}]}}`

### ReviewCard
Review card: source badge (App Store/Google Play/Reddit/…), stars, text, optional highlight phrase.

- pos: `stage` · enter: `rise` · sfx: `pop-soft`
- example: `{"block":"ReviewCard","props":{"source":"Google Play","stars":3,"text":"Удобно, но клиенты из другого города путают время","highlight":"путают время"}}`

### ReviewFeed
List of reviews appearing; focus:{at, keep:[idx]} collapses the rest (filtering).

- pos: `stage` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"ReviewFeed","props":{"items":[{"source":"App Store","stars":5,"text":"Отличное приложение!"},{"source":"App Store","stars":4,"text":"Нравится, но нет напоминаний"},{"source":"Reddit","stars":1,"text":"Подняли цену. Ухожу"}],"focus":{"at":1.8,"keep":[1]}}}`

### Checklist
Plan / todo list; checkAt[] anchors tick boxes.

- pos: `stage` · enter: `rise` · sfx: `paper-rustle` · has internal sound events
- example: `{"block":"Checklist","props":{"title":"План исправлений","items":["Напоминания по SMS","Одна цена для команды","Часовой пояс"],"checkAt":[1,1.5,2]}}`

### ScoreCard
Big percentage card with bar, status pill and ✕/✓ lists (e.g. «Сходство с оригиналом 62%»).

- pos: `right` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"ScoreCard","props":{"label":"Сходство с оригиналом","value":62,"status":"Не готово к выкладке","cons":["Перенос записи","Онлайн-оплата"]}}`

### PricingCards
2–3 pricing tiers, `hot` tier highlighted, `strike` old price.

- pos: `stage` · enter: `self` · sfx: `pop-triple`
- example: `{"block":"PricingCards","props":{"tiers":[{"name":"Старт","price":"0 ₽"},{"name":"Про","price":"990 ₽","period":"/мес","hot":true},{"name":"Команда","price":"+500 ₽","period":"/чел"}]}}`

### Toast
Small confirmation toast pill (check/warn/dot).

- pos: `bottom` · enter: `pop` · sfx: `success-soft`
- example: `{"block":"Toast","props":{"text":"Скилл установлен"}}`

### Cursor ⚑
OVERLAY mouse pointer (or hand:true) gliding through points [{x,y,at,click}] in frame px, ripple on clicks.

- pos: `full` · enter: `self` · sfx: `null` · has internal sound events
- example: `{"block":"Cursor","props":{"points":[{"x":300,"y":1300},{"x":640,"y":900,"at":1},{"x":520,"y":1100,"at":2}]}}`

### Callout ⚑
OVERLAY label with leader line from point (x,y) to label (lx,ly), frame px.

- pos: `full` · enter: `self` · sfx: `pop-high`
- example: `{"block":"Callout","props":{"text":"вот здесь","x":540,"y":1000,"lx":760,"ly":820}}`

### SearchBar
Search field typing a query, then results drop down (first highlighted).

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"SearchBar","props":{"query":"клиника рядом","results":["Клиника на Ленина, 4.8","Медцентр «Здоровье», 4.6"]}}`

### Toggles
Settings list whose switches flip on at onAt[] anchors.

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"Toggles","props":{"items":["Напоминания","Онлайн-оплата","Отзывы"],"onAt":[0.8,1.2,1.6]}}`

### Steps
Numbered steps on a progress rail; showAt[] anchors.

- pos: `stage` · enter: `self` · sfx: `-` · has internal sound events
- example: `{"block":"Steps","props":{"items":[{"title":"Скажи Claude","sub":"«поставь скилл»"},{"title":"Он сам установит"},{"title":"Пользуйся"}]}}`

### CompareSplit
Before/after columns with ✕ and ✓ lists; right side revealed at revealAt.

- pos: `stage` · enter: `self` · sfx: `swipe-soft`
- example: `{"block":"CompareSplit","props":{"left":{"title":"Было","items":["3 часа монтажа","шаблоны"]},"right":{"title":"Стало","items":["10 минут","свой стиль"]}}}`

### Progress
Progress / install bar counting to 100% then `done` text.

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"Progress","props":{"label":"Устанавливаю скилл","done":"Готово"}}`

### AvatarStack
Overlapping avatars + counting label (users, stars, team).

- pos: `stage` · enter: `self` · sfx: `pop-triple`
- example: `{"block":"AvatarStack","props":{"count":5,"n":4800,"label":"человек уже пользуются"}}`

### Bubble
Single chat/speech bubble (left/right), markup supported.

- pos: `stage` · enter: `pop` · sfx: `pop-bubble`
- example: `{"block":"Bubble","props":{"text":"А можно *без* монтажа?","side":"right"}}`

### EmergencyAlert
Civil-defence emergency alert screen (390×844) with pulsing radiation sign, level pill, title and instructions. Put it on IPhone17/Phone3D/Phone screens.

- pos: `stage` · enter: `self` · sfx: `null`
- example: `{"block":"EmergencyAlert","props":{}}`

### AppScreen
Mobile app screen builder (390×844): sections header|card|days|slots|rows|button|list|text|image|bars|search|gap. selectAt/pressAt anchors animate taps. Use inside Phone/Phone3D.

- pos: `stage` · enter: `self` · sfx: `null` · has internal sound events
- example: `{"block":"AppScreen","props":{"sections":[{"type":"header","app":"Окно","title":"Запись"},{"type":"days","label":"Октябрь","days":[["Пн","13"],["Вт","14"],["Ср","15"],["Чт","16"],["Пт","17"]],"selected":2},{"type":"slots","label":"Свободное время","slots":["10:00","11:30","13:00","14:30","16:00","17:30"],"selected":3},{"type":"rows","rows":[{"label":"Напоминание по SMS","value":"нет","status":"bad"},{"label":"Тариф","value":"+500 ₽","status":"bad"}]},{"type":"button","label":"Записаться"}]}}`

### ScreenGrid
Map of an app's screens (cols×rows wireframes S01…) with a highlighted click path and a counter pill. label with Russian plural forms: «клик|клика|кликов до записи». h = max height (default 740).

- pos: `stage` · enter: `self` · sfx: `pop-triple` · has internal sound events
- example: `{"block":"ScreenGrid","props":{"cols":6,"rows":3,"path":[0,2,8,9,14,16],"label":"клик|клика|кликов до записи"}}`

### LockScreen
Phone lock screen (390×844) with notifications; actions:['Отклонить','Разрешить'] + pressAt for an approval moment.

- pos: `stage` · enter: `self` · sfx: `null` · has internal sound events
- example: `{"block":"LockScreen","props":{"notes":[{"app":"VS Code","text":"Claude ждёт разрешения","actions":["Отклонить","Разрешить"],"pressAt":1.6}]}}`

### EmailCard
Inbox email row card: from, subject, preview, unread dot.

- pos: `stage` · enter: `drop` · sfx: `ding-soft`
- example: `{"block":"EmailCard","props":{"from":"GitHub","subject":"Your repo got 1 000 stars","preview":"Congrats! replica-skill just passed…"}}`

### DynamicIsland
Big black Dynamic-Island pill expanding with icon/title/sub and optional action buttons (pressAt).

- pos: `top` · enter: `self` · sfx: `swipe-tiny` · has internal sound events
- example: `{"block":"DynamicIsland","props":{"title":"Claude Code","sub":"требует разрешения","actions":["Отклонить","Разрешить"],"pressAt":1.8}}`

### Terminal
Agent CLI terminal: lines[] kinds prompt(typed)|tool(● Name(arg) ⎿ sub)|text|ask(permission box, chooseAt)|status(spinner until)|ok|diff. Auto-scrolls. Each line has `at`.

- pos: `stage` · enter: `rise` · sfx: `whoosh-airy` · has internal sound events
- example: `{"block":"Terminal","props":{"lines":[{"kind":"prompt","text":"почини форму входа и прогони тесты"},{"kind":"tool","name":"Read","arg":"auth/middleware.ts","sub":["Read 84 lines"]},{"kind":"tool","name":"Update","arg":"LoginForm.tsx","sub":["+11 −5"]},{"kind":"ask","cmd":"npm test","chooseAt":3.2},{"kind":"ok","text":"23 tests passed"}]}}`

### ClaudeChat
AI chat desktop app: greeting (serif), input with typed text (type,typeAt), attachment drop (attach:{src,name,at}), skill chips, model label, send (sendAt) then streaming reply (reply,replyAt). dark:true variant.

- pos: `stage` · enter: `rise` · sfx: `whoosh-airy` · has internal sound events
- example: `{"block":"ClaudeChat","props":{"type":"найди, где это снято","chips":["geo-sleuth"],"attach":{"name":"IMG_2041.jpg","at":0.2}}}`

### CodeEditor
Code editor with tabs, line numbers, naive syntax colours; typeFrom = line index where typing starts; marks:[{line,kind:add|del|hl,at}].

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"CodeEditor","props":{"file":"skill.md","code":"# geo-sleuth\nconst photo = await read(\"IMG_2041.jpg\")\nconst place = locate(photo) // ±2 м\nreturn place","typeFrom":1,"marks":[{"line":3,"kind":"hl","at":2}]}}`

### GithubRepo
Repository page: owner/repo, desc, topics, rolling star count stars:[from,to] at starsAt, forks, license, file rows; ring:'stars'|'license'|'forks' circles a metric at ringAt.

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"GithubRepo","props":{"owner":"you","repo":"replica-skill","desc":"11 free skills that clone any app","stars":[136,1200],"ring":"stars","files":[{"name":"replica-architect"},{"name":"replica-backend"},{"name":"replica-design"}]}}`

### FileTree
Folder tree with indentation and highlighted entries.

- pos: `stage` · enter: `rise` · sfx: `swipe-soft`
- example: `{"block":"FileTree","props":{"items":[{"name":"skills","dir":true},{"name":"geo-sleuth","depth":1,"dir":true},{"name":"SKILL.md","depth":2,"hl":true},{"name":"terrain.py","depth":2}]}}`

### EditorTimeline
Video-editor (NLE) timeline: tracks V2/V1/Субтитры/Голос/Звуки/Эффекты, moving playhead + timecode; adds:[{track,at,n}] piles clips onto a lane at an anchor (the pain of manual editing); errorAt/errorText = export crash overlay.

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"EditorTimeline","props":{"adds":[{"track":"T1","at":0.6,"n":8},{"track":"A2","at":1.2,"n":6}],"errorAt":2.4}}`


## Devices (2D)

### Phone
2D phone (flat, crisp): screen:{block,props} (use AppScreen/LockScreen/…) or src image; w, dark, tilt (deg), float.

- pos: `stage` · enter: `rise` · sfx: `whoosh-airy`
- example: `{"block":"Phone","props":{"screen":{"block":"AppScreen","props":{"sections":[{"type":"header","app":"Окно","title":"Запись"},{"type":"card","name":"Анна Ковалёва","sub":"Стрижка · 60 мин","value":"1 500 ₽"},{"type":"button","label":"Записаться"}]}}}}`

### Window
macOS window chrome; body:{block,props} or src; url:'…' turns it into a browser; tabs.

- pos: `stage` · enter: `rise` · sfx: `whoosh-airy`
- example: `{"block":"Window","props":{"title":"Claude","url":"github.com/you/skill","body":{"block":"Title","props":{"text":"Окно"}}}}`


## Social

### SocialProfile
Generic social profile screen (390×844) for the CTA end card: handle, bio lines, link (highlights at pressAt), tiles.

- pos: `stage` · enter: `self` · sfx: `null`
- example: `{"block":"SocialProfile","props":{"handle":"reel.studio","name":"Ролики, которые собирает агент","bio":["Объяснялки с голосом","Промо под музыку"],"link":"t.me/reelstudio","tiles":[{"title":"Голос"},{"title":"3D"},{"title":"Промо"}]}}`

### TikTokProfile
The channel's TikTok profile (light theme, 390×844, 2025 layout): name, @handle · badge, avatar, bio, link, tab icons, video grid (tiles: image srcs, pinned: n first tiles get the Pinned badge), bottom nav. highlightAt draws an accent frame + tap ripple round bio/link — the 'ссылка в шапке профиля' CTA. newTile {src,label,at}: a new video lands in the first cell (NEW badge) — 'продолжение в профиле'. stats only when the real numbers are worth showing. Put it on IPhone17 (enter:'flip').

- pos: `stage` · enter: `self` · sfx: `null` · has internal sound events
- example: `{"block":"TikTokProfile","props":{"highlightAt":1.2}}`

### StoryFrame
Story viewer (390×844): progress bars, user, photo src or body block, caption, reply bar.

- pos: `stage` · enter: `self` · sfx: `-`

### PostCard
Social post card with counting replies/reposts/likes.

- pos: `stage` · enter: `rise` · sfx: `pop-soft` · has internal sound events
- example: `{"block":"PostCard","props":{"name":"Мария","handle":"maria","text":"Попросила агента собрать ролик — и он собрал. С голосом."}}`


## Data

### BarChart
Horizontal labelled bars counting up (complaints, votes). dim:true greys out an outlier, note replaces the number.

- pos: `stage` · enter: `rise` · sfx: `riser-short`
- example: `{"block":"BarChart","props":{"title":"О чём жалуются","bars":[{"label":"Нет напоминаний","value":27},{"label":"Доплата за сотрудника","value":21},{"label":"Путаница с поясом","value":14},{"label":"«Ужасный цвет»","value":1,"dim":true,"note":"1 отзыв"}]}}`

### ColumnChart
Vertical columns growing; highlight index uses the accent.

- pos: `stage` · enter: `rise` · sfx: `riser-short`
- example: `{"block":"ColumnChart","props":{"values":[120,210,340,610],"labels":["янв","фев","мар","апр"]}}`

### LineChart
Line that draws itself with an area fill and a live end value.

- pos: `stage` · enter: `rise` · sfx: `riser-short`
- example: `{"block":"LineChart","props":{"values":[10,14,13,22,31,48,75],"title":"Звёзды за неделю"}}`

### Donut
Progress ring with a counting percentage and label.

- pos: `center` · enter: `pop` · sfx: `tick-roll`
- example: `{"block":"Donut","props":{"value":94,"label":"покрытие тестами"}}`

### KPIs
2–4 KPI tiles counting up (prefix/suffix/format).

- pos: `stage` · enter: `self` · sfx: `tick-roll`
- example: `{"block":"KPIs","props":{"items":[{"value":14000,"label":"точек обзора"},{"value":2,"label":"метра точность","prefix":"±"}]}}`

### Table
Table that fades in row by row and highlights one row at highlightAt.

- pos: `stage` · enter: `rise` · sfx: `null` · has internal sound events
- example: `{"block":"Table","props":{"head":["Тариф","Цена"],"rows":[["Старт","0 ₽"],["Про","990 ₽"]],"highlight":1}}`

### Waveform
Animated voice waveform bars (voice features, podcasts).

- pos: `center` · enter: `pop` · sfx: `null`
- example: `{"block":"Waveform","props":{"label":"Голос"}}`


## Maps

### MapPin
Location pin with pulse, error radius (±2 м) and monospace coordinates.

- pos: `center` · enter: `pop` · sfx: `ping-sonar`
- example: `{"block":"MapPin","props":{"coords":"23.7351° N · 113.1235° E","radius":"2 м"}}`


## 3D scenes

### S6Shot
Сосед с шестого этажа: one shot by id (PS1 + VHS), ev = event times, c0 = tape counter.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"S6Shot","props":{"shot":"bed_up"}}`

### S6Insert
Сосед с шестого этажа: tape inserts (card, tracks, count, zoom, match).

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"S6Insert","props":{"kind":"card","lines":["НОЧЬ 1"]}}`

### PzPoseTest
podezd: debug one actor in one pose under plain light.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"PzPoseTest","props":{"who":"him","pose":"floor"}}`

### PzShot
podezd horror reel: one shot by id (hook, moan, block, upgap, landing, boothWindow, journal, serega, ask, graffiti, crane, listen, pipe, upfast, breath, wake, bed, railing, point, boothEnter, journalFloor, door, call, cry, torch, nosig, count, scratches, doorway, him, face, scarf, step, lower); ev = event times.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"PzShot","props":{"shot":"hook"}}`

### PzSetTest
podezd horror: test of one location (booth, boothAfter, descent, lair, bedroom, pipe, block) with its actor.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"PzSetTest","props":{"set":"booth"}}`

### PzTest
podezd horror: test of the Khrushchyovka stairwell, residents and poses (PS1 + VHS look). cam keys, who, flicker, breath, look.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"PzTest","props":{}}`

### NkChase
nk reel: first-person run at Panmunjom on the chase clock. tau0, look:[tau,dur], exit.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkChase","props":{}}`

### NkCctv
nk reel: UN surveillance-camera shot. tau0, cam keys, label, jeepSpin.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkCctv","props":{}}`

### NkFall
nk reel: hit, hit, fall into the leaves. tau0.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkFall","props":{}}`

### NkBarracks
nk reel: barracks, first person. mode drink|slam, slamAt, lookAt, dreadAt.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkBarracks","props":{}}`

### NkDrive
nk reel: in the jeep on the road. mode start|checkpoint.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkDrive","props":{}}`

### NkBridge
nk reel: drone shot of the jeep on the 72-hour bridge.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkBridge","props":{}}`

### NkDitch
nk reel: Panmunjom by jeep. mode approach|ditch, dropAt, revAt.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkDitch","props":{}}`

### NkHeli
nk reel: looking up at the helicopter from a stretcher.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkHeli","props":{}}`

### NkSurgery
nk reel: operating lamp, white-out at whiteAt.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkSurgery","props":{}}`

### NkOutro
nk reel: last shots over the line. view line|wide.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"NkOutro","props":{}}`

### RescueTest
nk-escape test: ROK soldiers crawl to the defector and drag him (his eyes or a side view).

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"RescueTest","props":{}}`

### MxTest
nk-escape test: Mixamo soldiers. view: gallery|chase; qa logs feet checks.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"MxTest","props":{}}`

### SoldiersTest
nk-escape test: procedural soldiers (pose gallery).

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"SoldiersTest","props":{}}`

### BarracksTest
nk-escape test: KPA barracks room, first person at the table (one hand takes the cup).

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"BarracksTest","props":{}}`

### JsaTest
nk-escape test: Panmunjom JSA set. view: overview|run (first-person run to the wall).

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"JsaTest","props":{"view":"run"}}`

### JeepDriveTest
nk-escape test: first-person drive in the jeep with live hands on the wheel (project-specific).

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"JeepDriveTest","props":{}}`

### Laptop3D
Real 3D laptop (PBR metal, reflections, shadow) with a LIVE HTML screen: screen:{block,props} or src image. cam: hero|orbit|lowAngle|zoomScreen|top|side|close or keyframes. open:true animates the lid. color: silver|space|midnight|black.

- pos: `full` · enter: `self` · sfx: `null` · has internal sound events
- example: `{"block":"Laptop3D","props":{"screen":{"block":"Title","props":{"text":"Привет, *3D*"}},"cam":"hero","open":true}}`

### Phone3D
Real 3D phone(s) with LIVE HTML screens. phones:[{screen,pos,rot,color}] for a fan of up to 3 (keep them from overlapping). cam: hero|close|low|wide. turn:[fromDeg,toDeg], enterSpin. color: titanium|black|silver|white|gold.

- pos: `full` · enter: `self` · sfx: `whoosh-airy`
- example: `{"block":"Phone3D","props":{"screen":{"block":"Title","props":{"text":"9:41"}},"enterSpin":true}}`

### Globe3D
Earth with real coastlines. look: dots|solid|night|light. focus:[{t,lat,lon,dist}] flies the camera; markers:[{lat,lon,label,at}] pulse + HTML label; arcs:[{from:[lat,lon],to:[lat,lon],at,dur}] animated flight lines.

- pos: `full` · enter: `self` · sfx: `whoosh-deep` · has internal sound events
- example: `{"block":"Globe3D","props":{"look":"dots","focus":[{"t":0,"lat":30,"lon":80,"dist":3.8},{"t":2.5,"lat":49,"lon":-123,"dist":2.6}],"markers":[{"lat":49.2,"lon":-123.1,"label":"49.21° N · 123.11° W","at":2.4}],"arcs":[{"from":[23.7,113.1],"to":[49.2,-123.1],"at":0.5,"dur":1.8}]}}`

### Terrain3D
Procedural mountains. look: satellite|alpine|topo|desert|mono. cam: flyover|orbit|reveal|top|low. contours (0..1), scan:{at,dur} sweeping band, highlightHeight (accent iso-line), points:{count,at,dur} viewpoints appearing, pins:[{x,z,label,at}].

- pos: `full` · enter: `self` · sfx: `whoosh-deep` · has internal sound events
- example: `{"block":"Terrain3D","props":{"look":"alpine","cam":"reveal","contours":0.25,"points":{"count":1500,"at":1.5,"dur":2}}}`

### City3D
Procedural city that grows from the ground. look: warm|white|night|clay. cam: orbit|dive|street|iso. blossom 0..1 = share of pink trees; downtown = tower height; highlight:{x,z,label,at} target ring.

- pos: `full` · enter: `self` · sfx: `whoosh-medium` · has internal sound events
- example: `{"block":"City3D","props":{"look":"warm","cam":"dive","blossom":0.4,"highlight":{"x":2,"z":2,"label":"49.2158° N · 123.1087° W","at":3}}}`

### Shapes3D
Glossy iridescent hero objects: blob|torus|knot|rings|pills|cubes, glass:true for transmission. Use sparingly — abstract shapes read as generic.

- pos: `full` · enter: `self` · sfx: `reveal-glow`
- example: `{"block":"Shapes3D","props":{"kind":"rings"}}`

### Bars3D
3D bar chart growing with HTML value labels. bars:[{label,value,color}], unit, cam: orbit|front. Last bar uses the accent.

- pos: `full` · enter: `self` · sfx: `riser-short`
- example: `{"block":"Bars3D","props":{"bars":[{"label":"янв","value":120},{"label":"фев","value":210},{"label":"мар","value":340},{"label":"апр","value":610}],"unit":""}}`

### Tunnel3D
Flying through glowing rings/squares/hexes. Intros, 'deep dive' moments, transitions.

- pos: `full` · enter: `self` · sfx: `trans-zoom-through`
- example: `{"block":"Tunnel3D","props":{"shape":"hex"}}`

### StarRain
3D stars / coins / hearts raining and tumbling (GitHub stars, rewards, likes). Transparent — overlay on any scene.

- pos: `full` · enter: `self` · sfx: `sparkle-rise`
- example: `{"block":"StarRain","props":{"kind":"star"}}`

### Cards3D
CSS-3D (crisp HTML) cards floating in depth with a moving camera. items:[{block,props|src,x,y,z,rx,ry,w,h,at}], cam:{from:[x,y,z],to,rx:[a,b],ry:[a,b]}.

- pos: `full` · enter: `self` · sfx: `swipe-soft`
- example: `{"block":"Cards3D","props":{"items":[{"block":"Title","props":{"text":"Один"},"x":-250,"z":-200},{"block":"Title","props":{"text":"Два"},"x":250,"z":0}]}}`

### Tilt
Wrap any block in a slow perspective tilt (2.5D). child:{block,props}, rx:[from,to], ry:[from,to], w,h.

- pos: `center` · enter: `self` · sfx: `whoosh-airy`
- example: `{"block":"Tilt","props":{"child":{"block":"Title","props":{"text":"Tilt"}}}}`

### Room3D
Cut-away 3D room diorama in dark pastel. preset: office|living|bedroom|cafe|studio + cozy library (wall of books, armchair reader, candle) | kitchen (counter, stove with steam, fridge, dining table) | cabin (log walls, real fireplace) | basement (concrete shelter: supply racks, water, crank radio, lantern, sandbags, steel door, tally board). people:[{pose,pos,rotY,seed,look:{suit:true = improvised protective gear},walkTo}] (fpv cams default to nobody). screen:{block,props} = LIVE HTML on the monitor (office) or TV (living). cam: diorama|front|closeDesk|pushIn|top|inside; library: reading|shelves; kitchen: counter|table; cabin: fire; basement: corner + first-person fpvEnter|fpvShelf|fpvRadio|fpvDoor|fpvWindow|fpvBed|fpvTally|fpvHands. hands:{item:radio|can|bottle|tape|lantern|geiger|mask, gloves, sleeve, from} = your own hands in a first-person shot. basement: days (tally marks), door 0..1 or [from,to] animated, lantern. lights: day|evening|night. build:true pops the room up.

- pos: `full` · enter: `self` · sfx: `whoosh-airy`
- example: `{"block":"Room3D","props":{"preset":"office","cam":"diorama"}}`

### Street3D
Ordinary city street: buildings with windows, moving cars, walking people, lamps, trees, crosswalk + traffic lights. time: day|evening|night; cam: eye|high|follow|crossing|top|drone; cars, people counts; traffic red|green; highlight:{x,z,label,at}. abandoned:true = after a disaster: empty, dusty fog, abandoned cars with open doors, dead trees, rubble, paper, barricade, falling ash (ash:false to stop), lights dead; walkers:[{x,z,speed,dir,look:{suit:true}}] for a lone survivor.

- pos: `full` · enter: `self` · sfx: `whoosh-medium`
- example: `{"block":"Street3D","props":{"time":"evening","cam":"eye"}}`

### Blast3D
Nuclear blast over a distant city at dusk (stylized, no gore): flash (warm, never pure white) at flashAt, fireball → mushroom cloud rising for ~9 s, ground shockwave sweeping to the camera at waveAt (default flashAt+3.2) with camera shake, dust haze and falling ash. cam: hill|street|wide or keyframes. Cue your own boom/rumble SFX on flashAt and waveAt.

- pos: `full` · enter: `self` · sfx: `null`
- example: `{"block":"Blast3D","props":{"cam":"hill","flashAt":0.6}}`

### Scene3D
Compose your own low-poly scene: objects:[{type,pos,rotY,at,...}] types person|desk|chair|monitor|laptop|sofa|bed|table|shelf|plant|lamp|rug|frame|mug|pendant|counter|stool|tv|car|tree|streetlamp|bench|traffic|building|box. Persons: pose stand|walk|run|sit|type|wave|point|think|phone|cheer, walkTo. labels:[{text,pos,at}]. cam keyframes.

- pos: `full` · enter: `self` · sfx: `whoosh-airy`
- example: `{"block":"Scene3D","props":{"objects":[{"type":"rug","pos":[0,0,0],"w":4,"d":3},{"type":"person","pos":[-0.8,0,0],"pose":"wave","rotY":0.4},{"type":"person","pos":[0.8,0,0.2],"pose":"think","rotY":-0.4,"seed":3},{"type":"plant","pos":[2,0,-1]}],"labels":[{"text":"Привет!","pos":[-0.8,2.3,0],"at":1}]}}`

### Model3D
Import any .glb/.gltf from engine/public/models (BlenderKit/Sketchfab/Poly Haven; convert .blend with scripts/blend2glb.py). fit = size, cam hero|orbit|low|top, spin deg/s, enter rise|spin, anim plays embedded clip. screenMesh + screen:{block,props} maps a LIVE HTML screen onto the model's display mesh.

- pos: `full` · enter: `self` · sfx: `whoosh-airy`

### MacBook
The user's real MacBook model (models/macbook.glb) with a LIVE HTML screen. screen:{block,props}; cam: orbit|hero|low|top|close|toScreen (flies into the display) or keyframes; spin; enter rise|spin|none.

- pos: `full` · enter: `self` · sfx: `whoosh-airy`
- example: `{"block":"MacBook","props":{"screen":{"block":"Terminal","props":{"w":1280,"h":840,"size":34,"lines":[{"kind":"prompt","text":"собери ролик"}]}},"cam":"orbit"}}`

### IPhone17
The user's real iPhone 17 Pro model (models/iphone17pro.glb) standing upright with a LIVE 390×844 screen (AppScreen, LockScreen, SocialProfile…). spin deg/s, enter spin|rise, cam keyframes or orbit|hero|close|toScreen.

- pos: `full` · enter: `self` · sfx: `whoosh-airy`
- example: `{"block":"IPhone17","props":{"screen":{"block":"LockScreen","props":{"notes":[{"app":"Claude","text":"Ролик готов","at":0.5}]}},"spin":10,"enter":"spin"}}`


## Backgrounds

### WarmGlow
Default for ember/blaze: near-black warm base with a slow drifting amber glow.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"WarmGlow","props":{}}`

### Solid
Flat colour (theme bg by default).

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"Solid","props":{}}`

### MeshGradient
Soft drifting pastel blobs. Light explainers (cloud/pop).

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"MeshGradient","props":{}}`

### Aurora
Dark base with flowing coloured light. Neon/tech.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"Aurora","props":{"base":"#0B0614"}}`

### Studio
Warm spotlight + floor. Hero shots of devices (pair with Laptop3D).

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"Studio","props":{}}`

### Stars
Twinkling starfield (transparent).

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"Stars","props":{}}`

### PlanetHorizon
Night sky + glowing planet rim. Big questions / mission lines.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"PlanetHorizon","props":{}}`

### Sky
Blue sky with drifting procedural clouds. Calm, optimistic.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"Sky","props":{}}`

### Paper
Warm paper. Editorial / magazine.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"Paper","props":{}}`

### GridBG
Faint grid, or `floor:true` synthwave perspective floor.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"GridBG","props":{"floor":true}}`

### PhotoBG
Photo with Ken Burns zoom/pan, optional darken/blur/top shade.

- pos: `full` · enter: `self` · sfx: `-`

### VideoBG
Muted video background with slow zoom.

- pos: `full` · enter: `self` · sfx: `-`

### FootageTop
Screen recording/photo in the top 60%, fading to black (subtitles below).

- pos: `full` · enter: `self` · sfx: `-`

### LightSweep
Dark bg with a slow diagonal light sweep.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"LightSweep","props":{}}`

### DuoTone
Two-tone diagonal gradient.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"DuoTone","props":{}}`

### ShaderBG
GPU shader background. preset: skyAbove|skyBelow|cloudWall|liquid|aurora|contour|rays|smoke. skyAbove = flying over a sea of clouds; skyBelow = cumulus overhead; cloudWall = soft overcast; liquid = premium flowing gradient (theme colours); aurora; contour = topographic lines; rays; smoke. colors:[c1..c4], speed, sun, cover.

- pos: `full` · enter: `self` · sfx: `-`
- example: `{"block":"ShaderBG","props":{"preset":"skyAbove"}}`

