#!/usr/bin/env python3
"""Vigil helm library Mk 3 (VH3): bits package from tools/helms3.py.

Run: ~/projects/venvs/scifi-sculpt/bin/python source/build.py [VH3-01,VH3-05 ...]
Writes build/upright/*.stl (print meshes, NOT simplified: marched on the spec's grid and asserted one closed manifold
body under the checker's 300 k triangle limit), build/glass/*.npy (display masks), viewer/vigil-helms-mk3.parts.json,
reports/build.json, build/parts-plan.json, images/ (hero + turnaround from tools/vigil.py, display sheets).
STEP: sdfkit.write_step needs a FreeCAD Python; none exists on this host (no FreeCAD in WSL, no shim), so the STEP
export is recorded as skipped in reports/build.json instead of failing the build.
"""
import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np
import trimesh

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import helms3  # noqa: E402
import sdfkit  # noqa: E402
import sheet  # noqa: E402
from vigil import build_loose  # noqa: E402

SPEC = json.loads((PKG / "spec" / "vigil-helms-mk3.spec.json").read_text())
STEP = {"status": "skipped"}


def _no_step(path, parts):
    """Stand-in for sdfkit.write_step when no FreeCAD Python is available."""
    py = os.environ.get("FREECAD_PYTHON")
    if py and Path(py).exists():
        import freecadshim
        os.environ["FREECAD_PYTHON"] = py
        freecadshim.use()
        STEP.update(status="written", python=py)
        return _orig_step(path, parts)
    STEP.update(status="skipped", reason="no FreeCAD Python on this host (WSL without FreeCAD; $FREECAD_PYTHON unset)")


_orig_step = sdfkit.write_step
sdfkit.write_step = _no_step


def slug(k):
    return f"{k.lower()}-{helms3.VH3[k][0].lower()}"


def _mesh(k, h, tri_cap):
    g = helms3.helm(k, h)
    m = g.mesh(k, None)                                     # no simplification of the print mesh
    if len(m.faces) > tri_cap:
        raise SystemExit(f"{k}: {len(m.faces)} triangles > {tri_cap}: coarsen voxel_mm instead of decimating")
    mask = helms3.glass_mask(g.glass, m.triangles_center)
    return m.vertices, m.faces, mask


def mesh_in_child(k, h, tri_cap):
    """One helm per fresh process (numpy peaks stay per helm)."""
    with mp.get_context("spawn").Pool(1) as pool:
        v, f, mask = pool.apply(_mesh, (k, h, tri_cap))
    m = trimesh.Trimesh(v, f, process=False)
    return m, mask


if __name__ == "__main__":
    want = sys.argv[1].split(",") if len(sys.argv) > 1 else list(helms3.VH3)
    h, cap = SPEC["voxel_mm"], SPEC["max_triangles"]
    (PKG / "build" / "glass").mkdir(parents=True, exist_ok=True)
    parts, plan, rows = [], [], {}
    for i, k in enumerate(want):
        name, note, _ = helms3.VH3[k]
        m, mask = mesh_in_child(k, h, cap)
        np.save(PKG / "build" / "glass" / f"{slug(k)}.npy", mask)
        at = ((i % 4 - 1.5) * 9.0, -(i // 4) * 11.0, 0.0)
        parts.append((f"{k} {name}", m, slug(k), "#6f7a83", f"{k} {name}: {note}", at))
        plan.append({"stl": slug(k), "label": f"{k} {name}", "plan": True})
        rows[slug(k)] = {"triangles": len(m.faces), "glass_faces": int(mask.sum()),
                         "glass_area_mm2": round(float(m.area_faces[mask].sum()), 2)}
        print(f"{k} {name}: built {len(m.faces)} triangles", flush=True)
    rep = build_loose(PKG, SPEC, parts)
    (PKG / "build" / "parts-plan.json").write_text(json.dumps(plan, indent=1))
    rep = json.loads((PKG / "reports" / "build.json").read_text())
    rep["step"] = {"file": None, **STEP} if STEP["status"] != "written" else rep["step"]
    rep["voxel_mm"], rep["print_mesh_simplified"] = h, False
    rep["glass"] = rows
    (PKG / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    sheet.sheets(PKG, SPEC["id"], [(k, *helms3.VH3[k][:2], slug(k)) for k in want])
    for k in want:
        m, mask = sheet.load(PKG, slug(k))
        sheet.strip(m, mask, PKG / "images" / f"{slug(k)}.png", f"{k} {helms3.VH3[k][0]}: {helms3.VH3[k][1]}")
