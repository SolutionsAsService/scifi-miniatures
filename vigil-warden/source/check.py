#!/usr/bin/env python3
"""Printability check for the Vigilant Warden through the unified-CAD-MCP miniature_* tools (see tools/mcpcheck.py).

Run: PYTHONPATH=/mnt/d/ai-stack/repos/_work/unified-CAD-MCP/src /mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/python source/check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from mcpcheck import main  # noqa: E402
from checkplan import figure_plan  # noqa: E402

PLAN = figure_plan(25, scale_features=[
    {"name": "index finger (20 mm)", "kind": "wire", "real_mm": 20, "wire_length_real_mm": 80},
    {"name": "whip antenna (12 mm)", "kind": "wire", "real_mm": 12, "wire_length_real_mm": 300},
    {"name": "tabard cloth (4 mm)", "kind": "wall", "real_mm": 4},
], exaggerated=["index finger (20 mm)", "whip antenna (12 mm)", "tabard cloth (4 mm)"])

if __name__ == "__main__":
    main(__file__, PLAN)
