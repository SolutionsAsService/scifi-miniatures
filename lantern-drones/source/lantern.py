"""Lantern-pattern squad drone kit: SDF sculpts for every print part (SD-1 Wisp, SD-2 Tick, SD-C cradle, stem, bases).

Frame (as tools/sdfkit.py): millimetres at 1:56 print scale, z up, every part faces -y (its left side on +x).
Every key dimension comes from spec/lantern-drones.spec.json; offsets of small details (panel lines, lens bars,
rotor blades) are written here next to the feature they shape, with the process limit they respect.

Detail rules (MSLA resin, msla_resin preset of unified-CAD-MCP): walls >= 0.6 mm (Wisp ducts 0.85 mm, brief 0.8),
Tick parts >= 0.9 mm (brief), engraved lines and lens bars 0.4-0.45 mm wide x 0.3-0.35 mm deep, raised detail
>= 0.15 mm, air gaps between surfaces that face each other >= 0.5 mm, no knife edges, no sealed cavities.
"""
from __future__ import annotations

import math

import numpy as np

from sdfkit import Sculpt, Shape, capsule, cyl, d_peg, ellipsoid, half, rbox, rot, round_cone, sphere, unit, v3

I3 = np.eye(3)
Z = v3(0, 0, 1)
RX, RY = (1, 0, 0), (0, 1, 0)


# ------------------------------------------------------------------------------------------------ op lists
class Ops:
    """Ordered add / cut operations; each Shape may be moved by a 4x4 matrix when appended (parts reuse sub-assemblies)."""

    def __init__(self):
        self.ops = []

    def add(self, s, k=0.0):
        self.ops.append(("add", s, k))
        return s

    def cut(self, s, k=0.0):
        self.ops.append(("cut", s, k))
        return s

    def bounds(self):
        adds = [s for o, s, _ in self.ops if o == "add"]
        return np.min([s.lo for s in adds], axis=0), np.max([s.hi for s in adds], axis=0)

    def sculpt(self, h, pad=0.4):
        lo, hi = self.bounds()
        g = Sculpt(lo - pad, hi + pad, h)
        for o, s, k in self.ops:
            (g.add if o == "add" else g.cut)(s, k)
        return g


def mat(R=I3, t=(0, 0, 0)):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    return M


def along(a, b, hw, hh, r=0.2, ext=0.0, up=(0, 0, 1)):
    """Rounded bar from a to b: hw half width (sideways), hh half height (toward 'up')."""
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d))
    n = d / L
    upv = v3(up) - n * float(np.dot(up, n))
    upv = unit(upv)
    u = np.cross(n, upv)
    return rbox((a + b) / 2, (hw, L / 2 + ext, hh), np.stack([u, n, upv], axis=1), r)


def mesh_in_budget(ops, name, h0, budget=250_000, limit=290_000):
    """Mesh at pitch h0; if the marched mesh is over the checker budget, re-mesh the field coarser (triangles scale
    with 1 / pitch^2, the miniature_mesh_budget rule). Never decimates the print mesh."""
    h = h0
    for _ in range(3):
        m = ops.sculpt(h).mesh(name)
        if len(m.faces) <= limit:
            m.metadata["pitch_mm"] = h
            return m
        h = round(h * math.sqrt(len(m.faces) / budget) * 1.01, 4)
        print(f"{name}: {len(m.faces)} triangles over budget, re-meshing at {h} mm", flush=True)
    raise SystemExit(f"{name}: could not reach the triangle budget")


# ------------------------------------------------------------------------------------------------ SD-1 Wisp
def duct(o, M, spin=0.0, top=True, bottom=True, cover=False):
    """One ducted fan, local axis z, centre at the local origin (h 1.8: z -0.9..0.9). Wall 3.0 - 2.15 = 0.85 mm.
    Top well floor at z 0.15, rotor blades up to z 0.5 = 0.4 mm below the rim; bottom well up to z -0.45, so the
    rotor floor is 0.6 mm thick."""
    T = lambda s: s.moved(M)  # noqa: E731
    o.add(T(cyl(v3(0, 0, -0.9), v3(0, 0, 0.9), 3.0, 0.3)), 0.15)
    if top:
        o.cut(T(cyl(v3(0, 0, 0.15), v3(0, 0, 1.6), 2.15)))
        o.add(T(cyl(v3(0, 0, 0.0), v3(0, 0, 0.62), 0.55, 0.12)))                     # hub, 0.28 below the rim
        for k in range(3):
            a = math.radians(spin + 120 * k)
            d = v3(math.cos(a), math.sin(a), 0)
            o.add(T(along(d * 0.35, d * 1.55, 0.3, 0.2, 0.08, up=(0, 0, 1)).moved(mat(t=(0, 0, 0.3)))))  # blade 0.6 wide, top z 0.5
    elif cover:
        o.cut(T(cyl(v3(0, 0, 0.5), v3(0, 0, 1.6), 2.15)))                              # stowed cover, 0.4 recess
        o.add(T(cyl(v3(0, 0, 0.3), v3(0, 0, 0.75), 0.7, 0.15)))
    if bottom:
        o.cut(T(cyl(v3(0, 0, -1.6), v3(0, 0, -0.45), 2.15)))
        o.add(T(round_cone(v3(0, 0, -0.5), v3(0, 0, -0.75), 0.6, 0.3)))               # stator hub


def wisp_core(o, S, M=np.eye(4)):
    """Chevron-plan body (two swept wing bars meeting at the nose, a notch at the tail), dorsal hump, keel spine,
    chin sensor ball with split-chevron lenses."""
    W = S["wisp"]
    T = lambda s: s.moved(M)  # noqa: E731
    nose = v3(0, W["nose_y"], 0.1)
    o.add(T(ellipsoid(v3(0, -1.4, 0.15), (1.8, 2.9, 1.1))))                          # core
    for s in (-1, 1):
        tail = v3(s * W["tail"][0], W["tail"][1], 0.0)
        o.add(T(along(nose, tail, 1.15, 0.75, 0.5)), 0.4)                             # wing bar 2.3 x 1.5
    o.add(T(ellipsoid(v3(0, -1.0, 0.6), (1.25, 2.5, 0.8))), 0.3)                       # dorsal hump
    o.add(T(capsule(v3(0, -4.2, 0.85), v3(0, 1.4, 1.15), 0.45)), 0.2)                  # keel spine 0.9 mm
    for s in (-1, 1):                                                                 # panel line across each bar
        tail = v3(s * W["tail"][0], W["tail"][1], 0.0)
        n = unit(tail - nose)
        c = tail - n * 1.7 + v3(0, 0, 0.75)
        o.cut(T(rbox(c, (0.22, 1.5, 0.3), np.stack([n, np.cross(Z, n), Z], axis=1), 0.05)))
    cb = W["chin_ball"]
    o.add(T(sphere(v3(cb["c"]), cb["r"])), 0.25)
    for s in (-1, 1):                                                                 # split-chevron lenses
        o.cut(T(rbox(v3(cb["c"]) + v3(s * 0.47, -1.05, 0.12), (0.5, 0.45, 0.22), rot(RY, s * 28), 0.06)))


def wisp_arms_ducts(o, S, M=np.eye(4), bottom=True):
    W = S["wisp"]
    dx, dy, dz = W["duct_centre"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = v3(sx * dx, sy * dy, dz)
            root = v3(sx * 1.2, -2.6, 0.1) if sy < 0 else v3(sx * 1.9, 1.6, 0.1)
            end = c - unit(c - root) * 2.55                                           # ends inside the duct wall
            o.add(along(root, end, 0.6, 0.45, 0.2).moved(M), 0.25)                    # arm 1.2 x 0.9
            spin = 15 * sx + 40 * (sy > 0)
            duct(o, M @ mat(t=c), spin, top=True, bottom=bottom)


def wisp(S, variant="A"):
    """variant A recon, B designator + munition, L landed (legs and skids, no stem socket)."""
    W = S["wisp"]
    o = Ops()
    wisp_core(o, S)
    wisp_arms_ducts(o, S, bottom=(variant != "L"))
    st = W["stem_socket"]
    sx, sy = st["xy"]
    if variant in ("A", "B"):
        o.add(cyl(v3(sx, sy, -0.4), v3(sx, sy, st["boss_bottom_z"]), st["boss_r"], 0.3), 0.3)   # stem boss
        o.cut(cyl(v3(sx, sy, st["boss_bottom_z"] - 0.5), v3(sx, sy, st["boss_bottom_z"] + st["depth"]), st["d"] / 2))
    if variant == "B":
        # laser designator pod (right, -x) and shaped-charge munition (left, +x), each on a pylon under the body
        o.add(along(v3(-1.6, -2.4, -0.6), v3(-1.95, -3.6, -1.6), 0.45, 0.45, 0.2), 0.15)
        o.add(cyl(v3(-1.95, -2.7, -1.95), v3(-1.95, -5.6, -1.95), 0.6, 0.2), 0.15)
        o.cut(cyl(v3(-1.95, -5.9, -1.95), v3(-1.95, -5.3, -1.95), 0.3))                  # lens 0.6 dia, 0.3 deep
        o.add(along(v3(1.6, -2.4, -0.6), v3(1.95, -3.6, -1.6), 0.45, 0.45, 0.2), 0.15)
        o.add(round_cone(v3(1.95, -2.7, -1.95), v3(1.95, -5.3, -1.95), 0.72, 0.45), 0.15)
        o.add(cyl(v3(1.95, -3.9, -1.95), v3(1.95, -3.6, -1.95), 0.82, 0.1), 0.05)        # band, 0.15 proud
    if variant == "L":
        zs = W["landed_skid_z"]
        for sx in (-1, 1):
            for sy in (-1, 1):
                o.add(capsule(v3(sx * 2.6, sy * 3.4, -0.5), v3(sx * 3.3, sy * 3.9, zs + 0.5), 0.5), 0.2)   # leg 1.0
            o.add(capsule(v3(sx * 3.3, -5.0, zs + 0.5), v3(sx * 3.3, 5.0, zs + 0.5), 0.5), 0.2)          # skid 1.0
        o.cut(Shape(lambda P: P[:, 2] - zs, (-9, -9, zs - 2), (9, 9, zs)))            # flat feet at z = zs
    return o


def wisp_folded(o, S, M):
    """Stowed Wisp for the cradle: body nose-up, keel facing out (+y); the four ducts swung behind it into a 2 x 2
    stack with covers on (lower pair flat against the cradle plate, upper pair stepped 0.5 mm out)."""
    Rd = rot(RX, -90)                         # local z (duct axis) -> +y ; body nose (-y) -> +z
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        upper = sz > 0
        yc = 1.9 + (0.5 if upper else 0.0)
        duct(o, M @ mat(Rd, (sx * 1.7, yc, sz * 1.7)), top=False, bottom=False, cover=upper)
    wisp_core(o, S, M @ mat(Rd, (0, 4.25, 0.3)))
    for sx in (-1, 1):                                                               # folded arm stubs
        o.add(along(v3(sx * 1.1, 4.0, -1.8), v3(sx * 1.7, 3.0, -2.4), 0.6, 0.45, 0.2).moved(M), 0.2)
        o.add(along(v3(sx * 1.1, 4.0, 2.2), v3(sx * 1.7, 3.4, 2.6), 0.6, 0.45, 0.2).moved(M), 0.2)


# ------------------------------------------------------------------------------------------------ SD-C cradle + pack saddle
def cradle(S):
    """Cradle in the backpack frame: front face y = 0, 2.0 mm D-flat peg toward -y (flat up, like every Vigil pack)."""
    C = S["cradle"]
    o = Ops()
    o.add(rbox(v3(0, 0.55, 0), (2.9, 0.55, 3.6), I3, 0.35))                           # plate
    wisp_folded(o, S, np.eye(4))
    for z in (-3.3, 3.5):                                                             # retaining straps over the stack
        o.add(rbox(v3(0, 1.4, z), (3.4, 1.4, 0.45), I3, 0.2), 0.15)
    o.add(d_peg((0, 0.3, 0), (0, -1, 0), C["peg_d"], C["peg_len"] + 0.3, key=(0, 0, 1)))
    return o


def pack_heightmap(pack_grid, clearance):
    """Top of the pack in every (x, y) column of its sculpt grid, grown sideways by the clearance: the saddle slides
    down onto the pack, so it must clear everything at or below the pack's top in each column."""
    D, lo, h = pack_grid.D, pack_grid.lo, pack_grid.h
    inside = D < 0
    nz = D.shape[2]
    zi = np.where(inside.any(axis=2), nz - 1 - np.argmax(inside[:, :, ::-1], axis=2), -1)
    top = np.where(zi >= 0, lo[2] + zi * h, -100.0)
    # one extra cell: the bilinear lookup ramps across one cell at a column edge, so a dilation of exactly the
    # clearance left the saddle touching the pack (first build: min clearance -0.004 mm at the cheeks)
    r = int(math.ceil(clearance / h)) + 1
    grown = top.copy()
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            if i * i + j * j <= r * r:
                grown = np.maximum(grown, np.roll(np.roll(top, i, 0), j, 1))
    return grown + clearance, lo, h


def saddle(S, hm):
    """Pack saddle: caps the top and back of the line power pack (cheeks either side of the core), 0.1 mm clear of it,
    with the 2.0 mm D-flat socket on its back for the cradle peg."""
    C = S["cradle"]
    top, lo, h = hm
    nx, ny = top.shape

    def under_pack(P):
        fx = (P[:, 0] - lo[0]) / h
        fy = (P[:, 1] - lo[1]) / h
        i = np.clip(np.floor(fx).astype(int), 0, nx - 2)
        j = np.clip(np.floor(fy).astype(int), 0, ny - 2)
        tx, ty = np.clip(fx - i, 0, 1), np.clip(fy - j, 0, 1)
        t = (top[i, j] * (1 - tx) * (1 - ty) + top[i + 1, j] * tx * (1 - ty) + top[i, j + 1] * (1 - tx) * ty
             + top[i + 1, j + 1] * tx * ty)
        return P[:, 2] - t                                   # < 0: at or below the pack top in this column
    o = Ops()
    sx, sy, sz = C["saddle_socket"]
    o.add(rbox(v3(0, 2.9, 1.5), (3.15, 1.3, 2.5), I3, 0.4))                           # back shell + cheeks
    o.add(rbox(v3(0, 2.25, 3.65), (2.95, 1.25, 0.4), I3, 0.25), 0.15)                 # top cap
    o.add(rbox(v3(0, (sy + 3.8) / 2, sz), (1.8, (sy - 3.8) / 2, 1.8), I3, 0.4), 0.3)  # socket boss
    o.cut(Shape(under_pack, (-4, -1, -6), (4, 5, 6)))
    o.cut(d_peg((0, sy + 0.01, sz), (0, -1, 0), C["peg_d"], C["sock_depth"], key=(0, 0, 1), grow=0.1))
    return o


# ------------------------------------------------------------------------------------------------ SD-2 Tick
def track(xc, y0, y1, r, w, edge=0.25):
    zc = r
    ay, by = y0 + r, y1 - r

    def f(P):
        t = np.clip((P[:, 1] - ay) / (by - ay), 0, 1)
        dy = P[:, 1] - (ay + t * (by - ay))
        d2 = np.hypot(dy, P[:, 2] - zc) - (r - edge)
        dx = np.abs(P[:, 0] - xc) - (w / 2 - edge)
        return np.minimum(np.maximum(d2, dx), 0) + np.hypot(np.maximum(d2, 0), np.maximum(dx, 0)) - edge
    return Shape(f, (xc - w / 2, y0, 0), (xc + w / 2, y1, 2 * r))


def tick_hull(S):
    T = S["tick"]
    tr = T["track"]
    o = Ops()
    hw, dz, py, shy = T["hull_half_w"], T["deck_z"], T["prow_y"], T["shoulder_y"]
    apex = v3(0, py, 0)
    chev = [half(apex, unit((s * (shy - py), -hw, 0))) for s in (-1, 1)]              # chevron plan faces
    glacis_up = half(v3(0, py, 3.6), unit((0, -(dz - 3.6), 4.0)))
    glacis_lo = half(v3(0, py, 3.0), unit((0, -2.0, -2.0)))
    o.add(rbox(v3(0, -0.6, 3.5), (hw, 8.9, 2.5), I3, 0.4).clip(*chev, glacis_up, glacis_lo))   # hull, chevron prow
    for s in (-1, 1):
        xc = s * tr["xc"]
        o.add(track(xc, tr["y0"], tr["y1"], tr["r"], tr["w"]), 0.0)
        o.add(rbox(v3(s * 5.05, -0.2, 5.15), (1.4, 7.0, 0.85), I3, 0.3).clip(*chev), 0.15)          # sponson / guard
        o.add(rbox(v3(s * 5.95, -0.2, 3.95), (0.5, 6.8, 0.65), I3, 0.2).clip(*chev), 0.1)            # skirt lip 1.0
    # track shoe grooves 0.4 x 0.3: bottom run and the lower arcs only; the top run sits under the sponson, where a
    # groove would be a sealed void (first build: 22 bodies, the groove boxes as 0.73 mm3 inner shells)
    for s in (-1, 1):
        xc, r, w = s * tr["xc"], tr["r"], tr["w"]
        ay, by = tr["y0"] + r, tr["y1"] - r
        for y in np.arange(ay + 0.45, by, 0.95):
            o.cut(rbox(v3(xc, y, 0.0), (w / 2 + 0.2, 0.2, 0.3), I3, 0.0))
        for cy, sgn in ((ay, -1), (by, 1)):
            for phi in np.arange(0.45 / r, math.pi, 0.95 / r):
                p = v3(xc, cy + sgn * r * math.sin(phi), r + r * math.cos(phi))
                if p[2] > 3.2:                                                        # under the skirt / sponson
                    continue
                nrm = v3(0, sgn * math.sin(phi), math.cos(phi))
                tan = np.cross(v3(1, 0, 0), nrm)
                o.cut(rbox(p, (w / 2 + 0.2, 0.2, 0.3), np.stack([v3(1, 0, 0), tan, nrm], axis=1), 0.0))
        face = s * (tr["xc"] + w / 2)
        for y, rr in ((ay, 1.65), (by, 1.65), (-2.8, 1.0), (0.0, 1.0), (2.8, 1.0)):
            zc = r if rr > 1.2 else 1.25
            o.add(cyl(v3(face - s * 0.1, y, zc), v3(face + s * 0.22, y, zc), rr, 0.1))        # wheels / idlers
            o.add(cyl(v3(face, y, zc), v3(face + s * 0.38, y, zc), 0.42, 0.1))                # hubs
    o.add(capsule(v3(0, 0.6, dz), v3(0, 7.2, dz), 0.5), 0.2)                          # keel ridge 1.0 wide
    for y in (4.6, 5.5, 6.4):                                                         # engine grille slots 0.44
        o.cut(rbox(v3(2.0, y, dz), (1.1, 0.22, 0.35), I3, 0.05))
    o.add(rbox(v3(2.0, 1.4, dz + 0.1), (1.05, 1.25, 0.28), I3, 0.15), 0.08)           # access hatch, 0.2 proud
    ng = unit((0, -(dz - 3.6), 4.0))
    for s in (-1, 1):                                                                 # split chevron on the glacis
        e = unit((s * hw, shy - py, 0))
        e = unit(e - ng * float(e @ ng))
        c = v3(s * 1.05, -7.7, 0)
        c[2] = 3.6 + (c[1] - py) / (dz - 3.6 + 1e-9) * 0 + (c[1] - py) * (dz - 3.6) / 4.0
        o.cut(rbox(c, (1.0, 0.22, 0.3), np.stack([e, np.cross(ng, e), ng], axis=1), 0.05))
    o.add(rbox(v3(0, 8.45, 2.5), (1.0, 0.6, 0.6), I3, 0.25), 0.15)                    # tow hitch
    for key, sd in (("weapon_socket", T["weapon_socket"]), ("mast_socket", T["mast_socket"])):
        x, y = sd["xy"]
        o.cut(d_peg((x, y, dz + 0.01), (0, 0, -1), sd["peg_d"], sd["sock_depth"], key=(0, -1, 0), grow=0.1))
    return o


def peg_down(o, sd):
    o.add(d_peg((0, 0, 0.3), (0, 0, -1), sd["peg_d"], sd["peg_len"] + 0.3, key=(0, -1, 0)))


def tick_mast(S):
    """Periscope sensor mast: collar, 1.1 mm shaft, sensor head with split-chevron lenses and a keel cap."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.55), 1.1, 0.15))
    o.add(cyl(v3(0, 0, 0.3), v3(0, 0, 3.8), 0.55, 0.1), 0.15)
    o.add(rbox(v3(0, -0.15, 4.3), (1.3, 0.85, 0.75), I3, 0.3), 0.2)
    o.add(capsule(v3(0, -0.6, 5.05), v3(0, 0.6, 5.05), 0.45), 0.15)                     # keel cap 0.9 wide
    for s in (-1, 1):
        o.cut(rbox(v3(s * 0.5, -1.05, 4.3), (0.5, 0.35, 0.22), rot(RY, s * 26), 0.06))     # lens bars 0.44 x 0.3
    peg_down(o, S["tick"]["mast_socket"])
    return o


def talon_on_mount(S):
    """Module A: turret ring, pintle and the VW-05 Talon carbine from tools/armory.py (grown 0.05 mm)."""
    import armory
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.8), 1.5, 0.2))
    o.add(rbox(v3(0, 0.4, 1.4), (0.6, 0.7, 0.65), I3, 0.2), 0.15)
    o.add(rbox(v3(0, 1.5, 1.25), (1.0, 0.6, 0.45), I3, 0.2), 0.15)                     # battery box
    R = np.column_stack([(0, -1, 0), (1, 0, 0), (0, 0, 1)])                          # weapon x -> -y (muzzle forward)
    o.add(armory.talon_carbine().offset(0.05).moved(mat(R, (0, 0.6, 2.75))), 0.1)
    peg_down(o, S["tick"]["weapon_socket"])
    return o


def plough(S):
    """Module B: charge-layer box on the deck and a V mine-plough carried ahead of the chevron prow on two arms
    that clear the glacis by >= 0.35 mm (module origin = deck socket at hull (0, -2.2, 6.0))."""
    T = S["tick"]
    ox, oy = T["weapon_socket"]["xy"]
    oz = T["deck_z"]
    L = lambda x, y, z: v3(x - ox, y - oy, z - oz)  # noqa: E731  hull coords -> module coords
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.8), 1.5, 0.2))
    o.add(rbox(v3(0, 0.6, 1.5), (1.4, 1.3, 0.8), I3, 0.3), 0.2)
    for x in (-0.75, 0.0, 0.75):
        o.add(cyl(v3(x, 0.7, 2.2), v3(x, 0.7, 2.55), 0.4, 0.1), 0.05)                  # charges
    for s in (-1, 1):
        a, b, c = L(s * 1.2, -3.0, 8.3), L(s * 1.2, -10.6, 4.4), L(s * 1.2, -11.9, 1.6)
        o.add(along(a, b, 0.55, 0.55, 0.2, ext=0.3), 0.15)
        o.add(along(b, c, 0.55, 0.55, 0.2, ext=0.3), 0.15)
    tip = L(0, -12.8, 1.2)
    for s in (-1, 1):
        wing = L(s * 6.2, -10.0, 1.2)
        o.add(along(tip, wing, 0.5, 1.0, 0.2, ext=0.25), 0.1)                            # blade 1.0 thick, 2.0 tall
        for t in (0.3, 0.6, 0.9):
            p = tip + (wing - tip) * t + v3(0, -0.5, -0.65)
            o.add(rbox(p, (0.45, 0.6, 0.35), rot(Z, s * 24), 0.15), 0.05)              # tines
    peg_down(o, T["weapon_socket"])
    return o


def relay(S):
    """Module C: relay box, telescopic antenna with a dipole bar, two banks of three smoke dischargers."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.8), 1.5, 0.2))
    o.add(rbox(v3(0, 0.3, 1.5), (1.3, 1.2, 0.75), I3, 0.3), 0.2)
    o.add(cyl(v3(0.5, 0.8, 2.0), v3(0.5, 0.8, 5.0), 0.6, 0.1), 0.15)
    o.add(cyl(v3(0.5, 0.8, 4.8), v3(0.5, 0.8, 5.2), 0.78, 0.1), 0.05)
    o.add(cyl(v3(0.5, 0.8, 5.0), v3(0.5, 0.8, 8.0), 0.5, 0.1), 0.1)
    o.add(sphere(v3(0.5, 0.8, 8.05), 0.65), 0.1)
    o.add(rbox(v3(0.5, 0.8, 7.0), (1.2, 0.45, 0.45), I3, 0.15), 0.1)                   # dipole bar 0.9
    for s in (-1, 1):
        d = unit((s * 0.8, -0.25, 0.6))
        for y in (-0.75, 0.3, 1.35):
            b = v3(s * 1.0, y, 1.7)
            e = b + d * 1.7
            o.add(cyl(b, e, 0.5, 0.1), 0.05)                                           # discharger 1.0 dia
            o.cut(cyl(e - d * 0.35, e + d * 0.3, 0.28))                                # bore 0.56, 0.35 deep
    peg_down(o, S["tick"]["weapon_socket"])
    return o


# ------------------------------------------------------------------------------------------------ stem and bases
def stem_dir(S):
    a = math.radians(S["stem"]["lean_deg"])
    return v3(0, -math.sin(a), math.cos(a))


def flight_stem(S):
    """Printed 1.6 mm flight stem along z, bottom end at z = 0 (same size as a 1.6 mm clear rod)."""
    st = S["stem"]
    L = st["visible_mm"] + st["insert_wisp"] + st["insert_base"]
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, L), st["d"] / 2, 0.2))
    return o


def base(S, stem=False):
    """32 x 3 mm round base: bevelled rim, a chevron deck-plate pattern (engraved 0.45 x 0.35 mm, stopped short of the
    rim and the magnet floor), 5 x 2 mm magnet pocket vented to the rim; the stem variant adds a launch pad with the
    raked 1.8 mm stem socket behind the centre."""
    B = S["base"]
    R0, H0, ins = B["d"] / 2, B["h"], B["top_inset"]
    k = ins / H0
    o = Ops()

    def body(Q):
        rr = np.hypot(Q[:, 0], Q[:, 1])
        side = (rr - (R0 - k * np.clip(Q[:, 2], 0, H0))) / math.sqrt(1 + k * k)
        return np.maximum(side, np.maximum(-Q[:, 2], Q[:, 2] - H0))
    o.add(Shape(body, (-R0, -R0, 0), (R0, R0, H0)))
    ring = lambda Q: np.maximum(np.hypot(Q[:, 0], Q[:, 1]) - (R0 - ins - 1.5), 3.6 - np.hypot(Q[:, 0], Q[:, 1]))  # noqa: E731
    for ang in (35.0, -35.0):
        n = v3(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)
        for t in np.arange(-12.0, 12.1, 6.0):
            seam = Shape(lambda Q, n=n, t=t: np.maximum(np.abs(Q @ n - t) - 0.225, H0 - 0.35 - Q[:, 2]),
                         (-R0, -R0, H0 - 0.6), (R0, R0, H0 + 0.6))
            o.cut(seam.clip(Shape(ring, (-R0, -R0, 0), (R0, R0, H0 + 1))))
    o.cut(cyl(v3(0, 0, -1), v3(0, 0, B["pocket_depth"]), B["pocket_d"] / 2))
    o.cut(rbox(v3(-R0 / 2, 0, 0), (R0 / 2 + 1, B["vent_w"] / 2, B["vent_d"]), I3, 0.0))    # vent to the rim (-x)
    if stem:
        sb = B["stem_boss"]
        x, y = sb["xy"]
        top = H0 + sb["h"]
        o.add(cyl(v3(x, y, H0 - 0.3), v3(x, y, top), sb["r"], 0.5), 0.3)               # launch pad
        o.add(cyl(v3(x, y, top - 0.2), v3(x, y, top + 0.15), sb["r"] - 0.6, 0.1), 0.05)  # pad ring, 0.15 proud
        u = stem_dir(S)
        p = v3(x, y, top + 0.15)
        o.cut(cyl(p + u * 1.0, p - u * sb["socket_depth"], sb["socket_d"] / 2))
    return o
