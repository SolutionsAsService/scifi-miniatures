#!/usr/bin/env python3
"""Wayfarer-class APC (AW-8A, Tally RWS): print-ready 1:56 resin kit for the Aster Compact Vigil line.

Run with the sculpt venv:  ~/projects/venvs/scifi-sculpt/bin/python source/build.py [--stage N]
Frame: mm at 1:56, x = vehicle front, y = vehicle left, z up, ground z = 0 (same frame as concepts/wayfarer-apc).
Every number comes from spec/wayfarer-apc.spec.json (or is derived from it here, with the derivation in a comment).

Representation: exact CSG with manifold3d (hard-surface vehicle: crisp planes, low triangle counts, one closed manifold
solid per part by construction; no SDF and no decimation). The hull is the union of two convex station solids (deep-V
lower hull, tumblehome upper hull); its cavity is the union of their exact inward plane offsets (wall >= 2.0 mm
everywhere because (A u B) - t contains (A - t) u (B - t)).

--stage N builds the kit as it stood after design move M<N> (see DESIGN-LOG.md) so each move can be measured:
  1 hull: one manifold, hollow, split at the ring line, split pins, drains     4 shared 30 mm ring + Tally RWS
  2 relief layer (plates, lips, crest, vane, periscopes, cupola, smoke ...)     5 ramp, hatches, door, bay (BREAK)
  3 running gear: 8 identical wheels on D-flat stubs                          6 (default) everything + renders
Outputs: build/upright/*.stl, viewer/wayfarer-apc.parts.json, reports/build.json, images/*.png.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "concepts" / "_tools"))
import turret_ring as TR  # noqa: E402

S = json.loads((PKG / "spec" / "wayfarer-apc.spec.json").read_text())
M = mf.Manifold
H = S["hull"]
T = H["wall"]
RZ = H["roof_z"]
XS = H["split_x"]
X0, X1 = H["x_stern"], H["x_bow"]
SEG = 64


# ------------------------------------------------------------------------------------------------ CSG helpers
def hullp(pts):
    return M.hull_points([tuple(float(c) for c in p) for p in pts])


def box(c, s):
    return M.cube(tuple(float(v) for v in s), True).translate(tuple(float(v) for v in c))


def chbox(c, s, ch=0.4):
    """Chamfered box: hull of three boxes, each shrunk by the chamfer on two axes."""
    s = np.asarray(s, float)
    ch = min(ch, s.min() / 2 - 1e-3)
    parts = []
    for ax in range(3):
        e = s.copy()
        for o in range(3):
            if o != ax:
                e[o] -= 2 * ch
        parts.append(M.cube(tuple(e), True))
    return M.batch_hull(parts).translate(tuple(float(v) for v in c))


def frame_to(z_axis, y_hint=(0, 0, 1)):
    """Rotation matrix whose columns are the images of local x, y, z (local z -> z_axis, local y ~ y_hint)."""
    z = np.asarray(z_axis, float)
    z /= np.linalg.norm(z)
    y = np.asarray(y_hint, float) - z * np.dot(y_hint, z)
    if np.linalg.norm(y) < 1e-6:
        y = np.array([1.0, 0, 0]) - z * z[0]
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    return np.stack([x, y, z], axis=1)


def place(m, R=None, t=(0, 0, 0)):
    A = np.zeros((3, 4))
    A[:3, :3] = np.eye(3) if R is None else R
    A[:3, 3] = t
    return m.transform(A)


def cyl_ab(a, b, r, seg=SEG, r2=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    c = M.cylinder(L, r, r if r2 is None else r2, seg)
    return place(c, frame_to(b - a), a)


def chcyl_ab(a, b, r, ch, seg=SEG):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    return M.batch_hull([cyl_ab(a + d * ch, b - d * ch, r, seg), cyl_ab(a, b, r - ch, seg)])


def rrect(cx, cy, w, h, r, z0, z1, seg=24):
    """Rounded rectangle prism (axis z)."""
    cs = mf.CrossSection.square((w - 2 * r, h - 2 * r), True).offset(r, mf.JoinType.Round, 2.0, seg)
    return cs.extrude(z1 - z0).translate((cx, cy, z0))


def prism_x(poly_yz, x0, x1):
    """Extrude a (y, z) polygon along +x from x0 to x1."""
    cs = mf.CrossSection([[(float(y), float(z)) for y, z in poly_yz]])
    m = cs.extrude(x1 - x0)                     # local (u, v, w) = (y, z, x)
    R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)
    return place(m, R, (x0, 0, 0))


def union(ms):
    ms = [m for m in ms if m is not None and not m.is_empty()]
    return M.batch_boolean(ms, mf.OpType.Add) if ms else M()


def convex_offset(m, t):
    """Exact inward offset of a convex solid: intersect its face planes, each moved inward by t."""
    mesh = m.to_mesh()
    V = np.asarray(mesh.vert_properties)[:, :3].astype(float)
    F = np.asarray(mesh.tri_verts)
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    ln = np.linalg.norm(n, axis=1)
    keep = ln > 1e-9
    n = n[keep] / ln[keep, None]
    d = np.einsum("ij,ij->i", n, V[F[keep, 0]])
    planes = {}
    for ni, di in zip(n, d):
        planes.setdefault((round(ni[0], 5), round(ni[1], 5), round(ni[2], 5), round(di, 4)), (ni, di))
    out = M.cube((1000, 1000, 1000), True)
    for ni, di in planes.values():
        out = out.trim_by_plane(tuple(-ni), float(-(di - t)))
    return out


def stations(st):
    pts = []
    for x, sec in st:
        for y, z in sec:
            pts += [(x, y, z), (x, -y, z)]
    return pts


def to_tm(m, name):
    mesh = m.to_mesh()
    # process=False: manifold3d already shares vertices; trimesh's tolerance merge collapsed sub-0.01 mm CSG edges on the
    # ramp into non-manifold fans (measured M5: 5 bodies after merge vs 1 component in manifold3d)
    tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3].astype(np.float64), np.asarray(mesh.tri_verts), process=False)
    bodies = len(tm.split(only_watertight=False))
    if not (tm.is_watertight and bodies == 1 and tm.volume > 0):
        raise SystemExit(f"{name}: not one closed solid (watertight={tm.is_watertight}, bodies={bodies}, vol={tm.volume})")
    # the STL a slicer (and cad_inspect_stl_geometry) reads welds float32 positions: surfaces that merely touch along an
    # edge (e.g. a cylinder tangent to a plate face) become non-manifold there. Refuse that here (measured M5: ramp, 22 edges).
    w = trimesh.Trimesh(np.asarray(tm.vertices, np.float32).astype(np.float64), tm.faces, process=True)
    e = w.edges_sorted
    _, cnt = np.unique(e, axis=0, return_counts=True)
    if not (w.is_watertight and int((cnt != 2).sum()) == 0):
        raise SystemExit(f"{name}: welded float32 STL is not 2-manifold ({int((cnt != 2).sum())} bad edges)")
    return tm


def zg(x):
    """Glacis top surface height at station x (plane through the roof edge at glacis_x and the bow top at x_bow)."""
    return RZ - (x - H["glacis_x"]) * (RZ - 25.5) / (X1 - H["glacis_x"])


# ------------------------------------------------------------------------------------------------ the hull
def hull_solids():
    lower = hullp(stations(H["lower_stations"]))
    upper = hullp(stations(H["upper_stations"]))
    return lower, upper


def d_cutter(a, axis, d, depth, flat, key=(0, 0, 1)):
    """D-flat socket/peg body: cylinder from a along axis, everything beyond 'flat' from the axis toward key removed."""
    a, axis, key = np.asarray(a, float), np.asarray(axis, float), np.asarray(key, float)
    c = cyl_ab(a, a + axis / np.linalg.norm(axis) * depth, d / 2, 48)
    return c.trim_by_plane(tuple(-key), float(-(np.dot(key, a) + flat)))


def d_peg(a, axis, d, length, flat, key=(0, 0, 1), tip=0.25):
    a, axis = np.asarray(a, float), np.asarray(axis, float) / np.linalg.norm(axis)
    body = M.batch_hull([cyl_ab(a, a + axis * (length - tip), d / 2, 48), cyl_ab(a, a + axis * length, d / 2 - tip, 48)])
    key = np.asarray(key, float)
    return body.trim_by_plane(tuple(-key), float(-(np.dot(key, a) + flat)))


def build_hull(stage):
    lower, upper = hull_solids()
    outer = lower + upper
    # M6: near the bow the lower cavity's top and the upper cavity's floor (z 23.4) cross each other, leaving a feather-
    # edged internal shelf (measured: 0.05-0.11 mm thin spots, 47.8 mm2, at x ~70.5). Ahead of x 60 the lower cavity is
    # capped at z 21.8, so the shelf is a uniform 1.6 mm deck there instead of a knife edge.
    li = convex_offset(lower, T)
    li = li.trim_by_plane((-1, 0, 0), -60.0) + (li.trim_by_plane((1, 0, 0), 60.0).trim_by_plane((0, 0, -1), -21.8))
    cavity = li + convex_offset(upper, T)
    shell = outer - cavity
    add, cut = [], []
    ring_c = S["ring"]["centre"]
    sp = S["split_pins"]
    # --- M1: split-pin bosses (inside, clipped to the outer solid), ring magnet boss, drains, roof vent
    for (yc, zc), (hy, hz) in zip(sp["bosses_yz"], sp["boss_half"]):
        # boss box reaches 4 mm past its socket toward the side wall, then is clipped by the outer solid, so it always
        # fuses with the wall whatever the wall thickness (wall 1.8 left a 0.24 mm gap otherwise: measured, M2R)
        sg = 1.0 if yc > 0 else -1.0
        add.append(box((XS, yc + sg * 2.0, zc), (2 * sp["boss_depth"], 2 * hy + 4.0, 2 * hz)) ^ outer)
        a = (XS - sp["socket_depth"], yc, zc)
        cut.append(d_cutter(a, (1, 0, 0), sp["d"] + 0.2, 2 * sp["socket_depth"], 0.3 * sp["d"] + 0.1))
        # R1 (Holmes/Mace): 0.45 mm x 45 deg lead-in cone on both socket mouths
        r0 = (sp["d"] + 0.2) / 2
        # lead-in 0.15 mm (was 0.45): a 13.2 mm2 mouth open to the plate flagged as an 11.9 mm2 suction cup (M6)
        cut.append(cyl_ab((XS, yc, zc), (XS + 0.15, yc, zc), r0 + 0.15, 48, r0))
        cut.append(cyl_ab((XS, yc, zc), (XS - 0.15, yc, zc), r0 + 0.15, 48, r0))
        # M6: 1.2 mm vent from each socket bottom through the boss into the cavity (a socket open to the plate and closed
        # above was a 11.9 mm2 suction cup); the step still stops the pin at 3.95 mm
        cut.append(cyl_ab((XS - sp["boss_depth"] - 1.0, yc, zc), (XS + sp["boss_depth"] + 1.0, yc, zc), 0.6, 16))
    add.append(TR.hull_magnet_boss(ring_c[0], ring_c[1], RZ, T, S["ring"]["boss_depth"], S["ring"]["boss_r"]))
    for x in S["drains_x"]:
        cut.append(cyl_ab((x, 0, -1), (x, 0, 14.0), S["drain_d"] / 2, 32))
    vx, vy = S["roof_vent"]
    cut.append(cyl_ab((vx, vy, RZ - 4), (vx, vy, RZ + 2), S["drain_d"] / 2, 32))
    # M6: split-face vents. Each half prints standing on its split face, so its cavity sits on the plate; a 3.5 mm hole
    # centred on the split plane at the keel and at the roof spine (under the turntable) gives each half a half-hole
    # open at layer 0 (measured before: one 901 / 905 mm2 suction cup per half). Assembled they read as two drains.
    cut.append(cyl_ab((XS, 0, -1), (XS, 0, 14.0), S["drain_d"] / 2, 32))
    cut.append(cyl_ab((XS, 0, RZ - 4), (XS, 0, RZ + 2), S["drain_d"] / 2, 32))
    # seam panel line: 0.7 mm wide, 0.45 mm deep groove in the hull skin round the split plane
    # seam panel line: 0.8 mm wide, 0.5 mm deep into the skin AND through every detail standing on the skin there
    # (M6: a groove cut only in the skin left the chine rail bridging it with 0.23 mm walls)
    groove = box((XS, 0, 25), (0.8, 80, 60)) - (convex_offset(lower, 0.5) + convex_offset(upper, 0.5))
    if stage >= 2:
        a2, c2 = relief(outer)
        add += a2
        cut += c2
    if stage >= 3:
        add += running_gear_stubs()
    if stage >= 4:
        # radial gaps where the split plane crosses the collar: a plane through a ring leaves 41 deg feather edges
        # (measured 0.6-0.9 mm2 thin spots per side, M6); cut radially, each half's collar ends square
        col = TR.hull_collar(ring_c[0], ring_c[1], RZ)
        for s in (1, -1):
            a0, a1 = math.radians(131.0), math.radians(141.5)
            R_ = 30.0
            wedge = [(ring_c[0], ring_c[1])] + [(ring_c[0] + R_ * math.cos(a), ring_c[1] + s * R_ * math.sin(a)) for a in np.linspace(a0, a1, 6)]
            if s < 0:
                wedge = wedge[::-1]
            col = col - mf.CrossSection([wedge]).extrude(10.0).translate((0, 0, RZ - 2.0))
        add.append(col)
        cut.append(TR.hull_magnet_pocket(ring_c[0], ring_c[1], RZ))
        cut.append(cyl_ab((ring_c[0] + 4.6, ring_c[1], RZ - 0.4), (ring_c[0] + 4.6, ring_c[1], RZ + 0.5), 0.5, 20))   # polarity dot (R5)
    if stage >= 5:
        a5, c5 = open_box(outer)
        add += a5
        cut += c5
    body = union([shell] + add)
    body = body - union(cut + [groove])
    STATS["relief_outside_hull_mm3"] = round((body - outer).volume(), 1)
    STATS["shell_only_mm3"] = round(shell.volume(), 1)
    front = drop_slivers(body.trim_by_plane((1, 0, 0), XS))
    rear = drop_slivers(body.trim_by_plane((-1, 0, 0), -XS))
    return front, rear, outer


def drop_slivers(m, min_mm3=0.01):
    """Remove zero-volume components the seam-groove boolean leaves where the two convex skins meet (measured: four
    components of 0.000 mm3 at the tumblehome, x -11.5..-11.15). Real components are never this small."""
    keep = [c for c in m.decompose() if abs(c.volume()) >= min_mm3]
    return union(keep)


# ------------------------------------------------------------------------------------------------ M2 relief layer
def relief(outer):
    add, cut = [], []
    # six alternating applique plates a side on the vertical side wall (z 22.4-29.6); gap centred on the split
    b = np.linspace(-70.0, H["glacis_x"], 7)
    for s in (1, -1):
        for i in range(6):
            x0, x1 = b[i] + 0.6, b[i + 1] - 0.6
            t = 0.9 if i % 2 == 0 else 1.3                      # alternating stand-off (R2: below the 1.9 mm rail)
            yc = s * (27.6 - 0.3 + (t + 0.3) / 2)
            add.append(chbox(((x0 + x1) / 2, yc, 26.0), (x1 - x0, t + 0.3, 7.2), 0.45))
            # one 0.6 mm engraved line per plate, stopped 1.5 mm short of the plate ends
            cut.append(box(((x0 + x1) / 2, s * (27.6 + t), 27.4), (x1 - x0 - 3.0, 1.2, 0.8)))     # 0.8 wide x 0.6 deep
        # chine rail: shadow line at the tumblehome break (45 deg underside, prints without support when x is up)
        ys = s * 27.6
        add.append(hullp([(x, ys + s * dy, z) for x in (X0 + 1.0, H["glacis_x"])
                          for dy, z in ((-0.3, 30.6), (0.9, 30.6), (0.9, 30.2), (-0.3, 29.0)) ]))
        # R1 (Brancusi/Hildebrand): continuous sponson rail at z 21.6, the dominant line, 1.3 mm proud, 45 deg underside
        # 1.9 mm proud, 45 deg underside (R2); 0.6 mm flat at the bottom (M6: the knife-edged tip was a 0.3 mm fin)
        rail = ((-0.3, 22.5), (1.9, 22.5), (1.9, 21.9), (0.3, 20.3), (-0.3, 20.3))
        side = lambda x: 27.6 - max(0.0, x - H["glacis_x"]) * (27.6 - 23.5) / (X1 - H["glacis_x"])
        add.append(hullp([(x, s * (side(x) + dy), z) for x in (X0 + 1.0, H["glacis_x"]) for dy, z in rail]))
        # on the bow taper the side runs in over the front tyres: shallower underside keeps 0.5 mm over the tread (M3 interference)
        rail_t = ((-0.3, 22.5), (1.9, 22.5), (1.9, 22.0), (0.3, 21.5), (-0.3, 21.5))
        add.append(hullp([(x, s * (side(x) + dy), z) for x in (H["glacis_x"], X1 - 0.5) for dy, z in rail_t]))
        # fender lips over each wheel pair: lip + downturned flange outboard of the tyre
        ax = S["wheels"]["axles_x"]
        for xa, xb in ((ax[1] - 12.5, ax[0] + 12.5), (ax[3] - 12.5, ax[2] + 12.5)):
            add.append(chbox(((xa + xb) / 2, s * 29.1, 21.0), (xb - xa, 0.8, 2.4), 0.25))         # flange hanging under the rail
        add.append(chbox(((H["glacis_x"] + ax[0] + 12.5) / 2, s * 26.25, 21.5), (ax[0] + 12.5 - H["glacis_x"], 6.5, 0.8), 0.2))  # front lip where the side tapers
        # periscope hoods on the tumblehome face, each with a pair of slanted lens slots (split chevron)
        tdir = np.array([0, -6.1 * s, 8.5])
        tdir /= np.linalg.norm(tdir)
        nrm = np.array([0, 8.5 * s, 6.1])
        nrm /= np.linalg.norm(nrm)
        base = np.array([0, s * 24.6, 34.2])
        Rh = np.stack([np.array([1.0, 0, 0]), tdir, nrm], axis=1)
        for x in S["periscopes_x"]:
            c = base + np.array([x, 0, 0]) + nrm * 0.45
            add.append(place(chbox((0, 0, 0), (5.0, 3.0, 1.5), 0.35), Rh, c))
            for k in (1, -1):
                Rl = Rh @ np.array([[math.cos(math.radians(35 * k)), -math.sin(math.radians(35 * k)), 0],
                                    [math.sin(math.radians(35 * k)), math.cos(math.radians(35 * k)), 0], [0, 0, 1]])
                # 1.8 mm long at +-0.9 mm: the 2.2 mm slots broke into the hood chamfers (0.2 mm lips, M6 thin spots)
                cut.append(place(box((0, 0, 0), (0.9, 1.8, 1.0)), Rl, c + nrm * 0.75 + np.array([k * 0.9, 0, 0])))
        # stern lockers either side of the ramp
        add.append(chbox((X0 - 1.0, s * 21.2, 26.3), (3.0, 4.6, 6.2), 0.4))
        add.append(box((X0 - 0.2, s * 24.6, 32.0), (1.2, 2.2, 1.2)))            # tail light
        # waterjets (amphibious lore): ducts under the sponson rear, nozzles past the stern
        yj = s * 21.0
        add.append(M.batch_hull([cyl_ab((-62.0, yj, 18.8), (-61.0, yj, 18.8), 2.3, 40),
                                 cyl_ab((-73.5, yj, 18.4), (-72.5, yj, 18.4), 3.0, 40),
                                 box((-67.5, yj, 21.4), (12.0, 5.0, 1.0))]))
        add.append(chcyl_ab((-73.0, yj, 18.4), (-76.4, yj, 18.4), 2.7, 0.3, 48))
        cut.append(cyl_ab((-75.4, yj, 18.4), (-77.0, yj, 18.4), 1.4, 32))
        # headlamps and tow eyes on the bow
        add.append(chbox((X1 + 0.15, s * 18.5, 23.6), (1.1, 4.2, 1.6), 0.3))
        add.append(chcyl_ab((71.5, s * 9.0, 19.8), (74.6, s * 9.0, 19.8), 1.1, 0.25, 32))
        # smoke dischargers: a bank of four per side on the front roof corners, 40 deg out from vertical
        sm = S["smoke"]
        add.append(chbox((30.4, s * 19.1, RZ + 0.5), (10.0, 3.0, 1.6), 0.35))
        td = math.radians(sm["tilt_deg"])
        for x in sm["x"]:
            a = np.array([x, s * sm["y"], RZ + 0.6])
            add.append(chcyl_ab(a, a + np.array([0, s * math.sin(td), math.cos(td)]) * sm["len"], sm["r"], 0.2, 24))
        # belly strakes: one rib per V face, the blast chevron made legible head-on
        tv = np.array([0, s * 17.5, 8.0])
        tv /= np.linalg.norm(tv)
        nv = np.array([0, s * 8.0, -17.5])
        nv /= np.linalg.norm(nv)
        p = np.array([0, s * 8.75, 10.5])
        sec = [p + tv * 0.6 - nv * 0.3, p - tv * 0.6 - nv * 0.3, p + tv * 0.35 + nv * 0.8, p - tv * 0.35 + nv * 0.8]
        add.append(hullp([q + np.array([x, 0, 0]) for q in sec for x in (-62.0, 54.0)]))
    # keel crest: a blade 1.6 mm proud from the bow up the glacis and along the roof spine to the RWS ring collar
    rc = S["ring"]["centre"]
    xr = rc[0] + TR.collar_od() / 2 + 2.8          # crest end, just ahead of the collar; two arms then hug the ring (R2)
    pts = []
    for x, zb, h in ((72.8, zg(72.8) - 0.4, 1.6), (H["glacis_x"], RZ - 0.4, 1.6), (H["glacis_x"] - 6, RZ - 0.4, 1.6), (xr, RZ - 0.4, 1.6)):
        pts += [(x, 1.4, zb), (x, -1.4, zb), (x, 0.35, zb + 0.4 + h), (x, -0.35, zb + 0.4 + h)]
    add.append(hullp(pts[:8]))
    add.append(hullp(pts[4:12]))
    add.append(hullp(pts[8:16]))
    def crest_st(x, y, h, w=1.2):
        return [(x, y + w, RZ - 0.4), (x, y - w, RZ - 0.4), (x, y + 0.35, RZ + h), (x, y - 0.35, RZ + h)]
    for s in (1, -1):
        ra = TR.collar_od() / 2 + 1.6
        a1, a2 = math.radians(28), math.radians(58)
        p0 = crest_st(xr, 0.0, 1.6)
        p1 = crest_st(rc[0] + ra * math.cos(a1), s * ra * math.sin(a1), 1.3)
        p2 = crest_st(rc[0] + ra * math.cos(a2), s * ra * math.sin(a2), 0.9)
        add.append(hullp(p0 + p1))
        add.append(hullp(p1 + p2))
    # trim vane folded flat either side of the crest (two leaves), with a hinge bar at the bow end
    for s in (1, -1):
        leaf = []
        for x in (52.0, 69.5):
            for y in (2.4, 19.5):
                leaf += [(x, s * y, zg(x) - 0.3), (x, s * y, zg(x) + 0.9)]
        add.append(hullp(leaf))
        for y in (7.0, 14.0):
            add.append(hullp([(x, s * (y + dy), zg(x) + dz) for x in (53.0, 68.5) for dy in (-0.45, 0.45) for dz in (0.5, 1.6)]))
        add.append(chcyl_ab((70.6, s * 2.4, zg(70.6) + 0.5), (70.6, s * 19.5, zg(70.6) + 0.5), 0.75, 0.2, 24))
    # driver cupola (front left) with a split-chevron pair of vision blocks facing forward
    cu = S["cupola"]
    add.append(chcyl_ab((cu["x"], cu["y"], RZ - 0.5), (cu["x"], cu["y"], RZ + cu["h"]), cu["r"], 0.5, 64))
    add.append(chcyl_ab((cu["x"] - 0.6, cu["y"], RZ + cu["h"] - 0.2), (cu["x"] - 0.6, cu["y"], RZ + cu["h"] + 0.8), cu["r"] - 1.0, 0.3, 48))
    for k in (1, -1):
        ang = math.radians(28 * k)
        c = np.array([cu["x"] + math.cos(ang) * (cu["r"] - 0.2), cu["y"] + math.sin(ang) * (cu["r"] - 0.2), RZ + 1.5])
        Rv = frame_to((math.cos(ang), math.sin(ang), 0), (0, 0, 1))
        add.append(place(chbox((0, 0, 0), (2.8, 2.0, 1.6), 0.2), Rv, c))
        # lens 1.8 x 0.6 mm, 0.5 deep (M6: a 0.9 mm slot in a 1.6 mm block left 0.21 mm walls at the chamfers)
        cut.append(place(box((0, 0, 0), (1.8, 0.6, 1.0)), Rv, c + np.array([math.cos(ang), math.sin(ang), 0]) * 0.8))
    # engine deck louvres (front right roof): engraved 0.7 x 0.5 mm slots, stopped short of each other and of the edges
    for x in (30.5, 32.5, 34.5, 36.5, 38.5, 40.5):
        cut.append(box((x, -10.0, RZ), (0.8, 9.0, 1.2)))                      # 0.8 wide x 0.6 deep (R2, Holmes)
    # boarding rungs on the bow face (left) and a solid grab bar along the glacis edge beside the cupola (R2, Dreyfuss)
    add.append(chbox((72.6, 12.5, 18.8), (1.6, 4.0, 1.0), 0.25))
    add.append(chbox((X1 + 0.3, 12.5, 23.9), (1.2, 4.0, 1.0), 0.25))
    add.append(hullp([(x, y, zg(x) + dz) for x in (49.0, 58.0) for y in (20.15, 21.05) for dz in (-0.3, 0.9)]))
    # (roof stowage bin and antenna base removed in M5: the enlarged hatches fill the rear roof)
    return add, cut


# ------------------------------------------------------------------------------------------------ M3 running gear
W = S["wheels"]
PEG = W["peg"]
WZ = W["radius"]
WY_IN = W["track_half"] - W["width"] / 2          # inner tyre face (y = 19.8)


def axle_stations():
    for x in W["axles_x"]:
        for s in (1, -1):
            yield x, s


def running_gear_stubs():
    add = []
    for x, s in axle_stations():
        yo = s * (WY_IN - 0.2)                       # suspension block outer face, 0.2 mm short of the tyre
        add.append(chbox((x, s * 13.0 + (yo - s * 19.6), WZ), (7.0, 13.2, 6.0), 0.6))
        add.append(cyl_ab((x + 2.0, s * 16.5, WZ + 2.4), (x + 3.2, s * 18.0, 21.9), 0.8, 24))      # damper
        add.append(d_peg((x, yo, WZ), (0, s, 0), PEG["d"], PEG["length"], PEG["flat_from_axis"]))
    return add


def wheel():
    """One wheel in its local frame: axis +z, inner face z = 0, outer face z = width. D-flat socket flat toward +y."""
    r, w, rc = W["radius"], W["width"], W["core_radius"]
    core = M.batch_hull([M.cylinder(w - 1.8, rc, rc, 96).translate((0, 0, 0.9)), M.cylinder(w, rc - 0.9, rc - 0.9, 96)])
    lugs = []
    n = W["lugs"]
    for i in range(n):
        for half, (z0, z1) in enumerate(((0.35, 0.35 + W["lug_axial"]), (w - 0.35 - W["lug_axial"], w - 0.35))):
            th = 2 * math.pi * (i + 0.5 * half) / n
            blk = chbox((0, 0, 0), (W["lug_height"] + 0.6, W["lug_tangential"], z1 - z0), 0.3)
            R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
            lugs.append(place(blk, R, (math.cos(th) * (rc + (W["lug_height"] - 0.6) / 2), math.sin(th) * (rc + (W["lug_height"] - 0.6) / 2), (z0 + z1) / 2)))
    m = union([core] + lugs)
    d0, d1 = W["dish_r"]
    dd = W["dish_depth"]
    inner = M.cylinder(dd + 0.1, d1, d1, 96).translate((0, 0, -0.1)) - M.cylinder(dd + 0.3, d0, d0, 64).translate((0, 0, -0.2))
    outer = M.cylinder(dd + 0.1, d1, d1, 96).translate((0, 0, w - dd)) - M.cylinder(dd + 0.3, d0 - 0.4, d0 - 0.4, 64).translate((0, 0, w - dd - 0.1))
    m = m - inner - outer
    # lug nuts in the outer dish floor and a raised hub cap with an engraved chevron
    nuts = [M.cylinder(0.6, 0.5, 0.5, 16).translate((5.3 * math.cos(k * math.pi / 3), 5.3 * math.sin(k * math.pi / 3), w - dd - 0.1)) for k in range(6)]
    cap = M.cylinder(0.5, d0 - 0.4, d0 - 0.9, 64).translate((0, 0, w - 0.05))
    m = union([m, cap] + nuts)
    # one chevron outline pointing along local +y (the socket flat), 1.0 mm stroke, 0.5 mm deep (R8: two crossed bars left
    # a 0.028 mm sliver at the apex)
    chev = mf.CrossSection([[(-1.0, -0.9), (0.0, 0.1), (1.0, -0.9), (1.5, -0.4), (0.0, 1.1), (-1.5, -0.4)]]).extrude(1.0).translate((0, 0, w - 0.05))
    m = m - chev
    sock = d_cutter((0, 0, -0.5), (0, 0, 1), PEG["socket_d"], PEG["socket_depth"] + 0.5, PEG["socket_flat"], key=(0, 1, 0))
    return m - sock


def wheel_placement(x, s):
    """local z -> +-y (outward), local y -> +z (so the socket flat faces up, matching the stub), origin at the inner face."""
    if s > 0:
        R = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
    else:
        R = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)
    A = np.eye(4)
    A[:3, :3] = R
    A[:3, 3] = (x, s * WY_IN, WZ)
    return A


# ------------------------------------------------------------------------------------------------ M4 Tally RWS
def rws():
    """Tally RWS on the shared ring turntable; local frame: turntable underside at z = 0, weapon pointing +x."""
    tt = TR.turntable()
    h = TR.RING["turntable_h"]
    parts = [tt]
    parts.append(chbox((-1.5, 0, h + 2.0), (11.0, 10.0, 4.4), 0.8))                    # armoured pedestal
    parts.append(chbox((2.5, -0.6, h + 5.6), (9.0, 6.4, 3.6), 0.6))                     # weapon cradle / housing
    zb, yb = h + 5.8, -1.2
    parts.append(chcyl_ab((7.0, yb, zb), (12.5, yb, zb), 1.6, 0.3, 40))                 # barrel shroud
    parts.append(cyl_ab((12.0, yb, zb), (22.6, yb, zb), 1.0, 32))                       # heavy repeater barrel (2.0 mm)
    parts.append(chcyl_ab((22.4, yb, zb), (24.2, yb, zb), 1.35, 0.2, 32))               # muzzle brake
    parts.append(chbox((3.5, -5.0, h + 4.6), (6.0, 2.8, 2.8), 0.35))                    # 40 mm grenade launcher body
    parts.append(chcyl_ab((6.0, -5.0, h + 4.6), (10.8, -5.0, h + 4.6), 1.3, 0.2, 32))   # launcher tube
    parts.append(chbox((1.0, 5.2, h + 7.0), (4.6, 3.4, 3.4), 0.5))                      # sensor head
    parts.append(chbox((1.0, 3.0, h + 5.8), (3.0, 2.2, 2.6), 0.3))                      # sensor bracket (fuses head to housing)
    parts.append(chbox((-3.6, -4.2, h + 5.4), (4.0, 2.6, 3.0), 0.35))                   # ammunition box (on the pedestal)
    parts.append(cyl_ab((-5.5, 3.5, h + 4.0), (-5.5, 3.5, h + 10.5), 0.75, 24))         # antenna stub (1.5 mm, R5 Holmes)
    parts.append(M.sphere(0.8, 24).translate((-5.5, 3.5, h + 10.6)))
    m = union(parts)
    cut = [TR.turntable_pocket(),
           cyl_ab((4.6, 0, -0.5), (4.6, 0, 0.4), 0.5, 20),                             # polarity dot beside the pocket (R5 Holmes)
           cyl_ab((3.5, 5.2, h + 7.0), (2.9, 5.2, h + 7.0), 0.9, 24),                   # sensor lens recess (0.6 deep)
           cyl_ab((11.4, -5.0, h + 4.6), (10.3, -5.0, h + 4.6), 0.75, 24)]              # launcher bore (0.5 deep)
    return m - union(cut)


def rws_placement():
    c = S["ring"]["centre"]
    A = np.eye(4)
    A[:3, 3] = (c[0], c[1], RZ + 0.02)               # turntable sits on the seat floor (= roof plane)
    return A


# ------------------------------------------------------------------------------------------------ M5 the BREAK: open the box
RP = S["ramp"]
HT = S["hatches"]


def ramp_outline():
    a, b, zc, zt = RP["half_w_bottom"], RP["half_w"], RP["chamfer_top_z"], RP["top_z"]
    # plate bottom 0.3 mm below the hinge axis: at exactly the axis height the pins' polygon vertices lay on the plate's
    # bottom plane and welded into 12 non-manifold edges (measured M5)
    z0, zn = RP["hinge_z"] - 0.3, RP["narrow_top_z"]  # narrow (|y| <= 12.5) up to zn so the plate clears the hinge cheeks
    return [(-a, z0), (a, z0), (a, zn), (b, zc), (b, zt - 1.0), (b - 1.0, zt), (-(b - 1.0), zt), (-b, zt - 1.0), (-b, zc), (-a, zn)]


def aperture_half(z):
    """Half-width of the stern door polygon (spec ramp.aperture, symmetric) at height z."""
    pts = sorted([(zz, yy) for yy, zz in RP["aperture"] if yy > 0])
    return float(np.interp(z, [p[0] for p in pts], [p[1] for p in pts]))


def open_box(outer):
    add, cut = [], []
    # door aperture through the stern wall, sill flush with the bay floor
    # lower door: through the stern wall only (R8: running 0.6 mm on into the cavity nicked the V belly at the sill
    # corners, 0.048 mm). Upper door: on past the line where the stern bevel's inner face meets the roof underside
    # (x -70.48), otherwise the lintel keeps a 0.12-0.26 mm wedge of bevel (measured after the R8 fix, 37 mm2).
    door = prism_x(RP["aperture"], X0 - 1.5, X0 + T + 0.05)
    door_hi = prism_x(RP["aperture"], X0 - 1.5, X0 + T + 1.0).trim_by_plane((0, 0, 1), 30.0)
    cut.append(door + door_hi)
    # hinge cheeks with open-top U slots for the ramp pins
    xh, zh = RP["hinge_x"], RP["hinge_z"]
    y0, y1 = RP["cheek_y"]
    for s in (1, -1):
        add.append(chbox((X0 - 1.3 + 0.5, s * (y0 + y1) / 2, zh + 0.85), (3.6 + 1.0, y1 - y0, 5.7), 0.3))
        sl = RP["pin_r"] + RP["slot_clear"]
        cut.append(cyl_ab((xh, s * (y0 - 0.5), zh), (xh, s * (y1 + 0.5), zh), sl, 32))
        cut.append(box((xh, s * (y0 + y1) / 2, zh + 3.0), (2 * sl, y1 - y0 + 1.0, 6.0)))
        zt, fl_ = zh + 0.85 + 5.7 / 2, RP["slot_flare"]                    # cheek top; 0.3 mm flare so the pins drop in (R6)
        cut.append(hullp([(xh + sx * (sl + fl_ * k), s * yy, zt + 0.5 * k - fl_ * (1 - k)) for sx in (1, -1) for k in (0, 1)
                          for yy in (y0 - 0.5, y1 + 0.5)]))
    # bay floor and benches (visible through the open ramp), clipped to the hull solid
    f0, f1 = RP["floor_z"]
    fl = RP["floor_len"]            # floor only where it is seen through the door (resin pass, M5)
    add.append(box((X0 + T + fl / 2 - 0.5, 0, (f0 + f1) / 2), (fl + 1.0, 40, f1 - f0)) ^ outer)
    bn = S["benches"]
    z0, z1 = bn["seat_z"]
    for s in (1, -1):
        yi = bn["seat_inner_y"]
        add.append(box(((bn["x"][0] + bn["x"][1]) / 2, s * (yi + 4.5), (z0 + z1) / 2), (bn["x"][1] - bn["x"][0], 9.0, z1 - z0)) ^ outer)
        pitch = (bn["x"][1] - bn["x"][0]) / bn["seats_per_side"]
        for k in range(bn["seats_per_side"]):
            xc = bn["x"][0] + pitch * (k + 0.5)
            yw = 27.6 - T                                                                             # inner side wall
            add.append(box((xc, s * (yw - bn["pad_proud"] / 2 + 0.3), z1 + 3.4), (pitch - 3.0, bn["pad_proud"] + 0.6, 5.6)) ^ outer)   # back pads
    # roof hatch openings (through the roof) with raised coamings
    for cx, cy in HT["centres"]:
        (ox, oy), wd = HT["opening"], HT["coaming_w"]
        add.append(rrect(cx, cy, ox + 2 * wd, oy + 2 * wd, HT["corner_r"] + wd, RZ - 0.3, RZ + HT["coaming_h"])
                   - rrect(cx, cy, ox, oy, HT["corner_r"], RZ - 1, RZ + 2))
        cut.append(rrect(cx, cy, ox, oy, HT["corner_r"], RZ - T - 1.0, RZ + 2))
    return add, cut


def ramp():
    """Stern ramp in the closed position (world frame): plate, outer ribs, inner tread bars, hinge bar and pins."""
    xin = X0 - RP["gap"]
    xout = xin - RP["thickness"]
    plate = prism_x(ramp_outline(), xout, xin)
    zh, xh = RP["hinge_z"], RP["hinge_x"]
    a = RP["half_w_bottom"]
    parts = [plate]
    for z in (21.0, 27.0, 33.0):                                                    # outer stiffening ribs
        parts.append(chbox((xout - 0.35, 0, z), (1.0, 2 * RP["half_w"] - 3.0, 1.2), 0.3))
    for z in np.linspace(zh + 4.0, RP["top_z"] - 3.0, 7):                           # inner tread bars (walking face)
        # inner bars sit inside the door aperture when closed (they face the hull): width = aperture width - 1.0 mm
        parts.append(box((xin + 0.25, 0, z), (0.9, 2 * aperture_half(z) - 1.0, 0.8)))
    parts.append(chbox((xout - 0.55, -7.5, 30.0), (1.2, 3.8, 2.4), 0.3))            # vision block housing (overlaps the face 0.05; 3.8 x 2.4: M6)
    # hinge bar stops 0.2 mm inside the plate's side faces (coplanar end caps welded into non-manifold edges, M5)
    parts.append(cyl_ab((xh, -(a - 0.2), zh), (xh, a - 0.2, zh), RP["bar_r"], 32))
    for s in (1, -1):
        parts.append(chcyl_ab((xh, s * (a - 0.3), zh), (xh, s * (a + RP["pin_len"]), zh), RP["pin_r"], 0.15, 24))
    m = union(parts)
    cut = [prism_x([(1.5, 18.0), (10.5, 18.0), (10.5, 33.0), (1.5, 33.0)], xout - 1.0, xout + 0.5)
           - prism_x([(2.3, 18.8), (9.7, 18.8), (9.7, 32.2), (2.3, 32.2)], xout - 1.5, xout + 1.0),   # personnel-door outline (0.8 mm)
           box((xout - 1.1, -6.8, 30.0), (0.8, 0.7, 0.6)), box((xout - 1.1, -8.2, 30.0), (0.8, 0.7, 0.6))]   # 0.7 mm walls (M6)
    # off-axis engraved Vigil chevron (R3, Shklovsky): two 0.8 mm bars, 0.6 mm deep, pointing up, left of the door
    for k in (1, -1):
        a_ = math.radians(35 * k)
        Rr = np.array([[1, 0, 0], [0, math.cos(a_), -math.sin(a_)], [0, math.sin(a_), math.cos(a_)]])
        cut.append(place(box((0, 0, 0), (1.0, 0.8, 3.2)), Rr, (xout, -7.5 + k * 1.0, 24.0)))       # 0.5 mm deep (M6)
    return m - union(cut)


def ramp_open_placement():
    """Rotate about the hinge axis (parallel to y through (hinge_x, hinge_z)) so the lip rests on the table."""
    phi = math.radians(RP["open_deg"])
    R = np.array([[math.cos(phi), 0, math.sin(phi)], [0, 1, 0], [-math.sin(phi), 0, math.cos(phi)]])
    p = np.array([RP["hinge_x"], 0, RP["hinge_z"]])
    A = np.eye(4)
    A[:3, :3] = R
    A[:3, 3] = p - R @ p
    return A


def hatch():
    """Roof hatch, local frame: lid underside z = 0 (rests on the coaming top), plug ring below, hinge on +x."""
    (Lx, Ly), t, (ox, oy), c = HT["lid"], HT["lid_t"], HT["opening"], HT["plug_clear"]
    lid = M.batch_hull([rrect(0, 0, Lx, Ly, 2.6, 0, t - 0.3), rrect(0, 0, Lx - 0.6, Ly - 0.6, 2.3, 0, t)])
    pw = HT["plug_wall"]
    plug = (rrect(0, 0, ox - 2 * c, oy - 2 * c, HT["corner_r"] - c, -HT["plug_h"], 0.05)
            - rrect(0, 0, ox - 2 * c - 2 * pw, oy - 2 * c - 2 * pw, 1.0, -HT["plug_h"] - 1, 0.0))
    panel = M.batch_hull([rrect(0, 0, Lx - 4.0, Ly - 4.0, 1.6, t - 0.05, t + 0.15), rrect(0, 0, Lx - 4.6, Ly - 4.6, 1.3, t - 0.05, t + 0.45)])
    parts = [lid, plug, panel]
    for y in (-Ly / 2 + 3.5, Ly / 2 - 3.5):
        parts.append(chcyl_ab((Lx / 2 - 0.6, y - 2.0, t + 0.2), (Lx / 2 - 0.6, y + 2.0, t + 0.2), 0.8, 0.15, 24))   # hinge knuckles
    parts.append(chbox((-Lx / 2 + 3.0, 0, t + 0.7), (1.2, 6.0, 0.9), 0.3))                                         # locking bar
    parts.append(chbox((-4.0, -Ly / 2 + 3.4, t + 0.9), (3.0, 1.8, 1.4), 0.35))                                      # periscope
    parts.append(chbox((3.0, 0, t + 0.6), (8.0, 1.0, 0.7), 0.25))                                                  # stiffener rib
    return union(parts)


def hatch_placement(cx, cy):
    A = np.eye(4)
    A[:3, 3] = (cx, cy, RZ + HT["coaming_h"])
    return A


def hatch_open_placement(cx, cy):
    """Lid swung up 105 deg about its hinge line (+x edge of the lid, toward the bow) for the deployed render."""
    L = HT["lid"][0]
    phi = math.radians(105)      # +105 about y lifts the free (-x) edge up (measured: -105 swung the lid into the bay)
    R = np.array([[math.cos(phi), 0, math.sin(phi)], [0, 1, 0], [-math.sin(phi), 0, math.cos(phi)]])
    hinge = np.array([L / 2 - 0.6, 0, 0.2])
    A = np.eye(4)
    A[:3, :3] = R
    A[:3, 3] = np.array([cx, cy, RZ + HT["coaming_h"]]) + hinge - R @ hinge
    return A


def split_pin():
    """Alignment pin, lying on its D-flat (print flat on the plate): length along x, flat face at z = 0."""
    sp = S["split_pins"]
    L, r, tip = sp["length"], sp["d"] / 2, 0.3
    body = M.batch_hull([cyl_ab((-L / 2 + tip, 0, 0), (L / 2 - tip, 0, 0), r, 48), cyl_ab((-L / 2, 0, 0), (L / 2, 0, 0), r - tip, 48)])
    # both ends chamfered (R1, Holmes): either end is the right end; the D-flat (at 0.3 d from the axis) fixes roll
    return body.trim_by_plane((0, 0, 1), -0.3 * sp["d"]).translate((0, 0, 0.3 * sp["d"]))


# ------------------------------------------------------------------------------------------------ fit gauges (F5)
def deck_fit(rear_tm):
    """R9 (Criado Perez): based figures on the M7 deck. Section the rear hull 0.3 mm above the deck top, take the free
    region round (-40, 0), and pack 25/32/40 mm round bases on it (hex-row greedy, 0.5 mm gap). Upright clearance =
    bay clear height minus base height (3 / 4 mm) against figure heights (crown) of common ranges."""
    from shapely.geometry import Point, Polygon, box as sbox
    from shapely.ops import unary_union
    z = RP["floor_z"][1] + 0.3
    sec = rear_tm.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
    planar, T4 = sec.to_2D()
    mat = unary_union([pg.buffer(0) for pg in planar.polygons_full])
    from shapely import affinity
    A = T4                                 # 2D -> 3D transform of the section
    mat = affinity.affine_transform(mat, [A[0, 0], A[0, 1], A[1, 0], A[1, 1], A[0, 3], A[1, 3]])
    free = sbox(X0, -30, XS - 0.01, 30).difference(mat)
    geoms = getattr(free, "geoms", [free])
    deck = [g for g in geoms if g.contains(Point(-40, 0))][0]
    widths = []
    for x in np.arange(-70, -12, 2.0):
        cut = deck.intersection(sbox(x - 0.01, -30, x + 0.01, 30))
        widths.append(round(float(cut.bounds[3] - cut.bounds[1]), 2) if not cut.is_empty else 0.0)
    out = {"section_z_mm": z, "deck_area_mm2": round(float(deck.area), 1), "deck_bounds_mm": [round(float(v), 2) for v in deck.bounds],
           "min_width_mm": min(w for w in widths if w > 0), "max_width_mm": max(widths), "bases": {}}
    bay = RZ - T - RP["floor_z"][1]
    for d in (25, 32, 40):
        r_ = d / 2 + 0.25
        placed = []
        # greedy scan: x along the deck, y across, 0.5 mm steps, keep a circle if it lies inside and clears the others
        for x in np.arange(deck.bounds[0] + r_, deck.bounds[2] - r_ + 1e-6, 0.5):
            for y in np.arange(deck.bounds[1] + r_, deck.bounds[3] - r_ + 1e-6, 0.5):
                c = Point(x, y).buffer(r_, 32)
                if deck.contains(c) and all(math.hypot(x - px, y - py) >= 2 * r_ for px, py in placed):
                    placed.append((x, y))
        out["bases"][f"{d} mm"] = {"count_on_deck": len(placed), "centres": [[round(a, 1), round(b, 1)] for a, b in placed]}
    out["upright"] = []
    for name, crown in (("Vigil 30 mm heroic (crown ~32.4 measured rifleman)", 32.4), ("28 mm heroic range (crown ~30)", 30.0),
                        ("32 mm range (crown ~35)", 35.0), ("1:56 true-scale 1.8 m human (32.1 mm)", 32.1)):
        for bh in (3.0, 4.0):
            out["upright"].append({"figure": name, "base_h_mm": bh, "needs_mm": round(crown + bh, 1), "bay_clear_mm": round(bay, 2),
                                   "door_clear_mm": round(max(z for y, z in RP["aperture"]) - min(z for y, z in RP["aperture"]), 2),
                                   "fits_upright": crown + bh <= bay})
    out["method"] = ("trimesh section of hull-rear at the stated z; shapely free region containing (-40, 0); widths sampled every 2 mm "
                     "in x; bases packed greedily on a 0.5 mm grid with 0.25 mm clearance a side; crowns: measured Vigil rifleman "
                     "(reports of vigil-rifleman) and nominal ranges (owner-checkable).")
    return out


def fit_report():
    """Vigilant envelopes (measured from the figure packages' viewer meshes) against the openings in the spec."""
    from shapely.geometry import MultiPoint, Polygon
    out = {}
    for pid in S["fit_figures"]:
        f = ROOT / pid / "viewer" / f"{pid}.parts.json"
        if not f.exists():
            continue
        P = json.loads(f.read_text())
        V = np.vstack([np.array(p["vertices"]) for p in P if "base" not in p["group"]])
        r = MultiPoint(V[:, :2]).convex_hull.minimum_rotated_rectangle
        xy = np.array(r.exterior.coords)
        e = sorted([float(np.linalg.norm(xy[1] - xy[0])), float(np.linalg.norm(xy[2] - xy[1]))])
        torso = V[V[:, 2] > V[:, 2].min() + 0.55 * (V[:, 2].max() - V[:, 2].min())]
        rt = MultiPoint(torso[:, :2]).convex_hull.minimum_rotated_rectangle
        xt = np.array(rt.exterior.coords)
        et = sorted([float(np.linalg.norm(xt[1] - xt[0])), float(np.linalg.norm(xt[2] - xt[1]))])
        out[pid] = {"height_mm": round(float(V[:, 2].max() - V[:, 2].min()), 2), "plan_min_rect_mm": [round(v, 2) for v in e],
                    "upper_body_min_rect_mm": [round(v, 2) for v in et]}
    door = Polygon(RP["aperture"])
    dminx, dminy, dmaxx, dmaxy = door.bounds
    # largest axis-aligned rectangle test: does a w x h rectangle fit inside the door polygon (any position)?
    def fits(poly, w, h):
        for y0 in np.arange(dminy, dmaxy - h + 1e-6, 0.1):
            for x0 in np.arange(dminx, dmaxx - w + 1e-6, 0.1):
                if poly.contains(Polygon([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)])):
                    return True
        return False
    rows = []
    clr = 0.5     # msla_resin min_clearance_mm, per side
    door_h = dmaxy - dminy
    for pid, f in out.items():
        ch = round(S["fit_crouch_fraction"] * f["height_mm"], 2)
        rows.append({"figure": pid, "opening": f"stern door (crouched to {int(S['fit_crouch_fraction'] * 100)} % of height, Dreyfuss)",
                     "needs_height_mm": round(ch + clr, 2), "door_clear_height_mm": round(door_h, 2),
                     "fits": ch + clr <= door_h and f["plan_min_rect_mm"][0] + 2 * clr <= 2 * max(y for y, z in RP["aperture"])})
        a, b = f["plan_min_rect_mm"]
        rows.append({"figure": pid, "opening": "stern door (lying, lengthwise)", "needs_mm": [round(b + 2 * clr, 2), round(a + 2 * clr, 2)],
                     "fits": bool(fits(door, b + 2 * clr, a + 2 * clr) or fits(door, a + 2 * clr, b + 2 * clr))})
        rows.append({"figure": pid, "opening": "stern door (standing)", "needs_height_mm": f["height_mm"], "door_clear_height_mm": round(dmaxy - dminy, 2),
                     "fits": f["height_mm"] + clr <= dmaxy - dminy})
        ta, tb = f["upper_body_min_rect_mm"]
        oy, ox = sorted(HT["opening"])
        rows.append({"figure": pid, "opening": "roof hatch (upper body standing in the hatch)", "needs_mm": [round(ta + 2 * clr, 2), round(tb + 2 * clr, 2)],
                     "hatch_mm": HT["opening"], "fits": ta + 2 * clr <= oy and tb + 2 * clr <= ox})
        rows.append({"figure": pid, "opening": "roof hatch (whole figure passing through, lengthwise)", "needs_mm": [round(a + 2 * clr, 2), round(b + 2 * clr, 2)],
                     "hatch_mm": HT["opening"], "fits": a + 2 * clr <= oy and b + 2 * clr <= ox})
    bn = S["benches"]
    aisle = 2 * bn["seat_inner_y"]
    bay_h = RZ - T - RP["floor_z"][1]
    mh = [max(f["plan_min_rect_mm"][1] for f in out.values()) + 2 * clr, max(f["plan_min_rect_mm"][0] for f in out.values()) + 2 * clr]
    return {"figures": out, "openings": rows, "min_hatch_opening_mm": [round(v, 2) for v in mh], "hatch_opening_mm": HT["opening"],
            "aisle_between_benches_mm": round(aisle, 2), "bay_clear_height_mm": round(bay_h, 2),
            "seat_pitch_mm": round((bn["x"][1] - bn["x"][0]) / bn["seats_per_side"], 2),
            "method": "Figure envelopes from the figure packages' assembled viewer meshes (base excluded): minimum-area rectangle of the plan "
                      "projection (shapely); upper body = vertices above 55 % of the height. Openings from the spec. Clearance 0.5 mm per side "
                      "(msla_resin min_clearance). Door test slides the rectangle over the door polygon in 0.1 mm steps."}


# ------------------------------------------------------------------------------------------------ package writer
STATS = {}
COL = {"hull": "#7d8c96", "hull2": "#66747e", "wheel": "#3d4247", "rws": "#5d6a73", "ramp": "#6f7d87", "hatch": "#8a98a1",
       "pin": "#c9a246", "lens": "#59cfe0", "accent": "#c9a246", "figure": "#b9b2a4", "base": "#4b5057"}


def overlap(a, b):
    lo, hi = np.maximum(a.bounds[0], b.bounds[0]), np.minimum(a.bounds[1], b.bounds[1])
    if np.any(hi <= lo):
        return 0.0
    ma = M(mf.Mesh(vert_properties=np.asarray(a.vertices, np.float32), tri_verts=np.asarray(a.faces, np.uint32)))
    mb = M(mf.Mesh(vert_properties=np.asarray(b.vertices, np.float32), tri_verts=np.asarray(b.faces, np.uint32)))
    return float((ma ^ mb).volume())


def mesh_quality(tm):
    """LOCAL (trimesh) triangle-quality summary requested by the Mesh Quality critic (no MCP tool reports it)."""
    ang = np.degrees(tm.face_angles.min(axis=1))
    e = tm.vertices[tm.faces]
    L = np.stack([np.linalg.norm(e[:, 1] - e[:, 0], axis=1), np.linalg.norm(e[:, 2] - e[:, 1], axis=1), np.linalg.norm(e[:, 0] - e[:, 2], axis=1)], 1)
    alt = 2 * tm.area_faces / np.maximum(L.max(axis=1), 1e-12)
    asp = L.max(axis=1) / np.maximum(alt, 1e-12)
    return {"min_angle_deg": round(float(ang.min()), 3), "p05_min_angle_deg": round(float(np.percentile(ang, 5)), 2),
            "median_min_angle_deg": round(float(np.median(ang)), 2), "max_aspect": round(float(asp.max()), 1),
            "shortest_edge_mm": round(float(L.min()), 5), "faces_below_1deg": int((ang < 1).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, default=6)
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--pre-m7", action="store_true", help="bay floor as before M7 (25 mm stub), written to build/m7-before/")
    a = ap.parse_args()
    st = a.stage
    up = PKG / "build" / "upright"
    if a.pre_m7:
        RP["floor_len"] = RP["floor_len_pre_m7"]
        up = PKG / "build" / "m7-before"
        a.no_images = True
    up.mkdir(parents=True, exist_ok=True)
    for f in up.glob("*.stl"):
        f.unlink()
    front, rear, outer = build_hull(st)
    parts = {}          # stl name -> (trimesh, label, color)
    inst = []           # (name, stl, placement, group, color, note, explode)
    I4 = np.eye(4)
    parts["hull-front"] = (to_tm(front, "hull-front"), "Hull, front half", COL["hull"])
    parts["hull-rear"] = (to_tm(rear, "hull-rear"), "Hull, rear half", COL["hull"])
    parts["split-pin"] = (to_tm(split_pin(), "split-pin"), "Split pin (D-flat, 3 mm)", COL["pin"])
    inst += [("Hull front (glacis, cupola, ring seat)", "hull-front", I4, "hull", COL["hull"], "Hollow 2 mm shell, split at x = -11.5 under the RWS ring.", (12, 0, 0)),
             ("Hull rear (troop bay)", "hull-rear", I4, "hull", COL["hull"], "Hollow 2 mm shell with the bay floor, benches, hatch openings and stern door.", (-12, 0, 0))]
    for k, (yc, zc) in enumerate(S["split_pins"]["bosses_yz"]):
        A = np.eye(4)
        A[:3, :3] = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1.0]]) @ np.array([[1, 0, 0], [0, -1, 0], [0, 0, 1.0]])   # flat up
        A[:3, 3] = (XS, yc, zc + 0.3 * S["split_pins"]["d"])     # pin axis on the socket axis, flat up like the socket
        inst.append((f"Split pin {k + 1}", "split-pin", A, "pins", COL["pin"], "D-flat alignment pin across the hull split.", (0, 0, 0)))
    if st >= 3:
        parts["wheel"] = (to_tm(wheel(), "wheel"), "Wheel (x8)", COL["wheel"])
        for x, s in axle_stations():
            inst.append((f"Wheel {'L' if s > 0 else 'R'}{x:+.0f}", "wheel", wheel_placement(x, s), "wheels", COL["wheel"],
                         "Identical wheel; 3.2 mm D-flat socket on the axle stub.", (0, s * 10, 0)))
    if st >= 4:
        parts["rws"] = (to_tm(rws(), "rws"), "Tally RWS on 30 mm ring turntable", COL["rws"])
        inst.append(("Tally RWS", "rws", rws_placement(), "rws", COL["rws"], "Heavy repeater + 40 mm grenade launcher on the shared 30 mm magnetised ring.", (0, 0, 14)))
    if st >= 5:
        parts["ramp"] = (to_tm(ramp(), "ramp"), "Stern ramp", COL["ramp"])
        parts["hatch"] = (to_tm(hatch(), "hatch"), "Roof hatch (x4)", COL["hatch"])
        inst.append(("Stern ramp (closed)", "ramp", I4, "ramp", COL["ramp"], "Drop-in hinge pins; glue closed or open.", (-10, 0, 0)))
        for k, (cx, cy) in enumerate(HT["centres"]):
            inst.append((f"Roof hatch {k + 1}", "hatch", hatch_placement(cx, cy), "hatches", COL["hatch"], "Plugs into its coaming; glue open or closed.", (0, 0, 8)))
    rows = {}
    for name, (tm, label, col) in parts.items():
        tm.export(up / f"{name}.stl")
        rows[name] = {"label": label, "volume_mm3": round(float(tm.volume), 2), "bbox_mm": [round(float(v), 2) for v in tm.extents],
                      "triangles": int(len(tm.faces)), "bodies": len(tm.split(only_watertight=False)), "watertight": bool(tm.is_watertight),
                      "mesh_quality": mesh_quality(tm),
                      "instances": sum(1 for i in inst if i[1] == name)}
    asm = []
    for name, stl, A, group, col, note, ex in inst:
        m = parts[stl][0].copy()
        m.apply_transform(A)
        asm.append((name, stl, m, group, col, note, ex))
    interference = []
    for i in range(len(asm)):
        for j in range(i + 1, len(asm)):
            if asm[i][1] == "split-pin" or asm[j][1] == "split-pin":
                continue  # pins sit in sockets by design (checked by socket clearance instead)
            v = overlap(asm[i][2], asm[j][2])
            if v > 0.01:
                interference.append({"a": asm[i][0], "b": asm[j][0], "overlap_mm3": round(v, 3)})
    open_interf = []
    if st >= 5:
        ro = parts["ramp"][0].copy()
        ro.apply_transform(ramp_open_placement())
        for nm in ("Hull rear (troop bay)",):
            hm = [x for x in asm if x[0] == nm][0][2]
            open_interf.append({"a": "Stern ramp (open)", "b": nm, "overlap_mm3": round(overlap(ro, hm), 3)})
        ro_lo = ro.bounds
        open_interf.append({"ramp_open_lowest_z_mm": round(float(ro_lo[0][2]), 3), "ramp_open_rear_x_mm": round(float(ro_lo[0][0]), 3)})
    allv = np.vstack([x[2].vertices for x in asm])
    ext = allv.max(axis=0) - allv.min(axis=0)
    total_ml = sum(r["volume_mm3"] * r["instances"] for r in rows.values()) / 1000
    rep = {"id": S["id"], "stage": st, "generator": "source/build.py (manifold3d CSG; tools/turret_ring.py)",
           "assembled_bbox_mm": [round(float(v), 2) for v in ext], "assembled_min_mm": [round(float(v), 2) for v in allv.min(axis=0)],
           "assembled_max_mm": [round(float(v), 2) for v in allv.max(axis=0)],
           "parts": rows, "kit_resin_ml_solid_parts": round(total_ml, 2), "interference_closed": interference, "ramp_open": open_interf,
           "ring": TR.describe(), "fit": fit_report() if st >= 5 else None, "deck_fit": deck_fit(parts["hull-rear"][0]) if st >= 5 else None,
           "hull_stats": STATS,
           "step": {"file": None, "status": "SKIPPED: FreeCAD is not installed in this environment (sdfkit.write_step needs a FreeCAD Python)."}}
    if a.pre_m7:
        (up / "build.json").write_text(json.dumps(rep, indent=1))
        print(json.dumps({"pre_m7": True, "kit_ml": rep["kit_resin_ml_solid_parts"], "hull-rear": rows["hull-rear"]["volume_mm3"]}))
        return
    (PKG / "reports").mkdir(exist_ok=True)
    (PKG / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    (PKG / "viewer").mkdir(exist_ok=True)
    viewer = [{"name": n, "group": g, "color": c, "note": nt, "explode": list(ex), "printStl": f"print/stl/{stl}.stl",
               "vertices": np.round(m.vertices, 3).tolist(), "triangles": m.faces.tolist()} for n, stl, m, g, c, nt, ex in asm]
    (PKG / "viewer" / f"{S['id']}.parts.json").write_text(json.dumps(viewer, separators=(",", ":")))
    print(json.dumps({"stage": st, "parts": {k: (v["volume_mm3"], v["bbox_mm"], v["triangles"], v["instances"]) for k, v in rows.items()},
                      "kit_ml": rep["kit_resin_ml_solid_parts"], "assembled_bbox_mm": rep["assembled_bbox_mm"], "interference": interference,
                      "ramp_open": open_interf}, indent=1))
    if not a.no_images:
        import images
        images.render_all(PKG, S, asm, parts, st, ramp_open_placement() if st >= 5 else None,
                          [hatch_open_placement(cx, cy) for cx, cy in HT["centres"]] if st >= 5 else None)


if __name__ == "__main__":
    main()
