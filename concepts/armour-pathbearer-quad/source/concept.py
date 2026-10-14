"""Pathbearer-class Quadruped Carrier (QC-4): unmanned four-legged cargo / weapons walker, concept blockout at 1:56.
    ~/ai-stack/venvs/sculpt/bin/python concepts/armour-pathbearer-quad/source/concept.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "_tools"))
from armour_kit import (AMBER, BONE, DARK, HULL, HULL2, METAL, PLATE, Kit, beam, capsule, cbox, cyl,  # noqa: E402
                        ellipsoid, hull, rot, sphere, v3)

K = Kit("armour-pathbearer-quad", "Pathbearer-class Quadruped Carrier", "QC-4", "Unmanned quadruped cargo / weapons carrier")

# --- body: a long low spine hull with a dorsal keel (the helm crest grown into a backbone)
K.add(hull([(-13, -46, 24), (13, -46, 24), (-15, 44, 24), (15, 44, 24), (-11, -50, 30), (11, -50, 30),
            (-15, -40, 35), (15, -40, 35), (-15, 46, 33), (15, 46, 33), (-10, -42, 38), (10, -42, 38),
            (-10, 40, 38), (10, 40, 38), (-8, -40, 21), (8, -40, 21), (-8, 40, 21), (8, 40, 21)]), HULL)
K.add(hull([(0, -44, 38), (0, -38, 42.5), (0, 36, 42.5), (0, 44, 38), (-2, -42, 37.5), (2, -42, 37.5),
            (-2, 42, 37.5), (2, 42, 37.5)]), PLATE)                                               # dorsal keel
for y in (-30, -14, 2, 18, 32):
    K.add(cbox((24, 1.2, 1.0), (0, y, 38.4), 0.3), DARK)                                         # cargo rail tie-downs

# --- panniers: modular cargo cassettes slung either side (long-short-long rhythm)
for s in (-1, 1):
    for y0, y1, col in ((-28, -6, HULL2), (-4.5, 6.5, BONE), (8, 30, HULL2)):
        K.add(cbox((9, y1 - y0, 15), (s * 19.5, (y0 + y1) / 2, 27), 1.2), col)
    K.add(beam((s * 15, -30, 35.5), (s * 15, 32, 35.5), 1.4, 1.4, 0.3), METAL)                    # pannier rail
    K.add(cbox((1.0, 6, 3), (s * 24.3, -17, 30), 0.3), AMBER)                                    # cassette ID lights

# --- legs: high insect knees, long shins, splayed pad feet (a different gait silhouette from the Talus biped)
for sx in (-1, 1):
    for sy in (-1, 1):
        hip = v3(sx * 14, sy * 36, 30)
        knee = v3(sx * 31, sy * 46, 47)
        foot = v3(sx * 40, sy * 56, 4)
        K.add(cyl(hip - v3(sx * 2, 0, 0), hip + v3(sx * 4, 0, 0), 5.2, 20), DARK)               # hip drive
        K.add(beam(hip, knee, 6.5, 7.5, 1.2), HULL)                                              # thigh
        K.add(beam(hip + v3(sx * 1, sy * 1, 4.5), knee + v3(0, 0, 3.5), 3.5, 2.2, 0.5), PLATE)  # thigh plate
        K.add(sphere(knee, 4.2), DARK)
        K.add(ellipsoid(knee + v3(sx * 1.2, sy * 1.6, 2.4), (4.6, 4.6, 3.0)), PLATE)             # knee cap
        K.add(beam(knee, foot + v3(0, 0, 3), 5.0, 5.5, 1.0), HULL2)                              # shin
        K.add(beam(knee + v3(-sx * 2.5, 0, -3), foot + v3(-sx * 1.5, 0, 12), 1.8, 1.8, 0.4), METAL)  # shin ram
        K.add(cyl(foot + v3(0, 0, -4), foot + v3(0, 0, -1), 5.4, 20), DARK)                      # pad foot
        K.add(hull([foot + v3(-3.5, -3.5, -1), foot + v3(3.5, -3.5, -1), foot + v3(-3.5, 3.5, -1), foot + v3(3.5, 3.5, -1),
                    foot + v3(0, 0, 4)]), HULL2)                                                 # ankle cowl

# --- sensor head: a small Vigil helm on a short neck: split chevron lenses, keel crest
K.add(beam((0, -46, 31), (0, -54, 31), 6, 6, 1.0), DARK)
hc = v3(0, -58, 31)
K.add(ellipsoid(hc, (6.5, 8.0, 5.8), rot((1, 0, 0), 6)), HULL2)
K.add(capsule(hc + v3(0, -6.5, 4.2), hc + v3(0, 6, 5.0), 1.0), PLATE)
for s in (-1, 1):
    K.add(cbox((4.0, 1.4, 1.6), hc + v3(s * 2.2, -7.4, 0.8), 0.3, rot((0, 0, 1), s * -24) @ rot((0, 1, 0), s * 22)), AMBER)
K.add(ellipsoid(hc + v3(0, -6, -3.2), (3.0, 2.4, 1.8)), DARK)                                    # chin sensor

# --- default loadout: Picket remote weapon on the forward cargo rail (a Lance rifle on a gimbal)
K.add(cyl((0, -32, 38), (0, -32, 41), 4.5, 20), HULL2)
K.add(cbox((6, 9, 4.5), (0, -33, 43.2), 0.8), HULL2)
K.add(cyl((1.5, -37, 43.5), (1.5, -50, 43.5), 0.8, 10), METAL)
K.add(cbox((2.6, 2.6, 2.2), (-2.6, -36.5, 44.8), 0.4), AMBER)

# --- rear: tow hitch, mast, and the casualty litter cradle slung under the belly
K.add(cbox((6, 6, 4), (0, 48, 27), 0.8), DARK)
K.add(cyl((7, 42, 38), (7, 42, 56), 0.5, 8), METAL)
K.add(cbox((14, 40, 2.0), (0, 0, 17.5), 0.5), METAL)
for y in (-18, 18):
    K.add(cyl((0, y, 18), (0, y, 22), 0.8, 8), METAL)

K.figure((64, -12, 0), yaw=-20)

if __name__ == "__main__":
    K.finish(ROOT)
