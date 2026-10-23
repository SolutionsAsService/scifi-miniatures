#!/usr/bin/env python3
"""Iteration aid: sculpt named parts at a (coarse) pitch, write build/preview/<n>.stl + a 5-view PNG, print measures.
Run: ~/projects/venvs/scifi-sculpt/bin/python source/preview.py [--h 0.1] part ...
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import vigil_aerial as V  # noqa: E402
from render import render  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-aerial-drones.spec.json").read_text())
FN = {"belfry": V.belfry, "angelus": V.angelus, "main-rotor": V.main_rotor, "tail-rotor": V.tail_rotor, "knell": V.knell,
      "launcher-rail": V.launcher_rail, "launcher-tripod": V.launcher_tripod, "roof-pad": V.roof_pad,
      "base-50-stem": lambda S: V.base_stem(S, "base-50-stem"), "base-40-stem": lambda S: V.base_stem(S, "base-40-stem"),
      "base-50-tether": V.base_tether, "vl-01": V.bit_eo_turret, "vl-02": V.bit_sar_pod, "vl-03": V.bit_twin_munitions,
      "vl-04": V.bit_cargo_pod, "vl-10": V.bit_eo_mast, "vl-11": V.bit_relay_mast, "vl-12": V.bit_radar_mast}
args = sys.argv[1:]
h = 0.1
if args and args[0] == "--h":
    h = float(args[1])
    args = args[2:]
out = PKG / "build" / "preview"
out.mkdir(parents=True, exist_ok=True)
for n in args or list(FN):
    t0 = time.time()
    m = FN[n](S).sculpt(h).mesh(n)
    m.export(out / f"{n}.stl")
    render([(m, "#7d8a78")], out / f"{n}.png", views=((-35, 25, "3/4"), (0, 2, "front"), (90, 2, "side"), (0, 90, "top"), (0, -90, "bottom")), size=380, title=n)
    print(n, "tris", len(m.faces), "vol", round(m.volume, 2), "lo", np.round(m.bounds[0], 2).tolist(), "hi", np.round(m.bounds[1], 2).tolist(), f"{time.time()-t0:.0f}s", flush=True)
