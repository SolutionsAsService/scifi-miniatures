# CARRY-FORWARD (lantern-drones)

Measured facts about this medium (SDF sculpt -> marching cubes -> MSLA resin) for later runs. Fact | measurement | move.

- 90 deg V-grooves (0.6 x 0.3) pass miniature_gap_check where 0.45 box slots fail | bases 57-87 -> 0 mm2 | build 3 seams.
- vgroove top > 0.3 shaves neighbours (V widens above the skin) | relay split into 2 bodies at top 0.8 | M8.
- V cone ends need >= 0.6 clearance from other bodies | tick hull 9.0 -> 2.6 -> 0.8 mm2 | M8.
- Bar-tangent-to-duct wedges (0.40 mm) need a filler web | wisp-a 2.06 -> 0 mm2 | M8.
- A coarse probe at 2 x h predicts triangles within ~5 % (n(h) ~ 4 x n(2h)) | wisp-b 577k predicted, 150k at 0.098 | tooling.
- Rendering 13 x 150k triangles in-process > 1.5 GB; 40k per part renders in 40 s | build 5 OOM, build 6 | tooling.
- Raked (24 deg) 1.8 bore 3.2 deep needs a pad r >= 3.0 for the 0.40 mm layout margin | layout check 0.113 at r 2.4 | M9.
