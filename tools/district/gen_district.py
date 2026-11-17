"""Procedural pixel-art generator for the Rubinshteyna district map.

Run:  python3 tools/district/gen_district.py   (from the repo root)
Writes assets/district/*.png and scripts/district_layout.gd.
"""
import os, sys, random, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from common import T, hsh, vnoise, grid, shade, mix, add
import ground as gr
import facade as fc
import roofs as rf
import pixfont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'district')
TW, TH = 136, 96
W, H = TW * T, TH * T
CHUNK = 1024
PREVIEW = os.environ.get('PREVIEW', '/workspace/shots')

def px(*v):
    return tuple(int(round(a * T)) for a in v)

img = Image.new('RGB', (W, H), (60, 60, 64))
road = np.zeros((H, W), bool)
water = np.zeros((H, W), bool)
blocked = np.zeros((H, W), bool)
SOLIDS = []      # Rect2 in px (x, y, w, h)
AREAS = []       # (x, y, w, h, name)

def fill(rect_t, fn, **kw):
    x0, y0, x1, y1 = px(*rect_t)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    xs, ys = grid(x0, y0, x1 - x0, y1 - y0)
    arr = fn(xs, ys, **kw)
    img.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB'), (x0, y0))

def mark(mask, rect_t, v=True):
    x0, y0, x1, y1 = px(*rect_t)
    mask[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = v

def solid(x0, y0, x1, y1):
    SOLIDS.append((int(x0), int(y0), int(x1 - x0), int(y1 - y0)))

gr.load_src(os.path.join(ROOT, 'assets', 'street', 'ground.png'))

# ---------------------------------------------------------------- layout (tiles)
HSTREETS = [  # name, sw north y0, road y0, road y1, sw south y1, x0, x1, sidewalk texture
    ('Невский проспект', 9, 12, 20, 23, 0, TW, 'granite'),
    ('Улица Рубинштейна', 50, 53, 57, 59, 11, TW, 'paving'),
    ('Загородный проспект', 84, 86, 92, 94, 11, TW, 'granite2'),
]
VSTREETS = [  # name, sw west x0, road x0, road x1, sw east x1, y0, y1, road y0, road y1
    ('Набережная Фонтанки', 11, 13, 18, 20, 0, TH, 0, TH),
    ('Графский переулок', 56, 58, 62, 64, 23, 84, 20, 86),
    ('Владимирский проспект', 116, 118, 124, 126, 0, TH, 0, TH),
]
SW_TEX = {
    'granite': (gr.tex_granite, {}),
    'granite2': (gr.tex_granite, {'base': (142, 136, 134), 's': 11, 'sw': 32, 'sh': 32}),
    'paving': (gr.tex_paving, {}),
}
# default ground everywhere (embankment granite)
fill((0, 0, TW, TH), gr.tex_granite)
for name, a, b, c, dd, x0, x1, tex in HSTREETS:
    fn, kw = SW_TEX[tex]
    fill((x0, a, x1, b), fn, **kw)
    fill((x0, c, x1, dd), fn, **kw)
    AREAS.append(px(x0, a, x1 - x0, dd - a) + (name,))
for name, a, b, c, dd, y0, y1, ry0, ry1 in VSTREETS:
    tex = 'paving' if name.startswith('Граф') else 'granite'
    fn, kw = SW_TEX[tex]
    fill((a, y0, b, y1), fn, **kw)
    fill((c, y0, dd, y1), fn, **kw)
for name, a, b, c, dd, x0, x1, tex in HSTREETS:
    fill((x0, b, x1, c), gr.tex_asphalt)
    mark(road, (x0, b, x1, c))
for name, a, b, c, dd, y0, y1, ry0, ry1 in VSTREETS:
    fill((b, ry0, c, ry1), gr.tex_asphalt, s=5)
    mark(road, (b, ry0, c, ry1))
    AREAS.append(px(a, y0, dd - a, y1 - y0) + (name,))

# ---------------------------------------------------------------- curbs
def curbs():
    arr = np.array(img).astype(np.int16)
    side = ~road & ~water
    top = np.array((192, 186, 180)); edge = np.array((104, 98, 98)); face = np.array((132, 126, 124))
    shadow_k = 0.62
    # sidewalk pixels near road in each direction
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        near = np.zeros_like(road)
        for k in range(1, 6):
            sh = np.roll(road, (-dy * k, -dx * k), axis=(0, 1))
            near |= sh
        cm = side & near
        arr[cm] = top
        # the edge line right at the road
        e = side & np.roll(road, (-dy, -dx), axis=(0, 1))
        arr[e] = edge
    # curb faces visible on the road below north curbs, shadows right/below curbs
    below = road & np.roll(side, (1, 0), axis=(0, 1))
    arr[below] = face
    for k in (2, 3):
        b2 = road & np.roll(side, (k, 0), axis=(0, 1)) & ~np.roll(side, (k - 1, 0), axis=(0, 1))
        arr[b2] = face * 0.8
    for k in range(1, 4):
        sh = road & np.roll(side, (0, k), axis=(0, 1))
        arr[sh] = (arr[sh] * shadow_k).astype(np.int16)
    for k in range(4, 6):
        sh = road & np.roll(side, (k, 0), axis=(0, 1))
        arr[sh] = (arr[sh] * 0.8).astype(np.int16)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')

# ---------------------------------------------------------------- river
fill((2, 0, 10, TH), gr.tex_water)
mark(water, (2, 0, 10, TH))
# granite parapets
def parapet_v(x0, y0, y1, side):
    d = ImageDraw.Draw(img)
    X0, Y0, X1, Y1 = px(x0, y0, x0 + 1, y1)
    d.rectangle([X0, Y0, X1 - 1, Y1 - 1], fill=(156, 124, 116))
    for y in range(Y0, Y1, 44):
        d.line([(X0, y), (X1 - 1, y)], fill=(112, 88, 84))
        d.line([(X0, y + 1), (X1 - 1, y + 1)], fill=(184, 154, 144))
    d.line([(X0 + 3, Y0), (X0 + 3, Y1)], fill=(190, 160, 150))
    d.line([(X1 - 4, Y0), (X1 - 4, Y1)], fill=(128, 100, 94))
    # reflection shadow on the water side
    wx = X0 - 10 if side == 'east' else X1
    sub = img.crop((wx, Y0, wx + 10, Y1))
    a = np.array(sub).astype(np.float64)
    a *= np.linspace(0.55, 0.9, 10)[None, ::(-1 if side == 'east' else 1), None] if side == 'east' else np.linspace(0.55, 0.9, 10)[None, :, None]
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (wx, Y0))

base_curbs = None

# ---------------------------------------------------------------- squares
# Benois courtyard (cobbles) and the garden square
fill((74, 66, 110, 84), gr.tex_cobble)
fill((30, 59, 46, 84), gr.tex_grass)
AREAS.append(px(74, 59, 36, 25) + ('Двор «Фермы Бенуа»',))
AREAS.append(px(30, 59, 16, 25) + ('Сквер на Загородном',))
# garden paths
fill((36.5, 59, 39.5, 84), gr.tex_sand)
fill((30, 70, 46, 72.5), gr.tex_sand)
d = ImageDraw.Draw(img)
cx, cy = px(38, 71.25)
d.ellipse([cx - 120, cy - 84, cx + 120, cy + 84], fill=(186, 160, 118))
xs, ys = grid(cx - 120, cy - 84, 240, 168)
sand = gr.tex_sand(xs, ys)
mask = ((xs - cx) / 120.0) ** 2 + ((ys - cy) / 84.0) ** 2 <= 1
reg = np.array(img.crop((cx - 120, cy - 84, cx + 120, cy + 84))).astype(np.float64)
reg[mask] = sand[mask]
img.paste(Image.fromarray(reg.astype(np.uint8)), (cx - 120, cy - 84))

# curbs must be computed before blocks are drawn
img = curbs()
d = ImageDraw.Draw(img)
parapet_v(10, 0, 9, 'east'); parapet_v(10, 23, TH, 'east')
parapet_v(1, 0, 9, 'west'); parapet_v(1, 23, TH, 'west')

# ---------------------------------------------------------------- road markings
WHITE = (226, 224, 214)
def dash_h(y, x0, x1, length=40, gap=40, th=3, col=WHITE):
    for x in range(int(x0), int(x1), length + gap):
        d.rectangle([x, y, min(x + length, x1) - 1, y + th - 1], fill=col)
def dash_v(x, y0, y1, length=40, gap=40, th=3, col=WHITE):
    for y in range(int(y0), int(y1), length + gap):
        d.rectangle([x, y, x + th - 1, min(y + length, y1) - 1], fill=col)
def zebra_h_road(xc, y0, y1, band=64):
    """crossing over a horizontal road: horizontal bars stacked vertically"""
    for y in range(int(y0) + 8, int(y1) - 6, 16):
        d.rectangle([xc - band // 2, y, xc + band // 2, y + 7], fill=WHITE)
        d.line([(xc - band // 2, y + 8), (xc + band // 2, y + 8)], fill=(186, 184, 176))
def zebra_v_road(yc, x0, x1, band=64):
    for x in range(int(x0) + 8, int(x1) - 6, 16):
        d.rectangle([x, yc - band // 2, x + 7, yc + band // 2], fill=WHITE)

def skip_x(ranges):
    def ok(x):
        return all(not (a <= x < b) for a, b in ranges)
    return ok

V_ROADS_PX = [(px(b)[0], px(c)[0]) for _, a, b, c, dd, *_ in VSTREETS]
# Nevsky: double centre line and lane dashes
ny0, ny1 = px(12)[0], px(20)[0]
mid = (ny0 + ny1) // 2
for x0, x1 in [(0, px(13)[0] - 70), (px(18)[0] + 70, px(118)[0] - 70), (px(124)[0] + 70, W)]:
    d.rectangle([x0, mid - 5, x1, mid - 3], fill=WHITE)
    d.rectangle([x0, mid + 3, x1, mid + 5], fill=WHITE)
    dash_h(ny0 + 62, x0 + 10, x1)
    dash_h(ny1 - 64, x0 + 10, x1)
# Zagorodny: tram tracks (two), edge dashes
zy0, zy1 = px(86)[0], px(92)[0]
TRACKS = [zy0 + 52, zy1 - 52]
for tc in TRACKS:
    for ry in (tc - 22, tc + 20):
        d.rectangle([px(11)[0], ry, W, ry + 2], fill=(52, 52, 56))
        d.line([(px(11)[0], ry), (W, ry)], fill=(176, 178, 182))
        d.line([(px(11)[0], ry + 3), (W, ry + 3)], fill=(40, 40, 44))
    # worn strip between rails
    for x in range(px(11)[0], W, 6):
        if hsh(x, tc, 3) > 0.6:
            d.point((x, tc - 2 + int(hsh(x, tc, 4) * 6)), fill=(80, 80, 84))
# Fontanka embankment: centre dashes
ex = (px(13)[0] + px(18)[0]) // 2
dash_v(ex - 1, 0, ny0 - 70); dash_v(ex - 1, ny1 + 70, px(53)[0] - 70)
dash_v(ex - 1, px(57)[0] + 70, zy0 - 70); dash_v(ex - 1, zy1 + 70, H)
# Vladimirsky: double centre line
vx = (px(118)[0] + px(124)[0]) // 2
for y0, y1 in [(0, ny0 - 70), (ny1 + 70, px(53)[0] - 70), (px(57)[0] + 70, zy0 - 70), (zy1 + 70, H)]:
    d.rectangle([vx - 5, y0, vx - 3, y1], fill=WHITE)
    d.rectangle([vx + 3, y0, vx + 5, y1], fill=WHITE)
# Rubinshteyna: parking bay markings on the south side
ry1 = px(57)[0]
for x in range(px(20)[0], px(116)[0], 128):
    if not (px(56)[0] - 40 < x < px(64)[0] + 40):
        d.line([(x, ry1 - 30), (x, ry1 - 4)], fill=(200, 198, 190))
# zebra crossings where sidewalks meet roads
for name, a, b, c, dd, y0, y1, ry0, ry1 in VSTREETS:
    vx0, vx1 = px(b)[0], px(c)[0]
    for hname, ha, hb, hc, hdd, hx0, hx1, tex in HSTREETS:
        if not (hx0 <= a and dd <= hx1):
            continue
        if not (ry0 <= hb and hc <= ry1):
            continue
        # over the horizontal road, in line with both vertical sidewalks
        for sx in ((a + b) / 2, (c + dd) / 2):
            zebra_h_road(px(sx)[0], px(hb)[0], px(hc)[0], band=min(64, px(b - a)[0]))
        # over the vertical road, in line with both horizontal sidewalks
        for sy in ((ha + hb) / 2, (hc + hdd) / 2):
            if ry0 <= sy <= ry1:
                zebra_v_road(px(sy)[0], vx0, vx1, band=min(64, px(hb - ha)[0]))
# manholes and drains
def manhole(x, y):
    d.ellipse([x - 11, y - 8, x + 11, y + 8], fill=(46, 46, 50))
    d.ellipse([x - 9, y - 7, x + 9, y + 6], fill=(84, 84, 88))
    for k in range(-6, 7, 3):
        d.line([(x - 7, y + k // 2), (x + 7, y + k // 2)], fill=(66, 66, 70))
    d.arc([x - 9, y - 7, x + 9, y + 6], 200, 340, fill=(118, 118, 122))
rr = random.Random(5)
for _ in range(60):
    x, y = rr.randint(0, W - 1), rr.randint(0, H - 1)
    if road[y, x] and road[min(H - 1, y + 14), x] and road[max(0, y - 14), x] and road[y, min(W - 1, x + 14)] and road[y, max(0, x - 14)]:
        manhole(x, y)
# asphalt patches
for _ in range(90):
    x, y = rr.randint(0, W - 60), rr.randint(0, H - 40)
    w_, h_ = rr.randint(18, 60), rr.randint(10, 30)
    if road[y:y + h_, x:x + w_].all():
        reg = np.array(img.crop((x, y, x + w_, y + h_))).astype(np.float64) * 0.9
        img.paste(Image.fromarray(reg.astype(np.uint8)), (x, y))
        d.rectangle([x, y, x + w_ - 1, y + h_ - 1], outline=(52, 52, 58))
# cracks
for _ in range(70):
    x, y = rr.randint(0, W - 1), rr.randint(0, H - 1)
    if not road[y, x]:
        continue
    for k in range(rr.randint(10, 30)):
        x += rr.choice([-1, 0, 1, 1]); y += rr.choice([-1, 0, 1])
        if 0 <= x < W and 0 <= y < H and road[y, x]:
            d.point((x, y), fill=(42, 42, 46))

# puddles (late autumn)
for _ in range(26):
    x, y = rr.randint(0, W - 80), rr.randint(0, H - 40)
    w_, h_ = rr.randint(30, 70), rr.randint(10, 20)
    if road[y:y + h_, x:x + w_].all():
        d.ellipse([x, y, x + w_, y + h_], fill=(70, 84, 98))
        d.ellipse([x + 4, y + 2, x + w_ - 6, y + h_ - 4], fill=(88, 104, 120))
        d.line([(x + 8, y + 4), (x + w_ // 2, y + 4)], fill=(150, 170, 186))

# ---------------------------------------------------------------- bridge (Anichkov)
def bridge():
    X0, X1 = px(1)[0], px(11)[0]
    y_n, y_s = px(9)[0], px(23)[0]
    # deck over the water: reuse sidewalk + road already painted? water was painted after, redo deck
    fill((1, 9, 11, 12), gr.tex_granite)
    fill((1, 20, 11, 23), gr.tex_granite)
    fill((1, 12, 11, 20), gr.tex_asphalt)
    mark(road, (1, 12, 11, 20)); mark(water, (1, 9, 11, 23), False)
    d.rectangle([X0, y_n + 92, X1, y_n + 96], fill=(192, 186, 180))
    d.rectangle([X0, y_s - 96, X1, y_s - 92], fill=(192, 186, 180))
    d.rectangle([X0, y_s - 92, X1, y_s - 90], fill=(130, 124, 122))
    mid = (px(12)[0] + px(20)[0]) // 2
    d.rectangle([X0, mid - 5, X1, mid - 3], fill=WHITE)
    d.rectangle([X0, mid + 3, X1, mid + 5], fill=WHITE)
    # balustrades: granite base + cast-iron railing with hippocamp roundels
    for yb in (y_n - 14, y_s):
        d.rectangle([X0, yb, X1, yb + 13], fill=(150, 120, 112))
        d.line([(X0, yb), (X1, yb)], fill=(190, 160, 150))
        d.line([(X0, yb + 13), (X1, yb + 13)], fill=(96, 76, 72))
        for x in range(X0 + 4, X1 - 8, 20):
            d.ellipse([x, yb + 2, x + 10, yb + 11], outline=(46, 42, 40))
            d.point((x + 5, yb + 6), fill=(46, 42, 40))
        d.line([(X0, yb + 1), (X1, yb + 1)], fill=(40, 38, 36))
    # shadow of the bridge on the water
    for y in range(y_s + 14, y_s + 30):
        reg = np.array(img.crop((px(2)[0], y, px(10)[0], y + 1))).astype(np.float64)
        reg *= 0.55 + 0.45 * (y - y_s - 14) / 16
        img.paste(Image.fromarray(reg.astype(np.uint8)), (px(2)[0], y))
bridge()
AREAS.append(px(0, 9, 11, 14) + ('Аничков мост',))

# ---------------------------------------------------------------- shadows of blocks to the east
def shadow_rect(x0, y0, x1, y1, k=0.72):
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))
    if x1 <= x0 or y1 <= y0:
        return
    reg = np.array(img.crop((x0, y0, x1, y1))).astype(np.float64)
    xs, ys = grid(x0, y0, x1 - x0, y1 - y0)
    m = np.full(reg.shape[:2], k)
    # dithered soft edge on the far side
    edge = (xs - x0) > (x1 - x0) - 6
    m[edge & ((xs + ys) % 2 == 0)] = 1.0
    reg *= m[..., None]
    img.paste(Image.fromarray(reg.astype(np.uint8)), (x0, y0))

# ---------------------------------------------------------------- buildings
PALETTE = [(214, 168, 92), (226, 204, 140), (150, 190, 168), (214, 160, 148), (204, 136, 110),
           (178, 176, 168), (152, 178, 198), (216, 192, 150), (190, 118, 90), (176, 164, 182), (230, 220, 198), (196, 186, 120)]
ROOFS = [(124, 72, 60), (100, 106, 114), (88, 110, 100), (82, 86, 94), (132, 86, 70), (110, 114, 104)]
STYLES = ['plain', 'pilaster', 'grand', 'plain', 'rustic', 'brick', 'pilaster']

RUB_SHOPS = [
    {'t': 'shop', 'text': 'КОФЕЙНЯ', 'bg': (40, 64, 56), 'awning': ((40, 92, 70), (226, 220, 200)), 'warm': True},
    {'t': 'shop', 'text': 'ХИНКАЛЬНАЯ', 'bg': (64, 36, 30), 'warm': True, 'awning': ((150, 40, 40), (230, 220, 200))},
    {'t': 'shop', 'text': 'ВИННЫЙ БАР', 'bg': (70, 24, 40), 'warm': True},
    {'t': 'shop', 'text': 'РАМЕН', 'bg': (176, 40, 36), 'fg': (250, 240, 220), 'warm': True},
    {'t': 'shop', 'text': 'ПЕКАРНЯ', 'bg': (120, 84, 50), 'awning': ((200, 150, 70), (240, 230, 200))},
    {'t': 'shop', 'text': 'ЦВЕТЫ', 'bg': (48, 80, 60)},
    {'t': 'shop', 'text': 'ПРОДУКТЫ 24', 'bg': (40, 60, 120)},
    {'t': 'shop', 'text': 'ПИЦЦЕРИЯ', 'bg': (30, 90, 50), 'warm': True, 'awning': ((40, 120, 60), (230, 230, 220))},
    {'t': 'shop', 'text': 'СЫРНАЯ', 'bg': (190, 150, 60), 'fg': (40, 30, 20)},
    {'t': 'shop', 'text': 'БАР', 'bg': (28, 28, 30), 'fg': (240, 200, 90), 'warm': True},
    {'t': 'shop', 'text': 'ГАСТРОБАР', 'bg': (40, 40, 70), 'warm': True},
]
NEV_SHOPS = [
    {'t': 'shop', 'text': 'КНИГИ', 'bg': (30, 50, 90), 'span': 3},
    {'t': 'shop', 'text': 'АПТЕКА', 'bg': (40, 120, 80)},
    {'t': 'shop', 'text': 'ПЫШЕЧНАЯ', 'bg': (110, 60, 40), 'warm': True, 'awning': ((170, 60, 50), (240, 230, 210))},
    {'t': 'shop', 'text': 'ТЕАТРАЛЬНЫЕ КАССЫ', 'bg': (90, 30, 40), 'span': 3},
    {'t': 'shop', 'text': 'СУВЕНИРЫ', 'bg': (60, 50, 100)},
    {'t': 'shop', 'text': 'КОНДИТЕРСКАЯ', 'bg': (150, 90, 110), 'warm': True, 'span': 3},
    {'t': 'shop', 'text': 'БАНК', 'bg': (40, 40, 44), 'fg': (220, 190, 110)},
    {'t': 'shop', 'text': 'ОПТИКА', 'bg': (40, 70, 110)},
]
ZAG_SHOPS = [
    {'t': 'shop', 'text': 'ШАВЕРМА', 'bg': (190, 50, 30), 'fg': (255, 236, 160), 'warm': True},
    {'t': 'shop', 'text': 'РЕМОНТ ОБУВИ', 'bg': (60, 60, 64), 'span': 3},
    {'t': 'shop', 'text': 'ПОЧТА', 'bg': (30, 60, 140)},
    {'t': 'shop', 'text': 'ХОЗТОВАРЫ', 'bg': (120, 90, 30)},
    {'t': 'shop', 'text': 'ЧЕБУРЕЧНАЯ', 'bg': (120, 40, 30), 'warm': True},
    {'t': 'shop', 'text': 'СТОЛОВАЯ', 'bg': (50, 80, 70), 'warm': True},
    {'t': 'shop', 'text': 'КЛЮЧИ', 'bg': (70, 70, 40)},
]
BUILDINGS = []   # for layout export: x0, x1, base, top, name
DOORS = {}
SHOPS = []

def split_widths(total, rr, lo=9, hi=15):
    out = []
    while total > 0:
        if total <= hi + 3:
            out.append(total); break
        w_ = rr.randint(lo, hi)
        if total - w_ < 7:
            w_ = total - 7
        out.append(w_); total -= w_
    return out

def street_plate(x, y, text):
    tw = pixfont.width(text)
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + tw + 9, y + 13], fill=(24, 46, 96))
    d.rectangle([x + 1, y + 1, x + tw + 8, y + 12], outline=(214, 218, 226))
    d.line([(x + 1, y + 14), (x + tw + 10, y + 14)], fill=(40, 36, 36))
    pixfont.draw(d, x + 5, y + 3, text, (250, 250, 250))
    return tw + 10

def facade_row(x0t, x1t, y0t, base_t, shops, seed, n_choices=(3, 4, 4), specials=None, top_open=True, roofs=True, plate=None):
    rr = random.Random(seed)
    widths = split_widths(x1t - x0t, rr)
    x = x0t
    specials = specials or {}
    shop_i = rr.randint(0, len(shops) - 1)
    for bi, wt in enumerate(widths):
        X0, X1 = px(x)[0], px(x + wt)[0]
        spec = specials.get(bi)
        if spec is None:
            n = rr.choice(n_choices)
            gf = []
            ncols = max(1, (X1 - X0 - 30) // 50)
            k = 0
            while k < ncols:
                r = rr.random()
                if r < 0.42:
                    s = dict(shops[shop_i % len(shops)]); shop_i += 1
                    gf.append(s); k += s.get('span', 2)
                elif r < 0.6:
                    gf.append({'t': 'door'}); k += 1
                elif r < 0.68 and not any(u['t'] == 'arch' for u in gf):
                    gf.append({'t': 'arch'}); k += 1
                else:
                    gf.append({'t': 'gwin'}); k += 1
            spec = {'n': n, 'color': rr.choice(PALETTE), 'style': rr.choice(STYLES), 'gf': gf,
                    'roof': rr.choice(ROOFS), 'balcony': rr.randint(0, 6) if rr.random() < 0.6 else None}
            if spec['style'] == 'brick':
                spec['color'] = rr.choice([(160, 80, 60), (150, 92, 70), (170, 100, 74)])
        f, info = fc.make_facade(X1 - X0, spec, seed * 100 + bi)
        base = px(base_t)[0]
        top = base - f.height
        if roofs:
            rf.draw_roof(img, X0, X1, px(y0t)[0], top + 4, spec['roof'], spec['color'], rr, seed * 10 + bi,
                         left_fw=bi > 0, north_open=top_open)
        img.paste(f, (X0, top), f)
        BUILDINGS.append((X0, X1, base, top))
        for sx0, sx1, text, warm in info.get('shops', []):
            SHOPS.append((X0 + sx0, X0 + sx1, base, text, warm))
        for dx in info['doors']:
            DOORS.setdefault(spec.get('id', 'door'), []).append((X0 + dx, base))
        x += wt
    if plate:
        base = px(base_t)[0]
        street_plate(px(x0t)[0] + 14, base - fc.G_H - 4, plate)
        tw = pixfont.width(plate) + 10
        street_plate(px(x1t)[0] - 14 - tw, base - fc.G_H - 4, plate)
    solid(px(x0t)[0], max(0, px(y0t)[0]), px(x1t)[0], px(base_t)[0])
    # contact shadow at the facade foot
    shadow_rect(px(x0t)[0], px(base_t)[0], px(x1t)[0], px(base_t)[0] + 4, 0.7)

def shadow_east(x1t, y0t, y1t, width=36):
    shadow_rect(px(x1t)[0], px(y0t)[0], px(x1t)[0] + width, px(y1t)[0])

# shadows first (they fall on the ground only)
for (x1t, y0t, y1t) in [(56, 23, 50), (116, 23, 50), (30, 59, 84), (56, 59, 84), (74, 59, 66), (116, 59, 84), (116, 0, 9), (20, 0, 9)]:
    pass
shadow_east(56, 23, 50); shadow_east(116, 23, 50); shadow_east(30, 59, 84); shadow_east(56, 59, 84)
shadow_east(116, 59, 84); shadow_east(116, 0, 9); shadow_east(110, 66, 72, 30)

# apartment: Rubinshteyna 23 (ochre, pilasters, bakery + parade door)
APT = {'id': 'apartment', 'n': 5, 'color': (214, 168, 92), 'style': 'pilaster', 'balcony': 2, 'roof': (100, 106, 114),
       'gf': [{'t': 'shop', 'text': 'ПЕКАРНЯ', 'bg': (120, 84, 50), 'awning': ((200, 150, 70), (240, 230, 200)), 'warm': True},
              {'t': 'door', 'number': '23'}, {'t': 'gwin'}, {'t': 'arch'}, {'t': 'gwin'}, {'t': 'gwin'}]}

# row N (north side of Nevsky, facades only)
facade_row(20, 116, -14, 9, NEV_SHOPS, 11, n_choices=(4, 5), roofs=False, plate='НЕВСКИЙ ПР.')
facade_row(126, TW, -14, 9, NEV_SHOPS, 12, n_choices=(4, 5), roofs=False, plate='НЕВСКИЙ ПР.')
# row 1 (north side of Rubinshteyna)
facade_row(20, 56, 23, 50, RUB_SHOPS, 21, n_choices=(4, 4, 5), plate='УЛ. РУБИНШТЕЙНА')
facade_row(64, 116, 23, 50, RUB_SHOPS, 22, n_choices=(4, 5), specials={1: APT}, plate='УЛ. РУБИНШТЕЙНА')
facade_row(126, TW, 23, 50, RUB_SHOPS, 23, plate='УЛ. РУБИНШТЕЙНА')
# row 2 (north side of Zagorodny)
facade_row(20, 30, 59, 84, ZAG_SHOPS, 31, top_open=True, plate='ЗАГОРОДНЫЙ ПР.')
facade_row(46, 56, 59, 84, ZAG_SHOPS, 32)
facade_row(64, 74, 59, 84, ZAG_SHOPS, 33, plate='ЗАГОРОДНЫЙ')
facade_row(110, 116, 59, 84, ZAG_SHOPS, 34)
facade_row(126, TW, 59, 84, ZAG_SHOPS, 35, plate='ЗАГОРОДНЫЙ ПР.')

# firewall behind the Benois courtyard with a ghost advertisement
def firewall():
    X0, X1 = px(74)[0], px(110)[0]
    Y0, base = px(59)[0], px(66)[0]
    rr = random.Random(77)
    rf.draw_roof(img, X0, X1, Y0, Y0 + 40, (100, 106, 114), (160, 90, 70), rr, 991, left_fw=False)
    wall = Image.new('RGB', (X1 - X0, base - Y0 - 36), (150, 86, 66))
    fc.plaster(wall, (0, 0, wall.width, wall.height), (150, 86, 66), 5, 1.6)
    wd = ImageDraw.Draw(wall)
    for y in range(0, wall.height, 6):
        wd.line([(0, y), (wall.width, y)], fill=(126, 72, 56))
        off = 0 if (y // 6) % 2 else 7
        for x in range(off, wall.width, 14):
            wd.line([(x, y), (x, y + 5)], fill=(132, 76, 58))
    # ghost sign
    gx, gy = 120, 30
    wd.rectangle([gx, gy, gx + 520, gy + 70], fill=(170, 120, 90))
    wd.rectangle([gx + 6, gy + 6, gx + 514, gy + 64], outline=(196, 160, 120), width=2)
    pixfont.draw(wd, gx + 30, gy + 18, 'ХЛЕБ · МОЛОКО · МЯСО', (200, 176, 140), scale=4, shadow=(150, 100, 80))
    for k in range(400):
        x = rr.randint(gx, gx + 520); y = rr.randint(gy, gy + 70)
        wd.point((x, y), fill=(150, 90, 70))
    wd.line([(0, 0), (wall.width, 0)], fill=(186, 124, 100))
    img.paste(wall, (X0, Y0 + 36))
    solid(X0, Y0, X1, base)
    shadow_rect(X0, base, X1, base + 4, 0.7)
firewall()

# row 3 roofs (south of Zagorodny) – only the north eaves are visible
for x0t, x1t, seed in ((20, 116, 41), (126, TW, 42)):
    rr = random.Random(seed)
    x = x0t
    for wt in split_widths(x1t - x0t, rr):
        rf.draw_roof(img, px(x)[0], px(x + wt)[0], px(94)[0], H + 200, rr.choice(ROOFS), (200, 180, 150), rr, seed * 7 + x, left_fw=x != x0t)
        x += wt
    solid(px(x0t)[0], px(94)[0], px(x1t)[0], H)

# river is solid (except the bridge)
solid(0, 0, px(11)[0], px(9)[0] - 14)
solid(0, px(23)[0] + 14, px(11)[0], H)

APT_DOOR = DOORS['apartment'][0]


# ---------------------------------------------------------------- props
import props as P
P.load(os.path.join(ROOT, 'assets', 'street', 'objects.png'))
REG = {}   # name -> (img, anchor, [solid rects rel. to anchor])
def reg(name, img_, anchor, solids):
    if solids is not None and not isinstance(solids, list):
        solids = [solids]
    REG[name] = (img_, anchor, solids or [])

re_ = P.all_reused()
def bottom_anchor(im, inset=4):
    return (im.width // 2, im.height - inset)
r_im = re_['restaurant'][0]
reg('restaurant', r_im, bottom_anchor(r_im, 2), (-r_im.width // 2 + 8, -330, r_im.width - 16, 318))
for mode in ('green', 'autumn', 'dark', 'yellow'):
    t = re_['tree'][0] if mode == 'green' else P.recolor_tree(re_['tree'][0], mode)
    reg('tree_' + mode, t, (t.width // 2, t.height - 4), (-14, -12, 28, 12))
lm = re_['lamp'][0]; reg('lamp', lm, (lm.width // 2, lm.height - 3), (-8, -8, 16, 8))
b = re_['bench'][0]; reg('bench', b, bottom_anchor(b), (-b.width // 2 + 8, -24, b.width - 16, 24))
fb = re_['flowerbed'][0]; reg('flowerbed', fb, bottom_anchor(fb), (-fb.width // 2 + 4, -46, fb.width - 8, 46))
bk = P.cut((547, 386, 126, 58), 1.0); reg('bikes', bk, bottom_anchor(bk), (-bk.width // 2 + 6, -20, bk.width - 12, 20))
vn = re_['van'][0]; reg('van', vn, bottom_anchor(vn, 6), (-vn.width // 2 + 6, -26, vn.width - 12, 26))
bl = re_['bollard'][0]; reg('bollard', bl, bottom_anchor(bl, 2), (-7, -8, 14, 8))
gt = re_['gates'][0]; reg('gates', gt, bottom_anchor(gt, 2), [(-gt.width // 2, -22, 62, 22), (gt.width // 2 - 62, -22, 62, 22)])
fs = re_['flowershop'][0]; reg('flowershop', fs, bottom_anchor(fs, 2), (-fs.width // 2 + 4, -60, fs.width - 8, 60))
for c in ('white', 'silver', 'blue', 'red', 'black', 'taxi', 'green', 'beige'):
    for kind in ('sedan', 'hatch'):
        im_, an, so = P.car(c, kind)
        reg('car_%s_%s' % (c, kind), im_, an, so)
reg('tram', *P.tram())
reg('tram_stop', *P.tram_stop())
reg('urn', *P.urn())
reg('ad_column', *P.ad_column())
reg('kiosk_shawarma', *P.kiosk('ШАВЕРМА', (190, 50, 30)))
reg('kiosk_press', *P.kiosk('ПЕЧАТЬ', (40, 70, 140)))
reg('statue_l', *P.statue_horse(False))
reg('statue_r', *P.statue_horse(True))
reg('dovlatov', *P.dovlatov())
reg('fountain', *P.fountain())
reg('sign_west', *P.signpost(['ФЕРМА БЕНУА', 'ЗАГОРОДНЫЙ'], '←'))
reg('sign_south', *P.signpost(['ФЕРМА БЕНУА'], '↓'))
reg('sign_east', *P.signpost(['ФЕРМА БЕНУА'], '→'))
for wv in (160, 200, 240):
    reg('veranda_%d' % wv, *P.veranda(wv, random.Random(wv)))

PLACED = []
def place(name, x, y, flip=False, solid_=True):
    im_, an, sols = REG[name]
    x, y = int(round(x)), int(round(y))
    PLACED.append((name, x, y, flip))
    if solid_:
        for sx, sy, sw, sh in sols:
            if flip:
                sx = -sx - sw
            solid(x + sx, y + sy, x + sx + sw, y + sy + sh)

def fence_run(name, x0, y, width, gate_at=None, gate_w=96):
    im_, an, _ = P.fence(width, gate_at, gate_w)
    REG[name] = (im_, an, [])
    PLACED.append((name, int(x0), int(y), False))
    if gate_at is None:
        solid(x0, y - 10, x0 + width, y + 2)
    else:
        solid(x0, y - 10, x0 + gate_at - gate_w // 2 - 12, y + 2)
        solid(x0 + gate_at + gate_w // 2 + 2, y - 10, x0 + width, y + 2)

rr = random.Random(2026)
V_ROAD_X = [(px(a)[0] - 40, px(dd)[0] + 40) for _, a, b, c, dd, *_ in VSTREETS]
def clear_of_streets(x):
    return all(not (a0 <= x <= a1) for a0, a1 in V_ROAD_X)

# street lamps along all sidewalks (staggered)
for name, a, b, c, dd, x0, x1, tex in HSTREETS:
    for i, x in enumerate(range(px(x0)[0] + 150, px(x1)[0] - 40, 416)):
        if clear_of_streets(x) and not (name.startswith('Загород') and abs(x - px(92)[0]) < 200):
            place('lamp', x, px(b)[0] - 8)
        if clear_of_streets(x + 208) and not name.startswith('Улица'):
            place('lamp', x + 208, px(c)[0] + 14)
for name, a, b, c, dd, y0, y1, ry0, ry1 in VSTREETS:
    for y in range(px(y0)[0] + 160, px(y1)[0] - 40, 416):
        inside_h = any(px(ha)[0] - 30 <= y <= px(hdd)[0] + 40 for _, ha, hb, hc, hdd, *_ in HSTREETS)
        if not inside_h:
            place('lamp', px(b)[0] - 10, y)
# embankment: lindens along the houses, lamps on the parapet side already
for y in range(px(25)[0], px(84)[0], 160):
    if not (px(48)[0] < y < px(62)[0]):
        place(rr.choice(['tree_green', 'tree_autumn', 'tree_dark']), px(19)[0] - 4, y, rr.random() < 0.5)
for y in range(px(26)[0], px(82)[0], 240):
    if not (px(48)[0] < y < px(62)[0]):
        place('bench', px(12)[0] + 6, y + 70)
place('urn', px(12)[0] + 2, px(40)[0])
# Anichkov bridge horse tamers
place('statue_r', 80, px(10.5)[0])
place('statue_l', 290, px(10.5)[0])
place('statue_r', 80, px(22.6)[0])
place('statue_l', 290, px(22.6)[0])

# Nevsky: advertising column, press kiosk, cars waiting at the lights
place('ad_column', px(40)[0], px(11.6)[0])
place('ad_column', px(96)[0], px(22.7)[0])
place('kiosk_press', px(110)[0], px(22.8)[0])
place('urn', px(28)[0], px(11.7)[0])
place('urn', px(84)[0], px(22.7)[0])
place('car_taxi_sedan', px(23)[0], px(14.6)[0])
place('car_silver_hatch', px(28)[0], px(14.6)[0])
place('car_black_sedan', px(112)[0], px(18.8)[0], True)
place('car_white_sedan', px(104)[0] - 40, px(18.8)[0], True)
place('car_red_hatch', px(66)[0], px(14.6)[0])

# Rubinshteyna: cafe verandas, parked cars, Dovlatov, signpost
APT_X = APT_DOOR[0]
for sx0, sx1, base, text, warm in SHOPS:
    if base == px(50)[0] and warm and abs((sx0 + sx1) / 2 - APT_X) > 260 and sx1 - sx0 >= 80:
        wv = 240 if sx1 - sx0 >= 200 else (200 if sx1 - sx0 >= 150 else 160)
        place('veranda_%d' % wv, (sx0 + sx1) / 2, base + 88)
place('dovlatov', APT_X - 170, px(50)[0] + 66)
place('sign_west', APT_X + 120, px(53)[0] - 6)
place('bikes', APT_X - 330, px(53)[0] - 6)
cars = [k for k in REG if k.startswith('car_')]
x = px(21)[0]
while x < px(134)[0]:
    if clear_of_streets(x) and clear_of_streets(x + 140) and rr.random() < 0.72:
        place(rr.choice(cars), x + 70, px(57)[0] - 6, rr.random() < 0.5)
    x += rr.choice([150, 160, 176])
for xx in (px(26)[0], px(48)[0], px(70)[0], px(100)[0]):
    place('urn', xx, px(52.7)[0])

# Garden square (сквер)
SQ0, SQ1 = px(30)[0], px(46)[0]
fence_run('fence_sq_n', SQ0, px(59)[0] + 10, SQ1 - SQ0, gate_at=px(38)[0] - SQ0)
fence_run('fence_sq_s', SQ0, px(84)[0] - 2, SQ1 - SQ0, gate_at=px(38)[0] - SQ0)
place('fountain', px(38)[0], px(71.25)[0] + 40)
for (tx, ty) in ((32, 63), (35, 66.5), (42, 63.5), (44.3, 67), (32.4, 76), (35.2, 81), (41.5, 77), (44.4, 81.5)):
    place(rr.choice(['tree_green', 'tree_autumn', 'tree_yellow']), px(tx)[0], px(ty)[0], rr.random() < 0.5)
for (bx, by) in ((36.0, 64), (36.0, 79), (40.2, 64), (40.2, 79)):
    place('bench', px(bx)[0] - 40 if bx < 38 else px(bx)[0] + 40, px(by)[0])
place('urn', px(36)[0] - 4, px(68)[0]); place('urn', px(40)[0] + 4, px(75)[0])

# Benois courtyard
RX = px(92)[0]
place('restaurant', RX, px(76)[0])
RESTAURANT_DOOR = (RX - 44, px(76)[0] - 18, 88, 18)
gx = RX
fence_run('fence_bn_w', px(74)[0], px(84)[0] - 2, gx - 118 - px(74)[0])
fence_run('fence_bn_e', gx + 118, px(84)[0] - 2, px(110)[0] - gx - 118)
place('gates', gx, px(84)[0] - 2)
for fx in (RX - 230, RX + 230):
    place('flowerbed', fx, px(80.5)[0])
place('lamp', RX - 120, px(78.5)[0]); place('lamp', RX + 120, px(78.5)[0])
place('lamp', px(76)[0], px(80)[0]); place('lamp', px(108)[0], px(80)[0])
place('tree_green', px(76.5)[0], px(72)[0]); place('tree_dark', px(107.5)[0], px(72.5)[0], True)
place('bench', px(80)[0], px(82.5)[0]); place('bench', px(104)[0], px(82.5)[0])
place('bikes', RX - 400, px(77.4)[0])
place('van', px(105.5)[0], px(78)[0], True)
place('urn', RX + 330, px(77.3)[0])
place('sign_east', px(62.3)[0] + 30, px(84)[0] + 50)
place('sign_south', px(64.6)[0], px(59)[0] + 40)

# Zagorodny: tram at the stop, parked cars, shawarma kiosk
place('tram', px(40)[0], TRACKS[0] + 24)
place('tram_stop', px(40)[0], px(86)[0] - 6)
place('kiosk_shawarma', px(66.5)[0], px(93.8)[0])
x = px(21)[0]
while x < px(134)[0]:
    if clear_of_streets(x) and clear_of_streets(x + 140) and rr.random() < 0.55:
        place(rr.choice(cars), x + 70, px(92)[0] - 6, rr.random() < 0.5)
    x += rr.choice([150, 170, 190])
# Grafsky: a few trees and bollards
for y in (px(26)[0], px(33)[0], px(40)[0], px(64)[0], px(72)[0], px(79)[0]):
    place('tree_green' if y % 3 else 'tree_autumn', px(63.5)[0], y + 60)

# tour boats on the Fontanka (baked into the ground, the river is not walkable)
bt = P.boat()
img.paste(bt, (px(2.3)[0], px(44)[0]), bt)
bt2 = bt.rotate(180)
img.paste(bt2, (px(5.6)[0], px(70)[0]), bt2)

def export():
    os.makedirs(OUT, exist_ok=True)
    pdir = os.path.join(OUT, 'props')
    os.makedirs(pdir, exist_ok=True)
    for f in os.listdir(OUT):
        if f.startswith('ground_') and f.endswith('.png'):
            os.remove(os.path.join(OUT, f))
    for f in os.listdir(pdir):
        if f.endswith('.png'):
            os.remove(os.path.join(pdir, f))
    chunks = []
    for cy in range(0, H, CHUNK):
        for cx in range(0, W, CHUNK):
            name = 'ground_%d_%d.png' % (cx // CHUNK, cy // CHUNK)
            img.crop((cx, cy, min(W, cx + CHUNK), min(H, cy + CHUNK))).save(os.path.join(OUT, name), optimize=True)
            chunks.append((name, cx, cy))
    used = sorted({p[0] for p in PLACED})
    for name in used:
        REG[name][0].save(os.path.join(pdir, name + '.png'), optimize=True)
    ax, ay = APT_DOOR
    L = []
    L.append('# Generated by tools/district/gen_district.py - do not edit by hand.')
    L.append('extends RefCounted')
    L.append('')
    L.append('const MAP_SIZE := Vector2(%d, %d)' % (W, H))
    L.append('const ARRIVAL := Vector2(%d, %d)' % (ax, ay + 34))
    L.append('const APARTMENT_DOOR := Rect2(%d, %d, %d, %d)' % (ax - 26, ay - 14, 52, 14))
    L.append('const RESTAURANT_DOOR := Rect2(%d, %d, %d, %d)' % RESTAURANT_DOOR)
    L.append('const CHUNKS := [')
    for n, cx, cy in chunks:
        L.append('\t["%s", Vector2(%d, %d)],' % (n, cx, cy))
    L.append(']')
    L.append('const ANCHORS := {')
    for name in used:
        an = REG[name][1]
        L.append('\t"%s": Vector2(%d, %d),' % (name, an[0], an[1]))
    L.append('}')
    L.append('const PROPS := [')
    for name, x, y, flip in PLACED:
        L.append('\t["%s", Vector2(%d, %d), %s],' % (name, x, y, 'true' if flip else 'false'))
    L.append(']')
    L.append('const SOLIDS: Array[Rect2] = [')
    for (x, y, w_, h_) in SOLIDS:
        L.append('\tRect2(%d, %d, %d, %d),' % (x, y, w_, h_))
    L.append(']')
    L.append('const AREAS := [')
    # smaller, more specific areas first
    for (x, y, w_, h_, name) in sorted(AREAS, key=lambda a: a[2] * a[3]):
        L.append('\t[Rect2(%d, %d, %d, %d), "%s"],' % (x, y, w_, h_, name))
    L.append(']')
    open(os.path.join(ROOT, 'scripts', 'district_layout.gd'), 'w').write('\n'.join(L) + '\n')

def preview():
    os.makedirs(PREVIEW, exist_ok=True)
    full = img.convert('RGBA')
    for name, x, y, flip in sorted(PLACED, key=lambda p: p[2]):
        im_, an, _ = REG[name]
        if flip:
            im_ = im_.transpose(Image.FLIP_LEFT_RIGHT)
            ox = x - (im_.width - an[0])
        else:
            ox = x - an[0]
        full.alpha_composite(im_, (max(0, ox), max(0, y - an[1])) if ox >= 0 and y - an[1] >= 0 else (0, 0)) if ox >= 0 and y - an[1] >= 0 else full.paste(im_, (ox, y - an[1]), im_)
    full.save(os.path.join(PREVIEW, 'district_full.png'))
    full.resize((W // 4, H // 4), Image.BOX).save(os.path.join(PREVIEW, 'district_overview.png'))
    return full

if __name__ == '__main__':
    export()
    preview()
    print('apartment door', APT_DOOR, 'solids', len(SOLIDS), 'props', len(PLACED))
