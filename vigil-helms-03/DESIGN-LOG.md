# Vigil helm library 0.3 (VH4): 3DADA design log

Run of 2026-10-23 on Windows (native) with the Unified CAD MCP connected (`unified-cad`, 103 tools; startup fixed in
unified-CAD-MCP 82e514c: backends start concurrently, 8 s instead of 33 s). Compressed run, stated honestly in the
Compliance Check: the panel is written sequentially by one author (the skill's fallback), not one sub-agent per reference.

## Step 0. Tooling inventory

| Job | Tool used |
|---|---|
| CAD MCP | `unified_get_context` called: kicad, cad, pcb initialized (native KiCad 10.0.6 available), freecad disabled, drone/miniature/airframe builtin; STL reads limited to airframe output_root/read_roots, so iteration files live under `E:\ai-stack\cad-projects\3dada\airframe\helms`. |
| Measure | `miniature_printability_check`, `miniature_detail_resolution_check` called through the MCP on single helms; the same functions batch-run in-process (`E:\ai-stack\tools\helm_batch_check.py`, unified-CAD-MCP src on PYTHONPATH) for 18-helm tables; package certification by `source/check.py` (tools/cachedcheck.py: support plan + printability + gap + shell audit per helm). |
| Author | SDF sculpt: `tools/helms04.py` on `tools/helms3.py` / `tools/vh2.py` blocks, `tools/sdfkit.py` grid 0.05 mm; print-safety `tools/morph.py print_safe_selective` (new). Authored outside the CAD MCP. |
| Render | `E:\ai-stack\tools\helm_sheet.py` (contact sheets), `helm_look.py` (two-view close-ups), package `source/sheet.py` |
| Graph tooling | none beyond Mermaid text; Frontier kept by hand here |
| Panel | sequential, written one reference at a time |

## Step 1. Traversal Plan

**Brief.** A much better 0.3 helm library: pull every helm design from 0.1 (VH-01..10) and 0.2 (VH2-01..12, never
built; VH3-01..08, published), improve and clean them up, printable in MSLA resin at 30 mm heroic.

**Mode: Adaptive** (a product for the owner's line and tabletop painters; MAYA governs).

**3D frame.** Use: swappable helm bits on the Vigil 1.6 mm D-flat neck peg. Representation: implicit SDF -> triangle
mesh, one closed manifold body per helm, not decimated. Fate: MSLA resin (8K 7-inch class). Units mm, z up, face -y.
Formats: STL per helm (print pose from `miniature_support_plan`), viewer JSON. Hard limits: supported wall >= 0.4 mm
over <= 0.5 mm2; recesses >= 0.4 mm (0 fill-ins, marginal 0.3-0.4 reported); one body; no enclosed voids; <= 300 k
triangles; same peg and helm frame as every Vigil helm.

**Seed** (labels verbatim from the 3dada anchor graph): Stance `MAYA: Most Advanced Yet Acceptable (Raymond Loewy)`;
Rules `The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret)` and `Polygon Mesh Processing (Botsch,
Kobbelt, Pauly, Alliez, Lévy)`; Form `The Problem of Form in Painting and Sculpture (Adolf von Hildebrand)`; Breaker
`Complexity and Contradiction in Architecture (Robert Venturi)`; counterpoint by dotted edge `Less Is More (Ludwig
Mies van der Rohe)`. Carry-forward read first: `vigil-helms-mk3/DESIGN-LOG.md` and `LESSONS.md` (hand fixes do not
converge; one global morphological rule did).

**Panel:** Provocateur (Shklovsky), Inclusion (Holmes), Human Scale (Dreyfuss), Data Gap (Criado Perez), Relief and
Volume (Hildebrand), Manufacturability (Boothroyd), Manufacturability (Dewhurst), Mesh Quality (Botsch), Workmanship
(Pye).

### Premortem R0 (WHOLE, artifact: all 30 inherited helms built with the VH3 filter, `sheet-base-34.png`)

| Critic | Observed | Verdict | Requested change |
|---|---|---|---|
| Mesh Quality (Botsch) | VH3-01 close-up: contour rings and grain on every face (the filter takes min/max with integer-voxel distance fields everywhere) | OBJECT | remove the terracing |
| Relief and Volume (Hildebrand) | VH2-01 raw is crisp; through the VH3 filter its plates and frames melt (every convex edge rounded 0.25 mm on a 6 mm helm) | OBJECT | keep edges where nothing is unprintable |
| Manufacturability (Boothroyd) | VH2-01 raw: 10.75 mm2 of supported wall under 0.4 mm (MCP printability check) | OBJECT | make the detailed helms printable without the melt |
| Provocateur (Shklovsky) | VH2-01..12 share one silhouette; VH-05/08/10 read weakly | OBJECT | silhouettes first: carry VH3, re-sculpt the 0.1/VH2 ideas VH3 lacks |
| Workmanship (Pye) | VH3 floors allowed 0.3 mm slots; vents read as fills/marginal at 0.4 | OBJECT | raise slot floors |
| Human Scale (Dreyfuss) | same peg/frame everywhere | PASS | - |
| Data Gap (Criado Perez) | the owner's printer has never been characterised | OBJECT (data) | report marginal recesses, ask for a detail coupon |

## Decision Records

### M1 Terrace-free filter (KEEP-THE-RULE, Botsch) - SCRAPPED
`morph.print_safe_clean`: Gaussian-smoothed fields applied with a tolerance. Measured on VH3-01: passes (min wall
0.586 mm, 0 fills, MCP) and the rings are gone, but on VH2-01 it still melts edges. Superseded by M3.

### M2 Thicken thin features instead of removing them (BREAK, Venturi) - SCRAPPED
`morph.thicken_thin`. Measured on VH2-01: supported thin area 10.75 -> 10.95 mm2 and enclosed voids appeared: the
"walls" were 0.006-0.03 mm cracks where cuts nearly meet, not thin material. Recorded as a refused premise.

### M3 Selective print-safety filter (KEEP-THE-RULE, Redwood, against Mies) - KEPT
`morph.print_safe_selective`: the opening/closing acts only where it moves the surface deeper than 0.12 mm (removal)
or 0.04 mm (fill), feathered over 1.5 voxels; floating specks under 0.5 mm3 dropped. Measured on VH4-01 (MCP): raw
10.75 -> 0.15 mm2 supported thin area, one shell, edges and faces unchanged in the render (look-vh4-01-sel.png).

### M4 One library of 18 (Shklovsky, Venturi) - KEPT
VH3's eight carried (copied into helms04 so 0.3 can change them); ten re-sculpted in the VH3 vocabulary: Lineguard,
Marshal, Breacher, Sentinel, Raptor, Diver, Hunter, Specter, Mender, Wright (see helms04 docstring table).

### M5 Slot floors 0.3 -> 0.5 mm (Pye, Boothroyd) - KEPT
MCP detail check on VH4-01 found the fill-in at the prow vent (0.3 mm) and marginal cheek vents. Shared prow/cheek
vents overridden (0.5 mm, re-spaced so ribs >= 0.4 mm); every inline 0.3 mm cut in the eight ported VH3 designs widened
(jaw vents, recon cooling slots, portcullis grille, pack vents, death's-head teeth and nasal vent, lens cracks, crew
mouth); filter closing r 0.25 -> 0.22 mm so 0.5 mm slots survive.

### M6 Specter cowl rim (Hildebrand)
The hood read as a smooth ball at 3/4: face set 0.3 helm units deeper and a 0.6 mm cowl rim tube added round the opening.

## Measured result (final meshes; see reports/printability.md)

All 18 PASS: supported wall under 0.4 mm over 0-0.22 mm2 (limit 0.5), one closed manifold shell each, no enclosed
voids, 0 recesses that fill in; 1-8 marginal (0.3-0.4 mm) recesses per helm reported as advisory. Package print files
confirmed identical (volume, triangle count) to the measured meshes. Resolving recesses VH4-01 Lineguard 11 (VH3-style
global filter era, same design) -> 22 after the 0.5 mm slot floors; raw VH2-01 had 10.75 mm2 of thin wall.

### Panel R1 (WHOLE, artifact: sheet-vh4-front.png + the table)
| Critic | Observed | Verdict |
|---|---|---|
| Mesh Quality (Botsch) | no terracing on any face; edges as sculpted | PASS |
| Relief and Volume (Hildebrand) | plates, frames and cowl rim read at front view; Specter face now recessed inside a rim | PASS |
| Manufacturability (Boothroyd) | table: 18/18 pass, 0 fills | PASS |
| Manufacturability (Dewhurst) | vents 0.5 mm with >= 0.4 mm ribs by construction | PASS |
| Provocateur (Shklovsky) | 18 distinct front silhouettes; Sentinel's T reads weaker than the rest | PASS with note |
| Workmanship (Pye) | hierarchy keel > glass > vents > studs on every helm | PASS |
| Human Scale (Dreyfuss) | one peg/frame for all | PASS |
| Data Gap (Criado Perez) | marginal recesses remain; the owner's printer still uncharacterised | OBJECT (data, deferred: detail coupon) |

## Open frontier (stop conditions not all met; owner asked to publish without further model runs)
- source/check.py not run: per-helm support plans (print pose), gap check and the generated display sheets (3/4, side,
  back, per-helm strips). Published with upright print files and the front contact sheet; re-run check.py to certify
  print poses and regenerate the report.
- Fit on the rifleman figure not re-run (VH3 also deferred it).
- S2/S3 saturation rounds and the S4 ambition push not run; Sentinel T-visor readability is the next candidate.
- Detail coupon on the owner's printer (Criado Perez).
