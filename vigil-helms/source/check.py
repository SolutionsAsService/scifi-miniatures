#!/usr/bin/env python3
"""Printability check for Vigil helm library (unified-CAD-MCP miniature_* tools via tools/mcpcheck.py); run after build.py
with /mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/python source/check.py"""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from mcpcheck import main  # noqa: E402

PLAN = {"parts": [{**q, "plan": False, "supports": "light resin supports, upright"} for q in json.loads((PKG / "build" / "parts-plan.json").read_text())]}

if __name__ == "__main__":
    main(__file__, PLAN)
