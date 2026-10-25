"""Apply the profile supplied by the user; preserve the original screenshot pixels."""
import base64
import json
import io
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image

P = Path(__file__).resolve().parent
ENGINE = P.parents[2]
SOURCE = Path(r"C:\Users\Gigabyte\Pictures\Screenshots\Снимок экрана 2026-10-21 000537.png")
BRAND = ENGINE / "public" / "brand"
BRAND.mkdir(exist_ok=True)
uri = "data:image/png;base64," + base64.b64encode(SOURCE.read_bytes()).decode("ascii")
with Image.open(SOURCE) as source:
    source_w, source_h = source.size
    avatar_pixels = source.crop((83, 9, 256, 182))
    avatar_pixels.save(BRAND / "aipollon-avatar.png")
    avatar_buffer = io.BytesIO()
    avatar_pixels.save(avatar_buffer, format="PNG")
avatar_uri = "data:image/png;base64," + base64.b64encode(avatar_buffer.getvalue()).decode("ascii")

# SVG viewports and clip paths display the original image without retouching it.
avatar = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="83 9 173 173">
<image href="{uri}" x="0" y="0" width="{source_w}" height="{source_h}"/>
</svg>'''
(BRAND / "aipollon-avatar.svg").write_text(avatar, encoding="utf-8")

profile = f'''<svg xmlns="http://www.w3.org/2000/svg" width="390" height="844" viewBox="0 0 390 844">
<defs><clipPath id="avatar"><circle cx="195" cy="184" r="65"/></clipPath></defs>
<rect width="390" height="844" fill="#080808"/>
<g fill="#f4f1ee" font-family="Arial, sans-serif">
<text x="30" y="31" font-size="14" font-weight="700">00:05</text>
<text x="195" y="83" font-size="24" font-weight="700" text-anchor="middle">Aipollon</text>
<text x="28" y="84" font-size="30">‹</text><text x="348" y="82" font-size="25">☰</text>
<g clip-path="url(#avatar)"><image href="{avatar_uri}" x="130" y="119" width="130" height="130"/></g>
<text x="195" y="281" font-size="21" font-weight="700" text-anchor="middle">@videopollon</text>
<g text-anchor="middle"><text x="78" y="321" font-size="23" font-weight="700">0</text><text x="195" y="321" font-size="23" font-weight="700">0</text><text x="312" y="321" font-size="23" font-weight="700">0</text>
<g fill="#aaa7a3" font-size="12"><text x="78" y="342">Подписки</text><text x="195" y="342">Подписчики</text><text x="312" y="342">Лайки</text></g></g>
<rect x="58" y="366" width="274" height="45" rx="10" fill="#252525"/>
<text x="195" y="394" font-size="17" font-weight="700" text-anchor="middle">Изменить профиль</text>
<g text-anchor="middle" font-size="18"><text x="195" y="451">Возможность делать самые</text><text x="195" y="477">качественные инфоролики</text><text x="195" y="503">вместе с ИИ 👇🏻</text></g>
<rect x="28" y="525" width="334" height="54" rx="12" fill="#1f1510" stroke="#df8b56" stroke-width="2"/>
<text x="195" y="560" text-anchor="middle" font-size="23" font-weight="700" fill="#eda56f">t.me/aipollonvideo</text>
<line x1="0" y1="624" x2="390" y2="624" stroke="#292929"/>
<g font-size="14" text-anchor="middle"><text x="65" y="611" font-weight="700">Видео</text><text x="195" y="611" fill="#999">Избранное</text><text x="325" y="611" fill="#999">Лайки</text></g>
<line x1="28" y1="624" x2="102" y2="624" stroke="#f1eeea" stroke-width="3"/>
<rect x="132" y="817" width="126" height="4" rx="2" fill="#efedeb"/>
</g></svg>'''
(BRAND / "aipollon-profile.svg").write_text(profile, encoding="utf-8")

brand_file = ENGINE / "src" / "brand.json"
brand = json.loads(brand_file.read_text(encoding="utf-8"))
brand.update({"name": "Aipollon", "handle": "videopollon", "badge": "", "bio": "Возможность делать самые качественные инфоролики вместе с ИИ 👇🏻", "link": "https://t.me/aipollonvideo", "avatar": "brand/aipollon-avatar.png"})
brand_file.write_text(json.dumps(brand, ensure_ascii=False, indent=1), encoding="utf-8")

# Only caption presentation changes; the narration and its word timings stay intact.
words_file = P / "words.json"
words = json.loads(words_file.read_text(encoding="utf-8"))
words["cards"][-1].update({"mode": "editorial", "pos": "top"})
words_file.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
print("Updated Aipollon profile, original avatar, bio and Telegram link")
