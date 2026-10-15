# DESIGN-LOG: Vigil aerial wing (vigil-aerial-drones)

3DADA run, 2026-10-14, subagent build for the scifi-miniatures repo. Mode: **Adaptive** (see Traversal Plan).
Artifacts in this file: 1 Traversal Plan + Frontier, 2 Decision Records, 3 Panel Reports, 4 Anchor Ledger, 5 Compliance Check;
then the close (double loop, graph amendments). Carry-forward facts: CARRY-FORWARD.md. Reusable lessons for upstream: LESSONS.md.

## Step 0. Tooling inventory

| Job | Tool used | Note |
|---|---|---|
| Detect the Unified CAD MCP | live MCP server unifiedCad (code-mode namespace) + in-process server from ~/projects/unified-CAD-MCP/src | unified_get_context (unifiedGetContext): project_root /home/openclaw/projects; freecad backend disabled (no FreeCAD in WSL), airframe tools disabled on the live server, miniature STL reads not configured on the live server, kicad missing. cad_get_scope (cadGetScope): READ_ONLY_ASSET_CATALOG_WITH_OPT_IN_CAD_REVISIONS, self-intersection test false. |
| Author geometry | SDF sculpt: tools/sdfkit.py + new tools/aerial_kit.py + source/vigil_aerial.py (scifi-sculpt venv) | parametric script is the source of truth; marching cubes; never QEM-decimated for print |
| Plausible proportions | drone_propulsion_estimate, drone_mass_cg_budget, drone_fixed_wing_analysis (in-process MCP, source/sizing.py, re-run by check.py) | reports/sizing.json |
| Printability | miniature_scale_convert, detail_advice, base_and_peg, base_layout_check, slender_feature_check, gap_check, support_plan, printability_check, plate_pack, shell_audit, mesh_budget (in-process MCP through source/check.py; the live server has no airframe/miniature read root) | reports/printability.{json,md} |
| Measure fits / interference | sdfkit.overlap_volume (manifold3d boolean), k-d tree gaps, downward ray cast on the Wayfarer roof (source/build.py fits) | reports/build.json "fits" |
| STL geometry on the live server | cad_inspect_stl_geometry on print/stl (final-state rows) | see Measurement table |
| Render | tools/render.py (orthographic painter, 3/4 + front + side + top) | images/*.png |
| STEP | none available: FreeCAD absent, tools/freecadshim has no target here | UNKNOWN (recorded in reports/build.json) |
| Graph / Frontier | no graph tool: edges read by hand from references/anchor-graph.md; Mermaid text below | |
| Workflow state | this log (checklists) | |
| Independent critics | no per-reference agents spawned (cost); each critic report written in full before the next | disclosed in Compliance Check |

## 1. Traversal Plan

**Brief (one sentence).** A new 1:56 MSLA-resin package of three original Aster Compact Vigil airframes (a heavy-lift observation multirotor bigger than the Lantern Wisp, an unmanned observation helicopter with separate rotors, a flying-wing loitering UAV with a rail launcher that can sit on the Wayfarer APC roof) plus loadout bits, all flown on printed or clear-rod stems over 40/50 mm magnet bases, in the Vigil language (split-chevron sensor lenses, keel crest / spine).

**Mode: Adaptive.** The work serves an audience (tabletop players and the repo owner's line); it must read instantly as "Vigil" and as each aircraft type, so MAYA (Loewy) governs: the advanced pole (unusual, ambitious, original silhouettes and the tether idea) and the acceptable pole (legible types, printable, fits the existing line) must both hold.

**3D frame.**
- Use: tabletop wargaming miniatures (vehicles and drones tier), painted, handled.
- Representation: implicit SDF solids marched to watertight triangle meshes (one body per part).
- Fate: MSLA resin print, 8K 7-inch class printer (153.36 x 77.76 x 165 mm build volume, tools/mcpcheck PRINTERS); supports per miniature_support_plan; rotors flat on the plate.
- Units and axes: millimetres at print scale (1:56: 17.86 mm per metre), z up, every airframe faces -y with its left side on +x. STL carries no units: every print STL has a .meta.json units sidecar.
- Formats: STL (print/stl, print pose), viewer JSON (viewer/vigil-aerial-drones.parts.json), STEP skipped (UNKNOWN).
- Hard limits (numbers): wall >= 0.6 mm; rotor / prop blades >= 0.8 mm thick (brief); engraved lines >= 0.4 mm wide (0.44-0.45 used), raised detail >= 0.15 mm; air gaps between facing surfaces >= 0.5 mm; blunt trailing edges >= 0.7 mm; flight stem 1.6 mm in 1.8 mm glue-fit sockets (clear-rod compatible); bases 40 or 50 mm with a 5x2 mm magnet pocket (5.2 x 2.1 mm) vented; launcher peg 2.0 mm D-flat; payload never below the skid plane minus 0.5 mm; triangle budget 250k per part (160k small bits) for the checker; no suction cups, no sealed cavities, no specks.

**Seed (labels verbatim from references/anchor-graph.md).**
- Stance: Make It Bigger (Paula Scher)
- Rules: Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight); The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret); ISO/ASTM 52910 Design for Additive Manufacturing (ISO, ASTM)
- Form (3D cluster): On Growth and Form (D'Arcy Wentworth Thompson); Brancusi: The Sculpture and Drawings (Sidney Geist)
- Breaker: Complexity and Contradiction in Architecture (Robert Venturi)
- Counterpoint (dotted edge): Less Is More (Ludwig Mies van der Rohe), reached from Venturi by "less is a bore answers" (dotted)
- Governing: MAYA: Most Advanced Yet Acceptable (Raymond Loewy) -.->|tempers strangeness of| Art as Technique (Viktor Shklovsky)

**Chain.** Make It Bigger (Paula Scher) -> (heroic exaggeration, the line's scale rule) -> ISO/ASTM 52910 Design for Additive Manufacturing (ISO, ASTM) -->|additive design rules for| The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret) -->|wall, overhang and clearance rules for| 3MF/STL exchange; Poka-Yoke -->|assembly that cannot go wrong for| Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight); On Growth and Form (D'Arcy Wentworth Thompson) -->|morphology as parameter for| parametric form (sizing drives proportion); Brancusi: The Sculpture and Drawings (Sidney Geist) -->|reduction precedes| Specific Objects (Donald Judd); Complexity and Contradiction in Architecture (Robert Venturi) -.->|less is a bore answers| Less Is More (Ludwig Mies van der Rohe); MAYA: Most Advanced Yet Acceptable (Raymond Loewy) -.->|tempers strangeness of| Art as Technique (Viktor Shklovsky).

**Initial moves.** M1 Sizing drives proportion (KEEP-THE-RULE, D'Arcy). M2 Three Vigil silhouettes (KEEP-THE-RULE, Brancusi / Scher). M3 Exposed props and separate rotors (BREAK, Venturi against the miniature rule "no fragile slender parts"). M4 The stem becomes the tether (BREAK, Krauss against the pedestal). M5..: loadout poka-yoke, the Wayfarer interface, then whatever the panels open.

**R0 premortem.** No inherited artifact: the package is new. R0 was held on the inputs instead (reference photos, sibling packages): objections entered as the first Frontier candidates:
- Provocateur (Shklovsky): "a ZALA-like heli and a KUB-like wing will read as replicas" -> candidate F1: originality audit (what is ours, what is quality only).
- Usability (Krug): "a 38 mm hexacopter with 24 bare blades will snap in a figure case" -> F2: blade thickness and slender checks measured.
- Data Gap (Criado Perez): "the Wayfarer has no roof socket; an interface you can't verify is a guess" -> F3: measure the roof (ray cast) and the RWS sweep before choosing the pad spot.
- Manufacturability (Boothroyd): "three base designs, four peg sizes: assembly errors" -> F4: one stem for all, keyed D-flats, distinct peg sizes per socket family.

Mermaid (visited marked):
```mermaid
graph LR
  scher[Make It Bigger (Paula Scher)]:::visited
  dfam[ISO/ASTM 52910 Design for Additive Manufacturing (ISO, ASTM)]:::visited -->|additive design rules for| redwood[The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret)]:::visited
  c_poka[Poka-Yoke]:::visited -->|assembly that cannot go wrong for| dfma[Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight)]:::visited
  darcy[On Growth and Form (D'Arcy Wentworth Thompson)]:::visited
  brancusi[Brancusi: The Sculpture and Drawings (Sidney Geist)]:::visited -->|reduction precedes| judd[Specific Objects (Donald Judd)]
  venturi1[Complexity and Contradiction in Architecture (Robert Venturi)]:::visited -.->|less is a bore answers| mies[Less Is More (Ludwig Mies van der Rohe)]:::visited
  maya[MAYA: Most Advanced Yet Acceptable (Raymond Loewy)]:::visited -.->|tempers strangeness of| shk[Art as Technique (Viktor Shklovsky)]
  kraussField[Sculpture in the Expanded Field (Rosalind Krauss)] -.->|expanded field answers the pedestal of| hildebrand[The Problem of Form in Painting and Sculpture (Adolf von Hildebrand)]
  marching[Marching Cubes (William Lorensen, Harvey Cline)]:::visited -->|isosurface meshing for| botsch[Polygon Mesh Processing (Botsch, Kobbelt, Pauly, Alliez, Lévy)]:::visited
  pye[The Nature and Art of Workmanship (David Pye)] -.->|workmanship of risk counters| dfma
  classDef visited fill:#cfe
```

## Frontier (initial)
| Candidate | Reached via (edge label, direction) | From anchor | Status |
|---|---|---|---|
| F1 originality audit vs the reference photos | tempers strangeness of (dotted, out) | MAYA | OPEN |
| F2 blade / boom / skid slender + thickness measured | additive design rules for (out) | ISO/ASTM 52910 | OPEN |
| F3 Wayfarer roof measured before the pad spot | assembly that cannot go wrong for (in) | Poka-Yoke | OPEN |
| F4 one stem, keyed sockets, peg families | assembly that cannot go wrong for (out) | Poka-Yoke -> DFMA | OPEN |
| F5 stem as tether (pedestal into subject) | expanded field answers the pedestal of (dotted) | Krauss -> Hildebrand | OPEN |
| F6 Less Is More counter-test on the Belfry's 24 blades | less is a bore answers (dotted) | Venturi -> Mies | OPEN |
| F7 Workmanship of risk: what is allowed to be fragile | workmanship of risk counters (dotted, in) | Pye -> DFMA | OPEN |
| F8 mesh budget vs detail (pitch per part) | isosurface meshing for (out) | Marching Cubes -> Botsch | OPEN |
| F9 Specific Objects: reduce each airframe to one read | reduction precedes (out) | Brancusi -> Judd | OPEN |

## 2. Decision Records

## Move M1: Sizing drives proportion  (KEEP-THE-RULE)
Depends on: none
Anchors: Stance Make It Bigger (Paula Scher) | Rule Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | Form On Growth and Form (D'Arcy Wentworth Thompson) (morphology as parameter)
Intent: every airframe is first a plausible real aircraft (disc loading, CG, launch stroke); the miniature is that aircraft at 1:56 with heroic exaggeration only where resin demands it.
Formal argument: claim: proportions taken from physics read as "real" at arm's length and give sockets a reason to be where they are. Grounds: D'Arcy treats form as the diagram of forces; the drone_* calculators make those forces numbers. Warrant: an audience accepts a strange silhouette (advanced pole) when its masses sit where a working aircraft's would (acceptable pole).
Alternatives rejected: (a) eyeball the proportions from the reference photos: would drift toward replicas (R0 objection F1); (b) scale the Lantern Wisp up: a ducted quad scaled 2.4x is the same drone, not a heavy-lift one.
Consequence: the Angelus rotor is capped at 2.03 m by the tool's 80 in limit (tool gap, LESSONS); the Knell winglets had to grow (vertical tail volume 0.014 -> 0.023).
Fence: none broken.
Frontier effect: F10 put each flight socket on the CG; F11 rail length from the launch stroke.
Mode field: Advanced pole: original airframes whose layout follows their numbers (D'Arcy). Acceptable pole: types the eye knows (MAYA).
Geometry: spec real_world -> model: Belfry motor radius 778 mm -> 13.9 mm, prop 24 in -> 10.9 mm disc, span 38.7 mm; Angelus rotor 2.03 m -> 36.3 mm; Knell span 1.8 m -> 32.1 mm, root chord 0.82 m -> 14.6 mm, CG 762 mm aft of the nose -> model origin.
Measures: drone_propulsion_estimate (Belfry 12 x 24 in coaxial, 31 kg: disc loading 78.4 N/m2, thrust/weight 3.21, hover 21.7 min; Angelus 80 in single rotor 18 kg: 54.4 N/m2, hover 39.6 min), drone_mass_cg_budget (Belfry CG y -8.2 mm with payload, empty -8.15; Angelus CG 16.3 mm aft of the mast, inside the 25 mm tolerance), drone_fixed_wing_analysis (Knell NP 821.3 mm, static margin 0.101 at CG 762, band 733-792, L/D 13.1, stall 14.1 m/s, launch stroke 2.447 m at 12 g to 24 m/s). Source: reports/sizing.json.

## Move M2: Three Vigil silhouettes, one read each  (KEEP-THE-RULE)
Depends on: M1
Anchors: Stance Make It Bigger (Paula Scher) | Form Brancusi: The Sculpture and Drawings (Sidney Geist) -->|reduction precedes| Specific Objects (Donald Judd) | Governing MAYA: Most Advanced Yet Acceptable (Raymond Loewy)
Intent: Belfry = elongated chevron-hex hull on six arms (reads "heavy multirotor" from the top); Angelus = one smooth teardrop pod with a whip of a boom (reads "helicopter" from the side); Knell = arrowhead planform with a cigar spine (reads "loitering munition" from above). Vigil language on all three: a keel crest along the top, split-chevron lens pairs on every sensor face, chevron plan forms (Belfry hull, Angelus tail plane, Knell planform and split-chevron winglets).
Formal argument: claim: each airframe gets one dominant mass and one Vigil signature, nothing competing. Grounds: Brancusi's reduction to the essential form; Scher's scale rule (the signature large enough to read at 1 m). Warrant: tabletop reading distance demands a single silhouette per unit.
Alternatives rejected: (a) a ducted octocopter (Lantern language): would read as a big Wisp; (b) a canopied manned-helicopter look for the Angelus: misreads as crewed; (c) a straight-wing Knell: loses the arrowhead read and the KUB-quality "cropped delta" the brief asks for.
Consequence: originality audit (F1): from the ZALA we keep only qualities (teardrop pod, slender boom, two-blade exposed head, skids, chin sensor); ours: keel crest into a mast fairing hump with split-chevron intakes, chevron anhedral tail plane, swept fin with a ventral guard, the chin ball with split-chevron lenses, exhaust stub, hatch frame and panel rings. From the KUB only qualities (cropped delta, cigar fuselage, pusher, tip fins, hatches); ours: split-chevron winglets (upper up-and-out, lower down-and-out, both swept), keel spine, warhead band, chin split-chevron windows, blisters, the planform proportions from the fixed-wing tool.
Fence: none broken.
Frontier effect: F9 taken; F12 Belfry hull reads boxy in the first render (opened by the R1 panel).
Mode field: Advanced: Vigil faceting on aircraft types that are usually smooth. Acceptable: each type instantly named.
Geometry: Belfry hull rbox 8.6 x 14.6 x 3.8 mm clipped to chevron nose / tail, top deck +0.55 mm, keel crest r 0.45; Angelus pod: round cones in a 0.86-x space (7.65 x 8.9 mm at the widest), boom r 1.05 -> 0.72; Knell wing: exact planform polygon, thickness 1.75 -> 0.95 mm root to tip, blunt trailing edge >= 0.72 mm.
Measures: extents (build log), renders (build/preview, images/), slender checks on boom / wing / winglets.

## Move M3: Exposed props and separate rotors  (BREAK)
Depends on: M1, M2
Anchors: Breaker Complexity and Contradiction in Architecture (Robert Venturi) | Rule The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret) | Counterpoint Less Is More (Ludwig Mies van der Rohe) (dotted edge from Venturi: "less is a bore answers")
Intent: the Belfry shows 24 bare blades in coaxial pairs; the Angelus rotors are separate plates. The miniature rule "no fragile slender parts, duct them" (the Lantern Wisp's answer) is broken on purpose: the heavy-lift drone's honesty is its rotor stack.
Formal argument: claim: the coaxial stack is the type; ducts would erase it. Grounds: Venturi's both-and: a robust hull and a fragile rotor field in one object. Warrant: Redwood's numbers bound the risk: blades 0.84 mm (Belfry), 0.9 mm (main rotor), 0.8 mm (Knell prop) >= the 0.8 mm brief floor; rotors flat on the plate with no supports.
Alternatives rejected: (a) prop discs (solid translucent-style discs): read as toys at 1:56; (b) ducts: the Lantern answer, wrong type; (c) main rotor moulded on the airframe: a 36 mm cantilever on supports, guaranteed breakage and a support forest on the blades.
Consequence: 12 props add triangles (Belfry re-meshed to 0.1244 mm to stay under 250k); handling fragility recorded in limitations.
Fence: the rule exists because thin cantilevers snap in post-processing and cases; the fence is the measured thickness floor plus flat printing for the long rotors and mid-height pitch (10 deg) so each blade is a short root-supported plate.
Frontier effect: F2 taken (slender checks), F6 (Less Is More counter-test) opened, F7 (workmanship of risk) opened.
Mode field: Advanced: an exposed 12-prop stack at 1:56. Acceptable: blades at the brief's thickness, rotors separate and replaceable.
Geometry: aerial_kit.prop / blade: plates r0 0.4 -> 5.44 mm, chord 1.4 -> 1.0 mm, 0.84 mm thick, 10 deg pitch, upper across the arm, lower 60 deg on; main rotor plates 1.8 x 0.9 mm with 1.6 mm swept tips, hub bore 1.6 on a 1.4 pin; tail rotor 1.0 x 0.84 mm, bore 1.2 on a 1.0 pin.
Measures: miniature_slender_feature_check (blades), gap_check (blade vs arm), printability (flat pose, on_build_plate), fits (rotor vs airframe overlap, rotor-to-rotor gap).

## Move M4: The stem becomes the tether  (BREAK)
Depends on: M2
Anchors: Breaker Complexity and Contradiction in Architecture (Robert Venturi) | Counterpoint The Problem of Form in Painting and Sculpture (Adolf von Hildebrand) (dotted edge from Sculpture in the Expanded Field (Rosalind Krauss): "expanded field answers the pedestal of") | Rule Poka-Yoke -->|assembly that cannot go wrong for| Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight)
Intent: the flight stem is normally an apology (the clear rod you are asked not to see). On the tether-station base the same stem plugs into a fairlead fed by a cable spool and a generator: the support becomes the subject, a tethered observation drone.
Formal argument: claim: one part, two meanings (stem / tether) adds a variant without adding a part. Grounds: Krauss moves sculpture off the pedestal into the field; here the pedestal is narrated. Warrant: DFMA counts parts: the tethered variant costs one base and zero new airframe parts.
Alternatives rejected: (a) a separate printed cable: a second 1.6 mm wire, more parts, same look; (b) a raked flight base reused: a tethered drone hovers straight up, the rake would lie.
Consequence: the tether base is the most complex base (spool, A-frames, generator, cable run): the most triangles (re-meshed at 0.233 mm); the stem is vertical, so the Belfry centre sits 4.4 mm off the base centre (its stem socket is aft of the CG hardpoint).
Fence: Hildebrand's relief space wants the base to recede so the figure reads; the fence is height: the station tops out at 14.4 mm, the Belfry hovers above it (measured gap in fits).
Frontier effect: F5 taken; F13 ambition push (S4) on this move.
Mode field: Advanced: the base as narrative. Acceptable: still a 50 mm round magnet base with the line's deck seams.
Geometry: base-50-tether: generator 12 x 9 x 8 mm with louvres and exhaust, spool drum r 4.1 / flanges r 5.0 x 9 mm wide on A-frames, wound-cable grooves 0.44 x 0.25 every 0.9 mm, fairlead column r 2.6 to z 9.0 with a vertical 1.8 x 3.4 mm socket, 1.0 mm cable from the drum to the sheave housing, 0.9 mm power lead on the deck.
Measures: tether stack fits (Belfry offset, gap above the station), base_layout_check (two calls), printability.

## Move M5: Belfry hull to an elongated chevron-hex  (KEEP-THE-RULE)
Depends on: M2
Anchors: Form Brancusi: The Sculpture and Drawings (Sidney Geist) | Stance Make It Bigger (Paula Scher)
Intent: the R1 render showed the hull as a rounded box from above (the chevron clip planes barely cut the corners); push the clip so the plan is a pointed hexagon that echoes the six arms and points the nose.
Formal argument: claim: the plan view is the multirotor's identity view; the hull must carry the chevron there. Grounds: Brancusi's single essential contour. Warrant: Scher: if the signature does not read at table distance it is not there.
Alternatives rejected: (a) engrave a chevron on a box hull: decoration, not form; (b) a round hub (common real multirotors): loses Vigil.
Consequence: hull volume drops (measured), the chin turret sits under a narrower nose (still inside the hull at y -4.9: hull half-width there 2.4 mm).
Fence: none broken.
Frontier effect: none new.
Mode field: Advanced: a faceted hex body. Acceptable: still a symmetric multirotor hub.
Geometry: nose apex (0, -7.6), shoulders (+-4.3, -3.0); tail apex (0, 7.0), shoulders (+-4.3, 3.4); hull rbox half y 6.2 -> 7.3; top deck clipped likewise.
Measures: Belfry volume at the preview pitch 767 mm3 (0.12 mm, old hull) -> 750.8 mm3 (0.1244 mm, new hull); top-view render.

## Move M6: Payload on the CG, keyed loadouts that cannot collide  (KEEP-THE-RULE)
Depends on: M1, M3
Anchors: Rule Poka-Yoke -->|assembly that cannot go wrong for| Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | Form On Growth and Form (D'Arcy Wentworth Thompson)
Intent: two socket families on the Belfry (belly 1.6 D-flat hardpoint on the empty CG; top 1.2 D-flat mast socket); every load fits one family only, keyed forward, and is checked against the host, the skid plane and the flying stem.
Formal argument: claim: a heavy-lift drone's payload belongs on its CG (drone_mass_cg_budget: CG y -8.15 mm empty, -8.2 loaded: payload at the CG moves it 0.05 mm), and a bit that fits one hole only cannot be mis-assembled. Grounds: Poka-Yoke; D'Arcy (form as the diagram of forces). Warrant: DFMA part-count and insertion rules.
Alternatives rejected: (a) universal round pegs: bits rotate and can be fitted in the wrong socket; (b) magnetised bits: adds parts and magnets the size of the bits themselves.
Consequence: the stem socket moves aft of the hardpoint (y 4.4 vs -0.14), so the Belfry centre is offset over the base (measured); VL-04 container lowered (first draft hung 0.25 mm below the skid margin); every pylon top set exactly at the mating plane (the first assembly measured 1.877 mm3 SAR-pod interference from a pylon 0.1 mm proud).
Fence: none broken.
Frontier effect: F4 taken.
Mode field: Advanced: four belly loads and three masts on one airframe. Acceptable: one obvious socket per family, forward key.
Geometry: hardpoint boss r 1.75 to z -2.75 with a 1.6 D-flat socket 2.2 deep; mast boss r 1.5 to z 3.3 with a 1.2 D-flat socket 2.2 deep; stem boss r 1.6 with a 1.8 x 2.2 bore at y 4.4; VL-01..04 hang below z = 0 on 1.6 D-flat pegs; VL-10..12 stand on 1.2 D-flat pegs.
Measures: fits.belfry_loadouts (overlap with Belfry, gap, lowest z vs skid plane, overlap with the flying stem); miniature_base_and_peg for each peg family.

## Move M7: The launcher meets the Wayfarer without touching it  (KEEP-THE-RULE)
Depends on: M1 (rail length from the launch stroke)
Anchors: Rule Poka-Yoke | Rule Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | Counterpoint The Nature and Art of Workmanship (David Pye) (dotted edge into DFMA: "workmanship of risk counters")
Intent: one launcher, two mounts (ground tripod, vehicle roof) through one 2.0 mm D-flat peg; on the Wayfarer a glue pad carries the socket, placed where the roof is measured flat and clear.
Formal argument: claim: the interface is a documented surface contract, not an edit to another package. Grounds: Poka-Yoke (the D-flat key fixes the launch direction); DFMA (one peg, two hosts). Warrant: the brief forbids editing wayfarer-apc/.
Alternatives rejected: (a) ask the owner to drill a 2.0 mm hole in the roof: an unmeasured instruction, risk to a finished model; (b) a launcher with a clamp shaped to the roof edge: couples the launcher to one hull revision.
Consequence: the pad adds 4.0 mm under the launcher (the launcher flange sits on the pad boss); the RWS can no longer traverse through the whole circle (measured arc in fits).
Fence: none broken; Pye's workmanship of risk is acknowledged by leaving the final placement to the owner's glue, with the measured spot as the default.
Frontier effect: F3 taken; F14 RWS traverse limit to document.
Mode field: Advanced: a roof-launched loitering munition on an existing APC. Acceptable: no change to the APC.
Geometry: roof pad 10 x 5.8 x 1.2 mm (first draft 10 x 10 at (40.0, -12.5): over the louvres, see R2), boss r 2.4 to z 4.0, through 2.0 D-flat socket; Wayfarer placement (x 44.0, y -12.0, z 38.5), launcher -y -> Wayfarer +x; rail 46.4 mm at 12 deg, pivot 8.2 mm, shuttle at s -21.6 mm.
Measures: fits.wayfarer_roof (roof heights under the pad by ray cast, overlaps with hull and RWS, RWS yaw sweep 0-355 deg in 5 deg steps), fits.knell_on_launcher.

## Move M8: Ambition push on M4: the ground station takes the masts too  (BREAK)
Depends on: M4, M6
Anchors: Breaker Complexity and Contradiction in Architecture (Robert Venturi) | Counterpoint The Problem of Form in Painting and Sculpture (Adolf von Hildebrand) (via Sculpture in the Expanded Field (Rosalind Krauss), dotted) | Rule Poka-Yoke
Intent: the boldest move (the stem as tether) pushed one step: the tether station's generator roof gets the Belfry's own mast socket family (1.2 mm D-flat), so the relay or radar mast can stand on the ground station while the drone is up. The base is no longer a stand: it is the second half of the system.
Formal argument: claim: reusing a socket family turns a base into a host without a new part. Grounds: Krauss (the field, not the pedestal); Poka-Yoke (same family, same key: no new way to go wrong). Warrant: DFMA: zero new parts, one new feature.
Alternatives rejected: (a) a dedicated ground-radar bit: one more part for the same read; (b) leave the station as scenery: the push asked by S4 would not exist.
Consequence: the station's tallest point rises (VL-12 on the roof); it must stay clear of the tethered Belfry overhead (measured).
Fence: Hildebrand's fence (the base must not compete with the figure) is held by height: the mast stays below the hovering drone's skids with a measured gap.
Frontier effect: none new; F13 taken.
Mode field: Advanced: a base that is a functioning ground station host. Acceptable: one more socket of a family the player already knows.
Geometry: boss r 1.5 x 0.8 mm on the generator roof at (gc + (-3.6, -2.6)), 1.2 D-flat socket 2.2 mm deep (0.1 mm clearance per side).
Measures: fits.belfry_tethered_station_masts (overlap with station and tethered Belfry, gap to the Belfry, mast top z), miniature_base_and_peg (mast peg in a 3.0 mm boss), printability of base-50-tether.

## 3. Panel Reports

Panel seats (Adaptive): Critic: Provocateur (Debord), Critic: Provocateur (Shklovsky), Critic: Inclusion (Holmes),
Critic: Inclusion (Mace), Critic: Usability (Krug) [dotted pair: Critic: Provocateur (Shklovsky) -.->|attacks smoothness
favored by| Critic: Usability (Krug)], Critic: Human Scale (Dreyfuss), Critic: Data Gap (Criado Perez), Form seats
Critic: Essential Form (Brancusi) and Critic: Expanded Field (Krauss), fabrication seats Critic: Manufacturability
(Boothroyd) and Critic: Manufacturability (Dewhurst), geometry seat Critic: Mesh Quality (Botsch). Each report was written
in full before the next (no per-reference agents were spawned; see Compliance Check).

### Panel, WHOLE (M1-M4 first sculpts), round R1  (artifact examined: build/preview/{belfry,angelus,knell,launcher-rail,launcher-tripod,roof-pad,vl-*,base-50-stem}.png at 0.12 mm pitch)
| Critic | Anchor used | Observed in the work | Verdict | Requested change |
|---|---|---|---|---|
| Provocateur (Debord) | The Society of the Spectacle (Guy Debord) | Knell 3/4 view: arrowhead + cigar + pusher is the KUB's spectacle silhouette | PASS | keep the split-chevron winglets visible; they are what is ours |
| Provocateur (Shklovsky) | Art as Technique (Viktor Shklovsky) | Angelus side view: smooth teardrop, nothing strange | OBJECT | make one Vigil element strange enough to stop the eye (chevron tail plane in front view, split-chevron intakes on the hump) |
| Inclusion (Holmes) | Mismatch (Kat Holmes) | rotors are separate 36 mm plates; a player with low dexterity must thread a 1.6 bore onto a 1.4 pin | PASS | state in buildNotes that rotors may be glued at any angle |
| Inclusion (Mace) | Universal Design principles (Ronald Mace) | one stem length for all flyers (38 mm) | PASS | none |
| Usability (Krug) | Don't Make Me Think (Steve Krug) | four peg families on small bits | PASS | engrave the launch direction on the roof pad (done: chevron arrow) |
| Human Scale (Dreyfuss) | Designing for People (Henry Dreyfuss) | Belfry 38.7 mm span vs a 30 mm trooper: a heavy-lift drone ~1.3 m tall figure-equivalent | PASS | none |
| Data Gap (Criado Perez) | Invisible Women (Caroline Criado Perez) | the roof pad placement is chosen from a roof grid but the RWS sweep is not yet measured | OBJECT | measure the RWS traverse against the launcher + Knell before calling the interface done |
| Essential Form (Brancusi) | Brancusi: The Sculpture and Drawings (Sidney Geist) | Belfry top view: hull reads as a rounded box among six arms | OBJECT | give the hull one essential contour (chevron-hex) |
| Expanded Field (Krauss) | Sculpture in the Expanded Field (Rosalind Krauss) | base-50-stem: generic chevron deck, the base says nothing | PASS | the tether base answers this for one variant (M4) |
| Manufacturability (Boothroyd) | Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | VL-04 preview bottom z -4.25 mm: on the hardpoint (boss z -2.75) it would hang to -7.0, the skid plane | OBJECT | raise the container: lowest point >= skid plane + 0.5 |
| Manufacturability (Dewhurst) | Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | base-50-stem preview: 710k triangles at 0.12 mm for a flat disc | OBJECT | re-pitch bases from the triangle budget |
| Mesh Quality (Botsch) | Polygon Mesh Processing (Botsch, Kobbelt, Pauly, Alliez, Lévy) | marched meshes watertight, one body (Package refuses otherwise) | PASS | none |
Statements of meaning: three aircraft that share a family face (keel, split chevrons) and three different jobs; the tether base turns the stand into the story.
Artist questions: does the Angelus read as original next to the ZALA photo? Is the Belfry's blade field too busy?
Critic questions: (Criado Perez) where exactly does the RWS sweep? (Boothroyd) what is the lowest point of each load when mounted?
Opinions: see table.
Andon pulled: no.
Resolution: Shklovsky OBJECT -> OVERRULE with a measurement-free reason under MAYA? No: ADAPT accepted in part: the chevron anhedral tail plane and the split-chevron intakes were already in the sculpt but too small to see in the 380 px preview; verified in the 520 px Angelus front view (images/vigil-aerial-angelus.png) and kept; no geometry change (logged as inert request). Brancusi -> M5 (ADAPT). Boothroyd -> VL-04 container lowered (part of M6). Dewhurst -> base pitch 0.2 / 0.18 / tether 0.16 start (mesh_in_budget took it to 0.233). Criado Perez -> F14, measured in M7 fits.

### Panel, WHOLE (M1-M7 built), round R2  (artifact examined: images/vigil-aerial-{hero,turnaround,belfry,angelus,knell,launcher-wayfarer,loadout,bases}.png; reports/build.json fits from the reuse build)
| Critic | Anchor used | Observed in the work | Verdict | Requested change |
|---|---|---|---|---|
| Provocateur (Debord) | The Society of the Spectacle (Guy Debord) | hero: the launcher group in front of the Belfry base reads as clutter, the spectacle is the scene not the aircraft | OBJECT | hero = the four flyer stacks only; launcher in its own images |
| Provocateur (Shklovsky) | Art as Technique (Viktor Shklovsky) | Angelus front view: the chevron anhedral tail plane and the hump's split-chevron intakes now read; tether station reads as a story | PASS | push the strangest idea further (S4) |
| Inclusion (Holmes) | Mismatch (Kat Holmes) | bits peg in from below / above; D-flat keys forward | PASS | none |
| Inclusion (Mace) | Universal Design principles (Ronald Mace) | one stem, four uses | PASS | none |
| Usability (Krug) | Don't Make Me Think (Steve Krug) | the roof pad's chevron shows the launch direction | PASS | none |
| Human Scale (Dreyfuss) | Designing for People (Henry Dreyfuss) | Belfry flies 28.3 mm over its base, Angelus 28.3, Knell 31.3; tops at 45.5 / 55.3 / 46.9 mm: within a figure case's 60 mm | PASS | none |
| Data Gap (Criado Perez) | Invisible Women (Caroline Criado Perez) | roof under the pad measured 37.9..38.5 mm: a 0.6 mm "dip" nobody saw in the 4 mm grid; RWS sweep blocked at 220-245 and 325-335 deg | OBJECT | resolve the dip (artifact or real) before gluing advice; publish the RWS limit |
| Essential Form (Brancusi) | Brancusi: The Sculpture and Drawings (Sidney Geist) | Belfry top view: chevron-hex hull now reads among the arms | PASS | none |
| Expanded Field (Krauss) | Sculpture in the Expanded Field (Rosalind Krauss) | tether station: spool, generator, fairlead | PASS | let the station host something (S4 push) |
| Manufacturability (Boothroyd) | Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | interference: VL-02 SAR pod overlaps the Belfry 1.79 mm3 after the pylon fix: its radome reaches the chin turret | OBJECT | keep the pod between the chin turret and the flying stem |
| Manufacturability (Dewhurst) | Product Design for Manufacture and Assembly (Geoffrey Boothroyd, Peter Dewhurst, Winston Knight) | VL-04 container front at y -3.54 is 0.32 mm from the chin ball | OBJECT | shorten the container |
| Mesh Quality (Botsch) | Polygon Mesh Processing (Botsch, Kobbelt, Pauly, Alliez, Lévy) | fits report "main rotor disc 31.92 mm": a projected extent of the rotated rotor, not the disc (36.28) | OBJECT | measure the unrotated part |
Statements of meaning: the family reads; the station tells a story; the remaining faults are fits, not form.
Artist questions: is the roof dip real? Is the RWS limit acceptable?
Critic questions: (Boothroyd) why did the pylon fix not remove the overlap? (answer: the overlap was the radome vs the chin ball, a second cause).
Opinions: see table.
Andon pulled: no.
Resolution: Debord -> hero filter (ADAPT). Criado Perez -> the dip is real. A 1 mm integer grid (build/probe_roof.py) saw only 38.50, which first suggested a ray artifact (the measurement was switched to the topmost hit per ray and still read 37.9); a 0.25 mm grid (build/probe_seam.py, probe_free.py) found the Wayfarer's engine-deck louvre slots, 0.5 mm wide x 0.6 mm deep at x 36.5 / 38.5 / 40.5 for y -14.25..-7, exactly under the first pad spot. The integer grid had stepped over every slot (slots on half-millimetres): the Data Gap objection caught a sampling error, not a hull error. Fully flat 10 mm squares exist only at x 22-25 (the launcher's rear and the Knell would then sit over the RWS), so the pad was re-shaped to 10 x 5.8 mm and moved to the flat strip x 41..47 between the louvres and the glacis, centre (44.0, -12.0) (ADAPT, M7 consequence); the roof check is now "fraction of samples at the 38.5 plane >= 0.98 and nothing above it". RWS limit published in buildNotes and the Compliance Check. Shklovsky / Krauss -> M8 (S4 push). Boothroyd / Dewhurst -> SAR pod and cargo pod re-shaped (ADAPT, M6 consequence). Botsch -> metric fixed (ADAPT).
