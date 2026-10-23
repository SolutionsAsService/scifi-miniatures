"""Vigil aerial wing: SDF sculpts for every print part (VA-1 Belfry, VA-2 Angelus + rotors, VA-3 Knell + launcher,
loadout bits, flight stem, bases).

Frame (as tools/sdfkit.py): millimetres at 1:56 print scale, z up, every airframe faces -y (its left side on +x).
Key dimensions come from spec/vigil-aerial-drones.spec.json (in-world sizing in reports/sizing.json); small detail
offsets (panel lines, lens bars, louvres) are written next to the feature they shape, with the limit they respect.

Detail rules (MSLA resin, unified-CAD-MCP msla_resin preset + brief): walls >= 0.6 mm, rotor / prop blades >= 0.8 mm
thick, engraved lines 0.44-0.45 mm wide x 0.25-0.35 mm deep, raised detail >= 0.15 mm, air gaps between facing
surfaces >= 0.5 mm, no knife edges (blunt trailing edges >= 0.7 mm), no sealed cavities, sockets with >= 0.6 mm walls.
Vigil language: split-chevron sensor lenses on every sensor face, a keel crest / spine along each airframe's top,
chevron plan forms (Belfry hull, Angelus tail plane, Knell planform).
"""
from __future__ import annotations

import math

import numpy as np

from sdfkit import Shape, capsule, cyl, d_peg, ellipsoid, half, rbox, rot, round_cone, sphere, tube, unit, v3
from aerial_kit import (Ops, along, base_body, chain, deck_seams, launch_pad, magnet_pocket, mat, plate, poly_sdf,
                        prop, scaled, split_chevron_cuts, stem_dir)

I3 = np.eye(3)
Z = v3(0, 0, 1)
RX, RY, RZ = (1, 0, 0), (0, 1, 0), (0, 0, 1)
FWD = v3(0, -1, 0)


def peg_up(o, at, d, length, key=(0, -1, 0)):
    """D-flat peg from 'at' upward (loadout bits plug up into a belly hardpoint)."""
    o.add(d_peg(v3(at) - v3(0, 0, 0.3), (0, 0, 1), d, length + 0.3, key=key))


def peg_down(o, at, d, length, key=(0, -1, 0)):
    o.add(d_peg(v3(at) + v3(0, 0, 0.3), (0, 0, -1), d, length + 0.3, key=key))


def socket_down(o, top, d, depth, key=(0, -1, 0)):
    """D-flat socket opening upward at 'top' (0.1 mm glue clearance per side)."""
    o.cut(d_peg(v3(top) + v3(0, 0, 0.01), (0, 0, -1), d, depth, key=key, grow=0.1))


def socket_up(o, bottom, d, depth, key=(0, -1, 0)):
    """D-flat socket opening downward at 'bottom'."""
    o.cut(d_peg(v3(bottom) - v3(0, 0, 0.01), (0, 0, 1), d, depth, key=key, grow=0.1))


def round_socket_up(o, bottom, d, depth):
    """Round glue-fit stem bore opening downward (printed 1.6 stem or clear rod in a 1.8 bore)."""
    b = v3(bottom)
    o.cut(cyl(b - v3(0, 0, 0.5), b + v3(0, 0, depth), d / 2))


# ================================================================================================ VA-1 Belfry
def belfry(S):
    """Heavy-lift coaxial hexacopter: chevron-hex hull, six arms with coaxial motor pairs (12 two-blade props), chin
    gimbal turret, keel crest, mast socket (1.2 D-flat), belly payload hardpoint (1.6 D-flat) on the CG, flight /
    tether stem socket (1.8 round) aft of it, tubular landing skids with flat feet."""
    B = S["belfry"]
    o = Ops()
    # hull: rounded box cut to a chevron at the nose and the tail (elongated hexagon in plan)
    # apex (0, -7.6), shoulders (+-4.3, -3.0); tail apex (0, 7.0), shoulders (+-4.3, 3.4): an elongated chevron-hex
    nose = [half((0, -7.6, 0), (s * 4.6, -4.3, 0)) for s in (-1, 1)]
    tail = [half((0, 7.0, 0), (s * 3.6, 4.3, 0)) for s in (-1, 1)]
    o.add(rbox(v3(0, -0.3, 0.4), (4.3, 7.3, 1.9), I3, 0.9).clip(*nose, *tail))
    o.add(ellipsoid(v3(0, 0.2, -0.9), (3.4, 5.4, 1.5)), 0.5)                          # belly (blast-chevron keel)
    nose2 = [half((0, -6.7, 0), (s * 4.2, -3.1, 0)) for s in (-1, 1)]
    tail2 = [half((0, 6.1, 0), (s * 3.2, 3.1, 0)) for s in (-1, 1)]
    o.add(rbox(v3(0, -0.3, 2.15), (3.1, 6.4, 0.55), I3, 0.35).clip(*nose2, *tail2), 0.2)   # top deck, 0.55 step
    # deck panel lines 0.45 x 0.35, stopped 0.6 short of the keel crest and the deck edge
    for y in (-2.6, 1.3):
        for s in (-1, 1):
            o.cut(rbox(v3(s * 1.75, y, 2.7), (0.95, 0.225, 0.35), I3, 0.05))
    # side battery hatches: 0.45 x 0.3 engraved frames on each flank
    for s in (-1, 1):
        for (yy, zz) in ((-1.0, 0.5),):
            fr = rbox(v3(s * 4.3, yy, zz), (0.3, 2.0, 0.85), I3, 0.0)
            inner = rbox(v3(s * 4.3, yy, zz), (0.5, 1.55, 0.4), I3, 0.0)
            o.cut(Shape(lambda P, fr=fr, inner=inner: np.maximum(fr(P), -inner(P)), fr.lo, fr.hi))
    o.add(capsule(v3(0, -6.0, 2.0), v3(0, 3.0, 2.9), 0.45), 0.2)                      # keel crest 0.9 wide
    # arms + coaxial motor pairs + props
    R, pr = B["motor_r"], B["prop_r"]
    bl = B["blade"]
    for k, phi in enumerate(B["arm_phi_deg"]):
        a = math.radians(phi)
        d = v3(math.sin(a), -math.cos(a), 0)
        c = d * R
        o.add(along(d * 3.0 + v3(0, 0, 0.3), c - d * 0.7 + v3(0, 0, 0.6), 0.75, 0.6, 0.25), 0.3)     # arm 1.5 x 1.2
        o.add(capsule(d * 4.3 + v3(0, 0, 0.95), c - d * 1.5 + v3(0, 0, 1.15), 0.28), 0.12)          # arm ridge
        o.add(cyl(c + v3(0, 0, -1.75), c + v3(0, 0, 1.85), 1.1, 0.3), 0.2)                         # motor stack
        o.add(cyl(c + v3(0, 0, -0.1), c + v3(0, 0, 0.5), 1.28, 0.1), 0.05)                         # collar
        zu, zl = B["upper_prop_z"], B["lower_prop_z"]
        o.add(cyl(c + v3(0, 0, 1.6), c + v3(0, 0, zu + 0.45), 0.72, 0.22), 0.1)                     # upper hub
        o.add(cyl(c + v3(0, 0, zl - 0.45), c + v3(0, 0, -1.5), 0.72, 0.22), 0.1)                    # lower hub
        # phases are relative to the arm direction: upper blades across the arm, lower blades 60 deg on
        prop(o, c + v3(0, 0, zu), Z, pr, 2, bl["chord0"], bl["chord1"], bl["thick"], 90, bl["pitch_deg"], ref=d)
        prop(o, c + v3(0, 0, zl), Z, pr, 2, bl["chord0"], bl["chord1"], bl["thick"], 150, -bl["pitch_deg"], ref=d)
    # chin gimbal turret: neck, yoke, ball with the split-chevron lens pair and a laser window
    o.add(cyl(v3(0, -4.9, -1.2), v3(0, -4.9, -2.3), 0.85, 0.2), 0.25)
    o.add(rbox(v3(0, -4.95, -2.35), (1.9, 0.75, 0.42), I3, 0.2), 0.15)
    o.add(sphere(v3(0, -5.0, -3.25), 1.6), 0.2)
    split_chevron_cuts(o, v3(0, -6.55, -3.1), FWD, spread=0.5)
    o.cut(cyl(v3(0, -6.7, -3.95), v3(0, -5.95, -3.95), 0.3))                          # laser window 0.6, 0.4 deep
    # mast socket (1.2 D-flat) on a boss at the keel tail
    ms = B["mast_socket"]
    mx, my = ms["xy"]
    o.add(cyl(v3(mx, my, 2.0), v3(mx, my, ms["top_z"]), ms["boss_r"], 0.3), 0.3)
    # belly hardpoint (1.6 D-flat) + stem socket (1.8 round) bosses
    hp, st = B["hardpoint"], B["stem_socket"]
    o.add(cyl(v3(*hp["xy"], -1.6), v3(*hp["xy"], hp["boss_bottom_z"]), hp["boss_r"], 0.3), 0.3)
    for s in (-1, 1):                                                                 # sway-brace lugs either side
        o.add(rbox(v3(s * 2.2, hp["xy"][1], -2.2), (0.45, 1.2, 0.55), I3, 0.15), 0.15)
    o.add(cyl(v3(*st["xy"], -1.4), v3(*st["xy"], st["boss_bottom_z"]), st["boss_r"], 0.3), 0.3)
    # skids: struts from the belly sides to two tubular skids with upturned toes; flat feet at skid_z
    zs, xs = B["skid_z"], B["skid_x"]
    for s in (-1, 1):
        for sy in (-1, 1):
            o.add(capsule(v3(s * 2.5, sy * 3.3, -1.5), v3(s * xs, sy * 3.9, zs + 0.6), 0.5), 0.2)  # strut 1.0
        o.add(capsule(v3(s * xs, -5.8, zs + 0.55), v3(s * xs, 6.2, zs + 0.55), 0.55), 0.15)        # skid 1.1
        o.add(capsule(v3(s * xs, -5.8, zs + 0.55), v3(s * xs, -7.2, zs + 1.5), 0.55), 0.15)        # toe
    o.cut(Shape(lambda P: P[:, 2] - zs, (-20, -20, zs - 2), (20, 20, zs)))           # flat feet
    # sockets last, so no later add can fill them
    socket_down(o, (mx, my, ms["top_z"]), ms["peg_d"], ms["sock_depth"])
    socket_up(o, (*hp["xy"], hp["boss_bottom_z"]), hp["peg_d"], hp["sock_depth"])
    round_socket_up(o, (*st["xy"], st["boss_bottom_z"]), st["d"], st["depth"])
    return o


# ================================================================================================ loadout bits
def bit_eo_turret(S):
    """VL-01 long-range EO/IR turret for the Belfry hardpoint (hangs below z = 0, 1.6 D-flat peg up)."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, -0.6), 1.7, 0.2))
    for s in (-1, 1):
        o.add(rbox(v3(s * 1.55, 0, -1.3), (0.4, 0.8, 0.9), I3, 0.2), 0.15)             # yoke arms 0.8
    o.add(sphere(v3(0, 0, -1.95), 1.45), 0.15)
    split_chevron_cuts(o, v3(0, -1.38, -1.8), FWD, spread=0.48)
    o.cut(cyl(v3(0, -1.6, -2.6), v3(0, -1.0, -2.6), 0.28))
    peg_up(o, (0, 0, 0), S["loadout"]["hardpoint_peg_d"], S["loadout"]["peg_len"])
    return o


def bit_sar_pod(S):
    """VL-02 SAR / ground-moving-target radar pod: pylon and a capsule pod with flat side arrays."""
    o = Ops()
    # pod kept between the chin turret (ahead) and the flying stem (aft): y -2.95..3.05, hung low (bottom z -3.55)
    o.add(rbox(v3(0, 0.0, -0.65), (0.55, 1.4, 0.65), I3, 0.2))                       # pylon, top exactly at z = 0
    o.add(capsule(v3(0, -1.9, -2.4), v3(0, 1.9, -2.4), 1.15), 0.3)
    for s in (-1, 1):
        o.add(rbox(v3(s * 1.0, 0.0, -2.4), (0.3, 1.8, 0.75), I3, 0.12), 0.08)           # array faces, 0.15+ proud
        for y in (-1.2, 0.0, 1.2):
            o.cut(rbox(v3(s * 1.32, y, -2.4), (0.2, 0.22, 0.55), I3, 0.0))             # array seams 0.44 x 0.2
    o.add(round_cone(v3(0, -1.9, -2.4), v3(0, -2.5, -2.4), 0.85, 0.45), 0.2)           # radome nose
    peg_up(o, (0, 0, 0), S["loadout"]["hardpoint_peg_d"], S["loadout"]["peg_len"])
    return o


def glide_munition(o, c):
    """Small glide munition along y (nose -y): body 1.5 dia, ogive nose, cruciform 0.8 mm tail fins."""
    c = v3(c)
    o.add(capsule(c + v3(0, -1.8, 0), c + v3(0, 2.0, 0), 0.75), 0.1)
    o.add(round_cone(c + v3(0, -1.8, 0), c + v3(0, -3.0, 0), 0.75, 0.3), 0.15)
    for ang in (45, 135, 225, 315):
        e = rot(RY, ang) @ v3(1, 0, 0)
        o.add(plate(c, e, (0, 1, 0), [(0.4, 0.6), (1.55, 1.3), (1.55, 2.3), (0.4, 2.3)], 0.8, 0.2), 0.1)
    o.add(cyl(c + v3(0, -0.95, 0), c + v3(0, -0.7, 0), 0.9, 0.08), 0.03)                # band 0.15 proud


def bit_twin_munitions(S):
    """VL-03 twin glide munitions on a cross-bar rack."""
    o = Ops()
    o.add(rbox(v3(0, -0.4, -0.5), (0.6, 1.2, 0.5), I3, 0.2))
    o.add(rbox(v3(0, -0.4, -0.95), (2.7, 0.75, 0.4), I3, 0.2), 0.2)
    for s in (-1, 1):
        o.add(rbox(v3(s * 2.0, -0.4, -1.3), (0.4, 0.5, 0.4), I3, 0.15), 0.15)            # suspension lugs
        glide_munition(o, (s * 2.0, -0.4, -2.05))
    peg_up(o, (0, 0, 0), S["loadout"]["hardpoint_peg_d"], S["loadout"]["peg_len"])
    return o


def bit_cargo_pod(S):
    """VL-04 cargo / medevac-supply pod: sling bar, chevron-ribbed container (the heavy-lift job)."""
    o = Ops()
    o.add(rbox(v3(0, 0.0, -0.55), (0.6, 1.3, 0.55), I3, 0.2))
    o.add(rbox(v3(0, 0.0, -0.95), (1.6, 0.6, 0.3), I3, 0.15), 0.15)                     # sling bar
    for s in (-1, 1):
        o.add(capsule(v3(s * 1.3, 0.0, -1.0), v3(s * 2.0, 0.0, -1.9), 0.4), 0.1)         # sling legs 0.8
    # container bottom at z -3.6 (with ribs): on the hardpoint (boss bottom z -2.75) it stays 0.65 above the skid plane;
    # y +-2.7 keeps it clear of the chin turret ahead and the flying stem aft
    o.add(rbox(v3(0, 0.0, -2.6), (2.6, 2.7, 0.85), I3, 0.35), 0.15)
    for y in (-1.8, 0.0, 1.8):
        o.add(rbox(v3(0, y, -2.6), (2.75, 0.3, 1.0), I3, 0.15), 0.05)                   # ribs 0.15 proud
    ng = v3(0, -1, 0)
    split_chevron_cuts(o, v3(0, -2.7, -2.6), ng, spread=0.75, bar=(0.75, 0.3, 0.2))     # marking on the front
    peg_up(o, (0, 0, 0), S["loadout"]["hardpoint_peg_d"], S["loadout"]["peg_len"])
    return o


def bit_eo_mast(S):
    """VL-10 EO / radar ball mast (Belfry top socket, 1.2 D-flat peg down from z = 0)."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.6), 1.25, 0.2))
    o.add(cyl(v3(0, 0, 0.3), v3(0, 0, 5.8), 0.7, 0.15), 0.15)                          # mast 1.4
    o.add(cyl(v3(0, 0, 3.0), v3(0, 0, 3.4), 0.9, 0.1), 0.05)                           # clamp band
    o.add(cyl(v3(0, 0, 5.4), v3(0, 0, 5.9), 1.1, 0.15), 0.1)                           # yoke base
    o.add(sphere(v3(0, 0, 7.15), 1.6), 0.2)
    o.add(cyl(v3(0, 0, 8.45), v3(0, 0, 8.95), 1.15, 0.2), 0.2)                         # rain cap
    split_chevron_cuts(o, v3(0, -1.52, 7.25), FWD, spread=0.48)
    peg_down(o, (0, 0, 0), S["loadout"]["mast_peg_d"], S["loadout"]["peg_len"])
    return o


def bit_relay_mast(S):
    """VL-11 relay antenna mast: two dipole bars and a whip."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.6), 1.25, 0.2))
    o.add(cyl(v3(0, 0, 0.3), v3(0, 0, 5.6), 0.6, 0.12), 0.15)                          # mast 1.2
    for z, ang in ((3.4, 0.0), (5.0, 90.0)):
        o.add(rbox(v3(0, 0, z), (1.75, 0.45, 0.45), rot(RZ, ang), 0.15), 0.1)          # dipole bars 0.9
        o.add(cyl(v3(0, 0, z - 0.6), v3(0, 0, z + 0.6), 0.8, 0.12), 0.1)
    o.add(cyl(v3(0, 0, 5.5), v3(0, 0, 8.4), 0.5, 0.1), 0.1)                            # whip 1.0
    o.add(sphere(v3(0, 0, 8.45), 0.65), 0.1)
    peg_down(o, (0, 0, 0), S["loadout"]["mast_peg_d"], S["loadout"]["peg_len"])
    return o


def bit_radar_mast(S):
    """VL-12 rotating surveillance radar: turntable and a flat array tilted back 15 deg."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 0.6), 1.25, 0.2))
    o.add(cyl(v3(0, 0, 0.3), v3(0, 0, 4.6), 0.7, 0.15), 0.15)
    o.add(cyl(v3(0, 0, 4.3), v3(0, 0, 4.9), 1.3, 0.15), 0.1)
    R = rot(RX, -15)
    o.add(rbox(v3(0, 0.15, 6.2), (3.6, 0.45, 1.3), R, 0.2), 0.2)                       # array 7.2 x 0.9 x 2.6
    nrm = R @ v3(0, -1, 0)
    for x in (-2.4, -1.2, 0.0, 1.2, 2.4):                                              # element seams 0.44 x 0.25
        o.cut(rbox(v3(x, 0.15, 6.2) + nrm * 0.45, (0.22, 0.25, 1.05), R, 0.0))
    peg_down(o, (0, 0, 0), S["loadout"]["mast_peg_d"], S["loadout"]["peg_len"])
    return o


# ================================================================================================ VA-2 Angelus
def angelus_pod(S):
    """Teardrop pod: round cones in a space squeezed 0.86 in x (7.65 wide x 8.9 tall at the widest station)."""
    sx = S["angelus"]["pod_x_scale"]
    c = chain([(v3(0, -8.0, 9.4), 3.6), (v3(0, -3.2, 9.9), 4.45), (v3(0, 3.0, 10.6), 3.0), (v3(0, 8.6, 11.6), 1.25)],
              smooth=1.2)
    return scaled(c, sx, 1.0, 1.0)


def angelus(S):
    """Unmanned observation helicopter airframe (rotors are separate parts): teardrop pod, keel crest into a mast
    fairing, exposed mast + swashplate + head block with the rotor pin, chin sensor ball, tubular skids, slender boom,
    swept fin with the tail-rotor pin, ventral fin, chevron tail plane, flight-stem socket on the CG."""
    A = S["angelus"]
    o = Ops()
    pod = angelus_pod(S)
    o.add(pod)
    # engraved panel rings round the pod and a hatch frame on the left flank (cut before later adds)
    for y0 in (-5.4, 3.6):
        lo, hi = pod.lo.copy(), pod.hi.copy()
        lo[1], hi[1] = y0 - 0.4, y0 + 0.4
        o.cut(Shape(lambda P, y0=y0: np.maximum(np.abs(P[:, 1] - y0) - 0.22, -(pod(P) + 0.32)), lo, hi))
    fr_o = lambda P: np.maximum(np.abs(P[:, 1] + 1.4) - 2.0, np.abs(P[:, 2] - 9.7) - 1.5)   # noqa: E731
    fr_i = lambda P: np.maximum(np.abs(P[:, 1] + 1.4) - 1.56, np.abs(P[:, 2] - 9.7) - 1.06)  # noqa: E731
    o.cut(Shape(lambda P: np.maximum.reduce([fr_o(P), -fr_i(P), 0.5 - P[:, 0], -(pod(P) + 0.3)]),
                (0.5, -3.6, 8.0), (4.2, 0.8, 11.4)))
    # mast fairing hump + keel crest + split-chevron intakes on the hump front
    o.add(ellipsoid(v3(0, -1.2, 14.2), (1.95, 3.7, 1.15)), 0.5)
    o.add(capsule(v3(0, -8.9, 12.7), v3(0, -4.6, 14.45), 0.45), 0.25)
    split_chevron_cuts(o, v3(0, -4.55, 14.55), unit((0, -1, 0.35)), spread=0.62, bar=(0.6, 0.4, 0.22), cant=30)
    # exhaust stub on the right (-x) flank, bore 0.6 x 0.4
    o.add(capsule(v3(-2.6, 1.0, 11.6), v3(-3.75, 2.3, 11.1), 0.6), 0.25)
    dex = unit(v3(-3.75, 2.3, 11.1) - v3(-2.6, 1.0, 11.6))
    o.cut(cyl(v3(-3.75, 2.3, 11.1) - dex * 0.4, v3(-3.75, 2.3, 11.1) + dex * 0.8, 0.3))
    # exposed mast, swashplate, head block, rotor pin (1.4) for the separate main rotor
    mx, my = A["mast_xy"]
    o.add(cyl(v3(mx, my, 14.6), v3(mx, my, 16.7), 0.65, 0.1), 0.15)
    o.add(cyl(v3(mx, my, 15.3), v3(mx, my, 15.8), 1.45, 0.15), 0.1)
    o.add(rbox(v3(mx, my, A["head_top_z"] - 0.45), (1.3, 0.7, 0.45), I3, 0.2), 0.1)
    o.add(cyl(v3(mx, my, A["head_top_z"] - 0.2), v3(mx, my, A["pin_top_z"]), A["pin_d"] / 2, 0.3), 0.05)
    # chin sensor ball with the split-chevron lens pair
    o.add(cyl(v3(0, -7.3, 7.3), v3(0, -7.3, 6.4), 0.9, 0.2), 0.3)
    o.add(sphere(v3(0, -7.4, 6.1), 1.55), 0.25)
    split_chevron_cuts(o, v3(0, -8.88, 6.05), FWD, spread=0.5)
    # boom, fins, tail plane, tail-rotor gearbox + pin (1.0)
    o.add(round_cone(v3(0, 7.5, 11.75), v3(0, 24.9, 12.6), 1.05, 0.72), 0.6)
    o.add(capsule(v3(0, 9.6, 12.65), v3(0, 21.5, 13.25), 0.3), 0.12)                 # boom spine (keel line)
    o.add(plate((0, 0, 0), (0, 1, 0), (0, 0, 1), [(21.4, 12.3), (25.1, 12.3), (26.7, 17.3), (25.2, 17.3)], 0.9, 0.3), 0.25)
    o.add(plate((0, 0, 0), (0, 1, 0), (0, 0, 1), [(22.6, 12.5), (25.1, 12.5), (25.6, 9.7), (24.7, 9.7)], 0.9, 0.3), 0.25)
    an = math.radians(10)
    for s in (-1, 1):
        u = v3(s * math.cos(an), 0, -math.sin(an))
        o.add(plate((0, 0, 12.35), u, (0, 1, 0), [(0.3, 16.8), (4.0, 18.6), (4.0, 19.9), (0.3, 19.0)], 0.8, 0.3), 0.25)
    tr = A["tail_rotor"]
    tc = v3(tr["c"])
    o.add(cyl(tc + v3(0.2, 0, 0), tc + v3(tr["inner_x"], 0, 0), 0.85, 0.2), 0.15)       # gearbox / spacer
    o.add(cyl(tc + v3(tr["inner_x"] - 0.2, 0, 0), tc + v3(tr["inner_x"] + tr["hub_t"] + 0.2, 0, 0), tr["pin_d"] / 2, 0.25), 0.05)
    # skids: two tubes (1.0) with toes, two bent cross tubes each side into the pod
    xs = A["skid_x"]
    for s in (-1, 1):
        o.add(capsule(v3(s * xs, -7.4, 0.5), v3(s * xs, 5.2, 0.5), 0.5), 0.1)
        o.add(capsule(v3(s * xs, -7.4, 0.5), v3(s * xs, -8.9, 1.45), 0.5), 0.1)
        for y, zt in ((-4.0, 6.4), (2.2, 7.7)):
            o.add(tube([v3(s * xs, y, 0.5), v3(s * (xs - 0.25), y, 3.4), v3(s * 2.2, y, zt)], 0.5), 0.15)
    o.cut(Shape(lambda P: P[:, 2], (-10, -12, -2), (10, 8, 0)))                       # flat skid feet at z = 0
    # flight-stem socket boss on the CG (round 1.8 bore)
    st = A["stem_socket"]
    o.add(cyl(v3(*st["xy"], 6.4), v3(*st["xy"], st["boss_bottom_z"]), st["boss_r"], 0.3), 0.3)
    round_socket_up(o, (*st["xy"], st["boss_bottom_z"]), st["d"], st["depth"])
    return o


def main_rotor(S):
    """Two-blade main rotor, printed flat on the plate (underside z = 0): hub with a 1.6 through-bore for the 1.4
    rotor pin (no cup), blade grips, 1.8 x 0.9 mm blades with swept tips, split-chevron mark on the hub."""
    A = S["angelus"]
    rr = A["rotor"]
    R = A["rotor_r"]
    o = Ops()
    t = rr["thick"]
    o.add(cyl(v3(0, 0, 0), v3(0, 0, rr["hub_t"]), rr["hub_r"], 0.3))
    for s in (-1, 1):
        o.add(rbox(v3(s * 2.7, 0, 0.55), (1.15, 0.85, 0.55), I3, 0.3), 0.2)              # grips
        c = rr["chord"] / 2
        poly = [(rr["root_r"], -c), (R - 1.6, -c), (R, -c + 1.0), (R, c), (rr["root_r"], c)]
        o.add(plate((0, 0, t / 2), (s, 0, 0), (0, s, 0), poly, t, 0.3), 0.15)
    o.add(rbox(v3(0, 0, rr["hub_t"]), (0.7, 0.7, 0.2), rot(RZ, 45), 0.1), 0.05)
    o.cut(cyl(v3(0, 0, -1), v3(0, 0, 3), rr["hole_d"] / 2))
    for s in (-1, 1):                                                                  # split-chevron hub mark
        o.cut(rbox(v3(s * 1.2, -1.1, rr["hub_t"]), (0.45, 0.22, 0.2), rot(RZ, s * 35), 0.03))
    return o


def tail_rotor(S):
    """Two-blade tail rotor, printed flat (underside z = 0): hub with a 1.2 through-bore for the 1.0 pin."""
    tr = S["angelus"]["tail_rotor"]
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, tr["hub_t"]), tr["hub_r"], 0.25))
    t = tr["thick"]
    for s in (-1, 1):
        c = tr["chord"] / 2
        poly = [(0.7, -c), (tr["r"] - 0.5, -c), (tr["r"], -c + 0.35), (tr["r"], c), (0.7, c)]
        o.add(plate((0, 0, t / 2), (s, 0, 0), (0, s, 0), poly, t, 0.3), 0.12)
    o.cut(cyl(v3(0, 0, -1), v3(0, 0, 2), tr["hole_d"] / 2))
    return o


# ================================================================================================ VA-3 Knell
class KnellWing:
    """Cropped-delta wing as an approximate SDF: exact planform polygon distance, thickness from a blunt airfoil-like
    chordwise shape (max at 30 % chord) tapering root -> tip, trailing edge never thinner than 2 x te_half_min."""

    def __init__(self, K):
        self.K = K
        hs = K["half_span"]
        self.poly = [(-hs, K["tip_le_y"]), (0, K["root_le_y"]), (hs, K["tip_le_y"]), (hs, K["tip_te_y"]),
                     (0, K["root_te_y"]), (-hs, K["tip_te_y"])]

    def half_t(self, x, y):
        K = self.K
        hs = K["half_span"]
        s = np.clip(np.abs(x), 0, hs)
        yle = K["root_le_y"] + s * (K["tip_le_y"] - K["root_le_y"]) / hs
        yte = K["root_te_y"] + s * (K["tip_te_y"] - K["root_te_y"]) / hs
        u = np.clip((y - yle) / np.maximum(yte - yle, 1e-6), 0, 1)
        t = K["t_root"] + (K["t_tip"] - K["t_root"]) * s / hs
        f = np.where(u < 0.3, 0.55 + 0.45 * np.sin(np.pi / 2 * u / 0.3), 1.0 - 0.58 * (u - 0.3) / 0.7)
        return np.maximum(t * f / 2, K["te_half_min"])

    def shape(self, r=0.3):
        K = self.K
        hs = K["half_span"]

        def f(P):
            d2 = poly_sdf(P[:, :2], self.poly)
            dz = np.abs(P[:, 2]) - self.half_t(P[:, 0], P[:, 1])
            q0, q1 = d2 + r, dz + r
            return np.hypot(np.maximum(q0, 0), np.maximum(q1, 0)) + np.minimum(np.maximum(q0, q1), 0) - r
        return Shape(f, (-hs - 0.1, K["root_le_y"] - 0.1, -K["t_root"]), (hs + 0.1, K["tip_te_y"] + 0.1, K["t_root"]))

    def engrave(self, poly2d, depth):
        """Cut region: inside poly2d (x, y) and within depth below the top surface."""
        V = np.asarray(poly2d, dtype=np.float64)

        def f(P):
            return np.maximum(poly_sdf(P[:, :2], V), (self.half_t(P[:, 0], P[:, 1]) - depth) - P[:, 2])
        return Shape(f, (V[:, 0].min() - 0.1, V[:, 1].min() - 0.1, -0.2), (V[:, 0].max() + 0.1, V[:, 1].max() + 0.1, 1.5))


def line2d(a, b, w):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    n = np.array([-d[1], d[0]]) / np.linalg.norm(d) * w / 2
    return [tuple(a + n), tuple(b + n), tuple(b - n), tuple(a - n)]


def knell(S):
    """Flying-wing loitering UAV: cropped-delta wing blended into a cigar fuselage, split-chevron winglets (upper fin
    up, lower fin down, both swept back), pusher prop, keel spine, nose sensor with split-chevron windows, warhead
    band, elevon hinge lines, access hatches and blisters; flight-stem socket on the CG (origin)."""
    K = S["knell"]
    W = KnellWing(K)
    o = Ops()
    o.add(W.shape())
    # panel lines on the wing top (cut before the fuselage blends in): elevon hinge lines, root hatch, tip panel line
    hs = K["half_span"]
    for s in (-1, 1):
        a = (s * 5.6, K["root_te_y"] + (K["tip_te_y"] - K["root_te_y"]) * 5.6 / hs - 1.7)
        b = (s * 14.6, K["root_te_y"] + (K["tip_te_y"] - K["root_te_y"]) * 14.6 / hs - 1.5)
        o.cut(W.engrave(line2d(a, b, 0.44), 0.25))
        for (p, q) in (((s * 5.6, a[1]), (s * 5.6, a[1] + 1.55)), ((s * 14.6, b[1]), (s * 14.6, b[1] + 1.35))):
            o.cut(W.engrave(line2d(p, q, 0.44), 0.25))                                # elevon ends
        o.cut(W.engrave(line2d((s * 12.0, 3.4), (s * 12.0, 8.6), 0.44), 0.25))          # outer panel joint
    for (x0, y0) in ((4.4, 0.6),):                                                    # access hatch (left root)
        ring = [(x0, y0), (x0 + 3.0, y0), (x0 + 3.0, y0 + 2.4), (x0, y0 + 2.4)]
        for i in range(4):
            o.cut(W.engrave(line2d(ring[i], ring[(i + 1) % 4], 0.44), 0.25))
    # fuselage: cigar with a bulbous sensor nose, blended into the wing
    fus = chain([(v3(0, -11.85, 0.1), 1.75), (v3(0, -6.0, 0.15), 1.9), (v3(0, 3.5, 0.15), 1.6),
                 (v3(0, 8.9, 0.2), 0.85)], smooth=0.8)
    o.add(fus, 0.9)
    o.add(cyl(v3(0, -7.75, 0.15), v3(0, -7.3, 0.15), 2.07, 0.1), 0.04)                 # warhead band ~0.15 proud
    o.add(capsule(v3(0, -11.2, 1.65), v3(0, 7.6, 1.15), 0.4), 0.25)                    # keel spine 0.8 wide
    for s in (-1, 1):                                                                  # blisters (antennas)
        o.add(capsule(v3(s * 8.5, 4.4, 0.55), v3(s * 8.5, 5.4, 0.5), 0.32), 0.12)
    # nose sensor: split-chevron windows on the chin, and a small pitot
    split_chevron_cuts(o, v3(0, -13.25, -0.55), unit((0, -1, -0.5)), spread=0.55)
    # winglets: upper fin up and canted out, lower fin down and canted out, both swept back (split chevron in side view)
    WL = K["winglet"]
    cant = math.radians(WL["cant_deg"])
    for s in (-1, 1):
        root = v3(s * (hs - 0.25), 0, 0)
        up = v3(s * math.sin(cant), 0, math.cos(cant))
        dn = v3(s * math.sin(cant), 0, -math.cos(cant))
        hu, hl = WL["height"], WL["lower_height"]
        o.add(plate(root, up, (0, 1, 0), [(-0.2, WL["root_le_y"]), (-0.2, WL["root_le_y"] + WL["root_chord"]),
                                          (hu, WL["top_le_y"] + WL["top_chord"]), (hu, WL["top_le_y"])], WL["thick"], 0.3), 0.3)
        o.add(plate(root, dn, (0, 1, 0), [(-0.2, 7.8), (-0.2, 11.2), (hl, 11.5), (hl, 9.7)], WL["thick"], 0.3), 0.3)
    # pusher prop: spinner + two blades (0.8 mm) in the plane y = prop y
    P = K["prop"]
    o.add(round_cone(v3(0, 8.8, 0.2), v3(0, P["y"] + 1.1, 0.2), 0.95, 0.35), 0.2)
    prop(o, v3(0, P["y"], 0.2), (0, 1, 0), P["r"], 2, P["chord0"], P["chord1"], P["thick"], P["phase_deg"],
         P["pitch_deg"], r0=0.3, sweep_tip=0.3, ref=(1, 0, 0))
    # flight-stem socket boss on the CG
    st = K["stem_socket"]
    o.add(cyl(v3(*st["xy"], -1.2), v3(*st["xy"], st["boss_bottom_z"]), st["boss_r"], 0.3), 0.3)
    round_socket_up(o, (*st["xy"], st["boss_bottom_z"]), st["d"], st["depth"])
    return o


# ================================================================================================ launcher
def rail_frame(S):
    L = S["launcher"]
    e = math.radians(L["elev_deg"])
    a = v3(0, -math.cos(e), math.sin(e))          # launch direction (forward, up)
    n = v3(0, math.sin(e), math.cos(e))           # rail up-normal
    piv = v3(0, 0, L["pivot_z"])
    return a, n, piv


def shuttle_top(S):
    """Point on the shuttle top where the Knell's boss seats (its socket axis = n)."""
    L = S["launcher"]
    a, n, piv = rail_frame(S)
    return piv + n * 1.3 + a * L["shuttle_s"] + n * (L["rail_half"][1] + 0.6 + 1.2)


def launcher_rail(S):
    """Rail launcher: pedestal with the 2.0 mm D-flat peg (down), trunnion yoke, 2.6 m-class box rail at 12 deg with
    lightening pockets, guide strips, launch ram underneath, shuttle with a 1.6 pin that takes the Knell's stem socket."""
    L = S["launcher"]
    a, n, piv = rail_frame(S)
    x = v3(1, 0, 0)
    Rr = np.stack([x, a, n], axis=1)
    hl = L["rail_len"] / 2
    hw, hh = L["rail_half"]
    rc = piv + n * 1.3                                                                 # rail centre line
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, 1.0), 2.6, 0.3))                                  # flange (rests on the socket boss)
    o.add(rbox(v3(0, 0, 3.4), (1.3, 1.6, 2.7), I3, 0.3), 0.3)                         # column
    for s in (-1, 1):
        o.add(rbox(v3(s * 1.7, 0, piv[2] - 0.6), (0.45, 1.3, 1.9), I3, 0.2), 0.25)       # yoke cheeks 0.9
    o.add(cyl(piv - x * 2.4, piv + x * 2.4, 0.6, 0.15), 0.1)                           # trunnion pin
    o.add(rbox(rc, (hw, hl, hh), Rr, 0.3), 0.3)                                        # box rail 2.2 x 2.4
    for s in (-1, 1):
        o.add(rbox(rc + x * s * 0.65 + n * (hh + 0.3), (0.35, hl - 0.4, 0.3), Rr, 0.12), 0.08)   # guide strips
    for t in np.arange(-hl + 3.2, hl - 2.0, 4.2):                                       # lightening pockets 0.35 deep
        if abs(t) < 2.6:
            continue
        for s in (-1, 1):
            o.cut(rbox(rc + a * t + x * s * hw, (0.35, 1.5, 0.7), Rr, 0.1))
    o.add(capsule(rc + a * (-hl + 2.5) - n * (hh + 0.55), rc + a * (hl - 6.0) - n * (hh + 0.55), 0.75), 0.25)  # ram
    o.add(rbox(rc + a * (hl - 0.6) + n * 0.6, (hw + 0.2, 0.6, hh + 0.6), Rr, 0.2), 0.15)  # front stop
    # shuttle + pin (1.6, into the Knell's 1.8 socket)
    sp = rc + a * L["shuttle_s"] + n * (hh + 0.6 + 0.6)
    o.add(rbox(sp, (1.5, 1.6, 0.6), Rr, 0.2), 0.12)
    st = shuttle_top(S)
    o.add(cyl(st - n * 0.3, st + n * L["shuttle_pin_len"], L["shuttle_pin_d"] / 2, 0.25), 0.05)
    # split-chevron marking on the front stop face
    split_chevron_cuts(o, rc + a * (hl + 0.0) + n * 0.6, a, up=n, spread=0.55, bar=(0.55, 0.3, 0.22))
    peg_down(o, (0, 0, 0), L["peg_d"], L["peg_len"], key=tuple(L["key"]))
    return o


def launcher_tripod(S):
    """Ground tripod for the launcher: head with the 2.0 mm D-flat socket, three splayed 1.4 mm legs, spreader bars,
    flat foot pads (prints on its feet)."""
    L = S["launcher"]
    T = L["tripod"]
    o = Ops()
    top = T["head_top_z"]
    o.add(cyl(v3(0, 0, top - 3.2), v3(0, 0, top), T["head_r"], 0.3))
    feet = []
    for k in range(3):
        ang = math.radians(90 + 120 * k)
        f = v3(T["foot_r"] * math.cos(ang), T["foot_r"] * math.sin(ang), 0.0)
        feet.append(f)
        o.add(capsule(v3(0, 0, top - 2.6) + 0.12 * f, f + v3(0, 0, 0.75), T["leg_r"]), 0.3)
        o.add(cyl(f + v3(0, 0, 0), f + v3(0, 0, 0.75), 1.3, 0.2), 0.3)                  # foot pad
    for k in range(3):                                                                 # spreader bars at 40 %
        p = lambda f: v3(0, 0, top - 2.6) + 0.12 * f + (f + v3(0, 0, 0.75) - v3(0, 0, top - 2.6) - 0.12 * f) * 0.55  # noqa: E731
        o.add(capsule(p(feet[k]), p(feet[(k + 1) % 3]), 0.55), 0.2)
    o.cut(Shape(lambda P: P[:, 2], (-20, -20, -2), (20, 20, 0)))
    socket_down(o, (0, 0, top), L["peg_d"], L["sock_depth"], key=tuple(L["key"]))
    return o


def roof_pad(S):
    """Wayfarer roof adapter: 10 x 5.8 x 1.2 glue plate (sized to the measured flat strip between the engine-deck
    louvres and the glacis) with a boss and a THROUGH 2.0 mm D-flat socket (the roof closes it, so it is never a cup),
    engraved split-chevron arrow beside the boss pointing the launch direction (-y)."""
    L = S["launcher"]
    P = L["roof_pad"]
    o = Ops()
    hx, hy = P["half"]
    o.add(rbox(v3(0, 0, P["t"] / 2), (hx, hy, P["t"] / 2), I3, 0.35))
    o.add(cyl(v3(0, 0, P["t"] - 0.4), v3(0, 0, P["boss_top_z"]), P["boss_r"], 0.3), 0.3)
    for s in (-1, 1):
        o.cut(rbox(v3(3.75 + s * 0.55, 0.35, P["t"]), (0.65, 0.22, 0.3), rot(RZ, -s * 35), 0.03))   # arrow 0.44 x 0.3
    o.cut(d_peg(v3(0, 0, P["boss_top_z"] + 0.01), (0, 0, -1), L["peg_d"], P["boss_top_z"] + 1.0, key=tuple(L["key"]), grow=0.1))
    return o


# ================================================================================================ stem and bases
def base_stem(S, key):
    """Round base, chevron deck seams, vented 5x2 magnet pocket, launch pad with a raked 1.8 stem socket."""
    B = S["bases"][key]
    G = S["bases"]
    o = Ops()
    base_body(o, B["d"], B["h"], B["inset"])
    pad = B["pad"]
    deck_seams(o, B["d"], B["h"], B["inset"], keep_out=3.6, clear=[(pad["xy"][0], pad["xy"][1], pad["r"] + 0.8)])
    magnet_pocket(o, G["pocket_d"], G["pocket_depth"], G["vent_w"], G["vent_d"], B["d"] / 2)
    launch_pad(o, pad["xy"], B["h"], pad["r"], pad["h"], B["rake_deg"], S["stem"]["socket_d"], pad["socket_depth"])
    return o


def base_tether(S):
    """50 mm tether-station base for the tethered Belfry: generator box with louvres and an exhaust, cable spool on
    two A-frame cheeks with wound-cable grooves, cable run to a fairlead pedestal whose vertical 1.8 socket takes the
    stem as the tether (the stem IS the tether cable)."""
    B = S["bases"]["base-50-tether"]
    G = S["bases"]
    h = B["h"]
    sp, gen, fl = B["spool"], B["generator"], B["fairlead"]
    o = Ops()
    base_body(o, B["d"], h, B["inset"])
    gc = gen["c"]
    deck_seams(o, B["d"], h, B["inset"], keep_out=4.2,
               clear=[(gc[0], gc[1], math.hypot(*gen["half"][:2]) + 0.9), (sp["c"][0], sp["c"][1], 7.6)])
    magnet_pocket(o, G["pocket_d"], G["pocket_depth"], G["vent_w"], G["vent_d"], B["d"] / 2, vent_dir=(1.0, 0.0))
    # generator box
    gx, gy, gz = gen["half"]
    o.add(rbox(v3(gc[0], gc[1], h - 0.2 + gz), (gx, gy, gz), I3, 0.5), 0.3)
    for k in range(5):                                                                 # louvres 0.44 x 0.35 on the front
        o.cut(rbox(v3(gc[0] - 3.6 + 1.8 * k, gc[1] - gy, h + gz), (0.22, 0.35, 2.4), I3, 0.0))
    o.add(cyl(v3(gc[0] + 3.2, gc[1] + 1.5, h + 2 * gz - 0.4), v3(gc[0] + 3.2, gc[1] + 1.5, h + 2 * gz + 2.4), 0.8, 0.15), 0.2)
    o.cut(cyl(v3(gc[0] + 3.2, gc[1] + 1.5, h + 2 * gz + 1.9), v3(gc[0] + 3.2, gc[1] + 1.5, h + 2 * gz + 3.0), 0.35))
    o.add(rbox(v3(gc[0] - 1.5, gc[1] + 1.0, h + 2 * gz + 0.1), (2.4, 2.0, 0.3), I3, 0.15), 0.1)   # top hatch 0.3 proud
    # spool: drum (axis x) with flanges, cable grooves, two A-frame cheeks, axle caps
    c = v3(sp["c"])
    hw = sp["w"] / 2
    o.add(cyl(c - v3(hw - 0.8, 0, 0), c + v3(hw - 0.8, 0, 0), sp["r"] - 0.9, 0.2), 0.0)
    for s in (-1, 1):
        o.add(cyl(c + v3(s * (hw - 0.8), 0, 0), c + v3(s * hw, 0, 0), sp["r"], 0.2), 0.1)
    for xg in np.arange(-hw + 1.6, hw - 1.3, 0.9):                                     # wound cable, 0.44 x 0.25
        o.cut(Shape(lambda P, xg=xg: np.maximum(np.abs(P[:, 0] - c[0] - xg) - 0.22,
                                                (sp["r"] - 0.9 - 0.25) - np.hypot(P[:, 1] - c[1], P[:, 2] - c[2])),
                    c - v3(hw, sp["r"] + 1, sp["r"] + 1), c + v3(hw, sp["r"] + 1, sp["r"] + 1)))
    for s in (-1, 1):
        xc = c[0] + s * (hw + 0.55)
        for dy in (-1, 1):
            o.add(capsule(v3(xc, c[1] + dy * 4.6, h + 0.3), v3(xc, c[1], c[2]), 0.55), 0.2)   # A-frame legs 1.1
        o.add(rbox(v3(xc, c[1], h + 0.3), (0.55, 5.4, 0.45), I3, 0.2), 0.2)                # foot rail
        o.add(cyl(v3(xc - s * 0.3, c[1], c[2]), v3(xc + s * 0.7, c[1], c[2]), 1.1, 0.2), 0.15)  # axle cap
    # fairlead pedestal at the centre: column, sheave housing, vertical stem socket
    fx, fy = fl["xy"]
    o.add(cyl(v3(fx, fy, h - 0.3), v3(fx, fy, fl["top_z"]), fl["r"], 0.5), 0.3)
    o.add(cyl(v3(fx, fy, h - 0.3), v3(fx, fy, h + 0.9), fl["r"] + 1.1, 0.3), 0.3)      # foot flange
    o.add(rbox(v3(fx, fy + 1.9, fl["top_z"] - 1.6), (1.2, 1.4, 1.2), I3, 0.3), 0.3)    # sheave housing toward the spool
    split_chevron_cuts(o, v3(fx, fy - fl["r"] + 0.05, fl["top_z"] - 3.0), FWD, spread=0.55)
    # cable from the drum to the sheave housing (1.0) and a power lead from the generator (0.9) on the deck
    o.add(tube([c + v3(0, -sp["r"] + 0.95, -1.6), v3(fx, fy + 4.4, fl["top_z"] - 2.0), v3(fx, fy + 2.6, fl["top_z"] - 1.7)], 0.5), 0.15)
    o.add(tube([v3(gc[0] + gx - 0.5, gc[1] + 2.2, h + 0.35), v3(-3.6, -2.2, h + 0.35), v3(fx - 2.8, fy - 0.8, h + 0.35)], 0.45), 0.2)
    # M8: a mast socket (1.2 D-flat, the Belfry's mast family) on the generator roof: the relay / radar masts also
    # stand on the ground station
    ms = gen["mast_socket"]
    mx, my = gc[0] + ms["offset"][0], gc[1] + ms["offset"][1]
    gtop = h - 0.2 + 2 * gz
    o.add(cyl(v3(mx, my, gtop - 0.2), v3(mx, my, gtop + ms["boss_h"]), ms["boss_r"], 0.25), 0.2)
    socket_down(o, (mx, my, gtop + ms["boss_h"]), ms["peg_d"], ms["depth"])
    o.cut(cyl(v3(fx, fy, fl["top_z"] + 1.0), v3(fx, fy, fl["top_z"] - fl["socket_depth"]), S["stem"]["socket_d"] / 2))
    return o


def tether_mast_top(S):
    """Socket mouth of the generator-roof mast socket on the tether base (base frame)."""
    B = S["bases"]["base-50-tether"]
    gen = B["generator"]
    ms = gen["mast_socket"]
    return (gen["c"][0] + ms["offset"][0], gen["c"][1] + ms["offset"][1], B["h"] - 0.2 + 2 * gen["half"][2] + ms["boss_h"])
