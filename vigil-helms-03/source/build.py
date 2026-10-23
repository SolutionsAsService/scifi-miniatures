#!/usr/bin/env python3
"""Vigil helm library 0.3 (VH4): bits package from tools/helms04.py.

Run (sculpt venv, PYTHONUTF8=1): python source/build.py [VH4-01,VH4-05 ...]
Writes build/upright/*.stl (print meshes, NOT simplified: marched on the spec's grid and asserted one closed manifold
body under the checker's 300 k triangle limit), build/glass/*.npy (display masks), viewer/vigil-helms-03.parts.json,
reports/build.json, build/parts-plan.json, images/ (hero + turnaround from tools/vigil.py, display sheets).
Print safety: tools/morph.py print_safe_selective (spec "morph"): only walls thinner than 0.42 mm and slots narrower
than 0.5 mm are changed; every other surface keeps the sculpt exactly.
STEP: written only when $FREECAD_PYTHON is set. 18 faceted helms make a very large reference STEP, so the published
package ships the STLs (the print files) and records the STEP as skipped in reports/build.json.
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
import helms04  # noqa: E402
import helms3  # noqa: E402
import morph  # noqa: E402
import sdfkit  # noqa: E402
import sheet  # noqa: E402
from vigil import build_loose  # noqa: E402

SPEC = json.loads((PKG / "spec" / "vigil-helms-03.spec.json").read_text())
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
    return f"{k.lower()}-{helms04.VH4[k][0].lower()}"


def _mesh(k, h, tri_cap):
    g = helms04.helm(k, h)
    mo = SPEC.get("morph", {})
    st = morph.print_safe_selective(g, mo.get("r_open_mm", 0.21), mo.get("r_close_mm", 0.22), mo.get("deep_mm", 0.12),
                                   deep_close_mm=mo.get("deep_close_mm", 0.04))  # only thin walls / narrow slots
    print(k, "morph", st, flush=True)
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


def slim_viewer():
    """Display meshes only: quadric-decimate each viewer part to viewer_tris_per_part (the hosted viewer streams the
    parts file; 18 helms at full resolution were 11 MB). Print STLs are never touched."""
    import fast_simplification
    path = PKG / "viewer" / f"{SPEC['id']}.parts.json"
    parts = json.loads(path.read_text(encoding="utf-8"))
    for p in parts:
        v, f = np.asarray(p["vertices"], dtype=np.float64), np.asarray(p["triangles"], dtype=np.int64)
        if len(f) > SPEC["viewer_tris_per_part"]:
            v, f = fast_simplification.simplify(v, f, target_reduction=1 - SPEC["viewer_tris_per_part"] / len(f))
            p["vertices"], p["triangles"] = np.round(v, 3).tolist(), f.tolist()
    path.write_text(json.dumps(parts, separators=(",", ":")), encoding="utf-8")
    return path.stat().st_size


def finish_images(want):
    sheet.sheets(PKG, SPEC["id"], [(k, *helms04.VH4[k][:2], slug(k)) for k in want])
    for k in want:
        m, mask = sheet.load(PKG, slug(k))
        sheet.strip(m, mask, PKG / "images" / f"{slug(k)}.png", f"{k} {helms04.VH4[k][0]}: {helms04.VH4[k][1]}")


if __name__ == "__main__" and "--images" in sys.argv:
    print(f"viewer parts: {slim_viewer() / 1e6:.1f} MB")
    finish_images(list(helms04.VH4))
    sys.exit(0)

if __name__ == "__main__":
    want = sys.argv[1].split(",") if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else list(helms04.VH4)
    h, cap = SPEC["voxel_mm"], SPEC["max_triangles"]
    (PKG / "build" / "glass").mkdir(parents=True, exist_ok=True)
    parts, plan, rows = [], [], {}
    for i, k in enumerate(want):
        name, note, _ = helms04.VH4[k]
        m, mask = mesh_in_child(k, h, cap)
        np.save(PKG / "build" / "glass" / f"{slug(k)}.npy", mask)
        at = ((i % 6 - 2.5) * 9.0, -(i // 6) * 11.0, 0.0)
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
    print(f"viewer parts: {slim_viewer() / 1e6:.1f} MB")
    finish_images(want)
