#!/usr/bin/env python3
"""Vigil helm library Mk 2 (VH2): bits package from tools/vh2.py.

Run: ~/ai-stack/venvs/sculpt/bin/python source/build.py [VH2-01,VH2-05 ...]
Writes build/upright/*.stl, viewer/vigil-helms-mk2.parts.json, cad/vigil-helms-mk2-assembly.step, reports/build.json,
build/parts-plan.json and images/ (library hero + turnaround from tools/vigil.py, display sheets from source/sheet.py).
"""
import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import trimesh

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import bitspack  # noqa: E402
import freecadshim  # noqa: E402
import vh2  # noqa: E402
import sheet  # noqa: E402

freecadshim.use()   # STEP export through $FREECAD_PYTHON / the local FreeCAD shim (tools/freecadshim.py)

SPEC = json.loads((PKG / "spec" / "vigil-helms-mk2.spec.json").read_text())


def _mesh(k, h, nm, t):
    m = vh2.helm(k, h).mesh(nm, t)
    return m.vertices, m.faces


def mesh_in_child(k, h, nm, t):
    """Sculpt one helm in a fresh process: numpy peaks stay per helm (about 0.6 GB at 0.05 mm) instead of accumulating.
    REUSE=1 reloads build/upright/<slug>.stl from a previous run (e.g. to redo exports and images only)."""
    stl = PKG / "build" / "upright" / f"{bitspack.slug(k, vh2.VH2[k][0])}.stl"
    if os.environ.get("REUSE") == "1" and stl.exists():
        return trimesh.load(stl, process=True)   # STL stores triangle soup: merge vertices back into a closed mesh
    with mp.get_context("spawn").Pool(1) as pool:
        v, f = pool.apply(_mesh, (k, h, nm, t))
    return trimesh.Trimesh(v, f, process=False)


def items(idents=None):
    return [(k, name, note, lambda h, nm, t, k=k: mesh_in_child(k, h, nm, t)) for k, (name, note, _) in vh2.VH2.items()
            if not idents or k in idents]


if __name__ == "__main__":
    bitspack.build(PKG, items(), cols=6, dx=9.0, dy=11.0, h=SPEC["voxel_mm"], tris=SPEC["max_triangles"])
    sheet.sheets(PKG, SPEC["id"])
