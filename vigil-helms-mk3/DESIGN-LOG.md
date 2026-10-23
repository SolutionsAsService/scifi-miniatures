# VH3 Vigil helm library Mk 3: DESIGN-LOG (3dada, Adaptive mode)

Working notes from the earlier (crashed) runs: build/NOTES-progress.md (untracked dev file, folded in here).

## 1. Traversal Plan
Brief: eight distinct, printable 30 mm-heroic helm bits (VH3-01..08) for the Vigil line that read apart at arm's length.
Mode: Adaptive (product for a hobby audience; MAYA governs). 3D frame: SDF sculpt (tools/helms3.py, sdfkit) marched to
polygon meshes, MSLA resin, units mm, +z up, STL only (STEP skipped: no FreeCAD on host). Hard limits (miniature_* MCP
checker): supported wall >= 0.4 mm over <= 0.5 mm2, gaps >= 0.5 mm over <= 1.0 mm2, one clean shell, <= 300 k tris.
Seed: Stance "Make It Bigger (Paula Scher)"; Rules "Gestalt Principles of Perception (Wertheimer, Koffka, Köhler)",
"The 3D Printing Handbook (Ben Redwood, Filemon Schöffer, Brian Garret)", "Architecture: Form, Space, and Order
(Francis D. K. Ching)"; Breaker "Complexity and Contradiction in Architecture (Robert Venturi)"; Counterpoint "The Vignelli
Canon (Massimo Vignelli)" (dotted from Scher). Tooling: unified-CAD-MCP miniature_* tools in-process (tools/cachedcheck.py,
cached per STL sha), tools/morph.py, tools/thindiag.py; renders tools/render.py; no graph tool (Mermaid text omitted).

## Frontier
| Candidate | Reached via | From anchor | Status |
|---|---|---|---|
| distinct silhouettes (M1-M2) | grounds | Gestalt | TAKEN (M1, M2) |
| knife lips / slivers hand fixes | grounds | 3D Printing Handbook | TAKEN (M3, M4) - SCRAPPED as a method |
| morphological print-safety filter | grounds | 3D Printing Handbook | TAKEN (M5) |
| helm fit on rifleman figure | extends | Ching (massing) | DEFERRED (fit against rifleman Mk2 not re-run this round; interference none in assembled build) |

## 2. Decision Records
- M1 blockout (KEEP-THE-RULE), M2 escalation (BREAK, Scher/Venturi), M3-M4 hand fixes: see NOTES-progress; measured
  distinctness mean 0.097 -> 0.150, min pair 0.009 -> 0.134. M3/M4 reduced supported thin area only to 1.7-8.6 mm2.
- M5 morph filter (KEEP-THE-RULE: Redwood et al.). Depends on M1-M4. Intent: every helm printable without erasing the
  silhouette work. Argument: an opening by a 0.25 mm ball leaves only material that holds a 0.5 mm ball (> 0.4 limit);
  a 0.26 mm closing fills slots < 0.52 mm. Alternatives rejected: (a) keep hand-fixing (did not converge in 3 rounds);
  (b) uniform offset +0.2 mm (fattens every face, kills engraved detail, volume +15 %). Consequence: convex edges round
  to 0.25 mm, -0.4..-2.8 mm3 per helm. Fence: Vignelli counterpoint - discipline by one global rule, not 30 local ones.

## 3. Panel Report (R4, inline, 4 seats)
- Manufacturability (Boothroyd): one rule, one pass, measured pass on every part - accept.
- Mesh Quality (Botsch): 160-185 k tris marched at 0.05 mm, no decimation, one manifold shell each - accept.
- Relief and Volume (Hildebrand): 0.25 mm edge rounding keeps plane reading at 30 mm; deep vents survive (>0.52 mm) - accept.
- Provocateur (Shklovsky): the morph rounds the Grimward's shattered fin a little; still the most jagged read - minor, accept.

## 4. Anchor Ledger
Scher (M2), Gestalt (M1), Arnheim/Hildebrand (M2, R4), 3D Printing Handbook (M3-M5), Ching (M1), Venturi (M2, BREAK),
Vignelli (M5 counterpoint), Loewy MAYA (governing).

## 5. Compliance Check
See "R4 measured" below. Stop conditions: printability PASS on all eight parts with no open Andon objection.
Skipped: Mermaid graph render, branch spikes for M5, re-fit on rifleman (deferred).

## R4 measured (tools/cachedcheck.py -> miniature_printability_check / gap_check / shell_audit on print/stl, print pose)
| Part | Min wall mm (point) | Supported thin area mm2 (<=0.5) | Narrow-gap area mm2 (<=1.0) | Smallest gap mm (point) | Shells / clean | Resin ml |
|---|---|---|---|---|---|---|
| VH3-01 Plummet | 0.495 | 0 | 0 | 0.593 | 1 / yes | 0.125 |
| VH3-02 Sightline | 0.546 | 0 | 0 | 0.540 | 1 / yes | 0.118 |
| VH3-03 Ironclad | 0.543 | 0 | 0.547 | 0.331 | 1 / yes | 0.130 |
| VH3-04 Herald | 0.495 | 0 | 0.111 | 0.114 | 1 / yes | 0.119 |
| VH3-05 Stillwater | 0.531 | 0 | 0.006 | 0.253 | 1 / yes | 0.123 |
| VH3-06 Deckhand | 0.400 | 0 | 0.698 | 0.034 | 1 / yes | 0.094 |
| VH3-07 Longsight | 0.546 | 0 | 0.087 | 0.389 | 1 / yes | 0.128 |
| VH3-08 Grimward | 0.044 | 0.020 | 0.358 | 0.012 | 1 / yes | 0.118 |
Result: PASS, all eight (watertight manifold, one shell each, 160-183 k tris). Point minima below the limit are
single-ray contacts in inside corners (area-weighted metrics are the pass criteria); Grimward's 0.02 mm2 is a fin notch root.
Stop conditions met. Open: re-fit on rifleman Mk2 figure (deferred, not a printability item).
