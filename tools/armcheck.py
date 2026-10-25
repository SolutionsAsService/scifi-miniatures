"""Arm / hand check for a posed Kestrel figure: runs unified-CAD-MCP miniature_arm.arm_check on the Pose.

    import armcheck
    r = armcheck.check(P, hands, weapon_M=M, weapon_half=(7.5, 1.0, 1.4), weapon_c=(5, 0, 1.5))
    print(r["fix"])

`hands` = [{fist, grip, axis}] per arm (legion_centurion3.resolve3 returns it; for older poses grip = fist, axis = weapon M z).
Bodies: cuirass, pelvis, both pauldron domes, head, the weapon as a thin ellipsoid. Cape not included (it hangs behind).
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exosuit as X  # noqa: E402
from sdfkit import v3  # noqa: E402

_PATHS = (Path(r"E:\unified-CAD-MCP\src\unified_cad_mcp\miniature_arm.py"),
          Path(__file__).resolve().parents[2] / "unified-CAD-MCP" / "src" / "unified_cad_mcp" / "miniature_arm.py")
_spec = next((importlib.util.spec_from_file_location("miniature_arm", p) for p in _PATHS if p.exists()), None)
if _spec is None:
    raise ImportError("unified-CAD-MCP miniature_arm.py not found next to this repo")
MA = importlib.util.module_from_spec(_spec)
sys.modules["miniature_arm"] = MA
_spec.loader.exec_module(MA)

_rows = lambda R: tuple(tuple(float(x) for x in R[i]) for i in range(3))  # noqa: E731


def bodies(P, weapon_M=None, weapon_c=(5.0, 0, 1.5), weapon_half=(7.5, 1.0, 1.4)):
    Rc, Rp = P.Rc, P.Rp
    out = [dict(name="chest", center=list(P.chest + Rc @ v3(0, 0.05, 0.35)), radii=[4.6, 3.05, 3.4], rot=_rows(Rc)),
           dict(name="pelvis", center=list(P.pelvis + Rp @ v3(0, 0.1, 0.25)), radii=[2.85, 2.05, 2.1], rot=_rows(Rp)),
           dict(name="head", center=list(P.neck_cut + v3(0, 0, 2.9)), radii=[2.8, 2.8, 3.0])]
    for i, sgn in ((0, -1), (1, 1)):
        out.append(dict(name=f"pauldron_{i}", center=list(P.sh[i] + Rc @ v3(sgn * 1.55, 0, 1.35)), radii=[3.9, 4.1, 2.8], rot=_rows(Rc)))
    if weapon_M is not None:
        out.append(dict(name="weapon", center=list(X.apply(weapon_M, weapon_c)), radii=list(weapon_half), rot=_rows(weapon_M[:3, :3])))
    return out


def check(P, hands, weapon_M=None, **kw):
    arms = [dict(name=("right" if i == 0 else "left") + " arm", shoulder=list(P.sh[i]), elbow=list(P.elbow[i]), wrist=list(P.wrist[i]),
                 fist=list(P.fist[i]), grip=list(hands[i].get("grip", hands[i]["fist"])),
                 grip_axis=list(hands[i].get("axis", (weapon_M[:3, :3] @ v3(0, 0, -1)) if weapon_M is not None else v3(0, 0, -1))))
            for i in range(2)]
    return MA.arm_check(arms, bodies(P, weapon_M, **kw))
