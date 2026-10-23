#!/usr/bin/env python3
"""Dev printability probe: miniature_printability_check (unified-CAD-MCP, in-process) on build/dev/*.stl, upright as
modelled, with thin spots mapped back to model and helm-unit coordinates. The package check (source/check.py) is
the verdict of record; this is the iteration loop. Run with the unified-CAD-MCP venv and PYTHONPATH=<repo>/src."""
import asyncio
import json
import sys
from pathlib import Path

import numpy as np
from fastmcp import Client

from unified_cad_mcp.config import AirframeConfig, Configuration
from unified_cad_mcp.flotation import read_stl
from unified_cad_mcp.server import create_server

PKG = Path(__file__).resolve().parents[1]
HC, HS = np.array([0, 0, 2.8]), 1.12


async def main(names):
    cfg = Configuration(project_root=str(PKG), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(PKG / "build"), read_roots=[str(PKG / "build")]))
    out = {}
    async with Client(create_server(cfg), timeout=1800) as c:
        for n in names:
            stl = PKG / "build" / "dev" / f"{n}.stl"
            r = (await c.call_tool("miniature_printability_check", {"stl_path": str(stl), "process": "msla_resin",
                                                                    "on_build_plate": False})).data
            A = np.array(read_stl(stl), float).reshape(-1, 3)
            lo, hi = A.min(0), A.max(0)
            d = np.array([0.0, 0.0, -lo[2]])          # the tool keeps x, y and only lifts the part to the plate
            th = r["thickness"]
            spots = []
            for s in sorted(th["thin_spots"], key=lambda s: -s["area_mm2"]):
                if s["min_mm"] < 0.4:
                    p = np.array(s["at_mm"]) - d
                    spots.append((round(s["area_mm2"], 3), s["min_mm"], np.round(p, 2).tolist(), np.round((p - HC) / HS, 2).tolist()))
            fails = [ch["name"] for ch in r["checks"] if not ch["pass"] and ch["severity"] == "fail"]
            out[n] = {"fails": fails, "below_supported_mm2": th["area_below_supported_mm2"],
                      "below_unsupported_mm2": th["area_below_unsupported_mm2"], "min_mm": th["min_mm"], "spots": spots,
                      "warnings": r["warnings"], "islands": r["islands"]["count"],
                      "cups": max((x["max_area_mm2"] for x in r["suction_cups"]), default=0), "spikes": r.get("spikes")}
            print(n, out[n]["fails"], "supported<0.4:", out[n]["below_supported_mm2"], "unsup<0.6:", out[n]["below_unsupported_mm2"], flush=True)
            for s in spots[:6]:
                print("    ", s, flush=True)
    (PKG / "build" / "dev" / "devcheck.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
