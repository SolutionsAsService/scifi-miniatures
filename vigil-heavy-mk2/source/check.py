#!/usr/bin/env python3
"""Printability check for the Vigilant Heavy Gunner Mk2 (unified-CAD-MCP miniature_* tools via tools/mcpcheck.py).
Run after build.py with the unified-CAD-MCP venv:
    PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check.py
Own plan (tools/checkplan.figure_plan only knows 25/32 mm bases): 40 mm base, the enlarged pack boss (4.6 mm host
section) and the loose heavy weapons."""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from mcpcheck import main  # noqa: E402

REP = json.loads((PKG / "reports" / "build.json").read_text())
BITS = [s for s in REP["parts"] if s.startswith("vhw-")]
PLAN = {
    "scale_features": [
        {"name": "visor-line height", "real_mm": 1666},
        {"name": "gauntlet (110 mm)", "kind": "wall", "real_mm": 110},
        {"name": "armour plate step (8 mm)", "kind": "embossed", "real_mm": 8},
        {"name": "panel line (6 mm)", "kind": "engraved", "real_mm": 6},
        {"name": "rotary barrel (30 mm)", "kind": "wall", "real_mm": 30},
        {"name": "ammunition belt (55 mm)", "kind": "wall", "real_mm": 55},
        {"name": "support handle bar (40 mm)", "kind": "wall", "real_mm": 40},
    ],
    "exaggerated": ["armour plate step (8 mm)", "panel line (6 mm)", "rotary barrel (30 mm)"],
    "base_and_peg": [
        {"base": "40", "magnet": "5x2", "base_height_mm": round(4.0 - 1.1, 2)},
        {"base": "40", "magnet": None, "peg_diameter_mm": 1.6, "host_section_mm": 4.6},   # helm peg in the gorget
        {"base": "40", "magnet": None, "peg_diameter_mm": 2.0, "host_section_mm": 4.6},   # pack peg in the enlarged boss
    ],
    "extra_calls": [{"tool": "miniature_shell_audit", "args": {"stl_path": str(PKG / "build" / "upright" / f"{s}.stl")}}
                    for s in ["figure", "helm", "backpack", "base", *BITS]],
    "parts": [
        {"stl": "figure", "label": "Figure (with footplate, Bombard, belt)", "plan": True},
        {"stl": "helm", "label": "VH2-04 Bastion helm", "plan": True},
        {"stl": "backpack", "label": "VHW-01P drum pack", "plan": True},
        {"stl": "base", "label": "40 mm base", "plan": True},
        *[{"stl": s, "label": REP["names"][s], "plan": False, "supports": "as modelled, lying, light supports"} for s in BITS],
    ],
}

if __name__ == "__main__":
    main(__file__, PLAN)
