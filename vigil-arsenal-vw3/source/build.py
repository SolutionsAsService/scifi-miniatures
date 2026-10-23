#!/usr/bin/env python3
"""Vigil arsenal VW3: loose bits package from tools/arsenal3.py (WEAPONS3 guns + BLADES3 power blades), plus images.

Run with the sculpt venv (numpy, scikit-image, trimesh, manifold3d, pillow):
    ~/projects/venvs/scifi-sculpt/bin/python source/build.py            (all parts, then the display sheets)
    ~/projects/venvs/scifi-sculpt/bin/python source/build.py --sheets   (re-render the display sheets only)
    ~/projects/venvs/scifi-sculpt/bin/python source/build.py VW3-01 ... (rebuild only these parts' upright STLs)

Each part is meshed on its own grid at spec voxel_mm (0.05 mm); if a part is over the checker budget the SDF is
RE-MESHED COARSER (arsenal3.sculpt_fit) - print meshes are never decimated. The viewer JSON uses manifold3d
simplification (preview only). STEP: FreeCAD is not available on this host, so sdfkit.write_step is replaced by a
note writer and reports/build.json records the STEP as SKIPPED.
"""
import json
import sys
import time
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

import arsenal3 as A3  # noqa: E402
import sdfkit  # noqa: E402
from render import render  # noqa: E402
from sdfkit import Package, decimate, translate  # noqa: E402

SPEC = json.loads((PKG / "spec" / "vigil-arsenal-vw3.spec.json").read_text())
COLORS = {"VW": "#4d5257", "VB": "#7a8088"}
STEP_NOTE = ("STEP SKIPPED: FreeCAD is not installed on this build host (WSL, no FreeCAD / freecad-shim), so the faceted "
             "reference STEP that tools/sdfkit.write_step makes through FreeCAD could not be written. The print STLs in "
             "print/stl/ and build/upright/ are the deliverable; re-run source/build.py on a host with FreeCAD for a STEP.")


def _skip_step(path, parts):
    Path(str(path) + ".SKIPPED.txt").write_text(STEP_NOTE + "\n")


sdfkit.write_step = _skip_step


def slug(ident, name):
    return f"{ident.lower()}-{name.lower().replace(',', '').replace(' ', '-')}"


def items():
    return [(k, v[0], v[1]) for k, v in list(A3.WEAPONS3.items()) + list(A3.BLADES3.items())]


def at(i, ident):
    if ident.startswith("VW3"):
        return (0.0, -i * 7.0, 0.0)                     # one gun per row, muzzles to +x
    j = int(ident[-2:]) - 1
    return (-16.0 + j * 7.5, -len(A3.WEAPONS3) * 7.0 - 4.0, 0.0)   # blades stand in a row below


def build(only=None):
    up = PKG / "build" / "upright"
    up.mkdir(parents=True, exist_ok=True)
    k = Package(SPEC["id"], PKG)
    plan, pitches, meshlog = [], {}, {}
    for i, (ident, name, note) in enumerate(items()):
        stl = slug(ident, name)
        t = time.time()
        if only and ident not in only and (up / f"{stl}.stl").exists():
            mesh = trimesh.load(up / f"{stl}.stl", process=False)
            pitch = json.loads((PKG / "reports" / "build.json").read_text())["voxel_mm"][stl]
        else:
            mesh, pitch = A3.sculpt_fit(A3.item(ident), f"{ident} {name}", SPEC["voxel_mm"], SPEC["max_print_triangles"],
                                        open_r=SPEC["opening_r_mm"].get(ident[:3]), log=meshlog)
        pitches[stl] = pitch
        k.add(f"{ident} {name}", mesh, stl=stl, color=COLORS[ident[:2]], group=stl, note=f"{ident} {name}: {note}",
              explode=(0, 0, 4), placement=translate(*at(i, ident)))
        plan.append({"stl": stl, "label": f"{ident} {name}", "plan": False})
        print(f"{ident} {name}: {len(mesh.faces)} tris at {pitch} mm, {time.time() - t:.0f} s", flush=True)
    rep = k.write()
    rep["voxel_mm"] = pitches
    rep["mesh_log"] = meshlog
    rep["print_mesh_policy"] = ("marching cubes at the listed pitch after a morphological opening of the SDF grid (guns: ball "
                                "r 0.22 mm, arsenal3.open_slivers; blades: none), largest body kept (sub-0.05 mm3 dust dropped), no decimation")
    rep["step"] = {"file": None, "status": "SKIPPED", "reason": STEP_NOTE}
    (PKG / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    (PKG / "build" / "parts-plan.json").write_text(json.dumps(plan, indent=1))
    out = PKG / "images"
    out.mkdir(exist_ok=True)
    meshes = [(decimate(p["asm"], 25_000), p["color"]) for p in k.parts]
    render(meshes, out / f"{SPEC['id']}-hero.png", views=((-32, 18, "3/4 front"),), size=1000)
    return rep


if __name__ == "__main__":
    import sheet
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--sheets" not in sys.argv:
        build(set(args) or None)
    print(sheet.sheets(sheet.load_items()))
