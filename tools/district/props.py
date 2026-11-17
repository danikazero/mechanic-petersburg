"""Prop sprites. Each prop: (RGBA image, anchor (foot point), solid rect relative to anchor or None)."""
import random, math, os
import numpy as np
from PIL import Image, ImageDraw
from common import shade, mix, add
import pixfont

OBJ = None
SCALE = 1.45

def load(path):
    global OBJ
    OBJ = Image.open(path).convert('RGBA')

def cut(region, scale=SCALE):
    x, y, w, h = region
    im = OBJ.crop((x, y, x + w, y + h))
    return im.resize((round(w * scale), round(h * scale)), Image.NEAREST)

def shadow_ellipse(d, cx, cy, rx, ry, a=90):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(10, 12, 16, a))

def with_shadow(im, rx, ry, a=80, dy=0):
    out = Image.new('RGBA', (im.width, im.height + ry), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    shadow_ellipse(d, im.width // 2, im.height - 2 + dy, rx, ry, a)
    out.alpha_composite(im, (0, 0))
    return out

def recolor_tree(im, mode):
    a = np.array(im).astype(np.float64)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    leaf = (g > r * 1.02) & (g > b * 1.2) & (al > 0)
    if mode == 'autumn':
        a[leaf, 0] = np.clip(g[leaf] * 1.18 + 20, 0, 255)
        a[leaf, 1] = np.clip(g[leaf] * 0.92, 0, 255)
        a[leaf, 2] = np.clip(b[leaf] * 0.6, 0, 255)
    elif mode == 'dark':
        a[leaf, 0] *= 0.8; a[leaf, 1] *= 0.86; a[leaf, 2] *= 0.9
    elif mode == 'yellow':
        a[leaf, 0] = np.clip(g[leaf] * 1.05 + 10, 0, 255)
        a[leaf, 1] = np.clip(g[leaf] * 1.0, 0, 255)
        a[leaf, 2] = np.clip(b[leaf] * 0.5, 0, 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

# ------------------------------------------------------------------ cars
CAR_COLORS = {'white': (226, 226, 222), 'silver': (170, 176, 182), 'blue': (52, 78, 132), 'red': (170, 44, 40),
              'black': (46, 48, 54), 'taxi': (232, 190, 50), 'green': (70, 110, 84), 'beige': (200, 180, 140)}

def car(color, kind='sedan'):
    c = CAR_COLORS[color]
    W, Hh = 140, 72
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, 70, 62, 66, 9, 110)
    dark, light, outl = shade(c, 0.72), shade(c, 1.15), shade(c, 0.42)
    body_top, body_bot = 32, 58
    cab_top = 10 if kind == 'sedan' else 6
    # cabin
    if kind == 'sedan':
        cab = [(30, body_top + 1), (46, cab_top), (96, cab_top), (114, body_top + 1)]
    else:  # hatch / suv
        cab = [(18, body_top + 1), (24, cab_top), (100, cab_top), (118, body_top + 1)]
    d.polygon(cab, fill=c, outline=outl)
    # roof top surface seen from above (3/4)
    d.line([(cab[1][0] + 1, cab_top + 1), (cab[2][0] - 1, cab_top + 1)], fill=shade(c, 1.3))
    d.line([(cab[1][0] + 1, cab_top + 2), (cab[2][0] - 1, cab_top + 2)], fill=light)
    # windows
    gx0, gx1 = cab[1][0] + 3, cab[2][0] - 3
    win = [(cab[0][0] + 7, body_top - 1), (gx0 + 2, cab_top + 5), (gx1 - 2, cab_top + 5), (cab[3][0] - 7, body_top - 1)]
    d.polygon(win, fill=(58, 72, 90))
    mid = (win[1][0] + win[2][0]) // 2
    d.polygon([(win[1][0] + 4, cab_top + 6), (win[1][0] + 14, cab_top + 6), (win[0][0] + 14, body_top - 2), (win[0][0] + 6, body_top - 2)], fill=(120, 144, 166))
    d.line([(mid, cab_top + 5), (mid, body_top - 1)], fill=dark, width=3)
    # body
    d.rounded_rectangle([2, body_top, W - 3, body_bot], radius=8, fill=c, outline=outl)
    d.line([(6, body_top + 2), (W - 8, body_top + 2)], fill=shade(c, 1.25))
    d.line([(6, body_top + 3), (W - 8, body_top + 3)], fill=light)
    d.line([(4, body_top + 14), (W - 5, body_top + 14)], fill=dark)
    d.rectangle([4, body_bot - 7, W - 5, body_bot - 2], fill=dark)
    # doors
    for x in (cab[0][0] + 20, mid + 2):
        d.line([(x, body_top + 1), (x, body_bot - 4)], fill=outl)
    for x in (cab[0][0] + 38, mid + 18):
        d.rectangle([x, body_top + 6, x + 6, body_top + 7], fill=shade(c, 0.55))
    # lights & bumpers
    d.rectangle([W - 8, body_top + 5, W - 4, body_top + 10], fill=(255, 244, 200))
    d.rectangle([3, body_top + 5, 6, body_top + 10], fill=(210, 40, 40))
    d.rectangle([0, body_bot - 8, 8, body_bot - 3], fill=(50, 50, 56))
    d.rectangle([W - 10, body_bot - 8, W - 1, body_bot - 3], fill=(50, 50, 56))
    # wheel arches + wheels
    for wx in (30, 110):
        d.ellipse([wx - 15, body_bot - 15, wx + 15, body_bot + 15], fill=(24, 24, 28))
        d.ellipse([wx - 12, body_bot - 11, wx + 12, body_bot + 11], fill=(36, 36, 40))
        d.ellipse([wx - 7, body_bot - 6, wx + 7, body_bot + 6], fill=(150, 152, 158))
        d.ellipse([wx - 3, body_bot - 2, wx + 3, body_bot + 2], fill=(92, 94, 100))
        d.point((wx - 4, body_bot - 4), fill=(210, 212, 216))
    if color == 'taxi':
        d.rectangle([60, cab_top - 6, 80, cab_top - 1], fill=(250, 220, 90), outline=(80, 60, 20))
        for x in range(8, W - 10, 8):
            d.rectangle([x, body_top + 16, x + 3, body_top + 19], fill=(30, 30, 30))
    return im, (70, 64), (-66, -16, 132, 18)

def tram():
    W, Hh = 520, 132
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, W // 2, Hh - 8, W // 2 - 6, 10, 120)
    red, cream, grey = (178, 38, 40), (232, 226, 208), (110, 114, 120)
    top, bot = 26, Hh - 16
    # roof (seen from above)
    d.rounded_rectangle([14, top - 14, W - 15, top + 6], radius=10, fill=(150, 154, 160))
    d.line([(20, top - 12), (W - 20, top - 12)], fill=(196, 198, 202))
    # pantograph
    px0 = W // 2 - 30
    d.rectangle([px0, top - 18, px0 + 60, top - 12], fill=(70, 72, 78))
    d.line([(px0 + 10, top - 18), (px0 + 30, top - 40), (px0 + 50, top - 18)], fill=(40, 40, 46), width=2)
    d.line([(px0 + 16, top - 40), (px0 + 44, top - 40)], fill=(40, 40, 46), width=2)
    # body
    d.rounded_rectangle([6, top, W - 7, bot], radius=14, fill=red, outline=(90, 20, 22))
    d.rectangle([8, top + 4, W - 9, top + 44], fill=cream)
    d.line([(8, top + 3), (W - 9, top + 3)], fill=(240, 120, 110))
    # windows band
    for x in range(30, W - 40, 40):
        d.rectangle([x, top + 8, x + 32, top + 40], fill=(54, 66, 84))
        d.polygon([(x + 2, top + 9), (x + 12, top + 9), (x + 2, top + 26)], fill=(116, 138, 160))
        d.line([(x, top + 18), (x + 32, top + 18)], fill=(180, 176, 166))
    # cab windows
    d.rounded_rectangle([W - 34, top + 8, W - 12, top + 46], radius=6, fill=(60, 74, 92))
    d.rounded_rectangle([11, top + 8, 30, top + 46], radius=6, fill=(60, 74, 92))
    # route board
    d.rectangle([W - 32, top - 2, W - 12, top + 6], fill=(20, 20, 20))
    pixfont.draw(d, W - 26, top - 1, '3', (255, 170, 60))
    # doors
    for x in (60, 236, 412):
        d.rectangle([x, top + 6, x + 44, bot - 2], fill=(60, 60, 66))
        d.rectangle([x + 3, top + 9, x + 20, bot - 8], fill=(70, 86, 106))
        d.rectangle([x + 24, top + 9, x + 41, bot - 8], fill=(70, 86, 106))
        d.line([(x + 22, top + 6), (x + 22, bot - 2)], fill=(40, 40, 44))
    d.line([(8, top + 66), (W - 9, top + 66)], fill=(130, 24, 26))
    pixfont.draw(d, 120, top + 52, 'ГОРЭЛЕКТРОТРАНС', (240, 230, 210), shadow=(100, 20, 20))
    # skirt + bogies
    d.rectangle([12, bot - 6, W - 13, bot], fill=(60, 60, 64))
    for x in (90, W - 90):
        d.rectangle([x - 34, bot - 4, x + 34, bot + 8], fill=(36, 36, 40))
        for wx in (x - 20, x + 20):
            d.ellipse([wx - 9, bot - 4, wx + 9, bot + 12], fill=(30, 30, 34))
            d.ellipse([wx - 4, bot + 1, wx + 4, bot + 7], fill=(120, 120, 126))
    d.rectangle([W - 8, top + 50, W - 4, top + 58], fill=(255, 240, 190))
    return im, (W // 2, Hh - 8), (-W // 2 + 6, -22, W - 12, 24)

def tram_stop():
    W, Hh = 200, 130
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, W // 2, Hh - 8, 96, 8, 70)
    d.rectangle([10, 22, W - 10, 28], fill=(70, 74, 82))
    d.rectangle([10, 14, W - 10, 22], fill=(110, 116, 124))
    d.line([(10, 14), (W - 10, 14)], fill=(170, 176, 182))
    for x in (14, W - 18):
        d.rectangle([x, 28, x + 4, Hh - 10], fill=(60, 62, 68))
    # glass back panel
    d.rectangle([20, 30, W - 22, Hh - 26], fill=(130, 160, 176, 120))
    d.line([(20, 30), (W - 22, 30)], fill=(200, 220, 230, 200))
    d.rectangle([24, 36, 70, 92], fill=(220, 120, 60, 230))
    pixfont.draw(d, 30, 44, 'ТЕАТР', (255, 255, 255))
    pixfont.draw(d, 30, 56, 'СЕГОДНЯ', (255, 240, 200))
    # bench
    d.rectangle([80, Hh - 40, W - 30, Hh - 34], fill=(120, 82, 52))
    d.rectangle([84, Hh - 34, 88, Hh - 14], fill=(50, 50, 56))
    d.rectangle([W - 38, Hh - 34, W - 34, Hh - 14], fill=(50, 50, 56))
    # sign
    d.rectangle([W - 40, 0, W - 12, 14], fill=(255, 255, 255), outline=(30, 60, 140))
    pixfont.draw(d, W - 30, 4, 'Т', (30, 60, 140))
    pixfont.draw(d, 92, 34, 'ЗАГОРОДНЫЙ', (30, 40, 60))
    return im, (W // 2, Hh - 10), (-W // 2 + 12, -14, W - 24, 16)

def urn():
    im = Image.new('RGBA', (26, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, 13, 36, 11, 4, 90)
    d.polygon([(5, 10), (21, 10), (18, 34), (8, 34)], fill=(58, 74, 66))
    d.line([(6, 11), (9, 33)], fill=(90, 110, 98))
    d.ellipse([4, 6, 22, 14], fill=(70, 88, 78))
    d.ellipse([7, 8, 19, 12], fill=(24, 26, 26))
    d.rectangle([7, 33, 19, 36], fill=(40, 50, 46))
    return im, (13, 36), (-9, -6, 18, 8)

def ad_column():
    W, Hh = 64, 150
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, 32, Hh - 6, 30, 7, 90)
    d.rectangle([8, 26, W - 9, Hh - 10], fill=(60, 74, 70))
    posters = [(214, 196, 150), (180, 60, 50), (60, 80, 130), (230, 220, 200), (200, 150, 60)]
    y = 32
    rr = random.Random(3)
    while y < Hh - 22:
        h = rr.randint(18, 30)
        c = rr.choice(posters)
        d.rectangle([10, y, W - 11, min(Hh - 16, y + h)], fill=c)
        for k in range(3):
            d.line([(14, y + 5 + k * 5), (W - 16 - rr.randint(0, 14), y + 5 + k * 5)], fill=shade(c, 0.6))
        y += h + 2
    # cylindrical shading
    a = np.array(im).astype(np.float64)
    for x in range(8, W - 8):
        f = 0.75 + 0.45 * math.sin(math.pi * (x - 8) / (W - 16)) - 0.12 * (x - 8) / (W - 16)
        a[26:Hh - 10, x, :3] *= f
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(im)
    d.ellipse([2, 10, W - 3, 32], fill=(70, 86, 80))
    d.ellipse([6, 4, W - 7, 22], fill=(84, 104, 96))
    d.ellipse([24, 0, 40, 10], fill=(96, 118, 108))
    d.rectangle([4, Hh - 14, W - 5, Hh - 6], fill=(50, 62, 58))
    return im, (32, Hh - 6), (-24, -10, 48, 12)

def kiosk(text, bg):
    W, Hh = 150, 120
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, W // 2, Hh - 8, 72, 8, 90)
    d.rectangle([6, 8, W - 7, 26], fill=shade(bg, 0.8))
    d.rectangle([4, 4, W - 5, 10], fill=(200, 200, 196))
    tw = pixfont.width(text)
    pixfont.draw(d, W // 2 - tw // 2, 13, text, (255, 240, 200), shadow=shade(bg, 0.5))
    d.rectangle([10, 26, W - 11, Hh - 12], fill=(222, 218, 206))
    d.rectangle([18, 34, W - 19, 74], fill=(240, 196, 120))
    for x in range(26, W - 26, 18):
        d.rectangle([x, 50, x + 10, 72], fill=rr_c(x))
    d.line([(18, 74), (W - 19, 74)], fill=(120, 110, 100), width=2)
    d.rectangle([14, 76, W - 15, 82], fill=(170, 166, 156))
    d.rectangle([10, Hh - 16, W - 11, Hh - 10], fill=(90, 90, 96))
    return im, (W // 2, Hh - 10), (-W // 2 + 10, -16, W - 20, 18)

def rr_c(x):
    return [(200, 60, 50), (240, 230, 210), (90, 140, 60), (230, 180, 60)][(x // 18) % 4]

def bronze_shade(im, mask, base, hi, mid, lo, outline):
    a = np.array(im)
    m = mask
    up = np.roll(m, 1, axis=0); left = np.roll(m, 1, axis=1)
    down = np.roll(m, -1, axis=0); right = np.roll(m, -1, axis=1)
    a[m, :3] = base
    ys = np.indices(m.shape)[0]
    a[m & (ys % 2 == 0) & (np.indices(m.shape)[1] % 4 == 0), :3] = mid
    up2 = np.roll(m, 2, axis=0); left2 = np.roll(m, 2, axis=1)
    a[m & (~up2 | ~left2), :3] = mid
    a[m & (~up | ~left), :3] = hi
    a[m & (~down2_(m) | ~np.roll(m, -2, axis=1)), :3] = lo
    a[m & (~down | ~right), :3] = outline
    a[m, 3] = 255
    return Image.fromarray(a, 'RGBA')

def down2_(m):
    return np.roll(m, -2, axis=0)

def limb(d, p0, p1, w):
    d.line([p0, p1], fill=255, width=w)
    r = w // 2
    for p in (p0, p1):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)

def statue_horse(flip=False):
    """Anichkov bridge horse tamer: granite pedestal + bronze group."""
    W, Hh = 120, 200
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, W // 2, Hh - 8, 56, 9, 100)
    # pedestal (granite, two steps)
    d.rectangle([4, Hh - 20, W - 5, Hh - 8], fill=(132, 106, 100))
    d.line([(4, Hh - 20), (W - 5, Hh - 20)], fill=(170, 142, 134))
    d.rectangle([14, 112, W - 15, Hh - 20], fill=(120, 96, 90))
    d.rectangle([10, 104, W - 11, 114], fill=(150, 124, 116))
    d.line([(10, 104), (W - 11, 104)], fill=(186, 158, 148))
    d.line([(14, 115), (W - 15, 115)], fill=(92, 72, 68))
    d.rectangle([26, 124, W - 27, 166], outline=(104, 82, 78))
    d.line([(W - 16, 112), (W - 16, Hh - 20)], fill=(96, 76, 72))
    # bronze group as a mask
    m = Image.new('L', (W, Hh), 0)
    md = ImageDraw.Draw(m)
    # horse rearing to the right
    md.polygon([(34, 74), (46, 58), (70, 46), (86, 44), (92, 56), (78, 72), (50, 84), (36, 86)], fill=255)  # barrel
    limb(md, (84, 50), (96, 26), 13)          # neck
    md.polygon([(92, 16), (104, 14), (114, 30), (110, 36), (100, 32), (92, 28)], fill=255)  # head
    md.polygon([(95, 16), (97, 6), (100, 15)], fill=255)    # ear
    md.polygon([(84, 30), (90, 14), (94, 20), (88, 40)], fill=255)  # mane
    limb(md, (86, 58), (100, 54), 6); limb(md, (100, 54), (104, 66), 5)   # raised foreleg
    limb(md, (80, 64), (92, 70), 6); limb(md, (92, 70), (94, 80), 5)
    limb(md, (40, 80), (32, 92), 8); limb(md, (32, 92), (36, 104), 6)     # hind legs
    limb(md, (52, 82), (50, 94), 7); limb(md, (50, 94), (54, 104), 6)
    md.polygon([(36, 72), (24, 80), (16, 98), (22, 100), (30, 86), (40, 80)], fill=255)  # tail
    # tamer pulling the bridle, leaning back
    md.ellipse([22, 30, 34, 42], fill=255)                     # head
    md.polygon([(22, 42), (34, 42), (40, 70), (26, 74), (18, 56)], fill=255)  # torso
    limb(md, (32, 46), (60, 40), 5); limb(md, (60, 40), (96, 30), 4)        # arm + rein
    limb(md, (24, 50), (14, 64), 5)
    limb(md, (28, 72), (16, 104), 7); limb(md, (36, 72), (44, 104), 7)      # legs
    mask = np.array(m) > 0
    im = bronze_shade(im, mask, (52, 60, 50), (122, 138, 110), (78, 90, 72), (40, 46, 38), (22, 26, 22))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im, (W // 2, Hh - 8), (-W // 2 + 6, -26, W - 12, 26)

def dovlatov():
    """Bronze figure standing next to a doorway frame, low granite plinth, plaque."""
    W, Hh = 120, 156
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, W // 2, Hh - 8, 56, 8, 90)
    d.rectangle([6, Hh - 22, W - 7, Hh - 8], fill=(118, 108, 104))
    d.line([(6, Hh - 22), (W - 7, Hh - 22)], fill=(170, 160, 154))
    m = Image.new('L', (W, Hh), 0)
    md = ImageDraw.Draw(m)
    md.rectangle([64, 24, 71, Hh - 22], fill=255); md.rectangle([98, 24, 105, Hh - 22], fill=255)
    md.rectangle([60, 18, 109, 27], fill=255)
    md.ellipse([30, 14, 46, 32], fill=255)                     # head
    md.rectangle([35, 30, 41, 36], fill=255)                   # neck
    md.polygon([(24, 36), (52, 36), (56, 96), (20, 96)], fill=255)   # coat
    limb(md, (26, 40), (22, 74), 7); limb(md, (50, 40), (54, 74), 7)  # arms
    md.rectangle([26, 96, 36, Hh - 26], fill=255); md.rectangle([40, 96, 50, Hh - 26], fill=255)
    md.rectangle([24, Hh - 28, 37, Hh - 22], fill=255); md.rectangle([40, Hh - 28, 54, Hh - 22], fill=255)
    mask = np.array(m) > 0
    im = bronze_shade(im, mask, (86, 68, 48), (156, 128, 88), (112, 90, 62), (60, 46, 32), (34, 26, 20))
    d = ImageDraw.Draw(im)
    d.line([(38, 38), (38, 94)], fill=(60, 46, 32))            # coat opening
    d.point((35, 21), fill=(170, 140, 96)); d.point((41, 21), fill=(170, 140, 96))
    d.rectangle([66, Hh - 20, 116, Hh - 11], fill=(196, 170, 100))
    pixfont.draw(d, 68, Hh - 19, 'ДОВЛАТОВ', (60, 44, 20))
    return im, (W // 2, Hh - 8), (-W // 2 + 6, -20, W - 12, 20)

def fence(width, gate_at=None, gate_w=96):
    Hh = 56
    im = Image.new('RGBA', (width, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    iron, hi = (34, 36, 40), (90, 94, 100)
    d.rectangle([0, Hh - 10, width - 1, Hh - 2], fill=(124, 112, 108))
    d.line([(0, Hh - 10), (width - 1, Hh - 10)], fill=(168, 156, 150))
    def gap(x):
        return gate_at is not None and gate_at - gate_w // 2 <= x <= gate_at + gate_w // 2
    for x in range(2, width - 2, 6):
        if gap(x):
            continue
        d.line([(x, 12), (x, Hh - 10)], fill=iron)
        d.polygon([(x - 1, 12), (x, 7), (x + 1, 12)], fill=iron)
    for y in (16, Hh - 18):
        for x in range(0, width):
            if not gap(x):
                d.point((x, y), fill=iron)
    for x in range(0, width, 64):
        if gap(x) or gap(x + 10):
            continue
        d.rectangle([x, 2, x + 9, Hh - 8], fill=(130, 116, 110))
        d.rectangle([x - 1, 0, x + 10, 4], fill=(160, 146, 138))
        d.line([(x + 9, 4), (x + 9, Hh - 8)], fill=(96, 84, 80))
    if gate_at is not None:
        for gx in (gate_at - gate_w // 2 - 12, gate_at + gate_w // 2 + 2):
            d.rectangle([gx, 0, gx + 10, Hh - 6], fill=(130, 116, 110))
            d.rectangle([gx - 2, -1, gx + 12, 4], fill=(170, 156, 148))
            d.ellipse([gx, -6, gx + 10, 2], fill=(150, 136, 128))
    return im, (0, Hh - 4), None

def veranda(width=200, rr=None):
    rr = rr or random.Random(1)
    Hh = 96
    im = Image.new('RGBA', (width, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # deck
    d.rectangle([0, 34, width - 1, Hh - 8], fill=(128, 88, 56))
    for y in range(36, Hh - 8, 6):
        d.line([(0, y), (width - 1, y)], fill=(104, 70, 46))
    d.rectangle([0, Hh - 10, width - 1, Hh - 4], fill=(86, 58, 40))
    # tables with chairs
    for x in range(30, width - 20, 56):
        for cx in (x - 16, x + 16):
            d.rectangle([cx - 5, 44, cx + 5, 62], fill=(60, 50, 44))
            d.rectangle([cx - 6, 54, cx + 6, 58], fill=(90, 74, 60))
        d.ellipse([x - 14, 46, x + 14, 56], fill=(230, 226, 216))
        d.line([(x, 56), (x, 70)], fill=(60, 60, 60), width=2)
        d.point((x - 3, 49), fill=(200, 60, 60)); d.point((x + 4, 50), fill=(250, 250, 250))
    # parasol over the middle
    if width >= 150:
        px_ = width // 2
        d.line([(px_, 8), (px_, 60)], fill=(70, 60, 50), width=2)
        d.polygon([(px_ - 50, 26), (px_, 4), (px_ + 50, 26)], fill=(236, 230, 214))
        d.polygon([(px_ - 50, 26), (px_ - 25, 15), (px_ - 25, 28)], fill=(200, 60, 54))
        d.polygon([(px_ + 25, 15), (px_ + 50, 26), (px_ + 25, 28)], fill=(200, 60, 54))
        d.line([(px_ - 50, 26), (px_ + 50, 26)], fill=(150, 140, 120))
    # front railing and flower boxes
    d.rectangle([0, Hh - 26, width - 1, Hh - 22], fill=(70, 48, 32))
    for x in range(0, width, 10):
        d.line([(x, Hh - 22), (x, Hh - 10)], fill=(70, 48, 32))
    for x in range(4, width - 30, 70):
        d.rectangle([x, Hh - 34, x + 28, Hh - 26], fill=(90, 60, 40))
        for k in range(6):
            d.ellipse([x + k * 4, Hh - 40 - (k % 2) * 3, x + k * 4 + 6, Hh - 32], fill=rr.choice([(200, 60, 80), (240, 200, 80), (70, 120, 50)]))
    return im, (width // 2, Hh - 4), (-width // 2, -60, width, 60)

def signpost(text_lines, arrow='→'):
    W, Hh = 130, 120
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, 20, Hh - 6, 14, 4, 90)
    d.rectangle([17, 10, 22, Hh - 6], fill=(46, 48, 54))
    d.line([(17, 10), (17, Hh - 6)], fill=(90, 94, 100))
    y = 12
    for t in text_lines:
        tw = pixfont.width(t + ' ' + arrow)
        d.polygon([(8, y), (14 + tw + 6, y), (14 + tw + 14, y + 9), (14 + tw + 6, y + 18), (8, y + 18)], fill=(250, 248, 240), outline=(40, 60, 120))
        pixfont.draw(d, 14, y + 5, t + ' ' + arrow, (40, 60, 120))
        y += 24
    return im, (20, Hh - 6), (-6, -6, 12, 6)

def fountain():
    W, Hh = 150, 96
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shadow_ellipse(d, W // 2, Hh - 18, 72, 20, 70)
    d.ellipse([4, 30, W - 5, Hh - 10], fill=(140, 126, 120))
    d.ellipse([10, 34, W - 11, Hh - 18], fill=(176, 160, 152))
    d.ellipse([16, 38, W - 17, Hh - 22], fill=(58, 92, 104))
    d.ellipse([30, 46, W - 31, Hh - 30], fill=(72, 112, 122))
    d.rectangle([W // 2 - 6, 26, W // 2 + 6, 60], fill=(150, 136, 128))
    d.ellipse([W // 2 - 20, 22, W // 2 + 20, 34], fill=(170, 156, 148))
    for k in range(-14, 15, 7):
        d.arc([W // 2 - 14 + k, 0, W // 2 + 14 + k, 44], 200, 340, fill=(200, 226, 236))
    d.line([(W // 2, 2), (W // 2, 24)], fill=(220, 240, 250), width=2)
    for k in range(12):
        x = 30 + k * 8
        d.point((x, 52 + (k % 3) * 3), fill=(180, 210, 220))
    return im, (W // 2, Hh - 14), (-W // 2 + 4, -28, W - 8, 30)

def boat():
    """Tour boat moored along the river (top-down-ish, pointing north)."""
    W, Hh = 150, 420
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([10, Hh - 60, W - 10, Hh - 4], fill=(20, 40, 48, 120))
    hull = [(W // 2, 6), (W - 14, 70), (W - 12, Hh - 40), (W - 30, Hh - 14), (30, Hh - 14), (12, Hh - 40), (14, 70)]
    d.polygon(hull, fill=(236, 234, 228), outline=(60, 70, 80))
    d.line([(16, 74), (16, Hh - 40)], fill=(40, 60, 110), width=3)
    d.line([(W - 17, 74), (W - 17, Hh - 40)], fill=(150, 150, 150), width=2)
    # glass roof cabin
    d.rounded_rectangle([28, 80, W - 29, Hh - 70], radius=14, fill=(64, 88, 108))
    for y in range(92, Hh - 76, 22):
        d.line([(30, y), (W - 31, y)], fill=(150, 176, 192))
    d.line([(W // 2, 84), (W // 2, Hh - 74)], fill=(170, 196, 210))
    d.polygon([(34, 90), (60, 90), (34, 200)], fill=(110, 140, 160))
    # bow deck + benches
    d.polygon([(W // 2, 20), (W - 30, 70), (30, 70)], fill=(176, 140, 100))
    d.rectangle([40, Hh - 62, W - 41, Hh - 30], fill=(176, 140, 100))
    for y in range(Hh - 58, Hh - 32, 8):
        d.line([(44, y), (W - 45, y)], fill=(140, 104, 70), width=2)
    d.rectangle([W // 2 - 10, Hh - 26, W // 2 + 10, Hh - 18], fill=(200, 40, 40))
    pixfont.draw(d, 34, 70 + 4, 'ЭКСКУРСИИ', (250, 250, 250), shadow=(40, 60, 80))
    return im

def all_reused():
    out = {}
    out['restaurant'] = (cut((103, 0, 683, 209)), None, None)
    out['tree'] = (cut((14, 333, 126, 111)), None, None)
    out['lamp'] = (cut((170, 344, 32, 100)), None, None)
    out['bench'] = (cut((221, 393, 100, 51)), None, None)
    out['flowerbed'] = (cut((339, 362, 126, 82)), None, None)
    out['bikes'] = (cut((547, 386, 126, 58)), None, None)
    out['van'] = (cut((708, 374, 148, 70)), None, None)
    out['bollard'] = (cut((493, 390, 27, 54), 0.8), None, None)
    out['gates'] = (cut((307, 232, 162, 104)), None, None)
    out['flowershop'] = (cut((496, 225, 166, 115)), None, None)
    out['annex'] = (cut((693, 222, 176, 118)), None, None)
    return out
