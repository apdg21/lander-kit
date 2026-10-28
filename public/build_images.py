# REFERENCE IMAGE SCRIPT – composes all landing-page images from the generated scene images.
# Needs: Python 3 + Pillow + numpy (pip install pillow numpy). Fonts (Poppins) are downloaded automatically.
# Folder layout:  source/ = raw AI images (names below)   images/ = finished files for the page
#   source/product-raw.png   product alone on plain white (no text)          -> images/produkt.png (cut-out)
#   source/hero-base.png     main character using the product (person RIGHT, calm area LEFT)
#   source/before-after.png  ONE image split in two halves: left = before, right = after (same person)
#   source/mechanics.png     how it works (close-up / cut-away)            (skip if MECHANICS is not in the image plan)
#   source/material.png      OPTIONAL: product + close-up of its material(s) -> material.jpg (MATERIAL section)
#   source/step1.png step2.png step3.png   the 3 usage steps
#   source/expert.png        expert portrait (face upper middle)
#   source/testimonial.png   collage of happy customers with the product
#   source/closing.png       main character, happy result / offer mood
# Run:  python3 build_images.py      (edit CONFIG first – all on-image text lives here, NEVER in the AI image)
import os, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

CONFIG = {
    'name': 'Produktname',                     # wordmark for the logo (™ is added automatically)
    'accent': (235, 166, 40),                  # gold/amber badge colour  (#eba628)
    'navy': (15, 45, 83),                      # headline colour (#0f2d53)
    'before_label': 'VORHER', 'after_label': 'NACHHER',
    'mechanics_pills': ('Kurzer Satz zur Funktion', 'Zweiter Vorteil'),   # top-left / bottom-centre
    'material_pills': ('Name des Materials', 'Wichtigste Eigenschaft'),   # only used if source/material.png exists
    'steps': [('Titel Schritt 1', 'Zeile 1', 'Zeile 2'),
              ('Titel Schritt 2', 'Zeile 1', 'Zeile 2'),
              ('Titel Schritt 3', 'Zeile 1', 'Zeile 2')],
    'circle_labels': ('1  Schritt eins', '2  Schritt zwei', '3  Ergebnis'),  # hero GIF circle captions
    # crop boxes as fractions (left, top, right, bottom) of the source image – adjust after looking at the images
    'thumb_before': (0.04, 0.15, 0.46, 0.57), 'thumb_after': (0.54, 0.05, 0.96, 0.47),
    'circle_frames': [('step1.png', (0.25, 0.10, 0.85, 0.70)), ('step2.png', (0.25, 0.15, 0.85, 0.75)),
                      ('closing.png', (0.25, 0.02, 0.70, 0.47))],
    'expert_face': (0.5, 0.24, 0.17),         # avatar centre x, centre y, half-size (fractions)
    'cutout': True,                            # build images/produkt.png from source/product-raw.png
}
S, O, FD = 'source/', 'images/', 'fonts/'
os.makedirs(O, exist_ok=True); os.makedirs(FD, exist_ok=True)
for w in ('Regular', 'SemiBold', 'Bold', 'ExtraBold'):
    p = FD + f'Poppins-{w}.ttf'
    if not os.path.exists(p):
        urllib.request.urlretrieve(f'https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-{w}.ttf', p)
def font(w, s): return ImageFont.truetype(FD + f'Poppins-{w}.ttf', s)
GOLD, NAVY, BEIGE = CONFIG['accent'], CONFIG['navy'], (249, 246, 240)
def src(n): return Image.open(S + n).convert('RGB').resize((1024, 1024), Image.LANCZOS)
def fbox(b, W=1024, H=1024): return tuple(int(v * (W if i % 2 == 0 else H)) for i, v in enumerate(b))

# ---------- 1. product cut-out (transparent PNG) ----------
def cutout(path_in, path_out):
    im = Image.open(path_in).convert('RGB')
    try:                                        # best quality if rembg is installed
        from rembg import remove
        out = remove(im)
    except Exception:                           # fallback: light + smooth (low texture) + connected to border = background
        g = np.asarray(im.convert('L'), dtype=np.float64)
        def box(a, r=3):                        # mean filter via integral image
            p = np.pad(a, r + 1, mode='edge'); c = p.cumsum(0).cumsum(1); k = 2 * r + 1
            return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k])[:a.shape[0], :a.shape[1]] / (k * k)
        mean = box(g); std = np.sqrt(np.clip(box(g * g) - mean * mean, 0, None))
        rgb = np.asarray(im, dtype=np.int16); sat = rgb.max(2) - rgb.min(2)
        cand = ((g > 200) & (std < 4.0) & (sat < 18)).astype(np.uint8) * 255
        m = Image.fromarray(cand).copy()          # .copy(): fromarray can be read-only
        H, W = g.shape
        for x, y in [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1), (W // 2, 0), (W // 2, H - 1), (0, H // 2), (W - 1, H // 2)]:
            if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
        bg = (np.asarray(m) == 128).astype(np.uint8) * 255
        alpha = Image.fromarray(255 - bg).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
        out = im.convert('RGBA'); out.putalpha(alpha)
    out = out.crop(out.getbbox()); out.save(path_out); return out
prod = cutout(S + 'product-raw.png', O + 'produkt.png') if CONFIG['cutout'] else Image.open(O + 'produkt.png').convert('RGBA')
def fitp(h): return prod.resize((max(1, int(prod.width * h / prod.height)), h), Image.LANCZOS)

def pill(d, xy, text, f, bg, fg, pad=(18, 8), anchor='l'):
    x, y = xy; w = d.textlength(text, font=f); bb = f.getbbox(text); h = bb[3] - bb[1]
    if anchor == 'r': x -= (w + 2 * pad[0])
    if anchor == 'c': x -= (w + 2 * pad[0]) / 2
    d.rounded_rectangle((x, y, x + w + 2 * pad[0], y + h + 2 * pad[1] + 4), radius=(h + 2 * pad[1]) // 2, fill=bg)
    d.text((x + pad[0], y + pad[1] - bb[1] + 2), text, font=f, fill=fg)
def shadowed(base, img, pos, blur=14, off=(0, 12), alpha=100):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0)); a = img.split()[3].point(lambda v: v * alpha // 255)
    blk = Image.new('RGBA', img.size, (0, 0, 0, 255)); blk.putalpha(a); sh.paste(blk, (pos[0] + off[0], pos[1] + off[1]), blk)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur))); base.alpha_composite(img, pos)

# ---------- 2. section images ----------
ba = src('before-after.png').convert('RGBA'); d = ImageDraw.Draw(ba); f = font('Bold', 34)
pill(d, (28, 26), CONFIG['before_label'], f, (30, 30, 30, 230), (255, 255, 255))
pill(d, (996, 26), CONFIG['after_label'], f, GOLD + (255,), (255, 255, 255), anchor='r')
ba.convert('RGB').resize((1000, 1000), Image.LANCZOS).save(O + 'vorher-nachher.jpg', quality=88)

# mechanics + optional material image: same layout (2 label pills: top-left white, bottom-centre gold)
for srcname, pills, out in (('mechanics.png', 'mechanics_pills', 'mechanik.jpg'), ('material.png', 'material_pills', 'material.jpg')):
    if not os.path.exists(S + srcname):
        continue
    m = src(srcname).convert('RGBA'); d = ImageDraw.Draw(m); f = font('SemiBold', 27)
    pill(d, (40, 40), CONFIG[pills][0], f, (255, 255, 255, 235), NAVY)
    pill(d, (512, 935), CONFIG[pills][1], f, GOLD + (255,), (255, 255, 255), anchor='c')
    m.convert('RGB').resize((1000, 1000), Image.LANCZOS).save(O + out, quality=88)

st = Image.new('RGB', (1000, 1000), BEIGE); d = ImageDraw.Draw(st); rh = 310
for i, (t1, l1, l2) in enumerate(CONFIG['steps']):
    y = 25 + i * (rh + 12); ph = ImageOps.fit(Image.open(S + f'step{i+1}.png').convert('RGB'), (430, rh), centering=(0.5, 0.45))
    mk = Image.new('L', ph.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), radius=22, fill=255)
    d.rounded_rectangle((25, y, 975, y + rh), radius=22, fill=(255, 255, 255)); st.paste(ph, (25, y), mk)
    cx = 505; d.ellipse((cx, y + 52, cx + 76, y + 128), fill=GOLD); n = str(i + 1); fn = font('Bold', 44)
    d.text((cx + 38 - d.textlength(n, font=fn) / 2, y + 56), n, font=fn, fill=(255, 255, 255))
    d.text((cx, y + 150), t1, font=font('Bold', 36), fill=NAVY)
    d.text((cx, y + 206), l1, font=font('Regular', 25), fill=(70, 70, 70)); d.text((cx, y + 242), l2, font=font('Regular', 25), fill=(70, 70, 70))
st.save(O + 'schritte.jpg', quality=88)

ex = src('expert.png'); ex.resize((1000, 1000), Image.LANCZOS).save(O + 'experte.jpg', quality=88)
fx, fy, fr = CONFIG['expert_face']; c = (int(fx * 1024), int(fy * 1024)); r = int(fr * 1024)
ex.crop((c[0] - r, c[1] - r, c[0] + r, c[1] + r)).resize((200, 200), Image.LANCZOS).save(O + 'experte-avatar.jpg', quality=90)
for k, n in [('testimonial.png', 'testimonial'), ('closing.png', 'abschluss')]:
    src(k).resize((1000, 1000), Image.LANCZOS).save(O + n + '.jpg', quality=88)

# ---------- 3. bundles (product only, NO box), sticky image, text logo ----------
def bundle(n):
    W = 1000; g = np.linspace(0, 1, W)[:, None]; top = np.array([250, 247, 241]); bot = np.array([232, 225, 212])
    bg = Image.fromarray(np.repeat((top + (bot - top) * g[..., None]).astype('uint8'), W, axis=1)).convert('RGBA')
    h = {1: 760, 2: 700, 3: 650, 5: 580}[n]; t = fitp(h)
    if t.width > 700: t = t.resize((700, int(t.height * 700 / t.width)), Image.LANCZOS); h = t.height
    step = {1: 0, 2: int(t.width * 0.45), 3: int(t.width * 0.36), 5: int(t.width * 0.26)}[n]
    total = t.width + step * (n - 1)
    if total > 900: step = (900 - t.width) // max(1, n - 1); total = t.width + step * (n - 1)
    x0 = (W - total) // 2; y0 = (W - h) // 2 + 30
    for i in range(n): shadowed(bg, t, (x0 + i * step, y0 - int(i * step * 0.15)), blur=16, off=(0, 14), alpha=80)
    if n > 1:
        d = ImageDraw.Draw(bg); d.ellipse((815, 40, 955, 180), fill=GOLD); fn = font('Bold', 58); s = f'{n}x'
        d.text((885 - d.textlength(s, font=fn) / 2, 70), s, font=fn, fill=(255, 255, 255))
    bg.convert('RGB').save(O + f'paket-{n}x.jpg', quality=90)
for n in (1, 2, 3, 5): bundle(n)
sk = Image.new('RGBA', (400, 400), (0, 0, 0, 0)); t = fitp(390)
if t.width > 390: t = t.resize((390, int(t.height * 390 / t.width)), Image.LANCZOS)
sk.alpha_composite(t, ((400 - t.width) // 2, (400 - t.height) // 2)); sk.save(O + 'sticky.png')
lg = Image.new('RGBA', (1400, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(lg); fb = font('ExtraBold', 118)
d.ellipse((10, 70, 80, 140), fill=GOLD); d.text((105, 30), CONFIG['name'], font=fb, fill=NAVY)
w = d.textlength(CONFIG['name'], font=fb); d.text((105 + w + 4, 48), '™', font=font('Bold', 34), fill=NAVY)
lg = lg.crop(lg.getbbox()); lg.save(O + 'logo.png')

# ---------- 4. animated hero: before/after thumbnails + looping circle + product + main character ----------
base = src('hero-base.png').convert('RGBA'); bas = src('before-after.png')
def thumb(box, label, bg):
    im = ImageOps.fit(bas.crop(fbox(box)), (196, 196)); card = Image.new('RGBA', (208, 208), (255, 255, 255, 255)); card.paste(im, (6, 6))
    d = ImageDraw.Draw(card); f = font('Bold', 19); w = d.textlength(label, font=f)
    d.rounded_rectangle((104 - w / 2 - 12, 170, 104 + w / 2 + 12, 200), radius=14, fill=bg); d.text((104 - w / 2, 171), label, font=f, fill=(255, 255, 255)); return card
def drop(b, card, pos):
    sh = Image.new('RGBA', b.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((pos[0] + 4, pos[1] + 8, pos[0] + card.width + 4, pos[1] + card.height + 8), radius=8, fill=(0, 0, 0, 120))
    b.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); b.alpha_composite(card, pos)
static = base.copy()
drop(static, thumb(CONFIG['thumb_before'], CONFIG['before_label'], (30, 30, 30, 235)), (26, 26))
drop(static, thumb(CONFIG['thumb_after'], CONFIG['after_label'], GOLD + (255,)), (250, 26))
d = ImageDraw.Draw(static); d.ellipse((216, 108, 260, 152), fill=(255, 255, 255)); d.polygon([(229, 118), (229, 142), (250, 130)], fill=GOLD)
pt = fitp(330)
if pt.width > 300: pt = pt.resize((300, int(pt.height * 300 / pt.width)), Image.LANCZOS)
shadowed(static, pt, (18, 1024 - pt.height - 30), blur=16, off=(0, 14), alpha=110)
D = 236; cx, cy = 30, 282
frames = [ImageOps.fit(src(fn).crop(fbox(b)), (D, D)) for fn, b in CONFIG['circle_frames']]
mask = Image.new('L', (D * 4, D * 4), 0); ImageDraw.Draw(mask).ellipse((0, 0, D * 4 - 1, D * 4 - 1), fill=255); mask = mask.resize((D, D), Image.LANCZOS)
ring = Image.new('RGBA', (D + 20, D + 20), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring); rd.ellipse((0, 0, D + 19, D + 19), fill=GOLD + (255,)); rd.ellipse((5, 5, D + 14, D + 14), fill=(255, 255, 255, 255))
sh = Image.new('RGBA', static.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((cx + 2, cy + 10, cx + D + 22, cy + D + 30), fill=(0, 0, 0, 110))
static.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); static.alpha_composite(ring, (cx, cy))
labels = CONFIG['circle_labels']
def render(img, label):
    fr = static.copy(); fr.paste(img, (cx + 10, cy + 10), mask); d = ImageDraw.Draw(fr); f = font('SemiBold', 18); w = d.textlength(label, font=f); x = cx + 10 + D / 2 - w / 2 - 14
    d.rounded_rectangle((x, cy + D - 14, x + w + 28, cy + D + 16), radius=15, fill=GOLD); d.text((x + 14, cy + D - 12), label, font=f, fill=(255, 255, 255))
    return fr.convert('RGB').resize((1000, 1000), Image.LANCZOS)
out, dur = [], []
for i in range(3):                              # hold each frame 1.3 s, short cross-fade to the next
    a, b = frames[i], frames[(i + 1) % 3]; out.append(render(a, labels[i])); dur.append(1300)
    for k in (1, 2, 3): out.append(render(Image.blend(a, b, k / 4), labels[i] if k < 2 else labels[(i + 1) % 3])); dur.append(90)
out[0].save(O + 'hauptbild.webp', save_all=True, append_images=out[1:], duration=dur, loop=0, quality=82, method=4)
pal = out[0].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in out]
g[0].save(O + 'hauptbild.gif', save_all=True, append_images=g[1:], duration=dur, loop=0, optimize=True)
out[0].save(O + 'hauptbild-vorschau.jpg', quality=85)
print('done – check every file in images/ visually (contact sheet) before building the page')
