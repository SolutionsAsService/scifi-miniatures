"""Transport-lane concept kit: fast trimesh blockouts and labelled concept sheets for Vigil support vehicles.

Concept pass only (not print-ready sculpts). Frame: mm at 1:56 print scale, x = vehicle front, y = vehicle left,
z up, ground at z = 0. Every concepts/<id>/source/concept.py builds a list of (mesh, colour-key) parts and calls
publish().

Renderer: numpy z-buffer rasteriser (flat shading, key/fill/rim lights fixed in the world), image-space ink lines
where the face normal or depth jumps, and a soft ground shadow. Good enough to judge silhouette and mass.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import Polygon

MM_PER_M = 1000.0 / 56.0        # 1:56
SCALE = "1:56 (30 mm heroic)"

PALETTE = {
    "hull": "#7d8c96",      # Vigil slate (same family as the Kestrel exosuit renders)
    "hull2": "#66747e",     # recessed / secondary plates
    "panel": "#93a1aa",     # raised applique plates
    "dark": "#3d4247",      # tracks, tyres, vents
    "metal": "#5a5f66",     # weapons, running gear
    "accent": "#c9a246",    # Aster Compact amber (keel crest, markings)
    "lens": "#59cfe0",      # chevron vision blocks, grav glow
    "glass": "#3f6f86",     # canopy glazing
    "white": "#e6e4dc",     # medevac markings
    "figure": "#b9b2a4",    # scale trooper (bone)
    "base": "#4b5057",
    "stand": "#a9c4cf",
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(size, bold=False):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)
    except OSError:
        return ImageFont.load_default(size=size)


# ------------------------------------------------------------------------------------------------ primitives
def m2mm(x):
    return x * MM_PER_M


def _place(m, c=(0, 0, 0), R=None):
    T = np.eye(4)
    if R is not None:
        T[:3, :3] = R
    T[:3, 3] = c
    m.apply_transform(T)
    return m


def rotz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def roty(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def rotx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def box(c, s, R=None):
    return _place(trimesh.creation.box(extents=s), c, R)


def hull(pts):
    m = trimesh.convex.convex_hull(np.asarray(pts, dtype=float))
    m.fix_normals()
    if m.volume < 0:
        m.invert()
    return m


def chbox(c, s, ch=0.6, R=None):
    """Chamfered box: hull of three boxes, each shrunk by the chamfer on two axes."""
    s = np.asarray(s, float)
    ch = min(ch, s.min() / 2 - 1e-3)
    pts = []
    for ax in range(3):
        e = s.copy()
        for o in range(3):
            if o != ax:
                e[o] -= 2 * ch
        pts.append(trimesh.creation.box(extents=e).vertices)
    m = hull(np.vstack(pts))
    return _place(m, c, R)


def cyl(a, b, r, sections=32):
    return trimesh.creation.cylinder(radius=r, segment=[a, b], sections=sections)


def chcyl(a, b, r, ch=0.5, sections=32):
    """Cylinder with chamfered rims (tyres, hubs)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    ch = min(ch, np.linalg.norm(b - a) / 2 - 1e-3, r / 2)
    m1 = cyl(a + d * ch, b - d * ch, r, sections)
    m2 = cyl(a, b, r - ch, sections)
    return hull(np.vstack([m1.vertices, m2.vertices]))


def sph(c, r, sub=2):
    return _place(trimesh.creation.icosphere(subdivisions=sub, radius=r), c)


def ell(c, radii, R=None, sub=2):
    m = trimesh.creation.icosphere(subdivisions=sub, radius=1.0)
    m.vertices = m.vertices * np.asarray(radii, float)
    return _place(m, c, R)


def caps(a, b, r, sub=1):
    return hull(np.vstack([sph(a, r, sub).vertices, sph(b, r, sub).vertices]))


def annulus(c, axis, r_in, r_out, h, sections=40):
    m = trimesh.creation.annulus(r_min=r_in, r_max=r_out, height=h, sections=sections)
    ax = np.asarray(axis, float) / np.linalg.norm(axis)
    m.apply_transform(trimesh.geometry.align_vectors(np.array([0, 0, 1.0]), ax))
    m.apply_translation(c)
    return m


def prism_y(profile_xz, y0, y1):
    """Extrude any simple side-view polygon (x, z) between y0 and y1 (non-convex allowed)."""
    m = trimesh.creation.extrude_polygon(Polygon(profile_xz), y1 - y0)
    M = np.eye(4)
    M[:3, :3] = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float)   # (u, v, w) -> (x, z, y)
    M[1, 3] = y0
    m.apply_transform(M)
    if m.volume < 0:
        m.invert()
    return m


def prism_x(profile_yz, x0, x1):
    """Extrude a front-view polygon (y, z) between x0 and x1."""
    m = trimesh.creation.extrude_polygon(Polygon(profile_yz), x1 - x0)
    M = np.eye(4)
    M[:3, :3] = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)   # (u, v, w) -> (y, z, x)
    M[0, 3] = x0
    m.apply_transform(M)
    if m.volume < 0:
        m.invert()
    return m


def bev_prism_y(profile_xz, width, bevel=1.0, yc=0.0):
    """Convex side profile extruded to 'width' with bevelled long edges (hull of full and shrunk profiles)."""
    P = Polygon(profile_xz)
    inner = np.array(P.buffer(-bevel, join_style=2).exterior.coords)
    outer = np.array(P.exterior.coords)
    pts = []
    for y in (yc - width / 2 + bevel, yc + width / 2 - bevel):
        pts += [(x, y, z) for x, z in outer]
    for y in (yc - width / 2, yc + width / 2):
        pts += [(x, y, z) for x, z in inner]
    return hull(pts)


def bev_prism_x(profile_yz, x0, x1, bevel=1.0):
    P = Polygon(profile_yz)
    inner = np.array(P.buffer(-bevel, join_style=2).exterior.coords)
    outer = np.array(P.exterior.coords)
    pts = []
    for x in (x0 + bevel, x1 - bevel):
        pts += [(x, y, z) for y, z in outer]
    for x in (x0, x1):
        pts += [(x, y, z) for y, z in inner]
    return hull(pts)


# ------------------------------------------------------------------------------------------------ assemblies
def wheel(c, r, w, side=1, tread=True, sections=36):
    """Tyre + hub + tread blocks. c = wheel centre, axis along y; side = +1 left, -1 right (hub faces outward)."""
    c = np.asarray(c, float)
    parts = []
    a, b = c + (0, -w / 2, 0), c + (0, w / 2, 0)
    parts.append((chcyl(a, b, r, ch=min(0.9, r * 0.12), sections=sections), "dark"))
    hub_out = c + (0, side * (w / 2 + 0.25), 0)
    parts.append((chcyl(c, hub_out, r * 0.55, ch=0.35, sections=24), "metal"))
    parts.append((cyl(c, hub_out + (0, side * 0.6, 0), r * 0.2, 12), "metal"))
    if tread:
        n = max(12, int(2 * math.pi * r / 2.2))
        for i in range(n):
            t = 2 * math.pi * i / n
            p = c + np.array([math.cos(t) * (r - 0.1), 0, math.sin(t) * (r - 0.1)])
            parts.append((box(p, (1.0, w * 0.82, 0.9), roty(-math.degrees(t))), "dark"))
    return parts


def track_unit(x_rear, x_front, y, width, r_drive=6.0, r_road=4.2, n_road=5, side=1, lift_front=3.0,
               lift_rear=2.0, cleat=2.6):
    """Track loop (dark belt = convex hull of idler, sprocket and road wheels) with road-wheel discs proud of the
    outer face and grousers on the ground run. Returns (parts, belt_top_z)."""
    parts = []
    hw = width / 2
    wheels = []
    zf = r_drive + lift_front
    zr = r_drive + lift_rear
    wheels.append((x_front - r_drive, zf, r_drive * 0.9))      # idler
    wheels.append((x_rear + r_drive, zr, r_drive))             # sprocket
    for x in np.linspace(x_rear + r_drive * 1.9, x_front - r_drive * 1.9, n_road):
        wheels.append((x, r_road, r_road))
    pts = [cyl((x, y - hw, z), (x, y + hw, z), r + 0.8, 28).vertices for x, z, r in wheels]
    belt = hull(np.vstack(pts))
    parts.append((belt, "dark"))
    out = y + side * (hw + 0.05)
    for x, z, r in wheels:
        parts.append((chcyl((x, out - side * 0.6, z), (x, out + side * 0.6, z), r * 0.92, ch=0.4, sections=28), "metal"))
        parts.append((cyl((x, out, z), (x, out + side * 1.0, z), r * 0.35, 14), "metal"))
    x = x_rear + r_drive * 1.4
    while x < x_front - r_drive * 1.2:
        parts.append((box((x, y, 0.35), (0.9, width + 0.3, 0.7)), "dark"))
        x += cleat
    return parts, belt.bounds[1][2]


def figure_parts(pos=(0, 0, 0), yaw=0.0, base=True):
    """Stylised 32 mm Vigilant for scale: chunky armour, keel-crested egg helm with split chevron visor, spine pack,
    bullpup rifle at the ready, on a 32 mm base (3.8 mm). Local frame faces -y, then turned by yaw (deg)."""
    zb = 3.8 if base else 0.0
    P = []

    def add(m, col):
        P.append((m, col))

    if base:
        add(chcyl((0, 0, 0), (0, 0, zb), 16.0, ch=0.8, sections=48), "base")
    for s in (-1, 1):
        add(chbox((s * 2.1, -0.9, zb + 1.3), (2.7, 4.8, 2.6), 0.6), "figure")                     # boots
        add(caps((s * 2.1, 0, zb + 2.6), (s * 2.2, 0, zb + 8.6), 1.55), "figure")                    # greaves
        add(caps((s * 2.2, 0, zb + 9.0), (s * 2.5, 0.2, zb + 14.6), 1.85), "figure")                 # thighs
        add(sph((s * 2.15, -1.2, zb + 8.8), 1.25), "figure")                                          # knee guards
        add(ell((s * 5.3, 0.1, zb + 23.6), (2.5, 2.7, 2.0)), "figure")                               # shoulder caps
        add(caps((s * 5.5, 0.1, zb + 22.5), (s * 5.2, -1.3, zb + 18.6), 1.45), "figure")             # upper arms
    add(chbox((0, 0, zb + 15.6), (6.2, 4.0, 3.0), 0.9), "figure")                                     # pelvis
    add(hull(np.vstack([chbox((0, 0, zb + 19.0), (6.4, 4.6, 2.0), 0.6).vertices,
                        chbox((0, 0.1, zb + 23.2), (9.4, 5.8, 2.8), 1.0).vertices])), "figure")      # cuirass
    add(hull([(0, -3.25, zb + 18.2), (0, -3.25, zb + 24.2), (0, -2.6, zb + 24.6), (0, -2.6, zb + 17.8),
              (0.45, -2.6, zb + 21), (-0.45, -2.6, zb + 21)]), "accent")                              # sternum keel
    add(caps((-5.2, -1.3, zb + 18.6), (-1.0, -5.0, zb + 19.6), 1.3), "figure")                       # forearms
    add(caps((5.2, -1.3, zb + 18.6), (1.4, -8.0, zb + 19.2), 1.3), "figure")
    add(chbox((0.4, -6.0, zb + 20.4), (1.8, 11.0, 2.6), 0.4), "metal")                               # bullpup rifle
    add(cyl((0.4, -11.0, zb + 20.9), (0.4, -14.5, zb + 20.9), 0.65, 10), "metal")
    add(chbox((0.4, -4.0, zb + 18.6), (1.4, 1.8, 2.4), 0.3), "metal")                                # magazine
    add(chbox((0, 3.7, zb + 21.4), (6.0, 3.0, 7.2), 1.0), "figure")                                  # spine pack
    add(cyl((0, 3.7, zb + 25.0), (0, 3.7, zb + 26.2), 1.0, 12), "figure")
    hz = zb + 28.3
    add(ell((0, -0.1, hz), (2.75, 3.05, 3.1)), "figure")                                              # helm egg
    add(ell((0, -1.6, hz - 1.6), (1.7, 1.5, 1.2)), "figure")                                          # muzzle
    add(hull([(0, -2.8, hz + 1.4), (0, -1.0, hz + 3.3), (0, 1.8, hz + 3.2), (0, 3.3, hz + 1.2),
              (0.4, 0, hz + 2.6), (-0.4, 0, hz + 2.6)]), "figure")                                    # keel crest
    for s in (-1, 1):                                                                                 # split chevron visor
        add(box((s * 1.05, -2.75, hz + 0.25), (1.6, 0.9, 0.6), rotz(s * 18) @ roty(s * 26)), "lens")
    M = np.eye(4)
    M[:3, :3] = rotz(yaw)
    M[:3, 3] = pos
    for m, _ in P:
        m.apply_transform(M)
    return P


def merged(parts):
    return trimesh.util.concatenate([m for m, _ in parts])


# ------------------------------------------------------------------------------------------------ renderer
def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


KEY = _unit((0.45, 0.75, 1.0))
FILL = _unit((0.9, -0.35, 0.25))
RIM = _unit((-0.8, -0.3, 0.5))


def camera(az, el):
    """Camera direction (scene -> camera) from azimuth about z (0 = in front, on +x; 90 = on the vehicle's left)
    and elevation (deg). Returns right, up, d. el = 90 is a plan view with the front to the left."""
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)])
    if abs(el - 90) < 1e-6:
        d = np.array([0, 0, 1.0])
        right = np.array([-1.0, 0, 0])
    else:
        right = _unit(np.cross([0, 0, 1], d))
    up = np.cross(d, right)
    return right, up, d


class Scene:
    def __init__(self, parts):
        V, F, C = [], [], []
        off = 0
        for m, col in parts:
            V.append(np.asarray(m.vertices))
            F.append(np.asarray(m.faces) + off)
            C.append(np.repeat(_hex(PALETTE.get(col, col))[None], len(m.faces), axis=0))
            off += len(m.vertices)
        self.V = np.vstack(V)
        F = np.vstack(F)
        C = np.vstack(C)
        T = self.V[F]
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        keep = ln[:, 0] > 1e-12
        self.F, self.C = F[keep], C[keep]
        self.N = n[keep] / ln[keep]
        lk = np.clip(self.N @ KEY, 0, 1)[:, None]
        lf = np.clip(self.N @ FILL, 0, 1)[:, None]
        lr = np.clip(self.N @ RIM, 0, 1)[:, None]
        up = np.clip(self.N[:, 2], 0, 1)[:, None]
        self.shade = np.clip(self.C * (0.40 + 0.55 * lk * np.array([1.0, 0.97, 0.92]) + 0.24 * lf * np.array([0.85, 0.92, 1.05])
                                       + 0.10 * up) + 0.10 * lr, 0, 1)
        glow = np.all(np.isclose(self.C, _hex(PALETTE["lens"])), axis=1)
        self.shade[glow] = np.clip(_hex(PALETTE["lens"]) * 1.05, 0, 1)
        self.lo, self.hi = self.V.min(axis=0), self.V.max(axis=0)

    def project(self, az, el):
        r, u, d = camera(az, el)
        c = (self.lo + self.hi) / 2
        P = self.V - c
        return np.stack([P @ r, P @ u, -(P @ d)], axis=1), d

    def extent(self, az, el):
        S, _ = self.project(az, el)
        return S[:, 0].min(), S[:, 0].max(), S[:, 1].min(), S[:, 1].max()


def raster(scene, az, el, k, W, H, shadow=True, ink=(38, 42, 48)):
    """Rasterise at k px/mm into a W x H RGBA image (transparent background), centred on the projected bbox."""
    S, d = scene.project(az, el)
    cx = (S[:, 0].min() + S[:, 0].max()) / 2
    cy = (S[:, 1].min() + S[:, 1].max()) / 2
    X = (S[:, 0] - cx) * k + W / 2
    Y = -(S[:, 1] - cy) * k + H / 2
    Z = S[:, 2]
    F = scene.F
    vis = scene.N @ d > 1e-6
    zbuf = np.full((H, W), np.inf)
    fid = np.full((H, W), -1, dtype=np.int64)
    idx = np.nonzero(vis)[0]
    TX, TY, TZ = X[F[idx]], Y[F[idx]], Z[F[idx]]
    for j, f in enumerate(idx):
        xs, ys, zs = TX[j], TY[j], TZ[j]
        bx0, bx1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), W - 1)
        by0, by1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), H - 1)
        if bx1 < bx0 or by1 < by0:
            continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-9:
            continue
        px, py = np.meshgrid(np.arange(bx0, bx1 + 1) + 0.5, np.arange(by0, by1 + 1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        sub = zbuf[by0:by1 + 1, bx0:bx1 + 1]
        upd = inside & (z < sub)
        sub[upd] = z[upd]
        fid[by0:by1 + 1, bx0:bx1 + 1][upd] = f
    hit = fid >= 0
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (scene.shade[np.maximum(fid, 0)] * 255).astype(np.uint8)
    img[..., 3] = np.where(hit, 255, 0)
    # ink lines: face-normal crease or depth step between neighbouring pixels, plus the silhouette
    Nn = scene.N[np.maximum(fid, 0)]
    edge = np.zeros((H, W), bool)
    zf = np.where(hit, zbuf, 1e9)
    tol = max(0.5, 1.5 / k)
    for dy, dx in ((0, 1), (1, 0)):
        a_h, b_h = hit[:H - dy, :W - dx], hit[dy:, dx:]
        a_f, b_f = fid[:H - dy, :W - dx], fid[dy:, dx:]
        dot = np.sum(Nn[:H - dy, :W - dx] * Nn[dy:, dx:], axis=2)
        dz = np.abs(zf[:H - dy, :W - dx] - zf[dy:, dx:])
        e = (a_h != b_h) | ((a_f != b_f) & a_h & b_h & ((dot < 0.93) | (dz > tol)))
        edge[:H - dy, :W - dx] |= e & a_h
        edge[dy:, dx:] |= e & b_h
    img[edge, :3] = ink
    img[edge, 3] = 255
    out = Image.fromarray(img, "RGBA")
    if shadow:
        r_, u_, _ = camera(az, el)
        c = (scene.lo + scene.hi) / 2
        L = np.array([-0.25, -0.35, 1.0])
        G = scene.V - np.outer(scene.V[:, 2], L)
        G[:, 2] = 0.0
        P = G - c
        GX = (P @ r_ - cx) * k + W / 2
        GY = -(P @ u_ - cy) * k + H / 2
        sm = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(sm)
        for f in np.nonzero(scene.N[:, 2] > 0.05)[0]:
            t = F[f]
            dr.polygon([(GX[t[0]], GY[t[0]]), (GX[t[1]], GY[t[1]]), (GX[t[2]], GY[t[2]])], fill=95)
        sm = sm.filter(ImageFilter.GaussianBlur(radius=float(max(2.0, k * 1.0))))
        sh = Image.new("RGBA", (W, H), (40, 44, 52, 0))
        sh.putalpha(sm)
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        base.alpha_composite(sh)
        base.alpha_composite(out)
        out = base
    return out


BG = (236, 237, 239)


def _title(dr, x, y, name, sub):
    dr.text((x, y), name, font=font(40, True), fill=(28, 32, 40))
    dr.text((x, y + 52), sub, font=font(22), fill=(70, 76, 86))


def _scalebar(dr, x, y, k, mm=50):
    L = mm * k
    dr.rectangle([x, y, x + L, y + 8], outline=(40, 44, 52), width=2)
    for i in range(0, 5, 2):
        dr.rectangle([x + i * L / 5, y, x + (i + 1) * L / 5, y + 8], fill=(40, 44, 52))
    dr.text((x, y + 14), f"{mm} mm at 1:56  =  {mm * 56 / 1000:.1f} m", font=font(18), fill=(50, 54, 62))


def hero(scene, path, name, sub, az=38, el=24, W=1800, H=1150, ss=2, notes=()):
    x0, x1, y0, y1 = scene.extent(az, el)
    ih = H - 230
    k = min((W - 160) / (x1 - x0), (ih - 60) / (y1 - y0))
    im = raster(scene, az, el, k * ss, W * ss, ih * ss, shadow=True).resize((W, ih), Image.LANCZOS)
    sheet = Image.new("RGB", (W, H), BG)
    sheet.paste(im, (0, 120), im)
    dr = ImageDraw.Draw(sheet)
    _title(dr, 40, 26, name, sub)
    _scalebar(dr, 40, H - 70, k, 50)
    y = H - 64
    for line in notes:
        dr.text((W - 40, y), line, font=font(18), fill=(70, 76, 86), anchor="ra")
        y += 24
    dr.text((W - 40, 34), "CONCEPT BLOCKOUT · not print-ready", font=font(18, True), fill=(160, 120, 40), anchor="ra")
    dr.text((W - 40, 60), "Aster Compact · Vigil support vehicles", font=font(18), fill=(90, 96, 106), anchor="ra")
    sheet.save(path)
    return path


def three_view(scene, path, name, sub, dims_mm, extra=None, W=2000, H=1400, ss=2):
    """Side (vehicle's left), top (aligned under the side view), front (right of the side view) and a 4th panel
    (rear 3/4 by default, or extra = (scene, az, el, label))."""
    exs = scene.extent(90, 0)
    ext = scene.extent(0, 90)
    exf = scene.extent(0, 0)
    Lx, Hz = exs[1] - exs[0], exs[3] - exs[2]
    Wy = exf[1] - exf[0]
    top_h = ext[3] - ext[2]
    m = 60
    colA = int(W * 0.64)
    k = min((colA - 2 * m) / Lx, (H - 250 - 4 * m) / (Hz + top_h), (W - colA - 2 * m) / max(Wy, 1))
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    _title(dr, 40, 26, name, sub)
    dr.text((W - 40, 34), "CONCEPT BLOCKOUT · orthographic, common scale", font=font(18, True), fill=(160, 120, 40), anchor="ra")
    y_top = 140
    side_h = int(Hz * k + 2 * m)
    plan_h = int(top_h * k + 2 * m)
    panels = [((90, 0), (0, y_top, colA, side_h), "SIDE (left)"),
              ((0, 90), (0, y_top + side_h, colA, plan_h), "TOP"),
              ((0, 0), (colA, y_top, W - colA, side_h), "FRONT")]
    for (az, el), (px, py, pw, ph), label in panels:
        im = raster(scene, az, el, k * ss, pw * ss, ph * ss, shadow=False).resize((pw, ph), Image.LANCZOS)
        sheet.paste(im, (px, py), im)
        dr.text((px + 20, py + 4), label, font=font(20, True), fill=(80, 86, 96))
    L, Wd, Hh = dims_mm
    sx0 = colA / 2 - Lx * k / 2
    yb = y_top + side_h - m / 2 + 6
    dr.line([sx0, yb, sx0 + Lx * k, yb], fill=(60, 64, 72), width=2)
    for xx in (sx0, sx0 + Lx * k):
        dr.line([xx, yb - 8, xx, yb + 8], fill=(60, 64, 72), width=2)
    dr.text((colA / 2, yb + 4), f"L {L:.0f} mm  ({L * 56 / 1000:.1f} m)", font=font(18), fill=(40, 44, 52), anchor="ma")
    fx = colA + (W - colA) / 2
    dr.text((fx, yb + 4), f"W {Wd:.0f} mm ({Wd * 56 / 1000:.1f} m)  ·  H {Hh:.0f} mm ({Hh * 56 / 1000:.1f} m)",
            font=font(18), fill=(40, 44, 52), anchor="ma")
    px, py = colA, y_top + side_h + 30
    pw, ph = W - colA, H - py - 100
    sc, az, el, label = extra if extra else (scene, 215, 22, "REAR 3/4")
    x0, x1, y0, y1 = sc.extent(az, el)
    k4 = min((pw - 60) / (x1 - x0), (ph - 50) / (y1 - y0))
    im = raster(sc, az, el, k4 * ss, pw * ss, ph * ss, shadow=True).resize((pw, ph), Image.LANCZOS)
    sheet.paste(im, (px, py), im)
    dr.text((px + 20, py + 4), label + " (not to common scale)", font=font(20, True), fill=(80, 86, 96))
    _scalebar(dr, 40, H - 70, k, 50)
    sheet.save(path)
    return path


# ------------------------------------------------------------------------------------------------ publish
def publish(here, meta, vehicle, figure, hero_kw=None, sheet_extra=None, stl=True):
    """here: concept folder. vehicle / figure: part lists. Writes images/, blockout/ and concept.json; the scale
    dimensions are measured from the vehicle blockout and converted to world metres (x 56)."""
    os.makedirs(os.path.join(here, "images"), exist_ok=True)
    vm = merged(vehicle)
    lo, hi = vm.bounds
    dims_mm = [round(float(v), 1) for v in (hi - lo)]
    meta = dict(meta)
    role_short = meta.pop("role_short")
    meta["dims_scale_mm"] = {"length": dims_mm[0], "width": dims_mm[1], "height": dims_mm[2]}
    meta["dims_world_m"] = {k: round(v * 56 / 1000, 2) for k, v in meta["dims_scale_mm"].items()}
    meta["scale"] = SCALE
    meta["status"] = "concept"
    vid = meta["id"]
    title = f"{meta['name']} ({meta['designation']})"
    sub = f"{role_short}  ·  {meta['drive']}  ·  Vigilant on 32 mm base for scale"
    w = meta["dims_world_m"]
    notes = [f"{dims_mm[0]:.0f} × {dims_mm[1]:.0f} × {dims_mm[2]:.0f} mm at 1:56  ({w['length']} × {w['width']} × {w['height']} m)"]
    imgs = [f"images/{vid}-hero.png", f"images/{vid}-3view.png"]
    hero(Scene(vehicle + figure), os.path.join(here, imgs[0]), title, sub, notes=notes, **(hero_kw or {}))
    three_view(Scene(vehicle), os.path.join(here, imgs[1]), title, "Orthographic 3-view  ·  " + role_short, dims_mm,
               extra=sheet_extra)
    meta["images"] = imgs
    if stl:
        os.makedirs(os.path.join(here, "blockout"), exist_ok=True)
        vm.export(os.path.join(here, "blockout", f"{vid}-blockout.stl"))
        meta["blockout_stl"] = f"blockout/{vid}-blockout.stl"
        meta["blockout_note"] = "Overlapping primitive shells at 1:56 mm (visual blockout, not a unioned print mesh)."
    with open(os.path.join(here, "concept.json"), "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    print(json.dumps({"id": vid, "dims_mm": dims_mm, "world_m": w, "faces": int(len(vm.faces)), "images": imgs}))
    return meta
