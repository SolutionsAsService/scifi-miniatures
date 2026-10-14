#!/usr/bin/env python3
"""Printability check for the Vigilant Rifleman through the unified-CAD-MCP miniature_* tools (see tools/mcpcheck.py).

Run: PYTHONPATH=/mnt/d/ai-stack/repos/_work/unified-CAD-MCP/src /mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/python source/check.py
(after source/build.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from mcpcheck import main  # noqa: E402
from checkplan import figure_plan  # noqa: E402

PLAN = figure_plan(scale_features=[
    {"name": "Lance rifle barrel (24 mm)", "kind": "wire", "real_mm": 24, "wire_length_real_mm": 100},
    {"name": "Lance receiver depth (60 mm)", "kind": "wall", "real_mm": 60},
], exaggerated=["Lance rifle barrel (24 mm)"])

if __name__ == "__main__":
    main(__file__, PLAN)
