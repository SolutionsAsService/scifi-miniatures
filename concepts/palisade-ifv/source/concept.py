"""Palisade-class IFV (AV-3): concept blockout at 1:56 (mm). Run with the sculpt venv:
    ~/ai-stack/venvs/sculpt/bin/python concepts/palisade-ifv/source/concept.py
Frame: x = front, y = vehicle left, z up, ground z = 0. Writes images/, blockout/ and concept.json.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_tools"))
import numpy as np  # noqa: E402

from transport_kit import (bev_prism_x, bev_prism_y, box, chbox, cyl, figure_parts, hull, publish, roty,  # noqa: E402
                           rotz, track_unit)

META = {
    "id": "palisade-ifv",
    "name": "Palisade-class IFV",
    "designation": "AV-3",
    "role": "Tracked infantry fighting vehicle: carries a Vigil fireteam into contact and stays to fight beside it "
            "with a stabilised autocannon.",
    "role_short": "Tracked infantry fighting vehicle",
    "drive": "tracked",
    "crew": 3,
    "capacity": "6 Vigilants in full exosuit (seated, packs racked)",
    "weapons": [
        {"variant": "AV-3A (standard)", "main": "30 mm Rook autocannon, dual feed", "secondary": "coaxial Lance-pattern repeater; 2x3 smoke/chaff dischargers"},
        {"variant": "AV-3B Spindle", "main": "30 mm Rook + twin Spindle anti-armour missile pod on the turret left", "secondary": "coaxial repeater"},
        {"variant": "AV-3W Ward", "main": "turretless; roof remote weapon station (heavy repeater)", "secondary": "+2 seats (8 Vigilants), command fit"},
    ],
}

L, W = 132.0, 62.0                  # hull length / width over skirts (mm at 1:56)
X0, X1 = -L / 2, L / 2


def build():
    P = []
    # running gear: tracks either side, road wheels show below the skirts
    for side in (1, -1):
        parts, _ = track_unit(X0 + 3, X1 - 6, side * 23.5, 13.0, r_drive=6.2, r_road=4.4, n_road=6, side=side,
                              lift_front=4.5, lift_rear=3.0)
        P += parts
    # lower hull between the tracks
    P.append((bev_prism_y([(X0 + 2, 9), (X1 - 10, 9), (X1 - 2, 16), (X1 - 2, 20), (X0 + 2, 20)], 33, 1.5), "hull2"))
    # upper hull over the tracks: long glacis that rises to the roof
    prof = [(X0, 18.5), (X1 - 2, 18.5), (X1, 21.5), (X1 - 26, 33.0), (X0 + 4, 34.0), (X0, 29.0)]
    P.append((bev_prism_y(prof, W - 2, 2.2), "hull"))
    # keel crest: raised centre spine up the glacis and along the roof (the helm crest, scaled up)
    P.append((hull([(X1 - 1, 0, 21.8), (X1 - 26, 0, 34.6), (X1 - 40, 0, 35.2), (X1 - 40, 0, 33.5),
                    (X1 - 4, 1.6, 21.0), (X1 - 4, -1.6, 21.0), (X1 - 26, 1.8, 33.0), (X1 - 26, -1.8, 33.0),
                    (X1 - 40, 1.8, 33.6), (X1 - 40, -1.8, 33.6)]), "accent"))
    # troop-bay periscopes: small chevron vision blocks along both upper side walls
    for s in (1, -1):
        for x in (X0 + 16, X0 + 30, X0 + 44):
            for t in (1, -1):
                P.append((box((x + t * 1.3, s * (W / 2 - 0.6), 27.5 + 0.0), (2.4, 1.0, 1.0), roty(t * 35)), "lens"))
            P.append((chbox((x, s * (W / 2 - 1.0), 27.4), (6.0, 1.2, 3.4), 0.4), "hull2"))
    # glacis plate rhythm: two raised plates either side of the keel
    for s in (1, -1):
        P.append((hull([(X1 - 3, s * 4.0, 21.6), (X1 - 3, s * 25.5, 21.6), (X1 - 22, s * 4.0, 31.2),
                        (X1 - 22, s * 25.5, 31.2), (X1 - 3, s * 4.0, 20.4), (X1 - 22, s * 4.0, 30.0),
                        (X1 - 3, s * 25.5, 20.4), (X1 - 22, s * 25.5, 30.0)]).apply_translation((0.6, 0, 0.7)), "panel"))
        # driver / co-driver chevron vision blocks either side of the keel (split V)
        P.append((box((X1 - 24.5, s * 4.6, 32.6), (2.2, 3.6, 1.2), rotz(-s * 25) @ roty(-24)), "lens"))
        # skirts: five plates with gaps, alternating stand-off (the exosuit's armour plate rhythm)
        n = 5
        xs = np.linspace(X0 + 4, X1 - 14, n + 1)
        for i in range(n):
            off = 0.0 if i % 2 == 0 else 0.6
            P.append((chbox(((xs[i] + xs[i + 1]) / 2, s * (W / 2 + off - 0.4), 15.5),
                            (xs[i + 1] - xs[i] - 1.0, 2.0, 8.6), 0.5), "panel" if i % 2 == 0 else "hull"))
        P.append((hull([(X1 - 14, s * (W / 2 - 1.4), 11.2), (X1 - 14, s * (W / 2 - 1.4), 19.8), (X1 - 4, s * (W / 2 - 1.4), 19.8),
                        (X1 - 14, s * (W / 2 + 0.6), 11.2), (X1 - 14, s * (W / 2 + 0.6), 19.8), (X1 - 4, s * (W / 2 + 0.6), 19.8)]), "hull"))
        # stowage bins on the rear deck sides
        P.append((chbox((X0 + 12, s * 24.5, 35.0), (16, 8, 3.0), 0.6), "hull2"))
        # rear lights
        P.append((box((X0 - 0.2, s * 24, 26), (0.8, 3.0, 1.6)), "accent"))
    # rear ramp (tall door outline proud of the rear plate)
    P.append((chbox((X0 - 0.4, 0, 23.0), (1.6, 26, 18), 0.6), "hull2"))
    P.append((box((X0 - 1.0, 0, 25), (0.6, 4, 8)), "metal"))
    # roof hatches for the troop bay
    for x in (X0 + 22, X0 + 34):
        P.append((chbox((x, 0, 34.4), (9, 14, 1.4), 0.5), "hull2"))
    # exhaust grille
    P.append((chbox((X0 + 6, -16, 31.8), (6, 10, 1.2), 0.4), "dark"))
    # turret
    tx = -6.0
    tprof = [(-15.5, -16.5), (15.5, -16.5), (17.5, -12), (17.5, 12), (15.5, 16.5), (-15.5, 16.5), (-17.5, 12), (-17.5, -12)]
    T = bev_prism_x([(y, z) for y, z in [(-17, 34), (17, 34), (14, 44.5), (-14, 44.5)]], tx - 18, tx + 13, 1.6)
    P.append((T, "hull"))
    # turret nose: chevron prow (keel continues), mantlet
    P.append((hull([(tx + 13, -14.5, 34.2), (tx + 13, 14.5, 34.2), (tx + 13, -12, 44.0), (tx + 13, 12, 44.0),
                    (tx + 20, 0, 36.5), (tx + 20, 0, 41.0)]), "hull"))
    P.append((hull([(tx + 20.2, 0, 36.2), (tx + 20.2, 0, 41.4), (tx + 12, 0, 45.4), (tx + 12, 0, 34.5),
                    (tx + 13, 1.0, 44.5), (tx + 13, -1.0, 44.5), (tx + 13, 1.0, 35), (tx + 13, -1.0, 35)]), "accent"))
    for s in (1, -1):
        P.append((box((tx + 16.4, s * 4.2, 42.2), (1.6, 4.4, 1.3), rotz(s * 36) @ roty(-12)), "lens"))   # gunner chevron sight
        for j in range(3):                                                                                   # smoke dischargers
            P.append((cyl((tx - 2 + j * 3.0, s * 15.8, 41.5), (tx - 2 + j * 3.0 + 1.0, s * 18.5, 43.0), 0.9, 10), "metal"))
    P.append((chbox((tx + 20.5, 4.5, 38.8), (3.0, 7.0, 5.0), 0.6), "metal"))       # mantlet (offset right of keel)
    P.append((cyl((tx + 21, 4.5, 39.0), (tx + 52, 4.5, 39.0), 1.25, 16), "metal"))  # 30 mm Rook barrel
    P.append((cyl((tx + 47, 4.5, 39.0), (tx + 53, 4.5, 39.0), 1.75, 16), "metal"))  # muzzle brake
    P.append((cyl((tx + 21, -4.2, 38.3), (tx + 29, -4.2, 38.3), 0.7, 10), "metal")) # coax
    # commander's sight and turret bustle
    P.append((cyl((tx - 9, -7, 44.4), (tx - 9, -7, 47.6), 2.6, 20), "hull2"))
    P.append((box((tx - 7.2, -7, 46.8), (1.4, 3.4, 1.2)), "lens"))
    P.append((chbox((tx - 20.5, 0, 39.5), (6, 26, 8), 1.0), "hull2"))
    P.append((cyl((tx - 12, 8, 44.4), (tx - 12, 8, 56), 0.35, 6), "metal"))       # antenna
    return P


if __name__ == "__main__":
    veh = build()
    fig = figure_parts(pos=(X1 + 6, 50, 0), yaw=115)
    publish(HERE, META, veh, fig, hero_kw={"az": 40, "el": 24})
