"""Wayfarer-class APC (AW-8): concept blockout at 1:56 (mm). Run with the sculpt venv:
    ~/ai-stack/venvs/sculpt/bin/python concepts/wayfarer-apc/source/concept.py
Frame: x = front, y = vehicle left, z up, ground z = 0. Writes images/, blockout/ and concept.json.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_tools"))
import numpy as np  # noqa: E402

from transport_kit import box, chbox, cyl, figure_parts, hull, publish, roty, rotz, wheel  # noqa: E402

META = {
    "id": "wayfarer-apc",
    "name": "Wayfarer-class APC",
    "designation": "AW-8",
    "role": "Wheeled 8x8 amphibious armoured personnel carrier: moves a full Vigil section fast along colony roads, "
            "river crossings and causeways, drops them behind cover and pulls back to overwatch.",
    "role_short": "Wheeled 8x8 amphibious APC",
    "drive": "wheeled 8x8",
    "crew": 2,
    "capacity": "10 Vigilants in full exosuit (two inward-facing benches of five)",
    "weapons": [
        {"variant": "AW-8A (standard)", "main": "Tally remote weapon station: heavy repeater + 40 mm grenade launcher", "secondary": "2x4 smoke dischargers"},
        {"variant": "AW-8C Wren", "main": "low-profile two-seat turret, 25 mm Wren autocannon (troops reduced to 8)", "secondary": "coaxial repeater"},
        {"variant": "AW-8M Sling", "main": "twin-tube 120 mm breech-loaded mortar module in the troop bay (roof doors)", "secondary": "Tally RWS retained"},
    ],
}

X0, X1 = -73.0, 73.0
WR, WW, WY = 10.4, 7.6, 23.6          # wheel radius / width / track half-width
AXLES = (50.0, 29.0, -25.0, -46.0)


def build():
    P = []
    for x in AXLES:
        for s in (1, -1):
            P += wheel((x, s * WY, WR), WR, WW, side=s)
    # lower V belly (blast chevron in section) between the wheels
    pts = []
    for x in (X0 + 3, X1 - 16):
        pts += [(x, 0, 6.5), (x, 17.5, 14.5), (x, -17.5, 14.5), (x, 17.5, 22), (x, -17.5, 22)]
    pts += [(X1 - 1, 0, 17.5), (X1 - 1, 15, 20), (X1 - 1, -15, 20), (X1 - 1, 15, 24), (X1 - 1, -15, 24)]
    P.append((hull(pts), "hull2"))
    # upper hull: boat sides with tumblehome, long glacis, near-vertical stern
    sec = [(27.6, 21), (27.6, 30), (21.5, 38.5)]
    pts = []
    for x in (X0, X1 - 26):
        pts += [(x, s * y, z) for y, z in sec for s in (1, -1)]
    pts += [(X1, s * 23.5, z) for s in (1, -1) for z in (21.5, 25.5)]
    pts += [(X0 + 1.5, s * 21.0, 38.0) for s in (1, -1)]
    P.append((hull(pts), "hull"))
    # keel crest along the glacis to the driver's station; trim vane folded flat on the glacis
    P.append((hull([(X1 + 0.4, 0, 25.8), (X1 - 26, 0, 39.6), (X1 - 30, 0, 39.6), (X1 - 30, 0, 38.0),
                    (X1 - 1, 1.5, 25.0), (X1 - 1, -1.5, 25.0), (X1 - 28, 1.6, 38.0), (X1 - 28, -1.6, 38.0)]), "accent"))
    for s in (1, -1):
        P.append((hull([(X1 - 3, s * 3.0, 27.0), (X1 - 3, s * 22.5, 27.0), (X1 - 13, s * 3.0, 32.4),
                        (X1 - 13, s * 22.5, 32.4), (X1 - 3, s * 3.0, 25.8), (X1 - 13, s * 3.0, 31.2),
                        (X1 - 3, s * 22.5, 25.8), (X1 - 13, s * 22.5, 31.2)]), "panel"))
        # side applique plates: six-plate rhythm, alternating stand-off
        xs = np.linspace(X0 + 3, X1 - 14, 7)
        for i in range(6):
            off = 0.0 if i % 2 == 0 else 0.5
            P.append((chbox(((xs[i] + xs[i + 1]) / 2, s * (27.9 + off), 26.0), (xs[i + 1] - xs[i] - 1.2, 1.4, 7.4), 0.45),
                      "panel" if i % 2 == 0 else "hull"))
        # fender lips over each wheel pair
        for xa, xb in ((AXLES[1] - 12, AXLES[0] + 12), (AXLES[3] - 12, AXLES[2] + 12)):
            P.append((chbox(((xa + xb) / 2, s * 24.0, 21.4), (xb - xa, 9.0, 1.2), 0.4), "hull2"))
        # firing-port vision chevrons along the troop bay
        for x in (X0 + 14, X0 + 30, X0 + 46, X0 + 62):
            for t in (1, -1):
                P.append((box((x + t * 1.2, s * (26.3 - 0.0), 33.6), (2.2, 1.0, 1.0), rotz(s * 0) @ roty(t * 35)), "lens"))
        # waterjets at the stern
        P.append((cyl((X0 + 2, s * 15, 16.5), (X0 - 3.0, s * 15, 16.5), 3.2, 20), "metal"))
        # smoke dischargers on the roof edge
        for j in range(4):
            P.append((cyl((X1 - 34 - 2.6 * j, s * 19.5, 38.2), (X1 - 33.4 - 2.6 * j, s * 22.5, 40.0), 0.85, 10), "metal"))
        P.append((box((X0 - 0.3, s * 22, 31), (0.8, 3.0, 1.6)), "accent"))
    # driver cupola front-left with split chevron vision blocks
    P.append((cyl((X1 - 31, 10, 38.0), (X1 - 31, 10, 41.4), 4.2, 24), "hull2"))
    for t in (1, -1):
        P.append((box((X1 - 27.2, 10 + t * 1.5, 40.2), (1.2, 2.8, 1.1), rotz(t * 30)), "lens"))
    # roof: troop hatches, stowage, Tally RWS
    for x in (X0 + 12, X0 + 26):
        for s in (1, -1):
            P.append((chbox((x, s * 9.5, 38.8), (10, 8.5, 1.2), 0.4), "hull2"))
    P.append((chbox((X0 + 42, -12, 39.4), (16, 7, 2.6), 0.6), "hull2"))
    rx = 14.0
    P.append((cyl((rx, 0, 38.0), (rx, 0, 40.5), 6.0, 28), "hull2"))
    P.append((chbox((rx, 0, 43.2), (8.0, 7.0, 5.0), 0.8), "hull"))
    P.append((chbox((rx + 1.5, 5.4, 45.5), (4.0, 3.0, 3.0), 0.5), "hull2"))   # sensor head
    P.append((box((rx + 3.6, 5.4, 45.6), (0.6, 2.2, 1.2)), "lens"))
    P.append((cyl((rx + 3, -1.2, 43.6), (rx + 22, -1.2, 43.6), 0.9, 12), "metal"))   # heavy repeater
    P.append((cyl((rx + 3, -1.2, 43.6), (rx + 8, -1.2, 43.6), 1.5, 12), "metal"))
    P.append((chbox((rx + 5, -4.2, 41.8), (6, 2.6, 2.6), 0.4), "metal"))             # grenade launcher
    P.append((cyl((rx - 4, -4.5, 40.0), (rx - 4, -4.5, 52.0), 0.35, 6), "metal"))
    # stern ramp
    P.append((chbox((X0 - 0.4, 0, 28.0), (1.6, 28, 16), 0.6), "hull2"))
    P.append((box((X0 - 1.0, 0, 30), (0.6, 4, 7)), "metal"))
    # headlamps / tow eyes
    for s in (1, -1):
        P.append((box((X1 + 0.1, s * 19, 23.3), (0.8, 4.0, 1.4)), "accent"))
        P.append((cyl((X1 - 1.5, s * 9, 19.8), (X1 + 1.6, s * 9, 19.8), 1.0, 10), "metal"))
    return P


if __name__ == "__main__":
    publish(HERE, META, build(), figure_parts(pos=(X1 + 4, 50, 0), yaw=115), hero_kw={"az": 40, "el": 24})
