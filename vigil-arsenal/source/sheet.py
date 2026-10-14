#!/usr/bin/env python3
"""Display sheets for the Vigil arsenal (VW2 series): side-profile line-up at one common scale and 3/4 close-ups.

Renderer: the tools/render.py painter's algorithm (orthographic, back-face culled, same key / fill / rim lights),
drawn per weapon into a labelled sheet. Reads build/upright/*.stl (as modelled, weapon frame) unless meshes are given.
Run after build.py with the sculpt venv:  python source/sheet.py
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from render import FILL, KEY, RIM, _hex, view_matrix  # noqa: E402
from sdfkit import decimate  # noqa: E402

BG = (236, 237, 240)
INK = (28, 30, 36)
GUN = "#6b737d"
UPRIGHT_Z = ("VW2-13", "VW2-14")      # grip along z: lay them muzzle/blade to +x for the line-up


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def shade(n, col):
    k, f, r = (v / np.linalg.norm(v) for v in (KEY, FILL, RIM))
    lk, lf, lr = (np.clip(n @ v, 0, 1) for v in (k, f, r))
    h = k + np.array([0, -1, 0])
    sp = np.clip(n @ (h / np.linalg.norm(h)), 0, 1) ** 24
    base = _hex(col)
    c = (base[None] * (0.22 + 0.78 * lk[:, None] * np.array([1.0, 0.96, 0.9]) + 0.3 * lf[:, None] * np.array([0.8, 0.9, 1.05]))
         + 0.3 * lr[:, None] + 0.2 * sp[:, None])
    return (np.clip(c, 0, 1) * 255).astype(np.uint8)


def project(m, R):
    V = m.vertices @ R.T
    return V


def draw_mesh(img, m, R, k, cx, cy, center, col=GUN, ss=2):
    """Paint mesh m (view R, k px/mm) with its 'center' (view coords x, z) at pixel (cx, cy) of img (supersampled)."""
    V = project(m, R)
    T = V[m.faces]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    vis = n[:, 1] < 0
    T, n = T[vis], n[vis]
    C = shade(n, col)
    order = np.argsort(-T[:, :, 1].mean(axis=1))
    Xp = (T[:, :, 0] - center[0]) * k * ss + cx * ss
    Yp = -(T[:, :, 2] - center[1]) * k * ss + cy * ss
    dr = ImageDraw.Draw(img)
    for i in order:
        dr.polygon([(Xp[i, 0], Yp[i, 0]), (Xp[i, 1], Yp[i, 1]), (Xp[i, 2], Yp[i, 2])], fill=tuple(C[i]))


def lay_flat(ident, m):
    if ident in UPRIGHT_Z:
        m = m.copy()
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))   # z (blade/head) -> +x
    return m


def side_sheet(items, path, title, k=34.0, cols=2, cell_w=980, ss=2):
    """items: [(ident, name, mesh)]. Side profile (camera on -y, muzzle right), every weapon at k px/mm."""
    R = view_matrix(0, 0)
    flat = [(i, n, lay_flat(i, m)) for i, n, m in items]
    rows = [flat[r::cols] for r in range(cols)]                  # column-major: col c gets items c, c+cols, ...
    rows = [flat[j * cols:(j + 1) * cols] for j in range((len(flat) + cols - 1) // cols)]
    heights = [max((m.bounds[1][2] - m.bounds[0][2]) for _, _, m in row) * k + 70 for row in rows]
    top = 90
    W, H = cols * cell_w, int(top + sum(heights) + 60)
    img = Image.new("RGB", (W * ss, H * ss), BG)
    labels = []
    y = top
    for row, hgt in zip(rows, heights):
        for c, (ident, name, m) in enumerate(row):
            bb = m.bounds
            ctr = ((bb[0][0] + bb[1][0]) / 2, (bb[0][2] + bb[1][2]) / 2)
            cx, cy = c * cell_w + cell_w / 2, y + (hgt - 40) / 2
            draw_mesh(img, m, R, k, cx, cy, ctr, ss=ss)
            L = bb[1][0] - bb[0][0]
            labels.append(((c * cell_w + 24, y + hgt - 34), f"{ident}  {name}   ({L:.1f} mm)"))
        y += hgt
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    d.text((24, 22), title, fill=INK, font=font(30))
    d.text((24, 58), f"Side profile, orthographic, common scale {k:.0f} px/mm (30 mm heroic, 1:56). Muzzle / blade to the right.",
           fill=(80, 84, 92), font=font(18))
    for (x, yy), t in labels:
        d.text((x, yy), t, fill=INK, font=font(19))
    # 10 mm scale bar
    x0, y0 = W - 24 - 10 * k, H - 36
    d.rectangle([x0, y0, x0 + 10 * k, y0 + 6], fill=INK)
    d.text((x0, y0 - 24), "10 mm", fill=INK, font=font(16))
    img.save(path)
    return path


def closeups(items, path, title, cols=4, cell=(620, 430), az=-35, el=22, ss=2):
    """3/4 close-ups: every weapon fills its own cell (own scale, stated in the label)."""
    R = view_matrix(az, el)
    rows = (len(items) + cols - 1) // cols
    top = 70
    W, H = cols * cell[0], top + rows * cell[1]
    img = Image.new("RGB", (W * ss, H * ss), BG)
    labels = []
    for j, (ident, name, m) in enumerate(items):
        V = m.vertices @ R.T
        lo, hi = V.min(axis=0), V.max(axis=0)
        k = min((cell[0] - 50) / (hi[0] - lo[0]), (cell[1] - 80) / (hi[2] - lo[2]))
        cx, cy = (j % cols) * cell[0] + cell[0] / 2, top + (j // cols) * cell[1] + (cell[1] - 30) / 2
        R0 = np.eye(3)
        Vm = trimesh.Trimesh(V, m.faces, process=False)
        draw_mesh(img, Vm, R0, k, cx, cy, ((lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2), ss=ss)
        labels.append((((j % cols) * cell[0] + 16, top + (j // cols + 1) * cell[1] - 34), f"{ident}  {name}  ({k:.0f} px/mm)"))
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    d.text((20, 18), title, fill=INK, font=font(26))
    for (x, y), t in labels:
        d.text((x, y), t, fill=INK, font=font(17))
    img.save(path)
    return path


def load_items(tris=90_000):
    sys.path.insert(0, str(PKG.parent / "tools"))
    import arsenal as A
    import bitspack
    out = []
    for ident, (name, _, _) in A.WEAPONS2.items():
        m = trimesh.load(PKG / "build" / "upright" / f"{bitspack.slug(ident, name)}.stl")
        out.append((ident, name, decimate(m, tris)))
    return out


def sheets(items, mid="vigil-arsenal", out=None):
    out = Path(out or PKG / "images")
    out.mkdir(exist_ok=True)
    paths = [side_sheet(items, out / f"{mid}-sheet.png", "Vigil arsenal VW2-01..16: the set in side profile")]
    half = (len(items) + 1) // 2
    paths.append(closeups(items[:half], out / f"{mid}-closeups-1.png", "Vigil arsenal: 3/4 close-ups, VW2-01..08"))
    paths.append(closeups(items[half:], out / f"{mid}-closeups-2.png", "Vigil arsenal: 3/4 close-ups, VW2-09..16"))
    return paths


if __name__ == "__main__":
    print(sheets(load_items()))
