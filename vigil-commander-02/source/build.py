#!/usr/bin/env python3
"""Vigilant Commander 0.2 (power armour): the 0.1 Warden's pose (pointing the advance, sidearm raised, tabard) in the
tools/powerarmor.py kit, with the VW2-07 Culverin heavy revolver, the VH4-02 Marshal helm, a command pack, 32 mm base.
The 0.1 package (vigil-warden) is untouched: its pose and gear code are imported and the sidearm swapped at run time.

Run (sculpt venv, PYTHONUTF8=1): python source/build.py
"""
import importlib.util
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import arsenal as A  # noqa: E402
import exosuit as X  # noqa: E402
import powerarmor as PA  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-commander-02.spec.json").read_text(encoding="utf-8"))
X.sidearm = lambda: A.weapon_shape("VW2-07")          # Culverin heavy revolver: same VW grip block as the Spur
spec = importlib.util.spec_from_file_location("warden01", PKG.parent / "vigil-warden" / "source" / "build.py")
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)                             # 0.1 pose, sidearm placement, pointing hand, tabard (not built)

NOTES = {
    "figure": ("Vigilant commander 0.2", "Power-armoured body (tools/powerarmor.py) pointing the advance, VW2-07 Culverin raised, cloth tabard; integral keyed footplate."),
    "helm": ("VH4-02 Marshal", "Sergeant/commander helm from the 0.3 library: swept blade crest, command antenna, rank bars; 1.6 mm D-flat peg."),
    "backpack": ("Command pack", "Armoured command pack: comms mast with cross spars, power cell, twin exhausts; 2.0 mm D-flat peg."),
}

if __name__ == "__main__":
    print(json.dumps(PA.build_pa(PKG, S, W.pose, [W.gear], "VH4-02", PA.command_pack, NOTES, "commander").get("interference", []))[:600])
