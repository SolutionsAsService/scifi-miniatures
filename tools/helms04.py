"""VH4: the Vigil helm library 0.3 - every helm design of the line so far, in one print-safe library.

0.1 gave the line ten helms (VH-01..10, tools/armory.py, tools/exosuit.py): clear ideas, plain blobby surfaces.
0.2 gave two libraries: VH2-01..12 (tools/vh2.py, never built: detailed, but thin 0.13-0.26 mm plates and frames and
one shared silhouette) and VH3-01..08 (tools/helms3.py: distinct silhouettes at print-safe feature floors, published
with a morphological filter that left voxel terraces on every surface). VH4 keeps the eight VH3 helms (each absorbing
its 0.1/VH2 counterpart) and re-sculpts the ten designs VH3 had no equivalent for in the VH3 vocabulary and floors:

| VH4 | Name | Pulled from |
|---|---|---|
| 01 | Lineguard | VH-01 Vigil, VH2-01 Lineguard (the line standard) |
| 02 | Marshal | VH-02 Warden, VH2-05 Marshal |
| 03 | Plummet | VH3-01 |
| 04 | Sightline | VH3-02, VH-04 Seeker, VH2-03 Lookout |
| 05 | Ironclad | VH3-03, VH-09 Bulwark, VH2-04 Bastion |
| 06 | Breacher | VH-03 Breacher |
| 07 | Sentinel | VH-05 Sentinel |
| 08 | Raptor | VH-06 Raptor |
| 09 | Diver | VH-07 Diver, VH2-02 Tidewall |
| 10 | Stillwater | VH3-05 |
| 11 | Hunter | VH-08 Hunter |
| 12 | Specter | VH-10 Specter |
| 13 | Herald | VH3-04, VH2-10 Provost |
| 14 | Longsight | VH3-07, VH2-08 Plumb |
| 15 | Deckhand | VH3-06, VH2-09 Kite |
| 16 | Mender | VH2-06 Mender |
| 17 | Wright | VH2-07 Wright |
| 18 | Grimward | VH3-08, VH2-11/12 (battle damage) |

Family marks on every helm: SPLIT-CHEVRON glass (a recessed glass surface whose lower edge falls to a V or is split by
the keel; a separate surface for gloss/lens paint) and the KEEL LINE (one ridge from the nape over the crown to the
face). Feature floors (MSLA resin, measured with unified-CAD-MCP miniature_detail_resolution_check and
miniature_printability_check): glass and slots >= 0.5 mm wide, frames >= 0.45 mm, raised bars/ribs/tubes >= 0.44 mm,
gaps between raised features >= 0.5 mm, wires >= 0.76 mm. The build then runs morph.print_safe_selective: it acts
only where a slot is narrower than 0.5 mm or a wall thinner than 0.42 mm and leaves every other surface exactly as
sculpted (VH3's global filter rounded every edge and terraced every face). Same frame and 1.6 mm D-flat neck peg as every Vigil helm: any helm fits any trooper.
"""
from __future__ import annotations

import math

import numpy as np

import helms3
from exosuit import HS, RY, Z
from helms3 import Helm3, rwrap_prism, sinter
from sdfkit import Shape, capsule, cyl, ellipsoid, half, rbox, rot, round_cone, sphere, torus, tube, unit, v3
from vh2 import ALL, HC, R0, RX, SKULL, VISOR, H, crest_pt, mirror, r, snorm, surf

I3 = np.eye(3)


# ------------------------------------------------------------------------------------------------ 0.3 slot floors
# VH2/VH3 cut prow and cheek vents 0.3 mm wide (VH3's floor). They measure marginal or fill in at the 0.4 mm engraved
# limit (miniature_detail_resolution_check), so 0.3 cuts them 0.5 mm wide, one prow row, two cheek vents 0.9 mm apart.
def _prow_vents(self, rows=(-1.15,), xl=0.62, length=0.3, w=0.25, depth=0.28, ang=12):
    return helms3.Helm.prow_vents(self, rows, xl, length, w, depth, ang)


def _cheeks(self, vents=3, dz=0.0, size=1.0):
    g = self.g
    for s in (-1, 1):
        c = H(s * 1.6, -1.05, -1.0 + dz)
        R = rot(Z, s * 24) @ rot(RY, -s * 12)
        g.add(rbox(c, r(0.42, 1.0 * size, 0.75 * size), R, 0.2 * HS), 0.12)
        face = c + R[:, 0] * s * (0.42 * HS)
        n = min(vents, 2)
        for j in range(n):
            g.cut(rbox(face + R[:, 1] * (j - (n - 1) / 2) * 0.9, (0.25, 0.25, 0.42 * size), R, 0.06))
        g.add(ellipsoid(H(s * 1.85, -0.45, -0.65 + dz), r(0.38, 0.5, 0.42)), 0.15)              # web: cheek guard to ear
    return self


Helm3.prow_vents, Helm3.cheeks = _prow_vents, _cheeks          # only for helms built through this module's process


def glass_cut(m, cutter):
    """Cut a glass recess and record it as glass for the display masks."""
    m.g.cut(cutter)
    m.glass.append(lambda c, k=cutter: k(c) < 0.03)


# ------------------------------------------------------------------------------------------------ 01 Lineguard
def lineguard(h=0.05):
    """VH4-01 Lineguard: the line standard (VH-01 Vigil + VH2-01). Gull-wing split-chevron visor, crown and temple
    plates, keel crest, cheek vents, aural housings with breather hoses, V-prow respirator, right temple lamp,
    aerial stub."""
    m = Helm3(h, top=3.75).skull().plates(crown_t=0.3, temple_t=0.18)
    m.glass_visor(VISOR).jaw("std").cheeks().ears().prow_vents().chin_puck().keel().crest(0.3).lamp(-1)
    m.g.add(capsule(H(1.7, 1.6, 1.6), H(1.85, 2.3, 2.1), 0.4), 0.1)                                 # aerial stub
    m.g.add(sphere(H(1.85, 2.3, 2.1), 0.48), 0.04)
    return m


# ------------------------------------------------------------------------------------------------ 02 Marshal
def marshal(h=0.05):
    """VH4-02 Marshal: sergeant (VH-02 Warden + VH2-05). The line helm under a swept keel blade crest, a command
    antenna, a temple lamp and two raised rank bars."""
    m = Helm3(h, top=5.3).skull().plates(crown_t=0.3, temple_t=0.18)
    m.glass_visor(VISOR).jaw("std").cheeks().ears().prow_vents().chin_puck().keel()
    prof = [(-1.95, 1.85), (-1.2, 3.0), (0.0, 3.55), (1.3, 4.05), (2.5, 4.5), (3.15, 4.35), (3.0, 3.0), (2.4, 1.4),
            (1.0, 2.0), (-0.5, 2.0), (-1.5, 1.4)]
    m.blade_crest(prof, 0.42)
    m.antenna(1, length=4.8, r_mm=0.4).lamp(-1)
    for j in range(2):                                                                             # rank bars, 0.62 mm apart
        p = surf(-R0 * 1.45, 1.05 - 0.95 * j, 0.0)
        m.g.add(rbox(p, (0.25, 0.7, 0.22), rot(Z, -40), 0.08), 0.04)
    return m


# ------------------------------------------------------------------------------------------------ 06 Breacher
def breacher(h=0.05):
    """VH4-06 Breacher (VH-03): a full armoured faceplate bolted over the face, one wide slit lens split by the keel,
    two blast ribs under it, rivets round the plate, a brow shelf and a low crest."""
    m = Helm3(h, top=3.7, front=-4.7, side=3.9).skull().plates(crown_t=0.35, temple_t=0.2, brow_lift=0.2)
    m.faceplate((0, -1.45, -0.55), (1.78, 1.2, 1.55), apex=-2.72, slope=0.3, chin=(-2.15, -1.9), k=0.35)
    g = m.g
    for s in (-1, 1):
        p, R = m.facet_frame(s, s * 0.85, 0.42)
        glass_cut(m, rbox(p, (0.72, 0.32, 0.26), R, 0.08))                                          # slit lens half, 0.52 tall
    for zl in (-0.45, -1.2):                                                                       # blast ribs, 0.84 mm apart
        g.add(capsule(m.facet_point(1, -1.2, zl, 0.05)[0], m.facet_point(1, 1.2, zl, 0.05)[0], 0.24), 0.04)
    for s in (-1, 1):                                                                              # rivets round the plate
        for x, z in ((1.55, 0.95), (1.62, -0.05), (1.4, -1.0), (0.75, -1.55)):
            g.add(sphere(m.facet_point(s, s * x, z, 0.03)[0], 0.24), 0.03)
    m.shelf(mirror([(0.0, 1.55), (2.0, 1.5), (2.9, 1.25), (3.0, 0.95), (2.0, 1.0), (0.0, 1.06)]), 0.55)
    m.ears(hose=False).keel(z0=0.9, z1=0.62).crest(0.3)
    return m


# ------------------------------------------------------------------------------------------------ 07 Sentinel
T_VISOR = mirror([(0.0, 0.78), (1.95, 0.8), (2.55, 0.6), (2.45, 0.12), (0.36, 0.1), (0.34, -1.1), (0.0, -1.15)])


def sentinel(h=0.05):
    """VH4-07 Sentinel (VH-05): smooth egg under a heavy brow ridge, a T-visor (a band across the eyes and a slot down
    the mouth: the keel runs inside the slot), a ribbed sealed jaw and big ear discs."""
    m = Helm3(h, top=3.8).skull().plates(crown_t=0.22, temple_t=0.14, brow_lift=0.5)
    m.jaw("sealed").ears(hose=False, big=1.15)
    m.glass_visor(T_VISOR, depth=0.45, frame=0.48, frame_h=0.22, facet=False)
    g = m.g
    g.add(round_cone(H(-1.75, -2.0, 0.95), H(1.75, -2.0, 0.95), 0.46, 0.46), 0.25)                 # brow ridge
    for j in range(3):                                                                             # jaw ribs, 0.56 mm gaps
        p, _ = m.facet_point(1, 0.0, -1.0 - 0.45 * j / HS, 0.06)
        g.add(rbox(p, (1.0 - 0.15 * j, 0.25, 0.2), I3, 0.08), 0.05)
    m.keel(z0=0.9, z1=-0.4, r_mm=0.24).crest(0.32)
    return m


# ------------------------------------------------------------------------------------------------ 08 Raptor
LENS_SLANT_L = [(0.42, 0.42), (1.6, 0.92), (2.3, 1.06), (2.42, 0.7), (1.55, 0.42), (0.5, -0.06)]
LENS_SLANT_R = [(-s, z) for s, z in LENS_SLANT_L]


def raptor(h=0.05):
    """VH4-08 Raptor (VH-06): a beaked, faceted muzzle with nostril vents, two slanted eye lenses either side of the
    keel ridge running down the beak, and a swept fin crest."""
    m = Helm3(h, top=4.6, front=-4.9, side=3.8).skull().plates(crown_t=0.28, temple_t=0.16)
    m.glass_visor(LENS_SLANT_L, depth=0.32, facet=False).glass_visor(LENS_SLANT_R, depth=0.32, facet=False)
    g = m.g
    beak = round_cone(H(0, -1.0, -0.6), H(0, -3.0, -1.3), 1.35 * HS, 0.55 * HS)
    beak = sinter(beak, half(H(0, -2.0, -0.9), unit((0.55, -0.35, 0.2))) & half(H(0, -2.0, -0.9), unit((-0.55, -0.35, 0.2))), 0.12)
    g.add(beak, 0.45)                                                                              # faceted beak
    for s in (-1, 1):                                                                              # nostril vents
        for j in range(2):
            p = H(s * 0.62, -2.35 + 0.42 * j, -1.05 - 0.15 * j)
            g.cut(rbox(p, (0.2, 0.3, 0.26), rot(Z, s * 30) @ rot(RX, 20), 0.06))
    g.add(tube([crest_pt(8, 0.2), H(0, -2.0, 0.55), H(0, -2.75, -0.55), H(0, -3.1, -1.05)], 0.25), 0.06)  # keel down the beak
    prof = [(-1.6, 1.9), (-0.6, 3.0), (0.6, 3.75), (1.9, 4.35), (3.25, 4.55), (3.4, 3.9), (2.8, 2.4), (1.5, 2.2),
            (0.0, 2.15), (-1.2, 1.5)]
    m.blade_crest(prof, 0.42)                                                                      # swept fin
    m.ears(hose=False).cheeks(vents=2)
    return m


# ------------------------------------------------------------------------------------------------ 09 Diver
def diver(h=0.05):
    """VH4-09 Diver (VH-07 + VH2-02 Tidewall): round dome with one big circular faceport (ring frame, four bolts, a
    keel bar across the glass with a V foot), breather cans on the jaw corners, collar ring with lugs, crest."""
    m = Helm3(h, top=3.9, side=4.2, front=-4.6)
    g = m.g
    dome = ellipsoid(H(0, 0.2, 0.35), r(2.3, 2.55, 2.6))
    g.add(dome)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                       # neck seal
    c, n = H(0, -2.05, 0.15), v3(0, -1, 0)
    g.add(cyl(c - n * 0.6, c + n * 0.5, 1.62 * HS, 0.2), 0.2)                                       # faceport boss
    g.add(torus(c + n * 0.5, n, 1.42 * HS, 0.3), 0.08)                                              # ring frame
    glass = cyl(c + n * 0.25, c + n * 1.5, 1.2 * HS)
    glass_cut(m, glass)
    g.add(capsule(c + v3(0, -0.28, 1.05 * HS), c + v3(0, -0.28, -0.7 * HS), 0.25), 0.04)            # keel bar across the glass
    for s in (-1, 1):
        g.add(capsule(c + v3(0, -0.28, -0.7 * HS), c + v3(s * 0.55 * HS, -0.28, -1.2 * HS), 0.25), 0.04)  # V foot
    for a in (45, 135, 225, 315):                                                                   # four bolts on the ring
        t = math.radians(a)
        g.add(sphere(c + n * 0.75 + v3(1.42 * HS * math.cos(t), 0, 1.42 * HS * math.sin(t)), 0.3), 0.03)
    for s in (-1, 1):                                                                               # breather cans
        a = H(s * 1.45, -1.55, -1.25)
        b = a + unit(v3(s * 0.55, -0.6, -0.45)) * 1.2
        g.add(cyl(a, b, 0.55, 0.14), 0.12)
        g.cut(cyl(b - unit(b - a) * 0.15, b + unit(b - a) * 0.5, 0.3))
    m.collar(z=-1.8, R=2.15, rr=0.42)
    for a in (40, 140, 220, 320):
        t = math.radians(a)
        g.add(rbox(H(2.2 * math.cos(t), 0.15 + 2.2 * math.sin(t), -1.8), (0.38, 0.38, 0.45), rot(Z, a), 0.12), 0.08)
    g.add(tube([crest_pt(a, 0.32) for a in np.linspace(40, 168, 10)], 0.3), 0.1)                   # keel crest, nape to brow
    return m


# ------------------------------------------------------------------------------------------------ 11 Hunter
TALL_C, TALL_R = (0.0, 0.25, 0.75), (1.9, 2.45, 2.95)
TALL = ellipsoid(H(*TALL_C), r(*TALL_R))


def hunter(h=0.05):
    """VH4-11 Hunter (VH-08): tall narrow helm with three vertical lens slits (the centre slit carries the keel line),
    curved mandible guards, a rear sensor spine of four fins."""
    m = Helm3(h, top=4.3, side=3.4, back=4.2)
    g = m.g
    g.add(TALL)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                        # neck seal
    g.add(ellipsoid(H(0, -1.1, -1.0), r(1.3, 1.25, 1.1), rot(RX, 10)), 0.5 * HS)                    # jaw
    for x in (-0.85, 0.0, 0.85):                                                                   # three slits, 0.47 lands
        y = TALL_C[1] - TALL_R[1] * math.sqrt(max(0.0, 1 - (x / TALL_R[0]) ** 2)) + 0.05
        glass_cut(m, rbox(H(x, y, 0.75), (0.25, 0.45, 0.82), rot(Z, -x * 18), 0.08))
    for s in (-1, 1):                                                                              # mandible guards
        g.add(tube([H(s * 1.55, -0.2, -0.3), H(s * 1.65, -1.2, -1.15), H(s * 0.95, -2.05, -1.65), H(s * 0.42, -2.2, -1.75)], 0.36), 0.12)
    for j in range(4):                                                                             # rear sensor spine
        p = H(0, 2.55, 1.6 - 0.95 * j / HS)
        g.add(rbox(p + v3(0, 0.25, 0), (0.22, 0.55, 0.3), I3, 0.08), 0.06)
    g.add(tube([H(0, -2.15, 1.75), H(0, -1.4, 3.3), H(0, 0.4, 3.75), H(0, 1.9, 3.2)], 0.28), 0.06)  # keel over the crown
    m.ears(hose=False, big=0.9)
    return m


# ------------------------------------------------------------------------------------------------ 12 Specter
def specter(h=0.05):
    """VH4-12 Specter (VH-10): a scout helm under a cloth hood. Cowl with a deep face opening and three fold ridges,
    a big monocular lens over the right eye, a split-chevron left eye slot, a filter snout, a seam (keel) over the hood."""
    m = Helm3(h, top=4.1, side=4.2, front=-4.4, back=4.6)
    g = m.g
    hood = ellipsoid(H(0, 0.55, 0.55), r(2.6, 2.95, 2.95))
    g.add(hood)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.3, -1.4), 1.6), 0.5)                                       # cowl falls to the shoulders
    g.cut(ellipsoid(H(0, -2.55, 0.0), r(1.55, 1.7, 1.75)), 0.12)                                   # face opening
    g.add(ellipsoid(H(0, -0.15, -0.15), r(1.45, 1.35, 1.55)), 0.15)                                # face mask, ~1 mm inside the cowl
    rim = [H(1.5 * math.cos(t), -2.05 + 0.35 * math.sin(t) ** 2, 0.05 + 1.65 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 25)]
    g.add(tube(rim, 0.3), 0.1)                                                                     # cowl rim round the face opening
    for s in (-1, 1):                                                                              # fold ridges
        g.add(tube([H(s * 1.2, -1.2, 2.7), H(s * 2.35, -0.2, 1.6), H(s * 2.55, 0.6, -0.4)], 0.3), 0.15)
    g.add(tube([H(0, -1.75, 2.9), H(0, 0.55, 3.6), H(0, 2.9, 1.8), H(0, 3.3, -0.2)], 0.27), 0.08)   # hood seam = keel
    b = H(-0.55, -2.2, 0.15)
    m.lens(b + v3(0, 1.1, 0), b, 0.55, depth=0.3, rim=0.42)                                        # monocular, right eye
    glass_cut(m, rbox(H(0.6, -2.1, 0.2), (0.45, 0.5, 0.26), rot(Z, 15) @ rot((0, 1, 0), -14), 0.08))  # left eye slot
    a = H(0, -2.0, -0.85)
    tip = a + unit(v3(0, -0.8, -0.55)) * 1.1
    g.add(round_cone(a, tip, 0.62, 0.48), 0.12)                                                    # filter snout
    g.cut(cyl(tip - unit(tip - a) * 0.15, tip + unit(tip - a) * 0.5, 0.26))
    return m


# ------------------------------------------------------------------------------------------------ 16 Mender
def mender(h=0.05):
    """VH4-16 Mender (VH2-06): medic. Line helm with two paint channels either side of the crest, a triage scanner bar
    with three lens pits on the right brow, twin filter cans, rear beacon dome."""
    m = Helm3(h).skull().plates(crown_t=0.3, temple_t=0.18)
    m.glass_visor(VISOR).jaw("std").cheeks(vents=2).ears(hose=False).prow_vents(rows=(-0.95,)).keel(z1=-0.9).crest(0.3)  # no ear hose: its 0.3 mm crevice against the cheek filled in
    g = m.g
    for s in (-1, 1):                                                                              # paint channels, 0.6 mm
        band = Shape(lambda Q, s=s: np.abs(Q[:, 0] - s * 0.9) - 0.3, *ALL)
        g.cut((band & SKULL.offset(0.6)) - SKULL.offset(-0.05))
    bar_c = surf(-R0 * 0.45, 1.35, 0.25)
    g.add(rbox(bar_c, (0.95, 0.38, 0.32), rot(Z, -18), 0.12), 0.08)                                # scanner bar
    for j in range(3):
        g.cut(sphere(bar_c + rot(Z, -18) @ v3(-0.6 + 0.6 * j, -0.32, 0), 0.24))
    for s in (-1, 1):                                                                              # twin filter cans
        a = H(s * 0.85, -2.15, -1.45)
        b = a + unit(v3(s * 0.55, -0.7, -0.45)) * 1.05
        g.add(cyl(a, b, 0.5, 0.14), 0.1)
        g.cut(cyl(b - unit(b - a) * 0.12, b + unit(b - a) * 0.5, 0.27))
    g.add(sphere(H(0, 2.55, 1.0), 0.58), 0.12)                                                     # rear beacon
    return m


# ------------------------------------------------------------------------------------------------ 17 Wright
def wright(h=0.05):
    """VH4-17 Wright (VH2-07): engineer. Flip-up magnifier goggles on a strap hugging the dome, brow headlamp with its
    cable along the crown line, tool port on the left."""
    m = Helm3(h, top=3.9).skull().plates(crown_t=0.3, temple_t=0.18)
    m.glass_visor(VISOR).jaw("std").cheeks().ears().prow_vents().chin_puck().keel()
    g = m.g
    sn, sc = unit(v3(0, -0.55, 1)), H(0, 0.25, 1.85)
    strap = Shape(lambda Q: np.abs((Q - sc) @ sn) - 0.27, *ALL)
    g.add((strap & SKULL.offset(0.42)) - SKULL.offset(-0.2), 0.05)                                 # goggle strap
    for s in (-1, 1):
        c = surf(s * 0.8, 2.12, 0.5)
        n = unit(snorm(s * 0.8, 2.12) + v3(0, -0.5, 0.3))
        g.add(cyl(c - n * 0.4, c + n * 0.45, 0.62, 0.12), 0.1)                                     # goggle lens housings
        glass_cut(m, cyl(c + n * 0.28, c + n * 0.9, 0.38))
    g.add(capsule(surf(-0.8, 2.12, 0.5), surf(0.8, 2.12, 0.5), 0.28), 0.05)                         # bridge
    lc, fwd = surf(0, 1.2, 0.6), unit(v3(0, -1, -0.1))
    g.add(rbox(lc + v3(0, 0.25, 0.0), (0.62, 0.55, 0.42), I3, 0.15), 0.1)                          # headlamp
    g.add(cyl(lc - fwd * 0.2, lc + fwd * 0.55, 0.54, 0.1), 0.05)
    g.cut(cyl(lc + fwd * 0.38, lc + fwd * 1.0, 0.34))
    g.add(tube([lc + v3(0, 0.55, 0.2)] + [crest_pt(a, 0.3) for a in (55, 85, 120, 160)], 0.28), 0.1)  # cable = keel line
    p = surf(R0 * 1.55, 0.95, 0.05)
    g.add(cyl(p - v3(0.25, 0, 0), p + v3(0.4, 0, 0), 0.52, 0.1), 0.08)                             # tool port
    g.cut(cyl(p + v3(0.2, 0, 0), p + v3(0.8, 0, 0), 0.26))
    return m


# ================================================================================================ ported from VH3
# The eight VH3 designs (tools/helms3.py, unchanged there), copied so 0.3 can raise their slot floors:
# every vent, grille slot and crack cut 0.3 mm wide in 0.2 is 0.44-0.5 mm here, re-spaced so ribs stay >= 0.4 mm.
from helms3 import (GLOBE, GLOBE_C, GLOBE_R, LENS_L, LENS_R, VISOR_FROWN, VISOR_SLIT, VISOR_SNIPE, VISOR_WRAP, WINDOW,  # noqa: E402
                    hu, notch)
from vh2 import gouge, pit  # noqa: E402

# ------------------------------------------------------------------------------------------------ VH4 (from VH3-01 drop trooper
def drop(h=0.05):
    """VH4 (from VH3-01 Plummet: drop trooper. Wide wrap-around chevron visor under a ramped brow shelf, flat keel ridge plate,
    jaw armour that flares out and down (a trapezoid front silhouette), V-prow respirator, rear drop beacon."""
    m = Helm3(h, top=3.75, side=4.0).skull().plates(crown_t=0.3, temple_t=0.15, brow_lift=0.45)
    m.glass_visor(VISOR_WRAP, depth=0.34, frame=0.45, frame_h=0.16).jaw("std")                     # glass first: prow overrides its V tip
    g = m.g
    for s in (-1, 1):                                                                              # flared jaw armour
        c = H(s * 1.95, -0.7, -1.3)
        R = rot(Z, s * 14) @ rot(RY, -s * 27)
        g.add(rbox(c, r(0.44, 1.5, 1.05), R, 0.16 * HS), 0.3)
        g.add(ellipsoid(H(s * 1.5, -0.75, -1.2), r(0.55, 1.2, 0.8)), 0.3)                         # web into the jaw
        face = c + R[:, 0] * s * (0.44 * HS)
        for j in range(3):
            g.cut(rbox(face + R[:, 1] * (j - 1) * 0.95, (0.25, 0.25, 0.46), R, 0.06))           # three vents 0.5, ribs 0.45
    m.prow_vents().chin_puck()
    shelf_poly = mirror([(0.0, 2.0), (2.0, 2.0), (3.3, 1.7), (3.45, 1.06), (2.0, 1.1), (0.0, 1.14)])
    m.shelf(shelf_poly, 0.8)                                                           # brow ridge
    m.keel(z0=0.86, z1=-1.0)
    m.ridge(half_w=0.48, proud=0.62, z_min=0.6)                                                    # flat keel ridge plate
    g.add(sphere(H(0, 2.55, 1.35), 0.55), 0.12)                                                    # rear drop beacon
    for s in (-1, 1):
        g.add(capsule(H(s * 1.35, 1.95, 1.45), H(s * 1.5, 2.55, 0.65), 0.34), 0.1)                 # grab-bar studs
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-02 recon
def recon(h=0.05):
    """VH4 (from VH3-02 Sightline: recon. Two narrow chevron lenses split by the keel, a big optic/rangefinder pod clamped to the
    right side on a bracket (the silhouette goes asymmetric), whip antenna swept back along the left side."""
    m = Helm3(h, top=3.7, side=4.5, back=4.6).skull().plates(crown_t=0.22)
    m.glass_visor(LENS_L, depth=0.32, facet=False).glass_visor(LENS_R, depth=0.32, facet=False)
    m.jaw("std").ears(hose=False).prow_vents(rows=(-1.0,)).chin_puck()
    m.keel(z0=0.7).crest(0.3)
    g = m.g
    c = H(-3.0, -0.45, 0.8)
    Rp = rot(Z, -8)
    g.add(rbox(H(-2.3, -0.1, 0.6), (0.85, 0.8, 0.52), Rp, 0.15), 0.1)                              # clamp bracket
    g.add(rbox(c, (1.0, 1.45, 0.85), Rp, 0.24), 0.08)                                              # optic pod
    fwd, side, up = Rp @ v3(0, -1, 0), Rp @ v3(-1, 0, 0), v3(0, 0, 1)
    front = c + fwd * 1.4
    m.lens(front - fwd * 0.3 + up * 0.2, front + fwd * 0.4 + up * 0.2, 0.5)                       # main objective
    m.lens(front - fwd * 0.3 - up * 0.38 - side * 0.3, front + fwd * 0.2 - up * 0.38 - side * 0.3, 0.22, rim=0.3)  # rangefinder
    for j in range(3):                                                                             # cooling slots, outboard face
        p = c + side * 1.0 + fwd * (j - 1) * 0.95 + up * 0.05
        g.cut(rbox(p, (0.25, 0.25, 0.42), np.stack([fwd, side, up], axis=1), 0.06))
    g.add(rbox(c + up * 0.85 - fwd * 0.35, (0.5, 0.45, 0.22), Rp, 0.1), 0.06)                       # range dial cap
    a = H(2.3, 0.45, 0.35)                                                                          # swept whip antenna, left
    g.add(cyl(a - v3(0.3, 0, 0), a + v3(0.2, 0, 0), 0.55, 0.12), 0.1)
    b = H(1.85, 3.1, 1.5)
    g.add(capsule(a, b, 0.38), 0.06)
    g.add(sphere(b, 0.5), 0.05)
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-03 heavy assault
def assault(h=0.05):
    """VH4 (from VH3-03 Ironclad: heavy assault. Squat thick shell, a broad V-faceted faceplate with a portcullis grille (vertical
    slots; the centre bar is the keel), a narrow armoured slit visor under a brow hood, corrugated breathing hoses
    from the faceplate round the jaw into a collar ring."""
    m = Helm3(h, top=3.6, front=-4.7, side=4.3).skull().plates(crown_t=0.4, temple_t=0.24, brow_lift=0.1)
    g = m.g
    g.cut(Shape(lambda Q: hu(2.0) - Q[:, 2], (-9, -9, hu(2.0)), (9, 9, 20)))                       # flat-topped: crown cut off
    g.add(rbox(H(0, 0.3, 1.95), r(1.9, 2.2, 0.32), np.eye(3), 0.14), 0.25)                          # armoured cap plate
    g.add(rbox(H(0, 0.3, 2.25), r(0.3, 2.2, 0.2), np.eye(3), 0.1), 0.06)                           # keel ridge on the cap
    m.glass_visor(VISOR_SLIT, depth=0.3, frame=0.45, frame_h=0.18, facet=False)                    # glass first
    m.faceplate((0, -1.75, -1.05), (1.72, 1.0, 1.05), apex=-2.78, slope=0.33)
    for s in (-1, 1):                                                                              # jowls
        cj = H(s * 1.9, -0.95, -1.2)
        Rj = rot(Z, s * 22) @ rot(RY, -s * 10)
        g.add(rbox(cj, r(0.5, 1.0, 0.85), Rj, 0.16 * HS), 0.14)
    for s in (-1, 1):                                                                              # portcullis grille
        for j, xm in enumerate((0.45, 1.4)):
            ztop, zbot = -0.5, -1.72 + 0.22 * j
            p, R = m.facet_frame(s, s * xm / HS, (ztop + zbot) / 2)
            g.cut(rbox(p, (0.25, 0.34, HS * (ztop - zbot) / 2), R, 0.06))
    p, R = m.facet_frame(1, 0.0, -0.32, 0.0)
    g.add(rbox(p + v3(0, -0.05, 0), (1.55, 0.2, 0.24), np.eye(3), 0.08), 0.05)                     # grille header bar
    m.shelf(mirror([(0.0, 1.35), (2.0, 1.35), (2.75, 1.15), (2.85, 0.82), (2.0, 0.84), (0.0, 0.86)]), 0.52)  # brow hood
    m.ears(hose=False)
    m.collar(z=-1.85, R=2.3, rr=0.45)
    for s in (-1, 1):
        g.add(cyl(H(s * 1.3, -2.15, -1.35), H(s * 1.75, -2.75, -1.5), 0.5, 0.12), 0.08)            # hose ports
        m.hose([H(s * 1.6, -2.5, -1.45), H(s * 2.25, -1.7, -1.72), H(s * 2.5, -0.4, -1.82), H(s * 2.25, 0.95, -1.88),
                H(s * 1.45, 1.85, -1.88)], rad=0.32, bead=0.4)
    m.keel(z0=0.56, z1=-0.42, r_mm=0.28)
    g.add(tube([crest_pt(a, 0.25) for a in (14, 30, 46, 54)], 0.3), 0.08)                          # keel from the cap down to the visor
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-04 officer
def officer(h=0.05):
    """VH4 (from VH3-04 Herald: officer. Stern 'frown' visor (top edge falls outward), a tall stepped keel fin crest, a comm mast
    with two cross spars on the right rear, three raised rank chevrons on the left side."""
    m = Helm3(h, top=5.9, side=4.0, back=4.4).skull().plates().glass_visor(VISOR_FROWN)
    m.jaw("std").cheeks().ears().prow_vents().chin_puck().keel(z0=1.4)
    prof = [(-1.8, 1.7), (-1.0, 2.95), (0.0, 3.6), (1.0, 4.3), (2.0, 5.05), (2.7, 5.45), (3.15, 5.2), (3.1, 4.1),
            (2.7, 1.5), (1.0, 2.1), (-0.5, 2.1), (-1.5, 1.3)]
    m.blade_crest(prof, 0.4)
    g = m.g
    a = H(-2.15, 0.95, 0.55)
    up = unit(v3(-0.1, 0.22, 1))
    g.add(cyl(a + v3(0.35, 0, 0), a - v3(0.25, 0, 0), 0.62, 0.12), 0.1)                            # mast boss
    top = a + up * 5.0
    g.add(capsule(a, top, 0.4), 0.06)
    for d in (3.3, 4.3):                                                                           # cross spars
        p = a + up * d
        g.add(capsule(p - v3(0, 0.55, 0), p + v3(0, 0.55, 0), 0.38), 0.06)
    g.add(sphere(top, 0.52), 0.05)
    for j in range(2):                                                                             # rank chevrons
        zc = 1.95 - 0.55 * j
        arm = [surf(sv, zc - 0.4 * (1 - abs(sv - 3.05) / 0.85), 0.12) for sv in np.linspace(2.2, 3.9, 7)]
        g.add(tube(arm, 0.28), 0.1)
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-05 sealed void
def gpt(a_deg, lift=0.3):
    """Point on the globe's mid-plane at angle a from the front (0 = front, 90 = top), lifted by lift mm."""
    a = math.radians(a_deg)
    return H(0, 0.15 - 2.65 * math.cos(a), 0.35 + 2.6 * math.sin(a)) + v3(0, -math.cos(a), math.sin(a)) * lift


def void(h=0.05):
    """VH4 (from VH3-05 Stillwater: sealed void helm. A round globe with a big domed window (arched top, V lower edge) split by
    an external keel rib running from the back over the crown, down the glass to the chin; heavy collar ring with six
    bolts, a life-support pack on the back with hoses to the collar, two temple lamps, an antenna stub."""
    m = Helm3(h, top=3.9, side=4.0, back=4.6)
    g = m.g
    g.add(GLOBE)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                        # neck seal
    m.glass_visor(WINDOW, depth=0.3, frame=0.5, frame_h=0.22, facet=False, shell=GLOBE, c=GLOBE_C, radii=GLOBE_R)
    g.add(tube([gpt(a, -0.04) for a in np.linspace(-38, 172, 18)], 0.32), 0.06)                     # keel rib, seated on the glass
    m.collar(z=-1.9, R=2.05, rr=0.42)
    for k in range(6):
        t = math.radians(30 + 60 * k)
        g.add(sphere(H(2.38 * math.cos(t), 0.15 + 2.38 * math.sin(t), -1.9), 0.3), 0.04)            # collar bolts
    pc = H(0, 2.85, -0.25)
    g.add(rbox(pc, r(1.2, 0.55, 1.05), np.eye(3), 0.22), 0.15)                                       # life-support pack
    for s in (-1, 1):
        g.cut(rbox(pc + v3(s * 0.45, 0.62, 0.1), (0.25, 0.3, 0.6), np.eye(3), 0.06))                # pack vents 0.5
        m.hose([H(s * 1.05, 2.75, -0.95), H(s * 2.15, 1.75, -1.5), H(s * 2.3, 0.4, -1.75)], rad=0.3, bead=0.38)
        base = surf(s * R0 * 1.32, 1.05, 0.0)                                                       # temple lamps
        m.lens(base + v3(0, 0.35, 0), base + v3(0, -0.55, 0), 0.3, depth=0.25, rim=0.42)
    g.add(capsule(H(-0.9, 1.6, 2.25), H(-1.0, 2.2, 3.1), 0.38), 0.1)                                 # antenna stub
    g.add(sphere(H(-1.0, 2.2, 3.1), 0.48), 0.05)
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-06 open-face crew
def crew(h=0.05):
    """VH4 (from VH3-06 Deckhand: open-face crew cap. A low padded cap (keel ridge and two side ribs) cut away above the face,
    big headset ear cups, one-piece chevron goggles worn up on the brim, boom mic, chin strap; the face is bare."""
    m = Helm3(h, top=3.3, side=4.3)
    g = m.g
    g.add(ellipsoid(H(0, -0.35, -0.45), r(1.2, 1.6, 1.55)))                                         # head
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                        # neck
    cut_n, cut_p = unit((0, -0.5, -1)), H(0, 0, -0.25)
    cap = SKULL.offset(0.1).clip(half(cut_p, cut_n))
    g.add(cap, 0.25)
    rim = Shape(lambda Q: np.maximum((Q - cut_p) @ cut_n, -((Q - cut_p) @ cut_n) - 0.42), *ALL)
    g.add(SKULL.offset(0.32) & rim, 0.06)                                                           # rolled brim lip
    m.ridge(half_w=0.42, proud=0.42, z_min=0.9, shell=SKULL)                                        # keel ridge
    for s in (-1, 1):
        k_ = math.sqrt(1 - (1.05 / HS / 2.15) ** 2)                                                # padded side ribs (tubes:
        rib = [H(s * 1.05 / HS, 0.25 - 2.5 * k_ * math.cos(a), 0.3 + 2.5 * k_ * math.sin(a)) +             #  round ends, no wedges)
               v3(0, -math.cos(a), math.sin(a)) * 0.12 for a in np.radians(np.linspace(48, 150, 9))]
        g.add(tube(rib, 0.27), 0.08)
    face = [
        (capsule(H(-0.55, -1.86, 0.25), H(0.55, -1.86, 0.25), 0.21), 0.12),                       # brow
        (round_cone(H(0, -1.92, 0.05), H(0, -2.16, -0.5), 0.17, 0.25), 0.1),                      # nose
        (ellipsoid(H(-0.6, -1.7, -0.45), r(0.3, 0.24, 0.22)), 0.12),                              # cheekbones
        (ellipsoid(H(0.6, -1.7, -0.45), r(0.3, 0.24, 0.22)), 0.12),
        (ellipsoid(H(0, -1.66, -1.3), r(0.55, 0.4, 0.36)), 0.15),                                  # chin
    ]
    for sh, k in face:
        g.add(sh, k)
    for s in (-1, 1):
        g.cut(sphere(H(s * 0.42, -1.97, -0.05), 0.24), 0.06)                                        # eye sockets
        g.add(sphere(H(s * 0.42, -1.84, -0.08), 0.16), 0.02)                                        # eyes
    g.cut(capsule(H(-0.28, -1.98, -0.92), H(0.28, -1.98, -0.92), 0.22))                            # mouth 0.44
    gog = mirror([(0.0, 1.38), (1.5, 1.52), (2.35, 1.62), (2.5, 1.32), (1.5, 1.02), (0.0, 0.88)])  # goggles worn up
    P = rwrap_prism(gog)
    g.add((P.offset(0.45) & SKULL.offset(0.5)) - SKULL.offset(0.0), 0.06)                          # goggle body
    g.cut((P & SKULL.offset(1.2)) - SKULL.offset(0.24))                                             # lenses
    g.add((Shape(lambda Q: np.abs(Q[:, 0]) - 0.3, *ALL) & P.offset(0.5)) & SKULL.offset(0.5), 0.04)  # bridge = keel split
    m.glass.append(lambda c, P=P: (P(c) < -0.03) & (SKULL(c) < 0.3) & (np.abs(c[:, 0]) > 0.32))
    for s in (-1, 1):
        g.add(tube([surf(s * 2.75, 1.25, 0.25), surf(s * 3.4, 0.75, 0.25), H(s * 2.05, 0.0, 0.35)], 0.27), 0.06)  # strap
        a, b = H(s * 1.85, 0.0, -0.35), H(s * 2.6, 0.0, -0.35)
        g.add(cyl(a, b, 0.95, 0.28), 0.12)                                                         # ear cup
        g.cut(cyl(b - v3(s * 0.18, 0, 0), b + v3(s * 0.5, 0, 0), 0.55))
        g.add(sphere(b - v3(s * 0.12, 0, 0), 0.27), 0.04)
        g.add(tube([H(s * 1.95, -0.35, -0.95), H(s * 1.05, -1.3, -1.6), H(0, -1.5, -1.72)], 0.27), 0.1)  # chin strap, under the chin
    g.add(tube([H(2.4, -0.45, -0.75), H(1.95, -1.25, -1.0), H(1.1, -1.82, -0.98)], 0.27), 0.06)     # boom mic
    g.add(sphere(H(0.95, -1.86, -0.98), 0.38), 0.06)
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-07 sniper
def sniper(h=0.05):
    """VH4 (from VH3-07 Longsight: sniper. Compact chevron visor, a long sallet tail sweeping back over the neck (two lames),
    a flip-down monocular on a brow hinge sitting in front of the right lens, a low crest."""
    m = Helm3(h, top=3.6, side=3.9, front=-4.6, back=5.3).skull().plates(crown_t=0.22, nape=False)
    m.glass_visor(VISOR_SNIPE).jaw("std").cheeks(vents=2).ears().prow_vents(rows=(-0.95,)).chin_puck()
    g = m.g
    tail = ellipsoid(H(0, 0.9, -0.1), r(2.4, 3.5, 2.3))
    tail = sinter(sinter(tail, half(H(0, 1.0, 0), (0, -1, 0)) & half(H(0, 0, 1.2), Z) & half(H(0, 3.75, 0), (0, 1, 0)), 0.25),
                  half(H(0, 1.3, -1.95), unit((0, 0.5, -1))), 0.35)                                 # rounded rim, no knife edge
    g.add(tail, 0.35)
    for zl in (0.35, -0.4):                                                                      # two lames across the tail
        band = Shape(lambda Q, z0=hu(zl): np.abs(Q[:, 2] - z0) - 0.16, *ALL)
        side = Shape(lambda Q: np.abs(Q[:, 0]) - 1.45, *ALL)
        back = Shape(lambda Q: HS * 1.6 + HC[1] - Q[:, 1], *ALL)
        g.cut(((band & side & back) & tail.offset(0.6)) - tail.offset(-0.3))
    m.keel(z0=1.2).crest(0.27)
    hub = surf(-R0 * 0.55, 1.62, 0.32)                                                              # flip-down monocular
    g.add(sphere(hub, 0.5), 0.08)
    g.add(cyl(hub - v3(0.45, 0, 0), hub + v3(0.45, 0, 0), 0.38, 0.1), 0.05)                        # hinge pin housing
    eye = surf(-1.15, 0.6, 0.0)
    bc = eye + v3(0, -0.95, 0)
    g.add(capsule(hub, bc + v3(0, 0.25, 0.45), 0.32), 0.06)                                         # drop arm
    m.lens(bc + v3(0, 0.95, 0), bc + v3(0, -0.75, 0), 0.38, depth=0.28, rim=0.24)                   # barrel, glass at the front
    g.add(torus(bc + v3(0, -0.2, 0), (0, 1, 0), 0.62, 0.14), 0.04)                                  # focus ring
    return m


# ------------------------------------------------------------------------------------------------ VH4 (from VH3-08 scarred, relief face
def grim(h=0.05, seed=31):
    """VH4 (from VH3-08 Grimward: veteran's helm with an original relief death's-head faceplate made of Vigil parts (chevron
    lenses as eye sockets under raised brow arcs, a V vent as the nose, cheek ridges, jaw vents as teeth), then
    battle damage: gouges, pits, a bitten crest, a torn cheek corner, a cracked lens and a snapped antenna."""
    m = Helm3(h, top=3.7, side=3.9).skull().plates(crown_t=0.3, brow_lift=0.25)
    g = m.g
    m.faceplate((0, -1.3, -0.45), (1.8, 1.28, 1.6), apex=-2.55, slope=0.28, chin=(-2.05, -1.85), k=0.4)
    m.cheeks(vents=2).ears()
    for s in (-1, 1):
        p, R = m.facet_frame(s, s * 0.95, 0.38)                                                      # chevron eye lenses
        Rl = R @ rot((0, 1, 0), s * 22)
        cutter = rbox(p, (0.62, 0.3, 0.3), Rl, 0.12)
        g.cut(cutter)
        m.glass.append(lambda c, k=cutter: k(c) < 0.03)
        arc = [m.facet_point(s, s * x, z, 0.04)[0] for x, z in ((0.25, 0.86), (0.85, 1.05), (1.55, 0.82), (1.85, 0.42))]
        g.add(tube(arc, 0.26), 0.05)                                                                 # brow arc
        g.add(capsule(m.facet_point(s, s * 0.5, -0.12, 0.04)[0], m.facet_point(s, s * 1.6, -0.42, 0.04)[0], 0.25), 0.05)  # cheek ridge
        g.cut(capsule(m.facet_point(s, 0.0, -0.08, 0.0)[0], m.facet_point(s, s * 0.32, -0.55, 0.0)[0], 0.25))  # nasal vent
    g.add(capsule(m.facet_point(1, -1.25, -0.9, 0.04)[0], m.facet_point(1, 1.25, -0.9, 0.04)[0], 0.26), 0.05)  # upper lip bar
    for s in (-1, 1):                                                                              # teeth = jaw vents
        for xm in (0.4, 1.32):
            p, R = m.facet_frame(s, s * xm / HS, -1.42)
            g.cut(rbox(p, (0.25, 0.32, 0.3), R, 0.05))
    m.crest(0.3, a0=12, a1=78)
    prof = [(-1.2, 2.4), (-0.6, 3.1), (-0.2, 2.8), (0.3, 3.35), (0.6, 3.0), (1.2, 3.95), (2.2, 4.25), (2.8, 3.75),
            (2.9, 2.6), (2.5, 1.4), (0.8, 2.0), (-0.6, 2.0)]
    m.blade_crest(prof, 0.38)                                                                       # shattered keel fin
    g.add(tube([crest_pt(14, 0.1), crest_pt(4, 0.0), m.facet_point(1, 0.0, 0.7, 0.0)[0]], 0.27), 0.05)  # keel to the brow split
    a = H(-2.25, 0.55, 0.3)                                                                         # snapped antenna
    g.add(cyl(a + v3(0.35, 0, 0), a - v3(0.15, 0, 0), 0.55, 0.12), 0.1)
    b = a + unit(v3(-0.12, 0.35, 1)) * 1.5
    g.add(cyl(a, b, 0.42, 0.06), 0.06)                                                             # snapped antenna: flat stump
    g.cut(sphere(b + unit(v3(-0.12, 0.35, 1)) * 0.1, 0.24))                                         # broken core
    gouge(g, surf(0.75, 2.6, 0.24), surf(1.4, 2.2, 0.24), 0.3)                                     # battle damage, clear of the crest
    gouge(g, surf(0.7, 2.45, 0.24), surf(1.3, 2.1, 0.24), 0.27)
    gouge(g, surf(-0.5, 2.6, 0.24), surf(-1.3, 2.15, 0.24), 0.28)
    notch(g, crest_pt(100, 1.0), (0, 0.17, 0.98), 0.55, 0.75)                                       # crest bitten through
    for q_ in ((-1.45, -2.05, -1.45), (-1.25, -2.2, -1.2)):                                        # shrapnel strikes, right cheek
        pit(g, H(*q_), (-0.5, -0.8, -0.2), 0.3)
    for s, z in ((-2.0, 1.7), (2.2, 1.95), (-3.3, 0.85), (-0.5, 2.45), (3.5, 0.1)):
        pit(g, surf(s, z, 0.25), snorm(s, z), 0.32)
    p, R = m.facet_frame(1, 0.95, 0.38)                                                             # cracked left lens
    for d in ((0.55, 0.35), (-0.5, 0.3), (0.3, -0.42)):
        g.cut(capsule(p + R[:, 1] * 0.05, p + R[:, 0] * d[0] + R[:, 2] * d[1] + R[:, 1] * 0.05, 0.22))
    return m


def _vh3(ident):
    return lambda h=0.05: helms3.VH3[ident][2](h)


VH4 = {
    "VH4-01": ("Lineguard", "line standard: gull-wing split visor, keel crest, cheek vents, aural hoses, lamp", lineguard),
    "VH4-02": ("Marshal", "sergeant: swept blade crest, command antenna, rank bars", marshal),
    "VH4-03": ("Plummet", "drop trooper: wrap visor under a brow shelf, flared jaw armour (VH3-01)", drop),
    "VH4-04": ("Sightline", "recon: twin chevron lenses, side optic pod, whip antenna (VH3-02)", recon),
    "VH4-05": ("Ironclad", "heavy assault: portcullis faceplate, slit visor, hoses to a collar (VH3-03)", assault),
    "VH4-06": ("Breacher", "armoured faceplate, slit lens, blast ribs, rivets", breacher),
    "VH4-07": ("Sentinel", "T-visor under a heavy brow, ribbed sealed jaw, big ear discs", sentinel),
    "VH4-08": ("Raptor", "faceted beak, slanted eye lenses, swept fin crest", raptor),
    "VH4-09": ("Diver", "round faceport with bolts, breather cans, collar ring", diver),
    "VH4-10": ("Stillwater", "sealed void globe, domed window, back pack and hoses (VH3-05)", void),
    "VH4-11": ("Hunter", "tall helm, three lens slits, mandible guards, rear sensor spine", hunter),
    "VH4-12": ("Specter", "scout under a hood: monocular, eye slot, filter snout", specter),
    "VH4-13": ("Herald", "officer: frown visor, stepped fin crest, comm mast, rank chevrons (VH3-04)", officer),
    "VH4-14": ("Longsight", "sniper: sallet tail, flip-down monocular (VH3-07)", sniper),
    "VH4-15": ("Deckhand", "open-face crew cap, goggles up, headset, boom mic (VH3-06)", crew),
    "VH4-16": ("Mender", "medic: paint channels, triage scanner, twin filters, beacon", mender),
    "VH4-17": ("Wright", "engineer: flip-up goggles, headlamp, tool port", wright),
    "VH4-18": ("Grimward", "scarred veteran: relief death's-head faceplate, shattered fin (VH3-08)", grim),
}


def helm_obj(ident, h=0.05):
    return VH4[ident][2](h)


def helm(ident, h=0.05):
    """Finished sculpt (flat neck seat + 1.6 mm D-flat peg) with .glass masks for display."""
    m = helm_obj(ident, h)
    g = m.finish()
    g.glass = m.glass
    return g
