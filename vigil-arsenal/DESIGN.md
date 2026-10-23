# Vigil arsenal (VW2 series): design notes

A second, more detailed weapon set for the Aster Compact Vigilant line, alongside (not replacing) the 0.1 armory
(VW-01..08, VA-01..05 in `tools/armory.py`, which are unchanged). Registry: `tools/arsenal.py` (`WEAPONS2`,
`FORE`); package: this folder, built by `tools/bitspack.py` like `vigil-armory/`.

## Brief, restated

Sixteen original weapons for 30 mm heroic (1:56) power-armoured figures, with receivers, panel lines, vents, rails,
separate magazines, optics, muzzle devices, grip texture and stocks that survive MSLA resin (features >= 0.3-0.4 mm,
barrels >= 0.8 mm), sized to the existing Vigil gauntlets and exported as loose bits, with a display sheet.

**Inspiration, not source.** The owner's reference sheet (a stock-vector page of generic sci-fi guns) was used for
qualities only: long, flat, readable side silhouettes; a rhythm of vent slots and rail teeth along the top line; boxy
receivers broken by a few large panel seams; magazines and grips as separate dark masses under the line. No outline
was traced or copied, and the set carries no faction marks, logos or icons. Names follow the Vigil habit of old
weapon and hardware words (Lance, Needle, Talon...) without reusing any existing VW name or vehicle concept name.

## The set

Lengths are the measured x extent of each print file (`reports/build.json`, bbox). Frame: x to the muzzle, z up,
origin = the grip / fist centre.

| Id | Name | Role | Distinguishing detail |
|---|---|---|---|
| VW2-01 | Glaive service rifle | bullpup line rifle | 4-slot vented handguard with its own rail, holo sight (0.6 x 0.5 mm window), gas block, two-port brake, angled fore grip |
| VW2-02 | Quarrel carbine | short bullpup | handguard with a through cooling window, four-prong flash hider, stub fore grip |
| VW2-03 | Bodkin marksman rifle | bullpup DMR | free-float shroud with staggered vent ports, long 1.04 mm barrel, scope (turrets, lens recesses), cheek riser, folded bipod |
| VW2-04 | Ranseur grenadier rifle | bullpup + launcher | 1.9 mm under-barrel launcher tube with a 0.62 mm-radius bore, breech block, launcher grip, side ladder sight |
| VW2-05 | Thresher drum shotgun | pump shotgun | drum magazine with ringed faces and hub, grooved pump, slotted heat shield, breaching crown, skeleton stock, side shell carrier |
| VW2-06 | Rondel PDW | compact PDW | magazine through the grip, ringed integral suppressor, holo sight, vertical fore grip, twin-rod collapsed stock |
| VW2-07 | Culverin heavy revolver | sidearm | six-flute cylinder, slab barrel with top rib and raked vent slots, ejector housing, hammer spur |
| VW2-08 | Awl service pistol | sidearm | serrated slide, ported compensator, top ejection port, rail slots, notched rear sight, beavertail |
| VW2-09 | Partisan LMG | support | box magazine (3 ribs), feed cover with hinge and rail, carry handle, perforated barrel jacket, ribbed handguard, folded bipod, lightened butt |
| VW2-10 | Arbalest rail rifle | sniper / rail gun | twin magnetic rails in four coil clamps, capacitor drum stock, big scope, power cable, fore grip |
| VW2-11 | Censer plasma projector | special | plasma canister in a cradle, two coolant lines, four heat-sink fins, flared emitter cup with an electrode |
| VW2-12 | Ballista launcher | anti-armour | 2.6 mm tube, flat-faced venturi cup, rocket nose in the muzzle, side optic with lens recess, bands, shoulder pad |
| VW2-13 | Misericorde combat knife | blade | clip-point blade, fuller, spine notches, edge tapered to a 0.4 mm rounded flat, ribbed grip, glass breaker |
| VW2-14 | Crowbill breaching tool | tool | 1.0 mm haft with wrap ribs, hammer with cross-hatched striker, curved pry beak, langets |
| VW2-15 | Cinder grenade | ordnance | segmented body (ring + vertical grooves), fuze head, spoon lever, pull ring |
| VW2-16 | Petard breaching charge | ordnance | linear shaped-charge block with V ridge, detonator, cable stub, arming key, strap channels |

## Fit to the Vigil hands

- Every pistol grip is the VW grip block: centre (0, 0, -0.45), 1.0 x 1.1 mm section, 2.0 mm long, as on
  VW-01..07, so `exosuit.fist()` (gauntlet 1.7 x 2.0 x 2.1 mm, closed round the grip axis) fits unchanged.
- VW2 grips rake back 12-22 deg (bottom toward the stock). The VW blocks rake the other way (rot(RY, -14)) while the
  figures already close the fist on down = (-0.24, 0, -0.97); the VW2 rake now agrees with the fist axis.
- `FORE` in `tools/arsenal.py` gives the support-hand fist centre for two-handed poses (e.g. Glaive (5.9, 0, 0.0)).
- A figure holds a VW2 weapon the same way it holds a VW one:
  `g.add(arsenal.weapon_shape("VW2-01").moved(M)); X.fist(g, grip, down, grip - P.elbow[0])`.

## Detail rules (what every feature was sized to)

0.2 supersedes the WIP sizes below: panel lines 0.5 mm 90-degree V-grooves, vents 0.46 mm with 0.45 mm lands, rail
teeth 0.45 mm on a 1.0 mm pitch, raised bolts 0.4 mm / plates 0.16 mm, rings and fins 0.42 mm (`spec/detail_rules_mm`).
The original WIP table is kept for the record:

| Feature | Size | Why |
|---|---|---|
| Engraved panel line | 0.35 wide x 0.25 deep | >= 0.3-0.4 mm brief; miniature_detail_advice floor for panel lines (see reports) |
| Vent slot | 0.40 wide x 0.30 deep, lands >= 0.35 | slots read as a rhythm, lands stay above the 0.3 mm feature floor |
| Rail teeth | 0.42 wide, 0.85 pitch, 0.25 proud | readable rail rhythm; a true 1:56 rail would be 0.09 mm |
| Raised detail (knobs, sights, studs) | >= 0.35 | embossed limit |
| Barrels | 1.0-1.4 mm diameter | brief floor 0.8 mm; a true 25 mm barrel is 0.45 mm at 1:56 |
| Lens / bore recesses | 0.3-0.6 deep, rims >= 0.3 | wash catches, no knife rims |
| Bars (trigger guards, stock rods, carry handle, bipod legs) | 0.6-0.72 mm | above the resin wire floor for their short spans |
| Knife | 1.0 mm spine, 0.4 mm rounded edge flat | blade thickness exaggerated, no knife edge |

## Process (3DADA, compressed)

Run in **Adaptive** mode (the work serves a client brief and tabletop players). This was a compressed run, not the
full 3DADA traversal: no separate critic sub-agents were spawned and no anchor-graph Frontier was kept. What was done:

1. Tooling: unified-CAD-MCP in-process (the `miniature_*` tools through `tools/mcpcheck.py`), sculpt venv for the SDF
   generator; FreeCAD for the faceted STEP reference.
2. Frame: SDF sculpt, marching cubes at 0.05 mm, one closed manifold body per part (asserted in `sdfkit.Sculpt.mesh`),
   mm, z up; fate MSLA resin; formats STL (print), STEP (faceted reference), viewer JSON.
3. Moves, each rendered and looked at before the next:
   - M1 blockout of all 16 at a 0.08 mm grid, side-profile sheet + 3/4 close-ups rendered and inspected.
   - M2 two parts failed the one-body assertion: the Arbalest capacitor butt plate floated 0.1 mm off the drum, and the
     Censer emitter cup sat inside the round-cone's spherical end cap (an enclosed void read as a second shell). Fixed
     by moving the plate onto the drum and trimming round-cone ends flat (`xcap`) before cutting cups (Ballista too).
   - M3 final build at 0.05 mm, sheets re-rendered and inspected, then the printability screen.
4. Critique used in place of a panel (honest summary): silhouette readability at arm's length (side sheet), detail
   floor vs. print limits (miniature_scale_convert / detail_advice), and hand fit (shared grip block).

## Printability

See `reports/printability.md` (generated by `source/check.py`). Summary (0.2, measured): **not yet passing**. Fine detail: 0 recesses fill in on 11 of 16
parts (VW2-07 1, VW2-08 2, VW2-09 3, VW2-12 1, VW2-15 2 still do). Supported walls: every part still has 0.6-30 mm2 under
0.4 mm (largest VW2-12 Ballista 30.2, VW2-03 Bodkin 17.9), down from 2-34 mm2 before the thin-wall pass. Thin spots are
mapped to source lines (see DESIGN-LOG.md, Open frontier); print a coupon before trusting the guns as they stand.

## Files

- `spec/vigil-arsenal.spec.json`: scale, voxel pitch, triangle budget, hand-fit block, detail rules, exaggerations.
- `source/build.py`: builds every part (`tools/arsenal.py` -> `tools/bitspack.py`) and the display sheets.
- `source/sheet.py`: side-profile display sheet at one scale (34 px/mm) and 3/4 close-ups.
- `source/check.py`: unified-CAD-MCP printability screen; writes `print/stl/`, `reports/printability.*`, `mini.json`.
- `images/`: `vigil-arsenal-sheet.png`, `vigil-arsenal-closeups-1.png`, `vigil-arsenal-closeups-2.png`, hero, turnaround.

## Lessons (for 3dada / the CAD MCP)

Carried into 3dada `references/miniatures-lessons.md` ("Fine detail on small parts"): measure detail with
`miniature_detail_resolution_check` rather than trusting the intended size; floor every engraving helper (0.46 mm
recess, 0.45 mm land); fuse or clear near-miss bodies by > 0.46 mm; prefer raised detail (embossed limit 0.1 mm);
keep panel lines and vents off edge fillets; every raised ring or fin is a wall (>= 0.42 mm); write the reference STEP
from a coarse re-mesh and slim the viewer mesh, never the print STL.
