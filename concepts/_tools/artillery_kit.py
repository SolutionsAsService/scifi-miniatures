"""Artillery & fire-support lane: shared blockout + render helpers for Vigil support-vehicle CONCEPTS.

Concept pass only: convex hulls, cylinders and capsules in mm at 1:56, unioned per colour with manifold3d, rendered
with a small painter's-algorithm rasteriser (same lighting as tools/render.py) plus a silhouette outline so the
shapes read at thumbnail size. Not print geometry.

Frame (same as the infantry): mm, z up, the vehicle faces -y, its left side on +x.

Vigil vehicle language helpers (mirroring the Kestrel exosuit):
- keel():          the helm's keel crest as a rounded centreline ridge along hull / turret roofs;
- chevron_visor(): the split chevron visor as two lens slots in a V, split by the keel;
- prow():          a V glacis (the split chevron seen from above): the hull nose is a prow, not a flat plate;
- skirts():        armour plates in overlapping threes, like the layered shoulder caps;
- spine_pack():    the infantry spine power pack, scaled up: cell block, keel spine, three vent slots.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCALE = 56.0
HERE = os.path.dirname(os.path.abspath(__file__))
REF_STL = os.path.join(HERE, "artillery_vigil_scale_ref.stl")   # Vigilant Rifleman Mk II, decimated (32.4 mm tall)

PAL = {
    "hull": "#7f8c97",    # Aster Compact slate (same family as the rifleman's #7d8c96)
    "hull2": "#66727d",
    "dark": "#3a4047",    # tracks, barrels, wheels
    "metal": "#a3abb3",
    "accent": "#c98d2c",  # ochre chevron markings
    "lens": "#3fc2da",    # visor / sensor glass
    "crew": "#aeb7bf",
    "ref": "#c3c9cf",
    "base": "#8d9188",
}


def mm(metres):
    return metres * 1000.0 / SCALE


def world(mm_):
    return mm_ * SCALE / 1000.0


# ------------------------------------------------------------------------------------------------ transforms
def Rx(d):
    a = math.radians(d)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def Ry(d):
    a = math.radians(d)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def Rz(d):
    a = math.radians(d)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def M(pos=(0, 0, 0), rz=0.0, ry=0.0, rx=0.0):
    T = np.eye(4)
    T[:3, :3] = Rz(rz) @ Ry(ry) @ Rx(rx)
    T[:3, 3] = pos
    return T


def xf(mesh, T):
    m = mesh.copy()
    m.apply_transform(T)
    return m


def tp(T, p):
    return (T @ np.append(np.asarray(p, float), 1.0))[:3]


# ------------------------------------------------------------------------------------------------ primitives
def hull(points):
    return trimesh.convex.convex_hull(np.asarray(points, dtype=float))


def box(c, size, rz=0.0, ry=0.0, rx=0.0, bevel=0.0):
    hx, hy, hz = (s / 2 for s in size)
    b = min(bevel, hx * 0.9, hy * 0.9, hz * 0.9)
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                if b > 0:
                    pts += [(sx * hx, sy * (hy - b), sz * (hz - b)), (sx * (hx - b), sy * hy, sz * (hz - b)),
                            (sx * (hx - b), sy * (hy - b), sz * hz)]
                else:
                    pts.append((sx * hx, sy * hy, sz * hz))
    return xf(hull(pts), M(c, rz, ry, rx))


def cyl(a, b, r, sections=28):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return trimesh.creation.cylinder(radius=r, segment=np.stack([a, b]), sections=sections)


def cone(a, b, ra, rb, sections=28):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    u = np.cross(d, [0, 0, 1] if abs(d[2]) < 0.9 else [1, 0, 0])
    u /= np.linalg.norm(u)
    w = np.cross(d, u)
    t = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    ring = np.cos(t)[:, None] * u + np.sin(t)[:, None] * w
    return hull(np.vstack([a + ra * ring, b + rb * ring]))


def ellipsoid(c, radii, T=None, subdiv=2):
    s = trimesh.creation.icosphere(subdivisions=subdiv)
    s.vertices *= np.asarray(radii, float)
    if T is not None:
        s.apply_transform(T)
    s.apply_translation(c)
    return s


def sphere(c, r, subdiv=2):
    return ellipsoid(c, (r, r, r), subdiv=subdiv)


def capsule(a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    s = trimesh.creation.icosphere(subdivisions=1).vertices * r
    return hull(np.vstack([a + s, b + s]))


def tube(points, r):
    return [capsule(points[i], points[i + 1], r) for i in range(len(points) - 1)]


# ------------------------------------------------------------------------------------------------ Vigil language
def keel(model, points, r, key="hull", T=None):
    """Keel crest: rounded ridge through the given points (hull / turret centreline)."""
    for c in tube(points, r):
        model.add(key, c, T)


def chevron_visor(model, c, width, height, depth=0.8, angle=22.0, rx=0.0, rz=0.0, keel_r=None, T=None):
    """Two lens slots in a V split at the centre (the helm's split chevron), set on a face whose normal is -y
    (tilted back by rx, turned by rz)."""
    Tl = M(c, rz=rz, rx=rx)
    if T is not None:
        Tl = T @ Tl
    for s in (-1, 1):
        model.add("lens", xf(box((s * width * 0.27, 0, 0), (width * 0.46, depth, height), ry=s * angle), Tl))
    if keel_r:
        model.add("hull", xf(box((0, -depth * 0.1, -height * 0.25), (keel_r * 2, depth * 1.5, height * 2.6), bevel=keel_r * 0.6), Tl))


def prow(y_nose, y_back, half_w, z_lo, z_hi, nose_w=0.0, nose_top=0.55, nose_lo=0.0):
    """V glacis: hull of a rear block and a pointed / narrow nose. Seen from above it is the chevron."""
    pts = []
    for sx in (-1, 1):
        pts += [(sx * half_w, y_back, z_lo), (sx * half_w, y_back, z_hi),
                (sx * nose_w, y_nose, z_lo + (z_hi - z_lo) * nose_lo), (sx * nose_w, y_nose, z_lo + (z_hi - z_lo) * nose_top)]
    return hull(pts)


def skirts(model, x, y0, y1, z_top, h, n=3, t=1.0, key="hull", lap=1.5, step=0.4):
    """Overlapping armour plates along a side (x = inner face), stepped outboard like the layered shoulder caps."""
    L = (y1 - y0 + lap * (n - 1)) / n
    sgn = 1 if x > 0 else -1
    for i in range(n):
        yc = y0 + L / 2 + i * (L - lap)
        model.add(key, box((x + sgn * (t / 2 + i * step), yc, z_top - h / 2), (t, L, h), bevel=0.35))


def spine_pack(model, c, w, d, h, rz=0.0, T=None):
    """The infantry spine power pack scaled to a vehicle: core block, raised cell, keel spine, three vent slots.
    Faces -y (front against the hull); the vents face +y."""
    Tl = M(c, rz=rz)
    if T is not None:
        Tl = T @ Tl
    s = min(w, d, h)
    model.add("hull2", xf(box((0, 0, 0), (w, d, h), bevel=s * 0.12), Tl))
    model.add("hull2", xf(box((0, d * 0.2, h * 0.06), (w * 0.72, d * 0.75, h * 0.94), bevel=s * 0.1), Tl))
    model.add("hull", xf(capsule((0, d * 0.58, h * 0.5), (0, d * 0.58, -h * 0.32), s * 0.09), Tl))
    for j in range(3):
        model.add("dark", xf(box((0, d * 0.58, -h * 0.26 + j * h * 0.2), (w * 0.6, max(0.7, d * 0.08), h * 0.085)), Tl))


def chevron_mark(model, c, size, rz=0.0, rx=0.0, T=None, t=0.35, point_up=False):
    """Painted ochre chevron (raised 0.35 mm in the blockout so it shows in the renders); face normal -y."""
    Tl = M(c, rz=rz, rx=rx)
    if T is not None:
        Tl = T @ Tl
    sg = -1 if point_up else 1
    for s in (-1, 1):
        model.add("accent", xf(box((s * size * 0.25, 0, 0), (size * 0.6, t, size * 0.16), ry=sg * s * 32), Tl))


def track_unit(model, x, y_front, y_rear, r_drive, r_idle, z_ground, width, wheels=6, r_wheel=None):
    """Track loop (convex hull of sprocket, idler and road wheels; axes along x) + visible road-wheel hubs."""
    r_wheel = r_wheel or r_idle * 0.85
    pts = []

    def ring(yc, zc, r):
        return [(x + sx * width / 2, yc + r * math.cos(t), zc + r * math.sin(t))
                for t in np.linspace(0, 2 * math.pi, 24, endpoint=False) for sx in (-1, 1)]
    pts += ring(y_front, z_ground + r_wheel * 1.25 + r_drive * 0.6, r_drive)
    pts += ring(y_rear, z_ground + r_wheel * 1.1 + r_idle * 0.4, r_idle)
    ys = np.linspace(y_front + r_drive * 1.2, y_rear - r_idle * 1.2, wheels)
    for yc in ys:
        pts += ring(yc, z_ground + r_wheel, r_wheel)
    model.add("dark", hull(pts))
    sgn = 1 if x > 0 else -1
    for yc in ys:
        model.add("metal", cyl((x + sgn * width * 0.45, yc, z_ground + r_wheel), (x + sgn * (width * 0.5 + 0.5), yc, z_ground + r_wheel), r_wheel * 0.62, 18))
    return ys


def wheel(model, c, r, w, side):
    model.add("dark", cyl((c[0] - w / 2, c[1], c[2]), (c[0] + w / 2, c[1], c[2]), r, 30))
    model.add("metal", cyl((c[0] + side * w * 0.4, c[1], c[2]), (c[0] + side * (w / 2 + 0.5), c[1], c[2]), r * 0.52, 18))


# ------------------------------------------------------------------------------------------------ crew mannequin
def _ik(a, t, l1, l2, pole):
    a, t, pole = (np.asarray(v, float) for v in (a, t, pole))
    d = t - a
    L = min(float(np.linalg.norm(d)), l1 + l2 - 0.05)
    n = d / np.linalg.norm(d)
    c = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L)
    p = pole - n * (pole @ n)
    p /= np.linalg.norm(p)
    return a + n * l1 * c + p * l1 * math.sqrt(max(0.0, 1 - c * c))


def crew(model, pos, yaw=0.0, pelvis_z=15.8, lean=8.0, feet=((-3.0, 0.5), (3.0, -0.5)), knees=(None, None),
         hands=((-5.5, -4.0, 15.0), (5.5, -4.0, 15.0)), head_pitch=0.0, helm="vigil", pack=True, key="crew"):
    """Block-out Vigilant (about 32.5 mm to the crown when standing) in the exosuit proportions; local frame faces -y,
    its left on +x. feet: (x, y[, z]) per foot; knees: explicit local points for kneeling; hands: local fist targets.
    Returns a function mapping local points to world (to hang held props on the hands)."""
    T = M(pos, rz=yaw)
    R = Rx(-lean)                          # positive lean tips the torso forward (toward -y)
    pel = np.array([0, 0, pelvis_z])
    chest = pel + R @ np.array([0, 0.2, 5.8])
    neck = chest + R @ np.array([0, 0.3, 3.3])
    head = neck + Rx(-head_pitch) @ np.array([0, -0.2, 3.0])
    sh = [chest + R @ np.array([s * 5.2, 0.35, 2.0]) for s in (-1, 1)]
    hip = [pel + np.array([s * 2.6, 0.1, -0.6]) for s in (-1, 1)]
    parts = [ellipsoid(pel, (3.0, 2.2, 2.2))]
    Tt = np.eye(4); Tt[:3, :3] = R; Tt[:3, 3] = chest + R @ np.array([0, 0, 0.4])
    parts.append(xf(box((0, 0, 0), (9.6, 5.8, 6.8), bevel=1.6), Tt))                           # cuirass
    parts.append(xf(capsule((0, -2.9, 2.6), (0, -3.2, -2.2), 0.55), Tt))                       # sternum keel
    parts.append(capsule(pel + np.array([0, 0, 1.6]), chest, 2.6))                             # abdomen
    for i, s in enumerate((-1, 1)):
        f = np.asarray(feet[i], float)
        ankle = np.array([f[0], f[1], (f[2] if len(f) > 2 else 0.0) + 1.9])
        knee = np.asarray(knees[i], float) if knees[i] is not None else _ik(hip[i], ankle, 7.6, 7.3, (s * 0.3, -1, 0))
        parts += [capsule(hip[i], knee, 1.9), capsule(knee, ankle, 1.6), sphere(knee + np.array([0, -0.9, 0.2]), 1.4, 1)]
        parts.append(box((ankle[0], ankle[1] - 0.9, ankle[2] - 0.95), (2.8, 4.6, 1.9), bevel=0.6))   # boot
        hand = np.asarray(hands[i], float)
        elbow = _ik(sh[i], hand, 5.4, 5.6, (s * 1.0, 1.2, -0.6))
        parts += [sphere(sh[i] + np.array([s * 0.4, 0, 0.4]), 2.5, 1), capsule(sh[i], elbow, 1.35), capsule(elbow, hand, 1.45),
                  sphere(hand, 1.35, 1)]
    for p in parts:
        model.add(key, xf(p, T))
    Th = np.eye(4); Th[:3, :3] = Rx(-head_pitch); Th[:3, 3] = head
    TH = T @ Th
    model.add(key, xf(ellipsoid((0, 0.2, 0.2), (2.5, 2.85, 2.85)), TH))                       # helm egg
    model.add(key, xf(ellipsoid((0, -1.5, -1.2), (1.7, 1.4, 1.3)), TH))                       # respirator muzzle
    keel(model, [(0, -2.4, 1.5), (0, -1.0, 2.9), (0, 0.8, 3.1), (0, 2.4, 2.2)], 0.42,
         key="hull" if helm == "vigil" else "accent", T=TH)                                    # keel crest
    if helm == "warden":
        model.add("accent", xf(capsule((-2.4, 0.5, 0.5), (-2.8, 1.8, 6.5), 0.45), TH))         # whip antenna
    for s in (-1, 1):
        model.add("lens", xf(box((s * 1.05, -2.5, 0.25), (1.6, 0.9, 0.7), ry=s * 24), TH))    # split chevron visor
        model.add(key, xf(cyl((s * 2.2, 0.1, 0), (s * 2.8, 0.1, 0), 0.8, 12), TH))             # ear pods
    if pack:
        Tp = np.eye(4); Tp[:3, :3] = R; Tp[:3, 3] = chest + R @ np.array([0, 4.4, 0.2])
        model.add("hull2", xf(box((0, 0, 0), (5.2, 2.8, 6.4), bevel=0.8), T @ Tp))
        model.add("hull", xf(capsule((0, 1.5, 2.6), (0, 1.5, -2.2), 0.45), T @ Tp))
    return lambda p: tp(T, p)


# ------------------------------------------------------------------------------------------------ model
class Model:
    def __init__(self, name):
        self.name = name
        self.groups = {}
        self.refs = []      # scale references (rendered, not exported, not measured)

    def add(self, key, mesh, T=None):
        if T is not None:
            mesh = xf(mesh, T)
        self.groups.setdefault(key, []).append(mesh)
        return mesh

    def add_ref(self, pos, yaw=0.0):
        m = trimesh.load(REF_STL)
        m.apply_transform(M(pos, rz=yaw))
        self.refs.append(m)

    def merged(self):
        out = []
        for key, ms in self.groups.items():
            try:
                u = trimesh.boolean.union(ms, engine="manifold") if len(ms) > 1 else ms[0]
            except Exception:
                u = trimesh.util.concatenate(ms)
            out.append((u, PAL[key]))
        return out

    def export_stl(self, path, merged=None):
        merged = merged or self.merged()
        ms = [m for m, _ in merged]
        try:
            u = trimesh.boolean.union(ms, engine="manifold")
        except Exception:
            u = trimesh.util.concatenate(ms)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        u.export(path)
        return u


def bounds(merged):
    v = np.vstack([m.vertices for m, _ in merged])
    return v.min(axis=0), v.max(axis=0)


# ------------------------------------------------------------------------------------------------ render
KEY = np.array([-0.55, -0.65, 0.55]); KEY = KEY / np.linalg.norm(KEY)
FILL = np.array([0.8, -0.35, 0.1]); FILL = FILL / np.linalg.norm(FILL)
RIM = np.array([0.1, 0.9, 0.5]); RIM = RIM / np.linalg.norm(RIM)
BG = (236, 237, 240)
INK = (34, 38, 46)


def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def view(az, el):
    """az: degrees the model turns about z (0 = its front toward the camera); el: camera elevation."""
    return Rx(el) @ Rz(az)


def font(size, bold=False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    try:
        return ImageFont.truetype(p, size)
    except OSError:
        return ImageFont.load_default()


_FINE = {}


def _fine(m, max_edge=3.0):
    """Split long triangles so the painter's sort by centroid depth stays honest on big flat panels."""
    key = id(m)
    if key not in _FINE:
        v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=max_edge, max_iter=8)
        _FINE[key] = (m, trimesh.Trimesh(v, f, process=False))
    return _FINE[key][1]


def _project(meshes, R, center):
    tris, cols, depth = [], [], []
    meshes = [(_fine(m), c) for m, c in meshes]
    h = KEY + np.array([0, -1, 0]); h /= np.linalg.norm(h)
    for m, col in meshes:
        V = (m.vertices - center) @ R.T
        T = V[m.faces]
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        vis = n[:, 1] < 0
        T, n = T[vis], n[vis]
        lk = np.clip(n @ KEY, 0, 1)
        lf = np.clip(n @ FILL, 0, 1)
        lr = np.clip(n @ RIM, 0, 1)
        spec = np.clip(n @ h, 0, 1) ** 24
        base = _hex(col)
        shade = (base[None] * (0.26 + 0.72 * lk[:, None] * np.array([1.0, 0.96, 0.9]) + 0.28 * lf[:, None] * np.array([0.8, 0.9, 1.05]))
                 + 0.28 * lr[:, None] + 0.16 * spec[:, None])
        tris.append(T); cols.append(np.clip(shade, 0, 1)); depth.append(T[:, :, 1].mean(axis=1))
    return np.vstack(tris), np.vstack(cols), np.concatenate(depth)


def panel(meshes, R, center, k, W, H, ss=2, shadow_z=None, offset=(0.0, 0.0)):
    """Render one view. k: px per mm (final resolution). offset: view-space (x, z) placed at the panel centre."""
    S = ss
    img = Image.new("RGB", (W * S, H * S), BG)
    mask = Image.new("L", (W * S, H * S), 0)
    kk = k * S
    sx = lambda X: (X[..., 0] - offset[0]) * kk + W * S / 2
    sy = lambda X: -(X[..., 2] - offset[1]) * kk + H * S / 2
    if shadow_z is not None:   # soft contact shadow: the model squashed onto the ground, pushed away from the key light
        sh = Image.new("L", (W * S, H * S), 0)
        ds = ImageDraw.Draw(sh)
        for m, _ in meshes:
            V = m.vertices.copy()
            hgt = V[:, 2] - shadow_z
            V[:, 0] += hgt * 0.45; V[:, 1] += hgt * 0.35; V[:, 2] = shadow_z
            P = (V - center) @ R.T
            X, Y = sx(P), sy(P)
            for f in m.faces:
                ds.polygon([(X[f[0]], Y[f[0]]), (X[f[1]], Y[f[1]]), (X[f[2]], Y[f[2]])], fill=255)
        sh = sh.filter(ImageFilter.GaussianBlur(5 * S))
        img = Image.composite(Image.new("RGB", img.size, (190, 193, 200)), img, sh.point(lambda v: int(v * 0.75)))
    dr, dm = ImageDraw.Draw(img), ImageDraw.Draw(mask)
    T, C, Dp = _project(meshes, R, center)
    order = np.argsort(-Dp)
    X, Y = sx(T), sy(T)
    Ci = (C * 255).astype(np.uint8)
    for i in order:
        poly = [(X[i, 0], Y[i, 0]), (X[i, 1], Y[i, 1]), (X[i, 2], Y[i, 2])]
        dr.polygon(poly, fill=(int(Ci[i, 0]), int(Ci[i, 1]), int(Ci[i, 2])))
        dm.polygon(poly, fill=255)
    grown = mask.filter(ImageFilter.MaxFilter(3 + 2 * S))
    ring = Image.fromarray(np.clip(np.asarray(grown, np.int16) - np.asarray(mask, np.int16), 0, 255).astype(np.uint8))
    img = Image.composite(Image.new("RGB", img.size, (52, 56, 64)), img, ring)
    return img.resize((W, H), Image.LANCZOS)


def _extent(meshes, R, center):
    P = (np.vstack([m.vertices for m, _ in meshes]) - center) @ R.T
    return P[:, 0].min(), P[:, 0].max(), P[:, 2].min(), P[:, 2].max()


def _scalebar(d, x, y, k, length_mm=20):
    L = length_mm * k
    d.rectangle([x, y, x + L, y + 8], fill=INK)
    d.rectangle([x + L / 2, y + 2, x + L - 2, y + 6], fill=BG)
    d.text((x + L + 14, y - 6), f"{length_mm:g} mm at 1:56 = {world(length_mm):.2f} m", fill=INK, font=font(18))


def hero(model, path, title, subtitle, az=-38, el=20, W=1600, H=1000, merged=None):
    merged = merged or model.merged()
    meshes = merged + [(r, PAL["ref"]) for r in model.refs]
    allv = np.vstack([m.vertices for m, _ in meshes])
    center = (allv.min(0) + allv.max(0)) / 2
    R = view(az, el)
    x0, x1, z0, z1 = _extent(meshes, R, center)
    top, bot = 130, 80
    k = min((W - 140) / (x1 - x0), (H - top - bot) / (z1 - z0))
    off = ((x0 + x1) / 2, (z0 + z1) / 2 + (top - bot) / 2 / k)
    img = panel(meshes, R, center, k, W, H, shadow_z=allv[:, 2].min(), offset=off)
    d = ImageDraw.Draw(img)
    d.text((40, 26), title, fill=INK, font=font(46, True))
    d.text((42, 84), subtitle, fill=(80, 86, 96), font=font(22))
    d.text((W - 30, H - 24), "concept blockout · Aster Compact fire support · 1:56 (30 mm heroic) · light grey figure: Vigilant Rifleman Mk II for scale",
           fill=(90, 96, 106), font=font(16), anchor="rs")
    img.save(path)
    return path


def sheet(model, path, title, subtitle, W=1800, H=1250, merged=None, dims_text=""):
    """Orthographic 4-up (front, right side, top, rear) at ONE shared scale, with a scale bar."""
    merged = merged or model.merged()
    meshes = merged + [(r, PAL["ref"]) for r in model.refs]
    allv = np.vstack([m.vertices for m, _ in meshes])
    center = (allv.min(0) + allv.max(0)) / 2
    views = [("FRONT", view(0, 0)), ("RIGHT SIDE", view(90, 0)), ("TOP  (front to the right)", view(90, 90)), ("REAR", view(180, 0))]
    top_band, bot_band = 112, 64
    pw, ph = W // 2, (H - top_band - bot_band) // 2
    ext = [_extent(meshes, R, center) for _, R in views]
    k = min(min((pw - 70) / (e[1] - e[0]), (ph - 70) / (e[3] - e[2])) for e in ext)
    out = Image.new("RGB", (W, H), BG)
    for i, ((label, R), e) in enumerate(zip(views, ext)):
        off = ((e[0] + e[1]) / 2, (e[2] + e[3]) / 2 + 12 / k)
        p = panel(meshes, R, center, k, pw, ph, offset=off)
        dp = ImageDraw.Draw(p)
        dp.text((16, 12), label, fill=INK, font=font(22, True))
        dp.rectangle([0, 0, pw - 1, ph - 1], outline=(200, 203, 209))
        out.paste(p, ((i % 2) * pw, top_band + (i // 2) * ph))
    d = ImageDraw.Draw(out)
    d.text((40, 20), title, fill=INK, font=font(42, True))
    d.text((42, 74), subtitle + "  ·  orthographic, one scale", fill=(80, 86, 96), font=font(20))
    _scalebar(d, 40, H - bot_band + 26, k, 20)
    d.text((W - 40, H - 22), dims_text, fill=INK, font=font(19), anchor="rs")
    out.save(path)
    return path


def finish(model, root, cid, title, subtitle, info, hero_az=-38, hero_el=20):
    """Render hero + sheet, export blockout STL, write concept.json with measured dims (scale figure excluded)."""
    os.makedirs(os.path.join(root, "images"), exist_ok=True)
    merged = model.merged()
    lo, hi = bounds(merged)
    ext = hi - lo
    dims_mm = {"length": round(float(ext[1]), 1), "width": round(float(ext[0]), 1), "height": round(float(ext[2]), 1)}
    dims_m = {k: round(world(v), 2) for k, v in dims_mm.items()}
    dims_text = (f"overall L x W x H  {dims_mm['length']:.0f} x {dims_mm['width']:.0f} x {dims_mm['height']:.0f} mm"
                 f"  =  {dims_m['length']:.1f} x {dims_m['width']:.1f} x {dims_m['height']:.1f} m in-world")
    hero(model, os.path.join(root, "images", f"{cid}-hero.png"), title, subtitle, az=hero_az, el=hero_el, merged=merged)
    sheet(model, os.path.join(root, "images", f"{cid}-3view.png"), title, subtitle, merged=merged, dims_text=dims_text)
    stl = os.path.join(root, "blockout", f"{cid}-blockout.stl")
    u = model.export_stl(stl, merged)
    data = {"id": cid, **info, "dims_world_m": dims_m, "dims_scale_mm": dims_mm, "scale": "1:56 (30 mm heroic)",
            "images": [f"images/{cid}-hero.png", f"images/{cid}-3view.png"], "blockout": f"blockout/{cid}-blockout.stl",
            "status": "concept"}
    with open(os.path.join(root, "concept.json"), "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(cid, "dims mm", dims_mm, "world m", dims_m, "stl faces", len(u.faces), "bytes", os.path.getsize(stl))
    return data
