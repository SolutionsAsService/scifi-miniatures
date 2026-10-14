"""Matins-class Mass-Driver Walker (FS-4): long-range rail battery on a four-legged bracing walker.
Concept blockout at 1:56 (mm), with a Vigilant for scale.

Run:  ~/ai-stack/venvs/sculpt/bin/python concepts/matins-mass-driver/source/concept.py
Frame: mm, z up, faces -y, left side on +x.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "_tools"))
import numpy as np  # noqa: E402

from artillery_kit import (M, Model, box, capsule, chevron_mark, chevron_visor, cyl, finish, hull, keel, mm,  # noqa: E402
                           ellipsoid, sphere, spine_pack, tp)

ELEV = 28.0
m = Model("Matins")

# ---------------------------------------------------------------- body: hexagonal armoured cradle
BL, BW, BH = mm(5.6), mm(3.4), mm(1.7)
ZB0 = mm(1.7)
pts = []
for sx in (-1, 1):
    for z, k in ((ZB0, 0.82), (ZB0 + BH * 0.55, 1.0), (ZB0 + BH, 0.78)):
        pts += [(sx * BW / 2 * k, -BL / 2 + 8, z), (sx * BW / 2 * k, BL / 2 - 5, z), (sx * 6 * k, -BL / 2, z), (sx * 8 * k, BL / 2, z)]
m.add("hull", hull(pts))
ztop = ZB0 + BH
# crew cab as an oversized Vigil helm: egg, respirator chin, split chevron visor, keel crest
HC = np.array([0.0, -BL / 2 + 2.0, ZB0 + BH * 0.62])
m.add("hull", ellipsoid(HC, (10.5, 9.5, 8.5)))
m.add("hull2", ellipsoid(HC + (0, -5.5, -4.5), (6.5, 5.0, 4.0)))
for s in (-1, 1):
    m.add("lens", box(HC + (s * 4.2, -8.6, 1.2), (7.0, 3.0, 2.6), ry=s * 24, bevel=0.3))
    m.add("hull2", cyl(HC + (s * 8.5, 0, 0), HC + (s * 11.5, 0, 0), 3.2, 18))
keel(m, [HC + (0, -9.4, 5.0), HC + (0, -4.0, 8.9), HC + (0, 4.0, 9.2), HC + (0, 12.0, 6.5)], 1.2)
m.add("hull", capsule(HC + (0, -9.6, 3.5), HC + (0, -10.0, -2.0), 0.9))
for s in (-1, 1):
    m.add("hull2", cyl((s * (BW / 2 - 2), -BL / 2 + 22, ZB0 + BH * 0.5), (s * (BW / 2 + 2.5), -BL / 2 + 22, ZB0 + BH * 0.5), 3.6, 20))
    m.add("lens", cyl((s * (BW / 2 + 2.3), -BL / 2 + 22, ZB0 + BH * 0.5), (s * (BW / 2 + 3.0), -BL / 2 + 22, ZB0 + BH * 0.5), 2.1, 20))
    chevron_mark(m, (s * (BW / 2 + 0.25), 8, ZB0 + BH * 0.55), 11, rz=-s * 90)
m.add("hull2", box((0, 0, ZB0 - 2.0), (BW * 0.6, BL * 0.6, 4.5), bevel=1.0))                              # belly
spine_pack(m, (0, BL / 2 + 2.5, ZB0 + BH * 0.5), 18, 5, BH * 0.8)                                       # reactor / power pack

# ---------------------------------------------------------------- four bracing legs (knee high, splayed spade feet)
for sx in (-1, 1):
    for sy in (-1, 1):
        hip = np.array([sx * (BW / 2 - 3), sy * (BL / 2 - 12), ZB0 + BH * 0.45])
        knee = np.array([sx * (BW / 2 + 13), sy * (BL / 2 + 3), ZB0 + BH + 8])
        foot = np.array([sx * (BW / 2 + 22), sy * (BL / 2 + 14), 0.0])
        m.add("hull2", sphere(hip, 5.0, 2))
        m.add("hull", capsule(hip, knee, 5.0))                                                           # thigh
        for k in (0.35, 0.7):                                                                             # plate rhythm on the thigh
            c = hip + (knee - hip) * k
            m.add("hull2", capsule(c - (knee - hip) * 0.1, c + (knee - hip) * 0.1, 5.8))
        m.add("dark", sphere(knee, 5.2, 2))
        m.add("hull", hull([knee + (0, 0, 5.5), knee + (sx * 4, sy * 4, 3), knee + (-sx * 3, -sy * 3, 3.5), knee + (sx * 6, sy * 6, -2)]))   # knee plate
        ankle = foot + (0, 0, 7.0)
        m.add("hull", capsule(knee, ankle, 4.0))                                                          # shin
        m.add("metal", capsule(knee + (ankle - knee) * 0.15, knee + (ankle - knee) * 0.55, 4.7))        # shin sleeve / ram
        m.add("dark", sphere(ankle, 3.0, 1))
        d = np.array([sx, sy, 0.0]) / math.sqrt(2)
        m.add("hull2", hull([foot + d * 11, foot - d * 7, foot + np.cross(d, (0, 0, 1)) * 8, foot - np.cross(d, (0, 0, 1)) * 8,
                             foot + (0, 0, 6.0), foot + d * 5 + (0, 0, 3.0), foot + d * 11 + (0, 0, 1.2), foot - d * 7 + (0, 0, 1.2)]))   # spade foot
        m.add("dark", box(foot + d * 11.6 + (0, 0, 0.6), (2.0, 2.0, 1.2), rz=math.degrees(math.atan2(d[1], d[0])), bevel=0.3))

# ---------------------------------------------------------------- the mass driver: twin rails on a trunnion
PIV = np.array([0.0, 10.0, ztop + 7.0])
for s in (-1, 1):
    m.add("hull2", box((s * 9.5, 10, ztop + 3.5), (4, 18, 9), bevel=0.8))                                 # trunnion cheeks
m.add("dark", cyl((-11, 10, ztop + 7), (11, 10, ztop + 7), 3.4, 24))
Tr = M(PIV, rx=-ELEV)                                                                                     # front of the rail up
RF, RB = mm(8.6), mm(2.4)                                                                                 # rail ahead of / behind the pivot
for s in (-1, 1):
    m.add("dark", box((s * 3.6, (-RF + RB) / 2, 4.5), (2.8, RF + RB, 5.4), bevel=0.4), Tr)                 # rails
m.add("hull2", box((0, (-RF + RB) / 2 + 10, 0.4), (10, RF + RB - 30, 3.4), bevel=0.6), Tr)                 # spine beam
for j, y in enumerate(np.linspace(-RF + 6, RB - 26, 7)):                                                  # field-coil collars
    ring = []
    for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
        for yy in (y - 2.0, y + 2.0):
            ring.append((7.6 * math.cos(a), yy, 4.0 + 7.0 * math.sin(a)))
    m.add("hull" if j % 2 else "metal", hull(ring), Tr)
for s in (-1, 1):                                                                                         # open crown at the muzzle
    m.add("hull", box((s * 6.0, -RF + 1.5, 4.5), (2.0, 5, 13), bevel=0.4), Tr)
m.add("lens", box((0, -RF + 0.5, 11.2), (12, 2.5, 1.4), bevel=0.3), Tr)
m.add("lens", box((0, -RF + 0.5, -2.2), (12, 2.5, 1.4), bevel=0.3), Tr)
m.add("hull", box((0, RB - 9, 3.0), (17, 20, 15), bevel=1.6), Tr)                                          # breech / loader
spine_pack(m, (0, RB + 4.0, 2.5), 14, 6, 13, T=Tr)                                                        # capacitor bank
keel(m, [(0, RB - 18, 10.8), (0, RB - 4, 11.2), (0, RB + 3, 9.0)], 1.2, T=Tr)
for s in (-1, 1):
    m.add("metal", capsule((s * 7, 2, ztop + 1), tp(Tr, (s * 7, -26, -1.0)), 1.6))                       # elevation rams
chevron_mark(m, (8.75, RB - 9, 5), 8, rz=-90, T=Tr)
chevron_mark(m, (-8.75, RB - 9, 5), 8, rz=90, T=Tr)

m.add_ref((BW / 2 + 40, -BL / 2 - 34, 0), yaw=-25)

info = {
    "name": "Matins-class Mass-Driver Walker",
    "designation": "FS-4 Matins",
    "role": "Theatre-depth precision fire: an 11 m electromagnetic mass driver on a four-legged walker that braces into broken ground; strikes command posts, artillery and landing zones far beyond the Vigil front so the fireteams fight an enemy that has lost its support.",
    "drive": "walker (four bracing legs, spade feet)",
    "crew": 2,
    "capacity": "18 guided slugs in the breech magazine; reactor endurance 36 h",
    "weapons": [
        {"variant": "FS-4 (standard)", "main": "11 m twin-rail mass driver firing 40 kg guided 'Matin' slugs (direct lay to low-orbit intercept)"},
        {"variant": "FS-4S Lauds", "main": "6 m short rail with a rapid-fire 12 kg glide-shell loader (shorter, walks with the brigade)"},
        {"variant": "FS-4R Watchtower", "main": "rail replaced by a folding counter-battery radar mast and twin point-defence turrets (spotter for the battery)"},
    ],
}
finish(m, ROOT, "matins-mass-driver", "Matins-class Mass-Driver Walker  (FS-4)",
       "Four-legged walker with an 11 m twin-rail mass driver · crew 2 · long-range battery piece", info)
