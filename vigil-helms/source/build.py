#!/usr/bin/env python3
"""Vigil helm library: bits package from tools/armory.py. Run: /mnt/d/ai-stack/venvs/scifi-sculpt/bin/python source/build.py"""
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import bitspack  # noqa: E402

if __name__ == "__main__":
    bitspack.build(PKG, bitspack.helm_items())
