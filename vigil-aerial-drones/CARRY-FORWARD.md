# CARRY-FORWARD (vigil-aerial-drones)

Durable, measured facts about this medium (SDF sculpt -> marching cubes -> MSLA resin, 1:56) that a later run on this
package would otherwise rediscover. One line each: the fact | the measurement | the move it changed. Read before Step 1.

- Triangles scale ~1/pitch^2 for marched SDF parts; a 50 mm deck-seamed base is 710k tris at 0.12 mm, 265k at 0.2 mm | build log (preview vs build) | base pitch 0.2 / 0.18 / tether 0.233 (M1 R1 Dewhurst).
- A 12-prop coaxial hexacopter at 38.7 mm span is ~380k tris at 0.1 mm and 247k at 0.1244 mm | build log | Belfry pitch 0.1244.
- aerial_kit.prop phase is relative to ref (the arm): 90 = across the arm | first build blades lay along the side arms | M3 fix.
- Bit pylons centred at -half put their top exactly on the mating plane; centre -0.45 / half 0.55 pokes 0.1 mm in (1.877 mm3) | Package interference | M6.
- Coplanar contact between a bit collar and a boss top reads ~0.03 mm3 overlap in manifold3d (numerical) | Package interference (VL-10, VL-11 on the Belfry: 0.034) | fit threshold 0.05 mm3 for seated bits.
- drone_propulsion_estimate caps props at 80 in (2.03 m): the Angelus rotor is 2.03 m for that reason | sizing.json | M1.
- drone_fixed_wing_analysis: winglets as two vertical tails; vertical tail volume 0.014 at 170 mm, 0.023 at 230 mm | sizing.json | M1.
- Knell CG band for static margin 0.05-0.15: 733-792 mm aft of the nose; NP 821 mm; socket at 762 | sizing.json | M1.
- Wayfarer roof plane z 38.5; engine-deck louvre slots 0.5 x 0.6 mm deep at x 36.5 / 38.5 / 40.5, y -14.25..-7 (invisible to integer grids); flat strip x 41..47, y -17..-2; fully flat 10 mm squares only at x 22-25; keel crest y 0 from x 22 (z 40.1); smoke dischargers y <= -18 at x 28-35 | 0.25 mm ray-cast grid (build/probe_free.py) | M7 pad 10 x 5.8 at (44.0, -12.0).
- Wayfarer RWS: placed (0, 0, 38.52), local extents x -15..24.2, y +-15, z 0..13.2 (barrel toward +x) | rws.stl bounds | M7.
- trimesh.proximity.signed_distance on 250k-tri meshes got the build OOM-killed on the shared 8 GB host; k-d tree vertex gaps are cheap | build killed, rewritten | fits.
