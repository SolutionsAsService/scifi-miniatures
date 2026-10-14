"""Vesper-class Self-Propelled Howitzer (FS-1): concept blockout at 1:56 (mm), with a Vigilant for scale.

Run:  ~/ai-stack/venvs/sculpt/bin/python concepts/vesper-sph/source/concept.py
Writes images/, blockout/ and concept.json next to this folder. Frame: mm, z up, faces -y, left side on +x.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "_tools"))
import numpy as np  # noqa: E402

from artillery_kit import (M, Model, box, capsule, chevron_mark, chevron_visor, cone, cyl, finish, hull, keel, mm,  # noqa: E402
                           prow, skirts, spine_pack, sphere, tp, track_unit)

ELEV = 12.0            # gun elevation for the display pose (deg)
m = Model("Vesper")

# ---------------------------------------------------------------- running gear (tracked, 6 road wheels a side)
HL, HW = mm(8.2) / 2, mm(3.5) / 2          # half hull length / half width over tracks
TW = mm(0.66)
TX = HW - TW / 2
for s in (-1, 1):
    track_unit(m, s * TX, -HL + 6, HL - 5, r_drive=mm(0.36), r_idle=mm(0.34), z_ground=0, width=TW, wheels=6, r_wheel=mm(0.37))

# ---------------------------------------------------------------- hull
z_belly, z_spon, z_deck = mm(0.45), mm(1.1), mm(1.95)
xi = TX - TW / 2 - 0.4
m.add("hull", hull([(sx * xi, y, z) for sx in (-1, 1) for (y, z) in
                    ((-HL + 14, z_belly), (HL - 4, z_belly), (HL, z_deck - 2), (-HL + 2, z_spon + 2), (-HL + 22, z_deck), (HL, z_deck))]))
m.add("hull", box((0, 12, (z_spon + z_deck) / 2), (2 * HW, 2 * HL - 24, z_deck - z_spon), bevel=1.2))      # sponsons
m.add("hull", prow(-HL - 2, -HL + 32, HW, z_spon, z_deck, nose_w=mm(0.5), nose_top=0.62, nose_lo=0.1))     # V glacis
keel(m, [(0, -HL - 0.5, z_spon + 0.62 * (z_deck - z_spon) + 0.3), (0, -HL + 32, z_deck + 0.6), (0, -HL + 44, z_deck + 0.6)], 1.3)
m.add("hull2", prow(-HL + 9, -HL + 24, 12, z_deck - 3, z_deck + 4.5, nose_w=2.5, nose_top=0.8, nose_lo=0.0))   # driver's hood
chevron_visor(m, (0, -HL + 12.4, z_deck + 2.2), width=15, height=2.6, depth=1.4, angle=20, rx=-12)       # driver's chevron
for s in (-1, 1):
    chevron_mark(m, (s * (HW + 1.7), -HL + 30, z_deck - 5.5), 13, rz=-s * 90)                             # skirt chevrons
for s in (-1, 1):
    skirts(m, s * HW, -HL + 18, HL - 6, z_deck - 0.5, mm(0.62), n=3, t=1.1)
    m.add("dark", cyl((s * (HW - 4), -HL + 2, z_spon + 3.5), (s * (HW - 4), -HL - 1.5, z_spon + 3.5), 2.0, 16))  # tow eyes / lamps
# folded rear bracing spade (lowered when firing at max charge)
m.add("hull2", box((0, HL + 1.6, z_belly + 7), (2 * xi - 6, 2.2, 13), bevel=0.8))
for s in (-1, 1):
    m.add("dark", cyl((s * (xi - 5), HL, z_belly + 12), (s * (xi - 5), HL + 3.2, z_belly + 12), 1.4, 16))

# ---------------------------------------------------------------- turret (rear-set, chevron-fronted), local frame
TY0 = 16.0
Tt = M((0, TY0, z_deck))
TL, TWt, TH = mm(4.7), mm(3.05), mm(1.25)
tf, tb = -TL * 0.45, TL * 0.55
pts = []
for sx in (-1, 1):
    pts += [(sx * TWt / 2, tb, 0), (sx * TWt / 2 * 0.9, tb, TH), (sx * TWt / 2, tf + 14, 0), (sx * TWt / 2 * 0.86, tf + 16, TH),
            (sx * 7, tf, 2), (sx * 6, tf + 3, TH - 1)]
m.add("hull", hull(pts), Tt)
m.add("hull2", box((0, tb + 2.5, TH * 0.48), (TWt * 0.8, 5, TH * 0.8), bevel=1.0), Tt)                    # bustle
keel(m, [(0, tf + 4, TH + 0.2), (0, tf + 30, TH + 1.3), (0, tb - 6, TH + 1.3), (0, tb + 4, TH * 0.75)], 1.2, T=Tt)
spine_pack(m, (0, tb + 7.2, TH * 0.5), 20, 5, 15, T=Tt)                                                   # autoloader cell
for s in (-1, 1):                                                                                          # ear-pod sensors
    m.add("hull2", cyl((s * (TWt / 2 - 1), tf + 22, TH * 0.6), (s * (TWt / 2 + 2.6), tf + 22, TH * 0.6), 3.4, 20), Tt)
    m.add("lens", cyl((s * (TWt / 2 + 2.4), tf + 22, TH * 0.6), (s * (TWt / 2 + 3.0), tf + 22, TH * 0.6), 2.0, 20), Tt)
    keel(m, [(s * (TWt / 2 + 1.2), tf + 24, TH * 0.75), (s * (TWt / 2 + 0.9), tf + 33, TH * 0.9), (s * (TWt / 2 + 0.2), tf + 42, TH + 0.4)], 0.9, T=Tt)
    chevron_mark(m, (s * (TWt / 2 * 0.95 + 0.2), tf + 52, TH * 0.45), 16, rz=-s * 90, T=Tt)
# commander's cupola with a pintle Lance-pattern heavy rifle (VW family), left rear
cx, cyy = TWt / 2 - 11, tb - 20
m.add("hull2", cyl((cx, cyy, TH - 0.5), (cx, cyy, TH + 3.2), 5.2, 24), Tt)
m.add("lens", hull([(cx + 5.2 * math.cos(a), cyy + 5.2 * math.sin(a), TH + 2.0) for a in np.linspace(math.pi * 1.1, math.pi * 1.9, 8)] +
                   [(cx + 4.4 * math.cos(a), cyy + 4.4 * math.sin(a), TH + 3.0) for a in np.linspace(math.pi * 1.1, math.pi * 1.9, 8)]), Tt)
m.add("dark", box((cx, cyy - 4, TH + 5.3), (2.4, 9, 2.6), bevel=0.5), Tt)
m.add("dark", cyl((cx, cyy - 8, TH + 5.6), (cx, cyy - 15, TH + 5.6), 0.8, 12), Tt)
m.add("dark", capsule((cx, cyy - 1, TH + 3.0), (cx, cyy - 2, TH + 4.5), 0.8), Tt)
m.add("hull2", box((-TWt / 2 + 12, tb - 22, TH + 0.6), (9, 10, 1.4), bevel=0.4), Tt)                     # loader hatch

# ---------------------------------------------------------------- gun: coil-assisted 155 mm-class howitzer
piv = np.array([0, tf + 4, TH * 0.55])
Tg = Tt @ M(piv, rx=ELEV)
m.add("hull2", box((0, -2, 0), (15, 9, 13), bevel=2.0), Tg)                                               # mantlet
blen = mm(7.4)
m.add("dark", cone((0, -4, 0), (0, -blen, 0), 3.9, 3.1, 24), Tg)
for j, y in enumerate(np.linspace(-14, -blen + 26, 5)):                                                     # coil bands
    m.add("metal", cyl((0, y, 0), (0, y - 3.2, 0), 4.7 - j * 0.12, 24), Tg)
m.add("dark", box((0, -blen - 2.5, 0), (8.5, 7, 6.5), bevel=1.2), Tg)                                       # muzzle brake
for s in (-1, 1):
    m.add("lens", box((s * 4.3, -blen - 2.5, 0), (0.6, 4.5, 3.4)), Tg)                                     # brake ports
m.add("hull2", box((0, -9, 6.0), (4.5, 10, 2.4), bevel=0.6), Tg)                                            # recuperator / sight

# ---------------------------------------------------------------- scale
m.add_ref((HW + 14, -HL - 18, 0), yaw=-20)

info = {
    "name": "Vesper-class Self-Propelled Howitzer",
    "designation": "FS-1 Vesper",
    "role": "Tracked indirect-fire artillery: on-call fire missions, smoke and illumination for Vigil fireteams up to 40 km behind the line.",
    "drive": "tracked (6 road wheels a side)",
    "crew": 3,
    "capacity": "40 ready rounds in the bustle autoloader; no passengers",
    "weapons": [
        {"variant": "FS-1 (standard)", "main": "155 mm-class coil-assisted howitzer, 7.4 m tube", "secondary": "pintle Lance-pattern heavy rifle on the commander's cupola"},
        {"variant": "FS-1L Long Vesper", "main": "extended 52-calibre tube with a fourth coil band, ER rocket-assist shells"},
        {"variant": "FS-1B Bell", "main": "short 210 mm siege mortar-howitzer for bunker and urban work"},
    ],
}
finish(m, ROOT, "vesper-sph", "Vesper-class Self-Propelled Howitzer  (FS-1)",
       "Tracked 155 mm-class coil-assisted howitzer · crew 3 · Aster Compact fire support", info)
