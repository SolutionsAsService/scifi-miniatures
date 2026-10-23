# Wayfarer-class APC (AW-8A, Tally RWS) — 1:56 resin kit

Aster Compact / Vigil support vehicle. Deep-V blast hull with tumblehome sides, 8x8 running gear, Tally remote weapon
station on the shared 30 mm Vigil vehicle ring (`../tools/turret_ring.py`), stern ramp and four roof hatches.

All numbers below are measured on the delivered STLs (`reports/build.json`, `reports/printability.json`); units mm,
the sidecars `print/stl/*.stl.meta.json` carry the unit.

## Parts (print/stl/)

| File | Part | Qty | Volume each (mm3) | Extent (mm, model pose) |
|---|---|---|---|---|
| hull-front.stl | Hull, front half (glacis, cupola, ring seat) | 1 | 28 511.94 | 86.1 x 59.0 x 35.65 |
| hull-rear.stl | Hull, rear half (troop bay, deck, door) | 1 | 20 821.28 | 64.9 x 59.0 x 33.2 |
| split-pin.stl | D-flat split pin, 3 mm (symmetric, either end first) | 2 (+1 spare) | 44.79 | 7.5 x 3.0 x 2.4 |
| wheel.stl | Wheel, D-flat hub | 8 | 1 583.91 | 20.8 x 20.8 x 8.05 |
| rws.stl | Tally RWS on 30 mm turntable | 1 | 2 081.89 | 39.2 x 30.0 x 13.2 |
| ramp.stl | Stern ramp (drop-in hinge) | 1 | 1 321.13 | 3.45 x 30.0 x 25.45 |
| hatch.stl | Roof hatch | 4 | 704.17 | 26.1 x 18.0 x 3.6 |

Kit: 18 pieces (+1 spare pin), **68.31 ml** solid resin (budget 55-70 ml). Assembled 151.0 x 59.0 x 51.72 mm
(8.46 x 3.30 x 2.90 m at 1:56). Printability (unified-CAD-MCP `miniature_*` tools via `source/check.py`): see
`reports/printability.md` (PASS).

## Assembly

1. Wash and cure both hull halves with the drains open (3.5 mm keel drains, split-line and roof vents; the hatch
   openings and the stern door also drain the bay).
2. Push two split pins into the front half's sockets (lead-in chamfers; the D-flat fixes roll, either pin end works),
   then close the rear half onto them and glue. The seam sits under the RWS turntable.
3. Wheels: each hub has a 3.2 mm D-flat socket that only fits its axle stub one way round. Eight identical wheels.
4. Tally RWS: glue a 5 x 2 mm magnet in the turntable underside and one in the hull ring boss (pocket 5.2 x 2.1). The
   turntable (30.0 mm in a 30.4 mm seat) turns freely and swaps with every Vigil ring turret.
5. Ramp: drop the hinge pins into the stern hinge slots, no glue; it sits closed or lies open on the table.
6. Hatches: drop fit in their coamings; leave them loose to show the bay.

Optional parts (phase 2) are separate, swappable and checked on their own: see `OPTIONS.md` and
`print/stl/options/`. Nothing in the AW-8A kit above changes when you print them.

## Owner question: compressed heroic vehicle scale

At true 1:56 the troop bay is only **24.2 mm** clear high (1.36 m) and the stern door **26.0 x 23.7 mm**, while a 30 mm
heroic Vigilant on its base stands **35.4-36.4 mm**. Measured (`reports/build.json` `deck_fit`, `reports/fit.md`):

- No standing Vigilant fits the bay or passes the door upright; every measured Vigil figure passes the door crouched
  (65 % of height) or lying, and a hatch takes an upper body (commander pose).
- The troop deck (section at z 12.8) is 12.8-18.9 mm wide and 1 063.6 mm2: **0** based figures of 25, 32 or 40 mm fit.
- So the deck is a visual, seated-troop trench, not a play surface: based figures deploy on the dropped ramp and table.

**Decision needed from the owner:** keep the **true-scale** hull (as delivered; matches the concept and the rest of
the 1:56 vehicle range), or adopt a **compressed heroic vehicle scale** (raise the hull about 1.5x in height so a based
figure stands in the bay; this breaks the 1:56 range, roughly doubles the resin and needs a full rebuild). The kit as
delivered answers "true scale", and nothing in it claims that based figures ride inside.

## Sources

`source/build.py` (manifold3d CSG + renders), `source/check.py` (printability + fit), `source/options.py` and
`source/check_options.py` (phase 2 options), `spec/wayfarer-apc.spec.json`. Design record: `DESIGN-LOG.md`;
lessons: `LESSONS.md`.
