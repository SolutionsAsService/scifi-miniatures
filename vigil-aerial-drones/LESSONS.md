# LESSONS (vigil-aerial-drones, 2026-10-14)

Reusable, evidenced lessons from this package, to fold upstream: 3DADA references (miniatures-lessons.md,
airframe-lessons.md, cad-mcp.md) and unified-CAD-MCP (tool gaps / bugs). Each line: the lesson, the evidence here.

## For 3DADA references/miniatures-lessons.md

1. **Size the real aircraft first, then scale.** Running drone_propulsion_estimate / drone_mass_cg_budget /
   drone_fixed_wing_analysis on an in-world (1:1) spec before sculpting fixes proportions you can defend (rotor disc,
   disc loading, CG) and gives sockets a reason to be where they are: the Knell's flight-stem socket sits on the CG the
   fixed-wing tool picked (static margin 0.10, band 733-792 mm), the Belfry hardpoint on the empty CG (-8 mm in-world).
   check.py re-runs the calls and fails on drift. Evidence: reports/sizing.json, check.py sizing_drift().
2. **Rotor blades print best flat, as separate parts with a through-bore hub.** A 36 mm two-blade rotor 0.9 mm thick
   with a flat underside prints flat on the plate with no supports; the hub gets a through-bore (never a blind hole on
   the plate side: a pocket against the plate is a sealed cup). Mast pin 1.4 / bore 1.6; tail pin 1.0 / bore 1.2.
3. **Put attachment pegs on the bit and sockets on the airframe, with distinct sizes per socket family**
   (stem 1.6 round in 1.8; belly hardpoint 1.6 D-flat; mast 1.2 D-flat; launcher 2.0 D-flat) so a bit cannot go in the
   wrong hole; a single stem length for every flyer (38 mm = 33 visible + 2 + 3).
4. **Loadouts need three measured clearances, not one**: no overlap with the host, the lowest point above the
   skid plane plus margin (landing), and no overlap with the flying stem (the stem leaves the belly next to the
   hardpoint). Evidence: build.json fits.belfry_loadouts (VL-04 had to drop its container top; first build measured
   it 0.25 mm below the margin).
5. **Bit pylons must end exactly at the mating plane.** An rbox centred at -0.45 with half-height 0.55 pokes 0.1 mm
   into the host; Package interference measured 1.877 mm3 for the SAR pod before the fix. Write pylons as
   centre = -half so the top is z = 0 by construction.
6. **Prop phase is relative to the reference direction.** When a prop helper takes ref = the arm direction, the
   per-blade phase must be relative (90 = across the arm), not phi + 90: the first Belfry build had blades lying
   along two arms (0.36 mm over the arm ridge). Render every arm in top view before the checker.
7. **Interfaces to a package you may not edit: measure its surface at a pitch finer than its smallest feature,
   then add a pad.** The Wayfarer roof has no socket; a glue pad with a through D-flat socket (the roof closes it, so
   no cup) carries the launcher. A 4 mm and then a 1 mm integer ray-cast grid both read the roof as flat 38.5 mm,
   yet the first pad spot sat on engine-deck louvre slots (0.5 mm wide, 0.6 mm deep, on half-millimetre x): every
   integer sample stepped over them. A 0.25 mm grid found them; the pad was re-shaped (10 x 5.8 mm) to the flat strip
   between the louvres and the glacis. Rule: sample at <= half the narrowest engraved feature of the host (0.25 mm
   for 0.5 mm slots), test "fraction at plane and nothing above", and document the RWS-style sweep limits instead of
   hiding them. Evidence: build/probe_roof.py vs probe_seam.py / probe_free.py, build.json fits.wayfarer_roof.
8. **Deck-seam patterns on big bases cost triangles, not detail.** A 50 mm base with chevron seams marched at 0.12 mm
   is 710k triangles; 0.2 mm keeps it at 265k with the 0.45 mm seams still at >2 voxels. Pick base pitch from the
   triangle budget (triangles ~ 1 / pitch^2), not from the airframe pitch.
9. **Engrave curved surfaces with "region AND within depth of the surface" cuts**, done before later adds (pod rings,
   wing elevon lines): Shape = max(region(x, y), top(x, y) - depth - z) for a wing, max(|y - y0| - w/2,
   -(pod + depth)) for a pod; later adds (skid tubes, sensor balls) are never nicked because they come after.

## For 3DADA references/airframe-lessons.md

1. A flying wing's "tails" for drone_fixed_wing_analysis are its winglets (role vertical); the tool still requires
   at least one tail and reports a horizontal-tail-volume fail for a tailless aircraft: read stability from the
   static margin, not from tail volume. Enlarging the winglets from 170 to 230 mm in-world moved the vertical tail
   volume from 0.014 to 0.023 (pass).
2. The launcher rail length is a sizing output: drone_fixed_wing_analysis launch stroke (2.447 m at 12 g to 24 m/s)
   set the 2.6 m-class rail (46.4 mm at 1:56) and the shuttle at the rear (stroke 2.5 m in-world, measured).

## For 3DADA references/cad-mcp.md / process

1. In OpenClaw code mode the MCP namespace exposes camelCase names (unifiedGetContext, cadGetScope,
   cadInspectStlGeometry), not the snake_case tool ids the skill text names.
2. Long shell jobs in code mode: a background exec (background: true) survives; setsid/nohup jobs launched from a
   short exec were killed with the shell. Poll a log file with short (<= 5 s) sleeps: an exec that waits longer
   returns "waiting" and a later wait() returned a null value.
3. On a shared 8 GB WSL host, other agents' builds and checks run concurrently: one heavy job at a time is a global
   rule. trimesh.proximity.signed_distance on 250k-triangle meshes is the memory spike to avoid (k-d tree vertex gaps
   are within one edge of the surface gap on dense marched meshes and cost little).

## For unified-CAD-MCP (tool gaps / bugs)

1. drone_propulsion_estimate caps prop_diameter_in at 80 in (2.03 m): a helicopter main rotor beyond that cannot be
   sized; also the figure-of-merit default is flagged unreliable above 40 in. Suggest a rotor_diameter_m input and a
   helicopter preset (FoM 0.6-0.7, tail-rotor power fraction).
2. drone_fixed_wing_analysis requires tails (minItems 1) and fails "horizontal tail volume 0" for flying wings;
   suggest a configuration: "tailless" flag that skips tail-volume checks and reports reflex / elevon sizing instead.
3. drone_regulatory_weight_class needs a jurisdiction argument with no default; harmless but it errors in batch use.
4. The live server's miniature_* tools cannot read package STLs unless the airframe section (read_roots) is
   configured; package checks therefore run the server in-process. A documented "miniature read root" setting would
   let cad_* and miniature_* share the same path on the live server.
5. No ready way to ask "minimum distance between two meshes" or "overlap volume" from the server; both are needed
   for every assembly fit (loadout vs host, rotor vs fin, launcher vs vehicle). Suggest miniature_fit_check(a, b,
   transform) -> overlap_mm3, min_gap_mm.
