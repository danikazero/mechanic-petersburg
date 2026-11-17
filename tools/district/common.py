import numpy as np

T = 32
MASK = np.uint64(0xFFFFFFFF)

def hsh(x, y, s=0):
    """Deterministic hash -> float in [0,1). x, y numpy int arrays or ints."""
    x = np.asarray(x, dtype=np.uint64)
    y = np.asarray(y, dtype=np.uint64)
    h = (x * np.uint64(374761393) + y * np.uint64(668265263) + np.uint64(s * 2654435761 % 4294967296)) & MASK
    h = ((h ^ (h >> np.uint64(13))) * np.uint64(1274126177)) & MASK
    h = h ^ (h >> np.uint64(16))
    return (h & MASK).astype(np.float64) / 4294967296.0

def vnoise(xs, ys, cell, s=0):
    gx, gy = xs // cell, ys // cell
    fx, fy = (xs % cell) / cell, (ys % cell) / cell
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a = hsh(gx, gy, s); b = hsh(gx + 1, gy, s); c = hsh(gx, gy + 1, s); d = hsh(gx + 1, gy + 1, s)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def grid(x0, y0, w, h):
    ys, xs = np.mgrid[y0:y0 + h, x0:x0 + w]
    return xs.astype(np.int64), ys.astype(np.int64)

def shade(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c[:3])

def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))

def add(c, v):
    return tuple(max(0, min(255, int(c[i] + v))) for i in range(3))
