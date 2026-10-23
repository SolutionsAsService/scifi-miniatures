#!/usr/bin/env python3
"""Printability check for the VH4 helm library (0.3) through the unified-CAD-MCP miniature_* tools (tools/mcpcheck.py).

Run after build.py: PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check.py
Every helm gets a support plan (miniature_support_plan picks the print rotation) and is checked in that pose; the
pose STL is written to print/stl/ (the file you slice is the file that was checked).
"""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import cachedcheck  # noqa: E402

PLAN = {
    "scale_features": [
        {"name": "visor frame (25 mm)", "kind": "embossed", "real_mm": 25},
        {"name": "vent slot (17 mm)", "kind": "engraved", "real_mm": 17},
        {"name": "keel bar (30 mm)", "kind": "wall", "real_mm": 30},
        {"name": "antenna (12 mm dia, 280 mm)", "kind": "wire", "real_mm": 12, "wire_length_real_mm": 280},
    ],
    "exaggerated": ["visor frame (25 mm)", "vent slot (17 mm)", "antenna (12 mm dia, 280 mm)", "keel bar (30 mm)"],
    "base_and_peg": [{"base": "25", "magnet": None, "peg_diameter_mm": 1.6, "host_section_mm": 4.6}],
    "parts": [{**q, "supports": "light resin supports (rotation from miniature_support_plan)"}
              for q in json.loads((PKG / "build" / "parts-plan.json").read_text())],
}

if __name__ == "__main__":
    cachedcheck.main(__file__, PLAN)
