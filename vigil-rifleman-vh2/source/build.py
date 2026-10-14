#!/usr/bin/env python3
"""Vigilant Rifleman 0.3: the Mk II advancing pose wearing the VH2-01 Lineguard helm (tools/vh2.py).

Run: ~/ai-stack/venvs/sculpt/bin/python source/build.py
Frame: mm, z up, base underside at z = 0, the figure faces -y. Pose numbers from spec/vigil-rifleman-vh2.spec.json
(identical to vigil-rifleman-mk2); the armour kit is tools/exosuit.py, the helm tools/vh2.py. The 0.1 / 0.2 packages are
untouched.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import exosuit as X  # noqa: E402
import sdfkit  # noqa: E402
import vh2  # noqa: E402
from render import render  # noqa: E402
from sdfkit import unit, v3  # noqa: E402
from vigil import build_figure  # noqa: E402

import freecadshim  # noqa: E402

freecadshim.use()   # STEP export through $FREECAD_PYTHON / the local FreeCAD shim (tools/freecadshim.py)

S = json.loads((PKG / "spec" / "vigil-rifleman-vh2.spec.json").read_text())
pz = S["pose"]
d = unit(pz["rifle"]["dir"])
M = X.place(v3(pz["rifle"]["stock"]) + d * 3.6, d, (0, 0, 1))          # stock butt in the shoulder, grip 3.6 mm ahead
grip, fore = X.apply(M, (0, 0, 0)), X.apply(M, (2.9, 0, -0.2))
pose = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"],
              feet_yaw=pz["feet_yaw"], fists=(grip, fore), elbow_poles=pz["elbow_poles"], knee_poles=pz["knee_poles"],
              head_yaw=pz["head_yaw"])


def rifle(g, P):
    g.add(X.lance_rifle().moved(M))
    down = X.apply(M, (-0.24, 0, -0.97)) - grip
    X.fist(g, grip, down, grip - P.elbow[0])
    X.fist(g, fore, down, fore - P.elbow[1])
    for sx in (-1.5, 1.5):                                                  # magazine pouches on the belt
        g.add(X.rbox(P.pelvis + P.Rp @ v3(sx, -2.7, 0.4), (0.6, 0.45, 0.65), P.Rp, 0.2), 0.1)


# build_figure() asks exosuit.helm(variant) for the helm part; route "vh2-*" variants to the VH2 library
_exo_helm = X.helm
X.helm = lambda variant="vigil", h=0.06: vh2.helm(S["helm"]["ident"], 0.05) if variant.startswith("vh2") else _exo_helm(variant, h)

NOTES = {
    "figure": ("Vigilant rifleman", "Kestrel exosuit body with Lance rifle in both fists, integral keyed footplate; sockets for helm and backpack."),
    "helm": ("VH2-01 Lineguard helm", "Second-generation line helm: gull-wing wrap visor split by the keel bar, layered plates, V-prow respirator; 1.6 mm D-flat peg."),
    "backpack": ("Power pack", "Spine power pack with twin manoeuvring nozzles; 2.0 mm D-flat peg."),
}


def head_closeup(rep):
    """Close render of the helm on the figure (3/4 and side), cropped round the head."""
    import trimesh
    up = PKG / "build" / "upright"
    H0 = X.BASES[S["base"]["d"]]["h"]
    lift = sdfkit.translate(0, 0, H0)
    fig = trimesh.load(up / "figure.stl", process=True)
    helm = trimesh.load(up / "helm.stl", process=True)
    pack = trimesh.load(up / "backpack.stl", process=True)
    fig.apply_transform(lift)
    helm.apply_transform(lift @ X.helm_placement(pose))
    pack.apply_transform(lift @ X.pack_placement(pose))
    c = helm.bounds.mean(axis=0)
    box = (c - 7.5, c + 7.5)
    parts = []
    for m, col in ((fig, "#7d8c96"), (helm, "#8a98a1"), (pack, "#5d6a73")):
        keep = np.all((m.triangles_center > box[0]) & (m.triangles_center < box[1]), axis=1)
        if keep.any():
            sub = m.submesh([np.nonzero(keep)[0]], append=True)
            parts.append((sub, col))
    render(parts, PKG / "images" / "vigil-rifleman-vh2-head.png", views=((-30, 8, "3/4 front"), (0, 4, "front"), (60, 6, "3/4 left")), size=520,
           title="VH2-01 Lineguard on the rifleman (head and shoulders)")


if __name__ == "__main__":
    rep = build_figure(PKG, S, pose, [rifle], "vh2-01", "power", NOTES)
    head_closeup(rep)
