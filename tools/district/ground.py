import numpy as np
from PIL import Image
from common import T, hsh, vnoise, grid

GROUND_SRC = None

def load_src(path):
    global GROUND_SRC
    GROUND_SRC = np.array(Image.open(path).convert('RGB')).astype(np.float64)

def tex_asphalt(xs, ys, base=(63, 63, 69), s=1):
    out = np.zeros(xs.shape + (3,))
    out[:] = base
    m = vnoise(xs, ys, 48, s) - 0.5
    m2 = vnoise(xs, ys, 13, s + 1) - 0.5
    out += (m * 9 + m2 * 4)[..., None]
    sp = hsh(xs, ys, s + 2)
    out -= ((sp < 0.05) * 7)[..., None]
    out += ((sp > 0.965) * 8)[..., None]
    out += ((sp > 0.995) * 10)[..., None]
    return out

def tex_granite(xs, ys, base=(150, 141, 138), s=3, sw=48, sh=32):
    out = np.zeros(xs.shape + (3,))
    row = ys // sh
    off = (row % 2) * (sw // 2)
    sx = (xs + off) // sw
    tone = (hsh(sx, row, s) - 0.5) * 14
    out[:] = base
    out += tone[..., None]
    lx = (xs + off) % sw
    ly = ys % sh
    out += ((ly == 1) * 7 + (lx == 1) * 5)[..., None]
    out -= ((ly == sh - 1) * 10 + (lx == sw - 1) * 8)[..., None]
    seam = (ly == 0) | (lx == 0)
    out[seam] = (108, 100, 99)
    sp = hsh(xs, ys, s + 5)
    out -= ((sp < 0.06) * 9)[..., None]
    out += ((sp > 0.95) * 7)[..., None]
    return out

def tex_paving(xs, ys, s=4):
    """Reuse the approved pink paving tiles 0..2 of ground.png."""
    tx, ty = xs // T, ys // T
    idx = (hsh(tx, ty, s) * 3).astype(np.int64)
    lx, ly = xs % T, ys % T
    src = GROUND_SRC
    out = src[ly, idx * T + lx]
    sp = hsh(xs, ys, s + 1)
    out = out - ((sp < 0.02) * 6)[..., None]
    return out

def tex_cobble(xs, ys, s=6, base=(122, 113, 108)):
    sw, sh = 11, 9
    row = ys // sh
    off = (row % 2) * 5
    sx = (xs + off) // sw
    lx = (xs + off) % sw
    ly = ys % sh
    h = hsh(sx, row, s)
    out = np.zeros(xs.shape + (3,))
    out[:] = base
    out += ((h - 0.5) * 14)[..., None]
    warm = hsh(sx, row, s + 1) > 0.7
    out[warm] += (8, 2, -4)
    out += ((ly == 1) * 7 + (lx == 1) * 4)[..., None]
    out -= ((ly == sh - 2) * 6 + (lx == sw - 2) * 4)[..., None]
    gap = (ly == 0) | (lx == 0) | ((ly == sh - 1) & ((lx == 1) | (lx == sw - 1)))
    out[gap] = (92, 86, 82)
    corner = ((lx == 1) | (lx == sw - 1)) & ((ly == 1) | (ly == sh - 1))
    out[corner] = (100, 94, 90)
    return out

def tex_grass(xs, ys, s=8):
    out = np.zeros(xs.shape + (3,))
    out[:] = (98, 114, 38)
    m = vnoise(xs, ys, 20, s) - 0.5
    m2 = vnoise(xs, ys, 6, s + 1) - 0.5
    out += (m * 22)[..., None] * np.array([0.8, 1.0, 0.4])
    out += (m2 * 10)[..., None]
    sp = hsh(xs, ys, s + 2)
    tuft = (sp < 0.03)
    out[tuft] = (74, 92, 26)
    out[sp > 0.985] = (140, 150, 60)
    # occasional fallen leaves (November)
    leaf = hsh(xs // 2, ys // 2, s + 3) > 0.993
    out[leaf] = (196, 140, 50)
    return out

def tex_sand(xs, ys, s=9):
    out = np.zeros(xs.shape + (3,))
    out[:] = (192, 166, 122)
    m = vnoise(xs, ys, 16, s) - 0.5
    out += (m * 12)[..., None]
    sp = hsh(xs, ys, s + 1)
    out -= ((sp < 0.08) * 12)[..., None]
    out += ((sp > 0.96) * 10)[..., None]
    return out

def tex_water(xs, ys, s=10):
    out = np.zeros(xs.shape + (3,))
    out[:] = (40, 66, 76)
    m = vnoise(xs, ys, 60, s) - 0.5
    out += (m * 10)[..., None]
    # wave dashes: short horizontal strokes
    wy = ys // 6
    wx = (xs + (hsh(wy, 0, s) * 64).astype(np.int64)) // 14
    hh = hsh(wx, wy, s + 1)
    lx = (xs + (hsh(wy, 0, s) * 64).astype(np.int64)) % 14
    dash = (hh > 0.72) & (lx < 7) & (ys % 6 == 0)
    out[dash] = (70, 106, 114)
    dash2 = (hh > 0.93) & (lx < 4) & (ys % 6 == 1)
    out[dash2] = (124, 160, 164)
    dark = (hh < 0.12) & (lx < 9) & (ys % 6 == 3)
    out[dark] = (32, 54, 64)
    return out
