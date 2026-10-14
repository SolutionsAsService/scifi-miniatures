"""Talus-class Heavy Support Frame (HF-2): crewed bipedal walker, concept blockout at 1:56 (mm, z up, faces -y).
    ~/ai-stack/venvs/sculpt/bin/python concepts/armour-talus-walker/source/concept.py
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "_tools"))
from armour_kit import (AMBER, BASE, BONE, DARK, HULL, HULL2, METAL, PLATE, Kit, base_disc, beam, capsule, cbox, cone,  # noqa: E402
                        cyl, ellipsoid, hull, rot, sphere, v3)

K = Kit("armour-talus-walker", "Talus-class Heavy Support Frame", "HF-2", "Crewed bipedal fire-support walker")
K.add(base_disc((0, 2, 0), 60.0, 3.5), BASE)
B = 3.5

# --- legs: forward knees, chevron-toed feet, greaves in the long-short-long plate rhythm
stance = {1: (11, -7), -1: (-11, 7)}           # left (+x) foot forward
for s, (fx, fy) in stance.items():
    ank = v3(fx, fy, B + 8)
    knee = v3(fx * 1.08, fy - 9, B + 24)
    hip = v3(s * 9.5, 1, B + 38)
    K.add(hull([(fx, fy - 15, B), (fx - 7, fy - 8, B), (fx + 7, fy - 8, B), (fx - 5.5, fy + 9, B), (fx + 5.5, fy + 9, B),
                (fx, fy - 13, B + 3.5), (fx - 5, fy - 5, B + 6.5), (fx + 5, fy - 5, B + 6.5), (fx - 4, fy + 7, B + 6),
                (fx + 4, fy + 7, B + 6)]), HULL2)                                                # chevron-toed foot
    K.add(hull([(fx, fy + 8, B), (fx, fy + 13, B), (fx - 2, fy + 8, B + 3), (fx + 2, fy + 8, B + 3)]), DARK)  # heel spur
    K.add(sphere(ank, 3.6), DARK)
    K.add(beam(ank, knee, 7.5, 7.0, 1.2), HULL)                                                 # shin
    for t0, t1 in ((0.05, 0.42), (0.47, 0.62), (0.67, 0.95)):                                  # greave plates 3-2-3
        a, b = ank + (knee - ank) * t0, ank + (knee - ank) * t1
        K.add(beam(a + v3(0, -3.6, 0), b + v3(0, -3.6, 0), 8.6, 2.4, 0.7), PLATE)
    K.add(ellipsoid(knee + v3(0, -3, 0.5), (4.6, 3.4, 5.0)), PLATE)                              # knee cap
    K.add(beam(knee, hip, 8.5, 8.5, 1.4), HULL)                                                 # thigh
    K.add(beam(knee + v3(s * 4.5, 3, 0), hip + v3(s * 4.5, 3, -2), 2.4, 2.4, 0.5), METAL)       # thigh ram
    K.add(cyl(hip + v3(-s * 3, 0, 0), hip + v3(s * 4.5, 0, 0), 5.0, 20), DARK)                  # hip actuator

K.add(cbox((24, 15, 9), (0, 1.5, B + 40), 2.0), HULL2)                                         # pelvis

# --- torso: the cockpit pod is a giant Vigil helm, split chevron viewports, respirator chin, keel crest
tc = v3(0, -1, B + 54)
K.add(ellipsoid(tc, (14.5, 13.0, 12.0), rot((1, 0, 0), -8)), HULL)
K.add(ellipsoid(tc + v3(0, -9.5, -7), (7.5, 5.0, 4.6)), HULL2)                                 # respirator chin
for j in range(3):
    K.add(cbox((9 - 2 * j, 1.6, 1.0), tc + v3(0, -14.2 + j * 0.5, -6 - 1.5 * j), 0.3), DARK)    # chin vents
for s in (-1, 1):
    K.add(cbox((8.5, 2.2, 3.0), tc + v3(s * 5.0, -12.6, 2.2), 0.6, rot((0, 0, 1), s * -24) @ rot((0, 1, 0), s * 22)), AMBER)
K.add(capsule(tc + v3(0, -12.5, 3.5), tc + v3(0, -6, 11.0), 1.4), PLATE)                       # keel crest, front
K.add(capsule(tc + v3(0, -6, 11.0), tc + v3(0, 7, 12.0), 1.4), PLATE)
K.add(capsule(tc + v3(0, 7, 12.0), tc + v3(0, 14, 6.0), 1.4), PLATE)

# --- spine power pack with twin stacks
K.add(cbox((19, 10, 21), (0, 14, B + 53), 2.0), HULL2)
K.add(cbox((7, 3, 18), (0, 19.5, B + 53), 0.8), DARK)
for s in (-1, 1):
    K.add(cyl((s * 7, 15, B + 62), (s * 7.5, 17, B + 72), 2.0, 14), DARK)

# --- shoulders: layered caps that sweep back (the trooper's shoulder, not a pauldron)
for s in (-1, 1):
    sh = v3(s * 18, 1, B + 59)
    K.add(sphere(sh, 4.5), DARK)
    K.add(ellipsoid(sh + v3(s * 1.0, 1.5, 3.4), (8.0, 9.5, 3.0), rot((0, 1, 0), s * -18)), PLATE)
    K.add(ellipsoid(sh + v3(s * 2.0, 3.0, 0.2), (7.4, 8.2, 2.8), rot((0, 1, 0), s * -30)), HULL)

# --- right arm (-x): Hammerfall twin rotary autocannon
sh, el = v3(-18, 1, B + 57), v3(-21, -2, B + 46)
K.add(beam(sh, el, 6.5, 6.5, 1.0), HULL)
K.add(sphere(el, 3.6), DARK)
K.add(cbox((10, 20, 9), (-22, -10, B + 45), 1.6), HULL2)                                         # weapon body
for dx in (-2.4, 2.4):
    K.add(cyl((-22 + dx, -20, B + 45), (-22 + dx, -36, B + 45), 1.3, 12), METAL)
K.add(cbox((7.6, 2.4, 4.0), (-22, -30, B + 45), 0.5), DARK)                                     # barrel clamp
K.add(cbox((3, 10, 7), (-28, -6, B + 45), 0.8), DARK)                                           # ammo feed
K.add(cbox((4, 3, 2), (-22, -18, B + 50.5), 0.5), AMBER)                                       # sight

# --- left arm (+x): siege claw behind a Bulwark forearm plate
sh, el, wr = v3(18, 1, B + 57), v3(21, -1, B + 45), v3(21, -14, B + 39)
K.add(beam(sh, el, 6.5, 6.5, 1.0), HULL)
K.add(sphere(el, 3.6), DARK)
K.add(beam(el, wr, 7, 7, 1.2), HULL)
K.add(cbox((3.0, 17, 15), (26.5, -7, B + 42), 1.0, rot((1, 0, 0), 18)), PLATE)                 # forearm shield plate
for a in (-1, 0, 1):
    p0 = wr + v3(a * 2.6, -1, 0)
    K.add(beam(p0, p0 + v3(a * 1.2, -6, -3), 2.0, 2.0, 0.4), DARK)                              # claw fingers
K.add(beam(wr + v3(0, -1, 1), wr + v3(0, -4, 6), 2.2, 2.2, 0.4), DARK)                          # thumb

# --- shoulder rack: Volley missile pod on the left shoulder
K.add(cbox((11, 13, 8), (17, 5, B + 71), 1.2), HULL2)
for i in range(2):
    for j in range(2):
        K.add(cyl((14.4 + i * 5.2, -1.6, B + 69 + j * 4), (14.4 + i * 5.2, -2.0, B + 69 + j * 4), 1.6, 12), DARK)

K.figure((52, -6, 0), yaw=-20)

if __name__ == "__main__":
    K.finish(ROOT)
