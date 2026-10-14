"""Shared print plan for the Vigilant figures (tools/mcpcheck.py runs it through the unified-CAD-MCP miniature_* tools)."""


def figure_plan(scale_features=(), exaggerated=()):
    return {
        "scale_features": [
            {"name": "visor-line height", "real_mm": 1666},
            {"name": "gauntlet / fist (110 mm)", "kind": "wall", "real_mm": 110},
            {"name": "armour plate step (8 mm)", "kind": "embossed", "real_mm": 8},
            {"name": "panel line (6 mm)", "kind": "engraved", "real_mm": 6},
            {"name": "sensor fin (10 mm)", "kind": "wall", "real_mm": 10},
            *scale_features,
        ],
        "exaggerated": ["armour plate step (8 mm)", "panel line (6 mm)", "sensor fin (10 mm)", *exaggerated],
        "base_and_peg": [
            # base: 4.0 mm tall but the footplate recess is 1.1 mm deep, so 2.9 mm of base sits over the magnet pocket
            {"base": "32", "magnet": "5x2", "base_height_mm": 2.9},
            # helm peg into the gorget (4.3 mm across at the neck cut)
            {"base": "32", "magnet": None, "peg_diameter_mm": 1.6, "host_section_mm": 4.3},
            # backpack peg into the back boss (3.1 mm wide)
            {"base": "32", "magnet": None, "peg_diameter_mm": 2.0, "host_section_mm": 3.1},
        ],
        "parts": [
            {"stl": "figure", "label": "Figure (with footplate)", "plan": True},
            {"stl": "helm", "label": "Helm", "plan": True},
            {"stl": "backpack", "label": "Backpack", "plan": True},
            {"stl": "base", "label": "32 mm base", "on_build_plate": True,
             "orientation": "flat, underside on the plate (magnet pocket vented to the rim)", "supports": "none"},
        ],
    }
