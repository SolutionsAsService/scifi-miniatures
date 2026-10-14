#!/usr/bin/env python3
"""Printability check for the Vigilant Rifleman 0.3 (VH2 helm) through the unified-CAD-MCP miniature_* tools (tools/mcpcheck.py).

Run after build.py: PYTHONPATH=~/ai-stack/repos/unified-CAD-MCP/src ~/ai-stack/repos/unified-CAD-MCP/.venv/bin/python source/check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from mcpcheck import main  # noqa: E402
from checkplan import figure_plan  # noqa: E402

PLAN = figure_plan(25, scale_features=[
    {"name": "Lance rifle barrel (24 mm)", "kind": "wire", "real_mm": 24, "wire_length_real_mm": 100},
    {"name": "Lance receiver depth (60 mm)", "kind": "wall", "real_mm": 60},
    {"name": "VH2 visor frame (15 mm)", "kind": "embossed", "real_mm": 15},
    {"name": "VH2 vent slot (17 mm)", "kind": "engraved", "real_mm": 17},
], exaggerated=["Lance rifle barrel (24 mm)", "VH2 visor frame (15 mm)", "VH2 vent slot (17 mm)"])

if __name__ == "__main__":
    main(__file__, PLAN)
