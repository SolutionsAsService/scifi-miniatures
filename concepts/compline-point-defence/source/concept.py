"""Compline-class Point-Defence Skimmer (FS-5): grav-lifted air- and missile-defence vehicle.
Concept blockout at 1:56 (mm) on its flight stand, with a Vigilant for scale.

Run:  ~/ai-stack/venvs/sculpt/bin/python concepts/compline-point-defence/source/concept.py
Frame: mm, z up, faces -y, left side on +x.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "_tools"))
import numpy as np  # noqa: E402

from artillery_kit import (M, Model, box, capsule, chevron_mark, chevron_visor, cyl, ellipsoid, finish, hull, keel, mm,  # noqa: E402
                           spine_pack, tp)

m = Model("Compline")
ZH = mm(0.75)                                   # hover gap: hull belly above the ground
ZM = ZH + 7.0                                   # hull waist

# ---------------------------------------------------------------- flight stand: 60 mm round base + post
t = np.linspace(0, 2 * math.pi, 64, endpoint=False)
m.add("base", hull(np.vstack([np.c_[30 * np.cos(t), 30 * np.sin(t), np.zeros_like(t)],
                              np.c_[28.8 * np.cos(t), 28.8 * np.sin(t), np.full_like(t, 4.0)]])))
m.add("metal", cyl((0, 6, 4.0), (0, 6, ZH + 1.0), 2.6, 20))

# ---------------------------------------------------------------- lenticular hull with a chevron prow
plan = [(0, -mm(3.5)), (26, -42), (37, -8), (36, 34), (22, 54), (0, 55)]
plan = plan + [(-x, y) for x, y in plan[1:-1]]
def ring(k, z, dy=0.0):
    return [(x * k, y * k + dy, z) for x, y in plan]
m.add("hull", hull(ring(0.62, ZH) + ring(1.0, ZM) + ring(0.93, ZM + 2.5) + ring(0.66, ZM + 8.0, 3.0)))
keel(m, [(0, -mm(3.5) + 1.5, ZM + 1.2), (0, -38.5, ZM + 8.6), (0, -24, ZM + 8.9)], 1.4)
chevron_visor(m, (0, -47.5, ZM + 5.1), width=17, height=3.4, depth=1.8, angle=24, rx=-72)                 # driver's split visor
for s in (-1, 1):
    for i, (y0, y1) in enumerate(((-30, -2), (-4, 24), (22, 46))):                                         # skirt plates in threes
        yc = (y0 + y1) / 2
        xe = 37 - (0 if yc < 30 else (yc - 30) * 0.6)
        m.add("hull2", box((s * (xe + 0.6 + i * 0.35), yc, ZM - 0.3), (1.4, y1 - y0, 5.2), rz=s * (-3 + i * 6), bevel=0.4))
    chevron_mark(m, (s * 38.5, -16, ZM + 2.6), 8, rz=-s * 90)

# grav nacelles on stub pylons
for sx in (-1, 1):
    for sy, yc in ((-1, -26), (1, 34)):
        c = np.array([sx * 42.0, yc, ZM - 1.0])
        m.add("hull2", box(((sx * 36), yc, ZM - 0.5), (10, 8, 4), bevel=0.8))
        m.add("hull", ellipsoid(c, (7.5, 12.5, 5.2)))
        m.add("lens", cyl(c + (0, 0, -4.2), c + (0, 0, -5.3), 5.6, 24))                                     # emitter discs
        m.add("hull2", capsule(c + (0, -10, 3.2), c + (0, 9, 3.4), 1.1))                                   # nacelle keel

# ---------------------------------------------------------------- turret: sensor dome flanked by twin rotary cannons
TC = np.array([0.0, -10.0, ZM + 8.0])
m.add("hull2", cyl(TC, TC + (0, 0, 3.0), 15.5, 36))
Tt = M(TC + (0, 0, 3.0), rz=0)
m.add("hull", ellipsoid((0, 0, 4.0), (9.5, 10.5, 8.5)), Tt)                                                  # sensor dome
for s in (-1, 1):
    m.add("lens", box((s * 3.9, -9.2, 6.0), (6.2, 2.6, 2.4), ry=s * 24, bevel=0.3), Tt)                   # split chevron sensor
keel(m, [(0, -9.6, 9.0), (0, -3.0, 12.6), (0, 5.0, 12.4), (0, 10.5, 7.5)], 1.2, T=Tt)
ELEV = 38.0
for s in (-1, 1):
    Tg = Tt @ M((s * 14.5, 0, 5.5), rx=-ELEV)                                                               # muzzles up and forward
    m.add("hull", box((0, 2, 0), (8.5, 16, 8.5), bevel=1.6), Tg)                                            # gun housing
    m.add("dark", cyl((0, -6, 0), (0, -9.5, 0), 3.6, 20), Tg)
    for a in np.linspace(0, 2 * math.pi, 6, endpoint=False):                                               # 6-barrel rotary
        o = (1.9 * math.cos(a), 0, 1.9 * math.sin(a))
        m.add("dark", cyl(np.add((0, -9, 0), o), np.add((0, -27, 0), o), 0.75, 10), Tg)
    m.add("metal", cyl((0, -20, 0), (0, -22, 0), 3.4, 20), Tg)
    m.add("hull2", cyl((-s * 4.5, 0, 0), (-s * 1.5, 0, 0), 4.6, 20), Tg)                                    # trunnion
    m.add("hull2", box((s * 4.2, 5, 1.2), (2.4, 9, 6), bevel=0.6), Tg)                                      # ammo feed

# ---------------------------------------------------------------- rear: tilting phased-array plate + interceptor cells
mast = np.array([0.0, 30.0, ZM + 8.0])
m.add("hull2", cyl(mast, mast + (0, 0, 8.0), 3.0, 18))
Tp = M(mast + (0, 0, 15.0), rx=22)                                                                           # array faces forward-up
m.add("hull", box((0, 0, 0), (30, 2.4, 17), bevel=0.8), Tp)
m.add("lens", box((0, -1.6, 0), (26, 1.0, 13.5), bevel=0.2), Tp)
keel(m, [(-12, 0.4, 8.9), (0, 0.4, 9.8), (12, 0.4, 8.9)], 0.9, T=Tp)
for s in (-1, 1):                                                                                            # VLS: 2 x 4 cells a side
    m.add("hull2", box((s * 16, 33, ZM + 8.6), (12, 20, 2.4), bevel=0.5))
    for i in range(2):
        for j in range(4):
            m.add("dark", box((s * 16 + (i - 0.5) * 5.4, 26 + j * 4.6, ZM + 9.9), (4.2, 3.6, 0.6)))
spine_pack(m, (0, 52.5, ZM + 3.0), 20, 5, 8)

m.add_ref((52, -48, 0), yaw=-25)

info = {
    "name": "Compline-class Point-Defence Skimmer",
    "designation": "FS-5 Compline",
    "role": "Grav-lifted air and missile defence: rides with the Vigil fireteams and the artillery park, swatting drones, rockets, shells and gunships out of the sky with twin rotary cannons and a 16-cell interceptor battery cued by a tilting phased array.",
    "drive": "grav skimmer (four repulsor nacelles, hovers 0.75 m)",
    "crew": 2,
    "capacity": "16 interceptors in vertical cells, 2 x 1 800 cannon rounds",
    "base": "60 mm round flight base with a 5 mm post (magnetised top joint)",
    "weapons": [
        {"variant": "FS-5 (standard)", "main": "twin 6-barrel 30 mm 'Lattice' rotary flak cannons", "secondary": "16-cell 'Psalter' short-range interceptor VLS"},
        {"variant": "FS-5L Lamplight", "main": "single pulsed laser projector in the dome (cannon pods replaced by radiator fins)"},
        {"variant": "FS-5P Psalter", "main": "cannons replaced by two 8-round box launchers for medium-range interceptors; VLS kept"},
    ],
}
finish(m, ROOT, "compline-point-defence", "Compline-class Point-Defence Skimmer  (FS-5)",
       "Grav air / missile defence · twin rotary flak cannons + 16 interceptor cells · crew 2", info)
