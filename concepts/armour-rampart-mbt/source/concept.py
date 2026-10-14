"""Rampart-class Main Battle Tank (AT-7): concept blockout at 1:56 (mm, z up, faces -y). Run with the sculpt venv:
    ~/ai-stack/venvs/sculpt/bin/python concepts/armour-rampart-mbt/source/concept.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "_tools"))
from armour_kit import (AMBER, BONE, DARK, HULL, HULL2, METAL, PLATE, VIGIL, VIGIL2, Kit, box, capsule, cbox, cone, cyl,  # noqa: E402
                        ellipsoid, hull, rot, track_loop, v3)

K = Kit("armour-rampart-mbt", "Rampart-class Main Battle Tank", "AT-7", "Main battle tank / breakthrough armour")

# --- running gear: two track loops, sprocket at the rear, idler at the front
for s in (-1, 1):
    K.add(track_loop(s * 27, -64, 60, 0, 17, 15), DARK)
    for y in (-50, -33, -16, 1, 18, 35):
        K.add(cyl((s * 35, y, 6.5), (s * 35.6, y, 6.5), 3.2, 16), METAL)        # road wheel hubs peeking under skirts
# lower hull between the tracks
K.add(cbox((40, 118, 14), (0, -1, 11), 2.0), HULL2)

# --- upper hull: a wedge whose glacis runs to a keel prow (the sternum keel of the Vigil cuirass, scaled up)
K.add(hull([(-35, -50, 17), (35, -50, 17), (-35, 61, 17), (35, 61, 17),
            (-33, -40, 26), (33, -40, 26), (-33, 60, 26), (33, 60, 26),
            (-14, -68, 15), (14, -68, 15), (-10, -68, 19), (10, -68, 19)]), HULL)
K.add(hull([(0, -70, 16.5), (0, -40, 28.2), (-3.2, -40, 26), (3.2, -40, 26), (-2.5, -68, 16), (2.5, -68, 16),
            (0, -20, 28.2), (-3, -20, 26), (3, -20, 26)]), PLATE)                                 # prow keel ridge

# --- skirt plates: long-short-long rhythm (the 3-2-3 plate rhythm of the exosuit greaves), tilted out 8 degrees
for s in (-1, 1):
    for y0, y1 in ((-63, -26), (-24.6, -4), (-2.6, 36), (37.4, 58)):
        yc, L = (y0 + y1) / 2, y1 - y0
        K.add(cbox((2.6, L, 13), (s * 35.5, yc, 13.5), 0.8, rot((0, 1, 0), s * 8)), PLATE)
    K.add(hull([(s * 33, -66, 9), (s * 36.5, -63, 7), (s * 36.5, -63, 20), (s * 33, -66, 18),
                (s * 34.5, -62, 9), (s * 34.5, -62, 18)]), PLATE)  # front skirt nose

# --- engine deck: the vehicle's "spine pack", louvred like the trooper's pack
K.add(cbox((34, 30, 5), (0, 45, 28), 1.2), HULL2)
for i in range(7):
    K.add(box((28, 1.2, 0.8), (0, 33 + i * 3.8, 30.6)), DARK)
for s in (-1, 1):
    K.add(cyl((s * 22, 61, 22), (s * 22, 64, 22), 2.6, 14), DARK)                       # exhausts
    K.add(capsule((s * 31, 26, 28.5), (s * 31, 56, 28.5), 0.6, 1), METAL)               # rider rails for a fireteam
    for y in (28, 41, 54):
        K.add(cyl((s * 31, y, 26), (s * 31, y, 28.5), 0.5, 8), METAL)
K.add(cbox((40, 5, 2.2), (0, 64, 10), 0.5), METAL)                                     # rear rider step
for s in (-1, 1):
    K.add(cbox((4.5, 1.6, 2.4), (s * 24, -66.5, 20.5), 0.4), BONE)                     # headlamps
    K.add(cyl((s * 10, -69, 12), (s * 10, -66, 12), 1.6, 10), METAL)                   # tow eyes

# --- turret: chevron plan (a V nose), keel crest along the roof, split-chevron sensor slits on the cheeks
tb = [(0, -36), (-23, -16), (-21, 14), (-15, 25), (15, 25), (21, 14), (23, -16)]
tt = [(0, -28), (-17, -12), (-16, 12), (-11, 21), (11, 21), (16, 12), (17, -12)]
K.add(cyl((0, -2, 26), (0, -2, 28), 20, 40), DARK)                                     # turret ring
K.add(hull([(x, y, 27.5) for x, y in tb] + [(x, y, 40) for x, y in tt]), HULL2)
K.add(hull([(0, -29, 40.0), (0, -27, 42.6), (0, 20, 42.6), (0, 23, 40), (-1.4, -26, 40), (1.4, -26, 40),
            (-1.4, 21, 40), (1.4, 21, 40)]), PLATE)                                     # roof keel crest
for s in (-1, 1):
    K.add(cbox((7.5, 1.4, 1.8), (s * 8.5, -27.0, 35.4), 0.3, rot((0, 0, 1), s * -41) @ rot((0, 1, 0), s * 18)), AMBER)
    K.add(cbox((3.6, 9, 9), (s * 21.5, 4, 33.5), 1.0, rot((0, 0, 1), s * -4)), PLATE)  # cheek applique
    for j in range(3):
        K.add(cyl((s * 19, 18 + j * 2.6, 36), (s * 23.5, 19 + j * 2.6, 38.5), 1.0, 10), DARK)  # drone / smoke tubes

# --- main gun: Longwatch coil cannon, mantlet at the chevron nose
K.add(cbox((11, 8, 9), (0, -36, 33.2), 1.5), HULL2)
K.add(cyl((0, -38, 33.5), (0, -104, 33.5), 1.9, 20), METAL)
for i in range(6):
    y = -46 - i * 8.5
    K.add(cbox((5.8, 3.0, 5.8), (0, y, 33.5), 0.8), DARK)                              # coil sleeves
K.add(cbox((6.4, 6, 6.4), (0, -105, 33.5), 1.0), HULL2)                                # muzzle brake
K.add(box((1.2, 6.4, 2.6), (0, -105, 33.5)), DARK)

# --- commander's cupola with a Vigil helm (any VH helm drops in) and a remote weapon station
K.add(cyl((10, 6, 38.5), (10, 6, 42.5), 5.2, 24), HULL2)
K.add(ellipsoid((10, 6, 45.6), (2.5, 2.85, 2.9)), VIGIL)
K.add(capsule((10, 4.0, 47.2), (10, 8.6, 47.5), 0.55), VIGIL2)
for s in (-1, 1):
    K.add(cbox((1.5, 0.7, 0.7), (10 + s * 0.95, 3.45, 45.85), 0.15, rot((0, 1, 0), s * 24)), AMBER)
K.add(cbox((6, 7, 4), (-10, 2, 41.5), 0.8), HULL2)                                     # remote weapon station
K.add(cyl((-10, -1, 42), (-10, -14, 42), 0.8, 10), METAL)
K.add(cbox((3.4, 3.4, 2.2), (-10, 8, 41), 0.5), AMBER)                                 # its sensor block

# --- Vigil rifleman for scale
K.figure((60, -34, 0), yaw=-20)

if __name__ == "__main__":
    K.finish(ROOT)
