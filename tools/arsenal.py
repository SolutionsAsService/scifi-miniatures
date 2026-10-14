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

from sdfkit import Sculpt, Shape, capsule, cyl, rbox, rot, round_cone, torus, tube, v3

I3 = np.eye(3)
RY = (0, 1, 0)
RX = (1, 0, 0)
Z = (0, 0, 1)
GRIP_C = v3(0, 0, -0.45)          # VW grip block centre (armory / exosuit)
GRIP_HALF = (0.5, 0.55, 1.0)      # VW grip block half extents (1.0 x 1.1 x 2.0 mm)
LINE_W, LINE_D = 0.35, 0.25       # engraved panel line
SLOT_W, SLOT_D = 0.40, 0.30       # vent slot


class Build:
    """Ordered SDF operations for one weapon."""

    def __init__(self, name):
        self.name, self.ops = name, []

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
def hline(b, x0, x1, z, hy, sides=(-1, 1), w=LINE_W, d=LINE_D):
    """Horizontal engraved panel line on the side faces (|y| = hy) from x0 to x1 at height z."""
    for s in sides:
        b.cut(box(((x0 + x1) / 2, s * hy, z), ((x1 - x0) / 2, d, w / 2)))


def vline(b, x, z0, z1, hy, sides=(-1, 1), w=LINE_W, d=LINE_D, lean=0.0):
    for s in sides:
        b.cut(box((x, s * hy, (z0 + z1) / 2), (w / 2, d, (z1 - z0) / 2), rot(RY, lean)))


def slots(b, xs, z0, z1, hy, sides=(-1, 1), w=SLOT_W, d=SLOT_D, lean=0.0):
    """Vent slots on the side faces, optionally leaning (deg, about y)."""
    for x in xs:
        for s in sides:
            b.cut(box((x, s * hy, (z0 + z1) / 2), (w / 2, d, (z1 - z0) / 2), rot(RY, lean), 0.1))


def spaced(x0, x1, pitch):
    n = max(1, int(math.floor((x1 - x0) / pitch + 1e-6)) + 1)
    mid = (x0 + x1) / 2
    return [mid + (i - (n - 1) / 2) * pitch for i in range(n)]


def rail(b, x0, x1, z, hy=0.55):
    """Accessory rail on a top face at height z: strip z-0.05..z+0.35, teeth to z+0.6 (0.42 mm on a 0.85 pitch)."""
    b.add(box(((x0 + x1) / 2, 0, z + 0.15), ((x1 - x0) / 2, hy, 0.2), I3, 0.06))
    for x in spaced(x0 + 0.3, x1 - 0.3, 0.85):
        b.add(box((x, 0, z + 0.45), (0.21, hy + 0.08, 0.15), I3, 0.05))
    return z + 0.6


def grip(b, x=0.0, z=0.0, rake=14.0, grooves=True):
    """The VW grip block (fits exosuit.fist) raked back; finger grooves on the front strap, side texture grooves."""
    R = rot(RY, rake)
    c = v3(x, 0, z) + GRIP_C
    b.add(box(c, GRIP_HALF, R, 0.22))
    if grooves:
        u, n = R[:, 0], R[:, 2]
        for t in (-0.72, -0.15, 0.42):
            p = c + u * 0.52 + n * t
            b.cut(capsule(p - v3(0, 0.75, 0), p + v3(0, 0.75, 0), 0.19))
        for t in (-0.5, 0.2):
            for s in (-1, 1):
                b.cut(box(c + n * t + v3(0, s * 0.55, 0) - u * 0.08, (0.28, 0.18, 0.17), R, 0.05))
        b.add(box(c - n * 0.92, (0.56, 0.6, 0.14), R, 0.07))         # base cap
    return c


def trigger(b, x=0.0, zr=0.2, reach=1.45):
    """Trigger guard loop (0.6 mm bar) from the grip front to the receiver underside at zr, plus the trigger blade."""
    b.add(capsule(X(x + 0.2, -0.85), X(x + reach, -0.85), 0.3))
    b.add(capsule(X(x + reach, -0.85), X(x + reach + 0.2, zr + 0.15), 0.3))
    b.add(capsule(X(x + 0.82, zr + 0.1), X(x + 0.72, zr - 0.42), 0.2))


def box_mag(b, c, half, rake=0.0, ribs=2, plate=True):
    R = rot(RY, rake)
    c = v3(c)
    b.add(box(c, half, R, 0.22))
    n = R[:, 2]
    if plate:
        b.add(box(c - n * (half[2] - 0.12), (half[0] + 0.12, half[1] + 0.1, 0.2), R, 0.08))
    for t in (np.linspace(-0.45, 0.35, ribs) if ribs > 1 else [0.0]):
        for s in (-1, 1):
            b.cut(box(c + n * t * half[2] + v3(0, s * half[1], 0), (half[0] - 0.28, 0.2, 0.18), R, 0.05))


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
            b.add(box((xr, 0, (z + mount_z) / 2), (0.3, 0.42, (z - mount_z) / 2), I3, 0.1))


def holo(b, x, zb):
    """Holographic sight on a rail top at zb: base, hood with a 0.6 x 0.5 mm window (0.4 mm side walls), emitter."""
    b.add(box((x, 0, zb + 0.22), (0.9, 0.55, 0.3), I3, 0.12))
    b.add(box((x + 0.3, 0, zb + 1.12), (0.45, 0.7, 0.66), I3, 0.15))
    b.cut(box((x + 0.3, 0, zb + 1.2), (0.7, 0.3, 0.25), I3, 0.08))
    b.add(box((x - 0.55, 0, zb + 0.72), (0.3, 0.42, 0.28), I3, 0.1))


def brake(b, x0, x1, z, r, n=2, bore=0.26):
    """Muzzle brake: ported through the sides (0.36 mm ports, >= 0.38 mm lands), bore recess at the front."""
    b.add(cyl(X(x0, z), X(x1, z), r, 0.15))
    for xc in spaced(x0 + 0.45, x1 - 0.45, 0.75)[:n]:
        b.cut(box((xc, 0, z), (0.18, r + 0.2, r * 0.42), I3, 0.06))
    b.cut(cyl(X(x1 - 0.45, z), X(x1 + 0.3, z), bore))


def flash_hider(b, x0, x1, z, r):
    """Pronged flash hider: four prongs (cross slots 0.4 mm wide), bore recess."""
    b.add(cyl(X(x0, z), X(x1, z), r, 0.12))
    L = (x1 - x0) * 0.55
    b.cut(box((x1, 0, z), (L, 0.2, r + 0.2)))
    b.cut(box((x1, 0, z), (L, r + 0.2, 0.2)))
    b.cut(cyl(X(x1 - L, z), X(x1 + 0.3, z), 0.28))


def xcap(x, sign=1):
    """Half-space that trims a round-cone end cap flat at x (keeps the side toward -sign)."""
    return Shape(lambda Q: sign * (Q[:, 0] - x), (-99, -99, -99), (99, 99, 99))


def ring_grooves(b, xs, z, R_, r=0.18, y=0.0):
    for x in xs:
        b.cut(torus(v3(x, y, z), RX, R_, r))


# ------------------------------------------------------------------------------------------------ bullpup family
def _bullpup(b, rear=-3.7, front=4.6, butt=-5.9, top=2.3, mag_x=-2.1, mag_half=(0.95, 0.72, 1.25), rail_x=(-1.9, 3.6)):
    """Shared bullpup receiver (VW2-01..04): receiver, butt, spine, grip, trigger, magazine behind the grip."""
    mid = (rear + front) / 2
    b.add(box((mid, 0, (0.2 + top) / 2), ((front - rear) / 2, 0.95, (top - 0.2) / 2), I3, 0.3))     # receiver
    b.add(box(((butt + rear) / 2 + 0.15, 0, 1.15), ((rear - butt) / 2 + 0.25, 0.9, 1.2), rot(RY, 5), 0.35))  # butt
    b.add(box((butt + 0.15, 0, 1.1), (0.25, 0.97, 1.32), rot(RY, 5), 0.12))                         # butt pad
    b.add(box((mid + 0.4, 0, top + 0.2), ((front - rear) / 2 - 0.5, 0.72, 0.3), I3, 0.12))           # top spine
    zr = rail(b, rail_x[0], rail_x[1], top + 0.45)
    # side detail: ejection port (-y), charging handle, selector, panel lines, butt vents
    b.cut(box((-0.9, -0.95, 1.5), (0.85, 0.22, 0.35), I3, 0.08))
    b.add(box((front - 1.1, -0.98, top - 0.45), (0.38, 0.3, 0.22), I3, 0.1))
    b.add(cyl(v3(-0.25, -0.85, 1.25), v3(-0.25, -1.17, 1.25), 0.28, 0.08))
    hline(b, rear + 0.35, front - 0.35, 0.92, 0.95)
    vline(b, 1.45, 0.45, top - 0.3, 0.95)
    vline(b, rear + 0.25, 0.45, top - 0.3, 0.95)
    slots(b, [butt + 0.95, butt + 1.7], 0.55, 1.85, 0.9, lean=-18)
    grip(b)
    trigger(b, zr=0.2)
    box_mag(b, (mag_x, 0, 0.15 - mag_half[2] + 0.2), mag_half, rake=8, ribs=2)
    b.add(box((mag_x, 0, 0.15), (mag_half[0] + 0.15, mag_half[1] + 0.08, 0.25), rot(RY, 8), 0.1))  # mag well collar
    return zr


def glaive():
    """VW2-01 'Glaive' service rifle: bullpup, vented handguard, rail, holo sight, two-port brake, angled fore grip."""
    b = Build("glaive")
    zr = _bullpup(b)
    b.add(box((6.4, 0, 1.4), (1.95, 0.85, 0.85), I3, 0.3))                       # handguard x 4.45..8.35
    slots(b, spaced(5.1, 7.5, 0.8), 0.95, 1.85, 0.85)
    hline(b, 4.7, 8.1, 0.72, 0.85)
    rail(b, 4.9, 8.0, 2.25, hy=0.5)
    b.add(cyl(X(8.2, 1.45), X(10.2, 1.45), 0.55, 0.1))                          # barrel 1.1 mm
    b.add(box((8.7, 0, 1.45), (0.3, 0.6, 0.62), I3, 0.12))                       # gas block
    brake(b, 9.9, 11.5, 1.45, 0.8)
    holo(b, 0.7, zr)
    b.add(box((5.9, 0, 0.2), (0.45, 0.5, 0.75), rot(RY, -20), 0.2))              # angled fore grip
    return b


def quarrel():
    """VW2-02 'Quarrel' carbine: short bullpup, cut-down handguard with a cooling window, flash hider, short rail."""
    b = Build("quarrel")
    zr = _bullpup(b, rear=-3.3, front=3.7, butt=-5.0, mag_x=-1.9, mag_half=(0.85, 0.68, 1.05), rail_x=(-1.5, 2.9))
    b.add(box((4.9, 0, 1.4), (1.3, 0.82, 0.8), I3, 0.28))                        # handguard x 3.6..6.2
    b.cut(box((4.95, 0, 1.45), (0.75, 0.95, 0.28), I3, 0.12))                     # cooling window (through)
    b.add(cyl(X(5.5, 1.45), X(7.2, 1.45), 0.55, 0.1))
    flash_hider(b, 7.0, 8.3, 1.45, 0.72)
    holo(b, 0.4, zr)
    b.add(box((4.6, 0, 0.35), (0.42, 0.48, 0.55), rot(RY, -12), 0.18))           # stub fore grip
    return b


def bodkin():
    """VW2-03 'Bodkin' marksman rifle (DMR): long free-float shroud with staggered vent ports, long barrel,
    big scope, cheek riser, folded bipod."""
    b = Build("bodkin")
    zr = _bullpup(b, rear=-3.8, front=4.8, butt=-6.2, mag_half=(0.9, 0.7, 1.0), rail_x=(-2.4, 4.2))
    b.add(box((-4.7, 0, 2.55), (1.2, 0.7, 0.28), I3, 0.15))                      # cheek riser
    b.add(cyl(X(4.6, 1.45), X(10.4, 1.45), 0.85, 0.2))                          # shroud 1.7 mm
    for i, x in enumerate(spaced(5.3, 9.7, 0.7)):
        z = 1.75 if i % 2 else 1.15
        for s in (-1, 1):
            b.cut(cyl(v3(x, s * 1.2, z), v3(x, s * 0.55, z), 0.21))
    b.add(cyl(X(10.2, 1.45), X(14.4, 1.45), 0.52, 0.1))                         # barrel 1.04 mm
    brake(b, 14.0, 15.8, 1.45, 0.8)
    scope(b, -2.0, 4.6, zr + 1.05, r=0.58, bell=0.9, mount_z=zr - 0.05, rings=(-0.6, 2.6))
    for s in (-1, 1):                                                            # folded bipod legs
        b.add(capsule(v3(7.3, s * 0.45, 0.5), v3(10.0, s * 0.45, 0.5), 0.3))
    b.add(box((10.0, 0, 0.75), (0.4, 0.75, 0.45), I3, 0.15))                     # bipod hinge block
    return b


def ranseur():
    """VW2-04 'Ranseur' grenadier rifle: bullpup service rifle with an under-barrel launcher, ladder sight."""
    b = Build("ranseur")
    _bullpup(b)
    b.add(box((6.2, 0, 1.45), (1.75, 0.85, 0.8), I3, 0.3))                       # handguard x 4.45..7.95
    slots(b, spaced(5.0, 7.4, 0.8), 1.65, 2.1, 0.85)
    b.add(cyl(X(7.8, 1.45), X(10.0, 1.45), 0.55, 0.1))
    brake(b, 9.6, 11.2, 1.45, 0.78)
    b.add(cyl(X(3.4, -0.55), X(8.7, -0.55), 0.95, 0.25))                        # launcher tube 1.9 mm
    b.cut(cyl(X(8.15, -0.55), X(9.0, -0.55), 0.62))                             # launcher bore (rim 0.33)
    ring_grooves(b, [4.4, 7.6], -0.55, 0.95)
    b.add(box((3.6, 0, -0.35), (0.55, 0.9, 0.75), I3, 0.2))                      # breech block
    b.add(box((4.5, 0, 0.35), (1.0, 0.6, 0.3), I3, 0.12))                        # mount to handguard
    b.add(box((4.1, 0, -1.7), (0.42, 0.5, 0.6), rot(RY, 10), 0.18))              # launcher trigger grip
    b.add(box((6.4, -1.0, 1.55), (0.55, 0.22, 0.7), I3, 0.1))                    # ladder sight frame
    b.cut(box((6.4, -1.1, 1.62), (0.25, 0.4, 0.4), I3, 0.06))
    return b


# ------------------------------------------------------------------------------------------------ shotgun, PDW
def thresher():
    """VW2-05 'Thresher' drum shotgun: pump action, drum magazine, slotted heat shield, breaching crown muzzle,
    skeleton stock, side shell carrier."""
    b = Build("thresher")
    b.add(box((1.7, 0, 1.25), (2.5, 0.95, 1.05), I3, 0.3))                       # receiver x -0.8..4.2
    b.add(box((-3.0, 0, 1.8), (2.6, 0.72, 0.42), rot(RY, -4), 0.2))              # stock comb bar
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
    slots(b, spaced(5.75, 8.05, 0.75), 0.55, 1.3, 0.8, w=0.36, d=0.2)
    b.add(box((7.9, 0, 2.25), (2.7, 0.82, 0.38), I3, 0.18))                      # heat shield
    slots(b, spaced(5.7, 10.1, 0.73), 2.05, 2.45, 0.82, d=0.24)
    b.add(cyl(X(10.6, 1.75), X(11.9, 1.75), 0.92, 0.15))                        # breaching crown
    b.cut(box((11.9, 0, 1.75), (0.32, 0.22, 1.1)))
    b.cut(box((11.9, 0, 1.75), (0.32, 1.1, 0.22)))
    b.cut(cyl(X(11.3, 1.75), X(12.2, 1.75), 0.45))
    b.add(box((10.3, 0, 2.75), (0.22, 0.2, 0.2), I3, 0.06))                      # front sight
    rail(b, -0.3, 3.4, 2.3)
    b.add(box((1.6, -1.05, 1.15), (1.35, 0.2, 0.62), I3, 0.1))                   # shell carrier
    for x in (0.7, 1.6, 2.5):
        b.add(cyl(v3(x, -1.1, 1.15), v3(x, -1.42, 1.15), 0.28, 0.07))
    b.cut(box((3.6, -0.95, 1.6), (0.45, 0.22, 0.3), I3, 0.08))                   # ejection port
    vline(b, 3.95, 0.45, 2.0, 0.95)
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
    for t in (-0.6, 0.0):
        b.cut(capsule(v3(2.85, -0.7, t - 0.3), v3(2.85, 0.7, t - 0.3), 0.18))
    for s in (-1, 1):
        b.add(capsule(v3(-1.6, s * 0.52, 1.45), v3(-3.6, s * 0.52, 1.45), 0.32))  # stock rods
    b.add(box((-3.85, 0, 1.2), (0.25, 0.85, 0.95), I3, 0.12))                    # butt plate
    b.cut(box((0.2, -0.85, 1.4), (0.7, 0.22, 0.3), I3, 0.08))                    # ejection port
    slots(b, spaced(2.0, 3.0, 0.75), 0.6, 1.6, 0.85)
    hline(b, -1.5, 3.1, 0.62, 0.85)
    b.add(box((-1.3, 0, 2.25), (0.4, 0.25, 0.25), I3, 0.08))                     # charging knob
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
    for a in range(0, 360, 60):
        t = math.radians(a)
        p = v3(0, 0.98 * math.cos(t), 1.05 + 0.98 * math.sin(t))
        b.cut(capsule(p + X(0.7, 0), p + X(1.65, 0), 0.25))
    b.add(box((3.75, 0, 1.45), (1.8, 0.52, 0.42), I3, 0.15))                     # slab barrel x 1.95..5.55
    b.add(box((3.4, 0, 1.97), (1.95, 0.25, 0.14), I3, 0.05))                     # top rib
    slots(b, spaced(3.2, 4.7, 0.75), 1.25, 1.7, 0.52, w=0.38, d=0.22, lean=-25)
    b.add(cyl(X(5.4, 1.3), X(5.95, 1.3), 0.5, 0.1))                             # muzzle 1.0 mm
    b.cut(cyl(X(5.6, 1.3), X(6.2, 1.3), 0.22))
    b.add(cyl(X(2.0, 0.72), X(4.2, 0.72), 0.32, 0.08))                          # ejector rod housing
    b.add(box((5.3, 0, 2.15), (0.22, 0.17, 0.2), I3, 0.06))                      # front sight
    b.add(box((-0.4, 0, 2.05), (0.25, 0.42, 0.14), I3, 0.06))                    # rear sight
    b.add(capsule(X(-0.5, 1.6), X(-1.0, 2.15), 0.28))                            # hammer
    grip(b, x=-0.35, z=0.1, rake=22)
    trigger(b, x=-0.2, zr=0.25, reach=1.3)
    vline(b, 0.2, 0.3, 1.7, 0.55, w=0.35, d=0.2)
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
    b.add(box((4.25, 0, 1.35), (0.38, 0.56, 0.52), I3, 0.15))                    # compensator
    b.cut(box((4.3, 0, 1.87), (0.18, 0.28, 0.2), I3, 0.05))                      # comp port
    b.cut(cyl(X(4.35, 1.3), X(4.9, 1.3), 0.22))
    for x in spaced(2.1, 3.0, 0.85):                                             # rail slots under the frame
        b.cut(box((x, 0, 0.18), (0.2, 0.6, 0.15), I3, 0.05))
    b.add(box((-0.55, 0, 1.92), (0.26, 0.45, 0.14), I3, 0.06))                   # rear sight
    b.cut(box((-0.55, 0, 2.05), (0.4, 0.16, 0.14)))                              # sight notch
    b.add(box((3.55, 0, 1.92), (0.2, 0.18, 0.14), I3, 0.06))                     # front sight
    b.add(box((-0.75, 0, 0.75), (0.28, 0.38, 0.3), rot(RY, 30), 0.12))           # beavertail
    grip(b, rake=18)
    trigger(b, zr=0.2, reach=1.3)
    hline(b, -0.6, 3.6, 1.0, 0.5, w=0.32, d=0.15)
    return b


# ------------------------------------------------------------------------------------------------ support weapons
def partisan():
    """VW2-09 'Partisan' light machine gun: box magazine, feed cover with rail, carry handle over a perforated barrel
    jacket, ribbed handguard, folded bipod, skeleton butt."""
    b = Build("partisan")
    b.add(box((1.6, 0, 1.4), (3.4, 1.0, 1.2), I3, 0.32))                         # receiver x -1.8..5.0
    b.add(box((1.4, 0, 2.85), (2.5, 0.85, 0.35), I3, 0.15))                      # feed cover
    b.add(cyl(v3(-1.0, -0.9, 2.8), v3(-1.0, 0.9, 2.8), 0.35, 0.08))             # cover hinge
    rail(b, -0.4, 3.4, 3.15, hy=0.5)
    b.add(box((-4.1, 0, 1.55), (2.45, 0.85, 1.0), rot(RY, -3), 0.3))             # butt x -6.5..-1.7
    b.cut(box((-4.0, 0, 1.55), (1.2, 1.0, 0.36), rot(RY, -3), 0.15))             # lightening window
    b.add(box((-6.6, 0, 1.45), (0.25, 0.9, 1.15), I3, 0.1))
    grip(b, rake=16)
    trigger(b, zr=0.2)
    box_mag(b, (3.0, 0, -1.0), (1.5, 0.85, 1.3), ribs=3)
    b.add(box((3.0, 0, 0.25), (1.65, 0.95, 0.2), I3, 0.08))
    b.add(cyl(X(4.8, 1.6), X(11.0, 1.6), 0.95, 0.2))                            # barrel jacket 1.9 mm
    for x in spaced(7.5, 10.3, 0.8):
        for z, dx in ((1.2, 0.0), (2.0, 0.4)):
            for s in (-1, 1):
                b.cut(cyl(v3(x + dx, s * 1.25, z), v3(x + dx, s * 0.55, z), 0.22))
    b.add(box((6.1, 0, 0.95), (1.2, 0.85, 0.55), I3, 0.22))                      # handguard
    slots(b, spaced(5.4, 6.8, 0.7), 0.6, 1.3, 0.85, w=0.36, d=0.2)
    for x in (6.6, 8.6):                                                         # carry handle posts
        b.add(capsule(X(x, 2.3), X(x, 3.6), 0.33))
    b.add(capsule(X(6.6, 3.6), X(8.6, 3.6), 0.36))
    b.add(cyl(X(10.8, 1.6), X(12.4, 1.6), 0.55, 0.1))
    flash_hider(b, 12.1, 13.5, 1.6, 0.75)
    for s in (-1, 1):
        b.add(capsule(v3(7.4, s * 0.5, 0.55), v3(10.5, s * 0.5, 0.55), 0.3))
    b.add(box((10.6, 0, 0.9), (0.4, 0.8, 0.5), I3, 0.15))
    b.cut(box((0.2, -1.0, 1.6), (0.9, 0.22, 0.35), I3, 0.08))                    # ejection port
    b.add(box((3.8, -1.05, 1.9), (0.4, 0.3, 0.22), I3, 0.1))                     # charging handle
    hline(b, -1.5, 4.7, 0.75, 1.0)
    vline(b, 2.3, 0.45, 2.3, 1.0)
    return b


def arbalest():
    """VW2-10 'Arbalest' rail rifle: twin magnetic rails bound by four coil clamps, capacitor drum stock, big scope,
    power cable, fore grip under the rails."""
    b = Build("arbalest")
    b.add(box((1.5, 0, 1.4), (3.5, 1.0, 1.2), I3, 0.32))                         # receiver x -2.0..5.0
    b.add(cyl(X(-5.0, 1.5), X(-1.8, 1.5), 1.2, 0.3))                            # capacitor drum
    ring_grooves(b, spaced(-4.3, -2.5, 0.6), 1.5, 1.2)
    b.add(box((-5.15, 0, 1.3), (0.35, 0.95, 1.35), I3, 0.12))                    # butt plate
    for zc in (0.85, 2.15):
        b.add(box((11.3, 0, zc), (6.5, 0.6, 0.35), I3, 0.12))                    # rails x 4.8..17.8
    for x in (7.0, 9.9, 12.8, 15.7):
        b.add(box((x, 0, 1.5), (0.42, 0.95, 1.2), I3, 0.2))                      # coil clamps
        vline(b, x, 0.6, 2.4, 0.95, w=0.35, d=0.2)
    b.add(box((18.0, 0, 1.5), (0.45, 0.85, 1.15), I3, 0.2))                      # muzzle block
    b.cut(cyl(X(17.9, 1.5), X(18.7, 1.5), 0.3))
    zr = rail(b, -1.2, 4.2, 2.6)
    scope(b, -1.6, 6.2, zr + 1.15, r=0.62, bell=0.95, mount_z=zr - 0.05, rings=(-0.1, 3.4))
    b.add(tube([v3(-3.2, -1.05, 2.45), v3(-1.6, -1.3, 2.55), v3(0.9, -1.1, 2.3)], 0.28))  # power cable
    slots(b, spaced(1.6, 4.2, 0.75), 0.75, 2.0, 1.0)
    grip(b, rake=16)
    trigger(b, zr=0.2)
    b.add(box((7.0, 0, -0.15), (0.45, 0.5, 0.8), rot(RY, 10), 0.2))              # fore grip
    hline(b, -1.7, 4.7, 0.7, 1.0)
    return b


def censer():
    """VW2-11 'Censer' plasma projector: plasma canister over the housing, coolant lines, finned focusing coil,
    flared emitter with a recessed electrode."""
    b = Build("censer")
    b.add(box((1.0, 0, 1.4), (3.5, 1.05, 1.2), I3, 0.5))                         # housing x -2.5..4.5
    b.add(cyl(X(-2.6, 3.35), X(1.5, 3.35), 0.85, 0.25))                         # canister
    ring_grooves(b, [-1.6, -0.6, 0.4], 3.35, 0.85)
    b.add(box((-0.55, 0, 2.6), (1.4, 0.55, 0.3), I3, 0.12))                      # canister cradle
    b.add(cyl(X(4.3, 1.4), X(8.6, 1.4), 1.0, 0.2))                              # coil body
    for x in spaced(5.0, 7.9, 0.8):
        b.add(cyl(X(x - 0.2, 1.4), X(x + 0.2, 1.4), 1.38, 0.1))                  # heat-sink fins
    b.add(round_cone(X(8.4, 1.4), X(9.9, 1.4), 0.85, 1.15).clip(xcap(9.9)))      # emitter flare, flat face
    b.cut(cyl(X(9.3, 1.4), X(10.6, 1.4), 0.8))                                  # emitter cup (0.35 rim)
    b.add(cyl(X(9.0, 1.4), X(9.85, 1.4), 0.35, 0.1))                            # electrode
    for s in (-1, 1):
        b.add(tube([v3(1.5, s * 0.45, 3.35), v3(3.0, s * 0.95, 3.0), v3(4.6, s * 0.95, 2.25)], 0.27))  # coolant lines
    slots(b, spaced(0.6, 3.6, 0.75), 0.75, 1.95, 1.05, lean=15)
    hline(b, -2.1, 4.1, 0.62, 1.05)
    grip(b, rake=16)
    trigger(b, zr=0.2)
    b.add(box((6.2, 0, -0.25), (0.45, 0.5, 0.8), rot(RY, -8), 0.2))              # fore handle
    b.add(box((-2.85, 0, 1.3), (0.4, 0.9, 1.0), I3, 0.2))                        # rear cap
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
    b.add(box((-3.5, 0, 0.95), (1.4, 0.75, 0.4), I3, 0.25))                      # shoulder pad
    b.add(box((1.4, -1.9, 2.7), (1.1, 0.45, 0.55), I3, 0.18))                    # side optic
    b.cut(box((2.5, -1.9, 2.75), (0.3, 0.27, 0.3), I3, 0.06))                    # optic lens recess
    b.add(box((1.4, -1.25, 2.6), (0.5, 0.35, 0.35), I3, 0.1))                    # optic bracket
    b.add(box((6.4, 0, 3.6), (0.22, 0.2, 0.25), I3, 0.06))                       # front sight
    return b


# ------------------------------------------------------------------------------------------------ blades, tools, ordnance
def misericorde():
    """VW2-13 'Misericorde' combat knife: clip-point blade with a fuller and spine notches (edge tapers to a 0.4 mm
    rounded flat), angled guard, ribbed grip, glass-breaker pommel. Grip along z, origin = grip centre."""
    b = Build("misericorde")
    b.add(box((0, 0, 0), (0.42, 0.4, 1.2), I3, 0.2))                             # grip core
    for z in (-0.8, -0.25, 0.3, 0.85):
        b.add(box((0, 0, z), (0.52, 0.5, 0.17), I3, 0.08))                       # grip ribs
    b.add(box((0, 0, -1.4), (0.58, 0.52, 0.28), I3, 0.15))                       # pommel
    b.add(round_cone(v3(0, 0, -1.55), v3(0, 0, -2.0), 0.4, 0.22))               # glass breaker
    b.add(box((0.15, 0, 1.38), (1.15, 0.55, 0.22), rot(RY, -8), 0.12))           # guard
    blade = box((0, 0, 3.75), (0.78, 0.5, 2.2), I3, 0.22)
    tip = Shape(lambda Q: (Q[:, 2] - 6.0) + 0.85 * (Q[:, 0] + 0.2), (-9, -9, -9), (9, 9, 9))
    clip_ = Shape(lambda Q: (Q[:, 2] - 6.4) - 1.6 * (Q[:, 0] + 0.1), (-9, -9, -9), (9, 9, 9))
    bev = Shape(lambda Q: np.abs(Q[:, 1]) - 0.5 + 0.2 * np.clip(Q[:, 0] + 0.6, 0, None), (-9, -9, -9), (9, 9, 9))
    b.add(blade.clip(tip, clip_, bev))
    b.cut(box((-0.32, 0, 3.4), (0.18, 0.68, 1.35), I3, 0.1).clip(
        Shape(lambda Q: 0.25 - np.abs(Q[:, 1]), (-9, -9, -9), (9, 9, 9))))       # fuller, both faces (0.5 core)
    for z in spaced(2.3, 3.9, 0.8):
        b.cut(box((-0.78, 0, z), (0.18, 0.7, 0.18), rot(RY, 45), 0.04))          # spine notches
    return b


def crowbill():
    """VW2-14 'Crowbill' breaching tool: haft with a ribbed wrap, hammer face with a cross-hatched striker, curved pry
    beak, langets. Haft along z, origin = grip centre."""
    b = Build("crowbill")
    b.add(cyl(v3(0, 0, -2.0), v3(0, 0, 6.6), 0.5, 0.12))                       # haft 1.0 mm
    for z in spaced(-1.4, 1.4, 0.7):
        b.add(cyl(v3(0, 0, z - 0.17), v3(0, 0, z + 0.17), 0.64, 0.08))           # wrap ribs
    b.add(cyl(v3(0, 0, -2.45), v3(0, 0, -1.9), 0.75, 0.15))                     # pommel cap
    b.add(box((0.2, 0, 7.15), (1.1, 0.72, 0.75), I3, 0.2))                       # head block
    b.add(cyl(v3(1.2, 0, 7.15), v3(2.35, 0, 7.15), 0.8, 0.15))                   # hammer
    for t in (-0.3, 0.3):
        b.cut(box((2.35, 0, 7.15 + t), (0.2, 0.9, 0.17)))                        # striker hatching
        b.cut(box((2.35, t, 7.15), (0.2, 0.17, 0.9)))
    pts = [v3(-0.7, 0, 7.3), v3(-1.8, 0, 7.4), v3(-2.9, 0, 6.9), v3(-3.6, 0, 6.0)]
    b.add(tube(pts, 0.62, 0.32))                                                  # pry beak
    for s in (-1, 1):
        b.add(box((0, s * 0.5, 5.6), (0.42, 0.18, 0.95), I3, 0.08))              # langets
    vline(b, 0.2, 6.6, 7.7, 0.72, w=0.35, d=0.2)
    return b


def cinder():
    """VW2-15 'Cinder' fragmentation grenade: segmented body, fuze head, spoon lever, pull ring. Flat base at z = 0."""
    b = Build("cinder")
    b.add(cyl(v3(0, 0, 0.0), v3(0, 0, 2.0), 1.1, 0.35))
    for z in (0.65, 1.3):
        b.cut(torus(v3(0, 0, z), Z, 1.1, 0.18))
    for a in range(0, 360, 60):
        t = math.radians(a + 30)
        b.cut(box((1.1 * math.cos(t), 1.1 * math.sin(t), 1.0), (0.17, 0.17, 0.7), rot(Z, a + 30), 0.05))
    b.add(cyl(v3(0, 0, 1.9), v3(0, 0, 2.55), 0.55, 0.12))                       # fuze head
    b.add(box((0.9, 0, 1.6), (0.18, 0.36, 0.95), rot(RY, -12), 0.08))            # spoon lever
    b.add(box((0.55, 0, 2.45), (0.4, 0.34, 0.16), I3, 0.06))
    b.add(torus(v3(-0.25, -0.85, 2.3), RX, 0.38, 0.17))                          # pull ring
    return b


def petard():
    """VW2-16 'Petard' breaching charge: linear shaped-charge block with a raised V ridge, detonator box with a cable
    stub, arming key, top pad marks, strap channels. Lies flat, base at z = 0."""
    b = Build("petard")
    b.add(box((0, 0, 0.5), (2.1, 1.4, 0.5), I3, 0.2))
    b.add(box((0, 0, 1.15), (1.95, 0.3, 0.3), rot(RX, 45), 0.06).clip(
        Shape(lambda Q: 0.95 - Q[:, 2], (-9, -9, -9), (9, 9, 9))))                # V ridge
    b.add(box((-1.1, 0.75, 1.25), (0.6, 0.45, 0.35), I3, 0.12))                  # detonator
    b.add(cyl(v3(-1.7, 0.75, 1.25), v3(-2.6, 0.75, 1.25), 0.3, 0.08))            # cable stub
    b.add(cyl(v3(-0.85, 0.75, 1.55), v3(-0.85, 0.75, 1.85), 0.22, 0.05))         # arming key
    for x in (-1.5, 1.5):
        for y in (-0.95, 0.95):
            if not (x < 0 and y > 0):
                b.cut(box((x, y, 1.0), (0.3, 0.25, 0.12), I3, 0.05))             # pad marks
    for x in (-0.9, 0.9):
        b.cut(box((x, 0, 0.5), (0.2, 1.6, 0.18), I3, 0.05))                      # strap channels
    hline(b, -1.8, 1.8, 0.3, 1.4, w=0.35, d=0.2)
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
