#!/usr/bin/env python3
"""Quick 4-view previews of build/upright/*.stl into build/preview/ (iteration aid; tools/render.py)."""
import sys
from pathlib import Path

import trimesh

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from render import render  # noqa: E402

out = PKG / "build" / "preview"
out.mkdir(parents=True, exist_ok=True)
names = sys.argv[1:] or [p.stem for p in sorted((PKG / "build" / "upright").glob("*.stl"))]
for n in names:
    m = trimesh.load(PKG / "build" / "upright" / f"{n}.stl")
    render([(m, "#7d8a78")], out / f"{n}.png", views=((-35, 25, "3/4"), (0, 2, "front"), (90, 2, "side"), (0, 90, "top"), (0, -90, "bottom")), size=420, title=n)
    print(n, "ok")
