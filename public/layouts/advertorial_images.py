# REFERENCE IMAGE SCRIPT – layout "ADVERTORIAL"
# Needs: Python 3 + Pillow + numpy  (pip install pillow numpy)
# Input  (source/):  product-raw.png (product alone on a plain background – white/black/flat colour – or transparent PNG)
#                    hero-1.png, s1.png, s2.png, s3.png, abschluss.png, review-01..03.png (generated scenes)
#                    optional: other.png (generic "other solution" object for the comparison table)
# Output (images/):  produkt.png (transparent cut-out) · hero-1.jpg · hero-2.jpg (product on white)
#                    s1.jpg · s2.jpg · s3.jpg · abschluss.jpg · review-01..03.jpg
#                    paket-1x / 2x / 3x / 5x.jpg · vergleich-andere.png · logo.png (text logo, optional)
# The page itself adds: the product badge on every section image, the ✗ / ✓ marks on s2.jpg,
# stars, prices – so NO text goes into any image.
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CONFIG = {
    'product_name': 'Produkt™',          # used for the optional text logo
    'brand_color': (35, 55, 198),        # = button colour of the page (RGB)
    'make_logo': True,                    # False if you already have a logo.png
    'logo_font': None,                    # path to a bold .ttf (e.g. Outfit-Bold.ttf); None = default font
    'bg_tolerance': 28,                   # how far a pixel may differ from the background colour (0-255)
}
SRC, OUT = 'source', 'images'
os.makedirs(OUT, exist_ok=True)


def cutout(path):
    """Remove a plain background (white, black or any flat colour – taken from the image border):
    flood-fill from the borders with a colour tolerance, soft edge. Transparent PNGs are kept as they are."""
    im = Image.open(path)
    if im.mode in ('RGBA', 'LA') and np.asarray(im.convert('RGBA'))[..., 3].min() < 20:
        im = im.convert('RGBA'); return im.crop(im.getbbox())
    im = im.convert('RGB'); a = np.asarray(im).astype(np.int16)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    ref = np.median(border, axis=0)
    near = np.abs(a - ref).max(axis=2) <= CONFIG['bg_tolerance']
    h, w = near.shape
    bg = np.zeros_like(near)
    stack = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
    while stack:                                   # iterative flood fill (only background connected to the border)
        y, x = stack.pop()
        if 0 <= y < h and 0 <= x < w and near[y, x] and not bg[y, x]:
            bg[y, x] = True
            stack.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    alpha = Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    out = im.convert('RGBA'); out.putalpha(alpha)
    return out.crop(out.getbbox())


def square_jpg(src, dst, size=1080, quality=86):
    im = Image.open(src).convert('RGB'); w, h = im.size; s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)
    im.save(dst, quality=quality, optimize=True)


def on_canvas(prod, size, bg, scale=0.78, shadow=True):
    c = bg.copy() if isinstance(bg, Image.Image) else Image.new('RGB', (size, size), bg)
    p = prod.copy(); p.thumbnail((int(size * scale), int(size * scale)), Image.LANCZOS)
    x, y = (size - p.width) // 2, (size - p.height) // 2
    if shadow:
        sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
        d.ellipse((x + p.width * .1, y + p.height * .92, x + p.width * .9, y + p.height * 1.04), fill=(0, 0, 0, 70))
        c = Image.alpha_composite(c.convert('RGBA'), sh.filter(ImageFilter.GaussianBlur(size // 40))).convert('RGB')
    c.paste(p, (x, y), p)
    return c


def gradient(size, color):
    r, g, b = color
    top = (int(r * .35), int(g * .35), int(b * .35)); bot = (int(r * .9), int(g * .9), int(b * .9))
    arr = np.zeros((size, size, 3), np.uint8)
    for i, t in enumerate(np.linspace(0, 1, size)):
        arr[i] = [int(top[k] + (bot[k] - top[k]) * t) for k in range(3)]
    im = Image.fromarray(arr)
    glow = Image.new('L', (size, size), 0); ImageDraw.Draw(glow).ellipse((size * .15, size * .1, size * .85, size * .8), fill=120)
    return Image.composite(Image.new('RGB', (size, size), (255, 255, 255)), im, glow.filter(ImageFilter.GaussianBlur(size // 6)))


def bundle(prod, n, size=800):
    """n products fanned out on a brand-colour gradient (no box, no text)."""
    bg = gradient(size, CONFIG['brand_color']).convert('RGBA')
    cols = {1: 1, 2: 2, 3: 3, 5: 3}[n]
    p = prod.copy(); p.thumbnail((int(size * {1: .66, 2: .5, 3: .4, 5: .34}[n]),) * 2, Image.LANCZOS)
    pos = {1: [(0, 0)], 2: [(-.17, -.04), (.17, .04)], 3: [(-.25, .03), (0, -.03), (.25, .03)],
           5: [(-.26, -.16), (0, -.2), (.26, -.16), (-.13, .16), (.13, .16)]}[n]
    for i, (dx, dy) in enumerate(pos):
        q = p.rotate((i - (len(pos) - 1) / 2) * -6, expand=True, resample=Image.BICUBIC)
        x = int(size / 2 + dx * size - q.width / 2); y = int(size / 2 + dy * size - q.height / 2)
        sh = Image.new('RGBA', bg.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 90), (x + 8, y + 12), q)
        bg = Image.alpha_composite(bg, sh.filter(ImageFilter.GaussianBlur(10)))
        bg.alpha_composite(q, (max(0, x), max(0, y)))
    return bg.convert('RGB')


def text_logo(name, color):
    try: f = ImageFont.truetype(CONFIG['logo_font'], 120) if CONFIG['logo_font'] else ImageFont.load_default(size=120)
    except Exception: f = ImageFont.load_default()
    tmp = Image.new('RGBA', (10, 10)); bb = ImageDraw.Draw(tmp).textbbox((0, 0), name, font=f)
    im = Image.new('RGBA', (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), name, font=f, fill=color + (255,))
    return im


if __name__ == '__main__':
    prod = cutout(os.path.join(SRC, 'product-raw.png'))
    prod.save(os.path.join(OUT, 'produkt.png'))
    on_canvas(prod, 1080, (255, 255, 255)).save(os.path.join(OUT, 'hero-2.jpg'), quality=88)
    for name in ['hero-1', 's1', 's2', 's3', 'abschluss']:
        p = os.path.join(SRC, name + '.png')
        if os.path.exists(p): square_jpg(p, os.path.join(OUT, name + '.jpg'))
    for i in (1, 2, 3):
        p = os.path.join(SRC, f'review-{i:02d}.png')
        if os.path.exists(p): square_jpg(p, os.path.join(OUT, f'review-{i:02d}.jpg'), size=800, quality=82)
    for n in (1, 2, 3, 5):
        bundle(prod, n).save(os.path.join(OUT, f'paket-{n}x.jpg'), quality=86)
    if os.path.exists(os.path.join(SRC, 'other.png')):
        cutout(os.path.join(SRC, 'other.png')).save(os.path.join(OUT, 'vergleich-andere.png'))
    if CONFIG['make_logo']:
        text_logo(CONFIG['product_name'], CONFIG['brand_color']).save(os.path.join(OUT, 'logo.png'))
    print('done →', sorted(os.listdir(OUT)))
