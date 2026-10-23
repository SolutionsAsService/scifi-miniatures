#!/usr/bin/env python3
"""Printability check for the Vigil arsenal (unified-CAD-MCP miniature_* tools via tools/mcpcheck.py); run after build.py
with the unified-CAD-MCP venv, e.g.  ~/ai-stack/repos/unified-CAD-MCP/.venv/bin/python source/check.py
Besides miniature_printability_check on every part (print pose), the plan records miniature_scale_convert for the
exaggerated details, miniature_detail_advice for the heroic sizes, miniature_shell_audit on every upright STL, and (0.2)
miniature_detail_resolution_check on every upright STL: recess widths against the 0.4 mm engraved limit plus the detail
inventory (resolving recesses, sharp-edge loops)."""
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
        {"name": "panel line (6 mm)", "kind": "engraved", "real_mm": 6},
        {"name": "vent slot (12 mm)", "kind": "engraved", "real_mm": 12},
        {"name": "rail tooth (5 mm)", "kind": "embossed", "real_mm": 5},
        {"name": "knife blade spine (6 mm)", "kind": "wall", "real_mm": 6},
        {"name": "trigger guard bar (8 mm)", "kind": "wall", "real_mm": 8},
    ],
    "exaggerated": ["rifle barrel (25 mm)", "panel line (6 mm)", "vent slot (12 mm)", "rail tooth (5 mm)",
                    "knife blade spine (6 mm)", "trigger guard bar (8 mm)"],
    "extra_calls": [
        {"tool": "miniature_detail_advice", "args": {"scale": "28mm", "process": "msla_resin", "features": [
            {"kind": "panel_line", "real_mm": 6, "name": "panel line"},
            {"kind": "rivet", "real_mm": 5, "name": "rail tooth / stud"},
            {"kind": "weapon_haft", "real_mm": 25, "length_mm": 8, "name": "barrel"},
            {"kind": "blade", "real_mm": 6, "name": "knife blade"},
        ]}},
        *[{"tool": "miniature_shell_audit", "args": {"stl_path": str(PKG / "build" / "upright" / f"{q['stl']}.stl")}} for q in PARTS],
        # 0.2: every engraved recess must resolve at the 0.4 mm limit (fills fail the package); the inventory is the
        # measured "how detailed" figure the catalogue and DESIGN.md print
        *[{"tool": "miniature_detail_resolution_check", "args": {"stl_path": str(PKG / "build" / "upright" / f"{q['stl']}.stl")}}
          for q in PARTS],
    ],
    "parts": [{**q, "plan": False, "supports": "light resin supports, upright (grip down) as modelled"} for q in PARTS],
}

if __name__ == "__main__":
    main(__file__, PLAN)
