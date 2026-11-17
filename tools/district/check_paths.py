import re, sys, numpy as np
from collections import deque
src = open('scripts/district_layout.gd').read()
W, H = map(int, re.search(r'MAP_SIZE := Vector2\((\d+), (\d+)\)', src).groups())
ax, ay = map(int, re.search(r'ARRIVAL := Vector2\((\d+), (\d+)\)', src).groups())
rd = list(map(int, re.search(r'RESTAURANT_DOOR := Rect2\((\d+), (\d+), (\d+), (\d+)\)', src).groups()))
sol = src[src.index('const SOLIDS'):src.index('const AREAS')]
rects = [tuple(map(int, m)) for m in re.findall(r'Rect2\((-?\d+), (-?\d+), (\d+), (\d+)\)', sol)]
S = 4; R = 17
gw, gh = W // S, H // S
free = np.ones((gh, gw), bool)
for x, y, w, h in rects:
    x0, y0, x1, y1 = (x - R) // S, (y - R) // S, -(-(x + w + R) // S), -(-(y + h + R) // S)
    free[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = False
free[:R // S + 1, :] = free[-(R // S + 1):, :] = False
free[:, :R // S + 1] = free[:, -(R // S + 1):] = False
start = (ay // S, ax // S)
print('start free', free[start])
dist = np.full(free.shape, -1); dist[start] = 0
q = deque([start])
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < gh and 0 <= nx < gw and free[ny, nx] and dist[ny, nx] < 0:
            dist[ny, nx] = dist[y, x] + 1; q.append((ny, nx))
goal = ((rd[1] + rd[3] + 20) // S, (rd[0] + rd[2] // 2) // S)
print('door front free', free[goal], 'reachable', dist[goal] >= 0, 'path px', dist[goal] * S, 'seconds', round(dist[goal] * S / 112.5, 1))
print('reachable share of free', round((dist >= 0).sum() / free.sum(), 3))
from PIL import Image
im = np.zeros((gh, gw, 3), np.uint8); im[free] = (90, 90, 90); im[dist >= 0] = (200, 200, 200)
Image.fromarray(im).save('/workspace/shots/walkable.png')
