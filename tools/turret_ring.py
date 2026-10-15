"""Shared 30 mm magnetised turret / RWS ring for Vigil support vehicles at 1:56 (manifold3d CSG).

One ring standard so turret and RWS tops swap between hulls: the Wayfarer AW-8 Tally RWS and the Palisade AV-3
turrets / AV-3W Ward RWS (concepts/palisade-ifv/concept.md: "30 mm round turret ring (magnet 5x2 mm) ... the Ward
RWS uses the same ring as the Wayfarer's Tally RWS").

Frame: mm, z up. The hull side is a raised collar on the roof with a flat-bottomed seat (the roof itself); the
turret side is a 30.0 mm turntable disc that drops into the seat and is held by two 5 x 2 mm disc magnets (one under
the seat floor, one in the turntable underside). The turret turns freely; the seat is a slip fit (0.2 mm per side,
a little coarser than the 0.15 mm slip convention in miniature_base_and_peg so resin bloom on a 30 mm circle does
not bind). Print a tolerance coupon before trusting it.

Sizes are checked by source/check.py of each user package through miniature_base_and_peg (magnet pocket floor and
rim). Pure functions, no package state. Needs numpy and manifold3d (sculpt venv).
"""
from __future__ import annotations

import manifold3d as mf

RING = {
    "turntable_d": 30.0,      # the "30 mm ring": diameter of the turret turntable disc
    "seat_clearance": 0.2,    # per side (seat d = 30.4)
    "seat_depth": 1.2,        # collar height above the roof = depth of the seat
    "collar_wall": 1.6,       # radial width of the raised collar (outer d = 33.6)
    "turntable_h": 1.8,       # disc thickness (1.2 in the seat, 0.6 proud of the collar)
    "turntable_chamfer": 0.4,
    "magnet": "5x2",
    "magnet_pocket_d": 5.2,   # 5 mm disc + 0.1 mm glue fit per side (miniature_base_and_peg, glue)
    "magnet_pocket_depth": 2.1,
    "segments": 128,
}


def seat_d(r=RING):
    return r["turntable_d"] + 2 * r["seat_clearance"]


def collar_od(r=RING):
    return seat_d(r) + 2 * r["collar_wall"]


def _cyl(z0, z1, rad, seg):
    return mf.Manifold.cylinder(z1 - z0, rad, rad, seg).translate((0, 0, z0))


def hull_collar(cx, cy, roof_z, r=RING):
    """Raised collar ring standing on the roof plane z = roof_z (the seat floor is the roof itself)."""
    seg = r["segments"]
    outer = _cyl(roof_z - 0.6, roof_z + r["seat_depth"], collar_od(r) / 2, seg)   # buried 0.6 mm into the roof
    inner = _cyl(roof_z, roof_z + r["seat_depth"] + 1, seat_d(r) / 2, seg)
    return (outer - inner).translate((cx, cy, 0))


def hull_magnet_boss(cx, cy, roof_z, roof_t, depth=3.0, rad=4.5):
    """Boss hanging under the roof so the magnet pocket keeps a floor (pocket depth > roof thickness)."""
    return _cyl(roof_z - roof_t - depth, roof_z - roof_t + 0.3, rad, 48).translate((cx, cy, 0))


def hull_magnet_pocket(cx, cy, roof_z, r=RING):
    d = r["magnet_pocket_depth"]
    return _cyl(roof_z - d, roof_z + 0.5, r["magnet_pocket_d"] / 2, 48).translate((cx, cy, 0))


def turntable(r=RING):
    """Turret-side disc centred on the origin, underside at z = 0. Subtract turntable_pocket() after the caller has
    unioned the turret body on top (the body must cover the pocket by >= 0.4 mm)."""
    seg = r["segments"]
    R, h, c = r["turntable_d"] / 2, r["turntable_h"], r["turntable_chamfer"]
    return mf.Manifold.batch_hull([_cyl(c, h, R, seg), _cyl(0, h, R - c, seg)])


def turntable_pocket(r=RING):
    return _cyl(-0.5, r["magnet_pocket_depth"], r["magnet_pocket_d"] / 2, 48)


def describe(r=RING):
    return {**r, "seat_d": round(seat_d(r), 3), "collar_od": round(collar_od(r), 3),
            "note": "Shared Vigil vehicle ring: Wayfarer AW-8 Tally RWS, Palisade AV-3 turrets / AV-3W Ward RWS."}


if __name__ == "__main__":
    import json
    print(json.dumps(describe(), indent=1))
    t = turntable() - turntable_pocket()
    print("turntable volume mm3", round(t.volume(), 2), "collar volume", round(hull_collar(0, 0, 0).volume(), 2))
