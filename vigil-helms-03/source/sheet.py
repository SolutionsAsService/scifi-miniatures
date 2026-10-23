"""Display renders for the VH4 helm library (0.3): orthographic painter's renderer (lights as tools/render.py) with per-face
colour: faces flagged as glass by the helm's own glass masks (tools/helms3.py) are drawn dark blue so the visor shapes
read at thumbnail size. Display only; the print files are untouched single solids.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

from render import FILL, KEY, RIM, _hex, view_matrix

SHELL, GLASS = "#8d99a3", "#2b3d57"
def _font_path(names):
    """First font that exists: DejaVu on Linux, Arial/Segoe on Windows (PIL default otherwise)."""
    for p in names:
        if Path(p).exists():
            return p
    return None


FONT = _font_path(["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"])
FONT_B = _font_path(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"])
_truetype = ImageFont.truetype
ImageFont.truetype = lambda path, size: _truetype(path, size) if path else ImageFont.load_default()
CENTRE, RAD = np.array([0.0, 0.3, 3.6]), 6.4      # common helm frame for every sheet cell (mm)


def colours(m, mask, shell=SHELL):
    cols = np.tile(_hex(shell), (len(m.faces), 1))
    if mask is not None:
        cols[mask] = _hex(GLASS)
    return cols


def draw(m, cols, az, el, size, ss=2, rad=RAD, center=CENTRE, bg=(236, 237, 240), label=None):
    R = view_matrix(az, el)
    V = (m.vertices - center) @ R.T
    T = V[m.faces]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    vis = n[:, 1] < 0
    T, n, base = T[vis], n[vis], cols[vis]
    lk = np.clip(n @ (KEY / np.linalg.norm(KEY)), 0, 1)
    lf = np.clip(n @ (FILL / np.linalg.norm(FILL)), 0, 1)
    lr = np.clip(n @ (RIM / np.linalg.norm(RIM)), 0, 1)
    h = KEY / np.linalg.norm(KEY) + np.array([0, -1, 0])
    spec = np.clip(n @ (h / np.linalg.norm(h)), 0, 1) ** 24
    shade = (base * (0.20 + 0.78 * lk[:, None] * np.array([1.0, 0.96, 0.9]) + 0.28 * lf[:, None] * np.array([0.8, 0.9, 1.05]))
             + 0.35 * lr[:, None] + 0.22 * spec[:, None])
    C = (np.clip(shade, 0, 1) * 255).astype(np.uint8)
    S = size * ss
    img = Image.new("RGB", (S, S), bg)
    dr = ImageDraw.Draw(img)
    k = S / (2 * rad)
    X, Y = T[:, :, 0] * k + S / 2, -T[:, :, 2] * k + S / 2
    for i in np.argsort(-T[:, :, 1].mean(axis=1)):
        dr.polygon([(X[i, 0], Y[i, 0]), (X[i, 1], Y[i, 1]), (X[i, 2], Y[i, 2])], fill=tuple(C[i]))
    img = img.resize((size, size), Image.LANCZOS)
    if label:
        ImageDraw.Draw(img).text((8, 6), label, fill=(60, 60, 70), font=ImageFont.truetype(FONT, 13))
    return img


def strip(m, mask, path, title, views=((-35, 12, "3/4 front"), (0, 3, "front"), (90, 4, "right side"), (180, 10, "back")), size=420):
    cols = colours(m, mask)
    cells = [draw(m, cols, az, el, size, label=lab) for az, el, lab in views]
    top = 30
    sh = Image.new("RGB", (size * len(cells), size + top), (236, 237, 240))
    ImageDraw.Draw(sh).text((10, 7), title, fill=(30, 30, 40), font=ImageFont.truetype(FONT_B, 15))
    for i, c in enumerate(cells):
        sh.paste(c, (i * size, top))
    sh.save(path)
    return path


def grid(cells, labels, cols, path, title, sub, size):
    rows = (len(cells) + cols - 1) // cols
    f, fb, ft = ImageFont.truetype(FONT, 15), ImageFont.truetype(FONT_B, 16), ImageFont.truetype(FONT_B, 30)
    top, lab = 92, 44
    sheet = Image.new("RGB", (cols * size, top + rows * (size + lab)), (236, 237, 240))
    d = ImageDraw.Draw(sheet)
    d.text((18, 14), title, fill=(40, 44, 52), font=ft)
    d.text((20, 56), sub, fill=(90, 96, 106), font=f)
    for i, (img, (a, b)) in enumerate(zip(cells, labels)):
        x, y = (i % cols) * size, top + (i // cols) * (size + lab)
        sheet.paste(img, (x, y))
        d.text((x + size / 2, y + size + 2), a, fill=(40, 44, 52), font=fb, anchor="ma")
        d.text((x + size / 2, y + size + 22), b, fill=(96, 102, 112), font=f, anchor="ma")
    sheet.save(path)
    return path


def load(pkg, slug):
    """Print STL as triangle soup (face order = export order) + the glass mask saved by build.py."""
    pkg = Path(pkg)
    m = trimesh.load(pkg / "build" / "upright" / f"{slug}.stl", process=False)
    mp = pkg / "build" / "glass" / f"{slug}.npy"
    mask = np.load(mp) if mp.exists() else None
    if mask is not None and len(mask) != len(m.faces):
        mask = None
    return m, mask


def sheets(pkg, mid, items, size=300):
    """items: list of (ident, name, note, slug). Front, 3/4 and side sheets on one common scale."""
    pkg = Path(pkg)
    out = pkg / "images"
    out.mkdir(exist_ok=True)
    data = []
    for ident, name, note, slug in items:
        m, mask = load(pkg, slug)
        data.append((m, colours(m, mask), (f"{ident} {name}", note.split(":")[0])))
    sub = ("Original Aster Compact design: split-chevron glass and keel line on every helm; silhouettes differ. "
           "1.6 mm D-flat peg, 30 mm heroic.")
    paths = []
    for az, el, tag, lab in ((0, 3, "front", "front"), (-35, 12, "34", "3/4 front"), (90, 4, "side", "right side"),
                             (180, 8, "back", "back")):
        cells = [draw(m, c, az, el, size) for m, c, _ in data]
        paths.append(grid(cells, [l for _, _, l in data], 6, out / f"{mid}-sheet-{tag}.png",
                          f"Vigil helm library 0.3 (VH4): {lab}", sub, size))
    return paths
