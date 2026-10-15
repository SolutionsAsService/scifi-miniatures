#!/usr/bin/env python3
"""Printability check for the Vigil arsenal VW3 (unified-CAD-MCP miniature_* tools via tools/mcpcheck.py); run after
build.py with the unified-CAD-MCP venv:
    PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check.py
Besides miniature_printability_check on every part in its print pose, the plan records miniature_scale_convert for
the exaggerated details, miniature_detail_advice for the heroic sizes and miniature_shell_audit on every upright STL.
Print pose: as modelled (guns lying in their side-profile orientation, z up; blades standing blade-up) on supports."""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from mcpcheck import main  # noqa: E402

PARTS = json.loads((PKG / "build" / "parts-plan.json").read_text())
PLAN = {
    "scale_features": [
        {"name": "rifle barrel (25 mm)", "kind": "wall", "real_mm": 25},
        {"name": "panel seam (6 mm)", "kind": "engraved", "real_mm": 6},
        {"name": "vent slot (12 mm)", "kind": "engraved", "real_mm": 12},
        {"name": "rail tooth (5 mm)", "kind": "embossed", "real_mm": 5},
        {"name": "trigger guard bar (8 mm)", "kind": "wall", "real_mm": 8},
        {"name": "sword blade spine (8 mm)", "kind": "wall", "real_mm": 8},
        {"name": "sword edge (1 mm)", "kind": "wall", "real_mm": 1},
        {"name": "pommel ring wire (12 mm)", "kind": "wall", "real_mm": 12},
    ],
    "exaggerated": ["rifle barrel (25 mm)", "panel seam (6 mm)", "vent slot (12 mm)", "rail tooth (5 mm)",
                    "trigger guard bar (8 mm)", "sword blade spine (8 mm)", "sword edge (1 mm)", "pommel ring wire (12 mm)"],
    "extra_calls": [
        {"tool": "miniature_detail_advice", "args": {"scale": "28mm", "process": "msla_resin", "features": [
            {"kind": "panel_line", "real_mm": 6, "name": "panel seam"},
            {"kind": "rivet", "real_mm": 5, "name": "rail tooth / bolt"},
            {"kind": "weapon_haft", "real_mm": 25, "length_mm": 12, "name": "barrel"},
            {"kind": "blade", "real_mm": 8, "name": "sword blade"},
        ]}},
        *[{"tool": "miniature_shell_audit", "args": {"stl_path": str(PKG / "build" / "upright" / f"{q['stl']}.stl")}} for q in PARTS],
    ],
    "parts": [{**q, "plan": False, "supports": "light resin supports under the part, as modelled (guns lying, blades standing)"}
              for q in PARTS],
}

if __name__ == "__main__":
    main(__file__, PLAN)
