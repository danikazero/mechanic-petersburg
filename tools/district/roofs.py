import random
import numpy as np
from PIL import Image, ImageDraw
from common import shade, mix, add, grid, vnoise, hsh

def tin(xs, ys, col, s, seam=9):
    out = np.zeros(xs.shape + (3,))
    out[:] = col
    m = vnoise(xs, ys, 40, s) - 0.5
    out += (m * 16)[..., None]
    rust = vnoise(xs, ys, 11, s + 1) > 0.86
    out[rust] = out[rust] * 0.9 + np.array([30, 10, -6])
    lx = xs % seam
    out[lx == 0] *= 0.78
    out[lx == 1] *= 1.08
    sp = hsh(xs, ys, s + 2)
    out[sp < 0.01] *= 0.85
    return out

def put(img, x0, y0, arr):
    a = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
    img.paste(a, (x0, y0))

def chimney(d, x, y, rr):
    w, h = rr.choice([10, 12, 14]), 8
    d.rectangle([x + 3, y + 3, x + w + 5, y + h + 6], fill=(0, 0, 0, 0))
    # shadow (darken by drawing semi-dark)
    d.rectangle([x + 2, y + h, x + w + 4, y + h + 5], fill=(46, 44, 48))
    d.rectangle([x, y + 4, x + w, y + h + 4], fill=(132, 70, 54))
    for yy in range(y + 6, y + h + 4, 3):
        d.line([(x, yy), (x + w, yy)], fill=(112, 58, 46))
    d.rectangle([x, y, x + w, y + 4], fill=(166, 98, 78))
    d.rectangle([x - 1, y - 1, x + w + 1, y + 1], fill=(92, 92, 98))
    d.rectangle([x + 2, y + 1, x + w - 2, y + 3], fill=(36, 30, 30))

def dormer(d, x, y, col):
    c = shade(col, 1.1)
    d.polygon([(x, y + 14), (x + 9, y), (x + 18, y + 14)], fill=c)
    d.line([(x + 9, y), (x + 18, y + 14)], fill=shade(col, 0.7))
    d.line([(x, y + 14), (x + 9, y)], fill=shade(col, 1.3))
    d.rectangle([x + 5, y + 7, x + 13, y + 14], fill=(226, 220, 204))
    d.rectangle([x + 6, y + 8, x + 12, y + 14], fill=(42, 48, 60))
    d.line([(x + 9, y + 8), (x + 9, y + 14)], fill=(200, 200, 190))
    d.line([(x + 1, y + 15), (x + 18, y + 15)], fill=shade(col, 0.6))

def hatch(d, x, y):
    d.rectangle([x, y, x + 12, y + 9], fill=(120, 124, 128))
    d.rectangle([x + 1, y + 1, x + 11, y + 4], fill=(160, 164, 168))
    d.line([(x + 1, y + 10), (x + 13, y + 10)], fill=(50, 50, 56))

def antenna(d, x, y):
    d.line([(x, y), (x, y + 16)], fill=(60, 62, 68))
    for k in range(3):
        d.line([(x - 6 + k, y + 3 + k * 4), (x + 6 - k, y + 3 + k * 4)], fill=(60, 62, 68))
    d.line([(x + 1, y + 17), (x + 8, y + 22)], fill=(70, 70, 74))

def well(img, d, x0, y0, x1, y1, wall, rr):
    """Courtyard light well seen from above: the south-facing inner wall in shade, a dark floor."""
    h = y1 - y0
    wall_h = int(h * 0.55)
    wc = shade(wall, 0.5)
    for yy in range(y0, y1 + 1):
        if yy < y0 + wall_h:
            t = (yy - y0) / max(1, wall_h)
            c = mix(shade(wall, 0.62), shade(wall, 0.34), t)
        else:
            c = (30, 31, 34)
        d.line([(x0, yy), (x1, yy)], fill=c)
    for yy in range(y0 + 6, y0 + wall_h - 12, 20):
        for xx in range(x0 + 9, x1 - 12, 18):
            lit = rr.random() < 0.1
            d.rectangle([xx, yy, xx + 7, yy + 10], fill=(196, 146, 84) if lit else shade(wc, 0.55))
    # dark floor with a couple of details (bins, a tree)
    gy0 = y0 + wall_h
    if x1 - x0 > 70 and rr.random() < 0.5:
        tx = rr.randint(x0 + 18, x1 - 18)
        d.ellipse([tx - 12, gy0 - 4, tx + 12, gy0 + 12], fill=(44, 62, 34))
        d.ellipse([tx - 8, gy0 - 2, tx + 5, gy0 + 6], fill=(58, 80, 42))
    for k in range(rr.randint(0, 2)):
        bx = rr.randint(x0 + 8, x1 - 16)
        d.rectangle([bx, y1 - 12, bx + 8, y1 - 4], fill=(48, 62, 52))
    # side walls in shadow
    d.rectangle([x0, y0, x0 + 6, y1], fill=(20, 20, 24))
    d.rectangle([x1 - 3, y0, x1, y1], fill=shade(wall, 0.4))
    # parapet rim
    rim = (138, 138, 142)
    d.rectangle([x0 - 3, y0 - 4, x1 + 3, y0 - 1], fill=rim)
    d.line([(x0 - 3, y0 - 4), (x1 + 3, y0 - 4)], fill=(176, 176, 178))
    d.rectangle([x0 - 3, y1 + 1, x1 + 3, y1 + 3], fill=rim)
    d.line([(x0 - 3, y0), (x0 - 3, y1)], fill=rim)
    d.line([(x1 + 3, y0), (x1 + 3, y1)], fill=(170, 170, 172))

def ridge_band(img, d, x0, x1, y0, y1, col, s):
    """A pitched wing: back slope darker on top, front slope lighter below the ridge."""
    xs, ys = grid(x0, y0, x1 - x0, y1 - y0)
    arr = tin(xs, ys, col, s)
    mid = (y0 + y1) // 2
    arr[ys < mid] *= 0.84
    put(img, x0, y0, arr)
    d.line([(x0, mid), (x1 - 1, mid)], fill=shade(col, 1.32))
    d.line([(x0, mid + 1), (x1 - 1, mid + 1)], fill=shade(col, 1.08))
    d.line([(x0, mid - 1), (x1 - 1, mid - 1)], fill=shade(col, 0.66))
    return mid

def draw_roof(img, x0, x1, y0, y1, col, wall, rr, s, left_fw=True, north_open=True):
    """Roof of one building, footprint x0..x1, y0..y1 (y1 = top of its street facade)."""
    d = ImageDraw.Draw(img)
    depth = y1 - y0
    if depth <= 8:
        return
    front = min(depth, rr.choice([150, 170, 190]))
    back = min(depth - front, rr.choice([150, 170, 190])) if depth - front > 220 else depth - front
    ridges = []
    ridges.append(ridge_band(img, d, x0, x1, y1 - front, y1, col, s))
    if back > 0:
        ridges.append(ridge_band(img, d, x0, x1, y0, y0 + back, shade(col, 0.96), s + 1))
    mid_y0, mid_y1 = y0 + back, y1 - front
    if mid_y1 - mid_y0 > 0:
        xs, ys = grid(x0, mid_y0, x1 - x0, mid_y1 - mid_y0)
        put(img, x0, mid_y0, tin(xs, ys, shade(col, 0.9), s + 2) * 0.95)
        wing = rr.choice([90, 104, 120])
        if mid_y1 - mid_y0 > 70 and x1 - x0 > 2 * wing + 50:
            well(img, d, x0 + wing, mid_y0 + 6, x1 - wing, mid_y1 - 6, wall, rr)
        elif mid_y1 - mid_y0 > 70 and x1 - x0 > 160:
            well(img, d, x0 + 40, mid_y0 + 6, x1 - 40, mid_y1 - 6, wall, rr)
    # dormers on the front slope
    fy = y1 - front // 2 + 10
    for x in range(x0 + 30, x1 - 40, rr.choice([70, 90, 110])):
        if rr.random() < 0.65:
            dormer(d, x, fy - 4, col)
    # chimneys along ridges
    for ry in ridges:
        x = x0 + rr.randint(14, 40)
        while x < x1 - 24:
            chimney(d, x, ry - 10, rr)
            if rr.random() < 0.3:
                chimney(d, x + 16, ry - 10, rr)
            x += rr.randint(60, 120)
    for _ in range(rr.randint(0, 2)):
        hatch(d, rr.randint(x0 + 10, max(x0 + 11, x1 - 24)), y1 - front + rr.randint(8, 24))
    for _ in range(rr.randint(1, 3)):
        antenna(d, rr.randint(x0 + 12, max(x0 + 13, x1 - 12)), ridges[0] - 30)
    # firewall on the west boundary
    if left_fw:
        d.rectangle([x0, y0, x0 + 5, y1], fill=(150, 92, 72))
        d.line([(x0, y0), (x0, y1)], fill=(186, 124, 100))
        d.line([(x0 + 6, y0), (x0 + 6, y1)], fill=(70, 50, 46))
    # north eave
    if north_open:
        d.rectangle([x0, y0, x1 - 1, y0 + 3], fill=(112, 116, 122))
        d.line([(x0, y0), (x1 - 1, y0)], fill=(168, 170, 174))
