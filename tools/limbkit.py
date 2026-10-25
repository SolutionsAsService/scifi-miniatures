"""Reliable arms and hands for posed Kestrel figures: unified-CAD-MCP miniature_limb.arm_plan primitives -> sdfkit shapes.

    import limbkit
    kw = limbkit.outboard_poles(pose_kwargs, fists)         # elbow poles that keep each elbow on its own side of the chest
    P = X.Pose(**kw, fists=fists)
    plans = limbkit.plan_arms(P, hands, height=31.0)         # arm_plan on the Pose's own shoulder/elbow/wrist; raises if a check fails
    limbkit.add_arms(g, plans)                               # g.add(...) every primitive: tapered arm, bracer, bare wrist, palm, 4 fingers, thumb

Why (Legion Centurion 0.1-0.3): the arm came out missing or hidden: an IK elbow crossed the chest midline (the upper arm lived inside the
torso), the bracer swallowed the hand, the hand was a blob behind the pauldron. arm_plan builds every segment with 0.5 mm overlaps, stops
the bracer 1.3 mm short of the wrist and wraps four fingers round the grip; limbcheck.py then measures the built STL.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exosuit as X  # noqa: E402
from sdfkit import rbox, round_cone, sphere, tube, v3  # noqa: E402

_PATHS = (Path(r"E:\unified-CAD-MCP\src"), Path(__file__).resolve().parents[2] / "unified-CAD-MCP" / "src")
_src = next((p for p in _PATHS if (p / "unified_cad_mcp" / "miniature_limb.py").exists()), None)
if _src is None:
    raise ImportError("unified-CAD-MCP miniature_limb.py not found next to this repo")
sys.path.insert(0, str(_src))
from unified_cad_mcp import miniature_limb as ML  # noqa: E402  (imports fastmcp/pydantic: use the unified venv or `pip install pydantic fastmcp`)


def body_frame(P, i):
    """Torso axis point and the unit direction from the torso axis out toward arm i (0 = right, -x; 1 = left, +x)."""
    out = P.Rc @ v3(-1.0 if i == 0 else 1.0, 0, 0)
    return P.chest, out


def outboard_poles(kw, fists, margin=0.8):
    """Pick an elbow pole per arm so the elbow stays >= margin mm outboard of the torso midline and not inside the cuirass. Returns kw with elbow_poles."""
    kw = dict(kw)
    cands = [(0.0, 0.0, -1.0), (-1.0, 0.6, -0.5), (-1.0, 1.2, -0.4), (-1.0, 0.0, -0.8), (-0.6, 1.0, -1.0), (-1.0, -0.4, -0.6), (-0.3, 1.0, -1.0)]
    chosen = []
    for i in range(2):
        best = None
        for c in cands:
            pole = (c[0] if i == 0 else -c[0], c[1], c[2])
            kw2 = dict(kw, elbow_poles=tuple(pole if j == i else kw.get("elbow_poles", ((-1, 1.2, -0.4), (1, 1.2, -0.4)))[j] for j in range(2)))
            try:
                P = X.Pose(fists=fists, **kw2)
            except SystemExit:
                continue
            ctr, out = body_frame(P, i)
            side = float((P.elbow[i] - ctr) @ out)
            if best is None or side > best[0]:
                best = (side, pole)
            if side >= margin + 1.5:
                best = (side, pole)
                break
        chosen.append(best[1] if best else kw.get("elbow_poles", ((-1, 1.2, -0.4), (1, 1.2, -0.4)))[i])
    kw["elbow_poles"] = tuple(chosen)
    return kw


def plan_arms(P, hands, height=31.0, process="msla_resin", grip_length=3.2, grip_radius=0.95, strict=True):
    """arm_plan for both arms on the Pose's own joints. hands[i] = {grip, axis} (legion_centurion3.resolve3). Raises when a check fails."""
    plans = []
    for i in range(2):
        ctr, out = body_frame(P, i)
        pl = ML.arm_plan(height, tuple(P.sh[i]), tuple(hands[i]["grip"]), grip_axis=tuple(hands[i]["axis"]), grip_radius_mm=grip_radius, grip_length_mm=grip_length,
                         process=process, elbow=tuple(P.elbow[i]), wrist=tuple(P.wrist[i]), outward=tuple(out), body_center=tuple(ctr), lateral_out=tuple(out))
        bad = [c["name"] for c in pl["checks"] if not c["pass"]]
        if bad and strict:
            raise SystemExit(f"arm {i} plan fails: {bad}; change the pose (outboard_poles) or the hand target")
        plans.append(pl)
    return plans


def shapes(plan):
    out = []
    for p in plan["primitives"]:
        k = p["kind"]
        if k == "round_cone":
            a, b = v3(p["a"]), v3(p["b"])
            out.append((p["name"], sphere(a, p["r0"]) if np.allclose(a, b) else round_cone(a, b, p["r0"], p["r1"])))
        elif k == "tube":
            out.append((p["name"], tube([v3(q) for q in p["points"]], p["r"])))
        elif k == "rbox":
            R = np.stack([v3(a) for a in p["axes"]], axis=1)
            out.append((p["name"], rbox(v3(p["center"]), tuple(p["half"]), R, p.get("round", 0.2))))
    return out


def add_arms(g, plans, k=0.12):
    for pl in plans:
        for _, s in shapes(pl):
            g.add(s, k)
