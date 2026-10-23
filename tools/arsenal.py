"""Arsenal: the VW2 series, a more detailed second-generation weapon set for the Aster Compact Vigilant line.

Original designs (no shapes, logos or marks from existing games, films or stock art). The VW/VA registries in
tools/armory.py are untouched; this module adds a parallel registry:

- WEAPONS2 VW2-01..16: weapons in the same local weapon frame as armory.WEAPONS: millimetres at print scale (30 mm
  heroic, 1:56), x toward the muzzle, z up, y to the left side, origin = the main grip / fist centre. Knife and
  breaching tool: grip along z, origin = grip centre (like VW-08 Edge). Grenade and charge: flat base at z = 0.

Fit to the Vigil hands: every pistol grip is the VW grip block (centre (0, 0, -0.45), section 1.0 x 1.1 mm, 2.0 mm
long), so exosuit.fist() closes over it exactly as it does on VW-01..07. VW2 grips rake back 12-22 deg (bottom
toward the stock), which matches the fist axis the figures already use (down = (-0.24, 0, -0.97)). FORE[ident] gives
the support-hand point for two-handed poses (fist centre, weapon frame).

Detail rules (MSLA resin, 30 mm heroic): engraved panel lines 0.35 mm wide x 0.25 mm deep, vent slots 0.4 mm wide x
0.3 mm deep with >= 0.35 mm lands, rail teeth 0.42 mm on a 0.85 mm pitch, raised detail >= 0.35 mm, barrels >= 1.0 mm
diameter (0.8 mm brief minimum), lens / bore recesses 0.3-0.6 mm deep with >= 0.3 mm rims, no knife edges.

Each weapon is a Build: an ordered list of add / cut operations on SDF primitives. Build.sculpt(h) meshes it on its own
grid (each operation only touches voxels in its own bbox, so 0.05 mm grids stay fast); Build.shape() returns one
Shape for a figure to hold: g.add(arsenal.weapon_shape("VW2-01").moved(M)).
Use: arsenal.weapon("VW2-04"), arsenal.catalogue().
"""
from __future__ import annotations

import math

import numpy as np

from sdfkit import Sculpt, Shape, capsule, cyl, rbox, rot, round_cone, sphere, torus, tube, unit, v3

I3 = np.eye(3)
RY = (0, 1, 0)
RX = (1, 0, 0)
Z = (0, 0, 1)
GRIP_C = v3(0, 0, -0.45)          # VW grip block centre (armory / exosuit)
GRIP_HALF = (0.5, 0.55, 1.0)      # VW grip block half extents (1.0 x 1.1 x 2.0 mm)
LINE_W, LINE_D = 0.50, 0.25       # engraved panel line: 90 deg V-groove, 0.5 mouth, 0.25 deep (0.2 revision)
SLOT_W, SLOT_D = 0.46, 0.30       # vent slot (>= the 0.4 mm engraved-detail limit with margin)
MIN_RECESS = 0.46                 # floor for every engraved helper (miniature_detail_resolution_check: >= 0.4 resolves)
MIN_LAND = 0.45                   # material left between neighbouring slots (supported wall 0.4 mm + margin)


class Build:
    """Ordered SDF operations for one weapon."""

    def __init__(self, name):
        self.name, self.ops = name, []
        self.teeth = []            # rail tooth centres (x), so mounts can cover a tooth instead of stopping short

    def add(self, s, k=0.0):
        self.ops.append(("add", s, k))
        return s

    def cut(self, s, k=0.0):
        self.ops.append(("cut", s, k))
        return s

    def bounds(self):
        adds = [s for o, s, _ in self.ops if o == "add"]
        return np.min([s.lo for s in adds], axis=0), np.max([s.hi for s in adds], axis=0)

    def shape(self):
        acc = None
        for o, s, k in self.ops:
            if o == "add":
                acc = s if acc is None else (acc.smooth(s, k) if k else acc | s)
            else:
                acc = acc - s
        lo, hi = self.bounds()
        return Shape(acc.f, lo, hi)

    def sculpt(self, h=0.05, pad=0.4):
        lo, hi = self.bounds()
        g = Sculpt(lo - pad, hi + pad, h)
        for o, s, k in self.ops:
            (g.add if o == "add" else g.cut)(s, k)
        return g


def box(c, half, R=I3, r=0.0):
    return rbox(v3(c), half, R, r)


def X(x, z, y=0.0):
    return v3(x, y, z)


# ------------------------------------------------------------------------------------------------ detail helpers
def _v(w):
    """Half size of the square bar that, turned 45 deg and centred on a face, cuts a 90 deg V of mouth w (depth w/2)."""
    return max(w, LINE_W) / (2 * math.sqrt(2))


def hline(b, x0, x1, z, hy, sides=(-1, 1), w=LINE_W, d=LINE_D):
    """Horizontal engraved panel line on the side faces (|y| = hy) from x0 to x1 at height z: a 90 deg V-groove
    (box slots leave two parallel walls that fail the gap and wall checks; a V does not). d is implied by w."""
    h = _v(w)
    for s in sides:
        b.cut(box(((x0 + x1) / 2, s * hy, z), ((x1 - x0) / 2, h, h), rot(RX, 45)))


def vline(b, x, z0, z1, hy, sides=(-1, 1), w=LINE_W, d=LINE_D, lean=0.0):
    h = _v(w)
    for s in sides:
        b.cut(box((x, s * hy, (z0 + z1) / 2), (h, h, (z1 - z0) / 2), rot(RY, lean) @ rot(Z, 45)))


def slots(b, xs, z0, z1, hy, sides=(-1, 1), w=SLOT_W, d=SLOT_D, lean=0.0):
    """Vent slots on the side faces, optionally leaning (deg, about y). Width floored at MIN_RECESS; when the
    requested positions would leave lands under MIN_LAND they are respaced over the same span."""
    w = max(w, MIN_RECESS)
    xs = list(xs)
    if len(xs) > 1 and min(b_ - a for a, b_ in zip(xs, xs[1:])) < w + MIN_LAND:
        xs = spaced(xs[0], xs[-1], w + MIN_LAND)
    for x in xs:
        for s in sides:
            b.cut(box((x, s * hy, (z0 + z1) / 2), (w / 2, d, (z1 - z0) / 2), rot(RY, lean), 0.1))


def spaced(x0, x1, pitch):
    n = max(1, int(math.floor((x1 - x0) / pitch + 1e-6)) + 1)
    mid = (x0 + x1) / 2
    return [mid + (i - (n - 1) / 2) * pitch for i in range(n)]


def rail(b, x0, x1, z, hy=0.55):
    """Accessory rail on a top face at height z: strip z-0.05..z+0.35, teeth to z+0.6 (0.45 mm on a 1.0 pitch,
    0.55 mm gaps). Teeth stay inside the strip width so they leave no undercut."""
    b.add(box(((x0 + x1) / 2, 0, z + 0.15), ((x1 - x0) / 2, hy, 0.2), I3, 0.06))
    for x in spaced(x0 + 0.3, x1 - 0.3, 1.0):
        b.add(box((x, 0, z + 0.45), (0.225, hy, 0.15), I3, 0.05))
        b.teeth.append(x)
    return z + 0.6


def grip(b, x=0.0, z=0.0, rake=14.0, grooves=True):
    """The VW grip block (fits exosuit.fist) raked back; one 0.48 mm finger groove on the front strap and a 0.4 mm base
    cap (0.2: side texture grooves left 0.01-0.09 mm lips at the cap flange and were removed)."""
    R = rot(RY, rake)
    c = v3(x, 0, z) + GRIP_C
    b.add(box(c, GRIP_HALF, R, 0.22))
    if grooves:
        u, n = R[:, 0], R[:, 2]
        p = c + u * 0.52                                             # one finger groove, >= 0.5 mm lands to cap and receiver
        b.cut(capsule(p - v3(0, 0.75, 0), p + v3(0, 0.75, 0), 0.24))
        b.add(box(c - n * 0.86, (0.56, 0.6, 0.2), R, 0.07))          # base cap (0.4 thick)
    return c


def trigger(b, x=0.0, zr=0.2, reach=1.45):
    """Trigger guard loop (0.6 mm bar) from the grip front to the receiver underside at zr, plus the trigger blade."""
    b.add(capsule(X(x - 0.1, -0.85), X(x + reach, -0.85), 0.3), 0.12)
    b.add(capsule(X(x + reach, -0.85), X(x + reach + 0.2, zr + 0.15), 0.3))
    b.add(capsule(X(x + 0.82, zr + 0.1), X(x + 0.72, zr - 0.42), 0.22))


def box_mag(b, c, half, rake=0.0, ribs=2, plate=True, studs=True):
    R = rot(RY, rake)
    c = v3(c)
    b.add(box(c, half, R, 0.22))
    n = R[:, 2]
    if studs:                                                                    # round-count studs, front face
        for t in spaced(-half[2] + 0.95, half[2] - 0.95, 0.8):
            b.add(sphere(c + R[:, 0] * (half[0] - 0.05) + n * t, 0.17))
    if plate:
        b.add(box(c - n * (half[2] - 0.12), (half[0] + 0.12, half[1] + 0.1, 0.2), R, 0.08))
    for t in (np.linspace(-0.45, 0.35, ribs) if ribs > 1 else [0.0]):
        for s in (-1, 1):
            b.cut(box(c + n * t * half[2] + v3(0, s * half[1], 0), (half[0] - 0.28, 0.2, 0.23), R, 0.05))


def scope(b, x0, x1, z, r=0.6, bell=0.88, mount_z=None, rings=()):
    """Telescopic sight: tube, objective bell (0.3 mm lens recess, 0.3 mm rim), eyepiece, turrets, ring mounts."""
    b.add(cyl(X(x0 + 0.6, z), X(x1 - 1.2, z), r, 0.1))
    b.add(round_cone(X(x1 - 1.9, z), X(x1 - 1.25, z), r, bell - 0.02))
    b.add(cyl(X(x1 - 1.35, z), X(x1, z), bell, 0.15))
    b.add(cyl(X(x0, z), X(x0 + 0.95, z), r + 0.18, 0.12))
    b.cut(cyl(X(x1 - 0.32, z), X(x1 + 0.3, z), bell - 0.32))
    b.cut(cyl(X(x0 - 0.3, z), X(x0 + 0.3, z), r - 0.14))
    xm = x0 + 0.45 * (x1 - x0)
    b.add(cyl(X(xm, z), X(xm, z + r + 0.42), 0.36, 0.08))                       # elevation turret
    b.add(cyl(X(xm, z), v3(xm, -(r + 0.42), z), 0.34, 0.08))                    # windage turret
    for xr in rings:
        b.add(cyl(X(xr - 0.27, z), X(xr + 0.27, z), r + 0.16, 0.08))
        if mount_z is not None:
            m0, m1 = cover_teeth(b, xr - 0.3, xr + 0.3)
            b.add(box(((m0 + m1) / 2, 0, (z + mount_z - 0.3) / 2), ((m1 - m0) / 2, 0.42, (z - mount_z + 0.3) / 2), I3, 0.1))


def cover_teeth(b, x0, x1, tooth=0.225):
    """Widen a rail mount [x0, x1] over any tooth it would stop short of by less than MIN_RECESS."""
    for t in b.teeth:
        if t - tooth < x0 < t + tooth + MIN_RECESS:
            x0 = min(x0, t - tooth)
        if t - tooth - MIN_RECESS < x1 < t + tooth:
            x1 = max(x1, t + tooth)
    return x0, x1


def holo(b, x, zb):
    """Holographic sight on a rail top at zb: base, hood with a 0.6 x 0.5 mm window (0.4 mm side walls), emitter."""
    x0, x1 = cover_teeth(b, x - 0.9, x + 0.9)
    b.add(box(((x0 + x1) / 2, 0, zb + 0.07), ((x1 - x0) / 2, 0.55, 0.45), I3, 0.12))  # base down to the rail strip
    b.add(box((x + 0.3, 0, zb + 1.12), (0.45, 0.7, 0.66), I3, 0.15))
    b.cut(box((x + 0.3, 0, zb + 1.2), (0.7, 0.3, 0.25), I3, 0.08))
    b.add(box((x - 0.35, 0, zb + 0.72), (0.4, 0.42, 0.28), I3, 0.1))            # emitter, fused to the hood


def brake(b, x0, x1, z, r, n=2, bore=0.26):
    """Muzzle brake: ported through the sides (0.46 mm ports, >= 0.45 mm lands), bore recess at the front."""
    b.add(cyl(X(x0, z), X(x1, z), r, 0.15))
    for xc in spaced(x0 + 0.45, x1 - 0.45, MIN_RECESS + MIN_LAND)[:n]:
        b.cut(box((xc, 0, z), (MIN_RECESS / 2, r + 0.2, r * 0.3), I3, 0.06))
    b.cut(cyl(X(x1 - 0.45, z), X(x1 + 0.3, z), bore))


def flash_hider(b, x0, x1, z, r):
    """Pronged flash hider: four prongs (cross slots 0.48 mm wide), bore recess."""
    b.add(cyl(X(x0, z), X(x1, z), r, 0.12))
    L = (x1 - x0) * 0.55
    b.cut(box((x1, 0, z), (L, 0.24, r + 0.2)))
    b.cut(box((x1, 0, z), (L, r + 0.2, 0.24)))
    b.cut(cyl(X(x1 - L, z), X(x1 + 0.3, z), 0.28))


def xcap(x, sign=1):
    """Half-space that trims a round-cone end cap flat at x (keeps the side toward -sign)."""
    return Shape(lambda Q: sign * (Q[:, 0] - x), (-99, -99, -99), (99, 99, 99))


def ring_grooves(b, xs, z, R_, r=0.24, y=0.0):
    for x in xs:
        b.cut(torus(v3(x, y, z), RX, R_, r))


# ------------------------------------------------------------------------------------------------ relief (0.2 revision)
# Raised hardware: it needs only the 0.1 mm embossed limit and costs no wall, where engraving needs 0.4 mm and does.
BOLT_R, BOLT_H = 0.2, 0.12        # bolt head 0.4 mm across, 0.12 proud; >= 0.86 pitch keeps 0.46 between heads
PLATE_T = 0.16                    # raised access plate thickness (seams between plates hold a wash)


def bolt(b, p, n, r=BOLT_R, h=BOLT_H):
    """Round bolt head on a face with outward normal n, centred at p on that face (sunk 0.06 so it fuses)."""
    p, n = v3(p), v3(n)
    b.add(cyl(p - n * 0.06, p + n * h, r, 0.05))


def side_plate(b, x0, x1, z0, z1, hy, sides=(-1, 1), bolts=True, t=PLATE_T):
    """Raised access plate on the side faces |y| = hy: a bolt in each corner (inset 0.32) when it is tall enough for
    two rows, else a row of bolts on its centre line, else plain."""
    span = 0.64 + 2 * BOLT_R + MIN_RECESS                     # two bolts inset 0.32 with a 0.46 gap between heads
    if not bolts:
        pts = []
    elif z1 - z0 >= span and x1 - x0 >= span:
        pts = [(x, z) for x in (x0 + 0.32, x1 - 0.32) for z in (z0 + 0.32, z1 - 0.32)]
    elif x1 - x0 >= span and z1 - z0 >= 2 * BOLT_R + 0.2:
        inner = x1 - x0 - 0.64                                # a row on the centre line, 0.86-1.3 mm pitch
        n = max(2, min(int(inner / (2 * BOLT_R + MIN_RECESS)) + 1, math.ceil(inner / 1.3) + 1))
        pts = [(x, (z0 + z1) / 2) for x in np.linspace(x0 + 0.32, x1 - 0.32, n)]
    else:
        pts = []
    for s in sides:
        b.add(box(((x0 + x1) / 2, s * (hy + t / 2 - 0.04), (z0 + z1) / 2), ((x1 - x0) / 2, t / 2 + 0.04, (z1 - z0) / 2), I3, 0.05))
        for x, z in pts:
            bolt(b, (x, s * (hy + t), z), (0, s, 0))


def plate_row(b, x0, x1, z0, z1, hy, sides=(-1, 1), n=2, seam=0.5):
    """n raised plates side by side over [x0, x1], separated by seam-wide gaps (wash channels)."""
    w = (x1 - x0 - (n - 1) * seam) / n
    for i in range(n):
        a = x0 + i * (w + seam)
        side_plate(b, a, a + w, z0, z1, hy, sides)


def bolt_row(b, x0, x1, z, hy, sides=(-1, 1), pitch=1.0):
    for x in spaced(x0, x1, pitch):
        for s in sides:
            bolt(b, (x, s * hy, z), (0, s, 0))


def port_bolt(b, x, z, hy, half_z, side=-1, depth=0.22):
    """Bolt carrier inside an ejection port cut 2*depth deep at |y| = hy: a block spanning the port height, 0.6 long,
    standing 0.12 below the skin (leaves >= 0.5 mm of port open either side for a 1.6 mm port)."""
    lo, hi = hy - depth - 0.05, hy - 0.12            # from just under the port floor to 0.12 below the skin
    b.add(box((x, side * (lo + hi) / 2, z), (0.3, (hi - lo) / 2, half_z), I3, 0.05))
    b.add(cyl(v3(x + 0.1, side * (hi - 0.02), z), v3(x + 0.1, side * (hi + 0.08), z), 0.15, 0.04))  # extractor stud


def round_count(b, x, z0, z1, hy, sides=(1,), pitch=0.8, r=0.17):
    """Magazine round-count studs: a column of raised domes on a side face."""
    for z in spaced(z0, z1, pitch):
        for s in sides:
            b.add(sphere(v3(x, s * (hy - 0.05), z), r))


def cooling_rings(b, x0, x1, z, r_out, pitch=0.9, t=0.42, y=0.0):
    """Raised cooling rings round a barrel along x (0.42 thick: a ring is a wall; >= 0.46 mm between rings)."""
    for x in spaced(x0, x1, max(pitch, t + MIN_RECESS)):
        b.add(cyl(v3(x - t / 2, y, z), v3(x + t / 2, y, z), r_out, 0.08))


def lens(b, p, n, R=0.34):
    """Indicator / capacitor lens on a face (normal n): raised bezel ring with a dome filling it (no recess)."""
    p, n = v3(p), v3(n)
    b.add(torus(p + n * 0.02, n, R - 0.12, 0.12))
    b.add(sphere(p - n * 0.1, R - 0.08))


def cable(b, pts, r=0.22, clamps=()):
    """Cable run (tube through pts) with raised clamp collars ((centre, axis) pairs)."""
    if pts:
        b.add(tube([v3(p) for p in pts], r))
    for c, axis in clamps:
        a = unit(axis)
        b.add(cyl(v3(c) - a * 0.17, v3(c) + a * 0.17, r + 0.13, 0.05))


# ------------------------------------------------------------------------------------------------ bullpup family
def _bullpup(b, rear=-3.7, front=4.6, butt=-5.9, top=2.3, mag_x=-2.1, mag_half=(0.95, 0.72, 1.25), rail_x=(-1.9, 3.6)):
    """Shared bullpup receiver (VW2-01..04): receiver, butt, spine, grip, trigger, magazine behind the grip."""
    mid = (rear + front) / 2
    b.add(box((mid, 0, (0.2 + top) / 2), ((front - rear) / 2, 0.95, (top - 0.2) / 2), I3, 0.3))     # receiver
    b.add(box(((butt + rear) / 2 + 0.15, 0, 1.15), ((rear - butt) / 2 + 0.25, 0.9, 1.2), rot(RY, 5), 0.35), 0.25)  # butt
    b.add(box((butt + 0.15, 0, 1.1), (0.25, 0.97, 1.32), rot(RY, 5), 0.12))                         # butt pad
    b.add(box((mid + 0.4, 0, top + 0.2), ((front - rear) / 2 - 0.5, 0.72, 0.3), I3, 0.12), 0.15)    # top spine
    zr = rail(b, rail_x[0], rail_x[1], top + 0.45)
    # side detail: ejection port (-y), charging handle, selector, panel lines, butt vents
    b.cut(box((-0.9, -0.95, 1.5), (0.85, 0.22, 0.35), I3, 0.08))
    b.add(box((front - 1.1, -0.98, top - 0.45), (0.38, 0.3, 0.22), I3, 0.1))
    b.add(cyl(v3(0.55, -0.85, 1.55), v3(0.55, -1.17, 1.55), 0.28, 0.08))       # selector, clear of the port
    hline(b, rear + 0.35, front - 0.35, 0.92, 0.95, sides=(1,))              # -y: would lip the port
    vline(b, 1.45, 0.45, top - 0.3, 0.95)
    vline(b, rear + 0.25, 0.45, top - 0.3, 0.95)
    slots(b, [max(butt + 0.6, rear - 1.6), rear - 0.85], 0.75, 1.75, 0.9, lean=-18)
    port_bolt(b, -0.9, 1.5, 0.95, 0.35)                                          # bolt carrier in the port
    plate_row(b, rear + 0.75, 0.95, 1.35, top - 0.2, 0.95, sides=(1,), n=2)       # bolted access plates (+y)
    side_plate(b, 1.95, front - 0.45, 1.35, top - 0.2, 0.95, sides=(1,))
    if -2.3 - (rear + 0.6) >= 0.6:
        side_plate(b, rear + 0.6, -2.3, 1.35, top - 0.2, 0.95, sides=(-1,))        # -y, behind the port
    if front - 1.95 - 2.0 >= 0.6:
        side_plate(b, 2.0, front - 1.95, 1.35, top - 0.2, 0.95, sides=(-1,))       # -y, ahead of the selector
    for z in spaced(0.3, 2.0, 0.85):                                            # butt-pad ribs
        xf = butt + 0.15 - 0.25 * math.cos(math.radians(5)) + (z - 1.1) * math.sin(math.radians(5))  # pad face
        b.add(box((xf - 0.02, 0, z), (0.1, 0.8, 0.17), rot(RY, 5), 0.05))
    grip(b)
    trigger(b, zr=0.2)
    box_mag(b, (mag_x, 0, 0.15 - mag_half[2] + 0.2), mag_half, rake=8, ribs=2)
    b.add(box((mag_x, 0, 0.15), (mag_half[0] + 0.15, mag_half[1] + 0.08, 0.25), rot(RY, 8), 0.1))  # mag well collar
    return zr


def glaive():
    """VW2-01 'Glaive' service rifle: bullpup, vented handguard, rail, holo sight, two-port brake, angled fore grip."""
    b = Build("glaive")
    zr = _bullpup(b)
    b.add(box((6.4, 0, 1.4), (1.95, 0.85, 0.85), I3, 0.3), 0.2)                  # handguard x 4.45..8.35
    slots(b, spaced(5.1, 7.5, 0.8), 0.95, 1.85, 0.85)
    rail(b, 4.9, 8.0, 2.25, hy=0.5)
    b.add(cyl(X(8.2, 1.45), X(10.2, 1.45), 0.55, 0.1))                          # barrel 1.1 mm
    b.add(box((8.5, 0, 1.45), (0.3, 0.6, 0.62), I3, 0.12))                       # gas block, fused to the handguard
    brake(b, 10.1, 11.7, 1.45, 0.8)
    holo(b, 0.7, zr)
    b.add(box((5.9, 0, 0.2), (0.45, 0.5, 0.75), rot(RY, -20), 0.2))              # angled fore grip
    cooling_rings(b, 9.45, 9.45, 1.45, 0.82)                                     # barrel cooling ring
    for sd in (-1, 1):
        bolt(b, (8.5, sd * 0.6, 1.45), (0, sd, 0))                                # gas block pin
        bolt(b, (0.7, sd * 0.55, zr + 0.12), (0, sd, 0))                           # holo windage / elevation knobs
    lx0, lx1 = cover_teeth(b, 7.03, 7.97)                                         # signature: rail laser / torch
    b.add(box(((lx0 + lx1) / 2, 0, 2.9), ((lx1 - lx0) / 2, 0.42, 0.33), I3, 0.12))
    lens(b, (lx1, 0, 2.9), (1, 0, 0), R=0.3)
    for sd in (-1, 1):
        bolt(b, ((lx0 + lx1) / 2, sd * 0.42, 2.9), (0, sd, 0))
    return b


def quarrel():
    """VW2-02 'Quarrel' carbine: short bullpup, cut-down handguard with a cooling window, flash hider, short rail."""
    b = Build("quarrel")
    zr = _bullpup(b, rear=-3.3, front=3.7, butt=-5.0, mag_x=-1.9, mag_half=(0.85, 0.68, 1.05), rail_x=(-1.5, 2.9))
    b.add(box((4.9, 0, 1.4), (1.3, 0.82, 0.8), I3, 0.28), 0.2)                   # handguard x 3.6..6.2
    b.cut(box((4.95, 0, 1.45), (0.75, 0.95, 0.28), I3, 0.12))                     # cooling window (through)
    b.add(cyl(X(5.5, 1.45), X(7.2, 1.45), 0.55, 0.1))
    flash_hider(b, 7.0, 8.3, 1.45, 0.72)
    holo(b, 0.4, zr)
    b.add(box((4.6, 0, 0.35), (0.42, 0.48, 0.55), rot(RY, -12), 0.18))           # stub fore grip
    b.add(box((4.95, 0, 1.45), (0.2, 0.84, 0.32), I3, 0.06))                       # heat-sink bar across the window
    for sd in (-1, 1):
        bolt(b, (0.4, sd * 0.55, zr + 0.12), (0, sd, 0))                           # holo knobs
    return b


def bodkin():
    """VW2-03 'Bodkin' marksman rifle (DMR): long free-float shroud with staggered vent ports, long barrel,
    big scope, cheek riser, folded bipod."""
    b = Build("bodkin")
    zr = _bullpup(b, rear=-3.8, front=4.8, butt=-6.2, mag_half=(0.9, 0.7, 1.0), rail_x=(-2.4, 4.2))
    b.add(box((-4.7, 0, 2.55), (1.2, 0.7, 0.28), I3, 0.15), 0.2)                 # cheek riser
    b.add(cyl(X(4.6, 1.45), X(10.4, 1.45), 0.85, 0.2))                          # shroud 1.7 mm
    for i, x in enumerate(spaced(5.3, 9.7, 0.7)):
        z = 1.65 if i % 2 else 1.25
        for s in (-1, 1):
            b.cut(cyl(v3(x, s * 1.2, z), v3(x, s * 0.55, z), 0.24))
    b.add(cyl(X(10.2, 1.45), X(14.4, 1.45), 0.52, 0.1))                         # barrel 1.04 mm
    brake(b, 14.0, 15.8, 1.45, 0.8)
    scope(b, -2.0, 4.6, zr + 1.05, r=0.58, bell=0.9, mount_z=zr - 0.05, rings=(-0.3, 2.6))
    for s in (-1, 1):                                                            # folded bipod legs
        b.add(capsule(v3(7.3, s * 0.45, 0.5), v3(10.0, s * 0.45, 0.5), 0.3))
    b.add(box((10.0, 0, 0.75), (0.4, 0.75, 0.45), I3, 0.15))                     # bipod hinge block
    cooling_rings(b, 10.95, 13.55, 1.45, 0.75, pitch=0.85)                       # barrel cooling rings
    for sd in (-1, 1):
        bolt(b, (10.0, sd * 0.75, 0.75), (0, sd, 0))                              # bipod hinge pin
    zs = 2.3 + 0.45 + 0.6 + 1.05                                                  # scope axis (zr + 1.05)
    b.add(cyl(X(4.45, zs), X(5.2, zs), 0.9, 0.1))                                 # signature: scope sunshade
    b.cut(cyl(X(4.2, zs), X(5.5, zs), 0.62))
    b.add(box((7.2, 0, 0.5), (0.2, 0.75, 0.3), I3, 0.1))                          # bipod foot bar
    return b


def ranseur():
    """VW2-04 'Ranseur' grenadier rifle: bullpup service rifle with an under-barrel launcher, ladder sight."""
    b = Build("ranseur")
    _bullpup(b)
    b.add(box((6.2, 0, 1.45), (1.75, 0.85, 0.8), I3, 0.3), 0.2)                  # handguard x 4.45..7.95
    slots(b, spaced(5.0, 7.4, 0.8), 1.5, 1.9, 0.85)
    b.add(cyl(X(7.8, 1.45), X(10.0, 1.45), 0.55, 0.1))
    brake(b, 9.6, 11.2, 1.45, 0.78)
    b.add(cyl(X(3.4, -0.55), X(8.7, -0.55), 0.95, 0.25))                        # launcher tube 1.9 mm
    b.cut(cyl(X(8.15, -0.55), X(9.0, -0.55), 0.62))                             # launcher bore (rim 0.33)
    ring_grooves(b, [6.0, 7.6], -0.55, 0.95)
    b.add(box((3.6, 0, -0.35), (0.55, 0.9, 0.75), I3, 0.2))                      # breech block
    b.add(box((4.5, 0, 0.35), (1.0, 0.6, 0.3), I3, 0.12))                        # mount to handguard
    b.add(box((4.1, 0, -1.7), (0.42, 0.5, 0.6), rot(RY, 10), 0.18))              # launcher trigger grip
    b.add(box((6.4, -1.0, 1.2), (0.55, 0.22, 0.35), I3, 0.1))                    # ladder sight frame, below the vents
    b.cut(box((6.4, -1.1, 1.2), (0.25, 0.15, 0.2), I3, 0.06))                    # sight window (blind, 0.3 deep)
    cooling_rings(b, 8.8, 8.8, 1.45, 0.8)
    for sd in (-1, 1):
        bolt(b, (3.6, sd * 0.9, -0.35), (0, sd, 0))                               # launcher breech pin
    return b


# ------------------------------------------------------------------------------------------------ shotgun, PDW
def thresher():
    """VW2-05 'Thresher' drum shotgun: pump action, drum magazine, slotted heat shield, breaching crown muzzle,
    skeleton stock, side shell carrier."""
    b = Build("thresher")
    b.add(box((1.7, 0, 1.25), (2.5, 0.95, 1.05), I3, 0.3))                       # receiver x -0.8..4.2
    b.add(box((-3.0, 0, 1.8), (2.6, 0.72, 0.42), rot(RY, -4), 0.2), 0.2)         # stock comb bar
    b.add(capsule(X(-0.6, 0.55), X(-5.1, -0.25), 0.45))                          # stock lower bar
    b.add(box((-5.55, 0, 0.8), (0.35, 0.85, 1.4), rot(RY, -8), 0.2))             # butt plate
    grip(b, rake=18)
    trigger(b, zr=0.2)
    b.add(cyl(v3(2.4, -0.85, -0.65), v3(2.4, 0.85, -0.65), 1.5, 0.3))           # drum
    for s in (-1, 1):
        b.cut(torus(v3(2.4, s * 0.85, -0.65), (0, 1, 0), 1.0, 0.2))
        b.add(cyl(v3(2.4, s * 0.7, -0.65), v3(2.4, s * 1.05, -0.65), 0.45, 0.1))  # hub
    b.add(cyl(X(4.2, 1.75), X(10.9, 1.75), 0.7, 0.12))                          # barrel 1.4 mm
    b.add(box((6.9, 0, 0.95), (1.6, 0.8, 0.5), I3, 0.25))                        # pump
    slots(b, spaced(5.75, 8.05, 0.75), 0.72, 1.18, 0.8, w=0.36, d=0.2)
    b.add(box((8.0, 0, 2.25), (2.75, 0.82, 0.38), I3, 0.18))                     # heat shield, into the crown
    slots(b, spaced(5.7, 10.1, 0.73), 2.05, 2.45, 0.82, d=0.24)
    b.add(cyl(X(10.6, 1.75), X(11.9, 1.75), 0.92, 0.15))                        # breaching crown
    b.cut(box((11.9, 0, 1.75), (0.32, 0.24, 1.1)))
    b.cut(box((11.9, 0, 1.75), (0.32, 1.1, 0.24)))
    b.cut(cyl(X(11.3, 1.75), X(12.2, 1.75), 0.45))
    b.add(box((10.3, 0, 2.75), (0.22, 0.2, 0.2), I3, 0.06))                      # front sight
    rail(b, 0.1, 3.4, 2.3)
    b.add(box((1.6, -1.05, 1.15), (1.35, 0.2, 0.62), I3, 0.1))                   # shell carrier
    for x in (0.7, 1.6, 2.5):
        b.add(cyl(v3(x, -1.1, 1.15), v3(x, -1.42, 1.15), 0.28, 0.07))
    b.cut(box((3.45, -0.95, 1.6), (0.4, 0.22, 0.3), I3, 0.08))                   # ejection port
    vline(b, 3.55, 0.45, 1.35, 0.95, sides=(1,))
    side_plate(b, -0.35, 2.95, 0.65, 1.95, 0.95, sides=(1,))                     # bolted receiver plate (+y)
    for sd in (-1, 1):
        lens(b, (2.4, sd * 1.05, -0.65), (0, sd, 0), R=0.36)                      # drum round-count window
        bolt(b, (-5.55, sd * 0.85, 0.8), (0, sd, 0))                              # butt plate screw
    for x in spaced(5.6, 10.2, 1.2):                                              # heat-shield screws
        bolt(b, (x, 0, 2.63), (0, 0, 1))
    return b


def rondel():
    """VW2-06 'Rondel' PDW: compact receiver, magazine through the grip, integral ringed suppressor, holo sight,
    vertical fore grip, collapsed twin-rod stock."""
    b = Build("rondel")
    b.add(box((0.8, 0, 1.15), (2.6, 0.85, 0.95), I3, 0.28))                      # receiver x -1.8..3.4
    b.add(cyl(X(3.2, 1.3), X(6.6, 1.3), 0.78, 0.18))                            # suppressor 1.56 mm
    ring_grooves(b, spaced(4.0, 6.0, 0.75), 1.3, 0.78)
    b.cut(cyl(X(6.3, 1.3), X(6.9, 1.3), 0.3))
    zr = rail(b, -1.4, 2.8, 2.05)
    holo(b, 0.6, zr)
    c = grip(b, rake=12)
    n = rot(RY, 12)[:, 2]
    box_mag(b, c - n * 1.55, (0.42, 0.48, 0.8), rake=12, ribs=1)                 # magazine below the grip
    trigger(b, zr=0.2)
    b.add(box((2.4, 0, -0.35), (0.42, 0.48, 0.8), rot(RY, -6), 0.18))            # vertical fore grip
    for t in (-0.75, 0.05):
        b.cut(capsule(v3(2.85, -0.7, t - 0.3), v3(2.85, 0.7, t - 0.3), 0.24))
    for s in (-1, 1):
        b.add(capsule(v3(-1.6, s * 0.52, 1.45), v3(-3.6, s * 0.52, 1.45), 0.32))  # stock rods
    b.add(box((-3.85, 0, 1.2), (0.25, 0.85, 0.95), I3, 0.12))                    # butt plate
    b.cut(box((0.2, -0.85, 1.4), (0.7, 0.22, 0.3), I3, 0.08))                    # ejection port
    slots(b, spaced(2.0, 3.0, 0.75), 0.6, 1.6, 0.85)
    hline(b, -1.5, 1.6, 0.95, 0.85)
    b.add(box((-1.3, 0, 2.25), (0.4, 0.25, 0.25), I3, 0.08))                     # charging knob
    port_bolt(b, 0.2, 1.4, 0.85, 0.3)
    side_plate(b, -1.45, 1.55, 1.35, 1.85, 0.85, sides=(1,))
    return b


# ------------------------------------------------------------------------------------------------ sidearms
def culverin():
    """VW2-07 'Culverin' heavy revolver: six-shot fluted cylinder, top-rib slab barrel with vent slots, ejector rod,
    hammer spur, raked grip."""
    b = Build("culverin")
    b.add(box((-0.15, 0, 1.0), (0.55, 0.55, 0.95), I3, 0.2))                     # rear frame
    b.add(box((0.95, 0, 1.97), (1.35, 0.45, 0.2), I3, 0.1))                      # top strap
    b.add(box((1.15, 0, 0.35), (1.05, 0.5, 0.2), I3, 0.1))                       # frame under the cylinder
    b.add(cyl(X(0.35, 1.05), X(2.0, 1.05), 0.88, 0.18))                         # cylinder 1.76 mm
    for a in (0, 180, 240, 300):                                                 # flutes at 60/120 deg would cut the top strap
        t = math.radians(a)
        p = v3(0, 0.98 * math.cos(t), 1.05 + 0.98 * math.sin(t))
        b.cut(capsule(p + X(0.7, 0), p + X(1.65, 0), 0.25))
    b.add(box((3.75, 0, 1.45), (1.8, 0.52, 0.42), I3, 0.15))                     # slab barrel x 1.95..5.55
    b.add(box((3.4, 0, 1.97), (1.95, 0.25, 0.14), I3, 0.05))                     # top rib
    slots(b, spaced(3.2, 4.7, 0.75), 1.3, 1.6, 0.52, w=0.38, d=0.22, lean=-25)
    b.add(cyl(X(5.4, 1.3), X(5.95, 1.3), 0.5, 0.1))                             # muzzle 1.0 mm
    b.cut(cyl(X(5.6, 1.3), X(6.2, 1.3), 0.25))
    b.add(cyl(X(1.6, 0.72), X(4.2, 0.72), 0.32, 0.08))                          # ejector rod housing
    b.add(box((5.2, 0, 2.05), (0.22, 0.2, 0.24), I3, 0.06))                      # front sight, sunk into the rib
    b.add(box((-0.4, 0, 2.05), (0.25, 0.42, 0.14), I3, 0.06))                    # rear sight
    b.add(capsule(X(-0.45, 1.6), X(-1.0, 2.15), 0.28), 0.25)                     # hammer
    grip(b, x=-0.35, z=0.1, rake=22)
    trigger(b, x=-0.2, zr=0.25, reach=1.3)
    vline(b, 0.2, 0.65, 1.7, 0.55, w=0.35, d=0.2)
    for sd in (-1, 1):
        bolt(b, (-0.35, sd * 0.55, 1.0), (0, sd, 0))                              # frame screw
    for sd in (-1, 1):
        lens(b, (5.05, sd * 0.52, 1.45), (0, sd, 0), R=0.26)                       # signature: barrel charge cell
    return b


def awl():
    """VW2-08 'Awl' service pistol: slide with front and rear serrations, ported compensator, rail slots, sights,
    beavertail."""
    b = Build("awl")
    b.add(box((1.5, 0, 1.35), (2.4, 0.5, 0.5), I3, 0.18))                        # slide x -0.9..3.9
    b.add(box((1.3, 0, 0.6), (1.9, 0.45, 0.42), I3, 0.15))                       # frame
    slots(b, [-0.45, 0.3], 1.05, 1.65, 0.5, w=0.36, d=0.18)                      # rear serrations
    slots(b, [3.15], 1.05, 1.65, 0.5, w=0.36, d=0.18)
    b.cut(box((1.4, 0, 1.85), (0.55, 0.3, 0.2), I3, 0.06))                       # ejection port (top)
    b.add(box((4.25, 0, 1.35), (0.38, 0.56, 0.52), I3, 0.15), 0.15)              # compensator
    b.cut(cyl(X(4.35, 1.3), X(4.9, 1.3), 0.25))
    for x in spaced(2.1, 3.0, 0.85):                                             # rail slots under the frame
        b.cut(box((x, 0, 0.18), (0.24, 0.6, 0.15), I3, 0.05))
    b.add(box((-0.55, 0, 1.92), (0.26, 0.45, 0.14), I3, 0.06))                   # rear sight
    b.cut(box((-0.55, 0, 2.05), (0.4, 0.24, 0.14)))                              # sight notch
    b.add(box((3.55, 0, 1.92), (0.2, 0.18, 0.14), I3, 0.06))                     # front sight
    b.add(box((-0.75, 0, 0.75), (0.28, 0.38, 0.3), rot(RY, 30), 0.12))           # beavertail
    grip(b, rake=18)
    trigger(b, zr=0.2, reach=1.3)
    for sd in (-1, 1):
        lens(b, (1.6, sd * 0.45, 0.5), (0, sd, 0), R=0.26)                        # chamber indicator
    b.add(box((2.55, 0, 0.05), (0.9, 0.4, 0.3), I3, 0.1))                         # signature: rail light, over the rail slots
    lens(b, (3.45, 0, -0.05), (1, 0, 0), R=0.24)
    return b


# ------------------------------------------------------------------------------------------------ support weapons
def partisan():
    """VW2-09 'Partisan' light machine gun: box magazine, feed cover with rail, carry handle over a perforated barrel
    jacket, ribbed handguard, folded bipod, skeleton butt."""
    b = Build("partisan")
    b.add(box((1.6, 0, 1.4), (3.4, 1.0, 1.2), I3, 0.32))                         # receiver x -1.8..5.0
    b.add(box((1.4, 0, 2.85), (2.5, 0.85, 0.35), I3, 0.15))                      # feed cover
    b.add(cyl(v3(-1.0, -0.9, 2.8), v3(-1.0, 0.9, 2.8), 0.35, 0.08), 0.15)       # cover hinge
    rail(b, -0.4, 3.4, 3.15, hy=0.5)
    b.add(box((-4.1, 0, 1.55), (2.45, 0.85, 1.0), rot(RY, -3), 0.3))             # butt x -6.5..-1.7
    b.cut(box((-4.0, 0, 1.55), (1.2, 1.0, 0.36), rot(RY, -3), 0.15))             # lightening window
    b.add(box((-6.6, 0, 1.45), (0.25, 0.9, 1.15), I3, 0.1))
    grip(b, rake=16)
    trigger(b, zr=0.2)
    box_mag(b, (3.0, 0, -1.0), (1.5, 0.85, 1.3), ribs=3)
    b.add(box((3.0, 0, 0.25), (1.65, 0.95, 0.2), I3, 0.08))
    b.add(cyl(X(4.8, 1.6), X(11.0, 1.6), 0.95, 0.2))                            # barrel jacket 1.9 mm
    for x in spaced(7.5, 10.3, 0.8):                                             # one row on the axis: off-axis rows left knife edges
        for s in (-1, 1):
            b.cut(cyl(v3(x, s * 1.25, 1.6), v3(x, s * 0.55, 1.6), 0.24))
    b.add(box((6.1, 0, 0.95), (1.2, 0.85, 0.55), I3, 0.22))                      # handguard
    slots(b, spaced(5.4, 6.8, 0.7), 0.6, 1.3, 0.85, w=0.36, d=0.2)
    for x in (6.6, 8.6):                                                         # carry handle posts
        b.add(capsule(X(x, 2.3), X(x, 3.6), 0.33))
    b.add(capsule(X(6.6, 3.6), X(8.6, 3.6), 0.36))
    b.add(cyl(X(10.8, 1.6), X(12.4, 1.6), 0.55, 0.1))
    flash_hider(b, 12.1, 13.5, 1.6, 0.75)
    for s in (-1, 1):
        b.add(capsule(v3(7.0, s * 0.5, 0.55), v3(10.5, s * 0.5, 0.55), 0.3))     # folded bipod legs, from the handguard
    b.add(box((10.6, 0, 0.9), (0.4, 0.8, 0.5), I3, 0.15))
    b.cut(box((0.2, -1.0, 1.6), (0.9, 0.22, 0.35), I3, 0.08))                    # ejection port
    b.add(box((3.8, -1.05, 1.9), (0.4, 0.3, 0.22), I3, 0.1))                     # charging handle
    hline(b, -1.5, 4.7, 0.75, 1.0)
    vline(b, 2.3, 0.45, 2.3, 1.0)
    port_bolt(b, 0.2, 1.6, 1.0, 0.35)
    side_plate(b, -1.3, 1.8, 1.25, 2.35, 1.0, sides=(1,))
    for x in (-5.45, -2.55):                                                     # signature: bolted skeleton stock
        for z in (1.0, 2.1):
            for sd in (-1, 1):
                bolt(b, (x, sd * 0.85, z), (0, sd, 0))
    for x in (7.15, 8.05):                                                        # carry-handle grip rings (0.42 thick)
        b.add(cyl(X(x - 0.21, 3.6), X(x + 0.21, 3.6), 0.48, 0.06))
    return b


def arbalest():
    """VW2-10 'Arbalest' rail rifle: twin magnetic rails bound by four coil clamps, capacitor drum stock, big scope,
    power cable, fore grip under the rails."""
    b = Build("arbalest")
    b.add(box((1.5, 0, 1.4), (3.5, 1.0, 1.2), I3, 0.32))                         # receiver x -2.0..5.0
    b.add(cyl(X(-5.0, 1.5), X(-1.6, 1.5), 1.2, 0.3), 0.25)                      # capacitor drum
    ring_grooves(b, spaced(-4.3, -2.5, 0.6), 1.5, 1.2)
    b.add(box((-5.15, 0, 1.3), (0.35, 0.95, 1.35), I3, 0.12))                    # butt plate
    for zc in (0.85, 2.15):
        b.add(box((11.3, 0, zc), (6.5, 0.6, 0.35), I3, 0.12))                    # rails x 4.8..17.8
    for x in (7.0, 9.9, 12.8, 15.7):
        b.add(box((x, 0, 1.5), (0.42, 0.95, 1.2), I3, 0.2))                      # coil clamps
    b.add(box((18.0, 0, 1.5), (0.45, 0.85, 1.15), I3, 0.2))                      # muzzle block
    b.cut(cyl(X(17.9, 1.5), X(18.7, 1.5), 0.3))
    zr = rail(b, -1.2, 4.2, 2.6)
    scope(b, -1.6, 6.2, zr + 1.15, r=0.62, bell=0.95, mount_z=zr - 0.05, rings=(0.1, 3.4))
    b.add(tube([v3(-3.2, -0.95, 2.35), v3(-1.6, -1.2, 2.45), v3(0.9, -1.1, 2.3)], 0.28))  # power cable, sunk into the drum
    slots(b, spaced(1.6, 4.2, 0.75), 0.75, 2.0, 1.0)
    grip(b, rake=16)
    trigger(b, zr=0.2)
    b.add(box((7.0, 0, -0.15), (0.45, 0.5, 0.8), rot(RY, 10), 0.2))              # fore grip
    hline(b, -1.7, 4.7, 0.7, 1.0)
    for x in (7.0, 9.9, 12.8, 15.7):
        for sd in (-1, 1):
            lens(b, (x, sd * 0.95, 1.5), (0, sd, 0), R=0.34)                      # coil charge lenses
    for c in ((0.0, -1.15, 2.37),):
        b.add(cyl(v3(c) - v3(0.17, 0, 0), v3(c) + v3(0.17, 0, 0), 0.41, 0.05))    # power cable clamps
    for x0 in (7.42, 10.32, 13.22):                                              # signature: coil windings on the rails
        for x in spaced(x0 + 0.67, x0 + 2.06 - 0.67, 0.88):
            for zc in (0.85, 2.15):
                b.add(box((x, 0, zc), (0.21, 0.7, 0.45), I3, 0.05))
    return b


def censer():
    """VW2-11 'Censer' plasma projector: plasma canister over the housing, coolant lines, finned focusing coil,
    flared emitter with a recessed electrode."""
    b = Build("censer")
    b.add(box((1.0, 0, 1.4), (3.5, 1.05, 1.2), I3, 0.5))                         # housing x -2.5..4.5
    b.add(cyl(X(-2.6, 3.35), X(1.5, 3.35), 0.85, 0.25))                         # canister
    cooling_rings(b, -2.0, 1.0, 3.35, 0.97, pitch=1.5)                           # canister bands (raised)
    b.add(box((-0.55, 0, 2.6), (1.4, 0.55, 0.3), I3, 0.12))                      # canister cradle
    b.add(cyl(X(4.3, 1.4), X(8.6, 1.4), 1.0, 0.2))                              # coil body
    for x in spaced(5.0, 7.9, 0.9):
        b.add(cyl(X(x - 0.21, 1.4), X(x + 0.21, 1.4), 1.38, 0.1))                # heat-sink fins (0.42 thick, 0.48 gaps)
    b.add(round_cone(X(8.4, 1.4), X(9.9, 1.4), 0.85, 1.15).clip(xcap(9.9)))      # emitter flare, flat face
    b.cut(cyl(X(9.3, 1.4), X(10.6, 1.4), 0.8))                                  # emitter cup (0.35 rim)
    b.add(cyl(X(9.0, 1.4), X(9.85, 1.4), 0.35, 0.1))                            # electrode
    for s in (-1, 1):
        b.add(tube([v3(1.5, s * 0.45, 3.35), v3(3.0, s * 0.8, 2.8), v3(4.9, s * 0.6, 2.2)], 0.27))  # coolant lines, sunk at both ends
    slots(b, spaced(0.6, 3.6, 0.75), 0.75, 1.95, 1.05, lean=15)
    grip(b, rake=16)
    trigger(b, zr=0.2)
    b.add(box((6.25, 0, -0.25), (0.32, 0.5, 0.8), rot(RY, -8), 0.2), 0.15)       # fore handle
    b.add(box((-2.75, 0, 1.3), (0.4, 0.9, 1.0), I3, 0.2), 0.25)                  # rear cap
    side_plate(b, -2.0, 0.15, 0.95, 2.05, 1.05)                                   # bolted housing plates
    cable(b, [], clamps=[(v3(3.0, s_ * 0.8, 2.8), (1, 0, -0.3)) for s_ in (-1, 1)])  # coolant line clamps
    lens(b, (-2.6, 0, 3.35), (-1, 0, 0), R=0.42)                                  # signature: canister sight-glass
    return b


def ballista():
    """VW2-12 'Ballista' launcher: shoulder tube with a flared venturi, rocket nose in the muzzle, side optic,
    bands, shoulder pad, grip and fore grip."""
    b = Build("ballista")
    b.add(cyl(X(-7.2, 2.2), X(7.6, 2.2), 1.3, 0.2))                             # tube 2.6 mm
    b.add(round_cone(X(-8.4, 2.2), X(-7.0, 2.2), 1.6, 1.3).clip(xcap(-8.4, -1)))  # venturi, flat face
    b.cut(cyl(X(-9.4, 2.2), X(-7.6, 2.2), 1.2))                                 # venturi cup (0.4 rim)
    b.add(cyl(X(7.3, 2.2), X(8.2, 2.2), 1.5, 0.2))                              # muzzle ring
    b.cut(cyl(X(7.4, 2.2), X(8.6, 2.2), 1.15))
    b.add(round_cone(X(7.3, 2.2), X(8.1, 2.2), 0.8, 0.32))                       # rocket nose
    for x in (-5.4, -1.4, 4.6):
        b.add(cyl(X(x, 2.2), X(x + 0.5, 2.2), 1.45, 0.12))                       # bands
    ring_grooves(b, [-6.4, 6.2], 2.2, 1.3)
    b.add(box((0.3, 0, 0.8), (0.9, 0.6, 0.45), I3, 0.2))                         # grip mount
    b.add(box((3.2, 0, 0.8), (0.6, 0.6, 0.45), I3, 0.2))
    grip(b, rake=12)
    trigger(b, zr=0.35)
    b.add(box((3.2, 0, -0.2), (0.42, 0.5, 0.75), rot(RY, -6), 0.18))             # fore grip
    b.add(box((-3.3, 0, 0.95), (1.2, 0.75, 0.4), I3, 0.25), 0.15)                # shoulder pad
    b.add(box((1.4, -1.9, 2.7), (1.1, 0.6, 0.55), I3, 0.18))                     # side optic
    b.cut(box((2.5, -1.9, 2.75), (0.3, 0.2, 0.25), I3, 0.06))                    # optic lens recess (0.4 walls)
    b.add(box((1.4, -1.25, 2.6), (0.5, 0.35, 0.35), I3, 0.1))                    # optic bracket
    b.add(box((6.9, 0, 3.6), (0.22, 0.2, 0.25), I3, 0.06))                       # front sight
    for x in (-5.15, -1.15, 4.85):
        for sd in (-1, 1):
            bolt(b, (x + 0.1, sd * 1.45, 2.2), (0, sd, 0))                        # band screws
    lens(b, (0.6, -2.5, 2.7), (0, -1, 0), R=0.3)                                 # optic rangefinder lens
    for x in (-1.0, 1.6):                                                         # signature: carry handle
        b.add(capsule(X(x, 3.3), X(x, 4.3), 0.3))
    b.add(capsule(X(-1.0, 4.3), X(1.6, 4.3), 0.32))
    b.add(box((-2.3, 0, 3.75), (0.12, 0.4, 0.35), I3, 0.04))                      # rear sight blade
    b.cut(box((-2.3, 0, 4.1), (0.3, 0.24, 0.15)))                                 # sight notch 0.48
    for xa, xb in ((-6.0, -5.4), (-4.9, -1.4), (-0.9, 4.6)):                       # M4: side strakes, band to band
        for sd in (-1, 1):
            b.add(box(((xa + xb) / 2, sd * 1.3, 2.2), ((xb - xa) / 2, 0.15, 0.2), I3, 0.04))
    b.add(box((5.7, 0, 0.75), (0.75, 0.55, 0.4), I3, 0.12))                       # M4: fire-control box under the muzzle
    lens(b, (6.45, 0, 0.75), (1, 0, 0), R=0.3)
    for sd in (-1, 1):
        bolt(b, (5.25, sd * 0.55, 0.75), (0, sd, 0))
        bolt(b, (6.15, sd * 0.55, 0.75), (0, sd, 0))
    return b


# ------------------------------------------------------------------------------------------------ blades, tools, ordnance
def misericorde():
    """VW2-13 'Misericorde' combat knife: clip-point blade with a fuller and spine notches (edge tapers to a 0.4 mm
    rounded flat), angled guard, ribbed grip, glass-breaker pommel. Grip along z, origin = grip centre."""
    b = Build("misericorde")
    b.add(box((0, 0, 0), (0.42, 0.4, 1.2), I3, 0.2))                             # grip core
    for z in (-0.41, 0.45):
        b.add(box((0, 0, z), (0.52, 0.5, 0.15), I3, 0.08))                       # grip ribs (0.56 mm gaps)
    b.add(box((0, 0, -1.4), (0.58, 0.52, 0.28), I3, 0.15))                       # pommel
    b.add(round_cone(v3(0, 0, -1.55), v3(0, 0, -2.0), 0.4, 0.22))               # glass breaker
    b.add(box((0.15, 0, 1.38), (1.15, 0.55, 0.22), rot(RY, -8), 0.12))           # guard
    blade = box((0, 0, 3.65), (0.78, 0.5, 2.3), I3, 0.22)                        # root sunk into the guard
    tip = Shape(lambda Q: (Q[:, 2] - 6.0) + 0.85 * (Q[:, 0] + 0.2), (-9, -9, -9), (9, 9, 9))
    clip_ = Shape(lambda Q: (Q[:, 2] - 6.4) - 1.6 * (Q[:, 0] + 0.1), (-9, -9, -9), (9, 9, 9))
    bev = Shape(lambda Q: np.abs(Q[:, 1]) - 0.5 + 0.2 * np.clip(Q[:, 0] + 0.6, 0, None), (-9, -9, -9), (9, 9, 9))
    b.add(blade.clip(tip, clip_, bev))
    b.cut(box((-0.2, 0, 3.4), (0.24, 0.68, 1.35), I3, 0.1).clip(
        Shape(lambda Q: 0.25 - np.abs(Q[:, 1]), (-9, -9, -9), (9, 9, 9))))       # fuller, both faces (0.5 core)
    for z in spaced(2.3, 3.9, 0.8):
        b.cut(box((-0.78, 0, z), (0.24, 0.7, 0.24), rot(RY, 45), 0.04))          # spine notches
    return b


def crowbill():
    """VW2-14 'Crowbill' breaching tool: haft with a ribbed wrap, hammer face with a cross-hatched striker, curved pry
    beak, langets. Haft along z, origin = grip centre."""
    b = Build("crowbill")
    b.add(cyl(v3(0, 0, -2.0), v3(0, 0, 6.6), 0.5, 0.12))                       # haft 1.0 mm
    for z in spaced(-1.4, 1.4, 0.9):
        b.add(cyl(v3(0, 0, z - 0.21), v3(0, 0, z + 0.21), 0.64, 0.08))           # wrap ribs (0.42 thick)
    b.add(cyl(v3(0, 0, -2.45), v3(0, 0, -1.9), 0.75, 0.15))                     # pommel cap
    b.add(box((0.2, 0, 7.15), (1.1, 0.72, 0.75), I3, 0.2))                       # head block
    b.add(cyl(v3(1.2, 0, 7.15), v3(2.35, 0, 7.15), 0.8, 0.15))                   # hammer
    for t in (0.0,):
        b.cut(box((2.35, 0, 7.15 + t), (0.2, 0.9, 0.23)))                        # striker hatching
        b.cut(box((2.35, t, 7.15), (0.2, 0.23, 0.9)))
    pts = [v3(-0.7, 0, 7.3), v3(-1.8, 0, 7.4), v3(-2.9, 0, 6.9), v3(-3.6, 0, 6.0)]
    b.add(tube(pts, 0.62, 0.32))                                                  # pry beak
    for s in (-1, 1):
        b.add(box((0, s * 0.5, 5.6), (0.42, 0.18, 0.95), I3, 0.08))              # langets
    vline(b, 0.2, 6.6, 7.7, 0.72, w=0.35, d=0.2)
    return b


def cinder():
    """VW2-15 'Cinder' fragmentation grenade: segmented body, fuze head, spoon lever, pull ring. Flat base at z = 0."""
    b = Build("cinder")
    b.add(cyl(v3(0, 0, 0.0), v3(0, 0, 2.0), 1.0, 0.3))
    for z in (0.55, 1.45):                                                       # raised fragmentation bands
        b.add(cyl(v3(0, 0, z - 0.17), v3(0, 0, z + 0.17), 1.12, 0.06))
    for a in range(0, 360, 60):                                                  # raised segment ribs (no crossing cuts)
        t = math.radians(a + 30)
        b.add(box((1.0 * math.cos(t), 1.0 * math.sin(t), 1.0), (0.12, 0.17, 0.8), rot(Z, a + 30), 0.05))
    b.add(cyl(v3(0, 0, 1.9), v3(0, 0, 2.55), 0.55, 0.12))                       # fuze head
    b.add(box((1.1, 0, 1.4), (0.21, 0.36, 0.95), rot(RY, -5), 0.08), 0.12)       # spoon lever (0.42)
    b.add(box((0.55, 0, 2.45), (0.4, 0.34, 0.21), I3, 0.06))
    b.add(torus(v3(-0.25, -0.75, 2.35), RX, 0.45, 0.2))                          # pull ring (0.4 wire, 0.5 mm eye)
    return b


def petard():
    """VW2-16 'Petard' breaching charge: linear shaped-charge block with a raised V ridge, detonator box with a cable
    stub, arming key, top pad marks, strap channels. Lies flat, base at z = 0."""
    b = Build("petard")
    b.add(box((0, 0, 0.5), (2.1, 1.4, 0.5), I3, 0.2))
    b.add(box((0, 0, 1.0), (1.95, 0.3, 0.3), rot(RX, 45), 0.06).clip(
        Shape(lambda Q: 0.95 - Q[:, 2], (-9, -9, -9), (9, 9, 9))))                # V ridge
    b.add(box((-1.1, 0.75, 1.25), (0.6, 0.45, 0.35), I3, 0.12))                  # detonator
    b.add(cyl(v3(-1.7, 0.75, 1.25), v3(-2.6, 0.75, 1.25), 0.3, 0.08))            # cable stub
    b.add(cyl(v3(-0.85, 0.75, 1.55), v3(-0.85, 0.75, 1.85), 0.22, 0.05))         # arming key
    for x in (-1.5, 1.5):
        for y in (-0.8, 0.8):
            if not (x < 0 and y > 0):
                b.cut(box((x, y, 1.0), (0.3, 0.25, 0.12), I3, 0.05))             # pad marks
    for x in (-0.9, 0.9):
        b.cut(box((x, 0, 0.5), (0.24, 1.6, 0.18), I3, 0.05))                      # strap channels
    hline(b, -1.8, 1.8, 0.55, 1.4, w=0.35, d=0.2)
    return b


WEAPONS2 = {
    "VW2-01": ("Glaive service rifle", "bullpup service rifle: vented handguard, rail, holo sight, two-port brake", glaive),
    "VW2-02": ("Quarrel carbine", "short bullpup carbine: cooling-window handguard, pronged flash hider", quarrel),
    "VW2-03": ("Bodkin marksman rifle", "bullpup DMR: ported free-float shroud, long barrel, scope, folded bipod", bodkin),
    "VW2-04": ("Ranseur grenadier rifle", "bullpup with under-barrel grenade launcher and ladder sight", ranseur),
    "VW2-05": ("Thresher drum shotgun", "pump shotgun: drum magazine, heat shield, breaching crown, skeleton stock", thresher),
    "VW2-06": ("Rondel PDW", "compact PDW: magazine in the grip, ringed suppressor, holo sight, twin-rod stock", rondel),
    "VW2-07": ("Culverin heavy revolver", "six-shot fluted cylinder, slab barrel with vents, hammer spur", culverin),
    "VW2-08": ("Awl service pistol", "serrated slide, ported compensator, rail slots, sights", awl),
    "VW2-09": ("Partisan LMG", "light machine gun: box magazine, carry handle, perforated jacket, bipod", partisan),
    "VW2-10": ("Arbalest rail rifle", "twin magnetic rails, coil clamps, capacitor drum, big scope", arbalest),
    "VW2-11": ("Censer plasma projector", "plasma canister, coolant lines, finned coil, flared emitter", censer),
    "VW2-12": ("Ballista launcher", "shoulder rocket tube: venturi, rocket nose, side optic", ballista),
    "VW2-13": ("Misericorde combat knife", "clip-point fullered blade, spine notches, ribbed grip", misericorde),
    "VW2-14": ("Crowbill breaching tool", "hammer and pry beak on a ribbed haft", crowbill),
    "VW2-15": ("Cinder grenade", "segmented frag grenade, spoon lever, pull ring", cinder),
    "VW2-16": ("Petard breaching charge", "linear shaped charge, detonator, strap channels", petard),
}

# support-hand (fore) fist centre in the weapon frame, for two-handed figure poses (None: one-handed)
FORE = {"VW2-01": (5.9, 0, 0.0), "VW2-02": (4.6, 0, 0.2), "VW2-03": (6.5, 0, 0.6), "VW2-04": (4.1, 0, -1.6),
        "VW2-05": (6.9, 0, 0.95), "VW2-06": (2.4, 0, -0.35), "VW2-07": None, "VW2-08": None, "VW2-09": (6.1, 0, 0.95),
        "VW2-10": (7.0, 0, -0.15), "VW2-11": (6.2, 0, -0.25), "VW2-12": (3.2, 0, -0.2), "VW2-13": None,
        "VW2-14": (0, 0, 4.0), "VW2-15": None, "VW2-16": None}


def weapon(ident):
    return WEAPONS2[ident][2]()


def weapon_shape(ident):
    """One Shape for a figure to hold (weapon frame; move it with .moved(M))."""
    return weapon(ident).shape()


def sculpt(ident, name=None, h=0.05, tris=280_000):
    return weapon(ident).sculpt(h).mesh(name or ident, tris)


def catalogue():
    return {k: v[:2] for k, v in WEAPONS2.items()}
