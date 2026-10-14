"""Sunder-class breaching carrier (AB-9): concept blockout at 1:56 (mm). Run with the sculpt venv:
    ~/ai-stack/venvs/sculpt/bin/python concepts/sunder-breaching-carrier/source/concept.py
Frame: x = front, y = vehicle left, z up, ground z = 0. Two articulated tracked units; the assault module in front
has a chevron-prowed drop ramp (shown raised on the 3-view, lowered on the hero).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_tools"))
import numpy as np  # noqa: E402

from transport_kit import Scene, bev_prism_y, box, chbox, cyl, figure_parts, hull, publish, roty, rotz, track_unit  # noqa: E402

META = {
    "id": "sunder-breaching-carrier",
    "name": "Sunder-class breaching carrier",
    "designation": "AB-9",
    "role": "Heavy articulated assault carrier: noses its armoured assault module straight into a breach (bunker wall, "
            "hab lock, barricade), drops the chevron prow ramp and puts a full Vigil assault section out of the front "
            "under its own armour; the rear power unit stays back and fires over it.",
    "role_short": "Heavy articulated breaching carrier",
    "drive": "tracked, two articulated units (4 track runs)",
    "crew": 3,
    "capacity": "10 Vigilants in full exosuit, standing-ready on grab rails (assault module)",
    "weapons": [
        {"variant": "AB-9A (standard)", "main": "Cleaver 90 mm short demolition gun in the rear-unit turret", "secondary": "cab-roof grenade launcher; prow-mounted smoke mortars"},
        {"variant": "AB-9T Torch", "main": "twin Hearth thermal lances in the rear turret (short range bunker clearing)", "secondary": "as standard"},
        {"variant": "AB-9H Hold", "main": "Rook 30 mm autocannon turret + point-defence laser on the cab", "secondary": "assault module seats 12"},
    ],
}

# front unit (assault module) and rear unit (power + weapons) x-ranges (mm at 1:56)
FX0, FX1 = 6.0, 86.0
RX0, RX1 = -80.0, -10.0
HY = 33.0                       # half width over the tracks
HINGE = np.array([FX1 - 1.0, 0.0, 13.0])
RAMP_LEN = 41.0
RAMP_HW = 18.5


def ramp(open_):
    """Chevron-prow drop ramp: two leaves meeting at a raised keel ridge, breaching teeth on the top edge."""
    ang = math.radians(-18.5) if open_ else math.radians(101.0)
    d = np.array([math.cos(ang), 0, math.sin(ang)])
    n = np.array([d[2], 0, -d[0]])            # outward normal (forward when closed, down when open)
    y = np.array([0, 1.0, 0])

    def W(u, v, w):
        return HINGE + u * d + v * y + w * n

    parts = []
    t = 2.6
    pts = [W(u, v, w) for u in (0, RAMP_LEN) for v in (-RAMP_HW, RAMP_HW) for w in (0, t)]
    pts += [W(u, 0, t + 4.5) for u in (2, RAMP_LEN - 2)]
    parts.append((hull(pts), "hull"))
    parts.append((hull([W(1, 0, t + 4.7), W(RAMP_LEN - 1, 0, t + 4.7), W(1, 1.4, t + 3.6), W(1, -1.4, t + 3.6),
                        W(RAMP_LEN - 1, 1.4, t + 3.6), W(RAMP_LEN - 1, -1.4, t + 3.6)]), "accent"))  # keel ridge
    for v in (-12, -4, 4, 12):                                                                        # breaching teeth
        parts.append((hull([W(RAMP_LEN - 0.5, v - 2, 0.3), W(RAMP_LEN - 0.5, v + 2, 0.3), W(RAMP_LEN - 0.5, v - 2, t + 1.5),
                            W(RAMP_LEN - 0.5, v + 2, t + 1.5), W(RAMP_LEN + 3.5, v, t * 0.6 + 0.8)]), "metal"))
    for u in np.arange(5, RAMP_LEN - 3, 5.0):                                                         # inner tread bars
        parts.append((hull([W(u, -RAMP_HW + 2, -0.8), W(u, RAMP_HW - 2, -0.8), W(u + 1.4, -RAMP_HW + 2, -0.8),
                            W(u + 1.4, RAMP_HW - 2, -0.8), W(u, -RAMP_HW + 2, 0.1), W(u, RAMP_HW - 2, 0.1),
                            W(u + 1.4, -RAMP_HW + 2, 0.1), W(u + 1.4, RAMP_HW - 2, 0.1)]), "metal"))
    for v in (-RAMP_HW - 0.8, RAMP_HW + 0.8):                                                         # hinge knuckles
        parts.append((cyl(HINGE + (0, v - 1.2, 0), HINGE + (0, v + 1.2, 0), 2.0, 14), "metal"))
    return parts


def build(ramp_open=False):
    P = []
    for s in (1, -1):
        for xa, xb, nr in ((FX0 + 1, FX1 - 1, 5), (RX0 + 1, RX1 - 1, 4)):
            parts, _ = track_unit(xa, xb, s * 25.5, 14.0, r_drive=6.6, r_road=4.6, n_road=nr, side=s,
                                  lift_front=6.0, lift_rear=4.0)
            P += parts
    # ---------------- assault module (front unit): floor, side sponsons, roof, rear wall; the front is the ramp
    P.append((chbox(((FX0 + FX1) / 2 - 2, 0, 11.5), (FX1 - FX0 - 6, 37.6, 5.0), 0.8), "hull2"))       # floor pan
    side = [(FX0, 20.0), (FX1 - 2, 20.0), (FX1 + 1.0, 14.0), (FX1 + 1.0, 18.0), (FX1 - 7.5, 55.0), (FX0, 55.0)]
    for s in (1, -1):
        P.append((bev_prism_y(side, 14.0, 1.6, yc=s * (HY - 7.0)), "hull"))
        # interior wall face (visible with the ramp down)
        P.append((box(((FX0 + FX1) / 2 - 4, s * 19.4, 34), (FX1 - FX0 - 14, 1.0, 40)), "hull2"))
        for x in np.arange(FX0 + 10, FX1 - 10, 9.0):                                                 # grab-rail posts
            P.append((cyl((x, s * 18.6, 15), (x, s * 18.6, 50), 0.6, 8), "metal"))
        # sponson plate rhythm: four heavy plates, alternating stand-off
        xs = np.linspace(FX0 + 2, FX1 - 8, 5)
        for i in range(4):
            off = 0.0 if i % 2 == 0 else 0.8
            P.append((chbox(((xs[i] + xs[i + 1]) / 2, s * (HY + 0.4 + off), 31.0), (xs[i + 1] - xs[i] - 1.2, 1.8, 16), 0.6),
                      "panel" if i % 2 == 0 else "hull"))
        # skirts over the front track run
        P.append((chbox(((FX0 + FX1) / 2, s * (HY + 0.6), 17.5), (FX1 - FX0 - 4, 1.6, 6.0), 0.5), "hull2"))
        P.append((chbox(((RX0 + RX1) / 2, s * (HY + 0.6), 17.5), (RX1 - RX0 - 4, 1.6, 6.0), 0.5), "hull2"))
        # prow smoke mortars
        for j in range(2):
            P.append((cyl((FX1 - 9 - 3 * j, s * 29, 55), (FX1 - 7 - 3 * j, s * 30.5, 58.5), 1.1, 10), "metal"))
        P.append((box((FX1 + 0.6, s * 29, 24), (0.8, 4.0, 2.0)), "accent"))                         # headlamps
    P.append((chbox(((FX0 + FX1) / 2 - 4, 0, 55.8), (FX1 - FX0 - 6, 2 * HY - 1, 3.6), 1.0), "hull"))  # roof
    P.append((chbox((FX0 + 2.0, 0, 34), (4.0, 2 * HY - 4, 42), 0.8), "hull2"))                       # rear wall
    P.append((hull([(FX1 - 8, 0, 58.2), (FX0 + 4, 0, 58.2), (FX0 + 4, 0, 57.4), (FX1 - 8, 0, 57.4),
                    (FX1 - 8, 1.6, 57.4), (FX1 - 8, -1.6, 57.4), (FX0 + 4, 1.6, 57.4), (FX0 + 4, -1.6, 57.4)]), "accent"))
    # driver / commander cab on the roof: armoured box with split chevron vision slits
    cx = FX1 - 26
    P.append((hull([(cx - 12, -2, 57), (cx - 12, 22, 57), (cx + 10, -2, 57), (cx + 10, 22, 57),
                    (cx - 11, 0, 66), (cx - 11, 20, 66), (cx + 4, 0, 66), (cx + 4, 20, 66)]), "hull"))
    for t in (1, -1):
        P.append((box((cx + 7.4, 10 + t * 3.4, 62.6), (1.2, 5.8, 1.4), rotz(t * 28) @ roty(-30)), "lens"))
    P.append((chbox((cx - 3, 10, 67.0), (8, 9, 2.0), 0.5), "hull2"))
    P.append((chbox((cx - 3, 10, 69.4), (5, 3, 2.6), 0.4), "metal"))                                  # grenade launcher
    P.append((cyl((cx - 1, 10, 69.6), (cx + 7, 10, 69.6), 0.9, 10), "metal"))
    P.append((cyl((cx - 9, 18, 66), (cx - 9, 18, 72), 0.35, 6), "metal"))
    # roof hatches
    for x in (FX0 + 12, FX0 + 26):
        P.append((chbox((x, -12, 58.0), (10, 12, 1.2), 0.4), "hull2"))
    P += ramp(ramp_open)
    if ramp_open:
        P.append((box(((FX0 + FX1) / 2 - 2, 0, 14.2), (FX1 - FX0 - 10, 34, 0.4)), "dark"))           # interior deck
    # ---------------- articulation: coupling ring, bellows, steering rams
    P.append((chbox(((RX1 + FX0) / 2, 0, 22), (FX0 - RX1 + 8, 22, 18), 1.0), "dark"))
    for i in range(5):
        P.append((chbox((RX1 + 2 + i * 3.2, 0, 22), (1.2, 24, 20), 0.4), "metal"))
    P.append((cyl(((RX1 + FX0) / 2, 0, 9), ((RX1 + FX0) / 2, 0, 14), 7.0, 24), "metal"))
    for s in (1, -1):
        P.append((cyl((RX1 - 2, s * 9, 12), (FX0 + 4, s * 9, 12), 1.2, 10), "metal"))
    # ---------------- rear unit (power + weapons)
    rprof = [(RX0, 18.5), (RX1, 18.5), (RX1, 38.0), (RX1 - 6, 42.0), (RX0 + 4, 42.0), (RX0, 34.0)]
    P.append((bev_prism_y(rprof, 2 * HY, 2.0), "hull"))
    P.append((bev_prism_y([(RX0 + 2, 9), (RX1 - 2, 9), (RX1 - 2, 20), (RX0 + 2, 20)], 36, 1.5), "hull2"))
    for x in (RX0 + 8, RX0 + 16):
        P.append((chbox((x, 0, 42.4), (6, 40, 1.2), 0.4), "dark"))                                    # engine grilles
    for s in (1, -1):
        P.append((cyl((RX0 + 6, s * 26, 42), (RX0 + 6, s * 26, 49), 1.8, 14), "metal"))              # exhaust stacks
        P.append((box((RX0 - 0.3, s * 26, 30), (0.8, 3.0, 1.6)), "accent"))
        xs = np.linspace(RX0 + 3, RX1 - 3, 4)
        for i in range(3):
            P.append((chbox(((xs[i] + xs[i + 1]) / 2, s * (HY + 0.3), 31.0), (xs[i + 1] - xs[i] - 1.2, 1.6, 12), 0.5),
                      "panel" if i % 2 == 0 else "hull"))
    # turret: low wedge with a short, fat Cleaver demolition gun (raised to fire over the assault module)
    tx = -42.0
    P.append((hull([(tx - 15, -15, 42), (tx - 15, 15, 42), (tx + 12, -13, 42), (tx + 12, 13, 42), (tx + 18, 0, 44),
                    (tx - 13, -12, 52), (tx - 13, 12, 52), (tx + 8, -9, 52), (tx + 12, 0, 51)]), "hull"))
    P.append((hull([(tx + 18.3, 0, 44.2), (tx + 12.2, 0, 51.4), (tx - 10, 0, 52.6), (tx - 10, 0, 51.6),
                    (tx + 10, 1.2, 51.0), (tx + 10, -1.2, 51.0), (tx + 16, 1.2, 44.4), (tx + 16, -1.2, 44.4)]), "accent"))
    P.append((chbox((tx + 15, 7, 47.5), (5, 7, 6), 0.8), "metal"))
    gun_a, gun_b = np.array([tx + 16, 7, 48.0]), np.array([tx + 36, 7, 53.0])
    P.append((cyl(gun_a, gun_b, 2.6, 20), "metal"))
    P.append((cyl(gun_b - (gun_b - gun_a) * 0.15, gun_b + (gun_b - gun_a) * 0.05, 3.4, 20), "metal"))
    for t in (1, -1):
        P.append((box((tx + 13.5, -6 + t * 2.4, 49.2), (1.0, 3.6, 1.2), rotz(t * 30) @ roty(-20)), "lens"))
    P.append((cyl((tx - 6, -8, 52), (tx - 6, -8, 55), 2.4, 18), "hull2"))
    return P


if __name__ == "__main__":
    closed = build(False)
    opened = build(True)
    fig = figure_parts(pos=(FX1 + 54, 10, 0), yaw=100)
    publish(HERE, META, closed, fig, hero_kw=None, sheet_extra=None, stl=True)
    # hero with the ramp lowered and the Vigilant stepping off it (overwrites the default hero)
    from transport_kit import hero
    import json
    meta = json.load(open(os.path.join(HERE, "concept.json")))
    d = meta["dims_scale_mm"]
    wm = meta["dims_world_m"]
    hero(Scene(opened + fig), os.path.join(HERE, meta["images"][0]), f"{meta['name']} ({meta['designation']})",
         f"{META['role_short']}  ·  {META['drive']}  ·  prow ramp lowered  ·  Vigilant on 32 mm base for scale",
         az=32, el=24,
         notes=[f"{d['length']:.0f} × {d['width']:.0f} × {d['height']:.0f} mm at 1:56, ramp up  ({wm['length']} × {wm['width']} × {wm['height']} m)"])
