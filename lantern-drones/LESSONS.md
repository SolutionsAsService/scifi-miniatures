# LESSONS (lantern-drones, build 3, 2026-10-14)

Each line: the lesson | the evidence.

1. **Engrave with 90 deg V-grooves, never box slots, at resin scale.** A 0.40-0.45 mm box slot has two parallel walls
   facing each other (dot -1) closer than 0.5 mm: miniature_gap_check counts every one. A 90 deg V's walls meet at
   dot 0 and never count. | build 2 gap screen: bases 57-87 mm2 -> 0.0 after the change (deck seams).
2. **Keep the V cutter's height above the skin small (top <= 0.3).** Above the skin a V keeps widening (2 x (s + depth)),
   so a tall cutter shaves neighbours. | top 0.8 cut the relay antenna off its discharger bank (2 bodies, 7.29 mm3 loose).
3. **The V's conical end also widens above the skin: stop it >= 0.6 mm short of any neighbouring body.** | Tick track
   shoe grooves run to x 3.0 / 3.85 nicked the hull's rear corners (gap 9.0 / 2.6 mm2); stopping at hull + 0.75 -> 0.8 mm2.
4. **Near-tangent bodies need a web, not a nudge.** A wing bar running almost tangent to a duct leaves a long 0.4 mm
   wedge either side of the arm; a filler web makes bar, arm and duct one cowl. | wisp-a gap 2.06 -> 0.0 mm2.
5. **Never lay one body on another at a 0-0.5 mm step: either fuse (sink >= 0.45 with a >= 0.4 blend) or clear
   by > 0.6.** | cradle (stepped duct pairs under the body) 47.7 -> 0.2 mm2 with a stowage deck the body sinks into.
6. **Pylons root inboard and far from rims.** | wisp-b pylon 0.17 mm under the arm/duct (gap 4.9 mm2) -> 0.57.
7. **A raked socket needs a pad sized for its plan shadow.** | 24 deg, 3.2 deep bore in an r 2.4 pad sat 0.11 mm inside
   the footprint (layout check needs 0.40); r 3.0 fixes it.
8. **Sculpt memory: probe at 2 x pitch first.** Triangles ~ 1/pitch^2, so a coarse probe predicts the budget pitch; the
   old "mesh at h0, then re-mesh" path marched 540k triangles and was OOM-killed under a 1.5 GB cap. | build 4 kill,
   build 5 per-part processes 1-7 s each.
9. **Render in its own process from build/upright, decimated for the render only.** | the in-process render of 13 x
   150k triangles was OOM-killed at 1.5 GB after fits; --images at 40k/part takes 40 s.
10. **Use the local twin (source/diag.py) to iterate, the MCP tools to certify.** | ~30 s per part vs ~2 min, same sampling.
