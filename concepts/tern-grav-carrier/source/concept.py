"""Tern-class insertion carrier (AG-5): concept blockout at 1:56 (mm). Run with the sculpt venv:
    ~/ai-stack/venvs/sculpt/bin/python concepts/tern-grav-carrier/source/concept.py
Frame: x = front, y = vehicle left, z up, ground z = 0 (the model hovers on a clear flight stand).
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_tools"))
import numpy as np  # noqa: E402

from transport_kit import annulus, box, chbox, chcyl, cyl, figure_parts, hull, publish, roty, rotz  # noqa: E402

META = {
    "id": "tern-grav-carrier",
    "name": "Tern-class insertion carrier",
    "designation": "AG-5",
    "role": "Grav rapid-insertion transport: skims in under sensor cover from the orbital watch, hovers a metre off the "
            "ground with both side doors open so a Vigil fireteam can drop out in seconds, then covers the landing zone "
            "with door guns and lifts away.",
    "role_short": "Grav rapid-insertion transport",
    "drive": "grav (four tilting lift rings) + rear thrust",
    "crew": 2,
    "capacity": "8 Vigilants in full exosuit (four per side on drop rails) + 2 door gunners from the squad",
    "weapons": [
        {"variant": "AG-5A (standard)", "main": "2 pintle heavy repeaters in the side doors", "secondary": "chin sensor turret, flare/chaff pods"},
        {"variant": "AG-5G Gale", "main": "chin-mounted rotary repeater + 2 stub-wing rocket pods (troops reduced to 6)", "secondary": "door repeaters"},
        {"variant": "AG-5L Lift", "main": "unarmed cargo/sling variant: belly winch for a Lantern pod or supply crate", "secondary": "defensive flare pods only"},
    ],
}

HZ = 34.0           # belly height on the flight stand (mm)
X0, X1 = -72.0, 70.0


def build():
    P = []
    # flight stand: 60 mm round base and a clear rod into the belly socket
    P.append((chcyl((0, 0, 0), (0, 0, 4.0), 30.0, ch=1.0, sections=56), "base"))
    P.append((cyl((-4, 0, 3.5), (-4, 0, HZ + 2), 2.0, 16), "stand"))
    z0 = HZ
    # fuselage: troop bay box flowing into a chevron nose and a tapering tail boom
    bay = [(x, s * y, z) for x in (-34, 36) for s in (1, -1) for y, z in ((15, z0), (17.5, z0 + 6), (17.5, z0 + 18), (12, z0 + 24))]
    nose = [(X1, 0, z0 + 7), (X1 - 3, 3, z0 + 4), (X1 - 3, -3, z0 + 4), (X1 - 6, 0, z0 + 11),
            (50, 13, z0 + 2), (50, -13, z0 + 2), (50, 14, z0 + 12), (50, -14, z0 + 12), (46, 8, z0 + 21), (46, -8, z0 + 21)]
    P.append((hull(bay + nose), "hull"))
    tail = [(x, s * y, z) for x in (-30,) for s in (1, -1) for y, z in ((13, z0 + 3), (11, z0 + 21))]
    tail += [(X0, s * 4.5, z0 + 12) for s in (1, -1)] + [(X0, s * 3.5, z0 + 17) for s in (1, -1)]
    P.append((hull(tail), "hull"))
    # split chevron canopy: two glazed panes in a V, divided by the keel spine
    for s in (1, -1):
        P.append((hull([(X1 - 8, s * 0.5, z0 + 11.8), (44, s * 0.5, z0 + 25.0), (44, s * 11.5, z0 + 18.0),
                        (X1 - 13, s * 6.5, z0 + 10.2), (50, s * 0.5, z0 + 18.0), (X1 - 9, s * 0.5, z0 + 9.5)]), "glass"))
    # keel crest from the nose over the canopy and down the spine to the fins
    spine = [(X1 + 0.3, 0, z0 + 7.4), (X1 - 8, 0, z0 + 12.9), (44, 0, z0 + 26.2), (36, 0, z0 + 26.0), (-30, 0, z0 + 22.4),
             (X0 + 4, 0, z0 + 18.8)]
    for a, b in zip(spine[:-1], spine[1:]):
        P.append((hull([a, b, np.add(a, (0, 1.0, -1.6)), np.add(a, (0, -1.0, -1.6)), np.add(b, (0, 1.0, -1.6)),
                        np.add(b, (0, -1.0, -1.6))]), "accent"))
    # open side doors (dark bays) with drop rails and pintle repeaters
    for s in (1, -1):
        P.append((chbox((2, s * 17.3, z0 + 11.5), (40, 1.2, 15), 0.4), "dark"))
        P.append((cyl((-17, s * 18.4, z0 + 2.6), (21, s * 18.4, z0 + 2.6), 0.7, 8), "metal"))         # drop rail
        P.append((cyl((20, s * 18, z0 + 9), (20, s * 20.5, z0 + 12), 0.6, 8), "metal"))
        P.append((chbox((20.5, s * 21.0, z0 + 12.5), (5, 2.2, 2.4), 0.4), "metal"))
        P.append((cyl((23, s * 21.0, z0 + 12.8), (34, s * 21.5, z0 + 12.0), 0.7, 10), "metal"))
        # bay plate rhythm above and below the door
        for i, x in enumerate(np.linspace(-26, 30, 5)):
            P.append((chbox((x, s * 16.6, z0 + 21.0), (12.5, 1.4, 3.0), 0.4), "panel" if i % 2 == 0 else "hull2"))
        # pylons and lift rings (front pair, rear pair), tilted 12 deg forward
        for xp, yp, r in ((26, 40, 13.5), (-40, 38, 12.0)):
            y_in, y_out = 15.0, yp - r + 3.0
            P.append((chbox((xp, s * (y_in + y_out) / 2, z0 + 12), (8, y_out - y_in, 3.0), 1.0), "hull2"))
            c = np.array([xp, s * yp, z0 + 12])
            ax = np.array([np.sin(np.radians(12)), 0, np.cos(np.radians(12))])
            P.append((annulus(c, ax, r - 2.6, r, 6.0, 48), "hull"))
            P.append((annulus(c + ax * 0.2, ax, r - 3.6, r - 2.4, 4.0, 48), "dark"))
            P.append((cyl(c - ax * 1.0, c + ax * 1.0, r - 3.0, 40), "lens"))
            P.append((cyl(c - ax * 3.2, c + ax * 3.2, 2.0, 16), "metal"))            # hub
            for k in range(4):                                                      # stator vanes
                a = np.radians(45 + 90 * k)
                d = np.array([np.cos(a), np.sin(a), 0])
                P.append((box(c + d * (r - 3) / 2, (r - 3, 1.0, 1.6), rotz(np.degrees(a)) @ roty(-12)), "metal"))
        # twin canted tail fins
        P.append((hull([(X0 + 2, s * 3.0, z0 + 16), (X0 + 18, s * 5.5, z0 + 18), (X0 - 2, s * 12.4, z0 + 30),
                        (X0 + 6, s * 12.9, z0 + 30), (X0 + 2, s * 4.8, z0 + 16), (X0 + 18, s * 7.3, z0 + 18),
                        (X0 - 2, s * 13.8, z0 + 30), (X0 + 6, s * 14.3, z0 + 30)]), "hull2"))
        # landing skids (stowed against the belly)
        P.append((cyl((-26, s * 11, z0 - 3.2), (28, s * 11, z0 - 3.2), 0.9, 10), "metal"))
        for x in (-20, 22):
            P.append((cyl((x, s * 11, z0 - 3.2), (x, s * 10, z0 + 1.0), 0.7, 8), "metal"))
        # flare pods on the tail boom
        P.append((chbox((-48, s * 10.0, z0 + 8), (8, 2.4, 3), 0.5), "hull2"))
        # nav light
        P.append((box((48, s * 14.6, z0 + 9), (2.0, 0.6, 1.0)), "accent"))
    # chin sensor turret and belly grav keel strips
    P.append((cyl((56, 0, z0 + 1.5), (56, 0, z0 - 2.0), 3.6, 20), "hull2"))
    P.append((box((59.2, 0, z0 - 0.6), (1.0, 3.0, 1.2)), "lens"))
    for s in (1, -1):
        P.append((box((2, s * 7, z0 - 0.5), (52, 1.6, 1.2)), "lens"))
    # rear thrust nozzle
    P.append((cyl((-30, 0, z0 + 22.5), (-46, 0, z0 + 21), 4.5, 24), "hull2"))
    P.append((annulus((-46.5, 0, z0 + 21), (-1, 0, 0.1), 2.8, 4.6, 2.0, 24), "metal"))
    P.append((cyl((-45.8, 0, z0 + 21), (-46.6, 0, z0 + 21), 2.8, 24), "lens"))
    return P


if __name__ == "__main__":
    publish(HERE, META, build(), figure_parts(pos=(64, 66, 0), yaw=115), hero_kw={"az": 40, "el": 24})
