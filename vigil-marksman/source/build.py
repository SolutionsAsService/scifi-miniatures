#!/usr/bin/env python3
"""Vigilant Marksman (kneeling, Needle rifle aimed): Aster Compact Vigilant line, 30 mm heroic, MSLA resin.

Run: /mnt/d/ai-stack/venvs/scifi-sculpt/bin/python source/build.py
Frame: mm, z up, base underside at z = 0, the figure faces -y. Pose numbers from spec/vigil-marksman.spec.json;
the right knee is placed explicitly on the deck (exosuit.Pose knees=), the left leg is solved by IK.
"""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import exosuit as X  # noqa: E402
from sdfkit import unit, v3  # noqa: E402
from vigil import build_figure  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-marksman.spec.json").read_text())
pz = S["pose"]
d = unit(pz["rifle"]["dir"])
M = X.place(v3(pz["rifle"]["stock"]) + d * 3.6, d, (0, 0, 1))          # stock butt in the shoulder, grip 3.6 mm ahead
grip, fore = X.apply(M, (0, 0, 0)), X.apply(M, (2.9, 0, -0.25))
pose = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"],
              feet_yaw=pz["feet_yaw"], fists=(grip, fore), elbow_poles=pz["elbow_poles"], knee_poles=pz["knee_poles"],
              knees=(pz["knee_r"], None), head_yaw=pz["head_yaw"])


def rifle(g, P):
    g.add(X.needle_rifle().moved(M))
    down = X.apply(M, (-0.24, 0, -0.97)) - grip
    X.fist(g, grip, down, grip - P.elbow[0])
    X.fist(g, fore, down, fore - P.elbow[1])
    g.add(X.rbox(P.knee[0] + v3(0, 0, -0.55), (1.3, 1.5, 0.55), X.I3, 0.3), 0.3)  # knee pad on the deck: braces the kneel
    for sx in (-1.5, 1.5):  # magazine pouches on the belt
        g.add(X.rbox(P.pelvis + P.Rp @ v3(sx, -2.7, 0.4), (0.6, 0.45, 0.65), P.Rp, 0.2), 0.1)


NOTES = {
    "figure": ("Vigilant marksman", "Kestrel exosuit body kneeling with the Needle marksman rifle aimed in both fists, integral keyed footplate; sockets for helm and backpack."),
    "helm": ("Vigil helm", "Line-standard helm: chevron split visor, keel crest, ear-pod fins; 1.6 mm D-flat peg."),
    "backpack": ("Power pack", "Line-standard power pack; 2.0 mm D-flat peg."),
}

if __name__ == "__main__":
    build_figure(PKG, S, pose, [rifle], "vigil", "power", NOTES)
