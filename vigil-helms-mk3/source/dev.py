#!/usr/bin/env python3
"""Dev loop for one VH3 helm: sculpt at a given pitch, mesh (no simplification), write build/dev/<slug>.stl, the glass
mask and a four-view render in build/dev/. Run: <sculpt python> source/dev.py VH3-01 [pitch]"""
import json
import sys
import time
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import helms3  # noqa: E402
import sheet  # noqa: E402
from sdfkit import mesh_stats  # noqa: E402


def slug(k):
    return f"{k.lower()}-{helms3.VH3[k][0].lower()}"


if __name__ == "__main__":
    k = sys.argv[1]
    h = float(sys.argv[2]) if len(sys.argv) > 2 else 0.08
    t0 = time.time()
    g = helms3.helm(k, h)
    m = g.mesh(k, None)
    mask = helms3.glass_mask(g.glass, m.triangles_center)
    out = PKG / "build" / "dev"
    out.mkdir(parents=True, exist_ok=True)
    m.export(out / f"{slug(k)}.stl")
    bb = m.bounds
    st = {"ident": k, "pitch": h, "seconds": round(time.time() - t0, 1), "bbox_mm": np.round(bb[1] - bb[0], 2).tolist(),
          "min": np.round(bb[0], 2).tolist(), "max": np.round(bb[1], 2).tolist(), "volume_mm3": round(float(m.volume), 2),
          "glass_faces": int(mask.sum()), "glass_area_mm2": round(float(m.area_faces[mask].sum()), 2), **mesh_stats(m)}
    sheet.strip(m, mask, out / f"{slug(k)}.png", f"{k} {helms3.VH3[k][0]} (dev, pitch {h} mm)")
    print(json.dumps(st))
