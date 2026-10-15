"""Arsenal 3: the VW3 series (chunky heroic rifles, carbines, shotgun, SMG, pistols), the VB3 power blades and the
VHW heavy weapons of the Aster Compact Vigilant line. Original designs: no outline, logo or mark is taken from an
existing game, film, stock sheet or miniature range.

This module is additive. tools/armory.py (VW/VA/VH), tools/arsenal.py (VW2) and every package built from them are
untouched; arsenal3 only imports their shared helpers (Build, the VW grip block, the trigger guard).

Registries (all in millimetres at print scale, 30 mm heroic = 1:56, z up):
- WEAPONS3 VW3-01..14  guns. Weapon frame as armory/arsenal: x toward the muzzle, y to the weapon's left side, origin =
  the main grip / fist centre. Every pistol grip is the VW grip block (centre (0, 0, -0.45), 1.0 x 1.1 x 2.0 mm) raked
  10-18 deg back, so exosuit.fist() closes over it exactly as on VW-01..07 and VW2.
- BLADES3  VB3-01..06  power blades. Grip along +z (blade up), origin = grip centre; the grip core is 1.0 mm round with
  1.26 mm rings, inside the exosuit.fist() gauntlet (1.7 x 2.0 x 2.1 mm) like VW-08 / VW2-13.
  Every cutting edge is a FLAT >= 0.5 mm wide (brief: >= 0.4 mm), never a knife edge.
- HEAVY3   VHW-01..03  heavy weapons, weapon frame as WEAPONS3 (origin = rear grip); VHW-01 also has the ammo drum
  backpack drum_pack() in the exosuit backpack frame (front face y = 0, 2.0 mm D-flat peg toward -y).
FORE3 / HANDLE3 give the support-hand fist centres for two-handed poses (weapon frame).

VW3 detail floor (MSLA resin; chunkier than VW2 so details survive a wash and a drybrush at arm's length):
engraved panel seams 0.45 wide x 0.3 deep; vent slots 0.45 wide x 0.32 deep with lands >= 0.5; rail teeth 0.5 wide on a
1.0 pitch, 0.3 proud; raised plates 0.2 proud; bolts 0.5 diameter; barrels >= 1.2 mm; bores and lens recesses 0.35-0.6
deep with rims >= 0.4; bars (guards, stock struts, handles) >= 0.64 mm; through-windows keep >= 0.6 mm lands.
Receivers are 2.0-2.24 mm wide and 2.6-3.4 mm deep (VW2: 1.9 x 2.3), overall lengths 17-23 mm for long arms.
"""
from __future__ import annotations

import math

import numpy as np

from arsenal import Build, grip, spaced, xcap
from exosuit import PEG_PACK
from sdfkit import Sculpt, Shape, bezier, capsule, cyl, d_peg, rbox, rot, round_cone, sphere, torus, tube, unit, v3

I3 = np.eye(3)
RX, RY, RZ = (1, 0, 0), (0, 1, 0), (0, 0, 1)
SEAM_W, SEAM_D = 0.45, 0.30
SLOT_W, SLOT_D = 0.45, 0.32
TOOTH_W, TOOTH_P, TOOTH_H = 0.5, 1.0, 0.3


def box(c, half, R=I3, r=0.0):
    return rbox(v3(c), half, R, r)


def P(x, z, y=0.0):
    return v3(x, y, z)


def grip3(b, rake=14.0):
    """VW3 grip: exactly the VW grip block (fits exosuit.fist) via arsenal.grip(grooves=False), with VW3 texture:
    two front finger grooves and side grip panels inset >= 0.35 mm from every edge (the VW2 side grooves end 0.07 mm
    from the block's back edge - R1 finding), and the base cap."""
    c = grip(b, rake=rake, grooves=False)
    R = rot(RY, rake)
    u, n = R[:, 0], R[:, 2]
    for t in (-0.05, 0.5):
        p = c + u * 0.55 + n * t
        b.cut(capsule(p - v3(0, 0.8, 0), p + v3(0, 0.8, 0), 0.18))
    for s in (-1, 1):
        b.cut(box(c + n * (-0.15) + v3(0, s * 0.55, 0), (0.15, 0.12, 0.5), R, 0.06))           # side panel recess
    b.add(box(c - n * 0.92, (0.56, 0.6, 0.14), R, 0.07))                                        # base cap
    return c


def trigger3(b, x=0.0, zr=0.2, reach=1.35):
    """Trigger guard (0.64 mm bar) from low on the grip front to the receiver at zr, trigger blade 0.6 mm with a
    >= 0.35 mm gap to the guard (VW2's 0.4 mm blade is below the resin floor - R1 finding)."""
    zg = -1.05
    b.add(capsule(P(x + 0.2, zg), P(x + reach, zg), 0.32))
    b.add(capsule(P(x + reach, zg), P(x + reach + 0.2, zr + 0.15), 0.32))
    b.add(capsule(P(x + 0.8, zr + 0.15), P(x + 0.72, zr - 0.2), 0.3))


def open_slivers(g, r=0.24, smooth=0.8):
    """Morphological opening of the Sculpt's solid by a ball of radius r (mm), applied in place to the distance grid.
    Afterwards every surface point lies on an inscribed ball of radius r, so an inward ray (the checker's wall measure)
    stays in material for >= 2r: fins, lips and acute wedges thinner than 2r are removed, convex edges round to r.
    Only voxels within 3 of removed material change (max of the original field and an EDT field of the opened solid,
    lightly smoothed). Returns the removed volume in mm3. (3dada M6; never a mesh decimation.)"""
    from scipy import ndimage as ndi
    D = g.D
    M = D < 0
    rv = r / g.h
    k = int(math.ceil(rv))
    ax = np.arange(-k, k + 1)
    ball = (ax[:, None, None] ** 2 + ax[None, :, None] ** 2 + ax[None, None, :] ** 2) <= rv * rv + 1e-9
    O = ndi.binary_opening(M, structure=ball)
    R = M & ~O
    removed = float(R.sum()) * g.h ** 3
    if not R.any():
        return 0.0
    near = ndi.binary_dilation(R, iterations=3)
    idx = np.argwhere(near)
    pad = k + 8
    lo = np.maximum(idx.min(axis=0) - pad, 0)
    hi = np.minimum(idx.max(axis=0) + pad + 1, np.array(D.shape))
    sl = tuple(slice(lo[i], hi[i]) for i in range(3))
    Ob = O[sl]
    S = np.where(Ob, -(ndi.distance_transform_edt(Ob) - 0.5), ndi.distance_transform_edt(~Ob) - 0.5) * g.h
    if smooth:
        S = ndi.gaussian_filter(S, smooth)
    Db = D[sl]
    D[sl] = np.where(near[sl], np.maximum(Db, S.astype(Db.dtype)), Db)
    return removed


# ================================================================================================ detail helpers
def block(b, x0, x1, z0, z1, hy, r=0.3, chamfer=0.0):
    """Boxy receiver mass from x0..x1, z0..z1, half width hy; optional 45 deg chamfer on the two top long edges."""
    s = box(((x0 + x1) / 2, 0, (z0 + z1) / 2), ((x1 - x0) / 2, hy, (z1 - z0) / 2), I3, r)
    if chamfer:
        s = s.clip(*[Shape(lambda Q, sg=sg: ((Q[:, 1] * sg - (hy - chamfer)) + (Q[:, 2] - z1)) / math.sqrt(2),
                           (-99,) * 3, (99,) * 3) for sg in (-1, 1)])
    return b.add(s)


def seam_h(b, x0, x1, z, hy, w=SEAM_W, d=SEAM_D):
    """Horizontal engraved panel seam on both side faces (|y| = hy)."""
    for s in (-1, 1):
        b.cut(box(((x0 + x1) / 2, s * hy, z), ((x1 - x0) / 2, d, w / 2)))


def seam_v(b, x, z0, z1, hy, w=SEAM_W, d=SEAM_D, lean=0.0):
    for s in (-1, 1):
        b.cut(box((x, s * hy, (z0 + z1) / 2), (w / 2, d, (z1 - z0) / 2), rot(RY, lean)))


def vents(b, xs, z0, z1, hy, w=SLOT_W, d=SLOT_D, lean=0.0):
    for x in xs:
        for s in (-1, 1):
            b.cut(box((x, s * hy, (z0 + z1) / 2), (w / 2, d, (z1 - z0) / 2), rot(RY, lean), 0.1))


def bolts(b, pts, hy, r=0.25, h=0.22, sides=(-1, 1)):
    for x, z in pts:
        for s in sides:
            b.add(cyl(v3(x, s * (hy - 0.1), z), v3(x, s * (hy + h), z), r, 0.08))


def rail(b, x0, x1, z, hy=0.62, keep_out=()):
    """Top rail on a face at height z: strip to z + 0.36, teeth 0.5 wide on a 1.0 pitch to z + 0.66, flush with the
    strip sides; no tooth within 0.3 mm of a keep_out interval (mount bases), so no tooth is left half-buried."""
    b.add(box(((x0 + x1) / 2, 0, z + 0.12), ((x1 - x0) / 2, hy, 0.24), I3, 0.06))
    for x in spaced(x0 + 0.4, x1 - 0.4, TOOTH_P):
        if any(a - 0.55 < x < c + 0.55 for a, c in keep_out):
            continue
        b.add(box((x, 0, z + 0.5), (TOOTH_W / 2, hy, 0.16), I3, 0.05))
    return z + 0.66


def barrel(b, x0, x1, z, r=0.62):
    b.add(cyl(P(x0, z), P(x1, z), r, 0.1))


def bore(b, x, z, r=0.3, depth=0.55):
    b.cut(cyl(P(x - depth, z), P(x + 0.4, z), r))


def brake(b, x0, x1, z, r=0.9, ports=2):
    """Boxy muzzle brake: 0.45 mm ports through the sides, >= 0.5 mm lands, bore recess."""
    b.add(box(((x0 + x1) / 2, 0, z), ((x1 - x0) / 2, r * 0.92, r), I3, 0.22))
    for xc in spaced(x0 + 0.55, x1 - 0.55, 0.95)[:ports]:
        b.cut(box((xc, 0, z), (0.225, r + 0.3, r * 0.38), I3, 0.06))                       # strips >= 0.5 above/below
    bore(b, x1, z, 0.32, 0.5)


def hider(b, x0, x1, z, r=0.88):
    """Pronged flash hider: cross slots 0.45 mm, prongs >= 0.55 mm, bore 0.3."""
    b.add(cyl(P(x0, z), P(x1, z), r, 0.12))
    L = (x1 - x0) * 0.5
    b.cut(box((x1, 0, z), (L, 0.21, r + 0.2)))
    b.cut(box((x1, 0, z), (L, r + 0.2, 0.21)))
    b.cut(cyl(P(x1 - L - 0.2, z), P(x1 + 0.3, z), 0.3))


def can(b, x0, x1, z, r=0.85):
    """Integral suppressor: ringed can, bore recess."""
    b.add(cyl(P(x0, z), P(x1, z), r, 0.2))
    for x in spaced(x0 + 0.8, x1 - 0.8, 0.95):
        b.cut(torus(P(x, z), RX, r, 0.19))
    bore(b, x1, z, 0.3, 0.5)


def mag(b, c, half, rake=0.0, ribs=2, window=False):
    """Separate box magazine: body, floor plate, side ribs (the well collar above reads it as a separate part)."""
    R = rot(RY, rake)
    c = v3(c)
    n = R[:, 2]
    b.add(box(c, half, R, 0.25))
    b.add(box(c - n * (half[2] - 0.14), (half[0] + 0.14, half[1] + 0.1, 0.22), R, 0.08))       # floor plate
    for t in (np.linspace(-0.5, 0.3, ribs) if ribs > 1 else [-0.1]):
        for s in (-1, 1):
            b.cut(box(c + n * t * half[2] + v3(0, s * half[1], 0), (half[0] - 0.3, 0.2, 0.2), R, 0.05))
    if window:   # round-count window strip on the left face
        b.cut(box(c + n * 0.15 * half[2] + v3(0, half[1], 0), (0.24, 0.2, half[2] * 0.4), R, 0.05))


def well(b, c, half, rake=0.0, depth=0.5):
    """Magazine well collar (slightly bigger than the magazine) under the receiver."""
    b.add(box(v3(c), (half[0] + 0.18, half[1] + 0.12, depth / 2), rot(RY, rake), 0.12))


def fgrip(b, x, z_top, length=1.9, rake=-6.0):
    """Vertical fore grip hanging from z_top: 1.0 x 1.1 section (the fist fits), finger grooves, end cap, clamp."""
    R = rot(RY, rake)
    c = v3(x, 0, z_top - length / 2)
    b.add(box(c, (0.5, 0.55, length / 2), R, 0.22))
    b.add(box(c - R[:, 2] * (length / 2 - 0.1), (0.62, 0.64, 0.16), R, 0.08))
    b.add(box(v3(x, 0, z_top - 0.1), (0.7, 0.6, 0.22), I3, 0.08))
    for t in (-0.3, 0.15):
        p = c + R[:, 0] * 0.52 + R[:, 2] * t * length
        b.cut(capsule(p - v3(0, 0.8, 0), p + v3(0, 0.8, 0), 0.19))
    return c


def afgrip(b, x, z_top):
    """Angled fore grip: swept wedge under the handguard with a thumb stop."""
    b.add(box((x, 0, z_top - 0.5), (0.95, 0.55, 0.55), rot(RY, -28), 0.22))
    b.add(box((x - 0.6, 0, z_top - 0.7), (0.35, 0.55, 0.55), rot(RY, 10), 0.18))


def optic(b, x0, x1, zb, hy=0.85, h=1.5, hood=0.0):
    """Integrated optic housing (boxy block on top at zb): front lens recess 0.4 deep with a >= 0.4 rim, rear eyepiece
    recess, side seam and windage knob. Returns its top height."""
    zc = zb + h / 2
    b.add(box(((x0 + x1) / 2, 0, zc), ((x1 - x0) / 2, hy, h / 2), I3, 0.3))
    if hood:
        b.add(box((x1 + hood / 2 - 0.1, 0, zc), (hood / 2 + 0.1, hy + 0.08, h / 2 + 0.08), I3, 0.2))
    xf = x1 + (hood if hood else 0)
    b.cut(box((xf, 0, zc + 0.05), (0.4, hy - 0.46, h / 2 - 0.46), I3, 0.15))                    # front lens (0.46 rim)
    b.cut(box((x0, 0, zc + 0.05), (0.35, hy - 0.48, h / 2 - 0.48), I3, 0.12))                   # eyepiece
    b.add(cyl(v3((x0 + x1) / 2, -hy + 0.1, zc), v3((x0 + x1) / 2, -hy - 0.35, zc), 0.36, 0.08))  # windage knob
    seam_v(b, x0 + 0.75, zb + 0.25, zb + h - 0.25, hy, w=0.4, d=0.25)
    return zb + h


def scope(b, x0, x1, z, r=0.7, bell=1.08, mount_z=None, rings=()):
    """Large telescopic sight: tube, objective bell (0.4 lens recess, >= 0.4 rim), eyepiece, turrets, ring mounts."""
    b.add(cyl(P(x0 + 0.7, z), P(x1 - 1.3, z), r, 0.12))
    b.add(round_cone(P(x1 - 2.2, z), P(x1 - 1.35, z), r, bell - 0.02))
    b.add(cyl(P(x1 - 1.45, z), P(x1, z), bell, 0.18))
    b.add(cyl(P(x0, z), P(x0 + 1.05, z), r + 0.2, 0.14))
    b.cut(cyl(P(x1 - 0.4, z), P(x1 + 0.3, z), bell - 0.46))
    b.cut(cyl(P(x0 - 0.3, z), P(x0 + 0.35, z), r - 0.25))
    xm = x0 + 0.45 * (x1 - x0)
    b.add(cyl(P(xm, z), P(xm, z + r + 0.5), 0.42, 0.1))
    b.add(cyl(P(xm, z), v3(xm, -(r + 0.5), z), 0.4, 0.1))
    for xr in rings:
        b.add(cyl(P(xr - 0.3, z), P(xr + 0.3, z), r + 0.2, 0.1))
        if mount_z is not None:
            b.add(box((xr, 0, (z + mount_z) / 2), (0.34, 0.5, (z - mount_z) / 2), I3, 0.12))


def holo(b, x, zb, hy=0.66):
    """Chunky holographic sight: base, hood with a window (0.45 mm side walls), emitter box."""
    b.add(box((x, 0, zb + 0.1), (1.0, hy, 0.47), I3, 0.12))                                     # base down to the rail strip
    b.add(box((x + 0.35, 0, zb + 1.25), (0.5, hy + 0.15, 0.75), I3, 0.18))
    b.cut(box((x + 0.35, 0, zb + 1.35), (0.8, hy - 0.3, 0.3), I3, 0.08))
    b.add(box((x - 0.6, 0, zb + 0.8), (0.34, hy - 0.1, 0.32), I3, 0.1))


def launcher(b, x0, x1, z, r=1.05, grip_x=None):
    """Under-barrel grenade launcher: tube with a bore recess (0.4 rim), two ring grooves, breech block, opt. grip."""
    b.add(cyl(P(x0, z), P(x1, z), r, 0.25))
    b.cut(cyl(P(x1 - 0.6, z), P(x1 + 0.3, z), r - 0.46))
    for x in (x0 + 1.2, x1 - 1.3):
        b.cut(torus(P(x, z), RX, r, 0.19))
    b.add(box((x0 + 0.35, 0, z + 0.1), (0.6, r - 0.05, r + 0.05), I3, 0.2))
    if grip_x is not None:
        b.add(box((grip_x, 0, z - r - 0.75), (0.5, 0.55, 0.9), rot(RY, 12), 0.2))


def stock_box(b, x0, x1, z0, z1, hy=0.95, window=True):
    """Boxy stock with a through lightening window (>= 0.6 mm lands) and a ribbed butt pad."""
    block(b, x0, x1, z0, z1, hy, 0.3)
    crest(b, x0 + 0.35, x1 - 0.25, z1)                                                            # keel crest on the stock
    if window and (z1 - z0) > 2.0 and (x1 - x0) > 2.0:
        b.cut(box(((x0 + x1) / 2 + 0.2, 0, (z0 + z1) / 2 - 0.1), ((x1 - x0) / 2 - 0.8, hy + 0.3, (z1 - z0) / 2 - 0.75), I3, 0.2))
    b.add(box((x0 - 0.1, 0, (z0 + z1) / 2), (0.28, hy + 0.06, (z1 - z0) / 2 + 0.08), I3, 0.12))
    for z in spaced(z0 + 0.5, z1 - 0.5, 0.95):
        b.cut(box((x0 - 0.38, 0, z), (0.12, hy + 0.2, 0.2), I3, 0.04))


def bipod(b, x0, x1, z, hy=0.55):
    for s in (-1, 1):
        b.add(capsule(v3(x0, s * hy, z), v3(x1, s * hy, z), 0.34))
    b.add(box((x1, 0, z + 0.25), (0.45, hy + 0.3, 0.5), I3, 0.15))


def crest(b, x0, x1, z, w=0.5, h=0.3):
    """Vigil keel crest (M9): a raised 0.5 x 0.3 mm ridge along a top face at height z from x0 to x1, its front end
    swept down like the helm crest's leading edge."""
    L = x1 - x0
    b.add(box(((x0 + x1) / 2 - 0.15, 0, z + h / 2 - 0.05), (L / 2 - 0.15, w / 2, h / 2 + 0.05), I3, 0.12))
    b.add(box((x1 - 0.35, 0, z + h / 2 - 0.12), (0.4, w / 2, h / 2 + 0.05), rot(RY, 28), 0.12))


def chev(b, x, z, hy, size=0.7):
    """Vigil split chevron engraved on both sides: two 0.4 mm strokes in a V, split at the apex."""
    for s in (-1, 1):
        for k in (-1, 1):
            b.cut(box((x + k * 0.42 * size, s * hy, z), (0.48 * size, 0.25, 0.2), rot(RY, k * 35)))


# ================================================================================================ bullpup family
def _bullpup(b, rear=-4.6, front=4.4, butt=-7.4, top=3.2, hy=1.1, mag_x=-2.6, mag_half=(1.05, 0.82, 1.45), chamfer=0.55):
    """Shared chunky bullpup body: faceted receiver, butt with ribbed pad, separate magazine behind the grip, big side
    panel seams, ejection port, butt vent rhythm. Returns the receiver top height."""
    block(b, rear, front, 0.2, top, hy, 0.32, chamfer)
    block(b, butt, rear + 0.3, -0.1, top - 0.25, hy - 0.05, 0.35, chamfer * 0.8)                # butt
    b.add(box((butt - 0.1, 0, (top - 0.35) / 2), (0.3, hy + 0.04, (top + 0.2) / 2), I3, 0.14))  # butt pad
    crest(b, butt + 0.35, rear - 0.1, top - 0.25)                                                # keel crest on the butt
    for z in spaced(0.4, top - 0.7, 0.95):
        b.cut(box((butt - 0.4, 0, z), (0.12, hy + 0.2, 0.2), I3, 0.04))
    seam_v(b, rear + 0.1, 0.5, top - chamfer - 0.4, hy)
    seam_h(b, butt + 0.6, front - 0.4, 1.05, hy)
    seam_v(b, front - 2.6, 1.05, top - chamfer - 0.4, hy)
    vents(b, spaced(butt + 2.1, rear - 0.4, 0.95), 1.45, top - 1.05, hy - 0.05, lean=-15)
    chev(b, butt + 1.05, 1.7, hy - 0.05, size=0.6)                                               # Vigil split chevron
    b.cut(box((-1.0, -hy, 2.0), (0.95, 0.25, 0.42), I3, 0.08))                                   # ejection port (right)
    b.add(box((front - 1.2, -hy - 0.12, top - 0.75), (0.45, 0.3, 0.25), I3, 0.1))               # charging handle
    b.add(cyl(v3(0.55, -hy + 0.1, 1.2), v3(0.55, -hy - 0.3, 1.2), 0.3, 0.08))                # selector (clear of the port)
    grip3(b)
    trigger3(b, zr=0.2)
    mag(b, (mag_x, 0, 0.25 - mag_half[2] + 0.2), mag_half, rake=8, ribs=2, window=True)
    well(b, (mag_x, 0, 0.18), mag_half, rake=8)
    return top


def saker():
    """VW3-01 'Saker' line rifle: chunky bullpup, integrated optic housing, vented handguard with its own rail,
    three-port brake, angled fore grip."""
    b = Build("saker")
    top = _bullpup(b)
    block(b, 4.2, 9.8, 0.55, 2.95, 1.0, 0.3, 0.45)                                               # handguard
    vents(b, spaced(5.2, 9.0, 0.95), 1.7, 2.45, 1.0)
    seam_h(b, 4.6, 9.4, 1.05, 1.0)
    rail(b, 4.6, 9.4, 2.95, hy=0.55)
    optic(b, -2.2, 2.3, top - 0.05, hy=0.88, h=1.55, hood=0.6)
    barrel(b, 9.6, 12.1, 1.75, 0.62)
    b.add(box((10.2, 0, 1.75), (0.32, 0.68, 0.72), I3, 0.12))                                    # gas block
    brake(b, 11.9, 14.2, 1.75, 0.92, ports=2)
    afgrip(b, 7.4, 0.6)
    bolts(b, [(3.6, 0.65), (3.6, 2.35)], 1.1)
    return b


def caliver():
    """VW3-02 'Caliver' marksman bullpup: ported shroud, long barrel, large scope on high rings, cheek riser, bipod."""
    b = Build("caliver")
    top = _bullpup(b, rear=-4.8, front=4.6, butt=-7.8, mag_half=(1.0, 0.8, 1.2))
    b.add(box((-6.0, 0, top + 0.05), (1.4, 0.75, 0.32), I3, 0.15))                               # cheek riser
    zr = rail(b, -2.6, 4.2, top - 0.05, hy=0.6, keep_out=((-1.24, -0.56), (2.56, 3.24)))
    b.add(cyl(P(4.4, 1.8), P(11.4, 1.8), 1.0, 0.22))                                             # shroud 2.0 mm
    for x in spaced(5.4, 10.6, 0.95):
        for s in (-1, 1):
            b.cut(box((x, s * 1.0, 1.8), (0.225, 0.3, 0.5), I3, 0.1))
    barrel(b, 11.2, 15.6, 1.8, 0.6)
    brake(b, 15.2, 17.4, 1.8, 0.88, ports=2)
    scope(b, -2.4, 5.0, zr + 1.3, r=0.72, bell=1.1, mount_z=zr - 0.35, rings=(-0.9, 2.9))
    bipod(b, 7.6, 10.6, 0.7)
    return b


def serpentine():
    """VW3-03 'Serpentine' grenadier bullpup: short handguard over a 2.1 mm under-barrel launcher with its own grip,
    integrated optic, flash hider, side ladder sight."""
    b = Build("serpentine")
    top = _bullpup(b, rear=-4.4, front=4.2, butt=-7.1)
    block(b, 4.0, 8.4, 1.1, 3.0, 1.0, 0.3, 0.45)                                                 # handguard
    vents(b, spaced(4.9, 7.8, 0.95), 1.95, 2.55, 1.0)
    optic(b, -2.0, 1.8, top - 0.05, hy=0.85, h=1.45)
    rail(b, 4.4, 8.0, 3.0, hy=0.55)
    barrel(b, 8.2, 10.6, 2.0, 0.62)
    hider(b, 10.4, 12.0, 2.0, 0.88)
    launcher(b, 3.4, 9.6, -0.15, 1.05, grip_x=4.6)
    b.add(box((6.0, 0, 0.95), (1.6, 0.6, 0.3), I3, 0.12))                                         # launcher mount
    b.add(box((6.6, -1.1, 2.0), (0.6, 0.24, 0.72), I3, 0.1))                                     # ladder sight
    b.cut(box((6.6, -1.2, 2.05), (0.28, 0.4, 0.38), I3, 0.06))
    return b


def minion():
    """VW3-04 'Minion' compact bullpup carbine: integral ringed suppressor, big box optic on a riser, vertical grip."""
    b = Build("minion")
    top = _bullpup(b, rear=-4.0, front=3.8, butt=-6.4, mag_half=(0.95, 0.8, 1.3))
    block(b, 3.6, 6.6, 0.8, 2.85, 1.0, 0.3, 0.4)
    vents(b, spaced(4.4, 6.0, 0.95), 1.55, 2.3, 1.0)
    can(b, 6.4, 11.4, 1.75, 0.95)
    b.add(box((-0.2, 0, top + 0.3), (1.3, 0.55, 0.36), I3, 0.12))                                # optic riser
    optic(b, -1.8, 1.9, top + 0.55, hy=0.92, h=1.7, hood=0.5)
    fgrip(b, 5.1, 0.85)
    return b


# ================================================================================================ conventional family
def _conventional(b, rear=-2.4, front=4.2, top=3.0, hy=1.08, mag_x=1.75, mag_half=(0.92, 0.8, 1.7), mag_rake=-10,
                  chamfer=0.5, curved_mag=False):
    """Shared chunky conventional receiver: magazine in front of the grip, buffer housing at the back, big seams."""
    block(b, rear, front, 0.2, top, hy, 0.32, chamfer)
    b.add(box((rear - 0.7, 0, top - 0.85), (0.9, hy - 0.25, 0.75), I3, 0.25))                    # buffer housing
    seam_h(b, rear + 0.3, front - 0.3, 1.0, hy)
    seam_v(b, rear + 1.6, 1.0, top - chamfer - 0.4, hy)
    seam_v(b, front - 0.55, 0.45, top - chamfer - 0.4, hy)
    b.cut(box((0.2, -hy, 1.95), (0.85, 0.25, 0.4), I3, 0.08))                                     # ejection port
    b.add(box((rear + 0.5, -hy - 0.12, top - 0.55), (0.4, 0.3, 0.22), I3, 0.1))                  # charging handle
    b.add(cyl(v3(-1.45, -hy + 0.1, 1.3), v3(-1.45, -hy - 0.3, 1.3), 0.3, 0.08))               # selector (clear of the port)
    grip3(b, rake=16)
    trigger3(b, zr=0.2, reach=1.3)
    if curved_mag:   # three stacked, increasingly raked segments: a curved magazine
        for t in (0.0, 0.5, 1.0):
            c = v3(mag_x + 0.15 + 0.9 * t * t, 0, -0.45 - t * mag_half[2] * 1.5)
            b.add(box(c, (mag_half[0], mag_half[1], 0.75), rot(RY, mag_rake - 26 * t), 0.25))
        b.add(box(v3(mag_x + 1.05, 0, -0.45 - mag_half[2] * 1.5 - 0.6), (mag_half[0] + 0.12, mag_half[1] + 0.1, 0.22),
                  rot(RY, mag_rake - 26), 0.08))
        for s in (-1, 1):
            b.cut(box(v3(mag_x + 0.25, s * mag_half[1], -0.75), (mag_half[0] - 0.3, 0.2, 0.2), rot(RY, mag_rake), 0.05))
    else:
        mag(b, (mag_x - mag_half[2] * math.sin(math.radians(-mag_rake)) * 0.5, 0, 0.25 - mag_half[2] + 0.15), mag_half,
            rake=mag_rake, ribs=3)
    well(b, (mag_x, 0, 0.12), mag_half, rake=mag_rake, depth=0.6)
    return top


def falconet():
    """VW3-05 'Falconet' carbine: boxy windowed stock, vented handguard, full-length rail, holo, vertical grip."""
    b = Build("falconet")
    top = _conventional(b)
    b.add(cyl(P(-5.2, 2.15), P(-2.6, 2.15), 0.62, 0.12))                                         # buffer tube
    stock_box(b, -7.3, -4.6, 0.3, 3.0)
    block(b, 4.0, 8.9, 0.75, 2.9, 0.98, 0.3, 0.5)
    vents(b, spaced(4.9, 8.3, 0.95), 1.35, 2.25, 0.98)
    zr = rail(b, -1.8, 8.6, top - 0.05, hy=0.58, keep_out=((-0.8, 1.2),))
    holo(b, 0.2, zr)
    fgrip(b, 7.0, 0.8)
    barrel(b, 8.7, 10.4, 1.85, 0.62)
    hider(b, 10.2, 11.8, 1.85, 0.88)
    chev(b, -5.95, 1.65, 0.95)
    return b


def basilisk():
    """VW3-06 'Basilisk' battle rifle: long shroud with staggered square ports, large scope, two-strut skeleton
    stock, folded bipod, big three-port brake, curved magazine."""
    b = Build("basilisk")
    top = _conventional(b, rear=-2.6, front=4.6, top=3.2, mag_half=(1.0, 0.82, 1.6), curved_mag=True)
    for z in (0.75, 2.55):
        b.add(capsule(P(-3.0, z), P(-6.8, z - 0.15), 0.38))                                      # skeleton struts
    b.add(box((-7.2, 0, 1.55), (0.42, 0.95, 1.55), rot(RY, -4), 0.18))                           # butt plate
    b.add(box((-5.0, 0, 2.55), (1.4, 0.55, 0.32), I3, 0.12))                                      # cheek bar
    crest(b, -6.2, -3.7, 2.87)
    block(b, 4.4, 11.6, 0.65, 3.0, 1.05, 0.3, 0.5)
    for i, x in enumerate(spaced(5.3, 10.8, 0.95)):
        z = 2.25 if i % 2 else 1.45
        for s in (-1, 1):
            b.cut(box((x, s * 1.05, z), (0.24, 0.32, 0.27), I3, 0.08))
    zr = rail(b, -2.0, 4.3, top - 0.05, hy=0.6, keep_out=((-1.44, -0.76), (2.76, 3.44)))
    scope(b, -2.6, 5.4, zr + 1.3, r=0.72, bell=1.12, mount_z=zr - 0.35, rings=(-1.1, 3.1))
    barrel(b, 11.4, 14.4, 1.85, 0.62)
    brake(b, 14.2, 16.6, 1.85, 0.95, ports=2)
    bipod(b, 8.4, 11.3, 0.4)
    return b


def petronel():
    """VW3-07 'Petronel' assault rifle: pump under-barrel launcher, slab handguard, holo with magnifier, boxy stock."""
    b = Build("petronel")
    top = _conventional(b, mag_half=(0.92, 0.8, 1.55))
    b.add(cyl(P(-5.0, 2.15), P(-2.8, 2.15), 0.62, 0.12))
    stock_box(b, -7.0, -4.4, 0.6, 3.0)
    block(b, 4.0, 8.6, 1.1, 2.95, 1.0, 0.3, 0.45)
    vents(b, spaced(4.9, 8.0, 0.95), 1.75, 2.45, 1.0, lean=12)
    zr = rail(b, -1.8, 8.3, top - 0.05, hy=0.58, keep_out=((-1.55, 1.9),))
    holo(b, 0.9, zr)
    b.add(box((-1.0, 0, zr + 0.35), (0.55, 0.7, 0.73), I3, 0.18))                                # magnifier on the rail strip
    b.cut(cyl(P(-1.65, zr + 0.6), P(-1.3, zr + 0.6), 0.28))
    barrel(b, 8.4, 10.6, 2.0, 0.62)
    brake(b, 10.4, 12.3, 2.0, 0.9, ports=2)
    launcher(b, 3.6, 9.2, -0.1, 1.08)
    b.add(box((6.2, 0, -0.1), (1.0, 1.2, 0.95), I3, 0.3))                                         # pump
    for x in (5.7, 6.7):
        b.cut(box((x, 0, -1.05), (0.22, 1.4, 0.2), I3, 0.05))
    b.add(box((5.6, 0, 0.95), (1.4, 0.6, 0.3), I3, 0.12))
    chev(b, -5.7, 1.8, 0.95)
    return b


def hackbut():
    """VW3-08 'Hackbut' heavy rifle: tall slab receiver, full-length integrated carry-optic, coupled twin magazines,
    stacked side vents, angled fore grip, heavy windowed stock, shrouded muzzle."""
    b = Build("hackbut")
    top = _conventional(b, rear=-2.6, front=5.0, top=3.4, mag_half=(0.9, 0.62, 1.6), mag_rake=-6)
    mag(b, (1.95, 1.12, -1.35), (0.9, 0.55, 1.45), rake=-6, ribs=2)                               # coupled second magazine (left)
    b.add(box((1.85, 0.65, -1.2), (0.62, 1.25, 0.3), rot(RY, -6), 0.08))                         # coupler clamp
    stock_box(b, -7.4, -2.4, 0.4, 3.3, hy=1.0)
    block(b, 4.8, 10.4, 0.5, 3.3, 1.08, 0.32, 0.55)                                              # slab handguard
    for z in (1.25, 2.3):
        vents(b, spaced(5.8, 9.6, 0.95), z - 0.3, z + 0.3, 1.08)
    optic(b, -1.6, 4.4, top - 0.05, hy=0.8, h=1.3, hood=0.5)                                     # carry-optic
    barrel(b, 10.2, 11.6, 1.9, 0.66)
    b.add(box((12.2, 0, 1.9), (0.9, 0.95, 0.95), I3, 0.25))                                      # muzzle shroud
    b.cut(box((12.2, 0, 1.9), (0.225, 1.3, 0.5), I3, 0.06))
    bore(b, 13.1, 1.9, 0.34, 0.5)
    afgrip(b, 8.2, 0.5)
    chev(b, -4.9, 1.85, 1.0)
    bolts(b, [(6.0, 0.85), (9.3, 0.85), (6.0, 2.95), (9.3, 2.95)], 1.08)
    return b


def fowler():
    """VW3-09 'Fowler' las carbine: power-cell magazine, cooling fins, focusing coil rings, flared emitter, optic."""
    b = Build("fowler")
    top = _conventional(b, rear=-2.4, front=4.4, top=3.1, mag_half=(1.0, 0.85, 1.25), mag_rake=-4)
    stock_box(b, -7.0, -2.2, 0.5, 3.0, hy=0.98, window=False)
    vents(b, spaced(-6.2, -3.2, 0.95), 1.0, 2.4, 0.98)
    block(b, 4.2, 8.2, 0.8, 2.95, 1.05, 0.3, 0.5)
    for x in spaced(4.8, 7.6, 0.95):
        b.add(box((x, 0, 1.9), (0.25, 1.28, 1.05), I3, 0.08))                                   # cooling fins
    b.add(cyl(P(8.0, 1.85), P(11.6, 1.85), 0.82, 0.15))                                          # focusing tube
    for x in (8.9, 10.0, 11.1):
        b.add(cyl(P(x - 0.22, 1.85), P(x + 0.22, 1.85), 1.08, 0.1))                              # coil rings
    b.add(round_cone(P(11.4, 1.85), P(12.6, 1.85), 0.95, 1.15).clip(xcap(12.6)))                 # emitter flare
    b.cut(cyl(P(12.1, 1.85), P(13.0, 1.85), 0.66))                                               # emitter cup (0.49 rim)
    b.add(cyl(P(11.8, 1.85), P(12.55, 1.85), 0.34, 0.1))                                         # emitter needle
    optic(b, -1.4, 2.6, top - 0.05, hy=0.8, h=1.3, hood=0.7)
    fgrip(b, 6.3, 0.8, rake=-4)
    chev(b, -4.6, 2.0, 1.0)
    return b


def arquebus():
    """VW3-10 'Arquebus' assault rifle: side-folded windowed stock, oval-ported shroud, short rail with holo, long
    vertical grip, steeply raked magazine."""
    b = Build("arquebus")
    top = _conventional(b, rear=-2.2, front=4.4, mag_half=(0.92, 0.8, 1.65), mag_rake=-14)
    b.add(box((-2.8, 0, 1.6), (0.45, 1.0, 0.9), I3, 0.2))                                        # stock hinge block
    b.add(box((-0.2, -1.42, 1.6), (2.6, 0.4, 0.95), I3, 0.2))                                    # folded stock (right side)
    b.cut(box((0.0, -1.42, 1.6), (1.6, 0.7, 0.32), I3, 0.12))                                    # stock window
    b.add(cyl(P(4.2, 1.75), P(10.6, 1.75), 1.08, 0.25))                                          # shroud 2.16 mm
    for x in spaced(5.0, 9.8, 1.1):
        for s in (-1, 1):
            b.cut(capsule(v3(x - 0.2, s * 1.1, 1.75), v3(x + 0.2, s * 1.1, 1.75), 0.26))
    zr = rail(b, -1.2, 3.2, top - 0.05, hy=0.6, keep_out=((0.0, 2.0),))
    holo(b, 1.0, zr)
    barrel(b, 10.4, 12.0, 1.75, 0.62)
    hider(b, 11.8, 13.4, 1.75, 0.9)
    fgrip(b, 7.6, 0.75, length=2.1, rake=-8)
    return b


# ================================================================================================ shotgun, SMG, pistols
def musketoon():
    """VW3-11 'Musketoon' combat shotgun: box-fed slab receiver, slotted heat shield over a 1.6 mm barrel, breaching
    crown, under tube with a grooved pump, heavy windowed stock with shell holders."""
    b = Build("musketoon")
    block(b, -2.4, 4.6, 0.2, 3.3, 1.12, 0.32, 0.5)
    seam_h(b, -2.0, 4.2, 1.05, 1.12)
    seam_v(b, 1.4, 1.05, 2.4, 1.12)
    b.cut(box((2.8, -1.12, 2.2), (0.95, 0.25, 0.5), I3, 0.08))                                    # ejection port
    grip3(b, rake=18)
    trigger3(b, zr=0.2, reach=1.3)
    mag(b, (1.6, 0, -0.75), (1.05, 0.9, 1.15), rake=-4, ribs=2)
    well(b, (1.7, 0, 0.12), (1.05, 0.9, 1.15), rake=-4)
    stock_box(b, -7.2, -2.2, 0.4, 3.2, hy=1.02)
    for x in (-5.9, -3.3):                                                                       # shell holders
        b.add(cyl(v3(x, -1.0, 2.75), v3(x, -1.4, 2.75), 0.34, 0.08))
    barrel(b, 4.4, 11.2, 2.3, 0.8)
    b.add(box((8.0, 0, 2.95), (3.3, 0.9, 0.42), I3, 0.18))                                        # heat shield
    vents(b, spaced(5.3, 10.7, 0.95), 2.75, 3.15, 0.9, d=0.25)
    b.add(cyl(P(4.4, 1.0), P(9.2, 1.0), 0.6, 0.12))                                              # under tube
    b.add(box((7.0, 0, 0.95), (1.5, 0.98, 0.6), I3, 0.25))                                        # pump
    for x in spaced(6.0, 8.0, 0.95):
        b.cut(box((x, 0, 0.35), (0.22, 1.2, 0.22), I3, 0.05))
    b.add(cyl(P(10.8, 2.3), P(12.3, 2.3), 1.05, 0.15))                                           # breaching crown
    b.cut(box((12.3, 0, 2.3), (0.4, 0.25, 1.3)))
    b.cut(box((12.3, 0, 2.3), (0.4, 1.3, 0.25)))
    b.cut(cyl(P(11.6, 2.3), P(12.6, 2.3), 0.48))
    rail(b, -1.6, 3.8, 3.25, hy=0.58)
    chev(b, -0.4, 2.1, 1.12)
    return b


def snaphance():
    """VW3-12 'Snaphance' SMG: compact boxy receiver, folded wire stock, forward magazine well, optic box, vertical
    grip, ported shroud."""
    b = Build("snaphance")
    block(b, -2.0, 4.0, 0.2, 2.8, 1.0, 0.3, 0.45)
    seam_h(b, -1.6, 3.6, 0.95, 1.0)
    seam_v(b, 1.0, 0.95, 2.3, 1.0)
    b.cut(box((0.4, -1.0, 1.85), (0.7, 0.25, 0.35), I3, 0.08))
    grip3(b, rake=12)
    trigger3(b, zr=0.2, reach=1.3)
    mag(b, (2.25, 0, -1.2), (0.6, 0.62, 1.65), rake=-4, ribs=2)
    well(b, (2.25, 0, 0.1), (0.6, 0.62, 1.65), rake=-4, depth=0.7)
    b.add(cyl(P(3.8, 1.6), P(7.0, 1.6), 0.82, 0.18))                                             # shroud
    for x in spaced(4.5, 6.4, 0.95):
        for s in (-1, 1):
            b.cut(box((x, s * 0.82, 1.6), (0.225, 0.3, 0.4), I3, 0.08))
    bore(b, 7.0, 1.6, 0.3, 0.5)
    for z in (0.75, 2.3):                                                                        # wire stock (folded, left)
        b.add(capsule(v3(-2.2, 1.2, z), v3(3.2, 1.2, z), 0.33))
    b.add(capsule(v3(3.2, 1.2, 0.75), v3(3.2, 1.2, 2.3), 0.33))
    b.add(box((-2.3, 0.6, 1.5), (0.35, 0.75, 0.95), I3, 0.15))                                   # stock hinge
    optic(b, -1.2, 2.0, 2.75, hy=0.75, h=1.2)
    fgrip(b, 5.3, 0.95, length=1.8)
    return b


def dag():
    """VW3-13 'Dag' heavy pistol: tall slab slide, deep serrations, integral compensator with top port, lamp."""
    b = Build("dag")
    block(b, -1.1, 4.4, 1.0, 2.25, 0.62, 0.22, 0.25)                                             # slide
    block(b, -0.6, 3.9, 0.15, 1.05, 0.56, 0.18)                                                  # frame
    vents(b, spaced(-0.7, 0.4, 0.95), 1.25, 1.65, 0.62, w=0.42, d=0.22)                          # rear serrations
    vents(b, [3.5], 1.25, 1.65, 0.62, w=0.42, d=0.22)
    b.cut(box((1.5, 0, 2.3), (0.6, 0.32, 0.22), I3, 0.06))                                        # top ejection port
    b.add(box((4.85, 0, 1.6), (0.5, 0.7, 0.7), I3, 0.18))                                         # compensator
    b.cut(box((4.85, 0, 2.35), (0.225, 0.28, 0.25), I3, 0.05))
    bore(b, 5.35, 1.55, 0.24, 0.45)
    b.add(box((2.9, 0, -0.05), (0.7, 0.5, 0.32), I3, 0.12))                                      # lamp
    b.cut(cyl(P(3.3, -0.05), P(3.8, -0.05), 0.24))
    b.add(box((-0.8, 0, 2.38), (0.3, 0.55, 0.16), I3, 0.06))                                      # rear sight
    b.cut(box((-0.8, 0, 2.5), (0.45, 0.2, 0.15)))
    b.add(box((4.0, 0, 2.38), (0.24, 0.24, 0.16), I3, 0.06))                                      # front sight
    grip3(b, rake=18)
    trigger3(b, zr=0.2, reach=1.3)
    b.add(box((-0.66, 0, -1.6), (0.62, 0.62, 0.22), rot(RY, 18), 0.08))                          # extended mag base
    return b


def wheellock():
    """VW3-14 'Wheellock' machine pistol: boxy upper, short ventilated shroud, long magazine through the grip, fore
    lever, reflex sight."""
    b = Build("wheellock")
    block(b, -1.2, 3.8, 0.2, 2.15, 0.7, 0.22, 0.3)
    seam_h(b, -0.9, 3.5, 1.0, 0.7, w=0.42, d=0.22)
    b.add(cyl(P(3.6, 1.45), P(5.8, 1.45), 0.74, 0.15))
    for x in spaced(4.2, 5.3, 0.95):
        for s in (-1, 1):
            b.cut(box((x, s * 0.74, 1.45), (0.21, 0.25, 0.3), I3, 0.06))
    bore(b, 5.8, 1.45, 0.26, 0.45)
    c = grip3(b, rake=10)
    n = rot(RY, 10)[:, 2]
    mag(b, c - n * 2.0, (0.45, 0.5, 1.3), rake=10, ribs=1)
    trigger3(b, zr=0.2, reach=1.3)
    b.add(box((2.8, 0, -0.45), (0.4, 0.5, 0.75), rot(RY, -20), 0.16))                            # fore lever
    holo(b, 1.0, 2.1, hy=0.55)
    vents(b, [0.2, 1.15], 1.3, 1.6, 0.7, w=0.42, d=0.22)
    return b


WEAPONS3 = {
    "VW3-01": ("Saker line rifle", "chunky bullpup: integrated optic housing, vented railed handguard, ported brake, angled fore grip", saker),
    "VW3-02": ("Caliver marksman bullpup", "bullpup DMR: ported shroud, long barrel, large scope on high rings, bipod", caliver),
    "VW3-03": ("Serpentine grenadier bullpup", "bullpup with 2.1 mm under-barrel launcher and grip, integrated optic, ladder sight", serpentine),
    "VW3-04": ("Minion bullpup carbine", "compact bullpup: integral suppressor, big box optic on a riser, vertical grip", minion),
    "VW3-05": ("Falconet carbine", "conventional: boxy windowed stock, vented handguard, holo sight, vertical grip", falconet),
    "VW3-06": ("Basilisk battle rifle", "conventional: long ported shroud, large scope, skeleton stock, curved magazine, bipod", basilisk),
    "VW3-07": ("Petronel assault rifle", "conventional with pump under-barrel launcher, holo + magnifier", petronel),
    "VW3-08": ("Hackbut heavy rifle", "slab receiver, integrated carry-optic, coupled twin magazines, stacked vents", hackbut),
    "VW3-09": ("Fowler las carbine", "energy carbine: power-cell magazine, cooling fins, coil rings, flared emitter", fowler),
    "VW3-10": ("Arquebus assault rifle", "side-folded stock, oval-ported shroud, holo, long vertical grip", arquebus),
    "VW3-11": ("Musketoon combat shotgun", "box-fed shotgun: heat shield, under tube and pump, breaching crown", musketoon),
    "VW3-12": ("Snaphance SMG", "compact SMG: forward magazine well, folded wire stock, ported shroud, optic box", snaphance),
    "VW3-13": ("Dag heavy pistol", "slab slide, deep serrations, integral compensator, lamp", dag),
    "VW3-14": ("Wheellock machine pistol", "ventilated shroud, long magazine through the grip, fore lever", wheellock),
}
FORE3 = {"VW3-01": (7.4, 0, 0.0), "VW3-02": (8.0, 0, 0.9), "VW3-03": (4.6, 0, -1.9), "VW3-04": (5.1, 0, -0.1),
         "VW3-05": (7.0, 0, -0.15), "VW3-06": (7.5, 0, 0.6), "VW3-07": (6.2, 0, -0.1), "VW3-08": (8.2, 0, 0.0),
         "VW3-09": (6.3, 0, -0.15), "VW3-10": (7.6, 0, -0.3), "VW3-11": (7.0, 0, 0.95), "VW3-12": (5.3, 0, 0.05),
         "VW3-13": None, "VW3-14": (2.8, 0, -0.45)}

# ================================================================================================ VB3 power blades
EDGE_FLAT = 0.5          # every cutting edge is a flat this wide (brief floor 0.4 mm)


def blade(z0, z1, edge, back=None, spine=((0.0, 1.2),), te=EDGE_FLAT, curve=None, edge_side=-1, plateau=0.0):
    """Blade body along +z from z0 to z1 (local x across the width, y through the thickness).
    edge / back: (z, half width) knots for the edge side and the back side (back=None: twin-edged, symmetric).
    spine: (z, full thickness at the centre line) knots. The section is a flattened hexagon: thickness falls linearly
    from the spine to a flat of width te at each cutting edge; a single-edged blade keeps the full spine to its back.
    curve(z) -> x offset of the centre line (sabre / falx curvature).
    plateau: half width of a flat central band at full spine thickness (fenestrations sit in it, so their walls meet a
    flat face at 90 deg instead of an acute wedge - M8)."""
    ez, ew = np.array([k[0] for k in edge]), np.array([k[1] for k in edge])
    bz, bw = (ez, ew) if back is None else (np.array([k[0] for k in back]), np.array([k[1] for k in back]))
    sz, sw = np.array([k[0] for k in spine]), np.array([k[1] for k in spine])
    twin = back is None

    def f(Q):
        s = Q[:, 2]
        u = Q[:, 0] - (curve(s) if curve else 0.0)
        ue = u * edge_side                                      # > 0 toward the cutting edge
        he, hb = np.interp(s, ez, ew), np.interp(s, bz, bw)
        ts = np.interp(s, sz, sw)
        d_w = np.where(ue > 0, ue - he, -ue - hb)
        pl = np.minimum(plateau, he - 0.3)
        fe = np.clip((he - np.abs(ue)) / np.maximum(he - pl, 1e-3), 0, 1)
        frac = fe if twin else np.where(ue > 0, fe, 1.0)
        t = te / 2 + (ts / 2 - te / 2) * frac
        d = np.maximum(d_w, np.abs(Q[:, 1]) - t)
        return np.maximum(d, np.maximum(z0 - s, s - z1))

    zs = np.linspace(z0, z1, 64)
    cs = curve(zs) if curve else np.zeros_like(zs)
    w = max(ew.max(), bw.max())
    return Shape(f, (cs.min() - w - 0.1, -sw.max() / 2 - 0.1, z0 - 0.05), (cs.max() + w + 0.1, sw.max() / 2 + 0.1, z1 + 0.05))


def window(b, x, z, half_w, half_h, ang=0.0):
    """Through fenestration (stadium extruded through the blade along y), rotated ang deg about y."""
    r = min(half_w, half_h)
    b.cut(box((x, 0, z), (half_w, 2.0, half_h), rot(RY, ang), r * 0.98))


def bgrip(b, z0=-1.5, z1=1.5, rings=(-1.15, -0.4, 0.35, 1.1), r=0.5, rr=0.63):
    """Segmented ornate grip: 1.0 mm core, 1.26 mm rings (inside the exosuit fist), spiral-wrap grooves between."""
    b.add(cyl(v3(0, 0, z0), v3(0, 0, z1), r, 0.1))
    for z in rings:
        b.add(cyl(v3(0, 0, z - 0.16), v3(0, 0, z + 0.16), rr, 0.09))
    for z0_, z1_ in zip(rings[:-1], rings[1:]):
        zm = (z0_ + z1_) / 2
        b.add(sphere(v3(0, 0, zm), 0.58))                                                         # bead between rings


def pommel_ring(b, zc, R_=0.74, r=0.34, neck=-1.5):
    b.add(cyl(v3(0, 0, neck), v3(0, 0, zc + R_ - 0.1), 0.52, 0.12))
    b.add(cyl(v3(0, 0, neck - 0.05), v3(0, 0, neck - 0.4), 0.66, 0.12))
    b.add(torus(v3(0, 0, zc), RY, R_, r))


def quillon(b, pts, r0=0.4, r1=0.32, mirror=True, tip=0.42):
    """Swept crossguard arm along a cubic Bezier (and its mirror in x), finished with a round finial."""
    for s in ((-1, 1) if mirror else (1,)):
        q = [v3(s * p[0], p[1], p[2]) for p in pts]
        b.add(tube(bezier(*q, n=12), r0, r1))
        b.add(sphere(q[-1], tip))


def thorn():
    """VB3-01 'Thorn' power sword: broad twin-edged blade with three in-line fenestrations, two stepped shoulders
    toward the tip, horned up-swept crossguard over a ricasso collar, segmented grip, ring pommel."""
    b = Build("thorn")
    edge = [(2.0, 1.15), (2.6, 1.15), (3.1, 1.7), (9.0, 1.6), (9.3, 1.3), (12.4, 1.22), (12.7, 0.98), (15.0, 0.42), (15.4, 0.32)]
    b.add(blade(1.95, 15.4, edge, spine=[(2.0, 1.25), (12.0, 1.1), (15.4, 0.62)], plateau=0.82))
    for z0, z1, w in ((4.0, 5.9, 0.36), (6.5, 8.3, 0.36), (10.0, 11.3, 0.3)):
        window(b, 0.0, (z0 + z1) / 2, w, (z1 - z0) / 2)
    b.add(box((0, 0, 2.2), (1.3, 0.72, 0.28), I3, 0.12))                                         # ricasso collar
    b.add(box((0, 0, 1.75), (1.25, 0.65, 0.35), I3, 0.15))                                       # guard block
    quillon(b, [(0.9, 0, 1.75), (2.0, 0, 1.6), (2.9, 0, 2.2), (2.75, 0, 3.25)])                  # up-swept horns
    quillon(b, [(0.9, 0, 1.6), (1.5, 0, 1.2), (2.0, 0, 1.2), (2.25, 0, 0.95)], 0.34, 0.3, tip=0.36)  # rear spurs
    for s in (-1, 1):
        b.add(sphere(v3(0, s * 0.62, 1.8), 0.36))                                                 # emitter studs
    bgrip(b)
    pommel_ring(b, -2.65)
    return b


def tulwar():
    """VB3-02 'Tulwar' power sabre: curved single-edged blade (edge on the convex side), clipped back near the tip,
    pierced teardrop at the forte, stepped back spine, down-swept guard, disc pommel with a ring."""
    b = Build("tulwar")
    cv = lambda s: 0.0145 * np.clip(s - 2.0, 0, None) ** 2
    edge = [(2.0, 0.85), (3.0, 1.25), (10.5, 1.4), (13.0, 1.2), (14.6, 0.5), (15.0, 0.34)]
    back = [(2.0, 0.85), (3.0, 1.0), (11.0, 1.0), (11.3, 0.7), (13.0, 0.5), (14.6, 0.36), (15.0, 0.3)]
    b.add(blade(1.95, 15.0, edge, back, spine=[(2.0, 1.1), (11.0, 1.0), (15.0, 0.62)], curve=cv, edge_side=-1, plateau=0.65))
    window(b, float(cv(4.3)) - 0.15, 4.3, 0.32, 0.72)
    window(b, float(cv(5.6)) - 0.1, 5.6, 0.22, 0.24)
    b.add(box((0, 0, 1.75), (1.05, 0.65, 0.35), I3, 0.15))
    quillon(b, [(0.8, 0, 1.75), (1.6, 0, 1.85), (2.3, 0, 1.4), (2.4, 0, 0.75)])                  # down-swept
    bgrip(b, rings=(-1.15, -0.4, 0.35, 1.1))
    b.add(cyl(v3(0, 0, -1.5), v3(0, 0, -2.0), 0.55, 0.12))
    b.add(cyl(v3(0, -0.4, -2.45), v3(0, 0.4, -2.45), 0.85, 0.15))                                # disc pommel
    b.cut(cyl(v3(0, -0.6, -2.45), v3(0, 0.6, -2.45), 0.3))                                       # ring hole (0.55 rim)
    return b


def estoc():
    """VB3-03 'Estoc' great-blade: long narrow twin-edged blade with a long fuller and a step at the point, long
    six-ring two-hand grip, S-curl quillons with finials, orb pommel with a finial."""
    b = Build("estoc")
    edge = [(2.2, 0.95), (2.8, 1.25), (17.0, 1.05), (17.3, 0.82), (20.0, 0.42), (20.5, 0.32)]
    b.add(blade(2.15, 20.5, edge, spine=[(2.2, 1.3), (17.0, 1.15), (20.5, 0.62)], plateau=0.78))
    for s in (-1, 1):
        b.cut(box((0, s * 0.64, 9.6), (0.27, 0.22, 5.4), I3, 0.12))                              # fuller, both faces
    window(b, 0.0, 3.55, 0.3, 0.42)                                                               # pierced forte
    for s in (-1, 1):
        b.add(sphere(v3(0, s * 0.66, 2.3), 0.34))                                                 # emitter studs
    b.add(box((0, 0, 2.3), (1.35, 0.75, 0.3), I3, 0.12))
    b.add(box((0, 0, 1.8), (1.2, 0.66, 0.32), I3, 0.15))
    quillon(b, [(0.9, 0, 1.8), (2.1, 0, 1.5), (2.9, 0, 2.5), (2.15, 0, 3.15)])                   # S-curls
    bgrip(b, z0=-3.7, z1=1.5, rings=(-3.35, -2.6, -1.85, -1.1, -0.35, 0.4, 1.15))
    b.add(cyl(v3(0, 0, -3.7), v3(0, 0, -4.1), 0.62, 0.12))
    b.add(sphere(v3(0, 0, -4.75), 0.82))                                                          # orb pommel
    b.cut(torus(v3(0, 0, -4.75), RZ, 0.82, 0.16))
    b.add(round_cone(v3(0, 0, -5.4), v3(0, 0, -6.0), 0.4, 0.3))                                  # finial
    return b


def flamberge():
    """VB3-04 'Flamberge' power sword: twin edges stepped like a ratchet (teeth toward the hilt), split-chevron
    fenestrations down the centre, power-cell guard with vents and emitters, short swept wings, ring pommel."""
    b = Build("flamberge")
    edge = [(2.0, 1.1), (2.6, 1.1), (3.0, 1.45)]
    for z in np.arange(3.6, 12.4, 1.1):
        edge += [(z, 1.45), (z + 0.85, 1.7), (z + 1.0, 1.45)]
    edge += [(13.0, 1.4), (15.0, 0.42), (15.4, 0.32)]
    b.add(blade(1.95, 15.4, edge, spine=[(2.0, 1.25), (12.5, 1.15), (15.4, 0.62)], plateau=1.15))
    for z in (4.6, 7.0, 9.4):                                                                     # split chevron windows
        for k in (-1, 1):
            window(b, k * 0.36, z, 0.34, 0.19, ang=-k * 32)
    b.add(box((0, 0, 1.85), (1.55, 0.82, 0.5), I3, 0.2))                                          # power cell guard
    for x in (-0.8, 0.0, 0.8):
        b.cut(box((x, -0.82, 1.85), (0.22, 0.25, 0.28), I3, 0.06))
        b.cut(box((x, 0.82, 1.85), (0.22, 0.25, 0.28), I3, 0.06))
    for s in (-1, 1):
        b.add(box((s * 2.05, 0, 2.15), (0.75, 0.46, 0.34), rot(RY, -s * 30), 0.15))              # swept wings
        b.add(sphere(v3(s * 1.15, 0, 2.45), 0.34))                                                # emitters
    bgrip(b)
    pommel_ring(b, -2.65)
    return b


def falx():
    """VB3-05 'Falx' power cleaver: forward-curved heavy blade with the edge on the concave side, notched back spine,
    pierced near the point, single swept quillon on the edge side, spiked pommel."""
    b = Build("falx")
    cv = lambda s: -0.016 * np.clip(s - 2.5, 0, None) ** 2
    edge = [(2.0, 0.85), (3.0, 1.3), (10.0, 1.9), (12.6, 1.65), (13.8, 0.5), (14.2, 0.34)]
    back = [(2.0, 0.85), (3.0, 1.0)]
    for z in (4.2, 5.5, 6.8, 8.1):
        back += [(z, 1.0), (z + 0.35, 0.68), (z + 0.75, 0.68), (z + 0.9, 1.0)]
    back += [(12.6, 1.0), (13.8, 0.4), (14.2, 0.3)]
    b.add(blade(1.95, 14.2, edge, back, spine=[(2.0, 1.15), (11.0, 1.05), (14.2, 0.62)], curve=cv, edge_side=-1, plateau=0.6))
    window(b, float(cv(11.0)) - 0.2, 11.0, 0.34, 0.34)
    b.add(box((0, 0, 1.75), (1.05, 0.66, 0.36), I3, 0.15))
    quillon(b, [(-0.8, 0, 1.75), (-1.7, 0, 1.7), (-2.4, 0, 2.3), (-2.5, 0, 3.0)], mirror=False)  # edge-side quillon
    b.add(sphere(v3(1.05, 0, 1.75), 0.45))                                                        # back knob
    bgrip(b)
    b.add(cyl(v3(0, 0, -1.5), v3(0, 0, -1.95), 0.62, 0.12))
    b.add(round_cone(v3(0, 0, -2.0), v3(0, 0, -3.3), 0.62, 0.32))                                 # spike pommel
    return b


def keel():
    """VB3-06 'Keel' power sword: the Vigil blade. Broad twin-edged blade with a raised keel ridge on both faces,
    stepped chisel point, ricasso coil collars, split-chevron crossguard, ring pommel with a keel fin."""
    b = Build("keel")
    edge = [(2.0, 1.2), (2.9, 1.2), (3.3, 1.8), (12.5, 1.7), (12.85, 1.15), (14.9, 0.95), (15.5, 0.6)]
    b.add(blade(1.95, 15.5, edge, spine=[(2.0, 1.3), (13.0, 1.2), (15.5, 0.75)], plateau=1.2))
    for s in (-1, 1):
        b.add(box((0, s * 0.6, 8.1), (0.3, 0.22, 4.6), I3, 0.12))                                # keel ridge, 0.17 proud
        window(b, s * 0.9, 5.0, 0.22, 0.75)                                                       # flanking windows (M9)
        window(b, s * 0.9, 9.6, 0.22, 0.55)
    for z in (2.2, 2.98):
        b.add(box((0, 0, z), (1.42, 0.8, 0.22), I3, 0.1))                                         # coil collars 0.44 thick
    b.add(box((0, 0, 1.75), (0.6, 0.68, 0.38), I3, 0.15))                                         # guard core
    for s in (-1, 1):
        b.add(box((s * 1.45, 0, 1.6), (1.05, 0.55, 0.36), rot(RY, s * 24), 0.15))                # chevron arms, down-swept
    bgrip(b)
    pommel_ring(b, -2.65)
    b.add(box((0, 0, -3.55), (0.32, 0.36, 0.42), I3, 0.12))                                       # keel fin under the ring
    return b


BLADES3 = {
    "VB3-01": ("Thorn power sword", "broad twin-edged blade, three fenestrations, stepped shoulders, horned crossguard, ring pommel", thorn),
    "VB3-02": ("Tulwar power sabre", "curved single-edged sabre, pierced teardrop, clipped back, down-swept guard, disc pommel", tulwar),
    "VB3-03": ("Estoc great-blade", "long twin-edged blade with a fuller, six-ring two-hand grip, S-curl quillons, orb pommel", estoc),
    "VB3-04": ("Flamberge power sword", "ratchet-stepped edges, split-chevron windows, power-cell guard with vents, ring pommel", flamberge),
    "VB3-05": ("Falx power cleaver", "forward-curved blade, notched spine, pierced point, single swept quillon, spiked pommel", falx),
    "VB3-06": ("Keel power sword", "keel-ridged broad blade, stepped chisel point, coil collars, split-chevron guard, ring pommel", keel),
}
# second (lower) hand on two-hand grips, grip-frame z
HANDLE3_BLADES = {"VB3-03": (0, 0, -2.4)}

# ================================================================================================ VHW heavy weapons
def handle_bar(b, x0, x1, z, post_z=None, r=0.5):
    """Top carry / support handle: a 1.0 mm round bar along x (the exosuit fist closes on it) on two posts."""
    for x in (x0, x1):
        b.add(capsule(P(x, post_z if post_z is not None else z - 1.4), P(x, z), 0.45))
    b.add(capsule(P(x0, z), P(x1, z), r))
    for x in spaced(x0 + 0.9, x1 - 0.9, 0.9):
        b.add(cyl(P(x - 0.12, z), P(x + 0.12, z), r + 0.1, 0.05))                                # grip rings


def belt_links(b, pts, w=0.9, t=0.55, step=0.62, up=(0, 0, 1)):
    """Ammunition belt along a polyline: a continuous core strap plus raised links every 'step' mm (rounds read as a
    ribbed band). Section w (across) x t, both >= 0.55 mm."""
    pts = [v3(p) for p in pts]
    b.add(tube(pts, t * 0.5 + 0.02))
    L = [0.0] + list(np.cumsum([np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]))
    for s in np.arange(step / 2, L[-1] - step / 4, step):
        i = min(np.searchsorted(L, s) - 1, len(pts) - 2)
        i = max(i, 0)
        a = (s - L[i]) / max(L[i + 1] - L[i], 1e-6)
        p = pts[i] + (pts[i + 1] - pts[i]) * a
        d = unit(pts[i + 1] - pts[i])
        side = np.cross(d, unit(up))
        if np.linalg.norm(side) < 1e-3:
            side = np.cross(d, v3(1, 0, 0))
        side = unit(side)
        nrm = np.cross(side, d)
        R = np.stack([d, side, nrm], axis=1)
        b.add(rbox(p, (0.2, w / 2, t / 2 + 0.06), R, 0.08))


def bombard():
    """VHW-01 'Bombard' rotary heavy repeater: six-barrel rotary cluster in two clamps and a bored muzzle plate,
    vented motor housing, tall receiver with a right-side belt feed port, top support handle, rear grip,
    ammunition counter, heat shield. Fed from the drum_pack() backpack by the belt."""
    b = Build("bombard")
    zc = 2.2                                                                                     # rotor axis height
    block(b, -3.0, 5.2, 0.2, 4.2, 1.65, 0.4, 0.7)                                               # receiver
    b.add(box((-3.4, 0, 2.2), (0.45, 1.5, 1.7), I3, 0.2))                                        # rear plate
    for z in spaced(1.0, 3.4, 0.95):
        b.cut(box((-3.85, 0, z), (0.12, 1.7, 0.2), I3, 0.04))
    seam_h(b, -2.6, 4.8, 1.2, 1.65)
    seam_h(b, -2.6, 4.8, 3.1, 1.65)
    seam_v(b, 1.0, 1.2, 3.1, 1.65)
    seam_v(b, 3.4, 1.2, 3.1, 1.65)
    vents(b, spaced(-2.2, 0.4, 0.95), 1.55, 2.75, 1.65)
    bolts(b, [(-2.5, 0.65), (4.7, 0.65), (-2.5, 3.65), (4.7, 3.65)], 1.65)
    b.add(box((1.6, -1.95, 2.1), (1.25, 0.45, 0.95), I3, 0.2))                                   # feed port housing (right)
    b.cut(box((1.6, -2.3, 2.1), (0.8, 0.3, 0.5), I3, 0.1))                                       # feed throat recess
    b.add(box((-1.2, 1.85, 2.6), (0.85, 0.32, 0.6), I3, 0.15))                                   # ammunition counter (left)
    b.cut(box((-1.2, 2.15, 2.65), (0.5, 0.15, 0.32), I3, 0.06))
    b.add(cyl(P(5.0, zc), P(8.6, zc), 2.0, 0.3))                                                 # motor housing
    for x in (6.0, 7.6):
        b.cut(torus(P(x, zc), RX, 2.0, 0.22))
    for a in range(0, 360, 45):
        t = math.radians(a)
        b.cut(box(P(6.8, zc + 2.0 * math.sin(t), 2.0 * math.cos(t)), (0.5, 0.25, 0.25), rot(RX, -a), 0.08))
    b.add(cyl(P(8.4, zc), P(9.2, zc), 1.75, 0.2))                                                # rotor hub
    b.add(cyl(P(9.0, zc), P(20.4, zc), 0.6, 0.1))                                                # centre spindle
    for a in range(0, 360, 60):
        t = math.radians(a + 30)
        o = v3(0, 1.18 * math.cos(t), 1.18 * math.sin(t))
        b.add(cyl(P(9.0, zc) + o, P(20.6, zc) + o, 0.5, 0.1))                                    # barrels 1.0 mm
    for x0, x1 in ((13.6, 14.4), (19.6, 21.0)):
        b.add(cyl(P(x0, zc), P(x1, zc), 1.95, 0.2))                                              # clamps / muzzle plate
    for a in range(0, 360, 60):
        t = math.radians(a + 30)
        b.cut(cyl(P(20.5, zc) + v3(0, 1.18 * math.cos(t), 1.18 * math.sin(t)), P(21.4, zc) + v3(0, 1.18 * math.cos(t), 1.18 * math.sin(t)), 0.27))
    b.cut(torus(P(14.0, zc), RX, 1.95, 0.18))
    b.add(box((7.0, 0, 4.3), (2.6, 1.1, 0.25), I3, 0.12))                                        # heat shield over the motor
    for x in spaced(5.4, 8.6, 0.95):
        b.cut(box((x, 0, 4.55), (0.225, 0.8, 0.2), I3, 0.05))
    b.add(box((7.0, 0, 3.9), (0.5, 0.6, 0.4), I3, 0.1))
    handle_bar(b, 1.8, 5.4, 5.6, post_z=4.0)                                                     # support handle
    grip3(b, rake=12)
    trigger3(b, zr=0.2, reach=1.35)
    b.add(box((-0.8, 0, -0.2), (0.6, 0.9, 0.4), I3, 0.15))                                       # grip boss
    chev(b, 4.1, 2.1, 1.65, size=1.0)
    return b


def carronade():
    """VHW-02 'Carronade' heavy rail cannon: capacitor body with four side cells, twin magnetic rails in five coil
    clamps, muzzle crown, rangefinder box, cable loops, top support handle, rear grip."""
    b = Build("carronade")
    block(b, -3.6, 6.0, 0.2, 4.4, 1.6, 0.4, 0.7)
    b.add(box((-4.0, 0, 2.3), (0.45, 1.45, 1.8), I3, 0.2))
    for z in spaced(1.0, 3.6, 0.95):
        b.cut(box((-4.45, 0, z), (0.12, 1.65, 0.2), I3, 0.04))
    seam_h(b, -3.2, 5.6, 1.25, 1.6)
    seam_v(b, 2.0, 1.25, 3.7, 1.6)
    for s in (-1, 1):
        for z in (1.25, 3.05):
            b.add(cyl(v3(-2.4, s * 1.7, z), v3(3.4, s * 1.7, z), 0.68, 0.18))                   # capacitor cells
            for x in spaced(-1.6, 2.6, 0.95):
                b.cut(torus(v3(x, s * 1.7, z), RX, 0.68, 0.17))
    for zc in (1.25, 3.35):
        b.add(box((13.2, 0, zc), (7.4, 0.7, 0.48), I3, 0.15))                                    # rails x 5.8..20.6
    for x in spaced(7.4, 19.0, 2.9):
        b.add(box((x, 0, 2.3), (0.55, 1.45, 1.75), I3, 0.25))                                    # coil clamps
        seam_v(b, x, 0.9, 3.7, 1.45, w=0.4, d=0.25)
    b.add(box((21.0, 0, 2.3), (0.6, 1.35, 1.75), I3, 0.25))                                      # muzzle crown
    b.cut(box((21.6, 0, 2.3), (0.45, 0.45, 0.45), I3, 0.15))
    b.add(box((3.0, 0, 5.0), (1.6, 0.8, 0.6), I3, 0.2))                                          # rangefinder
    b.cut(cyl(P(4.5, 5.0, 0.0), P(4.9, 5.0, 0.0), 0.36))
    for s in (-1, 1):
        b.add(tube([v3(-1.0, s * 1.7, 3.8), v3(1.0, s * 2.35, 4.6), v3(4.0, s * 2.1, 4.0), v3(6.2, s * 1.6, 3.6)], 0.32))  # cable loops
    handle_bar(b, -1.6, 1.6, 6.0, post_z=4.4)
    grip3(b, rake=12)
    trigger3(b, zr=0.2, reach=1.35)
    b.add(box((-0.8, 0, -0.2), (0.6, 0.9, 0.4), I3, 0.15))
    chev(b, 4.5, 2.4, 1.6, size=1.0)
    return b


def siphon():
    """VHW-03 'Siphon' heavy flamer: slab body over twin fuel tanks, finned heat-sink barrel, flared nozzle with a
    recessed jet and pilot igniter, braided feed hoses, top support handle, vertical fore grip, rear grip."""
    b = Build("siphon")
    block(b, -2.6, 5.6, 0.2, 3.5, 1.4, 0.35, 0.6)
    seam_h(b, -2.2, 5.2, 1.2, 1.4)
    seam_v(b, 1.6, 1.2, 3.0, 1.4)
    vents(b, spaced(2.4, 4.8, 0.95), 1.6, 2.8, 1.4)
    for s in (-1, 1):
        b.add(cyl(v3(2.0, s * 1.15, -0.85), v3(7.2, s * 1.15, -0.85), 1.08, 0.5))               # fuel tanks
        b.cut(torus(v3(3.4, s * 1.15, -0.85), RX, 1.08, 0.18))
        b.cut(torus(v3(5.8, s * 1.15, -0.85), RX, 1.08, 0.18))
        b.add(tube([v3(7.0, s * 1.2, -0.4), v3(8.4, s * 1.2, 0.2), v3(9.6, s * 0.8, 1.0)], 0.32))  # feed hoses
    b.add(box((4.6, 0, 0.25), (2.6, 1.0, 0.3), I3, 0.1))                                          # tank saddle
    b.add(cyl(P(5.4, 1.85), P(14.2, 1.85), 0.9, 0.15))                                           # barrel
    for x in spaced(6.4, 12.6, 0.95):
        b.add(cyl(P(x - 0.22, 1.85), P(x + 0.22, 1.85), 1.3, 0.08))                              # heat-sink fins
    b.add(round_cone(P(13.8, 1.85), P(15.6, 1.85), 1.0, 1.45).clip(xcap(15.6)))                  # nozzle flare
    b.cut(cyl(P(14.9, 1.85), P(16.0, 1.85), 1.0))                                                # nozzle cup (0.45 rim)
    b.add(cyl(P(14.5, 1.85), P(15.5, 1.85), 0.45, 0.1))                                          # jet
    b.add(box((15.0, 0, 0.1), (0.7, 0.45, 0.42), I3, 0.12))                                      # pilot igniter
    b.add(box((14.4, 0, 0.62), (0.3, 0.4, 0.5), I3, 0.08))
    handle_bar(b, 0.0, 3.6, 4.9, post_z=3.5)
    grip3(b, rake=12)
    trigger3(b, zr=0.2, reach=1.35)
    fgrip(b, 9.6, 0.95, length=2.0)
    chev(b, -0.9, 2.0, 1.4, size=1.0)
    return b


def drum_pack(h=0.06):
    """VHW-01P ammunition drum backpack for the Bombard, in the exosuit backpack frame: front face on y = 0 against the
    back boss, 2.0 mm D-flat peg toward -y (exosuit.PEG_PACK), up z. A power core with a keel spine carries a large
    ribbed drum across the back; the feed throat leaves the drum's right (-x) end and stops at the front plane with a
    flat face (FEED_FACE) where the figure's belt chute ends, 0.1 mm proud of it for a glue joint."""
    g = Sculpt((-6.4, -PEG_PACK["len"] - 0.3, -6.8), (5.6, 7.4, 5.4), h)
    g.add(rbox(v3(0, 1.15, 0.6), (2.4, 1.15, 3.2), I3, 0.7))                                     # core
    g.add(round_cone(v3(0, 2.3, 3.6), v3(0, 2.3, -1.0), 0.45, 0.42), 0.12)                       # keel spine
    for j in range(3):
        g.cut(rbox(v3(0, 0.0, 1.6 + j * 0.9), (1.7, 0.2, 0.22), I3, 0.06))
    dc, dr = v3(0.3, 4.1, -1.6), 2.75
    g.add(cyl(dc - v3(4.2, 0, 0), dc + v3(4.2, 0, 0), dr, 0.5), 0.2)                              # drum
    for x in (-2.6, -0.9, 0.9, 2.6):
        g.cut(torus(dc + v3(x, 0, 0), RX, dr, 0.2))                                               # rib grooves
    for s in (-1, 1):
        g.add(cyl(dc + v3(s * 4.0, 0, 0), dc + v3(s * 4.55, 0, 0), dr - 0.55, 0.2), 0.1)          # end caps
        for a in range(0, 360, 60):
            t = math.radians(a)
            g.add(sphere(dc + v3(s * 4.55, 1.6 * math.cos(t), 1.6 * math.sin(t)), 0.3), 0.05)     # cap bolts
        g.add(cyl(dc + v3(s * 4.4, 0, 0), dc + v3(s * 4.95, 0, 0), 0.7, 0.15), 0.1)               # hub
    g.add(rbox(v3(0.3, 2.0, -1.6), (3.6, 0.9, 1.1), I3, 0.4), 0.3)                               # saddle to the core
    for x in (-2.6, 3.0):
        g.add(rbox(v3(x, 2.4, 0.2), (0.4, 1.0, 1.6), I3, 0.2), 0.2)                              # drum straps
    fc = v3(*FEED_FACE)
    g.add(rbox(v3(fc[0], (fc[1] + 3.0) / 2, fc[2]), (0.85, (3.0 - fc[1]) / 2, 0.7), I3, 0.25), 0.2)  # feed throat
    g.add(rbox(dc + v3(-4.0, -1.2, -1.2), (0.9, 1.6, 1.0), I3, 0.3), 0.3)
    g.cut(rbox(v3(fc[0], fc[1] - 0.15, fc[2]), (0.45, 0.35, 0.3), I3, 0.08))                     # 0.2 mm locating recess
    g.cut(Shape(lambda Q: Q[:, 1] - fc[1], (-9, -9, -9), (9, fc[1], 12)))                         # flat front at FEED_FACE
    g.add(d_peg((0, 0.3, 0.6), (0, -1, 0), PEG_PACK["d"], PEG_PACK["len"] + 0.3, key=(0, 0, 1)))
    return g


FEED_FACE = (-4.3, 0.1, -3.6)        # pack frame: centre of the throat face (the figure's chute stops 0.1 mm short)

HEAVY3 = {
    "VHW-01": ("Bombard rotary repeater", "six-barrel rotary heavy repeater: motor housing, belt feed port, support handle, bored muzzle plate", bombard),
    "VHW-02": ("Carronade rail cannon", "twin-rail heavy cannon: capacitor cells, five coil clamps, rangefinder, support handle", carronade),
    "VHW-03": ("Siphon heavy flamer", "twin fuel tanks, finned barrel, flared nozzle with igniter, vertical fore grip", siphon),
}
HANDLE3 = {"VHW-01": ((3.6, 0, 5.6), (1, 0, 0)), "VHW-02": ((0.0, 0, 6.0), (1, 0, 0)), "VHW-03": ((9.6, 0, -0.05), (0.1, 0, -1))}
REGISTRY = {**WEAPONS3, **BLADES3, **HEAVY3}


def item(ident):
    return REGISTRY[ident][2]()


def weapon_shape(ident):
    """One Shape for a figure to hold (weapon / grip frame; move it with .moved(M))."""
    return item(ident).shape()


def sculpt_fit(build, name, h0=0.05, budget=285_000, h_max=0.075, open_r=None, log=None):
    """Mesh a Build on its own grid at pitch h0; if the marched mesh is over the checker budget, RE-MESH THE FIELD
    COARSER (triangles scale with 1 / h^2) instead of decimating (3dada lesson: never QEM-decimate SDF meshes).
    Returns (mesh, pitch)."""
    h = h0
    while True:
        g = build.sculpt(h)
        removed = open_slivers(g, open_r) if open_r else 0.0
        m = g.mesh(name, None)
        n = len(m.faces)
        if log is not None:
            log[name] = {"pitch_mm": h, "triangles": n, "opening_r_mm": open_r, "opened_away_mm3": round(removed, 4)}
        if n <= budget or h >= h_max:
            return m, h
        h = min(h_max, round(h * math.sqrt(n / (budget * 0.93)) + 0.0005, 4))


def catalogue():
    return {k: v[:2] for k, v in REGISTRY.items()}
