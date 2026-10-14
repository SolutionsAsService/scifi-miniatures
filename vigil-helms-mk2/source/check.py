#!/usr/bin/env python3
"""Printability check for the VH2 helm library through the unified-CAD-MCP miniature_* tools (tools/mcpcheck.py).

Run after build.py: PYTHONPATH=~/ai-stack/repos/unified-CAD-MCP/src ~/ai-stack/repos/unified-CAD-MCP/.venv/bin/python source/check.py
Every helm is checked upright as modelled (peg down, on light supports), the pose the line's helms are printed in.
"""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from mcpcheck import main  # noqa: E402

PLAN = {
    "scale_features": [
        {"name": "visor frame (15 mm)", "kind": "embossed", "real_mm": 15},
        {"name": "vent slot (17 mm)", "kind": "engraved", "real_mm": 17},
        {"name": "keel bar (30 mm)", "kind": "wall", "real_mm": 30},
        {"name": "antenna (12 mm dia, 250 mm)", "kind": "wire", "real_mm": 12, "wire_length_real_mm": 250},
    ],
    "exaggerated": ["visor frame (15 mm)", "vent slot (17 mm)", "antenna (12 mm dia, 250 mm)"],
    # the helm peg in the figure's gorget: same joint as every Vigil helm
    "base_and_peg": [{"base": "25", "magnet": None, "peg_diameter_mm": 1.6, "host_section_mm": 4.6}],
    "parts": [{**q, "plan": False, "supports": "light resin supports, upright on the peg"}
              for q in json.loads((PKG / "build" / "parts-plan.json").read_text())],
}

if __name__ == "__main__":
    main(__file__, PLAN)
