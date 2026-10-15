#!/usr/bin/env python3
"""Display sheets for the Vigil arsenal VW3: guns in side profile at one common scale, blades face-on at one common
scale, and 3/4 close-ups (each part fills its cell; px/mm stated in the label).

Renderer: the tools/render.py lighting (orthographic, painter's algorithm, back-face culled; warm key upper front-left,
cool fill right, rim behind). Reads build/upright/*.stl; render copies are simplified with manifold3d (preview only).
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
GUN, BLADE = "#6b737d", "#8a929b"
MID = "vigil-arsenal-vw3"


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


def draw_mesh(img, m, R, k, cx, cy, center, col, ss=2):
    T = (m.vertices @ R.T)[m.faces]
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


def scale_bar(d, W, H, k, label="10 mm", top=False):
    x0, y0 = W - 24 - 10 * k, (70 if top else H - 36)
    d.rectangle([x0, y0, x0 + 10 * k, y0 + 6], fill=INK)
    d.text((x0, y0 - 24), label, fill=INK, font=font(16))


def gun_sheet(items, path, k=30.0, cols=2, cell_w=820, ss=2):
    """Side profile (camera on -y, muzzle right), every gun at k px/mm."""
    R = view_matrix(0, 0)
    rows = [items[j * cols:(j + 1) * cols] for j in range((len(items) + cols - 1) // cols)]
    heights = [max((m.bounds[1][2] - m.bounds[0][2]) for _, _, m in row) * k + 70 for row in rows]
    top = 90
    W, H = cols * cell_w, int(top + sum(heights) + 60)
    img = Image.new("RGB", (W * ss, H * ss), BG)
    labels, y = [], top
    for row, hgt in zip(rows, heights):
        for c, (ident, name, m) in enumerate(row):
            bb = m.bounds
            draw_mesh(img, m, R, k, c * cell_w + cell_w / 2, y + (hgt - 40) / 2, ((bb[0][0] + bb[1][0]) / 2, (bb[0][2] + bb[1][2]) / 2), GUN, ss)
            labels.append(((c * cell_w + 24, y + hgt - 34), f"{ident}  {name}   ({bb[1][0] - bb[0][0]:.1f} mm)"))
        y += hgt
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    d.text((24, 22), "Vigil arsenal VW3-01..14: guns in side profile", fill=INK, font=font(30))
    d.text((24, 58), f"Orthographic, common scale {k:.0f} px/mm (30 mm heroic, 1:56). Muzzle to the right. Lengths = measured x extent of each print file.",
           fill=(80, 84, 92), font=font(17))
    for (x, yy), t in labels:
        d.text((x, yy), t, fill=INK, font=font(18))
    scale_bar(d, W, H, k)
    img.save(path)
    return path


def blade_sheet(items, path, k=24.0, cell_w=300, ss=2):
    """Blades face-on (camera on -y), standing, every blade at k px/mm."""
    R = view_matrix(0, 0)
    hmax = max(m.bounds[1][2] - m.bounds[0][2] for _, _, m in items)
    top, W = 90, cell_w * len(items)
    H = int(top + hmax * k + 120)
    img = Image.new("RGB", (W * ss, H * ss), BG)
    labels = []
    for j, (ident, name, m) in enumerate(items):
        bb = m.bounds
        zc = (bb[0][2] + bb[1][2]) / 2
        cy = top + 20 + hmax * k - (bb[1][2] - bb[0][2]) * k / 2          # all blades share one base line
        draw_mesh(img, m, R, k, j * cell_w + cell_w / 2, cy, ((bb[0][0] + bb[1][0]) / 2, zc), BLADE, ss)
        labels.append(((j * cell_w + 14, H - 92), f"{ident}", f"{name}", f"{bb[1][2] - bb[0][2]:.1f} mm long"))
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    d.text((24, 22), "Vigil power blades VB3-01..06", fill=INK, font=font(30))
    d.text((24, 58), f"Face-on, orthographic, common scale {k:.0f} px/mm. Edges are 0.5 mm flats; grips fit the Vigil gauntlet.",
           fill=(80, 84, 92), font=font(17))
    for (x, yy), a, b, c in labels:
        d.text((x, yy), a, fill=INK, font=font(18))
        d.text((x, yy + 22), b, fill=INK, font=font(15))
        d.text((x, yy + 42), c, fill=(80, 84, 92), font=font(15))
    scale_bar(d, W, H, k, top=True)
    img.save(path)
    return path


def closeups(items, path, title, cols=5, cell=(500, 380), az=-35, el=22, ss=2):
    R = view_matrix(az, el)
    rows = (len(items) + cols - 1) // cols
    top = 70
    W, H = cols * cell[0], top + rows * cell[1]
    img = Image.new("RGB", (W * ss, H * ss), BG)
    labels = []
    for j, (ident, name, m) in enumerate(items):
        if ident.startswith("VB"):       # lay blades blade-to-the-right for the close-up
            m = m.copy()
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
        V = m.vertices @ R.T
        lo, hi = V.min(axis=0), V.max(axis=0)
        k = min((cell[0] - 40) / (hi[0] - lo[0]), (cell[1] - 70) / (hi[2] - lo[2]))
        cx, cy = (j % cols) * cell[0] + cell[0] / 2, top + (j // cols) * cell[1] + (cell[1] - 30) / 2
        draw_mesh(img, trimesh.Trimesh(V, m.faces, process=False), np.eye(3), k, cx, cy, ((lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2),
                  BLADE if ident.startswith("VB") else GUN, ss)
        labels.append((((j % cols) * cell[0] + 14, top + (j // cols + 1) * cell[1] - 32), f"{ident} {name} ({k:.0f} px/mm)"))
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    d.text((20, 18), title, fill=INK, font=font(26))
    for (x, y), t in labels:
        d.text((x, y), t, fill=INK, font=font(15))
    img.save(path)
    return path


def load_items(tris=70_000):
    import arsenal3 as A3
    import build as B
    out = []
    for ident, name, _ in B.items():
        m = trimesh.load(PKG / "build" / "upright" / f"{B.slug(ident, name)}.stl")   # process=True: merge STL vertices
        out.append((ident, name, decimate(m, tris)))
    return out


def sheets(items, out=None):
    out = Path(out or PKG / "images")
    out.mkdir(exist_ok=True)
    guns = [t for t in items if t[0].startswith("VW3")]
    blades = [t for t in items if t[0].startswith("VB3")]
    return [gun_sheet(guns, out / f"{MID}-sheet.png"),
            blade_sheet(blades, out / f"{MID}-blades.png"),
            closeups(guns[:10], out / f"{MID}-closeups-1.png", "Vigil arsenal VW3: 3/4 close-ups, VW3-01..10"),
            closeups(guns[10:] + blades, out / f"{MID}-closeups-2.png", "Vigil arsenal VW3: 3/4 close-ups, VW3-11..14 and VB3-01..06")]


if __name__ == "__main__":
    print(sheets(load_items()))
