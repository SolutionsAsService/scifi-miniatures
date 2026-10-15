# VH3 progress notes (working file for the run; folded into DESIGN-LOG.md at the end)

## Environment facts
- Repo ~/projects/scifi-miniatures; registry tools/helms3.py (new); package vigil-helms-mk3/ (source: build.py check.py sheet.py dev.py silhouettes.py devcheck.py; spec/vigil-helms-mk3.spec.json). Dev helpers in build/: thinmap.py thinmap2.py thinviz.py.
- view_image only reads under ~/.openclaw/workspace -> copy PNGs to ~/.openclaw/workspace/tmp-vh3/.
- exec: always awaitResults:true (wait loses values).
- MCP unifiedGetContext: project_root /home/openclaw/projects; freecad disabled; miniature builtin (STL reads disabled in server; package checks run mcpcheck in-process); cadGetScope READ_ONLY_ASSET_CATALOG_WITH_OPT_IN_CAD_REVISIONS, self_intersection_test false. cadInspectStlGeometry({relative_path:'scifi-miniatures/...', units:'mm'}).
- No FreeCAD, no ~/ai-stack shim -> STEP skipped (build.py monkeypatches sdfkit.write_step; report step.status=skipped).
- Fit figure: vigil-rifleman-mk2/build/upright/figure.stl + backpack.stl; pose from vigil-rifleman-mk2/source/build.py (module-level pose); X.helm_placement(pose); sdfkit.overlap_volume threshold 0.02 mm3.

## 3dada seed (Adaptive mode; MAYA governing)
Stance "Make It Bigger (Paula Scher)"; Rules "Gestalt Principles of Perception (Wertheimer, Koffka, Köhler)" -grounds-> "Art and Visual Perception (Rudolf Arnheim)" -perception of volume for-> "The Problem of Form in Painting and Sculpture (Adolf von Hildebrand)"; "The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret)"; "Architecture: Form, Space, and Order (Francis D. K. Ching)" -massing hierarchy analogue of-> Visual Hierarchy. Breaker "Complexity and Contradiction in Architecture (Robert Venturi)" (dotted: less is a bore answers "Less Is More (Ludwig Mies van der Rohe)"; complexity answers the purism of "Towards a New Architecture (Le Corbusier)"). Counterpoint "The Vignelli Canon (Massimo Vignelli)" via scher -.->|contrasts with| vignelliCanon. "MAYA: Most Advanced Yet Acceptable (Raymond Loewy)".
Panel (written sequentially, no subagents): Provocateur (Debord), Provocateur (Shklovsky), Inclusion (Holmes), Inclusion (Mace), Human Scale (Dreyfuss), Data Gap (Criado Perez), Relief and Volume (Hildebrand), Essential Form (Brancusi), Good Design (Rams) [dotted rams -.-> brancusi], Dionysian Excess (Venturi), Manufacturability (Boothroyd), Manufacturability (Dewhurst), Mesh Quality (Botsch).

## Measurements so far
- R0 baseline silhouettes (source/silhouettes.py, 0.04 mm px, z>0): VH-01..10 built STLs: mean distinctness 0.097, min 0.009 (vh-01 vs vh-03 IoU 0.991), mean pair IoU front 0.840 side 0.826. Old VH-01..10 printability: FAIL min wall (thin 0.38-5.9 mm2) - inherited.
- M1 blockout dev0 (pitch 0.08): mean distinctness 0.105, min 0.053 (01<->03 0.947), IoU front 0.836 side 0.855. All 1 body.
- M2 BREAK escalation dev1: mean 0.150, min 0.134, max pair 0.866, IoU front 0.805 side 0.816. 03 height 6.60->5.92 (flat top); 04 8.80->8.92; 07 side width 8.48->8.76; 02 front width 7.16->7.52; 01 front width 6.56->6.88; 08 height 6.52->7.16.
- Visual dev1: 01 brow became thin brim -> M2b thickened to a ledge (shelf poly top 2.0, t 0.8); flare plates boxy (webbed in). 03 flat top strong; 04 triangle fin; 05 globe strong; 06 cap+cups+face; 07 tail; 08 jagged shattered fin + relief death's head reads.
- Full build #1 (0.05 mm, pre-fix): 1 body each, tris 187-227k, unsimplified, RAM 1.23 GB, 7:47. vol mm3: 01 123.83, 02 118.28, 03 127.18, 04 119.46, 05 121.87, 06 94.28, 07 130.17, 08 119.24. bbox: 01 6.87x6.81x8.56, 02 7.49x7.11x8.54, 03 6.38x6.86x7.90, 04 6.24x6.66x10.90, 05 5.91x7.03x8.75, 06 6.12x6.44x8.36, 07 5.65x8.73x8.51, 08 5.91x6.93x9.09. interference none.
- Package check #1: ALL FAIL min wall (supported) area mm2: 01 4.79, 02 4.78, 03 4.30, 04 7.36, 05 6.51, 06 4.89, 07 10.55, 08 11.02. resin ml .124 .118 .127 .119 .122 .094 .130 .119. Support-plan poses: 01 +45x, 02 +45x, 03 +30x, 04 +30x, 05 -30x, 06 -45x, 07 +45x, 08 -30x. Islands 7-15, cups <0.3 mm2. Warnings: unsupported wall.
- Causes found (thin-spot markers): horizontal-ceiling glass walls (vh2.wrap_prism) -> knife lips; VH2 prow vents run off prow edge; clip edges of tail/ridges; random chunks/gouges across plate edges; cheek-ear crevice; Stillwater rib 0.12 mm above glass.
- M3 fixes: rwrap_prism (radial walls), shelf = radial ledge (sinter), ridge sinter ends, prow_vents override xl .62 len .3 depth .28, cheeks web, Ironclad cap thicker (r z .32), Herald keel z0 1.4 + chevron tubes, globe radial window + rib seated (lift -0.04), goggles radial, tail sinter rims + lames |x|<1.45, Grimward notch() + gouges on crown plate + sheared antenna.
- Dev check #2 (upright, 0.05): supported<0.4 mm2: 01 3.99, 02 4.81 (+thin spikes FAIL), 03 2.68, 04 5.84, 05 1.66, 06 3.03, 07 8.58 (+thin spikes FAIL), 08 7.39.
  Remaining spots (HU): 01 visor outer-top corner (+-1.31,-1.13,0.74), prow (+-0.58,-2.2,-0.88) 0.002, nape (+-1.8,1.16,-1.32). 02 pod front-lower outboard (-3.8,-1.6,0.16..0.52) [rangefinder lens near pod edge], prow (0.09,-1.96,-0.92). 03 (2.08,-0.82,0.56), nape (2.04,1.42,-0.78), grille (-0.99,-2.38,-1.29). 04 (-0.64,-1.85,0.57), cheek (-1.22,-2.03,-0.82), (-1.13,-1.99,-1.58), (-2.32,-0.83,-1.11), prow (0.3,-2.25,-0.87). 05 temple lamp rims (+-2.25,-0.52,1.15) [rim 0.25 too thin], (-2.05,-0.95,-0.69). 06 chin strap/chin crevice (0.2,-1.3,-1.65), side ribs (-0.74,..,2.3-3.0). 07 tail back rim (+-0.76,4.5,-0.55) 0.003 and (+-1.3,4.26,0.3); prow vents. 08 crest/fin junction (-0.05,-0.97,2.85), gouges (0.4,-1.34,2.54) (-1.43,-1.07,2.27), chin (-0.33,-2.5,-1.71), cheek notch (-2.46,-1.87,-1.43), antenna shear (-2.54,0.45,1.24).

## Next
1. Fix remaining spots, dev-check loop. 2. source/fit.py on rifleman. 3. final build+check+silhouettes+cadInspectStlGeometry. 4. DESIGN-LOG.md, DESIGN.md, carry-forward, docstring (rwrap_prism). 5. git add own files, commit.

## Round 2 findings (thin2 markers)
- devcheck mapping bug: the in-process tool keeps model x,y (only z shifted to plate) -> subtract only z (fixed in devcheck.py). Package check (mcpcheck to_plate) DOES recentre x,y (thinmap2 correct).
- Main remaining cause on std-jaw helms (01 02 04 07): visor lower V tip frame/recess cut into the prow -> slivers. Fix M4: glass_visor BEFORE jaw/prow/cheeks (prow overrides). Ironclad: visor before faceplate.
- 07 tail tip is a wedge -> blunt it (keep y <= 3.75 HU) ; 08 gouges must stay s<=1.3 (crown plate |x|<1.5 HU), crest tube a1 75 into fin, faceplate bottom raised (z=0 seat cut made wedge), cheek notch -> pits, antenna -> flat stub; 02 rangefinder lens overhung pod bottom -> up*-0.35 rim .3; 05 lamp rim .25 -> .42; 06 chin strap embedded (mid z -1.75), side ribs as tubes.

## Dev check #3 (after round-2 fixes)
```
vh3-01-plummet ['minimum wall (supported)', 'thin spikes / wires'] supported<0.4: 4.154 unsup<0.6: 7.284
     (0.319, 0.004, [0.79, -2.67, 1.89], [0.71, -2.38, -0.81])
     (0.287, 0.006, [-1.43, -1.65, 3.63], [-1.28, -1.47, 0.74])
     (0.225, 0.059, [-1.01, -2.5, 2.03], [-0.9, -2.23, -0.69])
     (0.217, 0.002, [-0.96, -2.57, 1.94], [-0.86, -2.29, -0.77])
     (0.199, 0.002, [1.48, -1.51, 3.63], [1.32, -1.35, 0.74])
     (0.162, 0.014, [1.97, 1.04, 1.29], [1.76, 0.93, -1.35])
vh3-02-sightline ['minimum wall (supported)', 'thin spikes / wires'] supported<0.4: 4.474 unsup<0.6: 9.34
     (0.63, 0.074, [-3.15, -2.29, 3.09], [-2.81, -2.04, 0.26])
     (0.438, 0.039, [-3.24, -2.2, 3.53], [-2.89, -1.96, 0.65])
     (0.378, 0.005, [-0.91, -2.61, 1.71], [-0.81, -2.33, -0.97])
     (0.368, 0.005, [0.97, -2.57, 1.72], [0.87, -2.29, -0.96])
     (0.166, 0.075, [-2.27, 1.54, 1.88], [-2.03, 1.38, -0.82])
     (0.132, 0.009, [-1.06, -2.49, 1.63], [-0.95, -2.22, -1.04])
vh3-03-ironclad ['minimum wall (supported)'] supported<0.4: 2.681 unsup<0.6: 9.63
     (0.331, 0.081, [-2.26, -0.83, 4.25], [-2.02, -0.74, 1.29])
     (0.147, 0.081, [-1.11, -2.71, 1.36], [-0.99, -2.42, -1.29])
     (0.146, 0.075, [-1.92, 2.19, 1.93], [-1.71, 1.96, -0.78])
     (0.138, 0.067, [2.28, 1.54, 1.91], [2.04, 1.38, -0.79])
     (0.097, 0.111, [-1.55, 1.09, 0.86], [-1.38, 0.97, -1.73])
     (0.087, 0.064, [0.66, 3.08, 1.93], [0.59, 2.75, -0.78])
vh3-04-herald ['minimum wall (supported)', 'thin spikes / wires'] supported<0.4: 5.993 unsup<0.6: 10.391
     (0.316, 0.003, [-0.77, -2.67, 1.94], [-0.69, -2.38, -0.77])
     (0.31, 0.001, [0.63, -2.72, 1.95], [0.56, -2.43, -0.76])
     (0.224, 0.02, [-1.06, -2.5, 1.8], [-0.95, -2.23, -0.89])
     (0.145, 0.002, [1.1, -1.88, 3.53], [0.98, -1.68, 0.65])
     (0.143, 0.014, [-1.08, -1.93, 3.54], [-0.96, -1.72, 0.66])
     (0.112, 0.076, [2.18, 1.55, 1.71], [1.95, 1.38, -0.97])
vh3-05-stillwater ['minimum wall (supported)'] supported<0.4: 0.831 unsup<0.6: 6.109
     (0.471, 0.14, [2.49, -0.93, 4.15], [2.22, -0.83, 1.21])
     (0.423, 0.12, [2.6, -1.0, 4.17], [2.32, -0.89, 1.22])
     (0.387, 0.128, [-2.4, -1.28, 4.34], [-2.14, -1.14, 1.38])
     (0.379, 0.113, [-2.62, -0.99, 4.1], [-2.34, -0.88, 1.16])
     (0.374, 0.056, [-2.36, -0.91, 1.63], [-2.11, -0.81, -1.04])
     (0.086, 0.043, [1.68, -0.84, 1.01], [1.5, -0.75, -1.6])
vh3-06-deckhand ['minimum wall (supported)'] supported<0.4: 1.618 unsup<0.6: 21.232
     (0.493, 0.232, [-2.11, -1.63, 4.29], [-1.88, -1.46, 1.33])
     (0.49, 0.218, [-2.21, -1.12, 4.72], [-1.97, -1.0, 1.71])
     (0.455, 0.057, [2.1, -1.14, 4.86], [1.88, -1.02, 1.84])
     (0.428, 0.164, [2.23, -1.38, 4.39], [1.99, -1.23, 1.42])
     (0.339, 0.193, [-2.1, 1.9, 2.02], [-1.88, 1.7, -0.7])
     (0.317, 0.268, [1.57, 2.4, 1.79], [1.4, 2.14, -0.9])
vh3-07-longsight ['minimum wall (supported)', 'thin spikes / wires'] supported<0.4: 6.562 unsup<0.6: 14.579
     (0.698, 0.021, [-1.47, 4.14, 3.12], [-1.31, 3.7, 0.29])
     (0.66, 0.069, [1.49, 4.09, 3.34], [1.33, 3.65, 0.48])
     (0.569, 0.074, [-1.37, 4.13, 2.16], [-1.22, 3.69, -0.57])
     (0.44, 0.006, [-0.98, -2.56, 1.75], [-0.87, -2.29, -0.94])
     (0.35, 0.007, [0.99, -2.57, 1.85], [0.88, -2.29, -0.85])
     (0.323, 0.01, [-2.16, -0.77, 4.24], [-1.93, -0.69, 1.29])
vh3-08-grimward ['minimum wall (supported)'] supported<0.4: 6.664 unsup<0.6: 14.101
     (1.837, 0.008, [0.49, -1.12, 5.84], [0.44, -1.0, 2.71])
     (0.371, 0.004, [-1.22, -2.47, 1.29], [-1.09, -2.21, -1.35])
     (0.332, 0.015, [0.88, -0.97, 5.79], [0.79, -0.87, 2.67])
     (0.243, 0.039, [1.05, -2.49, 0.89], [0.94, -2.22, -1.71])
     (0.205, 0.016, [0.39, -1.57, 5.59], [0.35, -1.4, 2.49])
     (0.191, 0.037, [2.29, 1.54, 1.93], [2.04, 1.38, -0.78])
vh3-01-plummet [{"xy_mm": [-0.66, -2.71], "top_z_mm": 3.825, "length_mm": 0.15, "mean_diameter_mm": 0.057, "min_diameter_mm": 0.042, "max_free_length_mm": 0.0}, {"xy_mm": [0.78, -2.66], "top_z_mm": 3.875, "length_mm": 0.2, "mean_diameter_mm": 0.055, "min_diameter_mm": 0.021, "max_free_length_mm": 0.0}, {"xy_mm": [
vh3-02-sightline [{"xy_mm": [-0.67, -2.71], "top_z_mm": 3.725, "length_mm": 0.25, "mean_diameter_mm": 0.074, "min_diameter_mm": 0.068, "max_free_length_mm": 0.0}, {"xy_mm": [0.67, -2.71], "top_z_mm": 3.725, "length_mm": 0.2, "mean_diameter_mm": 0.072, "min_diameter_mm": 0.068, "max_free_length_mm": 0.0}, {"xy_mm": [
vh3-04-herald [{"xy_mm": [-0.66, -2.71], "top_z_mm": 3.825, "length_mm": 0.15, "mean_diameter_mm": 0.057, "min_diameter_mm": 0.042, "max_free_length_mm": 0.0}, {"xy_mm": [0.78, -2.66], "top_z_mm": 3.875, "length_mm": 0.2, "mean_diameter_mm": 0.055, "min_diameter_mm": 0.021, "max_free_length_mm": 0.0}, {"xy_mm": [
vh3-07-longsight [{"xy_mm": [-0.66, -2.72], "top_z_mm": 3.775, "length_mm": 0.2, "mean_diameter_mm": 0.056, "min_diameter_mm": 0.043, "max_free_length_mm": 0.0}, {"xy_mm": [0.64, -2.72], "top_z_mm": 3.775, "length_mm": 0.2, "mean_diameter_mm": 0.057, "min_diameter_mm": 0.034, "max_free_length_mm": 0.0}, {"xy_mm": [-
```
