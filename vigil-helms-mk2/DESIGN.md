# VH2: the Vigil helm, Mk 2 — design notes

The second-generation helm profile of the Aster Compact Vigilants. The 0.1 helm library (\`vigil-helms\`, VH-01..10) is
untouched; VH2 is a new library alongside it, and \`vigil-rifleman-vh2\` (revision 0.3) is the rifleman wearing the new line
helm. Code: \`tools/vh2.py\` (registry \`VH2\`), package builder \`tools/bitspack.py\`, display sheets \`source/sheet.py\`.

## Brief

Redo the Vigil helm with more detail and a refreshed signature profile: layered shell plates over a skull dome, a wide
wrap-around faceted visor, cheek/jaw guards with vent grilles, respirator mouth, aural housings with tubes, brow ridge,
side lamps/sensors, antenna — ~12 variants on the line's 1.6 mm D-flat peg, at 30 mm heroic (helm about 5.7 mm wide).
The owner's references (space-marine helmet, ODST evolution chart, Halo helmets) are inspiration only.

## The signature profile

| Element | VH-01 (0.1) | VH2 |
|---|---|---|
| Visor | two small lens slots in a V (split chevron) | **gull-wing wrap visor**: one faceted visor that wraps ±65° round the dome; its wings rise and sweep back to the temples while the lower edge drops into a V at the centre; split by the keel bar |
| Glass | flat recess | 0.38 mm recess with an upper facet 0.17 mm proud of the lower one, inside a raised 0.26 mm frame |
| Keel | crest tube over the dome | **one keel line**: crest (0.6 mm) from the nape over the crown, down through the visor split (0.54 mm bar) onto the V-prow and the chin puck |
| Shell | smooth egg | **layered**: crown plate 0.25 mm over temple plates 0.13 mm over the skull, two stepped nape tiers (0.20 / 0.34 mm); the crown plate's front edge is the brow and follows the visor's top edge with a 0.38 mm shadow gap |
| Mouth | muzzle with 3 slots a side | **faceted V-prow** respirator, two rows of chevron vent slots (12°) echoing the visor's lower edge, chin puck |
| Sides | ear pods with swept fins | cheek guards with three vertical vent slots; aural housings with a recessed disc and centre stud; breather hose from ear to jaw |

### How it differs from the references

- **ODST / Halo** visors are a single rounded trapezoid or band with a flat or gently arched top edge, never split; the
  Spartan visor is one gold bubble. VH2's visor is split by a keel bar, and its top edge *rises* outward (gull wing)
  while its bottom edge falls to a centre V — the opposite rhythm of a flat-topped band.
- The **space-marine** helm has two separate round eye lenses and a beaked, steeply slotted grille. VH2 has one
  continuous wrap visor, a shallow faceted prow (31° facets, 12° vents) with a round chin puck, and the keel line that
  runs unbroken from crest to chin; it carries no faction iconography (no aquila, crosses or skulls as marks).
- None of the references uses the crown/temple/nape plate stack with the brow as the crown plate's edge, nor the
  rising-tip wing.

## Variants

| Id | Name | Role | What changes |
|---|---|---|---|
| VH2-01 | Lineguard | line trooper | the signature profile; lamp on the right temple, aerial stub left rear |
| VH2-02 | Tidewall | sealed void / EVA | sealed pane bulged 0.16 mm in a 0.42 mm frame, smooth sealed jaw, collar seal ring with four lugs, life-support hoses from the jaw corners to the nape, purge valve, rear O2 port, twin antenna stubs |
| VH2-03 | Lookout | recon | hinged optic stalk (0.64 mm) from the left temple to a 1.24 mm monocular with a focus ring resting on the left wing; whip antenna right |
| VH2-04 | Bastion | heavy | thicker crown/temple plates, narrowed armoured visor under a brow bar, heavy prow with three raised respirator slats, twin filter cans |
| VH2-05 | Marshal | sergeant / warden | swept keel blade crest (0.76 mm thick, rising to 2 mm above the crown at the back), command antenna, lamp, two rank bars |
| VH2-06 | Mender | medic | crown stripe channels either side of the crest (for paint), triage scanner bar with three lenses on the right brow, twin forward filters, rear beacon dome |
| VH2-07 | Wright | engineer | brow headlamp, flip-up magnifier goggles on a strap that hugs the dome, lamp cable along the crown line, tool port |
| VH2-08 | Plumb | marksman | stereo rangefinder on a hinge over the right wing with an eyepiece hood, flat stock-weld pad on the left cheek |
| VH2-09 | Kite | pilot / crew | sealed smooth jaw, stowed sun shade (the visor shape rotated up 34° on hinge arms), big ear cups, boom mic, oxygen hose |
| VH2-10 | Provost | officer, open face | face opening with a stylised face (brow, nose, eye sockets, cheekbones, chin), gull-wing visor flipped up 48° onto the brow on arms, chin strap, short blade crest, rank plate |
| VH2-11 | Lineguard, scarred | battle-damaged line | claw gouges over the left crown, gouge on the right side, crest notch, four pits, shattered left wing with a lost shard from the frame |
| VH2-12 | Bastion, breached | battle-damaged heavy | gash across the crown, torn respirator corner, sheared filter can, crest bitten through, five pits, cracked visor |

## Geometry and printing

- Frame: neck cut at z = 0, helm centre 2.8 mm above it, helm scale HS = 1.12, faces −y; the 1.6 mm D-flat peg is
  \`exosuit.PEG_HEAD\` — the same peg as VH-01..10, so every VH2 helm fits every Vigil figure and vice versa.
- Visor outlines are polygons in (arc length, height) helm units, wrapped round the skull axis (\`vh2.wrap_prism\`),
  so the wings follow the dome instead of being projected flat from the front.
- Feature floor (MSLA resin): raised details ≥ 0.5 mm wide; slots 0.30 mm wide, 0.25–0.38 mm deep, pitch 0.68 mm
  (ribs ≥ 0.38 mm); antennas 0.76 mm diameter with a 1.0 mm ball tip; blade crests 0.72–0.76 mm thick.
- Sculpted on a 0.05 mm signed-distance grid, one helm per child process (peak ≈ 0.6 GB), marched to one closed manifold
  body; print files are not decimated (≤ 200 k triangles; viewer/STEP copies are).
- Printed upright on the peg with light supports (as the VH-01..10 library).

PRINTABILITY_PLACEHOLDER

## Process (3dada, abbreviated)

Mode: Adaptive (the work serves the owner's figure line and a tabletop audience). 3D frame: resin miniature parts, SDF →
mesh, MSLA, mm, z up, STL + faceted STEP; limits 0.4 mm supported wall, 0.6 mm unsupported, 0.3 mm wire, 1.6 mm peg.
Moves (each rendered from four views and looked at before the next):

1. **M1 Gull-wing visor (BREAK of the split chevron).** First render: the visor read as a flat band. Measured lever:
   raising the wing tips (z 0.98 → 1.12 helm units), dropping the centre top (0.42 → 0.30) and opening a 0.38 mm shadow
   gap between frame and brow made the gull-wing silhouette read in the front view.
2. **M2 Mouth rhythm.** The first V-prow with 25° slots read close to the space-marine grille; the slots were flattened
   to 12° and moved outboard so the round chin puck and the keel carry the face.
3. **M3 Variant reads.** Lookout's first monocular (1.0 mm) vanished against the visor frame → 1.24 mm barrel with a
   focus ring. Marshal's first crest leaned forward as a block → profile redrawn to sweep up and back. Wright's lamp
   cable left the skull (a point placed above the dome) and its goggle strap was a torus floating off the back → cable
   on the mid-plane (\`crest_pt\`), strap as a band cut from the skull offset. Tidewall's three chin pucks read as a face
   → hose sockets moved to the jaw corners and the pane bulged.
4. **M4 Damage depth.** The first gouges cut 0.02 mm above the skull and so missed the 0.25 mm crown plate entirely
   (invisible in the render); re-placed relative to the plate (0.3 mm out, r 0.26–0.32 mm) they read.

Panel: run as a written self-critique against the renders (no sub-agent panel was convened — stated, not claimed).
Open items: the officer's face is a mask-level read at this scale; the line helm's visor depends on paint (the display
sheets tint the glass) more than on depth.
