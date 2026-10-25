import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
fs = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open(f).convert('RGB') for f in fs]
h = 640; row = [im.resize((int(im.width * h / im.height), h)) for im in ims]
cols = min(8, len(row)); W = row[0].width; rows = (len(row) + cols - 1) // cols
o = Image.new('RGB', (W * cols, h * rows), (40, 40, 40)); d = ImageDraw.Draw(o)
for i, (r, f) in enumerate(zip(row, fs)):
    x, y = (i % cols) * W, (i // cols) * h
    o.paste(r, (x, y)); d.text((x + 6, y + 6), os.path.basename(f)[:-4], fill=(255, 255, 0))
o.save(out, quality=86); print(o.size)
