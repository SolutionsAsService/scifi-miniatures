"""Shared print plan for the Vigilant figures (tools/mcpcheck.py runs it through the unified-CAD-MCP miniature_* tools)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def figure_plan(base_d, scale_features=(), exaggerated=()):
    base_h = {25: 3.8, 32: 4.0}[base_d]  # = exosuit.BASES (kept here so the check runs without numpy)
    return {
        "scale_features": [
            {"name": "visor-line height", "real_mm": 1666},
            {"name": "gauntlet (110 mm)", "kind": "wall", "real_mm": 110},
            {"name": "armour plate step (8 mm)", "kind": "embossed", "real_mm": 8},
            {"name": "panel line (6 mm)", "kind": "engraved", "real_mm": 6},
            {"name": "sensor fin (10 mm)", "kind": "wall", "real_mm": 10},
            *scale_features,
        ],
        "exaggerated": ["armour plate step (8 mm)", "panel line (6 mm)", "sensor fin (10 mm)", *exaggerated],
        "base_and_peg": [
            # the footplate recess is 1.1 mm deep and sits over the magnet pocket: check the floor that is left
            {"base": str(base_d), "magnet": "5x2", "base_height_mm": round(base_h - 1.1, 2)},
            {"base": str(base_d), "magnet": None, "peg_diameter_mm": 1.6, "host_section_mm": 4.6},   # helm peg in the gorget
            {"base": str(base_d), "magnet": None, "peg_diameter_mm": 2.0, "host_section_mm": 3.4},   # pack peg in the back boss
        ],
        "parts": [
            {"stl": "figure", "label": "Figure (with footplate)", "plan": True},
            {"stl": "helm", "label": "Helm", "plan": True},
            {"stl": "backpack", "label": "Backpack", "plan": True},
            {"stl": "base", "label": f"{base_d} mm base", "on_build_plate": True,
             "orientation": "flat, underside on the plate (magnet pocket vented to the rim)", "supports": "none"},
        ],
    }
