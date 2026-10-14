"""Tocsin-pattern Heavy Mortar Team (FS-3): crew-served emplacement concept blockout at 1:56 (mm).

Three block-out Vigilant crew (loader, gunner, section leader) on a 100 x 70 mm oval base, with a Vigilant Rifleman
Mk II alongside for scale.
Run:  ~/ai-stack/venvs/sculpt/bin/python concepts/tocsin-mortar-team/source/concept.py
Frame: mm, z up, the team fires toward -y, left on +x.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "_tools"))
import numpy as np  # noqa: E402

from artillery_kit import (M, Model, box, capsule, chevron_mark, crew, cyl, finish, hull, keel, mm, sphere,  # noqa: E402
                           spine_pack)

m = Model("Tocsin")
ZB = 4.0                                     # top of the base
BA, BB = 50.0, 35.0                          # oval half axes (100 x 70 mm)

# ---------------------------------------------------------------- base: 100 x 70 mm oval, 4 mm
t = np.linspace(0, 2 * math.pi, 72, endpoint=False)
m.add("base", hull(np.vstack([np.c_[BA * np.cos(t), BB * np.sin(t), np.zeros_like(t)],
                              np.c_[(BA - 1.2) * np.cos(t), (BB - 1.2) * np.sin(t), np.full_like(t, ZB)]])))
for (x, y, r, h) in ((-34, -6, 4, 1.2), (30, 6, 3, 0.9), (-6, 22, 5, 0.8), (38, -14, 2.5, 1.0)):       # rubble / deck plates
    m.add("base", box((x, y, ZB + h / 2 - 0.2), (2 * r, 1.6 * r, h), rz=x * 3, bevel=0.3))

# ---------------------------------------------------------------- chevron ward wall: two arms of three stacked plates
apex = np.array([0.0, -30.0])
for s in (-1, 1):
    end = np.array([s * 43.0, -6.0])
    d = end - apex
    L = float(np.linalg.norm(d))
    ang = math.degrees(math.atan2(d[1], d[0]))
    for i in range(3):
        c = apex + d * (0.2 + 0.31 * i)
        h = mm(0.8) - i * 1.4
        m.add("hull", box((c[0], c[1], ZB + h / 2), (L * 0.36, 3.2, h), rz=ang, bevel=0.6))
        m.add("hull2", box((c[0], c[1], ZB + h + 0.4), (L * 0.33, 2.4, 1.2), rz=ang, bevel=0.4))       # capping strip
    chevron_mark(m, (apex[0] + d[0] * 0.2 - 1.8 * math.sin(math.radians(ang)) * s * 0 , apex[1] + d[1] * 0.2 - 1.75, ZB + 7.5), 6.5,
                 rz=ang if s > 0 else ang + 180)
m.add("hull2", cyl((0, -30.5, ZB), (0, -30.5, ZB + mm(1.3)), 2.6, 18))                                   # apex keel post
keel(m, [(0, -31, ZB + mm(1.3)), (0, -31.5, ZB + mm(1.3) + 3)], 1.1)
m.add("lens", sphere((0, -30.5, ZB + mm(1.3) + 1.2), 1.6, 1))

# ---------------------------------------------------------------- the mortar: 120 mm smoothbore on a chevron-ribbed baseplate
BP = np.array([0.0, -2.0, ZB])
ELEV = 60.0
m.add("hull2", cyl(BP, BP + (0, 0, 1.6), 8.0, 32))
for s in (-1, 1):
    m.add("hull", box((s * 3.2, BP[1] + 1.5, ZB + 2.0), (1.4, 10, 1.2), rz=s * 32, bevel=0.3))           # chevron ribs
m.add("dark", sphere(BP + (0, 0, 2.6), 2.6, 1))
tl = mm(1.5)
dirn = np.array([0, -math.cos(math.radians(ELEV)), math.sin(math.radians(ELEV))])
b0 = BP + (0, 0, 2.6)
muzzle = b0 + dirn * tl
m.add("dark", cyl(b0, muzzle, 2.0, 24))
m.add("metal", cyl(muzzle - dirn * 2.2, muzzle + dirn * 0.4, 2.6, 24))
mid = b0 + dirn * tl * 0.58
m.add("metal", cyl(mid - dirn * 1.6, mid + dirn * 1.6, 2.7, 24))                                          # bipod collar
for s in (-1, 1):
    foot = np.array([s * 8.0, -20.0, ZB])
    m.add("hull2", capsule(mid + (s * 1.5, -1.0, -2.0), foot + (0, 0, 1.0), 1.0))
    m.add("hull2", box(foot + (0, 0, 0.6), (3.0, 3.6, 1.2), bevel=0.3))
m.add("hull2", capsule((-8 + 1.2, -19.5, ZB + 6), (8 - 1.2, -19.5, ZB + 6), 0.7))                       # spreader
m.add("hull2", box(mid + (0, -2.6, -3.6), (5, 3, 3.2), bevel=0.5))                                        # elevation screw
sight = mid + (4.0, 0.5, 0.0)
m.add("hull", box(sight, (3.2, 3.6, 3.8), bevel=0.6))                                                    # sight unit
m.add("lens", box(sight + (1.2, 1.9, 0.6), (1.6, 0.8, 1.6), bevel=0.2))
m.add("metal", cyl(mid + (2.3, -2.5, -4.0), mid + (4.2, -2.5, -4.0), 1.9, 14))                          # traverse wheel

# ---------------------------------------------------------------- crew 1: loader, standing at the muzzle (faces +x)
LP = np.array([-11.5, -17.0, ZB])
# local frame of a crew member facing +x: local (x, y) -> world (-y, x)
loader = crew(m, LP, yaw=90, pelvis_z=15.6, lean=10, feet=((-3.0, 1.5), (3.2, -1.5)),
              hands=((-1.5, -9.0, 26.5), (1.6, -9.0, 26.5)), head_pitch=12)
r0, r1 = loader((0, -9.6, 27.8)), loader((0, -9.6, 22.0))                                              # round, nose down
m.add("hull2", capsule(r0, r1, 1.75))
m.add("accent", sphere(r1 + (0, 0, -0.6), 1.6, 1))

# ---------------------------------------------------------------- crew 2: gunner, kneeling at the sight (faces -x)
GP = np.array([15.5, -10.0, ZB])
crew(m, GP, yaw=-90, pelvis_z=10.6, lean=14,
     feet=((-2.8, 8.0, 0.3), (2.8, -5.5)), knees=((-2.8, 1.6, 1.9), (2.8, -6.8, 9.6)),
     hands=((-0.2, -8.8, 15.2), (2.6, -8.6, 13.6)), head_pitch=18)

# ---------------------------------------------------------------- crew 3: section leader (Warden helm), rangefinder up
SP = np.array([-27.0, 14.0, ZB])
crew(m, SP, yaw=-12, pelvis_z=15.8, lean=4, feet=((-3.2, 1.0), (3.0, -1.5)),
     hands=((-2.6, -5.2, 26.4), (2.6, -5.2, 26.4)), helm="warden")
Ts = M(SP, rz=-12)
m.add("dark", box((0, -5.6, 27.6), (6.0, 3.2, 2.4), bevel=0.6), Ts)                                       # rangefinder
m.add("lens", box((0, -7.3, 27.6), (4.6, 0.6, 1.4), bevel=0.2), Ts)

# ---------------------------------------------------------------- ammunition and the tocsin sensor mast
for i, (x, y, z) in enumerate(((-30, -8, 0), (-30, -8, 5.5), (-23, -12, 0))):
    m.add("hull2", box((x, y, ZB + z + 2.7), (10, 6.5, 5.4), rz=12, bevel=0.6))
    m.add("dark", box((x, y, ZB + z + 2.7), (10.6, 4, 1.2), rz=12, bevel=0.2))
chevron_mark(m, (-30.7, -11.4, ZB + 8.3), 4.5, rz=12)
for j in range(4):                                                                                        # ready rounds
    p = np.array([-17.0 + j * 2.6, -2.0 + j * 0.4, ZB])
    m.add("hull2", capsule(p + (0, 0, 1.6), p + (0, 0, 8.5), 1.4))
    m.add("accent", sphere(p + (0, 0, 9.2), 1.3, 1))
mast = np.array([30.0, 16.0, ZB])
for a in (0, 120, 240):
    f = mast + (6 * math.cos(math.radians(a)), 6 * math.sin(math.radians(a)), 0)
    m.add("hull2", capsule(f + (0, 0, 0.5), mast + (0, 0, 14), 0.75))
m.add("hull2", cyl(mast + (0, 0, 13), mast + (0, 0, 28), 0.9, 12))
m.add("hull", cyl(mast + (0, 0, 28), mast + (0, 0, 31), 4.2, 24))                                         # acoustic / radar puck
m.add("lens", cyl(mast + (0, 0, 28.8), mast + (0, 0, 30.2), 4.4, 24))
spine_pack(m, (34, 24, ZB + 4), 9, 5, 8, rz=180)                                                          # field power cell

m.add_ref((BA + 16, -6, 0), yaw=-15)

info = {
    "name": "Tocsin-pattern Heavy Mortar Team",
    "designation": "FS-3 Tocsin",
    "role": "Organic company-level indirect fire: three Vigilants bring a 120 mm mortar forward on foot, dig in behind a chevron ward wall and drop smoke, HE and illumination within 7 km of the fireteams they support.",
    "drive": "emplacement (man-portable, crew-served)",
    "crew": 3,
    "capacity": "3 crew figures: loader, gunner (kneeling at the sight), section leader with rangefinder (Warden helm); 12 ready rounds",
    "base": "100 x 70 mm oval, 4 mm, three 5 x 2 mm magnet pockets",
    "weapons": [
        {"variant": "FS-3 (standard)", "main": "120 mm smoothbore 'Tocsin' mortar on a chevron-ribbed baseplate"},
        {"variant": "FS-3G Tocsin Guided", "main": "4-canister launcher for 'Lark' loitering munitions on the same baseplate"},
        {"variant": "FS-3A Twin Toll", "main": "twin 81 mm auto-mortar on a tripod with a clip feed (loader swaps to a magazine pose)"},
    ],
}
finish(m, ROOT, "tocsin-mortar-team", "Tocsin-pattern Heavy Mortar Team  (FS-3)",
       "Crew-served 120 mm mortar emplacement · 3 crew · 100 x 70 mm oval base", info, hero_az=148, hero_el=24)
