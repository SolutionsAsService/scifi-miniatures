"""Armory: the shared parts library of the Aster Compact Vigilant line (original designs).

Registries a figure (or a bits package) pulls from by identifier:
- HELMS   VH-01..: helm designs, each a separate keyed part (neck cut at z = 0, 1.6 mm D-flat peg down, faces -y)
- WEAPONS VW-01..: weapons in the local weapon frame (x to the muzzle, z up, origin = the main grip / fist centre)
- ARMOUR  VA-01..: bolt-on armour bits (shoulder caps, knee guards) as loose printable parts
Every feature is >= 0.6 mm printed (MSLA resin), lens recesses >= 0.25 mm deep, no knife edges.
Use: armory.helm("VH-06"), armory.weapon("VW-05"), armory.armour("VA-02"); armory.catalogue() lists them all.
"""
from __future__ import annotations

import math

import numpy as np

import exosuit as X
from exosuit import HEAD_UP, HS, I3, PEG_HEAD, RY, Z
from sdfkit import Sculpt, Shape, capsule, cyl, d_peg, ellipsoid, rbox, rot, round_cone, sphere, torus, tube, unit, v3


# ------------------------------------------------------------------------------------------------ helms
def _helm_frame():
    hc = v3(0, 0, HEAD_UP)
    return (lambda x, y, z: hc + HS * v3(x, y, z)), (lambda *a: tuple(HS * x for x in a))


def _finish_helm(g):
    g.cut(Shape(lambda Q: Q[:, 2], (-9, -9, -9), (9, 9, 0)))                                     # flat seat at z = 0
    g.add(d_peg((0, 0, 0.3), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["len"] + 0.3, key=(0, -1, 0)))
    return g


def _shell(top=3.6, h=0.06):
    H, r = _helm_frame()
    g = Sculpt((-4.4, -4.8, -PEG_HEAD["len"] - 0.3), (4.4, 4.8, HEAD_UP + HS * top), h)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                  # neck seal
    return g, H, r


def sentinel(h=0.06):
    """VH-05 Sentinel: smooth egg, T-visor (horizontal band + vertical slot), brow ridge, ribbed jaw."""
    g, H, r = _shell(h=h)
    g.add(ellipsoid(H(0, 0.2, 0.3), r(2.25, 2.55, 2.6)))
    g.add(ellipsoid(H(0, -1.3, -1.15), r(1.55, 1.3, 1.1)), 0.5 * HS)
    g.add(round_cone(H(-1.7, -2.05, 0.75), H(1.7, -2.05, 0.75), 0.42, 0.42), 0.25)            # brow ridge
    g.cut(rbox(H(0, -2.6, 0.15), r(1.75, 0.6, 0.3), I3, 0.12))                                 # visor band
    g.cut(rbox(H(0, -2.45, -0.8), r(0.32, 0.6, 0.85), I3, 0.1))                                # vertical slot
    for j in range(3):
        g.add(rbox(H(0, -2.35 + 0.1 * j, -1.25 - 0.32 * j), r(1.05 - 0.15 * j, 0.25, 0.12), I3, 0.08), 0.06)  # jaw ribs
    for s in (-1, 1):
        g.add(cyl(H(s * 2.0, 0.1, -0.1), H(s * 2.45, 0.1, -0.1), 0.62 * HS, 0.18), 0.12)        # ear discs
    return _finish_helm(g)


def raptor(h=0.06):
    """VH-06 Raptor: beaked angular muzzle, two narrow slanted eye slits, swept fin crest."""
    g, H, r = _shell(top=4.4, h=h)
    g.add(ellipsoid(H(0, 0.4, 0.3), r(2.1, 2.5, 2.5)))
    g.add(round_cone(H(0, -1.0, -0.6), H(0, -3.0, -1.35), 1.35 * HS, 0.55 * HS), 0.45)           # beak
    for s in (-1, 1):
        g.add(ellipsoid(H(s * 1.3, -1.2, -0.9), r(0.75, 1.4, 1.0), rot(Z, s * 22)), 0.35)       # cheek blades
        g.cut(rbox(H(s * 0.95, -2.35, 0.35), r(0.75, 0.5, 0.2), rot(RY, s * 28) @ rot(Z, -s * 12), 0.08))  # eye slits
    fin = [H(0, -1.6, 2.2), H(0, 0.2, 2.95), H(0, 1.9, 2.6), H(0, 3.2, 1.6)]
    g.add(tube(fin, 0.36), 0.2)                                                                # fin crest (0.72 mm)
    return _finish_helm(g)


def diver(h=0.06):
    """VH-07 Diver: round dome with a big circular faceplate lens, four bolts, breather cans."""
    g, H, r = _shell(h=h)
    g.add(sphere(H(0, 0.1, 0.35), 2.55 * HS))
    g.add(torus(H(0, -2.45, 0.1), (0, 1, 0), 1.35 * HS, 0.32 * HS), 0.15)                       # faceplate rim
    g.cut(cyl(H(0, -3.2, 0.1), H(0, -2.25, 0.1), 1.15 * HS))                                    # lens recess
    g.add(cyl(H(0, -2.35, 0.1), H(0, -2.1, 0.1), 1.1 * HS), 0.05)                               # lens face 0.3 mm back
    for a in (45, 135, 225, 315):
        t = math.radians(a)
        g.add(sphere(H(1.75 * math.cos(t), -2.05, 0.1 + 1.75 * math.sin(t)), 0.34 * HS), 0.06)  # bolts
    for s in (-1, 1):
        g.add(cyl(H(s * 1.6, -0.8, -1.7), H(s * 1.75, 0.2, -2.0), 0.55 * HS, 0.15), 0.25)       # breather cans
    return _finish_helm(g)


def hunter(h=0.06):
    """VH-08 Hunter: tall narrow helm, three vertical lens slits, mandible jaw guards, rear sensor spine."""
    g, H, r = _shell(top=4.0, h=h)
    g.add(ellipsoid(H(0, 0.3, 0.6), r(2.0, 2.45, 2.9)))
    for x in (-0.75, 0.0, 0.75):
        g.cut(rbox(H(x, -2.35, 0.55), r(0.22, 0.55, 0.7), I3, 0.08))                           # lens slits
    for s in (-1, 1):
        g.add(round_cone(H(s * 1.5, -0.6, -0.6), H(s * 0.75, -2.5, -1.85), 0.62 * HS, 0.42 * HS), 0.3)  # mandibles
    g.add(tube([H(0, 1.0, 2.9), H(0, 2.3, 2.2), H(0, 2.9, 0.8)], 0.38), 0.2)                   # rear spine
    return _finish_helm(g)


def bulwark(h=0.06):
    """VH-09 Bulwark: assault helm, heavy jaw and armoured collar, deep brow, single narrow visor slit."""
    g, H, r = _shell(h=h)
    g.add(ellipsoid(H(0, 0.2, 0.25), r(2.4, 2.6, 2.45)))
    g.add(rbox(H(0, -1.2, -1.2), r(1.9, 1.35, 1.0), I3, 0.55 * HS), 0.45)                       # jaw block
    g.add(torus(H(0, 0.2, -1.55), (0, 0, 1), 2.0 * HS, 0.42 * HS), 0.35)                        # armoured collar
    g.add(rbox(H(0, -2.0, 0.85), r(2.0, 0.55, 0.38), I3, 0.25), 0.3)                            # brow
    g.cut(rbox(H(0, -2.75, 0.25), r(1.5, 0.6, 0.2), I3, 0.08))                                  # visor slit
    for s in (-1, 1):
        for j in range(2):
            g.cut(rbox(H(s * (0.6 + 0.45 * j), -2.55, -1.15), (0.14, 0.5, 0.42), I3, 0.06))     # grille slots
    return _finish_helm(g)


def specter(h=0.06):
    """VH-10 Specter: scout helm under a cloth hood, one large monocular lens, filter snout."""
    g, H, r = _shell(top=4.0, h=h)
    g.add(ellipsoid(H(0, 0.2, 0.3), r(2.15, 2.45, 2.5)))
    g.add(ellipsoid(H(0, 0.75, 0.55), r(2.65, 2.75, 2.95)), 0.6)                                # hood
    g.cut(ellipsoid(H(0, -2.0, 0.1), r(1.9, 1.6, 2.1)), 0.3)                                    # hood opening
    g.add(ellipsoid(H(0, -0.6, 0.1), r(1.85, 1.9, 2.05)), 0.3)                                  # face under the hood
    g.add(cyl(H(0.0, -1.9, 0.35), H(0.0, -2.75, 0.35), 0.8 * HS, 0.15), 0.12)                    # monocular
    g.cut(cyl(H(0.0, -2.9, 0.35), H(0.0, -2.45, 0.35), 0.5 * HS))
    g.add(round_cone(H(0, -1.6, -0.9), H(0, -2.5, -1.4), 0.75 * HS, 0.55 * HS), 0.25)            # filter snout
    g.add(torus(H(0, 0.8, -1.4), (0, 0, 1), 1.9 * HS, 0.45 * HS), 0.4)                          # hood folds at the collar
    return _finish_helm(g)


HELMS = {
    "VH-01": ("Vigil", "line standard: chevron split visor, keel crest, ear-pod fins", lambda h: X.helm("vigil", h)),
    "VH-02": ("Warden", "command: crest blade and whip antenna", lambda h: X.helm("warden", h)),
    "VH-03": ("Breacher", "armoured faceplate with a slit lens", lambda h: X.helm("breacher", h)),
    "VH-04": ("Seeker", "monocular sensor on the right", lambda h: X.helm("seeker", h)),
    "VH-05": ("Sentinel", "T-visor, brow ridge, ribbed jaw", sentinel),
    "VH-06": ("Raptor", "beaked muzzle, slanted eye slits, swept fin crest", raptor),
    "VH-07": ("Diver", "round dome, circular faceplate lens, bolts, breather cans", diver),
    "VH-08": ("Hunter", "three lens slits, mandible jaw guards, rear spine", hunter),
    "VH-09": ("Bulwark", "assault: heavy jaw, armoured collar, single visor slit", bulwark),
    "VH-10": ("Specter", "scout: cloth hood, monocular lens, filter snout", specter),
}


def helm(ident, h=0.06):
    return HELMS[ident][2](h)


# ------------------------------------------------------------------------------------------------ weapons
def talon_carbine():
    """VW-05 'Talon' carbine: compact, folded stock, side magazine, short barrel (1.3 mm)."""
    s = rbox(v3(0.8, 0, 1.0), (2.4, 0.85, 1.05), I3, 0.35)
    s = s | cyl(v3(3.0, 0, 1.2), v3(5.6, 0, 1.2), 0.65, 0.12) | cyl(v3(5.1, 0, 1.2), v3(6.0, 0, 1.2), 0.85, 0.2)
    s = s | rbox(v3(-2.2, 0, 1.3), (0.6, 0.55, 0.9), I3, 0.25)                               # folded stock
    s = s | rbox(v3(1.2, -1.15, 1.0), (0.5, 0.45, 1.1), rot((1, 0, 0), 15), 0.2)            # side magazine
    s = s | rbox(v3(0, 0, -0.45), (0.5, 0.52, 0.95), rot(RY, -14), 0.22)                     # grip
    s = s | rbox(v3(1.0, 0, 2.3), (0.9, 0.42, 0.4), I3, 0.15)                                # red-dot
    return s


def brand_flamer():
    """VW-06 'Brand' flamer: fuel drum under the body, nozzle shroud, pilot light, rear grip origin."""
    s = rbox(v3(2.0, 0, 1.3), (3.0, 0.95, 0.95), I3, 0.4)
    s = s | cyl(v3(0.6, 0, -0.5), v3(4.2, 0, -0.5), 1.0, 0.3)                                 # fuel drum
    s = s | cyl(v3(5.0, 0, 1.3), v3(7.8, 0, 1.3), 0.75, 0.15) | cyl(v3(7.4, 0, 1.3), v3(8.6, 0, 1.3), 1.05, 0.25)  # nozzle + shroud
    s = s | cyl(v3(6.0, 0, 2.2), v3(7.6, 0, 2.2), 0.4, 0.1)                                   # pilot line (0.8 mm)
    s = s | rbox(v3(0, 0, 0.0), (0.5, 0.5, 0.95), rot(RY, -10), 0.2)                          # rear grip
    s = s | rbox(v3(3.6, 0, 2.5), (1.4, 0.35, 0.35), I3, 0.15)                                # handle rail
    return s


def halberd_shotgun():
    """VW-07 'Halberd' breaching shotgun: thick barrel over a tube magazine, pump grip, heavy stock."""
    s = rbox(v3(0.4, 0, 1.1), (2.8, 0.85, 1.05), I3, 0.35)
    s = s | cyl(v3(2.8, 0, 1.55), v3(9.0, 0, 1.55), 0.8, 0.15)                                # barrel (1.6 mm)
    s = s | cyl(v3(2.8, 0, 0.55), v3(7.6, 0, 0.55), 0.65, 0.15)                               # tube magazine
    s = s | rbox(v3(5.4, 0, 0.6), (1.3, 0.85, 0.75), I3, 0.3)                                 # pump
    s = s | rbox(v3(-3.6, 0, 0.9), (1.2, 0.75, 1.2), rot(RY, 8), 0.35)                        # stock
    s = s | rbox(v3(0, 0, -0.45), (0.5, 0.52, 0.95), rot(RY, -14), 0.22)                      # grip
    return s


def edge_blade():
    """VW-08 'Edge' combat blade: 1.0 mm blade (rounded spine and edge, no knife edge), guard, grip; origin = grip."""
    s = rbox(v3(0, 0, 0), (0.55, 0.5, 1.2), I3, 0.25)                                         # grip along z
    s = s | rbox(v3(0, 0, 1.35), (1.2, 0.55, 0.25), I3, 0.12)                                 # guard
    s = s | rbox(v3(0, 0, 4.2), (0.75, 0.5, 2.7), I3, 0.3).clip(
        Shape(lambda Q: (Q[:, 2] - 6.9) + 0.8 * Q[:, 0], (-9, -9, -9), (9, 9, 9)))            # blade, clipped point
    return s


WEAPONS = {
    "VW-01": ("Lance rifle", "bullpup battle rifle", X.lance_rifle),
    "VW-02": ("Needle rifle", "marksman rifle, long barrel, big scope", X.needle_rifle),
    "VW-03": ("Maul arc-cannon", "heavy support weapon, three emitter rails", X.maul_cannon),
    "VW-04": ("Spur sidearm", "pistol", X.sidearm),
    "VW-05": ("Talon carbine", "compact carbine, side magazine", talon_carbine),
    "VW-06": ("Brand flamer", "fuel drum, nozzle shroud", brand_flamer),
    "VW-07": ("Halberd shotgun", "breaching shotgun, tube magazine, pump", halberd_shotgun),
    "VW-08": ("Edge blade", "combat knife", edge_blade),
}


def weapon(ident):
    return WEAPONS[ident][2]()


# ------------------------------------------------------------------------------------------------ armour bits
def shoulder_cap(kind="standard"):
    """Layered shoulder cap as a loose part (flat underside to glue over the figure's cap)."""
    s = ellipsoid(v3(0, 0, 0.6), (2.4, 2.1, 1.5))
    s = s | ellipsoid(v3(0, 0.6, 0.2), (2.6, 2.2, 1.1))
    if kind == "riot":
        s = s | rbox(v3(0, -1.6, 0.4), (2.5, 0.5, 1.1), I3, 0.3)                              # raised riot lip
    elif kind == "command":
        s = s | rbox(v3(0, 0, 1.95), (1.0, 0.75, 0.35), I3, 0.15)                             # rank plate
    elif kind == "heavy":
        s = s | ellipsoid(v3(0, 0.2, 1.4), (1.9, 1.7, 0.9)) | ellipsoid(v3(0, 1.2, -0.1), (2.8, 1.4, 0.9))
    return s.clip(Shape(lambda Q: -Q[:, 2], (-9, -9, -9), (9, 9, 9)))


def knee_guard():
    s = ellipsoid(v3(0, 0, 0.8), (1.5, 1.2, 1.8)) | rbox(v3(0, -0.6, 0.8), (1.0, 0.5, 0.9), I3, 0.3)
    return s.clip(Shape(lambda Q: Q[:, 1] - 0.3, (-9, -9, -9), (9, 9, 9)))


ARMOUR = {
    "VA-01": ("Shoulder cap, standard", "line-standard layered cap", lambda: shoulder_cap("standard")),
    "VA-02": ("Shoulder cap, riot", "raised riot lip", lambda: shoulder_cap("riot")),
    "VA-03": ("Shoulder cap, command", "rank plate", lambda: shoulder_cap("command")),
    "VA-04": ("Shoulder cap, heavy", "triple layered", lambda: shoulder_cap("heavy")),
    "VA-05": ("Knee guard", "bolt-on knee plate", knee_guard),
}


def armour(ident):
    return ARMOUR[ident][2]()


def sculpt_shape(shape, name, h=0.06, tris=120_000):
    """Mesh a loose Shape (weapon or armour bit) on its own grid, flat on z = 0 for printing."""
    g = Sculpt(shape.lo - 0.4, shape.hi + 0.4, h)
    g.add(shape)
    return g.mesh(name, tris)


def catalogue():
    return {"helms": {k: v[:2] for k, v in HELMS.items()}, "weapons": {k: v[:2] for k, v in WEAPONS.items()},
            "armour": {k: v[:2] for k, v in ARMOUR.items()}}
