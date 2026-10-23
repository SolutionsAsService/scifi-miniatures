# Vigil arsenal 0.2: 3DADA design log

Run of 2026-10-22 on Windows (native), resuming the WIP VW2 set (commit 979c4e2, revision 0.1, never built or
checked). Compressed run, stated honestly in the Compliance Check: the panel is written sequentially by one author
(the skill's fallback when no sub-agent is used), not convened as one sub-agent per reference.

## Step 0. Tooling inventory

| Job | Tool used |
|---|---|
| CAD MCP | Unified CAD MCP `E:\unified-CAD-MCP` (registered as `unified-cad`; `unified_get_context` reports kicad, cad, pcb backends started, freecad disabled, native KiCad available, drone/miniature tools on). The `miniature_*` tools are driven in-process through `tools/mcpcheck.py` and `E:\ai-stack\tools\detail_survey.py` (same functions the MCP exposes). |
| Measure geometry | `miniature_detail_resolution_check` (new in this run, unified-CAD-MCP `miniature_detail.py`), `miniature_printability_check`, `miniature_support_plan`, `miniature_scale_convert`, `miniature_base_and_peg` via `source/check.py` |
| Author geometry | SDF sculpt (`tools/sdfkit.py`, `tools/arsenal.py`), marching cubes at 0.05 mm; FreeCAD 1.1.4 for the faceted STEP reference. Authored outside the CAD MCP (no `freecad_*` live GUI). |
| Render for the panel | `source/sheet.py` (side-profile sheet at 34 px/mm, 3/4 close-ups), `tools/render.py` |
| Graph tooling | none available beyond Mermaid text; the Frontier is kept by hand in this log |
| Workflow state | the session task list (Claude Code) and this log |
| Panel | sequential, written one reference at a time (fallback) |

## Step 1. Traversal Plan

**Brief.** Make the Vigil guns (and later the armour bits) much more detailed as a 0.2 revision, printable in MSLA resin
at 30 mm heroic (1:56), and improve 3DADA / the CAD MCP with a tool for designing small parts in fine detail.

**Mode: Adaptive.** The work serves a client (the owner's miniature line) and tabletop players who paint and play with it.

**3D frame.** Use: tabletop miniature bits (loose weapons for the Vigil figures). Representation: implicit SDF ->
triangle mesh (one closed manifold body per part). Fate: MSLA resin, 8K 7-inch class (build volume 153.36 x 77.76 x
165 mm). Units mm, z up, x to the muzzle, origin at the grip (spec). Formats: STL per part (print pose), faceted STEP
assembly (reference), viewer JSON. Hard limits (Formlabs Design Guide via `PROCESSES["msla_resin"]`): engraved detail
>= 0.4 mm, embossed >= 0.1 mm, supported wall 0.4 mm, unsupported wall 0.6 mm, wires 0.3 mm to 7 mm, one body per part,
<= 300 k triangles per checked file (pure-Python checker), grip block 1.0 x 1.1 x 2.0 mm (fits `exosuit.fist`).

**Seed** (labels verbatim from `skills/3dada/references/anchor-graph.md`):
- Stance: `MAYA: Most Advanced Yet Acceptable (Raymond Loewy)` (Adaptive governing criterion).
- Rules: `The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret)` --(wall, overhang and clearance
  rules for)--> 3MF/STL exchange; `Polygon Mesh Processing (Botsch, Kobbelt, Pauly, Alliez, Lévy)` <--(isosurface
  meshing for)-- `Marching Cubes (William Lorensen, Harvey Cline)`.
- Form: `The Problem of Form in Painting and Sculpture (Adolf von Hildebrand)` (relief read from one viewing plane:
  a gun is read side-on, at arm's length).
- Breaker: `Complexity and Contradiction in Architecture (Robert Venturi)` (more, layered detail).
- Counterpoint by dotted edge: Venturi -.->|less is a bore answers| `Less Is More (Ludwig Mies van der Rohe)`, itself
  preceded by `Ornament and Crime (Adolf Loos)`.

**Panel (Adaptive + 3D + fabrication):** Critic: Provocateur (Shklovsky), Critic: Inclusion (Holmes), Critic: Human
Scale (Dreyfuss), Critic: Data Gap (Criado Perez), Critic: Relief and Volume (Hildebrand) [Form], Critic:
Manufacturability (Boothroyd), Critic: Manufacturability (Dewhurst), Critic: Mesh Quality (Botsch), Critic:
Workmanship (Pye) [dotted to DFMA: `pye -.->|workmanship of risk counters| dfma`].

## Measurement table

Baseline, measured with `miniature_detail_resolution_check` (msla_resin, limit 0.4 mm, marginal from 0.3 mm, pitch
0.05 mm), file = build/upright print-scale STL. "resolving" = surface-detail regions whose mouth is >= 0.4 mm.

| Part | resolving | /cm2 | marginal | fills | slits |
|---|---|---|---|---|---|
| VW-01 Lance rifle (armory 0.1) | 5 | 3.27 | 0 | 3 | 0 |
| VW-02 Needle rifle | 2 | 1.47 | 0 | 0 | 2 |
| VW-03 Maul arc cannon | 2 | 1.35 | 0 | 0 | 0 |
| VW-04 Spur sidearm | 1 | 4.65 | 0 | 0 | 0 |
| VW-05 Talon carbine | 2 | 2.83 | 0 | 2 | 1 |
| VW-06 Brand flamer | 0 | 0 | 1 | 1 | 1 |
| VW-07 Halberd shotgun | 1 | 0.94 | 4 | 0 | 1 |
| VW-08 Edge blade | 0 | 0 | 0 | 0 | 0 |
| VW2-01 Glaive (WIP 0.1) | 22 | 10.11 | 18 | 9 | 3 |
| VW2-02 Quarrel | 14 | 8.15 | 10 | 9 | 3 |
| VW2-03 Bodkin | 32 | 12.21 | 16 | 6 | 2 |
| VW2-04 Ranseur | 21 | 9.09 | 16 | 13 | 4 |
| VW2-05 Thresher | 35 | 18.98 | 9 | 5 | 0 |
| VW2-06 Rondel | 14 | 11.76 | 7 | 7 | 4 |
| VW2-07 Culverin | 10 | 17.61 | 7 | 7 | 3 |
| VW2-08 Awl | 4 | 8.98 | 12 | 2 | 0 |
| VW2-09 Partisan | 25 | 10.36 | 20 | 10 | 1 |
| VW2-10 Arbalest | 24 | 7.65 | 19 | 1 | 3 |
| VW2-11 Censer | 20 | 10.75 | 6 | 9 | 8 |
| VW2-12 Ballista | 17 | 8.07 | 4 | 2 | 3 |
| VW2-13 Misericorde | 0 | 0 | 2 | 6 | 6 |
| VW2-14 Crowbill | 2 | 2.96 | 7 | 0 | 5 |
| VW2-15 Cinder | 1 | 3.85 | 5 | 5 | 2 |
| VW2-16 Petard | 3 | 5.92 | 1 | 3 | 1 |

### Premortem, round R0 (WHOLE, artifact examined: WIP VW2 build/upright STLs + baseline table)

| Critic | Anchor used | Observed in the work | Verdict | Requested change |
|---|---|---|---|---|
| Manufacturability (Boothroyd) | The 3D Printing Handbook (Redwood) | VW2-01: 18 marginal + 9 fill-in recesses vs 22 resolving (table) | OBJECT | Size every engraved feature to the 0.4 mm limit; the WIP panel lines are 0.35 mm |
| Manufacturability (Dewhurst) | Product Design for Manufacture and Assembly (DFMA) | Vents at 0.4 mm on 0.7-0.8 mm pitch leave 0.3-0.4 mm lands: thin walls between slots | OBJECT | Respace vents for >= 0.45 mm lands |
| Relief and Volume (Hildebrand) | The Problem of Form (Hildebrand) | Detail is cut *into* the receiver side planes; raised relief is limited to rails and sights | OBJECT | Build relief outward: raised plates, bolts, fins read in one plane and cost no wall |
| Mesh Quality (Botsch) | Polygon Mesh Processing; Marching Cubes | Recess walls are 7-8 grid steps wide at 0.05 mm: enough samples | PASS | - |
| Provocateur (Shklovsky) | Art as Device (estrangement) | The set is busy but uniform: every gun uses the same three helpers | OBJECT | Give each gun one signature detail no other gun has |
| Human Scale (Dreyfuss) | Designing for People | Grip block kept at 1.0 x 1.1 x 2.0 mm on all 12 guns (code) | PASS | - |
| Data Gap (Criado Perez) | Invisible Women | The 0.4 mm limit is Formlabs' conservative figure; hobby 8K printers resolve finer, the owner's printer was never measured | OBJECT (data) | Keep marginal (0.3-0.4) visible in the report; ask for a detail coupon print |
| Inclusion (Holmes) | Mismatch | Painters with ordinary brushes need wash channels and raised edges to drybrush | PASS with note | Raised detail serves drybrushing; keep it |
| Workmanship (Pye) | The Nature and Art of Workmanship | Uniform machine regularity everywhere; no hierarchy | OBJECT | Hierarchy: big panel breaks first, then small hardware |

Statements of meaning: a disciplined line infantry's kit, readable silhouettes. Artist question: is "more detail"
worth thin walls? Opinions: most of the WIP detail would not survive printing; the run's first job is to make the
existing detail real, the second to add relief.

## Frontier

| Candidate | Reached via | From anchor | Status |
|---|---|---|---|
| M1 Detail floor: V-grooves, >= 0.46 mm recesses, >= 0.45 mm lands in the shared helpers | wall, overhang and clearance rules for | Redwood | OPEN |
| M2 Relief layer: raised hardware (bolts, plates, fins, cables, selectors, loops) on every gun | relief (form) | Hildebrand | OPEN |
| M3 Signature detail per gun (one feature no other gun has) | estrangement | Shklovsky / Venturi (BREAK) | OPEN |
| M4 Ambition push: densify the boldest gun further | less is a bore answers (dotted) | Venturi vs Mies | OPEN |
| Hierarchy of detail (panel breaks before hardware) | workmanship of risk counters (dotted) | Pye vs DFMA | OPEN |
| Printer detail coupon | data gap | Criado Perez | DEFERRED (needs the owner's printer) |

## Move M1: Detail floor in the shared helpers (KEEP-THE-RULE)

- Anchor: The 3D Printing Handbook (Redwood); counter-anchor Less Is More (Mies) argues for deleting detail instead.
- Change: `hline`/`vline` become 90 deg V-grooves, 0.5 mm mouth, 0.25 mm deep (3dada lesson: box slots fail the gap
  and wall checks, V-grooves do not); every engraved helper floors its width at 0.46 mm; vents respaced so lands are
  >= 0.45 mm; rail teeth 0.45 mm on a 1.0 mm pitch (0.55 gaps); grip grooves 0.48 mm; ring grooves 0.48 mm; brake and
  flash-hider ports 0.46 mm; the one-off WIP cuts under 0.46 mm in individual guns widened.
- Expected measurable effect: fills -> 0 and marginal -> near 0 on VW2-01..12, resolving count not lower.
- Depends on: nothing. Dependents: M2, M3 (they reuse the helpers).

### M1 result (measured; `miniature_detail_resolution_check`, msla_resin, own frame)

All 16 rebuilt at 0.05 mm. Fills across the set 80 -> 14 (9 of them the grenade's crossing grooves), marginal
recesses 159 -> 29, resolving surface detail up on every gun (VW2-01 22 -> 34, VW2-08 4 -> 14, VW2-13 0 -> 11).
The run also found ~60 near-miss slits (0.03-0.25 mm) between separately added bodies that the WIP never measured:
holo base and scope mounts floating 0.08-0.2 mm above the rail strip between teeth, the holo emitter 0.1 mm off its
hood, gas blocks 0.05 mm off handguards, selectors over ejection ports, panel lines cut into 0.3 mm edge fillets,
sights bridging ring grooves. Fixed by fusing (smooth union k 0.12-0.25, sinking mounts to the strip) or by clearing
(> 0.46 mm). Located with a probe that maps each at-risk recess back to the arsenal.py lines whose shapes meet there.

Tool defect found and fixed in the run: `detail_resolution_check` called `rotate()` even without a print pose, and
`rotate()` drops the part so its lowest point is at z = 0; every reported location was 2.35 mm high on VW2-01.
Locations now stay in the part frame unless `rotate_deg` is given (regression test added).

Panel on M1 (artifact: m1b survey + iter STLs). Boothroyd PASS (fills 14, all located). Dewhurst PASS (lands
>= 0.45 by construction in `slots`, brake). Botsch PASS (one body per part asserted by sdfkit). Hildebrand OBJECT
stands (relief still mostly engraved) -> M2. Shklovsky OBJECT stands -> M3. Mies (counterpoint) argued that the
deletion of the glaive handguard's corner line was right: a line that cannot print is ornament without function;
recorded as the 2f deletion review item for that line.

## Move M2: Relief layer (KEEP-THE-RULE, from Hildebrand)

- Anchor: The Problem of Form in Painting and Sculpture (Hildebrand): a relief reads from one plane; at 30 mm a gun is
  read side-on. Raised detail needs only the 0.1 mm embossed limit and adds no thin wall, where engraved detail needs
  0.4 mm and costs wall.
- Change: shared raised hardware: bolted access plates (0.12 proud, 0.4 mm bolt heads at >= 0.86 pitch), a bolt
  carrier block inside each ejection port (0.55 mm gaps either side), magazine round-count windows (raised dots),
  barrel cooling rings where a barrel is exposed, capacitor / indicator lenses (bezel ring + dome), cable runs with
  clamp collars on the energy weapons, raised butt-pad ribs.
- Expected: resolving surface detail up >= 30 % per gun with fills unchanged.
- Depends on M1 (helper floors). Dependents: M3, M4.

### M2 result

Measured (gen-m2): every gun 0 fills (grenade 1); resolving recesses 237 (WIP) -> 344; marginal+fills 187 -> 25.
Instrument amended during the move: recesses shallower than 0.15 mm are slivers (inside corners where a rib meets a
curved body; they hold no wash), and the inventory gained `edge_features` (sharp-edge loops >= 1 mm, dihedral > 30
deg) because raised relief makes no recess and the recess count could not see it. Loops under 1 mm were measured to
be marching-cubes noise at rounded corners (VW2-12: 666 of 894 loops under 0.3 mm).

Panel on M2 (artifact: look-m2a.png, look-m2b.png, both sides at 3/4).
| Critic | Observed | Verdict | Requested change |
|---|---|---|---|
| Relief and Volume (Hildebrand) | +y plates read as one flat step; none carries bolts (rule needs a 1.5 mm tall plate) | OBJECT | bolt short plates on their centre line; break long faces into several plates with seams |
| Provocateur (Shklovsky) | The four guns in look-m2a still differ only in silhouette; no gun has a feature of its own | OBJECT | M3 signatures |
| Workmanship (Pye) | Hierarchy now exists (panel lines > plates > bolts) on the receivers only; stocks, tubes and rail bars are bare | OBJECT | carry the hierarchy onto stocks, launcher tube and rail bars |
| Mesh Quality (Botsch) | Censer hline at z 0.62 sits in the 0.5 mm housing fillet and renders as a shelf | OBJECT | delete it (Mies: a line that cannot sit on a flat face is not detail) |
| Manufacturability (Boothroyd) | gen-m2 fills 0 on all guns | PASS | - |
| Human Scale (Dreyfuss) | grips unchanged | PASS | - |
Edge loops fell slightly (930 -> 908): V-grooves and smooth unions soften the hard box-cut lips of the WIP. Reported
as measured; the relief is real but modest. OVERRULE requested by nobody; the objections go to M3.

## Move M3: Signatures and plated faces (BREAK, from Venturi via Shklovsky)

- Anchor: Complexity and Contradiction in Architecture (Venturi), against Less Is More (Mies, dotted).
- Change: one signature per gun (Glaive rail laser module, Bodkin bipod feet and scope sunshade, Partisan bolted
  stock and carry-handle grips, Arbalest coil windings on the rail bars, Ballista carry handle and flip-up sights,
  Thresher drum lens and plated receiver, Rondel suppressor end cap, Censer canister window, Culverin frame plate,
  Awl rail light, Ranseur launcher leaf sight, Quarrel fore-grip ribs); plates 0.16 thick (seams count as wash
  recesses), bolted on the centre line when short; butt-top round-counter screens on the bullpups.
- Depends on M1, M2. Expected: edge loops up >= 30 % over WIP, fills still 0.

## Open frontier (run incomplete, stopped by usage limit 2026-10-22)

Stop conditions S1-S6 NOT met. Resume point:
1. Package check (source/check.py) FAILS: every part has 2-34 mm2 of supported wall < 0.4 mm, and VW2-15 has 1 fill.
   Thin spots were mapped to source lines with E:\ai-stack\tools\thin_probe.py. Causes and fixes (not yet applied; the batch edit failed on shell quoting):
   grip side grooves next to the cap flange (remove; one finger groove at t=0; cap 0.4 thick); trigger blade r 0.22;
   brake ports r*0.3 tall; cooling_rings / censer fins / arbalest windings / partisan grip rings / crowbill ribs 0.42 thick;
   bullpup hline +y only; butt vents at rear-1.6, rear-0.85, z 0.75-1.75; bodkin ports z 1.25/1.65; ranseur vents z 1.5-1.9;
   thresher pump slots z 0.72-1.18, port x 3.45; rondel hline z 0.95 to x 1.6, plate z0 1.35; culverin flutes skip 60/120 deg,
   vents z 1.3-1.6, vline z 0.65; awl drop comp top port and slide hline; partisan one port row at z 1.6;
   arbalest cable sunk (y -0.95, z 2.35), drop drum clamp; censer canister bands raised (no end grooves), coolant lines sunk;
   ballista optic half-y 0.6, recess half-y 0.2, lens at y -2.5, fire-control bolts at 5.25/6.15; misericorde fuller x -0.2;
   crowbill single striker cross; cinder spoon/head 0.42, pull ring r 0.2; petard hline z 0.55, pad marks y 0.8.
2. Rebuild (source/build.py), re-run check.py until all_pass, WHOLE panel round, Step 2g re-measure, fill DESIGN.md
   PRINTABILITY_SUMMARY / LESSONS, then commit + push scifi-miniatures, register vigil-arsenal into miniature-viewer
   (single-entry insert, NOT a full register-minis run, which would delete vigil-helms-mk3 / lantern-drones / wayfarer-apc-aw8a),
   and push the 3dada reference updates.

### Thin-wall pass (2026-10-23) and publication

The fixes listed above were applied (E:\ai-stack\tools\thinwall_fix.py; all matched). Re-measured on the rebuilt package
(reports/printability.md): supported-wall area fell on 15 of 16 parts (VW2-11 29.8 -> 8.2 mm2, VW2-01 9.9 -> 4.9, VW2-14
2.1 -> 0.6) but no part is under the 0.5 mm2 limit; VW2-12 is unchanged at 30.2 (its thin spots are not the optic). The
moves also opened 9 fill-in recesses on VW2-07, -08, -09, -12, -15. Published as 0.2 with verdict FAIL ("not yet passing"),
as the line's other bits packages were, so the owner can review it in the viewer. Viewer mesh slimmed to 8,000
triangles per part (8.7 -> 3.4 MB; print STLs untouched).

Open frontier (unchanged stop state: S1-S6 not met): re-run tools/thin_probe.py and the arsenal probe on the new report,
fix, rebuild, re-check until all_pass; then a WHOLE panel round and Step 2g.
