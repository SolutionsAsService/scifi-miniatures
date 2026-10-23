# LESSONS (wayfarer-apc, AW-8A, 2026-10-14)

Each line: the lesson | the evidence.

1. **Re-check after every subtractive fix.** | Widening the stern door left a 37 mm² sliver of the sloped stern panel over the opening (< 0.4 mm), which turned a passing hull into a fail. Cut sloped panels deeper at the top than the bottom, or trim back to a 0.6 mm land.
2. **True 1:56 bays do not fit 30 mm heroic troopers.** | The internal height is 24.2 mm (1.36 m at scale), so a standing heroic Vigilant does not fit. Measure fit per pose (crouched, lying, through the hatch) and offer a compressed heroic vehicle scale instead of quietly enlarging the hull.
3. **Probe the roof at no more than half the narrowest engraved feature before seating accessories.** | 4 mm and 1 mm grids read the roof as flat and missed 0.5 mm louvre slots; a 0.25 mm grid found them. Seat bits on a glue pad over a verified flat strip (launcher pad moved to x 41..47).
4. **One socket per interface family.** | The roof accessory 2.0 mm D-flat and the shared 30 mm turret ring (tools/turret_ring.py) mean the RWS, launcher and future turrets cannot go in the wrong hole.
5. **The package id must be unique across the viewer, including concepts.** | The id "wayfarer-apc" collided with the AW-8 concept entry. The package registers as "wayfarer-apc-aw8a"; the build still writes viewer/wayfarer-apc.parts.json, so copy it to the new name after a rebuild.
