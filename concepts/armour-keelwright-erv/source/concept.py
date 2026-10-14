"""Keelwright-class Engineer & Recovery Vehicle (ERV-5): 6x6 wheeled combat engineer, concept blockout at 1:56.
    ~/ai-stack/venvs/sculpt/bin/python concepts/armour-keelwright-erv/source/concept.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "_tools"))
from armour_kit import (AMBER, BONE, DARK, HULL, HULL2, METAL, PLATE, Kit, beam, capsule, cbox, cyl,  # noqa: E402
                        hull, rot, sphere, v3, wheel)

GLASS = "#2f4652"
K = Kit("armour-keelwright-erv", "Keelwright-class Engineer & Recovery Vehicle", "ERV-5", "Combat engineer / armoured recovery")

# --- 6x6 running gear: one axle under the cab, a bogie pair at the rear
for y in (-50, 22, 46):
    for s in (-1, 1):
        t, r = wheel((s * 27, y, 9.5), 9.5, 8.5, (1, 0, 0), 0.5)
        K.add(t, DARK)
        K.add(r, METAL)
K.add(cbox((40, 150, 10), (0, -2, 16), 1.5), HULL2)                                             # chassis tub

# --- fenders in the long-short-long rhythm
for s in (-1, 1):
    for y0, y1 in ((-64, -36), (-33, 6), (9, 60)):
        K.add(cbox((12, y1 - y0, 2.4), (s * 26.5, (y0 + y1) / 2, 21.5), 0.8), PLATE)

# --- armoured cab: chevron-plan nose, split-chevron windscreen either side of a keel pillar, crest along the roof
K.add(hull([(-22, -66, 20), (22, -66, 20), (-23, -32, 20), (23, -32, 20), (0, -76, 22),
            (-18, -60, 44), (18, -60, 44), (-20, -32, 46), (20, -32, 46), (0, -66, 40)]), HULL)
for s in (-1, 1):
    K.add(cbox((12.5, 2.6, 6.4), (s * 9.8, -66.9, 34.5), 0.4,
               rot((0, 0, 1), s * 21.8) @ rot((1, 0, 0), -29) @ rot((0, 1, 0), s * 14)), GLASS)       # split-chevron screen
    K.add(cbox((1.0, 2.2, 6), (s * 22.2, -45, 38), 0.3), GLASS)                                  # side vision block
K.add(hull([(0, -73, 24), (0, -66, 41.5), (0, -34, 48.5), (-1.6, -70, 24), (1.6, -70, 24), (-1.6, -34, 46),
            (1.6, -34, 46), (0, -60, 46.8)]), PLATE)                                               # keel pillar + roof crest
for s in (-1, 1):
    K.add(cbox((4, 1.6, 2.2), (s * 16, -71.5, 25), 0.4), BONE)                                    # lamps
    K.add(cbox((2.2, 2.2, 2.2), (s * 18, -58.5, 45.2), 0.4), AMBER)                              # beacons

# --- dozer blade on push arms
K.add(hull([(-31, -86, 3), (31, -86, 3), (-31, -83, 21), (31, -83, 21), (-31, -80, 3), (31, -80, 3),
            (-31, -79, 21), (31, -79, 21), (0, -87.5, 12)]), PLATE)
for s in (-1, 1):
    K.add(beam((s * 18, -80, 10), (s * 18, -58, 14), 3.0, 3.0, 0.6), DARK)
    K.add(beam((s * 12, -80, 17), (s * 10, -64, 22), 1.8, 1.8, 0.4), METAL)                      # blade rams

# --- crew & sapper bay behind the cab (a Vigil engineer fireteam of four), with roof hatches and stowage
K.add(cbox((44, 30, 20), (0, -16, 30), 2.0), HULL)
for s in (-1, 1):
    K.add(cyl((s * 10, -16, 40), (s * 10, -16, 41.5), 4.0, 18), HULL2)
K.add(cbox((40, 3, 4), (0, -30, 41.5), 0.6), HULL2)
K.add(cbox((3, 34, 7), (24.5, 2, 27), 0.8), BONE)                                               # bridging plank, left
K.add(cbox((3, 34, 7), (24.5, 2, 35), 0.8), BONE)
for y in (-10, 14):
    K.add(cbox((4.4, 1.6, 17), (24.6, y, 31), 0.3), DARK)                                          # straps

# --- recovery deck: winch, slewing crane with telescopic boom, hook, rear spades
K.add(cbox((40, 60, 6), (0, 32, 24), 1.2), HULL2)
K.add(cyl((-14, 2, 28), (14, 2, 28), 4.5, 20), DARK)                                             # winch drum
K.add(cyl((0, 30, 27), (0, 30, 31), 11, 32), HULL)                                              # crane turntable
K.add(cbox((14, 16, 10), (0, 30, 36), 1.6), HULL)
base_p, tip = v3(0, 32, 38), v3(0, 82, 74)
mid = base_p + (tip - base_p) * 0.58
K.add(beam(base_p, mid, 8, 7, 1.2), HULL2)                                                     # boom, outer
K.add(beam(mid, tip, 5.5, 5, 0.8), PLATE)                                                      # boom, telescopic
K.add(beam((0, 22, 33), base_p + (tip - base_p) * 0.4 + v3(0, 0, -3.5), 3, 3, 0.6), METAL)  # lift ram
K.add(cyl(tip + v3(-3.5, 0, 0), tip + v3(3.5, 0, 0), 3.0, 16), DARK)                            # sheave
K.add(cyl(tip + v3(0, 0, -2), tip + v3(0, 0, -26), 0.45, 8), METAL)                             # cable
K.add(cbox((4.5, 3.5, 4), tip + v3(0, 0, -28), 0.6), AMBER)                                      # hook block
K.add(capsule(tip + v3(0, 0, -30.5), tip + v3(0, -1.6, -33), 0.8, 1), DARK)
for s in (-1, 1):
    K.add(beam((s * 18, 62, 16), (s * 30, 76, 2.5), 3.4, 3.4, 0.6), HULL2)                     # spade legs
    K.add(cbox((9, 6, 1.6), (s * 31, 77, 1.0), 0.4), DARK)                                       # spade pads
K.add(cbox((28, 3, 9), (0, 62, 15), 0.8), PLATE)                                                 # rear plate

K.figure((60, -46, 0), yaw=-20)

if __name__ == "__main__":
    K.finish(ROOT)
