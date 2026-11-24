"""Экраны для «Канал без лица»: телефон и монитор героя (PNG), которые сцены Blender кладут на экраны.
    python3 ui_textures.py OUT_DIR
Шрифты DejaVu (облако) или Arial (Windows). Сумм заработка и ссылок на экранах нет (knowledge/rules/promo-funnel.md).
"""
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else 'ui'
os.makedirs(OUT, exist_ok=True)
FONTS = {
    'b': ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf'],
    'r': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf'],
}
BG = (18, 19, 24)
CARD = (34, 36, 44)
TXT = (240, 240, 244)
DIM = (150, 152, 164)
ACC = (255, 196, 64)       # фирменный жёлтый
OK = (88, 214, 141)
RED = (255, 84, 92)
rng = random.Random(7)


def font(kind, size):
    for p in FONTS[kind]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def save(im, name):
    im.save(os.path.join(OUT, name + '.png'))


def thumb(d, box, seed):
    """Превью вертикального 3D-ролика: небо, земля, силуэт героя, полоска титров (без текста)."""
    r = random.Random(seed)
    x0, y0, x1, y1 = box
    sky = r.choice([(255, 168, 96), (120, 176, 255), (196, 140, 255), (255, 120, 140), (110, 220, 200)])
    d.rounded_rectangle(box, 18, fill=sky)
    gy = y0 + (y1 - y0) * r.uniform(0.6, 0.72)
    d.rectangle([x0, gy, x1, y1 - 18], fill=tuple(int(c * 0.45) for c in sky))
    d.rounded_rectangle([x0, y1 - 40, x1, y1], 18, fill=tuple(int(c * 0.45) for c in sky))
    for k in range(r.randint(2, 4)):                       # дома на горизонте
        bx = x0 + (x1 - x0) * r.uniform(0.05, 0.8)
        bw = (x1 - x0) * r.uniform(0.1, 0.22)
        bh = (y1 - y0) * r.uniform(0.12, 0.3)
        d.rectangle([bx, gy - bh, bx + bw, gy], fill=tuple(int(c * 0.65) for c in sky))
    cx = (x0 + x1) / 2 + (x1 - x0) * r.uniform(-0.15, 0.15)
    hr = (x1 - x0) * 0.09
    d.ellipse([cx - hr, gy - hr * 5.2, cx + hr, gy - hr * 3.2], fill=(40, 36, 44))
    d.rounded_rectangle([cx - hr * 1.2, gy - hr * 3.3, cx + hr * 1.2, gy - hr * 0.2], int(hr * 0.6), fill=(40, 36, 44))
    d.rounded_rectangle([x0 + 14, y0 + (y1 - y0) * 0.18, x1 - 14, y0 + (y1 - y0) * 0.18 + 16], 8, fill=(255, 255, 255))


# ----------------------------------------------------------------------------- телефон: лента безликого канала
def phone_feed():
    W, H = 720, 3120                                     # две высоты экрана: сцена прокручивает UV
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    for k in range(2):
        y = k * 1560
        thumb(d, (0, y, W, y + 1560), 11 + k)
        d.text((40, y + 1330), '@kanal_bez_lica', font=font('b', 34), fill=TXT)
        d.text((40, y + 1380), 'Что если исчезнут все…', font=font('r', 30), fill=TXT)
        for j, ic in enumerate(('♥', '💬', '↗')):
            cy = y + 860 + j * 130
            d.ellipse([W - 110, cy, W - 30, cy + 80], fill=(0, 0, 0, 90) if False else (30, 30, 36))
            d.text((W - 70, cy + 40), '♥' if j == 0 else ('…' if j == 1 else '➦'), font=font('b', 40), fill=TXT, anchor='mm')
    save(im, 'phone_feed')


# ----------------------------------------------------------------------------- телефон: уведомления о рекламе
NOTES = [('Предложение о рекламе', 'Бренд хочет интеграцию в ваш ролик'),
         ('Интеграция в ролик', 'Можно обсудить формат и сроки?'),
         ('Партнёрская программа', 'Ваш канал подходит для партнёрки')]


def phone_notes():
    W, H = 720, 1560
    for n in range(len(NOTES) + 1):
        im = Image.new('RGB', (W, H), (26, 30, 44))
        d = ImageDraw.Draw(im)
        d.text((W / 2, 170), '21:47', font=font('b', 120), fill=TXT, anchor='mm')
        d.text((W / 2, 260), 'среда, 25 ноября', font=font('r', 34), fill=DIM, anchor='mm')
        for k in range(n):
            y = 380 + k * 190
            d.rounded_rectangle([30, y, W - 30, y + 165], 34, fill=(58, 62, 78))
            d.rounded_rectangle([56, y + 30, 126, y + 100], 18, fill=ACC)
            d.text((91, y + 65), '▶', font=font('b', 36), fill=BG, anchor='mm')
            d.text((150, y + 30), NOTES[k][0], font=font('b', 32), fill=TXT)
            d.text((150, y + 80), NOTES[k][1], font=font('r', 26), fill=(205, 207, 216))
        save(im, 'phone_notes%d' % n)


# ----------------------------------------------------------------------------- монитор: ручной монтаж ночью
def mon_edit():
    W, H = 1600, 900
    im = Image.new('RGB', (W, H), (28, 29, 34))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 44], fill=(44, 45, 52))
    for k, t in enumerate(('Файл', 'Правка', 'Клип', 'Эффекты', 'Окно')):
        d.text((24 + k * 120, 10), t, font=font('r', 22), fill=DIM)
    d.rectangle([520, 70, 1080, 470], fill=(12, 12, 14))
    thumb(d, (690, 80, 910, 460), 5)
    for x in (40, 1110):                                  # панели слева и справа
        d.rounded_rectangle([x, 70, x + 450, 470], 10, fill=CARD)
        for j in range(7):
            d.rounded_rectangle([x + 20, 92 + j * 52, x + 20 + rng.randint(160, 400), 122 + j * 52], 6, fill=(52, 55, 66))
    d.rectangle([0, 500, W, H], fill=(22, 23, 27))
    cols = [(92, 140, 255), (255, 140, 92), (120, 220, 140), (220, 120, 255), (255, 200, 80)]
    for tr in range(7):                                   # дорожки, нарезка на кусочки
        y = 530 + tr * 50
        x = 30
        while x < W - 40:
            w = rng.randint(30, 180)
            d.rounded_rectangle([x, y, min(W - 30, x + w), y + 38], 5, fill=cols[tr % 5] if tr < 4 else (70, 72, 84))
            x += w + rng.randint(2, 14)
    d.rectangle([845, 500, 849, H], fill=RED)
    d.text((W - 40, 470), 'Экспорт 3 %   осталось 2 ч 40 мин', font=font('b', 26), fill=RED, anchor='rb')
    save(im, 'mon_edit')


# ----------------------------------------------------------------------------- монитор: одна фраза → ролик
STEPS = ['Сценарий', 'Голос', '3D-сцены', 'Субтитры']
PROMPT = 'сделай ролик про то, что будет, если исчезнет интернет'


def mon_build():
    W, H = 1600, 900
    for st in range(-1, len(STEPS) + 1):                 # -1 пустое поле, 0 фраза, 1..4 галочки, последний = готово
        for typed in ([0.0, 0.35, 0.7, 1.0] if st == -1 else [1.0]):
            im = Image.new('RGB', (W, H), BG)
            d = ImageDraw.Draw(im)
            d.text((80, 70), 'KINEMA', font=font('b', 54), fill=ACC)
            d.text((80, 140), 'ролик из одной фразы', font=font('r', 30), fill=DIM)
            d.rounded_rectangle([80, 210, W - 80, 320], 26, fill=CARD, outline=ACC if st == -1 else (70, 72, 84), width=4)
            s = PROMPT[:int(round(len(PROMPT) * typed))]
            d.text((120, 265), s + ('|' if st == -1 else ''), font=font('r', 38), fill=TXT, anchor='lm')
            if st >= 0:
                for k, name in enumerate(STEPS):
                    y = 390 + k * 105
                    done = k < st
                    d.ellipse([110, y, 170, y + 60], fill=OK if done else (60, 62, 72))
                    if done:
                        d.line([(124, y + 31), (137, y + 44), (158, y + 18)], fill=BG, width=8)
                    d.text((200, y + 30), name, font=font('b', 40), fill=TXT if done else DIM, anchor='lm')
                d.rounded_rectangle([1050, 360, 1430, 860], 22, fill=(12, 12, 14))
                if st >= len(STEPS):
                    thumb(d, (1065, 375, 1415, 845), 21)
                    d.ellipse([1200, 560, 1280, 640], fill=(255, 255, 255))
                    d.polygon([(1228, 578), (1228, 622), (1262, 600)], fill=BG)
                    d.rounded_rectangle([80, 820, 560, 870], 25, fill=OK)
                    d.text((320, 845), 'Готово: ролик.mp4', font=font('b', 30), fill=BG, anchor='mm')
                else:
                    pr = st / len(STEPS)
                    d.rounded_rectangle([1090, 600, 1390, 616], 8, fill=(60, 62, 72))
                    d.rounded_rectangle([1090, 600, 1090 + max(16, 300 * pr), 616], 8, fill=ACC)
            name = ('mon_type%d' % int(typed * 100)) if st == -1 else ('mon_build%d' % st)
            save(im, name)


# ----------------------------------------------------------------------------- монитор: меню стилей
STYLES = [('3D', 0), ('Пиксель', 0),                 # выпущенные; дальше стили из теста с таксой (mike 24.11)
          ('Пластилин', 1), ('Аниме', 1), ('Неон', 1), ('Гжель', 1),
          ('Low poly', 1), ('Мультик', 1), ('Полутон', 1), ('16-бит', 1), ('Силуэт', 1), ('Чертёж', 1)]


def mon_styles():
    W, H = 1600, 900
    tint = [(255, 168, 96), (120, 176, 255), (255, 214, 92), (110, 220, 200), (220, 140, 110), (255, 120, 180),
            (120, 255, 230), (90, 140, 255), (190, 160, 255), (240, 120, 100), (70, 70, 80), (90, 150, 220)]
    for hi in range(len(STYLES)):
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        d.text((80, 50), 'Стиль ролика', font=font('b', 50), fill=TXT)
        for k, (name, soon) in enumerate(STYLES):
            c, r = k % 4, k // 4
            x, y = 80 + c * 370, 150 + r * 245
            d.rounded_rectangle([x, y, x + 340, y + 215], 22, fill=tint[k], outline=ACC if k == hi else None, width=8)
            d.rounded_rectangle([x, y + 145, x + 340, y + 215], 22, fill=(0, 0, 0))
            d.text((x + 24, y + 180), name, font=font('b', 34), fill=TXT, anchor='lm')
            if soon:
                d.rounded_rectangle([x + 200, y + 16, x + 324, y + 60], 22, fill=BG)
                d.text((x + 262, y + 38), 'скоро', font=font('b', 24), fill=ACC, anchor='mm')
        save(im, 'mon_styles%02d' % hi)


# ----------------------------------------------------------------------------- монитор: созвон «настроим за тебя»
def mon_call():
    W, H = 1600, 900
    for step in range(3):
        im = Image.new('RGB', (W, H), (16, 17, 22))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([60, 60, 1060, 840], 24, fill=CARD)
        d.text((100, 100), 'Установка KINEMA', font=font('b', 40), fill=TXT)
        for k, t in enumerate(('Скачать движок', 'Подключить голос', 'Название канала', 'Первый ролик')):
            y = 200 + k * 140
            done = k < step + 2
            d.rounded_rectangle([100, y, 1020, y + 110], 18, fill=(46, 49, 60))
            d.ellipse([130, y + 25, 190, y + 85], fill=OK if done else (70, 72, 84))
            if done:
                d.line([(144, y + 56), (157, y + 69), (178, y + 42)], fill=BG, width=8)
            d.text((220, y + 55), t, font=font('b', 36), fill=TXT if done else DIM, anchor='lm')
        d.rounded_rectangle([1100, 60, 1540, 440], 24, fill=(52, 70, 96))   # окно созвона: аватар помощника
        d.ellipse([1255, 140, 1385, 270], fill=(214, 220, 232))
        d.rounded_rectangle([1215, 280, 1425, 440], 60, fill=(214, 220, 232))
        d.rounded_rectangle([1100, 470, 1540, 840], 24, fill=(44, 48, 60))
        d.text((1320, 560), 'Помощник', font=font('b', 36), fill=TXT, anchor='mm')
        d.text((1320, 620), 'на связи', font=font('r', 30), fill=OK, anchor='mm')
        cx, cy = [(700, 370), (720, 510), (760, 650)][step]
        d.polygon([(cx, cy), (cx, cy + 54), (cx + 15, cy + 40), (cx + 34, cy + 50)], fill=(255, 255, 255), outline=BG)
        save(im, 'mon_call%d' % step)


# ----------------------------------------------------------------------------- телефон: комментарии в конце
def phone_comments():
    """Поле комментария, куда зритель сам пишет «канал» (без выдуманных чужих комментов)."""
    W, H = 720, 1560
    for typed in range(6):
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        thumb(d, (0, 0, W, 900), 31)
        d.rounded_rectangle([0, 860, W, H], 40, fill=(28, 29, 36))
        d.text((W / 2, 910), 'Комментарии', font=font('b', 32), fill=TXT, anchor='mm')
        d.text((W / 2, 1150), 'Напиши первым', font=font('r', 30), fill=DIM, anchor='mm')
        d.rounded_rectangle([30, 1420, W - 140, 1510], 45, fill=(48, 50, 60), outline=ACC if typed else None, width=3)
        d.text((70, 1465), 'канал'[:typed] + ('|' if typed < 5 else ''), font=font('b', 36), fill=TXT, anchor='lm')
        d.ellipse([W - 120, 1420, W - 30, 1510], fill=ACC if typed == 5 else (60, 62, 72))
        d.polygon([(W - 92, 1445), (W - 92, 1485), (W - 52, 1465)], fill=BG)
        save(im, 'phone_comment%d' % typed)


if __name__ == '__main__':
    phone_feed()
    phone_notes()
    mon_edit()
    mon_build()
    mon_styles()
    mon_call()
    phone_comments()
    print('UI ->', OUT, len(os.listdir(OUT)), 'files')
