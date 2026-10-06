import sys, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

SRC, OUT = sys.argv[1], sys.argv[2]
BG = np.array([13, 17, 23], float)        # GitHub dark background
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 110   # dot columns
OUT_W = int(sys.argv[4]) if len(sys.argv) > 4 else 640

rgb = Image.open(SRC).convert("RGB")
H0, W0 = rgb.size[1], rgb.size[0]
hsv = np.asarray(rgb.convert("HSV")).astype(float)
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

# ---------- subject mask ----------
bgpix = (s <= 40) & (v > 115) & (v < 240) & (h >= 130) & (h <= 180)
subj = ~bgpix
subj = nd.binary_opening(subj, iterations=3)
subj = nd.binary_closing(subj, iterations=6)
lab, n = nd.label(subj)
subj = lab == (np.argmax(nd.sum(subj, lab, range(1, n + 1))) + 1)
subj = nd.binary_fill_holes(subj)
subj = nd.binary_erosion(subj, iterations=4)

# ---------- crop: head + upper shoulders ----------
ys, xs = np.where(subj)
top = ys.min()
cx = int(np.median(xs[ys < top + 0.35 * H0]))
crop_h = int(0.80 * H0)
y0 = max(0, top - int(0.07 * H0))
y1 = min(H0, y0 + crop_h)
half_w = int(crop_h * 0.47)
x0, x1 = max(0, cx - half_w), min(W0, cx + half_w)

lum = np.asarray(rgb.convert("L")).astype(float)[y0:y1, x0:x1]
m = subj[y0:y1, x0:x1].astype(float)
H, W = lum.shape

# ---------- tone mapping (local contrast + equalize inside subject) ----------
blur = nd.gaussian_filter(lum, 40)
detail = lum + 1.6 * (lum - blur)                  # boost local detail
detail = nd.gaussian_filter(detail, 1.2)
inside = detail[m > 0.5]
lo, hi = np.percentile(inside, 2), np.percentile(inside, 99.5)
t = np.clip((detail - lo) / (hi - lo), 0, 1)
# equalize so dark skin/hair still separates
hist, edges = np.histogram(t[m > 0.5], bins=256, range=(0, 1))
cdf = np.cumsum(hist) / hist.sum()
teq = np.interp(t, edges[:-1], cdf)
tone = 0.55 * teq + 0.45 * t
tone = tone ** 1.15

# ---------- sample on dot grid ----------
cell = W / COLS
ROWS = int(H / cell)
gy, gx = (np.arange(ROWS) + 0.5) * cell, (np.arange(COLS) + 0.5) * cell
small_tone = nd.map_coordinates(nd.gaussian_filter(tone, cell * 0.35), np.meshgrid(gy, gx, indexing="ij"), order=1)
small_m = nd.map_coordinates(nd.gaussian_filter(m, cell * 0.6), np.meshgrid(gy, gx, indexing="ij"), order=1)

rng = np.random.default_rng(7)
def fbm(shape, scales=(3, 6, 12, 24)):
    acc = np.zeros(shape)
    for i, sc in enumerate(scales):
        acc += nd.gaussian_filter(rng.standard_normal(shape), sc) * (sc ** 0.9)
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    return acc
fog = fbm((ROWS, COLS))

# distance (in cells) from silhouette for fog particles
dist = nd.distance_transform_edt(small_m < 0.5)
yy = np.arange(ROWS)[:, None] / ROWS

# bottom dissolve
bottom = np.clip((1.0 - yy) / 0.38, 0, 1) ** 1.6
dissolve = np.clip(bottom * 1.25 + (fog - 0.5) * 0.9, 0, 1)

val = np.zeros((ROWS, COLS))
inner = small_m * (0.10 + 0.90 * small_tone) * dissolve
val = np.maximum(val, inner)
# halo fog: sparse, dim particles drifting off the silhouette
halo = np.exp(-dist / 4.5) * (fog ** 2.2) * 0.55 * (small_m < 0.5)
halo *= (rng.random((ROWS, COLS)) < 0.75)
halo *= np.clip(bottom * 1.6, 0, 1)
val = np.maximum(val, halo)
# fade particles toward the frame edges so the fog has no hard box
ex = np.minimum(np.arange(COLS), COLS - 1 - np.arange(COLS)) / (COLS * 0.14)
ey = np.arange(ROWS) / (ROWS * 0.12)
frame = np.clip(ex[None, :], 0, 1) * np.clip(ey[:, None], 0, 1)
val = np.where(small_m >= 0.5, val, val * frame)
# faint ambient fog field across the frame
amb = (fog ** 4) * 0.16 * frame * (rng.random((ROWS, COLS)) < 0.35)
val = np.maximum(val, amb)

# ---------- render (supersampled) ----------
SS = 3
scale = OUT_W / W
CW = cell * scale * SS
out_h = int(ROWS * cell * scale)
canvas = np.zeros((out_h * SS, OUT_W * SS))
r_max = CW * 0.47
# stamp disc per cell via vectorised distance in each cell
cy_idx = (np.arange(out_h * SS) / CW).astype(int).clip(0, ROWS - 1)
cx_idx = (np.arange(OUT_W * SS) / CW).astype(int).clip(0, COLS - 1)
fy = (np.arange(out_h * SS) % CW) - CW / 2
fx = (np.arange(OUT_W * SS) % CW) - CW / 2
d = np.sqrt(fy[:, None] ** 2 + fx[None, :] ** 2)
V = val[cy_idx][:, cx_idx]
R = r_max * np.sqrt(np.clip(V, 0, 1)) * 0.95 + (V > 0.03) * CW * 0.06
canvas = np.clip(R - d + 0.5, 0, 1) * (0.25 + 0.75 * V)
canvas = Image.fromarray((canvas * 255).astype(np.uint8)).resize((OUT_W, out_h), Image.LANCZOS)
c = np.asarray(canvas).astype(float) / 255

# bloom
glow = nd.gaussian_filter(c, 9) * 0.55 + nd.gaussian_filter(c, 28) * 0.45
lit = np.clip(c + glow * 0.6, 0, 1)

# transparent PNG: colour is a constant fog grey, dots + glow live in alpha
fogcol = np.array([214, 221, 232], np.uint8)
a = (np.clip(lit, 0, 1) * 255).astype(np.uint8)
rgba = np.dstack([np.broadcast_to(fogcol, a.shape + (3,)), a])
Image.fromarray(rgba, "RGBA").quantize(colors=48, method=Image.FASTOCTREE).save(OUT, optimize=True)
print(rgba.shape)
