# Sci-fi Miniatures: the Vigil

Original 3D-printable sci-fi miniatures, generated in code and checked for resin printing.

## The faction

**The Vigil** are the power-armoured line infantry of the Aster Compact, a frontier alliance that keeps watch over
its colonies from orbit. Each Vigilant wears a sealed exosuit with a split chevron visor and a keel-crested helm,
carries a compact bullpup rifle and a spine power pack, and fights in small, disciplined fireteams. The design is
original: no helm, pauldron or weapon is copied from an existing game or film.

## Scale and process

- **Scale:** 30 mm heroic (1:56), measured soles to visor line; about 32.5 mm to the crown. Heroic proportions:
  oversized hands, helm and weapon so details survive printing and handling.
- **Process:** MSLA resin (8K 7-inch class). Every part is screened with the unified-CAD-MCP `miniature_*` tools on
  the `msla_resin` preset (minimum wall, islands, suction cups, support plan).
- **Assembly:** figure with an integral footplate that drops into a keyed recess on a separate 32 mm base with a
  5 × 2 mm magnet pocket; helm and backpack plug in on D-flat pegs and swap across the whole line.

## Miniatures

| Id | Name | Family |
|---|---|---|
| [`vigil-rifleman`](vigil-rifleman/) | Vigilant Rifleman, advancing | Troopers |

More figures (heavy weapons, warden) are in progress on the `wip/vigil-1` branch.

## Package format

Same format as the fantasy line (SolutionsAsService/fantasy-miniatures); one folder per miniature:

| Path | What it is |
|---|---|
| `mini.json` | Viewer catalogue entry (`"line": "scifi"`, family, images, scale, resin volume, printability verdict). |
| `spec/<id>.spec.json` | Every dimension and the pose; the generator reads nothing else. |
| `source/build.py` | Sculpt generator: writes `build/upright/*.stl`, `cad/<id>-assembly.step`, `viewer/<id>.parts.json`, `reports/build.json`, `images/`. |
| `source/check.py` | Printability checks (unified-CAD-MCP): writes print-pose STLs in `print/stl/` (+ `.meta.json`), `reports/printability.{json,md}` and `mini.json`. |
| `print/stl/` | The files to slice, already in their print orientation. |
| `images/` | Renders listed in `mini.json`. |

Shared code is in `tools/`: `sdfkit.py` (signed-distance sculpting and export), `exosuit.py` (the Vigil armour kit),
`vigil.py` (package builder), `render.py` (turntable renders), `mcpcheck.py` / `checkplan.py` (print checks).

Rebuild one miniature:

```sh
cd vigil-rifleman
/mnt/d/ai-stack/venvs/scifi-sculpt/bin/python source/build.py
PYTHONPATH=<unified-CAD-MCP>/src <unified-CAD-MCP venv>/bin/python source/check.py
```

Printability is a heuristic screen, not a test print; print a tolerance coupon first.
