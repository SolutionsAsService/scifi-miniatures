#!/usr/bin/env python3
"""Vigilant Heavy Gunner (Maul arc-cannon from the hip): Aster Compact Vigilant line, 30 mm heroic, MSLA resin.

Run: /mnt/d/ai-stack/venvs/scifi-sculpt/bin/python source/build.py
Frame: mm, z up, base underside at z = 0, the figure faces -y. Pose numbers from spec/vigil-heavy.spec.json.
"""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import exosuit as X  # noqa: E402
from sdfkit import bezier, rbox, tube, unit, v3  # noqa: E402
from vigil import build_figure  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-heavy.spec.json").read_text())
pz = S["pose"]
cz = pz["cannon"]
M = X.place(v3(cz["grip"]), unit(cz["dir"]), (0, 0, 1))
grip, handle = X.apply(M, (0, 0, 0)), X.apply(M, (cz["handle_x"], 0, 2.8))
pose = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"],
              feet_yaw=pz["feet_yaw"], fists=(grip, handle), elbow_poles=pz["elbow_poles"], knee_poles=pz["knee_poles"],
              head_yaw=pz["head_yaw"])


def cannon(g, P):
    g.add(X.maul_cannon().moved(M))
    X.fist(g, grip, X.apply(M, (-0.17, 0, -0.98)) - grip, grip - P.elbow[0])
    X.fist(g, handle, M[:3, 0], handle - P.elbow[1])
    # belt power cell on the right hip and the cable from the capacitor drum
    cell = P.pelvis + P.Rp @ v3(-2.95, 1.1, 0.7)
    g.add(rbox(cell, (0.85, 1.1, 1.25), P.Rp, 0.38), 0.15)
    a = X.apply(M, (-2.4, 0, 0.3))
    b = cell + P.Rp @ v3(-0.5, -0.4, -0.9)
    g.add(tube(bezier(a, a + v3(0, 0, -2.2), b + v3(-0.8, -1.2, -2.0), b, 12), 0.5), 0.2)


NOTES = {
    "figure": ("Vigilant heavy gunner", "Kestrel exosuit body with the Maul arc-cannon, power cable and belt cell, integral keyed footplate."),
    "helm": ("Vigil helm", "Line-standard helm: chevron split visor, keel crest, ear-pod fins; 1.6 mm D-flat peg."),
    "backpack": ("Power pack", "Spine power pack with twin manoeuvring nozzles; 2.0 mm D-flat peg."),
}

if __name__ == "__main__":
    build_figure(PKG, S, pose, [cannon], "vigil", "power", NOTES)
