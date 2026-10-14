"""Display sheets for the VH2 helm library: a labelled grid of front views (like an evolution chart) and one of 3/4 views.

Same orthographic painter's renderer and lights as tools/render.py, plus per-face colour: faces inside the helm's visor
outline and below its raised frame are drawn as dark glass, so the visor shapes read at thumbnail size. Display only;
the print files are untouched single solids.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

import vh2
from render import FILL, KEY, RIM, _hex, view_matrix
from sdfkit import decimate

SHELL, GLASS = "#8d99a3", "#2b3d57"
VISORS = {"VH2-04": vh2.VISOR_HEAVY, "VH2-12": vh2.VISOR_HEAVY, "VH2-10": None}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def face_colors(ident, m):
    cols = np.tile(_hex(SHELL), (len(m.faces), 1))
    poly = VISORS.get(ident, vh2.VISOR)
    if poly is None:
        return cols
    c = m.triangles_center
    inside = (vh2.wrap_prism(poly)(c) < -0.03) & (vh2.SKULL(c) < 0.12) & (c[:, 1] < 0)
    cols[inside] = _hex(GLASS)
    return cols


def draw(m, cols, az, el, size, ss=2, rad=None, center=None, bg=(236, 237, 240)):
    R = view_matrix(az, el)
    c = center if center is not None else (m.vertices.min(axis=0) + m.vertices.max(axis=0)) / 2
    rad = rad or np.linalg.norm(m.vertices - c, axis=1).max() * 1.04
    V = (m.vertices - c) @ R.T
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
    return img.resize((size, size), Image.LANCZOS)


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


def sheets(pkg, mid, size=300):
    pkg = Path(pkg)
    up = pkg / "build" / "upright"
    meshes, labels = [], []
    for k, (name, note, _) in vh2.VH2.items():
        stl = up / f"{k.lower()}-{name.lower().replace(',', '').replace(' ', '-')}.stl"
        m = trimesh.load(stl, process=True)   # merge the STL triangle soup into a closed mesh
        m = decimate(m, 70_000)
        meshes.append((k, m, face_colors(k, m)))
        labels.append((f"{k} {name}", note.split(":")[0]))
    # one common scale and centre (helm frame) so the helms compare like an evolution chart
    centre = np.array([0.0, 0.0, 3.3])
    rad = 6.2
    out = pkg / "images"
    out.mkdir(exist_ok=True)
    sub = "Original Aster Compact design: gull-wing wrap visor split by the keel, layered crown/temple/nape plates, V-prow respirator. 1.6 mm D-flat peg, 30 mm heroic."
    front = [draw(m, c, 0, 3, size, center=centre, rad=rad) for _, m, c in meshes]
    grid(front, labels, 4, out / f"{mid}-sheet-front.png", "Vigil helm Mk 2 (VH2): front", sub, size)
    tq = [draw(m, c, -35, 12, size, center=centre, rad=rad) for _, m, c in meshes]
    grid(tq, labels, 4, out / f"{mid}-sheet-34.png", "Vigil helm Mk 2 (VH2): 3/4 front", sub, size)
    side = [draw(m, c, 90, 4, size, center=centre, rad=rad) for _, m, c in meshes]
    grid(side, labels, 4, out / f"{mid}-sheet-side.png", "Vigil helm Mk 2 (VH2): right side", sub, size)
