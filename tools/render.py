"""Orthographic turntable renders of assembled parts (numpy + Pillow, painter's algorithm with back-face culling).

Good enough to judge silhouette, mass and surface on closed, finely tessellated meshes; it is not a path tracer.
Lights: warm key from upper front-left, cool fill from the right, rim from behind (stated so the renders are reproducible).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255


def view_matrix(az, el):
    """az: degrees the model turns about z (0 = front, the camera on -y); el: camera elevation in degrees."""
    a, e = math.radians(az), math.radians(el)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
    return Rx @ Rz


KEY = np.array([-0.55, -0.65, 0.55])
FILL = np.array([0.8, -0.35, 0.1])
RIM = np.array([0.1, 0.9, 0.5])


def render(meshes, path, views=((-35, 12, "3/4 front"), (0, 4, "front"), (90, 4, "side (right)"), (180, 10, "back")),
           size=560, ss=2, title=None, bg=(232, 233, 236)):
    """meshes: list of (trimesh, '#rrggbb'). Writes one PNG strip with a panel per view."""
    allv = np.vstack([m.vertices for m, _ in meshes])
    c = (allv.min(axis=0) + allv.max(axis=0)) / 2
    rad = np.linalg.norm(allv - c, axis=1).max() * 1.04
    S = size * ss
    panels = []
    for az, el, label in views:
        R = view_matrix(az, el)
        tris, cols, depth = [], [], []
        for m, col in meshes:
            V = (m.vertices - c) @ R.T
            Fc = m.faces
            T = V[Fc]
            n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            vis = n[:, 1] < 0  # facing the camera (camera looks along +y)
            T, n = T[vis], n[vis]
            lk = np.clip(n @ (KEY / np.linalg.norm(KEY)), 0, 1)
            lf = np.clip(n @ (FILL / np.linalg.norm(FILL)), 0, 1)
            lr = np.clip(n @ (RIM / np.linalg.norm(RIM)), 0, 1)
            h = KEY / np.linalg.norm(KEY) + np.array([0, -1, 0])
            spec = np.clip(n @ (h / np.linalg.norm(h)), 0, 1) ** 24
            base = _hex(col)
            shade = (base[None] * (0.20 + 0.78 * lk[:, None] * np.array([1.0, 0.96, 0.9]) + 0.28 * lf[:, None] * np.array([0.8, 0.9, 1.05]))
                     + 0.35 * lr[:, None] + 0.22 * spec[:, None])
            tris.append(T)
            cols.append(np.clip(shade, 0, 1))
            depth.append(T[:, :, 1].mean(axis=1))
        T, C, Dp = np.vstack(tris), np.vstack(cols), np.concatenate(depth)
        order = np.argsort(-Dp)
        img = Image.new("RGB", (S, S), bg)
        dr = ImageDraw.Draw(img)
        k = S / (2 * rad)
        X = (T[:, :, 0] * k + S / 2)
        Y = (-T[:, :, 2] * k + S / 2)
        Ci = (C * 255).astype(np.uint8)
        for i in order:
            dr.polygon([(X[i, 0], Y[i, 0]), (X[i, 1], Y[i, 1]), (X[i, 2], Y[i, 2])], fill=tuple(Ci[i]))
        img = img.resize((size, size), Image.LANCZOS)
        ImageDraw.Draw(img).text((10, 8), label, fill=(60, 60, 70))
        panels.append(img)
    W = size * len(panels)
    top = 26 if title else 0
    sheet = Image.new("RGB", (W, size + top), bg)
    if title:
        ImageDraw.Draw(sheet).text((10, 6), title, fill=(30, 30, 40))
    for i, p in enumerate(panels):
        sheet.paste(p, (i * size, top))
    sheet.save(path)
    return path
