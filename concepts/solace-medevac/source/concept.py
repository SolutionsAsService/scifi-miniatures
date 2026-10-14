"""Solace-class armoured medevac (AL-2): concept blockout at 1:56 (mm). Run with the sculpt venv:
    ~/ai-stack/venvs/sculpt/bin/python concepts/solace-medevac/source/concept.py
Frame: x = front, y = vehicle left, z up, ground z = 0. Light 4x4, cab forward, swappable rear mission pod.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_tools"))
import numpy as np  # noqa: E402

from transport_kit import annulus, box, chbox, cyl, figure_parts, hull, publish, roty, rotx, rotz, wheel  # noqa: E402

META = {
    "id": "solace-medevac",
    "name": "Solace-class armoured medevac",
    "designation": "AL-2",
    "role": "Light 4x4 armoured ambulance and utility runabout: follows the fireteam right up to the line, recovers a "
            "downed Vigilant (exosuit and all) into a protected litter pod, and runs them back to the aid post. The rear "
            "pod swaps for recon and utility fits.",
    "role_short": "Light 4x4 armoured medevac / utility",
    "drive": "wheeled 4x4 (independent suspension)",
    "crew": 2,
    "capacity": "2 armoured litters (suited casualties) + 1 medic, or 4 seated Vigilants in the utility pod",
    "weapons": [
        {"variant": "AL-2M Solace (medevac)", "main": "cab-roof light repeater on a ring mount", "secondary": "smoke dischargers; no offensive fit under the medevac marking"},
        {"variant": "AL-2R Outrider (recon)", "main": "open bed with telescopic sensor mast + twin Spindle anti-armour missiles", "secondary": "light repeater"},
        {"variant": "AL-2U Wick (utility)", "main": "cargo/ammo pod with crane arm; pintle heavy repeater", "secondary": "smoke"},
    ],
}

X0, X1 = -46.0, 46.0
WR, WW, WY = 8.6, 6.4, 17.6
AXLES = (27.5, -28.0)
ZB = 12.5            # hull belly


def build():
    P = []
    for x in AXLES:
        for s in (1, -1):
            P += wheel((x, s * WY, WR), WR, WW, side=s)
            # exposed double wishbones + damper
            for dz in (-2.0, 2.4):
                P.append((hull([(x - 3, s * 9, WR + dz), (x + 3, s * 9, WR + dz), (x, s * (WY - 2), WR + dz * 0.6),
                                (x - 3, s * 9, WR + dz + 0.9), (x + 3, s * 9, WR + dz + 0.9), (x, s * (WY - 2), WR + dz * 0.6 + 0.9)]), "metal"))
            P.append((cyl((x + 2.5, s * 12, WR + 2), (x + 1.5, s * 10, ZB + 9), 0.9, 8), "metal"))
            # flared armoured fenders
            P.append((hull([(x - 11, s * 14, ZB + 6), (x + 11, s * 14, ZB + 6), (x - 9, s * 21.4, ZB + 6.5), (x + 9, s * 21.4, ZB + 6.5),
                            (x - 10, s * 14, ZB + 8), (x + 10, s * 14, ZB + 8), (x - 8, s * 21.4, ZB + 7.6), (x + 8, s * 21.4, ZB + 7.6)]), "hull2"))
    # chassis tub (V belly)
    pts = []
    for x in (X0 + 2, X1 - 4):
        pts += [(x, 0, ZB - 1.5), (x, 10, ZB + 1), (x, -10, ZB + 1), (x, 14, ZB + 6), (x, -14, ZB + 6)]
    P.append((hull(pts), "hull2"))
    # bonnet: low wedge with the keel crest running up to the windscreen pillar
    P.append((hull([(X1, s * 13.5, ZB + 3) for s in (1, -1)] + [(X1, s * 12.5, ZB + 10) for s in (1, -1)] +
                   [(28, s * 15, ZB + 3) for s in (1, -1)] + [(28, s * 15, ZB + 14) for s in (1, -1)]), "hull"))
    # cab: armoured box, split-chevron windscreen (two panes in a V around a forward keel pillar)
    cab = [(28, s * 15.5, ZB + 3) for s in (1, -1)] + [(4, s * 16.5, ZB + 3) for s in (1, -1)]
    cab += [(4, s * 15.0, ZB + 25) for s in (1, -1)] + [(20, s * 13.5, ZB + 25) for s in (1, -1)] + [(26, 0, ZB + 25)]
    cab += [(31, 0, ZB + 14), (28, s * 15, ZB + 14)][0:1] + [(28, s * 15, ZB + 14) for s in (1, -1)]
    P.append((hull(cab), "hull"))
    for s in (1, -1):
        P.append((hull([(30.2, s * 0.9, ZB + 15), (25.6, s * 0.9, ZB + 24.2), (19.8, s * 12.8, ZB + 24.2),
                        (27.8, s * 14.6, ZB + 15), (29.4, s * 0.9, ZB + 15), (24.8, s * 0.9, ZB + 23.6),
                        (19.0, s * 12.2, ZB + 23.6), (27.0, s * 14.0, ZB + 15)]).apply_translation((0.5, 0, 0)), "glass"))
        P.append((hull([(16, s * 15.6, ZB + 17), (6, s * 15.4, ZB + 17), (6, s * 15.2, ZB + 22.5), (14, s * 14.6, ZB + 22.5),
                        (16, s * 16.2, ZB + 17), (6, s * 16.0, ZB + 17), (6, s * 15.8, ZB + 22.5), (14, s * 15.2, ZB + 22.5)]), "glass"))
        P.append((box((X1 + 0.1, s * 10.5, ZB + 7.5), (0.8, 4.0, 1.6)), "accent"))                   # headlamps
        P.append((chbox((18, s * 16.6, ZB + 9), (12, 1.0, 10), 0.3), "panel"))                         # cab door plate
        for j in range(3):
            P.append((cyl((8 - 2.4 * j, s * 14.0, ZB + 25), (8.6 - 2.4 * j, s * 16.6, ZB + 26.6), 0.75, 10), "metal"))
    P.append((hull([(X1 + 0.3, 0, ZB + 10.4), (31.4, 0, ZB + 14.8), (26.4, 0, ZB + 25.6), (20, 0, ZB + 25.8),
                    (X1 - 1, 1.2, ZB + 9.6), (X1 - 1, -1.2, ZB + 9.6), (30, 1.2, ZB + 14.4), (30, -1.2, ZB + 14.4),
                    (25.5, 1.2, ZB + 25.0), (25.5, -1.2, ZB + 25.0), (20, 1.2, ZB + 25.0), (20, -1.2, ZB + 25.0)]), "accent"))
    # front bull bar + winch
    P.append((cyl((X1 + 2.2, -12, ZB + 2), (X1 + 2.2, 12, ZB + 2), 1.0, 10), "metal"))
    for s in (1, -1):
        P.append((cyl((X1 - 1, s * 9, ZB + 2), (X1 + 2.2, s * 9, ZB + 2), 0.9, 10), "metal"))
    P.append((chbox((X1 + 0.4, 0, ZB + 3.0), (2.4, 7, 3.2), 0.4), "metal"))
    # roof ring mount + light repeater
    P.append((annulus((12, 0, ZB + 25.6), (0, 0, 1), 4.2, 5.6, 1.4, 28), "metal"))
    P.append((chbox((12, 0, ZB + 25.4), (9, 9, 0.8), 0.3), "hull2"))
    P.append((cyl((12, 0, ZB + 26.2), (13, 0, ZB + 29.6), 0.6, 8), "metal"))
    P.append((chbox((13.5, 0, ZB + 30.2), (5, 1.8, 2.0), 0.3), "metal"))
    P.append((cyl((15.5, 0, ZB + 30.4), (24, 0, ZB + 30.4), 0.6, 8), "metal"))
    # rear mission pod (medevac fit): armoured box with chamfered roof edges, litter door, markings, light bar
    pod = [(-44, s * 18.0, ZB + 5) for s in (1, -1)] + [(3, s * 18.0, ZB + 5) for s in (1, -1)]
    pod += [(-44, s * 18.0, ZB + 24) for s in (1, -1)] + [(3, s * 18.0, ZB + 24) for s in (1, -1)]
    pod += [(-43, s * 14.0, ZB + 28.5) for s in (1, -1)] + [(2, s * 14.0, ZB + 28.5) for s in (1, -1)]
    P.append((hull(pod), "hull"))
    for s in (1, -1):
        # plate rhythm: three pod-side plates; the middle one carries the Compact aid marking
        for i, x in enumerate((-35, -20.5, -6)):
            P.append((chbox((x, s * (18.3 + (0.5 if i == 1 else 0)), ZB + 15), (13.0, 1.2, 16), 0.4), "panel" if i != 1 else "hull2"))
        c = np.array([-20.5, s * 19.4, ZB + 15.5])
        P.append((annulus(c, (0, s, 0), 3.6, 5.2, 0.6, 32), "white"))       # aid marking: open ring with a lamp bar
        P.append((box(c, (1.6, 0.6, 7.6)), "white"))
        P.append((box((-44.3, s * 12, ZB + 21), (0.8, 2.6, 1.4)), "accent"))
    P.append((chbox((-44.4, 0, ZB + 15), (1.4, 22, 18), 0.5), "hull2"))                               # litter door
    P.append((box((-45.0, 0, ZB + 15.5), (0.6, 0.8, 16)), "dark"))
    P.append((chbox((-46.0, 0, ZB + 4.6), (4.0, 18, 1.0), 0.3), "metal"))                             # rear step
    for t in (1, -1):                                                                                  # light bar (chevron)
        P.append((box((-8 + t * 0.0, t * 3.2, ZB + 29.0), (2.0, 6.4, 1.2), rotz(t * 30)), "lens"))
    P.append((cyl((-38, 11, ZB + 28.5), (-38, 11, ZB + 36), 0.35, 6), "metal"))
    P.append((chbox((-30, -8, ZB + 29.0), (12, 7, 1.6), 0.4), "hull2"))
    return P


if __name__ == "__main__":
    publish(HERE, META, build(), figure_parts(pos=(X1 + 4, 40, 0), yaw=115), hero_kw={"az": 40, "el": 24})
