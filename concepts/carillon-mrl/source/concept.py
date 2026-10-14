"""Carillon-class Rocket Artillery Carrier (FS-2): concept blockout at 1:56 (mm), with a Vigilant for scale.

Run:  ~/ai-stack/venvs/sculpt/bin/python concepts/carillon-mrl/source/concept.py
Writes images/, blockout/ and concept.json next to this folder. Frame: mm, z up, faces -y, left side on +x.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "_tools"))
import numpy as np  # noqa: E402

from artillery_kit import (M, Model, box, capsule, chevron_mark, chevron_visor, cyl, finish, hull, keel, mm,  # noqa: E402
                           skirts, spine_pack, tp, wheel)

ELEV, TRAV = 32.0, 0.0
m = Model("Carillon")

HL, HW = mm(9.6) / 2, mm(2.9) / 2
WR, WW = mm(0.62), mm(0.52)
WX = HW - WW / 2
AXLES = (-HL + 24, -HL + 45, HL - 50, HL - 28)
for y in AXLES:
    for s in (-1, 1):
        wheel(m, (s * WX, y, WR), WR, WW, s)

# ---------------------------------------------------------------- chassis + armoured cab-forward
zc0, zc1, zdeck = mm(0.6), mm(1.3), mm(1.55)
m.add("hull2", box((0, 6, (zc0 + zc1) / 2), (2 * (WX - WW / 2) - 1, 2 * HL - 14, zc1 - zc0), bevel=1.0))
cab_back, cab_top = -HL + 52, mm(2.95)
pts = []
for sx in (-1, 1):
    pts += [(sx * HW, cab_back, zc0 + 6), (sx * HW, cab_back, cab_top), (sx * HW * 0.92, -HL + 16, cab_top - 1),
            (sx * HW, -HL + 8, zc0 + 6), (sx * 9, -HL, zc0 + 9), (sx * 8, -HL + 2, zc1 + 12)]
m.add("hull", hull(pts))
keel(m, [(0, -HL + 1, zc0 + 9), (0, -HL + 3.5, zc1 + 12), (0, -HL + 16, cab_top + 0.6), (0, cab_back - 2, cab_top + 0.6)], 1.3)
for s in (-1, 1):                                                                                            # split windscreen
    m.add("lens", box((s * 6.2, -HL + 8.6, zc1 + 19.2), (11.5, 3.2, 4.6), rz=-s * 24, rx=-40, ry=s * 18, bevel=0.4))
for s in (-1, 1):
    m.add("lens", box((s * (HW + 0.2), -HL + 24, zc1 + 18), (0.8, 10, 4), bevel=0.2))                     # side vision
    m.add("hull2", box((s * (HW - 4), -HL + 4, zc0 + 2.5), (8, 6, 4), bevel=0.6))                          # bumper horns
    chevron_mark(m, (s * (HW + 0.6), -HL + 37, zc1 + 9), 14, rz=-s * 90)
m.add("hull2", cyl((-8, cab_back - 12, cab_top), (-8, cab_back - 12, cab_top + 3), 5, 22))                  # RWS ring
m.add("dark", box((-8, cab_back - 15, cab_top + 5), (3, 10, 3), bevel=0.5))
m.add("dark", cyl((-8, cab_back - 20, cab_top + 5.4), (-8, cab_back - 27, cab_top + 5.4), 0.8, 12))
m.add("lens", box((-8, cab_back - 9, cab_top + 5), (4, 1.2, 2.4), bevel=0.3))
for s in (-1, 1):
    m.add("hull2", cyl((s * 9, cab_back - 6, cab_top), (s * 9, cab_back - 6, cab_top + 6), 0.8, 10))       # whip bases
m.add("hull2", capsule((9, cab_back - 6, cab_top + 6), (10, cab_back - 2, cab_top + 26), 0.45))

# rear deck, fenders and side lockers (plate rhythm in threes)
m.add("hull", box((0, (cab_back + HL) / 2 + 1, (zc1 + zdeck) / 2), (2 * HW - 2, HL - cab_back - 1, zdeck - zc1 + 1), bevel=0.8))
for s in (-1, 1):
    skirts(m, s * (HW - 1.1), cab_back + 2, HL - 2, zdeck + 1, 7, n=3, t=1.1)
    for y in AXLES[2:]:
        m.add("hull2", box((s * WX, y, WR * 2 + 1.5), (WW + 2, WR * 2 + 5, 1.2), bevel=0.4))               # mudguards
    m.add("hull2", box((s * (HW - 4.5), cab_back + 14, zdeck + 4), (7, 14, 8), bevel=0.8))                 # reload crane boxes

# stabiliser jacks, deployed
for y in (cab_back + 6, HL - 6):
    for s in (-1, 1):
        x = s * (HW + 2.5)
        m.add("hull2", box((s * (HW + 0.6), y, zc1), (4.5, 5, 4), bevel=0.5))
        m.add("metal", cyl((x, y, zc1), (x, y, 1.6), 1.3, 14))
        m.add("dark", cyl((x, y, 1.6), (x, y, 0), 3.2, 18))

# ---------------------------------------------------------------- launcher: turntable, cradle, twin pods
TY = HL - 30
m.add("hull2", cyl((0, TY, zdeck), (0, TY, zdeck + 3.5), 17, 32))
Tl = M((0, TY, zdeck + 3.5), rz=TRAV)
for s in (-1, 1):
    m.add("hull2", box((s * 12, 4, 6), (4, 14, 12), bevel=0.8), Tl)                                        # cradle cheeks
PIV = (0, 12, 10)
Te = Tl @ M(PIV, rx=-ELEV)        # front of the pods up: cells fire forward over the cab
PL, PWd, PH = mm(4.7), mm(1.2), mm(1.45)
CELL = 3
for s in (-1, 1):
    px = s * (PWd / 2 + 1.2)
    m.add("hull", box((px, -PL / 2 + 4, PH / 2), (PWd, PL, PH), bevel=1.0), Te)
    for k in (0.22, 0.52, 0.8):                                                                           # pod frame ribs
        m.add("hull2", box((px, -PL * k + 4, PH / 2), (PWd + 1.2, 2.2, PH + 1.2), bevel=0.5), Te)
    for i in range(3):                                                                                     # 3 x 4 cells
        for j in range(4):
            cx = px + (i - 1) * PWd * 0.3
            cz = PH * (0.14 + 0.24 * j)
            m.add("dark", cyl((cx, -PL + 4.6, cz), (cx, -PL + 3.0, cz), CELL, 18), Te)
            m.add("accent", cyl((cx, -PL + 4.9, cz), (cx, -PL + 4.4, cz), CELL * 0.45, 12), Te)
keel(m, [(0, -PL + 6, PH + 0.5), (0, -PL * 0.5, PH + 1.8), (0, 2, PH + 1.2)], 1.6, T=Te)                    # central keel spine
spine_pack(m, (0, 7.5, PH * 0.5), 2 * PWd - 4, 6, PH * 0.85, T=Te)                                          # fire-control cell
for s in (-1, 1):
    m.add("metal", capsule(tp(Tl, (s * 8, -10, 2)), tp(Te, (s * 8, -PL * 0.42, 0.5)), 1.3))                 # elevation rams

m.add_ref((HW + 16, -HL - 14, 0), yaw=-20)

info = {
    "name": "Carillon-class Rocket Artillery Carrier",
    "designation": "FS-2 Carillon",
    "role": "Wheeled shoot-and-scoot rocket artillery: saturates an area or breaks up an assault ahead of Vigil fireteams, then relocates before counter-battery fire.",
    "drive": "wheeled 8x8 (two steering axles forward), deployable stabiliser jacks",
    "crew": 3,
    "capacity": "one launcher load (2 pods); reload by the integral crane from a tender",
    "weapons": [
        {"variant": "FS-2 (standard)", "main": "2 x 12-cell 140 mm 'Peal' guided rocket pods", "secondary": "cab remote weapon station (Lance-pattern heavy rifle)"},
        {"variant": "FS-2K Knell", "main": "2 x 2-cell long-range 'Knell' ballistic missile pods (same pod shells, 2 big cells)"},
        {"variant": "FS-2C Chime", "main": "2 x 24-cell 80 mm 'Chime' saturation / smoke / scatter-mine rockets"},
    ],
}
finish(m, ROOT, "carillon-mrl", "Carillon-class Rocket Artillery Carrier  (FS-2)",
       "Wheeled 8x8 rocket / missile launcher · 24 x 140 mm guided rockets · crew 3", info)
