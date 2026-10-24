#!/usr/bin/env python3
"""Vigilant Heavy Gunner 0.2 (power armour): the 0.1 heavy gunner's stance in the tools/powerarmor.py kit, firing the
VW2-09 Partisan LMG (tools/arsenal.py) from the hip, VH4-05 Ironclad helm, reactor pack, 32 mm base.
The 0.1 package (vigil-heavy) is untouched.

Run (sculpt venv, PYTHONUTF8=1): python source/build.py
Frame: mm, z up, base underside at z = 0, the figure faces -y. Pose numbers from spec/vigil-heavy-02.spec.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import arsenal as A  # noqa: E402
import exosuit as X  # noqa: E402
import powerarmor as PA  # noqa: E402
from sdfkit import bezier, rbox, rot, tube, unit, v3  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-heavy-02.spec.json").read_text(encoding="utf-8"))
pz = S["pose"]
wp = pz["weapon"]
probe = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"], feet_yaw=pz["feet_yaw"])
grip = v3(wp["grip"])
fore_local = A.FORE[wp["ident"]]
REACH = X.L_UPPER + X.L_FORE + 0.6
for ang in range(0, 70, 2):                       # swing the muzzle toward the left until the left fist reaches the fore-grip
    d = rot((0, 0, 1), ang) @ unit(wp["dir"])
    M = X.place(grip, d, (0, 0, 1))
    fore = X.apply(M, fore_local)
    if np.linalg.norm(fore - probe.sh[1]) < REACH:
        break
pose = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"],
              feet_yaw=pz["feet_yaw"], fists=(grip, fore), elbow_poles=pz["elbow_poles"], knee_poles=pz["knee_poles"],
              head_yaw=pz["head_yaw"])


def lmg(g, P):
    g.add(A.weapon_shape(wp["ident"]).moved(M))
    X.fist(g, grip, X.apply(M, (-0.2, 0, -0.98)) - grip, grip - P.elbow[0])
    X.fist(g, fore, M[:3, 1], fore - P.elbow[1])
    # ammunition cable: from the box magazine round the hip to an ammo cell on the belt
    cell = P.pelvis + P.Rp @ v3(-3.4, 1.4, 0.6)
    g.add(rbox(cell, (0.95, 1.2, 1.35), P.Rp, 0.4), 0.15)
    a = X.apply(M, (3.0, 0, -2.2))
    b = cell + P.Rp @ v3(-0.4, -0.6, -1.0)
    g.add(tube(bezier(a, a + v3(-0.6, 0.4, -1.8), b + v3(-0.6, -1.4, -1.6), b, 12), 0.55), 0.2)


NOTES = {
    "figure": ("Vigilant heavy gunner 0.2", "Power-armoured body (tools/powerarmor.py) with the VW2-09 Partisan LMG, ammo cable and belt cell; integral keyed footplate."),
    "helm": ("VH4-05 Ironclad", "Heavy assault helm from the 0.3 library: portcullis faceplate, slit visor, hoses to a collar; 1.6 mm D-flat peg."),
    "backpack": ("Reactor pack", "Armoured reactor pack: fusion-cell drum with a window, twin exhaust stacks with cooling fins; 2.0 mm D-flat peg."),
}

if __name__ == "__main__":
    print("muzzle swing deg", ang, "fore reach", round(float(np.linalg.norm(fore - probe.sh[1])), 2), flush=True)
    print(json.dumps(PA.build_pa(PKG, S, pose, [lmg], "VH4-05", PA.reactor_pack, NOTES, "heavy").get("interference", []))[:600])
