import random
import numpy as np
from PIL import Image, ImageDraw
from common import shade, mix, add, grid, vnoise, hsh
import pixfont

G_H, U_H, BELT, TOP = 112, 64, 8, 26
CREAM = (238, 232, 216)
GLASS_T, GLASS_B = (146, 168, 184), (56, 70, 88)
LIT_T, LIT_B = (252, 214, 140), (214, 146, 74)
IRON = (38, 38, 44)

def height(n):
    return TOP + n * U_H + BELT + G_H

def plaster(img, box, col, seed, strength=1.0):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return
    xs, ys = grid(0, 0, w, h)
    n = vnoise(xs, ys, 23, seed) - 0.5
    sp = hsh(xs, ys, seed + 9)
    base = np.array(col, dtype=np.float64)
    arr = np.zeros((h, w, 3))
    arr[:] = base
    arr += (n * 14 * strength)[..., None]
    arr -= ((sp < 0.025) * 7 * strength)[..., None]
    arr += ((sp > 0.985) * 5 * strength)[..., None]
    a = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
    img.paste(a, (x0, y0))

def streak(d, x, y0, length, col, rr):
    for i in range(length):
        if rr.random() < 0.85:
            d.point((x, y0 + i), fill=col)

def glass(d, x0, y0, x1, y1, lit, rr, curtains=False):
    h = max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        t = (y - y0) / h
        c = mix(LIT_T, LIT_B, t) if lit else mix(GLASS_T, GLASS_B, t ** 0.8)
        d.line([(x0, y), (x1, y)], fill=c)
    if not lit:
        # diagonal sky reflection
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                k = (x - x0) + (y - y0) // 2
                if k % 17 in (3, 4) or k % 17 == 9:
                    c = d._image.getpixel((x, y))
                    d.point((x, y), fill=add(c, 20))
    if curtains:
        cc = (226, 214, 190) if not lit else (255, 236, 196)
        d.rectangle([x0, y0, x0 + 2, y1], fill=shade(cc, 0.9))
        d.rectangle([x1 - 2, y0, x1, y1], fill=shade(cc, 0.9))

def window(d, cx, top, ww, wh, col, rr, kind='plain', lit=False):
    light = shade(col, 1.16)
    dark = shade(col, 0.66)
    x0 = cx - ww // 2
    x1 = x0 + ww - 1
    y1 = top + wh - 1
    # surround (nalichnik)
    if kind != 'none':
        d.rectangle([x0 - 3, top - 3, x1 + 3, y1 + 1], fill=light)
        d.line([(x1 + 4, top - 2), (x1 + 4, y1 + 1)], fill=shade(col, 0.82))
    # reveal
    d.rectangle([x0, top, x1, y1], fill=(34, 36, 44))
    glass(d, x0 + 2, top + 2, x1 - 1, y1, lit, rr, curtains=rr.random() < 0.35)
    # frame: outer, transom, mullion
    fr = CREAM
    d.rectangle([x0 + 1, top + 1, x1, y1], outline=fr)
    tr = top + max(8, wh // 4)
    d.line([(x0 + 1, tr), (x1, tr)], fill=fr)
    d.line([(cx, tr), (cx, y1)], fill=fr)
    d.line([(x0 + 1, top + 2), (x0 + 1, y1)], fill=shade(fr, 0.85))
    # sill
    d.rectangle([x0 - 5, y1 + 2, x1 + 5, y1 + 4], fill=light)
    d.line([(x0 - 5, y1 + 4), (x1 + 5, y1 + 4)], fill=shade(col, 0.9))
    d.line([(x0 - 4, y1 + 5), (x1 + 4, y1 + 5)], fill=dark)
    # weathering under sill
    for sx in (x0 - 2, cx + rr.randint(-3, 3), x1 + 2):
        if rr.random() < 0.5:
            streak(d, sx, y1 + 6, rr.randint(3, 9), shade(col, 0.9), rr)
    # pediment
    if kind == 'tri':
        pts = [(x0 - 6, top - 5), (cx, top - 14), (x1 + 6, top - 5)]
        d.polygon(pts, fill=light)
        d.line([(x0 - 6, top - 5), (x1 + 6, top - 5)], fill=shade(col, 0.95))
        d.line([(x0 - 6, top - 4), (x1 + 6, top - 4)], fill=dark)
        d.line([pts[0], pts[1]], fill=CREAM)
        d.line([pts[1], pts[2]], fill=shade(light, 0.9))
    elif kind == 'flat':
        d.rectangle([x0 - 7, top - 9, x1 + 7, top - 5], fill=light)
        d.line([(x0 - 7, top - 9), (x1 + 7, top - 9)], fill=CREAM)
        d.line([(x0 - 6, top - 4), (x1 + 6, top - 4)], fill=dark)
    elif kind == 'key':
        d.polygon([(cx - 4, top - 5), (cx + 4, top - 5), (cx + 3, top + 2), (cx - 3, top + 2)], fill=CREAM)
        d.line([(cx + 4, top - 4), (cx + 3, top + 2)], fill=dark)
    return lit

def balcony(d, cx, y, width, col):
    x0, x1 = cx - width // 2, cx + width // 2
    d.rectangle([x0, y, x1, y + 4], fill=shade(col, 1.12))
    d.line([(x0, y + 5), (x1, y + 5)], fill=shade(col, 0.6))
    for kx in (x0 + 3, x1 - 5):
        d.polygon([(kx, y + 5), (kx + 3, y + 5), (kx + 2, y + 11), (kx + 1, y + 11)], fill=shade(col, 1.05))
    # iron railing
    ry = y - 13
    d.line([(x0 + 1, ry), (x1 - 1, ry)], fill=IRON, width=2)
    for x in range(x0 + 2, x1 - 1, 4):
        d.line([(x, ry), (x, y - 1)], fill=IRON)
    for x in range(x0 + 4, x1 - 3, 8):
        d.ellipse([x - 2, ry + 4, x + 2, ry + 8], outline=IRON)
    d.line([(x0 + 1, y - 2), (x1 - 1, y - 2)], fill=IRON)

def drainpipe(d, x, top, bottom, rr):
    pc, ph, pd = (118, 122, 128), (164, 168, 172), (78, 80, 86)
    d.rectangle([x - 4, top, x + 4, top + 7], fill=pc)  # funnel
    d.line([(x - 4, top), (x + 4, top)], fill=ph)
    d.rectangle([x - 2, top + 8, x + 2, bottom - 8], fill=pc)
    d.line([(x - 2, top + 8), (x - 2, bottom - 8)], fill=ph)
    d.line([(x + 2, top + 8), (x + 2, bottom - 8)], fill=pd)
    for y in range(top + 30, bottom - 20, rr.choice([48, 56])):
        d.rectangle([x - 3, y, x + 3, y + 2], fill=pd)
    d.polygon([(x - 2, bottom - 8), (x + 2, bottom - 8), (x + 7, bottom - 2), (x + 3, bottom - 1)], fill=pc)

def sign_board(d, x0, x1, y, text, bg, fg, rr, scale=1):
    tw = pixfont.width(text, scale)
    w = max(tw + 14, 40)
    w = min(w, x1 - x0)
    cx = (x0 + x1) // 2
    bx0, bx1 = cx - w // 2, cx + w // 2
    hh = 7 * scale + 8
    d.rectangle([bx0, y, bx1, y + hh], fill=shade(bg, 0.7))
    d.rectangle([bx0 + 1, y + 1, bx1 - 1, y + hh - 1], fill=bg)
    d.line([(bx0 + 1, y + 1), (bx1 - 1, y + 1)], fill=shade(bg, 1.25))
    d.line([(bx0, y + hh + 1), (bx1, y + hh + 1)], fill=(40, 36, 36))
    pixfont.draw(d, cx - tw // 2, y + 4, text, fg, scale=scale, shadow=shade(bg, 0.55))

def awning(d, x0, x1, y, c1, c2):
    for x in range(x0, x1 + 1):
        c = c1 if ((x - x0) // 6) % 2 == 0 else c2
        d.line([(x, y), (x, y + 14)], fill=c)
        d.point((x, y), fill=shade(c, 1.2))
    for x in range(x0, x1 + 1, 6):
        d.polygon([(x, y + 14), (x + 6, y + 14), (x + 3, y + 18)], fill=c1 if ((x - x0) // 6) % 2 == 0 else c2)
    d.line([(x0, y + 15), (x1, y + 15)], fill=shade(c1, 0.75))
    d.line([(x0 + 2, y + 19), (x1 - 2, y + 19)], fill=(30, 30, 34))

def shopfront(d, img, x0, x1, gy, bottom, unit, rr):
    text = unit.get('text', '')
    bg = unit.get('bg', (44, 60, 54))
    fg = unit.get('fg', (240, 222, 170))
    frame = unit.get('frame', (54, 50, 48))
    warm = unit.get('warm', False)
    sy = gy + 10
    sign_board(d, x0 + 2, x1 - 2, sy, text, bg, fg, rr, unit.get('scale', 1))
    wy0 = sy + 7 * unit.get('scale', 1) + 16
    wy1 = bottom - 16
    d.rectangle([x0, wy0 - 3, x1, wy1 + 3], fill=frame)
    d.line([(x0, wy0 - 3), (x1, wy0 - 3)], fill=shade(frame, 1.5))
    # glass door on one side
    door_w = 26
    door_left = unit.get('door_left', rr.random() < 0.5)
    dx0 = x0 + 3 if door_left else x1 - 3 - door_w
    gx0, gx1 = (dx0 + door_w + 3, x1 - 3) if door_left else (x0 + 3, dx0 - 3)
    glass(d, gx0, wy0, gx1, wy1, warm, rr)
    if warm:
        # interior silhouettes: lamps and tables
        for k in range(gx0 + 8, gx1 - 6, 22):
            d.ellipse([k - 3, wy0 + 4, k + 3, wy0 + 8], fill=(255, 240, 196))
            d.line([(k, wy0), (k, wy0 + 4)], fill=(80, 60, 40))
            d.rectangle([k - 6, wy1 - 16, k + 6, wy1 - 14], fill=(110, 70, 44))
            d.line([(k, wy1 - 14), (k, wy1)], fill=(90, 58, 38))
    else:
        for k in range(gx0 + 4, gx1 - 4, 9):
            if rr.random() < 0.6:
                hgt = rr.randint(6, 16)
                d.rectangle([k, wy1 - hgt, k + 5, wy1 - 1], fill=rr.choice([(170, 70, 60), (210, 190, 120), (90, 120, 150), (220, 220, 210)]))
        d.line([(gx0, wy1 - 18), (gx1, wy1 - 18)], fill=shade(frame, 1.2))
    for k in range(gx0 + (gx1 - gx0) // 2, gx0 + (gx1 - gx0) // 2 + 1):
        d.line([(k, wy0), (k, wy1)], fill=frame)
    # door
    d.rectangle([dx0, wy0 - 3, dx0 + door_w, bottom - 2], fill=frame)
    glass(d, dx0 + 3, wy0, dx0 + door_w - 3, bottom - 8, warm, rr)
    d.line([(dx0 + door_w - 6, wy0 + 30), (dx0 + door_w - 6, wy0 + 40)], fill=(220, 200, 150), width=2)
    if unit.get('awning'):
        a1, a2 = unit['awning']
        awning(d, x0 - 2, x1 + 2, wy0 - 2, a1, a2)
    return (dx0 + door_w // 2)

def entrance_door(d, cx, gy, bottom, col, number, rr, wood=(104, 70, 46)):
    w, top = 44, gy + 18
    x0, x1 = cx - w // 2, cx + w // 2
    light = shade(col, 1.16)
    # portal surround
    d.rectangle([x0 - 7, top - 8, x1 + 7, bottom], fill=light)
    d.rectangle([x0 - 3, top - 4, x1 + 3, bottom], fill=shade(col, 0.6))
    d.rectangle([x0, top, x1, bottom - 1], fill=(30, 26, 26))
    # fanlight
    d.rectangle([x0 + 2, top + 2, x1 - 2, top + 16], fill=(40, 36, 36))
    glass(d, x0 + 3, top + 3, x1 - 3, top + 15, True, rr)
    for k in range(x0 + 6, x1 - 2, 6):
        d.line([(cx, top + 15), (k, top + 3)], fill=(60, 48, 40))
    # leaves
    for lx0, lx1 in ((x0 + 2, cx - 1), (cx + 1, x1 - 2)):
        d.rectangle([lx0, top + 19, lx1, bottom - 2], fill=wood)
        d.line([(lx0, top + 19), (lx0, bottom - 2)], fill=shade(wood, 1.3))
        for py0, py1 in ((top + 23, top + 46), (top + 50, bottom - 6)):
            d.rectangle([lx0 + 3, py0, lx1 - 3, py1], outline=shade(wood, 0.7))
            d.line([(lx0 + 4, py0 + 1), (lx1 - 4, py0 + 1)], fill=shade(wood, 1.2))
    d.rectangle([cx - 4, top + 50, cx - 2, top + 54], fill=(214, 186, 110))
    d.rectangle([cx + 2, top + 50, cx + 4, top + 54], fill=(214, 186, 110))
    # canopy (kozyrek)
    d.polygon([(x0 - 12, top - 14), (x1 + 12, top - 14), (x1 + 8, top - 8), (x0 - 8, top - 8)], fill=(76, 80, 88))
    d.line([(x0 - 12, top - 14), (x1 + 12, top - 14)], fill=(140, 146, 152))
    d.line([(x0 - 8, top - 7), (x1 + 8, top - 7)], fill=(30, 30, 36))
    d.line([(x0 - 10, top - 8), (x0 - 4, top - 2)], fill=IRON)
    d.line([(x1 + 10, top - 8), (x1 + 4, top - 2)], fill=IRON)
    # lamp and house number
    d.rectangle([x1 + 12, top - 2, x1 + 30, top + 10], fill=(28, 48, 92))
    d.rectangle([x1 + 13, top - 1, x1 + 29, top + 9], outline=(220, 220, 220))
    pixfont.draw(d, x1 + 21 - pixfont.width(number) // 2, top + 1, number, (250, 250, 250))
    return x0, x1

def arch(d, cx, gy, bottom, col, rr):
    w, top = 60, gy + 12
    x0, x1 = cx - w // 2, cx + w // 2
    light = shade(col, 1.14)
    d.rectangle([x0 - 6, top - 6, x1 + 6, bottom], fill=light)
    d.ellipse([x0 - 6, top - 6, x1 + 6, top + w + 6], fill=light)
    for y in range(top, bottom):
        t = (y - top) / (bottom - top)
        c = mix((14, 14, 18), (44, 42, 46), t)
        if y < top + w // 2:
            dy = top + w // 2 - y
            half = int((max(0, (w / 2) ** 2 - dy ** 2)) ** 0.5)
            d.line([(cx - half, y), (cx + half, y)], fill=c)
        else:
            d.line([(x0, y), (x1, y)], fill=c)
    # light at the end of the passage
    d.rectangle([cx - 10, top + 40, cx + 10, bottom - 4], fill=(70, 74, 70))
    d.rectangle([cx - 8, top + 46, cx + 8, bottom - 4], fill=(96, 104, 92))
    # gate bars
    for x in range(x0 + 2, x1 - 1, 5):
        y_start = top + w // 2 - int((max(0, (w / 2) ** 2 - (x - cx) ** 2)) ** 0.5) + 2
        d.line([(x, y_start), (x, bottom - 1)], fill=IRON)
    d.line([(x0, top + 38), (x1, top + 38)], fill=IRON)
    d.line([(x0, bottom - 10), (x1, bottom - 10)], fill=IRON)
    d.polygon([(cx - 5, top - 7), (cx + 5, top - 7), (cx + 3, top + 3), (cx - 3, top + 3)], fill=CREAM)

def make_facade(w, spec, seed):
    rr = random.Random(seed)
    n = spec['n']
    col = spec['color']
    style = spec.get('style', 'plain')
    h = height(n)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    light, dark = shade(col, 1.15), shade(col, 0.68)
    brick = style == 'brick'
    plaster(img, (0, 0, w, h), col, seed, 1.6 if brick else 1.0)
    if brick:
        for y in range(TOP, h, 6):
            d.line([(0, y), (w, y)], fill=shade(col, 0.78))
            off = 0 if (y // 6) % 2 else 7
            for x in range(off, w, 14):
                d.line([(x, y), (x, y + 5)], fill=shade(col, 0.82))
    gy = TOP + n * U_H + BELT
    # roof lip and main cornice
    roof = spec.get('roof', (100, 106, 112))
    d.rectangle([0, 0, w, 5], fill=shade(roof, 0.95))
    d.line([(0, 0), (w, 0)], fill=shade(roof, 1.3))
    d.rectangle([0, 6, w, 9], fill=CREAM if not brick else light)
    d.rectangle([0, 10, w, 12], fill=light)
    d.line([(0, 13), (w, 13)], fill=dark)
    for x in range(0, w, 6):
        d.rectangle([x, 14, x + 2, 17], fill=light)
        d.rectangle([x + 3, 14, x + 5, 17], fill=shade(col, 0.8))
    d.line([(0, 18), (w, 18)], fill=dark)
    d.line([(0, 19), (w, 19)], fill=shade(col, 0.85))
    if style in ('pilaster', 'grand'):
        # frieze band
        d.rectangle([0, 20, w, 24], fill=shade(col, 1.06))
    # the cornice overhang shades the wall below it
    for k, f in ((20, 0.78), (21, 0.84), (22, 0.9)):
        d.line([(0, k + (5 if style in ('pilaster', 'grand') else 0)), (w, k + (5 if style in ('pilaster', 'grand') else 0))], fill=shade(col, f))
    # stains below cornice
    for x in range(rr.randint(0, 9), w, rr.randint(9, 15)):
        streak(d, x, 20, rr.randint(4, 18), shade(col, 0.9), rr)
    # window grid
    pitch = spec.get('pitch', rr.choice([46, 50, 54]))
    k = max(1, (w - 30) // pitch)
    start = (w - k * pitch) // 2 + pitch // 2
    cols = [start + i * pitch for i in range(k)]
    ww = 22
    lit_p = spec.get('lit', 0.22)
    # pilasters
    if style in ('pilaster', 'grand') and k >= 3:
        for i in range(k + 1):
            if i in (0, k) or (style == 'grand' and i % 2 == 0):
                px = start - pitch // 2 + i * pitch
                px = max(6, min(w - 7, px))
                d.rectangle([px - 5, TOP, px + 4, gy - BELT], fill=light)
                d.line([(px + 5, TOP), (px + 5, gy - BELT)], fill=shade(col, 0.8))
                d.rectangle([px - 7, TOP, px + 6, TOP + 4], fill=CREAM)
    if style == 'rustic' or spec.get('quoins'):
        for qx in (0, w - 14):
            for y in range(TOP, gy - BELT, 12):
                ww2 = 14 if (y // 12) % 2 == 0 else 10
                x_ = qx if qx == 0 else w - ww2
                d.rectangle([x_, y, x_ + ww2 - 1, y + 10], fill=light)
                d.line([(x_, y + 11), (x_ + ww2 - 1, y + 11)], fill=dark)
    for s in range(n):
        sy = TOP + s * U_H
        nobile = s == n - 1
        top_floor = s == 0
        wh = 34 if top_floor else 40
        kind = 'tri' if (nobile and style in ('grand', 'pilaster')) else ('flat' if nobile else ('key' if style != 'brick' and rr.random() < 0.6 else 'plain'))
        if spec.get('sandrik') and nobile:
            kind = spec['sandrik']
        # storey string course for some styles
        if style in ('grand',) and s > 0:
            d.line([(0, sy + 2), (w, sy + 2)], fill=light)
            d.line([(0, sy + 3), (w, sy + 3)], fill=dark)
        for i, cx in enumerate(cols):
            top = sy + (16 if not top_floor else 18)
            window(d, cx, top, ww, wh, col, rr, kind, lit=rr.random() < lit_p)
        if nobile and spec.get('balcony') is not None and cols:
            i = spec['balcony'] % len(cols)
            balcony(d, cols[i], sy + 16 + wh + 6, 46, col)
    # belt course
    by = gy - BELT
    d.rectangle([0, by, w, by + 3], fill=light)
    d.line([(0, by), (w, by)], fill=CREAM)
    d.line([(0, by + 4), (w, by + 4)], fill=dark)
    d.rectangle([0, by + 5, w, gy - 1], fill=shade(col, 0.92))
    # ground floor: rustication
    gcol = shade(col, 0.93) if not brick else col
    plaster(img, (0, gy, w, h), gcol, seed + 3, 1.0)
    if brick:
        for y in range(gy, h, 6):
            d.line([(0, y), (w, y)], fill=shade(col, 0.78))
            off = 0 if (y // 6) % 2 else 7
            for x in range(off, w, 14):
                d.line([(x, y), (x, y + 5)], fill=shade(col, 0.82))
    else:
        for y in range(gy + 12, h - 12, 12):
            d.line([(0, y), (w, y)], fill=shade(gcol, 0.72))
            d.line([(0, y + 1), (w, y + 1)], fill=shade(gcol, 1.1))
    # plinth
    d.rectangle([0, h - 12, w, h - 1], fill=(124, 108, 104))
    d.line([(0, h - 12), (w, h - 12)], fill=(170, 152, 146))
    d.line([(0, h - 11), (w, h - 11)], fill=(146, 128, 122))
    for x in range(rr.randint(0, 40), w, 46):
        d.line([(x, h - 11), (x, h - 1)], fill=(96, 84, 82))
    info = {'doors': [], 'arches': [], 'height': h, 'cols': cols}
    units = list(spec.get('gf', []))
    i = 0
    ui = 0
    bottom = h - 12
    while i < len(cols):
        unit = units[ui] if ui < len(units) else {'t': 'gwin'}
        ui += 1
        t = unit['t']
        if t == 'shop' and i + 1 < len(cols):
            x0, x1 = cols[i] - pitch // 2 + 5, cols[i + 1] + pitch // 2 - 5
            span = unit.get('span', 2)
            if i + span - 1 < len(cols):
                x1 = cols[i + span - 1] + pitch // 2 - 5
            shopfront(d, img, x0, x1, gy, bottom, unit, rr)
            info.setdefault('shops', []).append((x0, x1, unit.get('text', ''), unit.get('warm', False)))
            i += span
            continue
        cx = cols[i]
        if t == 'door':
            entrance_door(d, cx, gy, bottom, gcol, unit.get('number', str(rr.randint(3, 40))), rr)
            info['doors'].append(cx)
        elif t == 'arch':
            arch(d, cx, gy, bottom, gcol, rr)
            info['arches'].append(cx)
        elif t == 'blank':
            pass
        else:
            top = gy + 26
            window(d, cx, top, 24, 46, gcol, rr, 'key', lit=rr.random() < lit_p)
            for x in range(cx - 11, cx + 12, 5):
                d.line([(x, top + 22), (x, top + 45)], fill=IRON)
            d.line([(cx - 12, top + 22), (cx + 12, top + 22)], fill=IRON)
            # basement window in plinth
            d.rectangle([cx - 10, h - 10, cx + 10, h - 3], fill=(30, 30, 36))
            d.line([(cx - 10, h - 10), (cx + 10, h - 10)], fill=(176, 160, 152))
        i += 1
    # drainpipes on building edges
    if spec.get('pipes', True):
        for x in (6, w - 7):
            drainpipe(d, x, 4, h, rr)
    # bottom contact shadow
    return img, info
