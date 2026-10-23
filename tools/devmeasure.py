#!/usr/bin/env python3
"""Fast dev measurement of STLs with the unified-CAD-MCP miniature functions (same code the MCP tools run):
printability_check (thin walls, spikes, bodies, manifold) and gap_check (narrow gaps). One line per STL.
Usage: PYTHONPATH=~/projects/unified-CAD-MCP/src python devmeasure.py a.stl [b.stl ...] [--rot rx,ry,rz]"""
import json
import sys
from pathlib import Path

from unified_cad_mcp.flotation import read_stl
from unified_cad_mcp.miniature import printability_check
from unified_cad_mcp.miniature_gaps import gap_check

args = [a for a in sys.argv[1:] if not a.startswith("--")]
for p in args:
    t = read_stl(Path(p))
    r = printability_check(t, process="msla_resin", on_build_plate=False)
    g = gap_check(t, process="msla_resin")
    th = r["thickness"]
    fails = [c["name"] for c in r["checks"] if not c["pass"] and c["severity"] == "fail"]
    gf = [c["name"] for c in g["checks"] if not c["pass"] and c["severity"] == "fail"]
    spots = sorted(th["thin_spots"], key=lambda s: -s["area_mm2"])[:3]
    print(json.dumps({"stl": p.split("/")[-1], "fails": fails + gf, "thin_s": th["area_below_supported_mm2"],
                      "thin_u": th["area_below_unsupported_mm2"], "min_wall": th["min_mm"],
                      "gap_area": g["narrow_gap_area_mm2"], "min_gap": g["smallest_gap_mm"], "spikes": len(r.get("spikes") or []),
                      "spots": [(round(s["area_mm2"], 3), s["min_mm"], s["at_mm"]) for s in spots],
                      "gspots": g["narrow_spots"][:3]}), flush=True)
