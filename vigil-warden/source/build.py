#!/usr/bin/env python3
"""Vigilant Warden (squad leader, pointing, sidearm raised): Aster Compact Vigilant line, 30 mm heroic, MSLA resin.

Run: /mnt/d/ai-stack/venvs/scifi-sculpt/bin/python source/build.py
Frame: mm, z up, base underside at z = 0, the figure faces -y. Pose numbers from spec/vigil-warden.spec.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import exosuit as X  # noqa: E402
from sdfkit import bezier, frame, rbox, unit, v3  # noqa: E402
from vigil import build_figure  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-warden.spec.json").read_text())
pz = S["pose"]
probe = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"], feet_yaw=pz["feet_yaw"])
pdir = unit(pz["point"]["dir"])
hand = probe.sh[1] + pdir * pz["point"]["reach"]                       # left hand, nearly straight arm
sa = pz["sidearm"]
M = X.place(v3(sa["grip"]), unit(sa["dir"]), (0, 1, 0))               # muzzle up, grip toward the front
grip = X.apply(M, (0, 0, 0))
pose = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"],
              feet_yaw=pz["feet_yaw"], fists=(grip, hand), elbow_poles=pz["elbow_poles"], head_yaw=pz["head_yaw"])


def gear(g, P):
    g.add(X.sidearm().moved(M))
    X.fist(g, grip, X.apply(M, (-0.28, 0, -0.96)) - grip, grip - P.elbow[0])
    palm = unit(np.cross(pdir, v3(0, 0, 1)) * -1)                   # palm turned inward
    X.open_hand(g, hand, pdir, palm, 1)
    # tabard: a cloth panel swept from the belt over the leading thigh (rounded-rectangle section along a curve)
    a = P.pelvis + P.Rp @ v3(0.15, -2.55, 0.55)
    pts = bezier(a, a + v3(0.2, -1.2, -2.5), P.knee[1] + v3(-1.4, -1.6, 2.2), P.knee[1] + v3(-1.2, -1.75, 0.3), 14)
    for j in range(len(pts) - 1):
        t = j / (len(pts) - 2)
        R = frame(pts[j + 1] - pts[j], P.fwd)
        g.add(rbox((pts[j] + pts[j + 1]) / 2, (1.55 + 0.35 * t, 0.42, float(np.linalg.norm(pts[j + 1] - pts[j])) / 2 + 0.15), R, 0.2), 0.2)
    # rank plate on the left shoulder cap
    g.add(rbox(P.sh[1] + P.Rc @ v3(1.2, -0.4, 1.75), (0.7, 0.55, 0.3), P.Rc, 0.15), 0.1)


NOTES = {
    "figure": ("Vigilant warden", "Kestrel exosuit body pointing the advance, Spur sidearm raised, cloth tabard; integral keyed footplate."),
    "helm": ("Warden helm", "Command helm: chevron split visor, keel crest with a crest blade, whip antenna; 1.6 mm D-flat peg."),
    "backpack": ("Comms pack", "Long-range comms pack: whip antenna with ball tip, dish housing, twin nozzles; 2.0 mm D-flat peg."),
}

if __name__ == "__main__":
    build_figure(PKG, S, pose, [gear], "warden", "comms", NOTES)
