#!/usr/bin/env python3
"""Vigil arsenal (VW2 series): bits package from tools/arsenal.py, plus the display sheets (source/sheet.py).

Run with the sculpt venv (numpy, scikit-image, trimesh, manifold3d, pillow), e.g.
    ~/ai-stack/venvs/sculpt/bin/python source/build.py            (all parts)
    ~/ai-stack/venvs/sculpt/bin/python source/build.py --sheets   (re-render the display sheets only)
The FreeCAD python used for the faceted STEP reference is sdfkit.FREECAD_PYTHON, or $FREECAD_PYTHON (default: the
unified-CAD-MCP shim ~/ai-stack/freecad-shim/bin/python) when that path is missing on this machine. The shim pre-imports
FreeCAD and runs a script file (runpy): a bare "python -c" in the FreeCAD env loses its imports when "import FreeCAD"
clobbers __main__ globals, so sdfkit's "-c" call is routed through a temporary script file here.
"""
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import arsenal as A  # noqa: E402
import bitspack  # noqa: E402
import sdfkit  # noqa: E402
import sheet  # noqa: E402

SPEC = json.loads((PKG / "spec" / "vigil-arsenal.spec.json").read_text())
if not Path(sdfkit.FREECAD_PYTHON).exists():
    sdfkit.FREECAD_PYTHON = os.environ.get("FREECAD_PYTHON", str(Path.home() / "ai-stack/freecad-shim/bin/python"))


def _run_as_file(cmd, **kw):
    """sdfkit.write_step runs [FREECAD_PYTHON, '-c', code]; run the code from a temporary file instead (shim-safe)."""
    if len(cmd) == 3 and cmd[1] == "-c":
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(cmd[2])
        try:
            return subprocess.run([cmd[0], f.name], **kw)
        finally:
            os.unlink(f.name)
    return subprocess.run(cmd, **kw)


sdfkit.subprocess = types.SimpleNamespace(run=_run_as_file)


def items():
    return [(k, name, note, lambda h, nm, t, fn=fn: fn().sculpt(h).mesh(nm, t)) for k, (name, note, fn) in A.WEAPONS2.items()]


def at(i, ident):
    return (0.0, -i * 6.0, 0.0)          # one weapon per row (y extent <= 4 mm), muzzles to +x


def reference_step():
    """Faceted STEP reference from a coarser re-mesh of each SDF (step_voxel_mm), not from the 0.05 mm print mesh:
    manifold simplification keeps the 0.2 detail's sharp edges, so the print meshes stay at 5-50 k triangles even at a
    0.4 mm tolerance and a STEP of them runs to ~1 GB (~3.5 kB per triangle)."""
    parts = []
    for i, (ident, (name, _, fn)) in enumerate(A.WEAPONS2.items()):
        m = fn().sculpt(SPEC["step_voxel_mm"]).mesh(f"{ident} {name}")
        m = sdfkit.decimate(m, SPEC["step_tris_per_part"], f"{ident} {name}", coarse=True)
        m.apply_transform(sdfkit.translate(*at(i, ident)))
        parts.append({"name": f"{ident} {name}", "vertices": m.vertices.tolist(), "faces": m.faces.tolist()})
    _write_step(PKG / "cad" / f"{SPEC['id']}-assembly.step", parts)
    return sum(len(p["faces"]) for p in parts)


def slim_viewer():
    """Display meshes only: quadric-decimate each viewer part to viewer_tris_per_part. The hosted viewer streams the
    parts file uncompressed at ~110 kB/s, so 8.7 MB took over a minute to open; print STLs are never touched."""
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


_write_step = sdfkit.write_step

if __name__ == "__main__":
    if "--sheets" not in sys.argv:
        sdfkit.write_step = lambda path, parts: None        # the print-mesh STEP is replaced by reference_step()
        bitspack.build(PKG, items(), h=SPEC["voxel_mm"], tris=SPEC["max_print_triangles"], at_fn=at)
        print(f"reference STEP: {reference_step()} triangles")
        print(f"viewer parts: {slim_viewer() / 1e6:.1f} MB")
    print(sheet.sheets(sheet.load_items()))
