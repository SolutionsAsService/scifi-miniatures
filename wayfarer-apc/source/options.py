#!/usr/bin/env python3
"""Wayfarer phase 2: swappable option parts for the AW-8A kit (AW-8A itself is untouched: build.py owns it).

Run with the sculpt venv AFTER source/build.py (it reads nothing from build.py's outputs, it rebuilds the hull in
memory for the fit tests):   ~/projects/venvs/scifi-sculpt/bin/python source/options.py [--no-images] [--only a,b]
Frame: the hull frame of build.py (mm at 1:56, x = front, y = left, z up, ground z = 0).
Outputs: build/options/*.stl (model pose), reports/options.json (volumes, bboxes, interference, sweeps, interface),
viewer/wayfarer-apc.options.json, images/wayfarer-apc-*.png (variant sheets).

Every option plugs into an interface the AW-8A kit already has, so no AW-8A part changes:
  30 mm ring (tools/turret_ring.py) .... AW-8C Wren turret
  hatch opening 24.5 x 16.8 r2 (plug) .. AW-8M Sling mortar module (front pair), open hatch, commander, roof adapter,
                                          spare-wheel mount
  bow tow eyes (r 1.1, x 71.5-74.6) .... obstacle blade, mine roller (slip sockets 0.15 mm per side)
  stern door / ramp hinge slots ........ detailed ramp (same hinge pins), bay insert (drops on the M7 deck)
  flat glue faces ...................... stowage, antennae (stern lockers), headlight cages (bow face), damage plates
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import build as B  # noqa: E402  (AW-8A generator: CSG helpers, spec, hull)
from build import (M, mf, S, RZ, T, HT, RP, W, TR, X0, X1, XS, box, chbox, cyl_ab, chcyl_ab, hullp, rrect, prism_x,  # noqa: E402
                   union, place, frame_to)

PKG = B.PKG
OUT = PKG / "build" / "options"
OPT = S.get("options", {})
STATS = {}


def prism_y(poly_xz, y0, y1):
    """Extrude an (x, z) polygon along +y from y0 to y1."""
    cs = mf.CrossSection([[(float(x), float(z)) for x, z in poly_xz]])
    m = cs.extrude(y1 - y0)                      # local (u, v, w) = (x, z, y)
    R = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
    return place(m, R, (0, y0, 0))


def Tm(x=0.0, y=0.0, z=0.0, R=None):
    A = np.eye(4)
    if R is not None:
        A[:3, :3] = R
    A[:3, 3] = (x, y, z)
    return A


def Rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def Ry(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def mx(m, A):
    return m.transform(np.asarray(A)[:3, :])


def tm_to_m(tm):
    return M(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))


# ------------------------------------------------------------------------------------------------ shared interfaces
CT = RZ + HT["coaming_h"]                     # coaming top (z of a closed lid's underside)


def hatch_plug(plate=True, plate_t=1.0):
    """The hatch's own plug ring (same numbers as build.hatch) plus, optionally, a lid-footprint plate on the coaming top.
    Local frame = hatch frame: z = 0 on the coaming top, opening long axis along x."""
    (Lx, Ly), (ox, oy), c, pw = HT["lid"], HT["opening"], HT["plug_clear"], HT["plug_wall"]
    plug = (rrect(0, 0, ox - 2 * c, oy - 2 * c, HT["corner_r"] - c, -HT["plug_h"], 0.05)
            - rrect(0, 0, ox - 2 * c - 2 * pw, oy - 2 * c - 2 * pw, 1.0, -HT["plug_h"] - 1, 0.0 if plate else 1.0))
    # (plate=False: the inner cut must run past the ring top, else a 0.05 mm membrane closes the hole: measured as a
    #  -53.8 mm3 void under the commander, the hatch's own z 0.0 cut is only safe because its lid covers it)
    if not plate:
        return plug
    deck = M.batch_hull([rrect(0, 0, Lx, Ly, 2.6, 0, plate_t - 0.3), rrect(0, 0, Lx - 0.6, Ly - 0.6, 2.3, 0, plate_t)])
    return plug + deck


def hatch_A(cx, cy):
    return Tm(cx, cy, CT)


def d_socket(a, axis, d, depth, key, clear=0.1, flat_frac=0.3):
    """D-flat socket cutter of the Vigil line standard (sdfkit.d_peg: flat at 0.3 d from the axis; socket = peg + clear
    per side), from a along axis; the flat faces 'key'."""
    a, key = np.asarray(a, float), np.asarray(key, float)
    c = cyl_ab(a, a + np.asarray(axis, float) / np.linalg.norm(axis) * depth, d / 2 + clear, 48)
    return c.trim_by_plane(tuple(-key), float(-(np.dot(key, a) + flat_frac * d + clear)))


# ------------------------------------------------------------------------------------------------ AW-8C Wren turret
def wren():
    """Low two-seat turret on the shared ring. Local frame: turntable underside z = 0, gun along +x.
    Clearance rule (measured on the AW-8A roof): nothing beyond r 18.0 below local z 3.3 (closed rear-hatch hinge
    knuckles reach r 18.4 at local z 2.8); the sweep test in fits() proves it at 24 headings."""
    tt = TR.turntable()
    h = TR.RING["turntable_h"]
    z0, z1 = h - 0.05, h + 5.6
    bot = [(17.6, 0), (11.0, 12.6), (-8.5, 14.6), (-15.6, 8.2)]
    top = [(13.6, 0), (8.0, 10.6), (-8.0, 12.0), (-13.4, 7.0)]
    pts = [(x, s * y, z0) for x, y in bot for s in (1, -1)] + [(x, s * y, z1) for x, y in top for s in (1, -1)]
    body = hullp(pts)
    parts = [tt, body]
    parts.append(chbox((-14.2, 0, h + 3.5), (5.6, 13.0, 4.0), 0.6))                     # bustle (ready-round magazine), bottom at local 3.3
    parts.append(chbox((14.6, -1.2, h + 3.5), (6.4, 7.2, 4.0), 0.5))                    # mantlet (r <= 18.9 at local z >= 3.3)
    zb, yb = h + 3.6, -1.2
    parts.append(chcyl_ab((17.0, yb, zb), (24.0, yb, zb), 1.5, 0.3, 40))                 # barrel jacket
    parts.append(cyl_ab((23.5, yb, zb), (45.5, yb, zb), 1.0, 32))                        # 25 mm barrel (2.0 mm: wire limit)
    parts.append(chcyl_ab((45.3, yb, zb), (47.6, yb, zb), 1.35, 0.25, 32))               # muzzle brake
    parts.append(chcyl_ab((16.0, 3.0, h + 3.0), (21.0, 3.0, h + 3.0), 0.65, 0.15, 24))  # coaxial repeater (1.3 mm)
    for s in (1, -1):                                                                    # two crew hatches
        parts.append(chcyl_ab((-3.0, s * 5.4, z1 - 0.3), (-3.0, s * 5.4, z1 + 0.6), 3.3, 0.25, 48))
        parts.append(chbox((-0.2, s * 5.4, z1 + 0.75), (1.2, 2.4, 0.8), 0.25))           # hinge block
    parts.append(chbox((3.0, 6.4, z1 + 1.1), (3.4, 3.0, 2.4), 0.4))                     # commander's panoramic sight
    parts.append(chbox((7.4, -6.6, z1 + 0.7), (3.0, 2.6, 1.6), 0.35))                   # gunner's sight
    # keel crest on the turret face (the hull crest's language carried up)
    parts.append(hullp([(17.3, 0.6, z0 + 0.3), (17.3, -0.6, z0 + 0.3), (13.4, 0.35, z1 + 0.5), (13.4, -0.35, z1 + 0.5),
                        (12.0, 0.5, z0 + 0.3), (12.0, -0.5, z0 + 0.3)]))
    for s in (1, -1):                                                                    # 3 smoke dischargers a side
        for k, x in enumerate((-4.5, -2.0, 0.5)):
            a = np.array([x, s * 12.2, h + 3.4])
            d = np.array([0.0, s * math.sin(math.radians(40)), math.cos(math.radians(40))])
            parts.append(chcyl_ab(a, a + d * 3.0, 0.85, 0.2, 24))
        parts.append(chbox((-2.0, s * 12.6, h + 2.6), (8.0, 1.8, 1.6), 0.3))            # discharger shelf
    m = union(parts)
    cut = [TR.turntable_pocket(), cyl_ab((4.6, 0, -0.5), (4.6, 0, 0.4), 0.5, 20),       # polarity dot (as the Tally RWS)
           cyl_ab((4.75, 6.4, z1 + 1.1), (4.0, 6.4, z1 + 1.1), 0.8, 24),                # sight lens recess
           cyl_ab((48.0, yb, zb), (46.8, yb, zb), 0.55, 20)]                            # muzzle bore (1.2 deep)
    for s in (1, -1):
        cut.append(box((-3.0, s * 5.4, z1 + 0.62), (4.2, 0.6, 0.5)))                     # hatch grip slot (0.6 x 0.5)
    return m - union(cut)


# ------------------------------------------------------------------------------------------------ AW-8M Sling mortar module
SL = {"cx": -31.35, "pivot_x": -33.0, "trunnion_dx": 2.0, "elev_deg": 55.0, "tube_r": 1.8, "tube_len": 25.0, "tube_y": 3.8}


def sling():
    """Twin 120 mm breech-loaded mortar module: one deck plate over the two forward hatch openings (both plugs), a
    traversing ring, trunnion cheeks and two tubes at 55 deg pointing aft; the roof doors stand open at the sides.
    World frame (it only fits the forward pair: cx = -31.35, cy = +-9.9)."""
    cx = SL["cx"]
    (Lx, Ly) = HT["lid"]
    span = 2 * 9.9 + Ly                                                                   # 37.8: both lids
    plate_t = 1.2
    parts = []
    deck = M.batch_hull([rrect(cx, 0, Lx, span, 2.6, CT, CT + plate_t - 0.3), rrect(cx, 0, Lx - 0.6, span - 0.6, 2.3, CT, CT + plate_t)])
    parts.append(deck)
    for cy in (9.9, -9.9):
        parts.append(mx(hatch_plug(plate=False), hatch_A(cx, cy)))
    zt = CT + plate_t
    px = SL["pivot_x"]
    parts.append(chcyl_ab((px, 0, zt - 0.2), (px, 0, zt + 1.0), 8.0, 0.3, 64))             # traversing ring
    tx, tz = px + SL["trunnion_dx"], zt + 1.0 + 4.4
    for s in (1, -1):                                                                     # trunnion cheeks
        parts.append(hullp([(px + 4.5, s * yy, zt + 0.9) for yy in (6.6, 7.8)] + [(px - 3.0, s * yy, zt + 0.9) for yy in (6.6, 7.8)]
                           + [(tx + 1.6, s * yy, tz + 1.4) for yy in (6.6, 7.8)] + [(tx - 1.6, s * yy, tz + 1.4) for yy in (6.6, 7.8)]))
    parts.append(cyl_ab((tx, -7.6, tz), (tx, 7.6, tz), 1.0, 32))                           # trunnion shaft
    e = math.radians(SL["elev_deg"])
    d = np.array([-math.cos(e), 0.0, math.sin(e)])
    for s in (1, -1):
        y = s * SL["tube_y"]
        p0 = np.array([tx, y, tz]) - d * 3.5                                              # breech end
        p1 = p0 + d * SL["tube_len"]
        parts.append(chcyl_ab(p0, p1, SL["tube_r"], 0.3, 40))                              # tube (3.6 mm)
        parts.append(chcyl_ab(p0 - d * 0.6, p0 + d * 5.0, 2.3, 0.4, 40))                   # breech ring + block
        parts.append(chcyl_ab(p0 + d * 7.0, p0 + d * 9.5, 2.15, 0.3, 40))                  # recoil collar
        parts.append(chcyl_ab(p1 - d * 1.6, p1, 2.1, 0.3, 40))                             # muzzle reinforce
        parts.append(cyl_ab(np.array([tx, y, tz]) - d * 0.2, np.array([tx, y, tz]) + d * 0.2, 2.35, 32))
    parts.append(cyl_ab((tx, 0, tz), (tx, 0, tz) - np.array([0, 0, 4.4]), 1.2, 24))        # elevating screw column
    # open roof doors: two leaves standing at the deck sides
    for s in (1, -1):
        parts.append(chbox((cx, s * (span / 2 - 0.9), zt + 4.3), (Lx - 3.0, 1.0, 8.8), 0.3))
        parts.append(chbox((cx, s * (span / 2 - 1.6), zt + 0.5), (Lx - 3.0, 2.2, 1.0), 0.2))   # hinge strip
    # ready rack: six 120 mm bombs in a cradle at the aft end
    rack_x = cx - Lx / 2 + 3.6
    parts.append(chbox((rack_x, 0, zt + 0.7), (4.4, 15.0, 1.4), 0.3))
    for k in range(6):
        y = -6.25 + 2.5 * k
        parts.append(chcyl_ab((rack_x - 2.0, y, zt + 2.3), (rack_x + 2.4, y, zt + 2.3), 1.05, 0.35, 24))
    m = union(parts)
    cut = []
    for s in (1, -1):
        p1 = np.array([tx, s * SL["tube_y"], tz]) - d * 3.5 + d * SL["tube_len"]
        cut.append(cyl_ab(p1 + d * 0.5, p1 - d * 2.5, 1.07, 32))                          # 120 mm bore (2.14 mm), 2.5 deep
    return m - union(cut)


# ------------------------------------------------------------------------------------------------ detailed ramp
def ramp_detailed():
    """Drop-in alternative to the AW-8A ramp: same plate, hinge bar and pins (B.ramp), but the walking face carries a
    kick-rail border that follows the door aperture and Vigil chevron tread plates, so the open ramp reads as a deck.
    Every inner feature stays inside the door aperture inset 0.5 mm (closed fit unchanged; measured in fits())."""
    base = B.ramp()
    xin = X0 - RP["gap"]
    zlo = RP["hinge_z"] + 2.2
    ap = mf.CrossSection([[(float(y), float(z)) for y, z in RP["aperture"]]])
    in1, in2 = ap.offset(-0.5, mf.JoinType.Miter), ap.offset(-1.3, mf.JoinType.Miter)
    clipz = mf.CrossSection.square((40, RP["top_z"] - 2.2 - zlo), False).translate((-20, zlo))

    def ext(cs, h):
        m = cs.extrude(h)
        R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)                           # (y, z, x)
        return place(m, R, (xin - 0.05, 0, 0))

    rail = ext((in1 - in2) ^ clipz, 0.75)                                                 # 0.8 mm kick rail, 0.7 proud
    tread = []
    for z in np.arange(zlo + 1.8, RP["top_z"] - 3.5, 2.6):
        for k in (1, -1):
            a = math.radians(28 * k)
            Rr = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
            tread.append(place(box((0, 0, 0), (0.6, 9.5, 0.8)), Rr, (xin + 0.25, k * 4.0, z)))
    treads = union(tread) ^ ext(in2 ^ clipz, 0.75)
    rings = [cyl_ab((xin - 0.05, s * 6.5, RP["top_z"] - 4.0), (xin + 0.55, s * 6.5, RP["top_z"] - 4.0), 0.9, 24) for s in (1, -1)]
    lugs = union(rings) - union([cyl_ab((xin - 0.1, s * 6.5, RP["top_z"] - 4.0), (xin + 0.7, s * 6.5, RP["top_z"] - 4.0), 0.4, 16) for s in (1, -1)])
    # remove the AW-8A tread bars first: they are boxes 0.9 thick on the inner face; cut a 0.75 slab inside the aperture
    slab = ext(in1, 0.80)
    return union([base - slab, rail, treads, lugs])


# ------------------------------------------------------------------------------------------------ bay insert (M7 deck)
def deck_regions(rear_tm):
    """Free yz/xy regions of the bay measured on the AW-8A rear half (shapely)."""
    from shapely.geometry import Point, box as sbox
    from shapely.ops import unary_union
    from shapely import affinity

    def sec(origin, normal, keep_pt, frame, clipbox):
        s = rear_tm.section(plane_origin=origin, plane_normal=normal)
        pl, A = s.to_2D()
        mat = unary_union([pg.buffer(0) for pg in pl.polygons_full])
        P3 = []
        # map 2D section polygons back to the requested 2D frame through 3D
        def to_frame(geom):
            def f(x, y, z=None):
                q = A @ np.vstack([np.asarray(x), np.asarray(y), np.zeros_like(np.asarray(x)), np.ones_like(np.asarray(x))])
                return (q[frame[0]], q[frame[1]])
            import shapely
            return shapely.transform(geom, lambda c: np.stack(f(c[:, 0], c[:, 1]), axis=1))
        mat = to_frame(mat)
        free = clipbox.difference(mat)
        geoms = getattr(free, "geoms", [free])
        return [g for g in geoms if g.contains(Point(*keep_pt))][0]
    floor = sec((0, 0, RP["floor_z"][1] + 0.05), (0, 0, 1), (-40, 0), (0, 1), sbox(X0 + T + 0.5, -30, XS - 0.5, 30))
    wall_x = -19.6
    wall = sec((wall_x, 0, 0), (1, 0, 0), (0, 18), (1, 2), sbox(-30, RP["floor_z"][1] + 0.3, 30, S["benches"]["seat_z"][0] - 0.2))
    return floor, wall, wall_x


def bay_insert(rear_tm):
    """Floor grating on the M7 deck + a trench end wall with a rifle rack, one L-shaped part, dropped into the rear
    half through its split face before the halves are glued. The wall stands just aft of the -y split-pin boss."""
    from shapely.geometry import box as sbox
    from shapely.geometry.polygon import orient

    def big(gm):
        gm = max(getattr(gm, "geoms", [gm]), key=lambda q: q.area)
        return orient(gm, 1.0)                                    # CCW: manifold3d CrossSection fills positive area only
    floor, wall, wx = deck_regions(rear_tm)
    z0 = RP["floor_z"][1] + 0.02
    fl = big(floor.intersection(sbox(X0 + T + 0.7, -30, wx - 0.45, 30)).buffer(-0.25, join_style=2))
    g = mf.CrossSection([list(map(tuple, np.asarray(fl.exterior.coords)[:-1]))]).extrude(1.0).translate((0, 0, z0))
    STATS["bay_insert"] = {"grating_area_mm2": round(fl.area, 1), "grating_bounds": [round(v, 2) for v in fl.bounds], "wall_area_mm2": round(wl.area, 1) if False else None}
    cut = []
    for x in np.arange(X0 + T + 2.0, wx - 2.0, 1.6):                                     # grating slots 0.6 wide, 0.4 deep
        cut.append(box((x, 0, z0 + 1.0), (0.6, 2 * 3.6, 0.8)))
    add = []
    for x in (X0 + T + 6.0, -45.0, -26.0):                                               # tie-down pads
        for s in (1, -1):
            add.append(chcyl_ab((x, s * 4.6, z0 + 0.9), (x, s * 4.6, z0 + 1.35), 0.75, 0.15, 20))
    wl = big(wall.intersection(sbox(-30, z0 + 0.5, 30, B.S["benches"]["seat_z"][0] - 0.2)).buffer(-0.3, join_style=2))
    wpts = [(float(y), float(z)) for y, z in np.asarray(wl.exterior.coords)[:-1]]
    w = prism_x(wpts, wx - 0.9, wx)
    add.append(w)
    # rifle rack on the aft face: six Lance rifles muzzle-up in a clamp rail, an extinguisher and a med box
    zr0 = z0 + 2.0
    add.append(chbox((wx - 1.2, 0, zr0 + 6.6), (0.8, 13.0, 0.9), 0.2))                  # clamp rail
    add.append(chbox((wx - 1.2, 0, zr0 + 0.4), (0.8, 13.0, 0.9), 0.2))                  # butt tray
    for k in range(6):
        y = -5.5 + 2.2 * k
        add.append(chbox((wx - 1.35, y, zr0 + 2.0), (0.9, 1.3, 3.0), 0.2))              # stock
        add.append(chbox((wx - 1.3, y, zr0 + 5.2), (0.8, 0.9, 4.2), 0.2))               # receiver + barrel
    add.append(chcyl_ab((wx - 1.6, 9.2, zr0), (wx - 1.6, 9.2, zr0 + 5.0), 1.0, 0.3, 24))  # extinguisher
    add.append(chbox((wx - 1.1, -9.0, zr0 + 4.0), (1.4, 3.2, 2.6), 0.3))                # med box
    cut.append(box((wx - 1.9, -9.0, zr0 + 4.0), (0.8, 0.6, 1.8)))                        # chevron cross, 0.6 mm
    cut.append(box((wx - 1.9, -9.0, zr0 + 4.0), (0.8, 1.8, 0.6)))
    out = union([g] + add) - union(cut)
    comps = out.decompose()
    if len(comps) > 1:
        print("bay-insert components:", [(round(c.volume(), 3), [round(v, 1) for v in c.bounding_box()]) for c in comps])
    return out


# ------------------------------------------------------------------------------------------------ hatches open / commander
def lid_only():
    """The AW-8A hatch lid without its plug (build.hatch minus the plug ring), hatch frame."""
    (Lx, Ly), t = HT["lid"], HT["lid_t"]
    lid = M.batch_hull([rrect(0, 0, Lx, Ly, 2.6, 0, t - 0.3), rrect(0, 0, Lx - 0.6, Ly - 0.6, 2.3, 0, t)])
    panel = M.batch_hull([rrect(0, 0, Lx - 4.0, Ly - 4.0, 1.6, t - 0.05, t + 0.15), rrect(0, 0, Lx - 4.6, Ly - 4.6, 1.3, t - 0.05, t + 0.45)])
    parts = [lid, panel]
    for y in (-Ly / 2 + 3.5, Ly / 2 - 3.5):
        parts.append(chcyl_ab((Lx / 2 - 0.6, y - 2.0, t + 0.2), (Lx / 2 - 0.6, y + 2.0, t + 0.2), 0.8, 0.15, 24))
    parts.append(chbox((-Lx / 2 + 3.0, 0, t + 0.7), (1.2, 6.0, 0.9), 0.3))
    parts.append(chbox((-4.0, -Ly / 2 + 3.4, t + 0.9), (3.0, 1.8, 1.4), 0.35))
    parts.append(chbox((3.0, 0, t + 0.6), (8.0, 1.0, 0.7), 0.25))
    return union(parts)


def hatch_open():
    """Open hatch as one keyed part: the plug ring, a hinge block on the coaming's bow side and the lid fused at 105 deg
    (the deployed render's pose), so an open hatch has a defined, glue-free pose."""
    (Lx, Ly), (ox, oy), c = HT["lid"], HT["opening"], HT["plug_clear"]
    A = B.hatch_open_placement(0.0, 0.0)
    A[:3, 3] -= np.array([0, 0, CT])                                                       # hatch frame (coaming top z = 0)
    lid = mx(lid_only(), A)
    xe = ox / 2 - c                                                                        # plug ring outer x
    block = box((xe - 0.6, 0, -0.5), (1.2, 2 * (Ly / 2 - 3.5) + 4.0, 1.0)) + box((Lx / 2 - 1.1, 0, 0.5), (2.2, 2 * (Ly / 2 - 3.5) + 4.0, 1.0))
    return union([hatch_plug(plate=False), block, lid])


def welded_bad_edges(m):
    """Non-manifold edge count of the STL a slicer reads (float32 positions welded), as build.to_tm checks it."""
    mesh = m.to_mesh()
    w = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3].astype(np.float32).astype(np.float64), np.asarray(mesh.tri_verts), process=True)
    _, cnt = np.unique(w.edges_sorted, axis=0, return_counts=True)
    return int((cnt != 2).sum())


def commander():
    """Retry the sculpt at a few voxel pitches until the float32-welded STL is 2-manifold (the pinch a marching-cubes /
    CSG union leaves moves with the grid; measured: h 0.1 -> 2 bad edges). Every attempt is recorded."""
    tries = []
    for h in OPT.get("commander", {}).get("voxel_try_mm", (0.1, 0.095)):
        m = commander_at(h)
        bad = welded_bad_edges(m)
        tries.append({"voxel_mm": h, "welded_bad_edges": bad, "tris": int(m.num_tri())})
        print("commander try", tries[-1], flush=True)
        if bad == 0:
            break
    STATS["commander_tries"] = tries
    return m


def commander_at(h=None):
    """Commander half-figure standing in an open hatch: Kestrel exosuit torso, warden helm, power pack (tools/exosuit.py
    shared body parts, SDF, not decimated) on a crossbar of the hatch-open part. Hatch frame."""
    sys.path.insert(0, str(PKG.parent / "tools"))
    import exosuit as X
    from sdfkit import v3
    cm = OPT.get("commander", {})
    h = h or cm.get("voxel_mm", 0.1)
    pose = X.Pose(pelvis=(0, 0, 15.8), lean=4.0, twist=8.0, fists=(tuple(cm.get("fist_r", (-6.6, -2.4, 19.6))), tuple(cm.get("hand_l", (6.4, -8.4, 25.2)))),
                  head_yaw=12.0)

    def hands(g, P):
        X.fist(g, P.fist[0], v3(0, 0, -1), P.fist[0] - P.elbow[0])
        X.open_hand(g, P.fist[1], P.fist[1] - P.elbow[1], v3(0, 0, -1), 1)

    cut_fz = cm.get("cut_figure_z", 16.6)
    body = X.figure(pose, h=h, extras=[hands], bbox=((-10.5, -15.0, cut_fz - 0.6), (10.5, 8.0, pose.cut_z + 3.2))).mesh("commander-body")
    helm = X.helm("warden").mesh("commander-helm")
    pack = X.backpack("power").mesh("commander-pack")
    # pack sunk 0.2 mm into the back plate: seated exactly on its mount face it closed a 1.5 mm3 pocket against the back
    # whose shell pinched the skin (2 non-manifold edges after float32 welding: measured at hatch-local (-3.2, 1.07, 8.16))
    Ap = X.pack_placement(pose)
    Ap[:3, 3] -= pose.Rc @ np.array([0.0, cm.get("pack_inset_mm", 0.2), 0.0])
    # fused for print, the glue-fit sockets (peg + 0.1 per side, 0.2 deeper) become sealed voids whose shells pinch the
    # skin (2 non-manifold edges after float32 welding at the neck, for voxel 0.1 and 0.095 alike): fill both sockets
    fill_h = mx(cyl_ab((0, 0, 0.05), (0, 0, -X.PEG_HEAD["sock_depth"] - 0.1), X.PEG_HEAD["d"] / 2 + 0.15, 32), X.helm_placement(pose))
    fill_p = mx(cyl_ab((0, 0.05, 0), (0, -X.PEG_PACK["sock_depth"] - 0.1, 0), X.PEG_PACK["d"] / 2 + 0.15, 32), X.pack_placement(pose))
    # the helm's neck-cut face is coplanar with the gorget top: clean in the figure frame, but after the 135 deg yaw the
    # float32 STL welds that contact into 2 non-manifold edges (diag: body, helm, pack and their unions all clean
    # unrotated; bad edges sat exactly at neck_cut z 25.355). Sink the helm 0.05 mm.
    Ah = X.helm_placement(pose)
    Ah[:3, 3] -= np.array([0.0, 0.0, cm.get("helm_sink_mm", 0.05)])
    m = tm_to_m(body) + fill_h + fill_p + mx(tm_to_m(helm), Ah) + mx(tm_to_m(pack), Ap)
    m = m.trim_by_plane((0, 0, 1), float(cut_fz))
    yaw = cm.get("yaw_deg", 135.0)
    z_at_coaming = cm.get("figure_z_at_coaming", 17.2)
    fig = mx(m, Tm(cm.get("x", -2.6), 0.0, -z_at_coaming, Rz(yaw)))
    (ox, oy), c, pw = HT["opening"], HT["plug_clear"], HT["plug_wall"]
    # floor plate filling the plug ring (z -1.0..-0.2): every piece the waist cut leaves (abdomen, glute and thigh caps)
    # stands on it, so the part is one body (a 9 mm crossbar left 12 bodies: measured)
    floor = rrect(0, 0, ox - 2 * c - 2 * pw + 0.4, oy - 2 * c - 2 * pw + 0.4, 1.2, -1.0, -0.2)
    out = union([hatch_open(), floor, fig])
    comps = out.decompose()
    # marching-cubes union leaves inside-out bubbles (negative shells) and specks: fill / drop them (miniatures lesson)
    STATS["commander_dropped_shells_mm3"] = sorted(round(q.volume(), 4) for q in comps if q.volume() <= 0.05)
    out = union([q for q in comps if q.volume() > 0.05])
    # the SDF/CSG union keeps edges shorter than float32 resolution; the STL a slicer reads welds them into 2 non-manifold
    # edges (measured). Collapse edges < 1 um only (manifold3d simplify tolerance 0.001 mm): a sliver cleanup, not a
    # decimation (QEM is banned on SDF meshes); the triangle change is recorded.
    n0 = out.num_tri()
    out = out.simplify(0.001)
    STATS["commander_micro_clean"] = {"tol_mm": 0.001, "tris_before": int(n0), "tris_after": int(out.num_tri())}
    comps = out.decompose()
    if len(comps) > 1:
        print("commander components:", sorted([(round(q.volume(), 3), [round(v, 1) for v in q.bounding_box()]) for q in comps])[:12])
    STATS["commander_figure_triangles"] = int(body.faces.shape[0] + helm.faces.shape[0] + pack.faces.shape[0])
    STATS["commander_pose"] = {"fists": [list(map(float, f)) for f in pose.fist], "cut_figure_z": cut_fz, "yaw_deg": yaw}
    return out


# ------------------------------------------------------------------------------------------------ roof accessory interface
RA = {"peg_d": 2.0, "peg_depth": 3.0, "pin_d": 1.6, "pin_depth": 2.2, "pin_dx": 8.0, "clear": 0.1, "plate_t": 1.2,
      "key": "+x (toward the bow)"}


def roof_adapter():
    """Documented roof accessory interface for drone racks and other roof kit: plugs into any of the four hatch openings
    (or the spare-wheel position) and offers a 2.0 mm D-flat socket (flat toward +x) between two 1.6 mm pin sockets.
    Hatch frame: plate top at z = 1.2 (= coaming top + 1.2)."""
    t = RA["plate_t"]
    m = hatch_plug(plate=True, plate_t=t)
    m = m + chcyl_ab((0, 0, -2.6), (0, 0, 0.2), 2.5, 0.3, 48)                             # peg boss (wall 1.4 round the socket)
    for s in (1, -1):
        m = m + chcyl_ab((s * RA["pin_dx"], 0, -1.6), (s * RA["pin_dx"], 0, 0.2), 1.9, 0.25, 40)
    cut = [d_socket((0, 0, t + 0.01), (0, 0, -1), RA["peg_d"], RA["peg_depth"], (1, 0, 0), RA["clear"]),
           cyl_ab((0, 0, t - RA["peg_depth"] + 0.2), (0, 0, -3.0), 0.5, 16)]              # vent through the boss floor
    for s in (1, -1):
        cut.append(cyl_ab((s * RA["pin_dx"], 0, t + 0.01), (s * RA["pin_dx"], 0, t - RA["pin_depth"]), RA["pin_d"] / 2 + RA["clear"], 32))
        cut.append(cyl_ab((s * RA["pin_dx"], 0, t - RA["pin_depth"] + 0.1), (s * RA["pin_dx"], 0, -2.0), 0.4, 12))
    # engraved key arrow toward +x (0.6 wide, 0.4 deep), off the sockets
    cut.append(box((4.0, 3.4, t), (3.0, 0.6, 0.8)))
    cut.append(place(box((0, 0, 0), (1.6, 0.6, 0.8)), Rz(35), (5.3, 3.0, t)))
    cut.append(place(box((0, 0, 0), (1.6, 0.6, 0.8)), Rz(-35), (5.3, 3.8, t)))
    return m - union(cut)


def spare_wheel_mount():
    """Spare wheel carrier: hatch plug + plate, a pedestal and the AW-8A axle stub (3.0 mm D-flat, key +y), so a ninth
    kit wheel drops on it lying flat. Hatch frame."""
    m = hatch_plug(plate=True, plate_t=1.0)
    m = m + chcyl_ab((0, 0, 0.9), (0, 0, 2.6), 3.4, 0.3, 48)
    P = W["peg"]
    m = m + B.d_peg((0, 0, 2.55), (0, 0, 1), P["d"], P["length"], P["flat_from_axis"], key=(0, 1, 0))
    return m


def spare_wheel_A(cx, cy):
    """World placement of the kit wheel on the mount at hatch (cx, cy): inner face on the pedestal top."""
    return hatch_A(cx, cy) @ Tm(0, 0, 2.6)


# ------------------------------------------------------------------------------------------------ stowage set
def crate(L, Wd, Hh, seed=0):
    """Ammunition crate: chamfered box, lid seam (0.6 x 0.4), rope handles at the ends, stencil chevron. Flat bottom z = 0."""
    m = chbox((0, 0, Hh / 2), (L, Wd, Hh), 0.35)
    m = m + chbox((0, 0, Hh - 0.4), (L + 0.3, Wd + 0.3, 0.8), 0.25)                       # lid lip
    for s in (1, -1):
        m = m + chbox((s * (L / 2 + 0.25), 0, Hh * 0.55), (0.7, Wd * 0.5, 0.9), 0.2)       # end cleats
        m = m + chbox((0, s * (Wd / 2 + 0.1), Hh * 0.45), (L - 2.4, 0.5, 0.7), 0.15)      # side battens
    cut = [box((0, 0, Hh - 0.95), (L + 2, Wd + 2, 0.4)) - chbox((0, 0, Hh / 2), (L - 0.8, Wd - 0.8, Hh + 2), 0.1)]
    for k in (1, -1):
        cut.append(place(box((0, 0, 0), (0.6, 2.2, 0.8)), Rz(35 * k), (k * 0.6, 0, Hh + 0.0)))
    return m - union(cut)


def roll():
    """Tarp / bedroll: 3.6 mm roll, two straps, a 1.6 mm flat glue strip underneath. Axis x, bottom z = 0."""
    L, r = 14.0, 1.8
    m = chcyl_ab((-L / 2, 0, r), (L / 2, 0, r), r, 0.5, 40) + box((0, 0, 0.3), (L - 1.6, 1.6, 0.6))
    for x in (-L / 4, L / 4):
        m = m + chcyl_ab((x - 0.5, 0, r), (x + 0.5, 0, r), r + 0.3, 0.1, 40)
    cut = [chcyl_ab((L / 2 + 0.01, 0, r), (L / 2 - 0.5, 0, r), 0.8, 0.1, 24), chcyl_ab((-L / 2 - 0.01, 0, r), (-L / 2 + 0.5, 0, r), 0.8, 0.1, 24)]
    return m - union(cut)


def jerrican_rack():
    """Two jerricans (465 x 345 x 165 mm -> 8.3 x 6.2 x 2.9) lying in a rack frame with a strap. Bottom z = 0."""
    parts = [chbox((0, 0, 0.3), (8.3, 13.4, 0.6), 0.2)]                                    # rack floor
    for s in (1, -1):
        c = (0, s * 3.25, 0.6 + 1.45)
        parts.append(chbox(c, (8.0, 6.0, 2.9), 0.5))
        parts.append(chbox((0, s * 3.25, 0.6 + 2.9 + 0.2), (1.2, 1.2, 0.6), 0.2))         # cap
        parts.append(chbox((-2.3, s * 3.25, 0.6 + 2.9 + 0.2), (1.4, 2.0, 0.5), 0.15))     # triple handle
    for y in (-6.4, 6.4):
        parts.append(chbox((0, y, 1.6), (8.3, 0.6, 3.2), 0.2))                             # rack sides
    parts.append(chbox((1.8, 0, 3.55), (0.9, 13.2, 0.5), 0.15))                           # strap (sunk 0.05 into the cans)
    m = union(parts)
    cut = []
    for s in (1, -1):                                                                      # pressed X on each can face
        for k in (1, -1):
            cut.append(place(box((0, 0, 0), (5.0, 0.6, 0.8)), Rz(30 * k), (0, s * 3.25, 0.6 + 2.9 + 0.0)))
    return m - union(cut)


def tow_cable():
    """Tow cable laid along the deck: two 1.3 mm runs on a 0.6 mm glue strip, a thimble eye at each end. Axis x."""
    L = 22.0
    parts = [box((0, 0, 0.3), (L, 2.4, 0.6)), box((0, 0, 0.9), (L - 3.2, 1.2, 0.8))]   # web fills the tunnel under the two runs
    for y in (-0.6, 0.6):
        parts.append(cyl_ab((-L / 2 + 1.6, y, 1.1), (L / 2 - 1.6, y, 1.1), 0.65, 20))
    for s in (1, -1):
        ring = chcyl_ab((s * (L / 2 - 0.5), 0, 0.0), (s * (L / 2 - 0.5), 0, 1.6), 1.6, 0.2, 32) - cyl_ab((s * (L / 2 - 0.5), 0, -1), (s * (L / 2 - 0.5), 0, 3), 0.75, 24)
        parts.append(ring)
        parts.append(chcyl_ab((s * (L / 2 - 2.6), 0, 1.1), (s * (L / 2 - 1.6), 0, 1.1), 1.2, 0.2, 24))   # ferrule
    return union(parts)


# ------------------------------------------------------------------------------------------------ antennae, headlight cages
def antenna():
    """Antenna mount for the stern-locker tops: 2.0 mm base, 1.5 mm stub mast 12 mm tall (wire limit), ball tip.
    Drill 0.5 mm into the ball for a brass whip if wanted. Bottom z = 0."""
    return union([chcyl_ab((0, 0, 0), (0, 0, 1.2), 1.0, 0.2, 32), chcyl_ab((0, 0, 1.0), (0, 0, 2.2), 0.95, 0.15, 32),
                  cyl_ab((0, 0, 2.0), (0, 0, 12.6), 0.75, 24), M.sphere(0.85, 24).translate((0, 0, 12.7))])


def headlight_cage():
    """Brush guard over a bow headlamp: back frame glued to the bow face (x = 0 plane, local), four stand-offs and a
    three-bar front grille 2.4 mm out. Symmetric in y, so one part fits either lamp. Local: back face x = 0."""
    yw, zh = 5.8, 3.2                     # outer frame (lamp 4.2 x 1.6 + 0.1 clearance + 0.7 border)
    frame = box((0.3, 0, 0), (0.6, yw, zh)) - box((0.3, 0, 0), (2, yw - 1.4, zh - 1.4))
    parts = [frame]
    for sy in (1, -1):
        for sz in (1, -1):
            parts.append(box((1.5, sy * (yw / 2 - 0.4), sz * (zh / 2 - 0.4)), (2.0, 0.8, 0.8)))
    for y in (-(yw / 2 - 0.4), 0.0, yw / 2 - 0.4):
        parts.append(box((2.75, y, 0), (0.7, 0.75, zh)))
    for z in (-(zh / 2 - 0.4), zh / 2 - 0.4):
        parts.append(box((2.75, 0, z), (0.7, yw, 0.8)))
    return union(parts)


# ------------------------------------------------------------------------------------------------ bow options (tow eyes)
EYE = {"x0": 71.5, "x1": 74.6, "y": 9.0, "z": 19.8, "r": 1.1, "slip": 0.15}


def eye_sockets(hull_front, x_back=None):
    """Mount block pair that slides over the two bow tow eyes (slip fit). The block's back face is moved forward in
    0.1 mm steps until it does not intersect the AW-8A hull (manifold3d intersection volume), then 0.1 mm more."""
    hf = tm_to_m(hull_front)
    xb = x_back if x_back is not None else EYE["x1"] - 2.4
    for _ in range(40):
        blk = union([chbox(((xb + 78.0) / 2, s * EYE["y"], EYE["z"]), (78.0 - xb, 4.4, 4.2), 0.4) for s in (1, -1)])
        if (blk ^ hf).volume() < 1e-4:
            break
        xb += 0.1
    xb += 0.1
    blk = union([chbox(((xb + 78.0) / 2, s * EYE["y"], EYE["z"]), (78.0 - xb, 4.4, 4.2), 0.4) for s in (1, -1)])
    sock = union([cyl_ab((xb - 0.5, s * EYE["y"], EYE["z"]), (EYE["x1"] + 0.3, s * EYE["y"], EYE["z"]), EYE["r"] + EYE["slip"], 32) for s in (1, -1)])
    STATS.setdefault("eye_socket_back_x", round(xb, 2))
    STATS["eye_socket_depth_mm"] = round(EYE["x1"] + 0.3 - xb, 2)
    return blk, sock


def obstacle_blade(hull_front):
    """Front obstacle / dozer blade on the tow eyes: 50 mm curved moldboard 2 mm off the table, ribbed back, two push arms."""
    blk, sock = eye_sockets(hull_front)
    face = [(84.2, 2.0), (82.4, 4.6), (81.4, 7.6), (81.2, 10.6), (81.8, 13.6)]
    back = [(x - 1.3, z) for x, z in face[::-1]]
    mb = prism_y(face + back, -25.0, 25.0)
    parts = [blk, mb, chbox((84.0, 0, 2.3), (1.0, 50.0, 0.8), 0.2)]                         # cutting edge strip
    for y in (-21.0, -9.0, 9.0, 21.0):
        parts.append(hullp([(80.6, y + dy, z) for dy in (-0.6, 0.6) for z in (3.6, 12.6)] + [(77.6, y + dy, 8.0) for dy in (-0.6, 0.6)]))   # buried 0.5 in the board
    for s in (1, -1):
        y = s * EYE["y"]
        parts.append(hullp([(x, y + dy, z + dz) for dy in (-1.0, 1.0) for dz in (-1.1, 1.1) for x, z in ((76.8, EYE["z"] - 0.5), (80.7, 8.0))]))
        parts.append(hullp([(80.0, y + dy, z) for dy in (-1.0, 1.0) for z in (3.8, 12.4)] + [(78.6, y + dy, 8.0) for dy in (-1.0, 1.0)]))
    for s in (1, -1):                                                                      # end wings
        parts.append(hullp([(x, s * 25.0 + s * dy, z) for dy in (0.45, -0.9) for x, z in ((84.0, 2.2), (81.7, 13.4), (79.5, 13.0), (79.5, 3.0))]))   # wing overlaps the board end
    m = union(parts) - sock
    return m


def mine_roller(hull_front):
    """Mine roller: two gangs of four toothed discs ahead of the wheel tracks on a crossbar hung from the tow eyes."""
    blk, sock = eye_sockets(hull_front)
    ty = W["track_half"]
    parts = [blk, chbox((79.2, 0, 18.4), (2.4, 2 * ty + 1.6, 2.6), 0.4)]
    for s in (1, -1):
        y = s * EYE["y"]
        parts.append(hullp([(x, y + dy, z) for dy in (-1.1, 1.1) for x, z in ((77.0, EYE["z"] - 0.8), (77.0, EYE["z"] + 0.8), (79.6, 17.6), (79.6, 19.4))]))
        yg = s * ty
        parts.append(hullp([(x, yg + dy, z) for dy in (-0.9, 0.9) for x, z in ((78.6, 18.0), (80.0, 19.2), (93.6, 5.6), (92.0, 4.4))]))
        parts.append(cyl_ab((93.0, yg - 6.0, 5.0), (93.0, yg + 6.0, 5.0), 1.0, 24))
        for k, dy in enumerate((-4.2, -1.4, 1.4, 4.2)):
            yc = yg + dy
            disc = chcyl_ab((93.0, yc - 0.7, 5.0), (93.0, yc + 0.7, 5.0), 4.4, 0.3, 48)
            teeth = []
            for i in range(10):
                a = 2 * math.pi * (i + 0.5 * (k % 2)) / 10
                teeth.append(place(chbox((0, 0, 0), (1.4, 1.4, 1.2), 0.25), Rz(0) @ np.array([[math.cos(a), 0, -math.sin(a)], [0, 1, 0], [math.sin(a), 0, math.cos(a)]]),
                                   (93.0 + 4.35 * math.cos(a), yc, 5.0 + 4.35 * math.sin(a))))
            parts.append(disc + union(teeth))
            if k < 3:
                parts.append(chcyl_ab((93.0, yc + 0.6, 5.0), (93.0, yc + 2.2, 5.0), 2.0, 0.2, 32))   # spacer
    return union(parts) - sock


# ------------------------------------------------------------------------------------------------ battle damage
def plate_box(i, s):
    """Outer face of AW-8A applique plate i (0 = rearmost) on side s: (x0, x1, y_face, z0, z1)."""
    b = np.linspace(-70.0, H["glacis_x"], 7)
    t = 0.9 if i % 2 == 0 else 1.3
    return b[i] + 0.6, b[i + 1] - 0.6, s * (27.6 - 0.3 + t + 0.3), 22.4, 29.6


H = S["hull"]


def damage_plate(variant):
    """0.9 mm overlay glued over one applique plate (inside its 0.45 chamfer). a: shell crater with a raised splash rim,
    bullet scars; b: torn corner, welded patch with rivets, gouge. Local: back face z = 0, plate long axis x."""
    L, Hh, t = 18.3 - 1.0, 7.2 - 1.0, 0.9
    if variant == "a":
        outline = mf.CrossSection.square((L, Hh), True)
    else:
        pts = [(-L / 2, -Hh / 2), (L / 2 - 3.6, -Hh / 2), (L / 2 - 2.6, -Hh / 2 + 1.1), (L / 2 - 1.6, -Hh / 2 + 0.9),
               (L / 2 - 0.9, -Hh / 2 + 2.0), (L / 2, -Hh / 2 + 2.4), (L / 2, Hh / 2), (-L / 2, Hh / 2)]
        outline = mf.CrossSection([pts])
    m = outline.extrude(t - 0.3) + outline.offset(-0.3, mf.JoinType.Miter).extrude(t)       # 0.3 mm step round the rim
    cut, add = [], []
    if variant == "a":
        cx = -2.5
        add.append(cyl_ab((cx, 0.3, t - 0.05), (cx, 0.3, t + 0.3), 2.3, 40) - cyl_ab((cx, 0.3, t - 1), (cx, 0.3, t + 1), 1.5, 40))
        cut.append(M.sphere(1.9, 40).scale((1.0, 1.0, 0.26)).translate((cx, 0.3, t + 0.0)))
        for (x, y) in ((4.5, 1.6), (5.6, -0.9), (6.9, 1.2), (3.6, -2.0), (-7.0, -1.8)):
            cut.append(M.sphere(0.55, 20).scale((1.0, 1.0, 0.6)).translate((x, y, t + 0.05)))
    else:
        add.append(chbox((-3.5, 0.2, t + 0.15), (5.4, 4.2, 0.5), 0.15))                 # patch sunk 0.1 (coplanar = 2 bodies)
        for x in (-5.8, -1.2):
            for y in (-1.6, 2.0):
                add.append(cyl_ab((x, y, t + 0.3), (x, y, t + 0.65), 0.35, 12))
        cut.append(place(box((0, 0, 0), (6.0, 0.6, 0.8)), Rz(-18), (3.6, 1.2, t)))
    return union([m] + add) - union(cut) if cut else union([m] + add)


def damage_A(i, s):
    """World placement of a damage overlay on plate i, side s (back face on the plate face, outer face outward)."""
    x0, x1, yf, z0, z1 = plate_box(i, s)
    # local (x, y, z) -> world (x, z-ish, outward): local z (thickness) -> +s*y, local y -> z
    R = np.array([[-s, 0, 0], [0, 0, s], [0, 1, 0]], float)                              # proper rotation (det +1)
    return Tm((x0 + x1) / 2, yf + s * 0.01, (z0 + z1) / 2, R)



# ------------------------------------------------------------------------------------------------ AW-8A assembly (read back)
UP = PKG / "build" / "upright"
HATCH_XY = [tuple(c) for c in HT["centres"]]          # (-58.25, 9.9), (-58.25, -9.9), (-31.35, 9.9), (-31.35, -9.9)


def load(name):
    return trimesh.load(UP / f"{name}.stl", process=False)


def aw8a():
    """AW-8A instances as build.py places them (meshes read back from build/upright, i.e. what the owner prints)."""
    P = {n: load(n) for n in ("hull-front", "hull-rear", "wheel", "rws", "ramp", "hatch")}
    inst = {"Hull front": ("hull-front", np.eye(4)), "Hull rear": ("hull-rear", np.eye(4)), "Tally RWS": ("rws", B.rws_placement()),
            "Stern ramp": ("ramp", np.eye(4))}
    for x, s in B.axle_stations():
        inst[f"Wheel {'L' if s > 0 else 'R'}{x:+.0f}"] = ("wheel", B.wheel_placement(x, s))
    for k, (cx, cy) in enumerate(HATCH_XY):
        inst[f"Hatch {k + 1}"] = ("hatch", B.hatch_placement(cx, cy))
    return P, inst


def placed(tm, A):
    m = tm.copy()
    m.apply_transform(A)
    return m


COLS = {"turret": "#5d6a73", "module": "#6f7d87", "hatch": "#8a98a1", "figure": "#b9b2a4", "stow": "#8b8468", "wheel": "#3d4247",
        "bow": "#5d666d", "detail": "#7a8790", "damage": "#7d8c96", "iface": "#c9a246"}


def registry(rear_tm, front_tm):
    """name -> dict(builder, label, qty, group, color, note, frame). frame: 'local' parts need a placement to show on the
    hull; 'world' parts are modelled in place."""
    R = {}

    def add(name, fn, label, qty, group, note, frame="world"):
        R[name] = {"fn": fn, "label": label, "qty": qty, "group": group, "note": note, "frame": frame}
    add("opt-wren-turret", wren, "AW-8C Wren 25 mm two-seat turret", 1, "turret", "Drops on the shared 30 mm ring in place of the Tally RWS (5 x 2 mm magnet; troops 8 in the lore).", "local")
    add("opt-sling-module", sling, "AW-8M Sling twin 120 mm mortar module", 1, "module", "Plugs into the two forward hatch openings; Tally RWS retained on the ring.")
    add("opt-ramp-detailed", ramp_detailed, "Stern ramp, detailed walking face", 1, "detail", "Swaps for the AW-8A ramp (same hinge pins): kick-rail border, chevron treads, tie-down rings.")
    add("opt-bay-insert", lambda: bay_insert(rear_tm), "Bay insert: deck grating + rifle-rack end wall", 1, "detail", "Drops onto the M7 deck through the rear half's split face before the halves are glued.")
    add("opt-hatch-open", hatch_open, "Roof hatch, open (plug + lid at 105 deg)", 2, "hatch", "Any hatch opening; replaces a closed hatch.", "local")
    add("opt-commander", commander, "Commander half-figure in an open hatch", 1, "figure", "Kestrel exosuit torso, warden helm, power pack (tools/exosuit.py) standing in an open hatch; any opening.", "local")
    add("opt-roof-adapter", roof_adapter, "Roof accessory adapter (2.0 D-flat + 2 x 1.6 pin sockets)", 2, "iface", "Documented interface for drone launch racks and roof kit; any hatch opening.", "local")
    add("opt-spare-wheel-mount", spare_wheel_mount, "Spare-wheel mount (print a 9th wheel)", 1, "stow", "Any hatch opening; the kit wheel drops on its D-flat stub.", "local")
    add("opt-crate-large", lambda: crate(9.0, 6.0, 4.5), "Ammunition crate, large", 2, "stow", "Glue anywhere flat (front roof).", "local")
    add("opt-crate-small", lambda: crate(6.0, 4.5, 3.5), "Ammunition crate, small", 2, "stow", "Glue anywhere flat.", "local")
    add("opt-roll", roll, "Tarp roll", 2, "stow", "Flat glue strip underneath.", "local")
    add("opt-jerrican-rack", jerrican_rack, "Jerrican pair in rack", 1, "stow", "Flat bottom.", "local")
    add("opt-tow-cable", tow_cable, "Tow cable (deck run)", 1, "stow", "Flat glue strip; eyes at each end.", "local")
    add("opt-antenna", antenna, "Antenna mount + stub mast", 2, "detail", "Glue on the stern-locker tops; drill the ball for a brass whip.", "local")
    add("opt-headlight-cage", headlight_cage, "Headlight brush guard", 2, "detail", "Glue on the bow face round each headlamp; symmetric.", "local")
    add("opt-obstacle-blade", lambda: obstacle_blade(front_tm), "Front obstacle blade", 1, "bow", "Slides over the two bow tow eyes (slip fit).")
    add("opt-mine-roller", lambda: mine_roller(front_tm), "Mine roller (two toothed gangs)", 1, "bow", "Slides over the two bow tow eyes (slip fit); rollers ride on the table.")
    add("opt-damage-a", lambda: damage_plate("a"), "Battle-damage overlay A (crater, scars)", 2, "damage", "Glue over any applique plate.", "local")
    add("opt-damage-b", lambda: damage_plate("b"), "Battle-damage overlay B (torn corner, patch)", 2, "damage", "Glue over any applique plate.", "local")
    return R


# placements that show each local part on the hull (the 'field' configuration; all measured for interference)
FIELD = {
    "opt-commander": [hatch_A(-31.35, 9.9)],
    "opt-hatch-open": [hatch_A(-31.35, -9.9)],
    "opt-roof-adapter": [hatch_A(-58.25, 9.9)],
    "opt-spare-wheel-mount": [hatch_A(-58.25, -9.9)],
    "opt-crate-large": [Tm(28.5, -11.0, RZ + 0.01)],
    "opt-crate-small": [Tm(21.6, 9.4, RZ + 0.01, Rz(90))],
    "opt-roll": [Tm(20.6, -10.0, RZ + 0.01, Rz(90))],
    "opt-jerrican-rack": [Tm(30.2, 9.6, RZ + 0.01)],
    "opt-tow-cable": [Tm(35.0, -4.6, RZ + 0.01)],
    "opt-antenna": [Tm(-74.1, 21.2, 29.4 + 0.01), Tm(-74.1, -21.2, 29.4 + 0.01)],
    "opt-headlight-cage": [Tm(X1 + 0.01, 18.5, 23.6), Tm(X1 + 0.01, -18.5, 23.6)],
    "opt-damage-a": [damage_A(3, 1)],
    "opt-damage-b": [damage_A(5, 1)],
}



def ov(a, b):
    return round(B.overlap(a, b), 4)


def sweep(part_tm, about_A, others, step=15):
    """Turn a ring-mounted part about the ring axis through 360 deg; worst overlap with each other part."""
    worst = {}
    c = np.array(S["ring"]["centre"] + [0.0])
    for deg in range(0, 360, step):
        A = Tm(*c) @ Tm(R=Rz(deg)) @ Tm(*(-c)) @ about_A
        m = placed(part_tm, A)
        for n, o in others.items():
            v = ov(m, o)
            if v > worst.get(n, (-1, 0))[0]:
                worst[n] = (v, deg)
    return {n: {"max_overlap_mm3": v, "at_deg": d} for n, (v, d) in worst.items()}


def fits(T_, P, inst):
    A = {n: placed(P[s], M_) for n, (s, M_) in inst.items()}
    hulls = {"Hull front": A["Hull front"], "Hull rear": A["Hull rear"]}
    closed = {f"Hatch {k + 1}": A[f"Hatch {k + 1}"] for k in range(4)}
    F = {}
    # Wren on the ring: closed and swept against hull + 4 closed hatches
    F["opt-wren-turret"] = {"sweep_24_headings": sweep(T_["opt-wren-turret"], B.rws_placement(), {**hulls, **closed})}
    # Sling in the forward pair, Tally RWS retained: static vs hull + rear hatches (closed and open), RWS swept over it
    sl = T_["opt-sling-module"]
    rear_open = {f"Hatch {k + 1} open": placed(T_["opt-hatch-open"], hatch_A(*HATCH_XY[k])) for k in (0, 1)}
    F["opt-sling-module"] = {"static": {n: ov(sl, o) for n, o in {**hulls, "Hatch 1": closed["Hatch 1"], "Hatch 2": closed["Hatch 2"], **rear_open}.items()},
                             "rws_sweep_24_headings": sweep(P["rws"], B.rws_placement(), {"Sling module": sl}),
                             "top_z_mm": round(float(sl.bounds[1][2]), 2)}
    rd = T_["opt-ramp-detailed"]
    rdo = placed(rd, B.ramp_open_placement())
    F["opt-ramp-detailed"] = {"closed_vs_hull_rear": ov(rd, A["Hull rear"]), "open_vs_hull_rear": ov(rdo, A["Hull rear"]),
                              "open_lowest_z_mm": round(float(rdo.bounds[0][2]), 3)}
    bi = T_["opt-bay-insert"]
    F["opt-bay-insert"] = {"vs_hull_rear": ov(bi, A["Hull rear"]), "vs_ramp_closed": ov(bi, A["Stern ramp"]), "vs_ramp_detailed_closed": ov(bi, rd),
                           "bay_clear_height_over_grating_mm": round(RZ - T - (RP["floor_z"][1] + 0.02 + 1.0), 2)}
    # hatch-plug parts in every opening, against the hull and the three other (closed) hatches
    for n in ("opt-hatch-open", "opt-commander", "opt-roof-adapter", "opt-spare-wheel-mount"):
        rows = {}
        for k, (cx, cy) in enumerate(HATCH_XY):
            m = placed(T_[n], hatch_A(cx, cy))
            others = {**hulls, **{h: o for h, o in closed.items() if h != f"Hatch {k + 1}"}}
            rows[f"opening {k + 1} ({cx}, {cy})"] = {o: ov(m, x) for o, x in others.items()}
        F[n] = {"per_opening": rows}
    wheel9 = placed(P["wheel"], spare_wheel_A(-58.25, -9.9))
    F["opt-spare-wheel-mount"]["kit_wheel_on_mount_vs"] = {o: ov(wheel9, x) for o, x in {**hulls, **closed}.items() if o != "Hatch 2"}
    F["opt-spare-wheel-mount"]["kit_wheel_vs_mount_mm3"] = ov(wheel9, placed(T_["opt-spare-wheel-mount"], hatch_A(-58.25, -9.9)))
    F["opt-commander"]["rws_sweep_24_headings"] = sweep(P["rws"], B.rws_placement(), {"Commander (opening 3)": placed(T_["opt-commander"], hatch_A(-31.35, 9.9))})
    # field glue-ons: against the hull, the RWS sweep, and each other
    field = {}
    for n, As in FIELD.items():
        for j, Aj in enumerate(As):
            field[f"{n}#{j + 1}"] = placed(T_[n], Aj)
    gl = {}
    names = list(field)
    for i, n in enumerate(names):
        gl[n] = {o: ov(field[n], x) for o, x in hulls.items()}
        gl[n].update({m: ov(field[n], field[m]) for m in names[i + 1:]})
    F["field_glue_ons"] = gl
    stow = {n: m for n, m in field.items() if any(k in n for k in ("crate", "roll", "jerrican", "tow"))}
    F["field_rws_sweep_24_headings"] = sweep(P["rws"], B.rws_placement(), stow)
    F["field_wren_sweep_24_headings"] = sweep(T_["opt-wren-turret"], B.rws_placement(), stow)
    wheels = {n: o for n, o in A.items() if n.startswith("Wheel")}
    for n in ("opt-obstacle-blade", "opt-mine-roller"):
        m = T_[n]
        F[n] = {"vs_hull_front": ov(m, A["Hull front"]), "vs_front_wheels": {w: ov(m, wheels[w]) for w in wheels if "+50" in w or "+29" in w},
                "lowest_z_mm": round(float(m.bounds[0][2]), 3), "front_x_mm": round(float(m.bounds[1][0]), 2),
                "eye_socket_back_x_mm": STATS.get("eye_socket_back_x"), "eye_socket_depth_mm": STATS.get("eye_socket_depth_mm")}
    return F


def render(T_, P, inst, outdir):
    sys.path.insert(0, str(PKG.parent / "concepts" / "_tools"))
    import images as IM
    col = {"hull-front": B.COL["hull"], "hull-rear": B.COL["hull"], "wheel": B.COL["wheel"], "rws": B.COL["rws"], "ramp": B.COL["ramp"], "hatch": B.COL["hatch"]}
    base = {n: (placed(P[s], A), col[s]) for n, (s, A) in inst.items()}
    name = S["name"].split(" (")[0]
    reg = T_["_reg"]

    def opt(n, A=np.eye(4)):
        return (placed(T_[n], A), COLS[reg[n]["group"]])

    def sheet(fn, parts, title, sub, az=38, el=22, figure=True, xfig=None):
        notes = ["Phase 2 option parts on the AW-8A hull (manifold3d CSG; commander figure SDF)", "Vigilant proxy (32 mm base) for scale; lights fixed in the world"]
        return IM.sheet_hero(parts, outdir / fn, title, sub, notes, az=az, el=el, figure=figure, xfig=xfig)

    outs = []
    sc = [v for k, v in base.items() if k != "Tally RWS"] + [opt("opt-wren-turret", B.rws_placement())]
    outs.append(sheet("wayfarer-apc-aw8c-wren.png", sc, name + " AW-8C Wren", "Wren 25 mm two-seat turret on the shared 30 mm ring (swaps with the Tally RWS)"))
    sc = [v for k, v in base.items() if k not in ("Hatch 3", "Hatch 4")] + [opt("opt-sling-module")]
    outs.append(sheet("wayfarer-apc-aw8m-sling.png", sc, name + " AW-8M Sling", "Twin 120 mm mortar module in the forward hatch openings, roof doors open; Tally RWS retained",
                      az=215, el=28, xfig=(-92, 26, 0)))
    sc = [v for k, v in base.items() if not k.startswith("Hatch")] + [opt("opt-obstacle-blade")]
    for n, As in FIELD.items():
        for Aj in As:
            sc.append(opt(n, Aj))
    sc.append((placed(P["wheel"], spare_wheel_A(-58.25, -9.9)), B.COL["wheel"]))
    outs.append(sheet("wayfarer-apc-field.png", sc, name + " in the field", "Obstacle blade, stowage, spare wheel, antennae, headlight guards, damage overlays, commander, open hatch, roof adapter",
                      az=40, el=26, xfig=(70, 58, 0)))
    sc = [v for k, v in base.items() if k not in ("Stern ramp", "Hatch 1", "Hatch 2", "Hatch 3", "Hatch 4")]
    sc += [opt("opt-ramp-detailed", B.ramp_open_placement()), opt("opt-bay-insert")]
    sc += [opt("opt-hatch-open", hatch_A(-58.25, 9.9)), opt("opt-hatch-open", hatch_A(-58.25, -9.9))]
    outs.append(sheet("wayfarer-apc-interior.png", sc, name + " deployed, detailed interior", "Detailed ramp open, deck grating and rifle-rack end wall in the bay, rear hatches open, forward hatches off",
                      az=212, el=34, xfig=(-100, 30, 0)))
    sc = [v for k, v in base.items() if k != "Tally RWS"] + [opt("opt-wren-turret", B.rws_placement()), opt("opt-mine-roller")]
    outs.append(sheet("wayfarer-apc-mine-roller.png", sc, name + " AW-8C with mine roller", "Mine roller on the bow tow eyes; Wren turret", az=30, el=20, xfig=(40, 62, 0)))
    # lineup of every option part (print set), laid out on the table
    items = [n for n in reg]
    cells, x, y, rowh = [], 0.0, 0.0, 0.0
    for n in items:
        m = T_[n].copy()
        if n == "opt-sling-module":
            pass
        m.apply_transform(Tm(*(-m.bounds[0])))
        e = m.extents
        if x + e[0] > 190:
            x, y, rowh = 0.0, y - rowh - 8.0, 0.0
        m.apply_transform(Tm(x, y - e[1], 0))
        cells.append((m, COLS[reg[n]["group"]]))
        x += e[0] + 8.0
        rowh = max(rowh, e[1])
    outs.append(IM.sheet_hero(cells, outdir / "wayfarer-apc-options-lineup.png", name + " phase 2 option parts",
                              "Every option part in model pose, laid out (order: " + ", ".join(n[4:] for n in items) + ")"[:0],
                              ["Order, row by row: " + ", ".join(n[4:] for n in items[:10]), ", ".join(n[4:] for n in items[10:])], az=30, el=40, figure=False))
    return [str(o) for o in outs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    P, inst = aw8a()
    reg = registry(P["hull-rear"], P["hull-front"])
    only = [s for s in a.only.split(",") if s]
    T_, rows = {}, {}
    for n, r in reg.items():
        if only and n not in only and not any(n.endswith(o) for o in only):
            continue
        m = r["fn"]()
        tm = B.to_tm(m, n)
        tm.export(OUT / f"{n}.stl")
        T_[n] = tm
        rows[n] = {"label": r["label"], "qty": r["qty"], "group": r["group"], "note": r["note"], "frame": r["frame"],
                   "volume_mm3": round(float(tm.volume), 2), "bbox_mm": [round(float(v), 2) for v in tm.extents],
                   "triangles": int(len(tm.faces)), "bodies": len(tm.split(only_watertight=False)), "watertight": bool(tm.is_watertight),
                   "mesh_quality": B.mesh_quality(tm)}
        print(n, rows[n]["volume_mm3"], rows[n]["bbox_mm"], rows[n]["triangles"], flush=True)
    if only:
        return
    T_["_reg"] = reg
    F = fits(T_, P, inst)
    total = sum(r["volume_mm3"] * r["qty"] for r in rows.values()) / 1000
    rep = {"generator": "source/options.py (manifold3d CSG; commander figure tools/exosuit.py SDF, not decimated)", "parts": rows,
           "options_resin_ml_all_qty": round(total, 2), "aw8a_kit_ml": json.loads((PKG / "reports" / "build.json").read_text())["kit_resin_ml_solid_parts"],
           "fits": F, "stats": STATS,
           "roof_interface": {"standard": RA, "socket_bore_mm": RA["peg_d"] + 2 * RA["clear"], "d_flat_from_axis_mm": round(0.3 * RA["peg_d"] + RA["clear"], 2),
                              "pin_bore_mm": RA["pin_d"] + 2 * RA["clear"], "plate_top_above_roof_mm": HT["coaming_h"] + RA["plate_t"],
                              "positions_hull_frame": [{"opening": k + 1, "peg_xy": [cx, cy], "pins_xy": [[cx - RA["pin_dx"], cy], [cx + RA["pin_dx"], cy]],
                                                         "plate_top_z": round(CT + RA["plate_t"], 2)} for k, (cx, cy) in enumerate(HATCH_XY)]}}
    (PKG / "reports" / "options.json").write_text(json.dumps(rep, indent=1))
    viewer = []
    for n, As in FIELD.items():
        for j, Aj in enumerate(As):
            m = placed(T_[n], Aj)
            viewer.append({"name": f"{reg[n]['label']} {j + 1}", "group": reg[n]["group"], "color": COLS[reg[n]["group"]], "note": reg[n]["note"],
                           "explode": [0, 0, 6], "printStl": f"print/stl/options/{n}.stl", "vertices": np.round(m.vertices, 3).tolist(), "triangles": m.faces.tolist()})
    for n in ("opt-wren-turret", "opt-sling-module", "opt-obstacle-blade", "opt-mine-roller", "opt-ramp-detailed", "opt-bay-insert"):
        A = B.rws_placement() if n == "opt-wren-turret" else np.eye(4)
        m = placed(T_[n], A)
        viewer.append({"name": reg[n]["label"], "group": reg[n]["group"], "color": COLS[reg[n]["group"]], "note": reg[n]["note"], "explode": [0, 0, 6],
                       "printStl": f"print/stl/options/{n}.stl", "vertices": np.round(m.vertices, 3).tolist(), "triangles": m.faces.tolist()})
    (PKG / "viewer" / f"{S['id']}.options.json").write_text(json.dumps(viewer, separators=(",", ":")))
    print(json.dumps({"options_ml": rep["options_resin_ml_all_qty"], "fits": F}, indent=1)[:6000], flush=True)
    if not a.no_images:
        print("images:", render(T_, P, inst, PKG / "images"))


if __name__ == "__main__":
    main()
