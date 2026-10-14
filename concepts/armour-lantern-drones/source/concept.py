"""Lantern-pattern Squad Drone Kit (SD-1 Wisp recon quadcopter, SD-2 Tick ground drone, SD-C pack cradle):
concept blockout at 1:56 (mm, z up, faces -y). Every drone fits a 32 mm infantry base.
    ~/ai-stack/venvs/sculpt/bin/python concepts/armour-lantern-drones/source/concept.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "_tools"))
from armour_kit import (AMBER, BASE, BONE, DARK, HULL, HULL2, METAL, PLATE, Kit, base_disc, beam, capsule, cbox, cyl,  # noqa: E402
                        ellipsoid, hull, rot, sphere, track_loop, v3)

STEM = "#b8c6cf"
K = Kit("armour-lantern-drones", "Lantern-pattern Squad Drone Kit", "SD-1 / SD-2", "Fireteam recon & ground drones")
K.dims_text = "Wisp SD-1: 16 x 16 x 4 mm (0.9 m span)  |  Tick SD-2: 13 x 19 x 11 mm (~1 m long)  |  32 mm bases"


def wisp(o, docked=False):
    """SD-1 Wisp: chevron-plan body with a keel spine, four ducted rotors, chin sensor with split chevron lenses."""
    o = v3(o)
    K.add(hull([o + v3(0, -6.0, 0), o + v3(-3.2, -1.0, 0), o + v3(3.2, -1.0, 0), o + v3(-2.2, 4.5, 0), o + v3(2.2, 4.5, 0),
                o + v3(0, -5.0, 1.6), o + v3(-2.2, -0.6, 2.0), o + v3(2.2, -0.6, 2.0), o + v3(-1.5, 3.8, 1.6),
                o + v3(1.5, 3.8, 1.6), o + v3(0, -4.5, -1.2), o + v3(0, 3.5, -1.0)]), HULL)
    K.add(capsule(o + v3(0, -4.6, 1.8), o + v3(0, 3.6, 2.0), 0.45, 1), PLATE)                     # keel spine
    if docked:
        return
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = o + v3(sx * 5.2, sy * 4.4, 0.6)
            K.add(beam(o + v3(sx * 1.5, sy * 1.2, 0.6), c, 1.2, 0.9, 0.2), HULL2)                 # arm
            K.add(cyl(c - v3(0, 0, 0.9), c + v3(0, 0, 0.9), 2.9, 24), HULL2)                      # duct
            K.add(cyl(c - v3(0, 0, 0.6), c + v3(0, 0, 1.0), 2.3, 24), DARK)                       # rotor well
    K.add(sphere(o + v3(0, -4.0, -1.4), 1.3, 2), DARK)                                           # chin sensor ball
    for s in (-1, 1):
        K.add(cbox((1.2, 0.6, 0.6), o + v3(s * 0.55, -5.2, -1.2), 0.1, rot((0, 1, 0), s * 24)), AMBER)


# --- 1: rifleman with the SD-C cradle on the spine pack carrying a folded Wisp
K.figure((0, 0, 0), yaw=0)
K.add(cbox((4.6, 1.2, 4.0), (0, 5.6, 26.0), 0.3), DARK)                                          # cradle plate
K.add(cbox((5.6, 3.2, 6.4), (0, 7.4, 25.6), 0.6), HULL)                                          # folded Wisp
K.add(capsule((0, 9.0, 23.0), (0, 9.0, 28.4), 0.45, 1), PLATE)
K.add(cbox((1.6, 0.5, 0.6), (0, 9.2, 29.0), 0.1), AMBER)

# --- 2: Wisp in flight on a clear stem, 32 mm base
x2 = 38
K.add(base_disc((x2, 0, 0), 32.0, 3.0), BASE)
K.add(cyl((x2, 0, 3), (x2, 0, 25), 0.8, 12), STEM)
wisp((x2, 0, 27))

# --- 3: Tick ground drone on a 32 mm base (default: sensor mast + Talon carbine)
x3 = 76
K.add(base_disc((x3, 0, 0), 32.0, 3.0), BASE)
z = 3.0
for s in (-1, 1):
    K.add(track_loop(x3 + s * 4.0, -7.5, 7.5, z, z + 4.6, 2.6, 16), DARK)
K.add(hull([(x3 - 3, -8.5, z + 2.0), (x3 + 3, -8.5, z + 2.0), (x3 - 3.4, 7, z + 1.6), (x3 + 3.4, 7, z + 1.6),
            (x3 - 2.6, -5.5, z + 5.6), (x3 + 2.6, -5.5, z + 5.6), (x3 - 3.2, 6.5, z + 5.8), (x3 + 3.2, 6.5, z + 5.8),
            (x3, -9.5, z + 3.4)]), HULL)                                                           # chevron-prow body
for s in (-1, 1):
    K.add(cbox((1.1, 13.5, 3.4), (x3 + s * 5.75, -0.5, z + 3.4), 0.3), PLATE)                     # track guards
K.add(capsule((x3, -5.0, z + 6.0), (x3, 6.0, z + 6.0), 0.45, 1), PLATE)                           # keel ridge
K.add(cyl((x3 - 1.6, 3.5, z + 5.6), (x3 - 1.6, 3.5, z + 9.2), 0.5, 8), METAL)                    # sensor mast
K.add(cbox((2.8, 1.8, 1.6), (x3 - 1.6, 3.2, z + 9.8), 0.3), HULL2)
for s in (-1, 1):
    K.add(cbox((1.2, 0.5, 0.55), (x3 - 1.6 + s * 0.6, 2.25, z + 9.9), 0.1, rot((0, 1, 0), s * 24)), AMBER)
K.add(cbox((1.6, 4.0, 1.6), (x3 + 1.6, -1.5, z + 6.6), 0.3), HULL2)                              # carbine mount
K.add(cyl((x3 + 1.6, -3.5, z + 6.8), (x3 + 1.6, -8.0, z + 6.8), 0.45, 8), METAL)

if __name__ == "__main__":
    K.finish(ROOT, hero={"az": -32, "el": 26},
             sheet={"views": [(0, 0, "FRONT (L-R: cradle, Wisp, Tick)", 0, 0), (-35, 12, "3/4 FRONT", 1, 0),
                              (0, 90, "TOP (front down)", 0, 1), (145, 18, "3/4 BACK (cradle on the spine pack)", 1, 1)],
                    "note": "front and top orthographic, same scale"})
