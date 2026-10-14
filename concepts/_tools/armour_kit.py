"""Armour-lane concept blockout kit (ARMOUR, WALKERS & DRONES concepts for the Vigil line).

Fast, primitive-based blockouts at 1:56 print scale (mm, z up, vehicles face -y like the Vigil figures, their left on +x),
a stand-in Vigil rifleman for scale, and a painter's-algorithm renderer that writes a labelled hero view and a
shared-scale orthographic turnaround. Concept quality only: no print checks, no supports, no tolerances.

Lighting follows tools/render.py (warm key upper front-left, cool fill right, rim behind) so the sheets sit with the
figure renders.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCALE = 56.0                       # 1:56, 30 mm heroic
MM_PER_M = 1000.0 / SCALE          # 17.857 mm per in-world metre
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# palette (Aster Compact: slate armour, bone accents, amber chevron lenses)
HULL = "#7d8a78"      # vehicle olive-slate
HULL2 = "#68745f"
PLATE = "#97a38f"
DARK = "#3e4246"
METAL = "#8c9096"
BONE = "#d8cfb4"
AMBER = "#f0a83a"
VIGIL = "#6f7f95"
VIGIL2 = "#56657a"
BASE = "#4a4d52"


def m(x):
    """in-world metres to print mm."""
    return x * MM_PER_M


def v3(*a):
    if len(a) == 1:
        a = a[0]
    return np.asarray(a, dtype=float)


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis)[:3, :3]


def _tf(mesh, R=None, t=None):
    T = np.eye(4)
    if R is not None:
        T[:3, :3] = R
    if t is not None:
        T[:3, 3] = t
    mesh.apply_transform(T)
    return mesh


# ------------------------------------------------------------------------------------------------ primitives
def box(size, center=(0, 0, 0), R=None):
    return _tf(trimesh.creation.box(extents=size), R, v3(center))


def hull(points):
    return trimesh.convex.convex_hull(np.asarray(points, dtype=float))


def cbox(size, center=(0, 0, 0), ch=0.5, R=None):
    """Chamfered box (all edges bevelled by ch)."""
    sx, sy, sz = (s / 2 for s in size)
    ch = min(ch, sx * 0.9, sy * 0.9, sz * 0.9)
    pts = []
    for X in (-1, 1):
        for Y in (-1, 1):
            for Z in (-1, 1):
                pts += [(X * (sx - ch), Y * sy, Z * (sz - ch)), (X * sx, Y * (sy - ch), Z * (sz - ch)),
                        (X * (sx - ch), Y * (sy - ch), Z * sz)]
    mh = hull(pts)
    return _tf(mh, R, v3(center))


def beam(p0, p1, w, d, ch=0.5, ref=(0, 0, 1), ext=0.0):
    """Chamfered bar from p0 to p1 (extended by ext at both ends): w across, d in the plane holding ref."""
    p0, p1 = v3(p0), v3(p1)
    a = p1 - p0
    L = float(np.linalg.norm(a))
    z = a / L
    r = v3(ref) if abs(z @ v3(ref)) < 0.95 else v3(1, 0, 0)
    x = np.cross(z, r)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return cbox((w, d, L + 2 * ext), (p0 + p1) / 2, ch, np.stack([x, y, z], axis=1))


def wedge(x0, x1, y0, y1, z0, z1, top_inset=(0, 0, 0, 0), bot_inset=(0, 0, 0, 0)):
    """Box with insets on top/bottom faces (insets: -x, +x, -y, +y) -> sloped glacis/plates."""
    a, b, c, d = top_inset
    e, f, g, h = bot_inset
    pts = [(x0 + e, y0 + g, z0), (x1 - f, y0 + g, z0), (x0 + e, y1 - h, z0), (x1 - f, y1 - h, z0),
           (x0 + a, y0 + c, z1), (x1 - b, y0 + c, z1), (x0 + a, y1 - d, z1), (x1 - b, y1 - d, z1)]
    return hull(pts)


def cyl(p0, p1, r, sections=28):
    p0, p1 = v3(p0), v3(p1)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    c = trimesh.creation.cylinder(radius=r, height=L, sections=sections)
    z = np.array([0, 0, 1.0])
    T = trimesh.geometry.align_vectors(z, d / L)
    c.apply_transform(T)
    c.apply_translation((p0 + p1) / 2)
    return c


def cone(p0, p1, r0, r1, sections=28):
    p0, p1 = v3(p0), v3(p1)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    n = d / L
    a = np.cross(n, [0, 0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(n, a)
    pts = []
    for i in range(sections):
        t = 2 * math.pi * i / sections
        for p, r in ((p0, r0), (p1, r1)):
            pts.append(p + r * (math.cos(t) * a + math.sin(t) * b))
    return hull(pts)


def sphere(c, r, sub=2):
    s = trimesh.creation.icosphere(subdivisions=sub, radius=r)
    s.apply_translation(v3(c))
    return s


def ellipsoid(c, radii, R=None, sub=3):
    s = trimesh.creation.icosphere(subdivisions=sub, radius=1.0)
    s.apply_scale(radii)
    return _tf(s, R, v3(c))


def capsule(p0, p1, r, sub=2):
    a = trimesh.creation.icosphere(subdivisions=sub, radius=r)
    return hull(np.vstack([a.vertices + v3(p0), a.vertices + v3(p1)]))


def wheel(c, r, w, axis=(1, 0, 0), hub=0.45):
    c, ax = v3(c), v3(axis) / np.linalg.norm(axis)
    tyre = cyl(c - ax * w / 2, c + ax * w / 2, r, 30)
    rim = cyl(c - ax * (w / 2 + 0.25), c + ax * (w / 2 + 0.25), r * hub, 16)
    return tyre, rim


def track_loop(x, y0, y1, z0, z1, w, sections=24):
    """Track run along y (front -y) at lateral x: rounded loop between two wheel radii (z0..z1 tall)."""
    r = (z1 - z0) / 2
    zc = (z0 + z1) / 2
    return hull(np.vstack([cyl((x - w / 2, y, zc), (x + w / 2, y, zc), r, sections).vertices
                           for y in (y0 + r, y1 - r)]))


# ------------------------------------------------------------------------------------------------ the scale figure
def vigil_figure(origin=(0, 0, 0), yaw=0.0, with_base=True):
    """Stand-in Vigil rifleman, ~32.5 mm soles to crown, on a 32 mm base: keel-crested egg helm with a split chevron
    visor, broad cuirass with sternum keel, spine power pack, bullpup rifle at port arms. Returns [(mesh, colour)]."""
    R = rot((0, 0, 1), yaw)
    o = v3(origin)
    parts = []
    b = 3.0 if with_base else 0.0

    def P(mesh, col):
        mesh.apply_transform(np.vstack([np.hstack([R, o[:, None]]), [0, 0, 0, 1]]))
        parts.append((mesh, col))

    if with_base:
        P(cone((0, 0, 0), (0, 0, b), 16.0, 15.0, 40), BASE)
    z = b
    for s in (-1, 1):
        P(cbox((3.4, 5.6, 2.2), (s * 2.6, -0.6, z + 1.1), 0.5), VIGIL2)                 # boots
        P(capsule((s * 2.6, 0, z + 2.6), (s * 2.7, -0.4, z + 9.0), 1.55), VIGIL)          # greaves
        P(capsule((s * 2.7, -0.4, z + 9.2), (s * 2.5, 0.2, z + 15.8), 1.9), VIGIL)        # thighs
    P(cbox((6.6, 4.2, 3.0), (0, 0.1, z + 16.0), 0.8), VIGIL2)                              # pelvis
    P(hull(np.vstack([cbox((9.4, 5.6, 6.0), (0, 0.2, z + 20.4), 1.2).vertices,
                      [[0, -3.6, z + 21.8], [0, -3.2, z + 18.0]]])), VIGIL)                # cuirass + keel
    for s in (-1, 1):
        P(ellipsoid((s * 5.3, 0.5, z + 23.0), (2.6, 2.9, 1.9), rot((0, 1, 0), s * -14)), VIGIL2)  # shoulder caps
        P(capsule((s * 5.6, 0.3, z + 21.8), (s * 4.6, -2.6, z + 17.6), 1.35), VIGIL)       # upper arms
        P(capsule((s * 4.6, -2.6, z + 17.6), (s * 1.6, -5.2, z + 19.8), 1.25), VIGIL)      # forearms
    P(cbox((5.2, 3.0, 7.0), (0, 3.6, z + 20.8), 0.8), VIGIL2)                             # spine power pack
    P(cbox((2.0, 1.6, 7.6), (0, 3.9, z + 21.2), 0.4), DARK)
    P(cbox((1.6, 13.0, 2.4), (0.6, -5.4, z + 20.5), 0.4, rot((1, 0, 0), -38)), DARK)       # bullpup rifle, port arms
    hz = z + 27.6
    P(ellipsoid((0, 0.1, hz), (2.5, 2.85, 2.9)), VIGIL)                                   # egg helm
    P(capsule((0, -2.0, hz + 1.6), (0, 2.6, hz + 1.9), 0.55), VIGIL2)                    # keel crest
    for s in (-1, 1):
        P(cbox((1.5, 0.7, 0.7), (s * 0.95, -2.55, hz + 0.25), 0.15, rot((0, 1, 0), s * 24)), AMBER)  # split chevron
    return parts


def base_disc(center, d=32.0, h=3.0, oval=None):
    c = v3(center)
    if oval:
        b = cone((0, 0, 0), (0, 0, h), 1.0, 0.95, 56)
        b.apply_scale((oval[0] / 2, oval[1] / 2, 1.0))
        b.apply_translation(c)
        return b
    return cone(c, c + (0, 0, h), d / 2, d / 2 - 1.0, 48)


# ------------------------------------------------------------------------------------------------ the kit
class Kit:
    def __init__(self, cid, name, designation, role):
        self.cid, self.name, self.designation, self.role = cid, name, designation, role
        self.parts = []      # (mesh, colour, is_vehicle)

    def add(self, mesh, col=HULL, vehicle=True):
        if isinstance(mesh, (list, tuple)):
            for x in mesh:
                self.add(x, col, vehicle)
            return
        self.parts.append((mesh, col, vehicle))

    def mirror_add(self, fn, col=HULL):
        """fn(s) builds a part for side s in (-1, 1)."""
        for s in (-1, 1):
            self.add(fn(s), col)

    def figure(self, origin, yaw=0.0, with_base=True):
        for mh, col in vigil_figure(origin, yaw, with_base):
            self.parts.append((mh, col, False))

    def vehicle_bounds(self):
        V = np.vstack([mh.vertices for mh, _, veh in self.parts if veh])
        return V.min(axis=0), V.max(axis=0)

    # -------------------------------------------------------------------------------------------- export
    def export_stl(self, path):
        meshes = [mh for mh, _, veh in self.parts if veh and mh.is_volume]
        try:
            u = trimesh.boolean.union(meshes, engine="manifold")
        except Exception as e:  # noqa: BLE001 - blockout only: fall back to a plain concatenation
            print("union failed, concatenating:", e)
            u = trimesh.util.concatenate(meshes)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        u.export(path)
        return u

    # -------------------------------------------------------------------------------------------- rendering
    def _project(self, az, el):
        a, e = math.radians(az), math.radians(el)
        Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        Rx = np.array([[1, 0, 0], [0, math.cos(e), -math.sin(e)], [0, math.sin(e), math.cos(e)]])
        return Rx @ Rz

    def _panel(self, az, el, W, H, k, cx, cy, ox, oy, bg, ss=2, shadow=True):
        R = self._project(az, el)
        key = np.array([-0.55, -0.65, 0.55]); key /= np.linalg.norm(key)
        fill = np.array([0.8, -0.35, 0.1]); fill /= np.linalg.norm(fill)
        rim = np.array([0.1, 0.9, 0.5]); rim /= np.linalg.norm(rim)
        hv = key + np.array([0, -1, 0]); hv /= np.linalg.norm(hv)
        tris, cols, dep = [], [], []
        for mh, col in self._render_parts():
            V = mh.vertices @ R.T
            T = V[mh.faces]
            n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            vis = n[:, 1] < 0
            T, n = T[vis], n[vis]
            # camera-space lights, as tools/render.py: every view is lit the same way
            lk = np.clip(n @ key, 0, 1)
            lf = np.clip(n @ fill, 0, 1)
            lr = np.clip(n @ rim, 0, 1)
            sp = np.clip(n @ hv, 0, 1) ** 24
            base = np.array([int(col[i:i + 2], 16) for i in (1, 3, 5)]) / 255
            sh = (base[None] * (0.24 + 0.74 * lk[:, None] * np.array([1.0, 0.96, 0.9])
                                + 0.30 * lf[:, None] * np.array([0.8, 0.9, 1.05])) + 0.22 * lr[:, None] + 0.16 * sp[:, None])
            tris.append(T); cols.append(np.clip(sh, 0, 1)); dep.append(T[:, :, 1].mean(axis=1))
        T, C, D = np.vstack(tris), np.vstack(cols), np.concatenate(dep)
        S = ss
        img = Image.new("RGB", (W * S, H * S), bg)
        mask = Image.new("L", (W * S, H * S), 0)
        dr, dm = ImageDraw.Draw(img), ImageDraw.Draw(mask)
        X = (T[:, :, 0] - cx) * k * S + ox * S
        Y = -(T[:, :, 2] - cy) * k * S + oy * S
        if shadow and el < 80:
            allv = np.vstack([mh.vertices for mh, _, _ in self.parts])
            g = allv.copy(); g[:, 2] = 0.0
            g[:, 0] += 2.0; g[:, 1] += 3.0
            G = g @ R.T
            pts2 = np.stack([(G[:, 0] - cx) * k * S + ox * S, -(G[:, 2] - cy) * k * S + oy * S], axis=1)
            try:
                from scipy.spatial import ConvexHull
                hv2 = ConvexHull(pts2).vertices
                sc = tuple(int(c * 0.86) for c in bg)
                dr.polygon([tuple(p) for p in pts2[hv2]], fill=sc)
            except Exception:  # noqa: BLE001
                pass
        Ci = (C * 255).astype(np.uint8)
        for i in np.argsort(-D):
            poly = [(X[i, 0], Y[i, 0]), (X[i, 1], Y[i, 1]), (X[i, 2], Y[i, 2])]
            dr.polygon(poly, fill=tuple(Ci[i]), outline=tuple(Ci[i]))
            dm.polygon(poly, fill=255)
        edge = ImageChops_sub(mask.filter(ImageFilter.MaxFilter(5)), mask)
        dark = Image.new("RGB", img.size, (38, 40, 46))
        img.paste(dark, (0, 0), edge)
        return img.resize((W, H), Image.LANCZOS)

    def _render_parts(self, max_edge=2.5):
        """Painter's algorithm needs small triangles: split long faces once and cache."""
        if getattr(self, "_rp", None) is None:
            self._rp = []
            for mh, col, _ in self.parts:
                v, f = trimesh.remesh.subdivide_to_size(mh.vertices, mh.faces, max_edge, max_iter=12)
                self._rp.append((trimesh.Trimesh(v, f, process=False), col))
        return self._rp

    def _fit(self, views, W, H, margin=0.86):
        """Shared scale k (px per mm) fitting every view; returns k and per-view projected bboxes."""
        boxes = []
        allv = np.vstack([mh.vertices for mh, _, _ in self.parts])
        for az, el, _ in views:
            V = allv @ self._project(az, el).T
            boxes.append((V[:, 0].min(), V[:, 0].max(), V[:, 2].min(), V[:, 2].max()))
        k = min(min(W * margin / (b[1] - b[0]), H * margin / (b[3] - b[2])) for b in boxes)
        return k, boxes

    def _header(self, sheet, W, sub):
        d = ImageDraw.Draw(sheet)
        d.rectangle([0, 0, W, 86], fill=(36, 40, 48))
        d.rectangle([0, 86, W, 90], fill=(240, 168, 58))
        d.text((24, 12), f"{self.name}  ({self.designation})", font=ImageFont.truetype(FONT_B, 34), fill=(240, 240, 236))
        d.text((24, 54), sub, font=ImageFont.truetype(FONT, 19), fill=(200, 205, 212))

    def _footer(self, sheet, W, Hs, k, note):
        d = ImageDraw.Draw(sheet)
        y = Hs - 50
        d.rectangle([0, y - 6, W, Hs], fill=(222, 223, 226))
        lo, hi = self.vehicle_bounds()
        dims = hi - lo
        txt = (f"Blockout {dims[0]:.0f} W x {dims[1]:.0f} L x {dims[2]:.0f} H mm at 1:56  "
               f"(~{dims[0] / MM_PER_M:.1f} x {dims[1] / MM_PER_M:.1f} x {dims[2] / MM_PER_M:.1f} m)   |   {note}")
        if getattr(self, "dims_text", None):
            txt = f"{self.dims_text}   |   {note}"
        L = 20 * k
        x1 = W - 40
        x0 = x1 - L
        fs = 17
        while fs > 11 and ImageFont.truetype(FONT, fs).getlength(txt) > x0 - 190:
            fs -= 1
        d.text((24, y + 10), txt, font=ImageFont.truetype(FONT, fs), fill=(40, 42, 50))
        # scale bar: 20 mm
        yb = y + 22
        d.rectangle([x0, yb - 4, x1, yb + 4], outline=(30, 30, 30), fill=(30, 30, 30))
        d.rectangle([x0 + L / 2, yb - 3, x1 - 1, yb + 3], fill=(240, 240, 240))
        d.text((x0 - 150, y + 10), "20 mm = 1.12 m", font=ImageFont.truetype(FONT, 17), fill=(40, 42, 50))

    def render_hero(self, path, az=-38, el=22, W=1500, H=1000, note="CONCEPT - not a print file"):
        bg = (233, 234, 237)
        top, bot = 90, 56
        ph = H - top - bot
        views = [(az, el, "")]
        k, boxes = self._fit(views, W, ph, 0.84)
        b = boxes[0]
        img = self._panel(az, el, W, ph, k, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, W / 2, ph / 2, bg)
        # cx/cy given in projected coords: _panel subtracts them after projection
        sheet = Image.new("RGB", (W, H), bg)
        sheet.paste(img, (0, top))
        self._header(sheet, W, f"{self.role}   |   Aster Compact - Vigil support   |   hero 3/4 view, Vigil rifleman (32 mm) for scale")
        self._footer(sheet, W, H, k, note)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sheet.save(path)
        return path

    def render_sheet(self, path, wide=900, narrow=560, ph=470, note="orthographic 3-view + back, all views same scale",
                     views=None):
        """2 x 2 sheet: SIDE | FRONT over TOP | BACK. Side and top share the wide column (front of the vehicle to the
        right), front and back the narrow one; one scale for every panel. views: [(az, el, label, col, row)]."""
        bg = (233, 234, 237)
        top, bot = 90, 56
        views = views or [(90, 0, "SIDE (right)", 0, 0), (0, 0, "FRONT", 1, 0), (90, 90, "TOP (front to the right)", 0, 1),
                          (180, 0, "BACK", 1, 1)]
        allv = np.vstack([mh.vertices for mh, _, _ in self.parts])
        boxes, k = [], 1e9
        for az, el, _, col, _ in views:
            V = allv @ self._project(az, el).T
            b = (V[:, 0].min(), V[:, 0].max(), V[:, 2].min(), V[:, 2].max())
            boxes.append(b)
            pw = wide if col == 0 else narrow
            k = min(k, pw * 0.88 / (b[1] - b[0]), ph * 0.84 / (b[3] - b[2]))
        zmin = min(b[2] for b, v in zip(boxes, views) if v[1] < 80)
        zmax = max(b[3] for b, v in zip(boxes, views) if v[1] < 80)
        W = wide + narrow
        Hs = 2 * ph + top + bot
        sheet = Image.new("RGB", (W, Hs), bg)
        for (az, el, label, col, row), b in zip(views, boxes):
            pw = wide if col == 0 else narrow
            if el < 80:   # elevations share one ground line
                img = self._panel(az, el, pw, ph, k, (b[0] + b[1]) / 2, (zmin + zmax) / 2, pw / 2, ph / 2, bg)
            else:
                img = self._panel(az, el, pw, ph, k, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, pw / 2, ph / 2, bg, shadow=False)
            d = ImageDraw.Draw(img)
            d.text((14, 10), label, font=ImageFont.truetype(FONT_B, 18), fill=(50, 52, 60))
            d.rectangle([0, 0, pw - 1, ph - 1], outline=(205, 206, 210), width=2)
            sheet.paste(img, (0 if col == 0 else wide, top + row * ph))
        self._header(sheet, W, f"{self.role}   |   orthographic views at 1:56, Vigil rifleman (32 mm) for scale")
        self._footer(sheet, W, Hs, k, note)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sheet.save(path)
        return path

    def finish(self, root, stl=True, hero=None, sheet=None):
        """Write images (and the blockout STL); returns measured vehicle dims in mm."""
        self.render_hero(os.path.join(root, "images", f"{self.cid}-hero.png"), **(hero or {}))
        self.render_sheet(os.path.join(root, "images", f"{self.cid}-turnaround.png"), **(sheet or {}))
        if stl:
            u = self.export_stl(os.path.join(root, "blockout", f"{self.cid}-blockout.stl"))
            print("stl", u.is_watertight, len(u.faces))
        lo, hi = self.vehicle_bounds()
        dims = {"width_x": round(float(hi[0] - lo[0]), 1), "length_y": round(float(hi[1] - lo[1]), 1),
                "height_z": round(float(hi[2] - lo[2]), 1)}
        print(json.dumps({"id": self.cid, "dims_scale_mm": dims,
                          "dims_world_m": {k2: round(v / MM_PER_M, 2) for k2, v in dims.items()}}))
        return dims


def ImageChops_sub(a, b):
    from PIL import ImageChops
    return ImageChops.subtract(a, b)
