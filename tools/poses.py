"""Pose presets for the Kestrel figures: resolves unified-CAD-MCP miniature_pose presets into a real exosuit.Pose.

The preset data and the seeded variation live in unified-CAD-MCP (src/unified_cad_mcp/miniature_pose.py, stdlib only, loaded
here by path so no MCP stack is needed). This module turns a variant into world fists (offsets from each shoulder, a
weapon frame for the grip hands) and builds the Pose, retrying with a smaller jitter when a hand is out of reach:

    from poses import pose_for
    pose, hands = pose_for("dynamic-shoulder-aim", seed=3)           # hands: per-hand dicts with world 'fist' (+ 'M' weapon frame)
    # hands[0]['M'] is the weapon frame (x along the weapon): g.add(weapon_shape.moved(hands[0]['M']))

    from poses import squad
    figs = squad(["rifleman"], count=6, seed=2)                        # six different stances

Hand types: weapon (grip + direction; M = the weapon frame), weapon_up (muzzle up: sidearm), weapon_vert (long weapon held vertically at the side, muzzle up), on_weapon (second hand at weapon
x, z = fore; set the real foregrip with `fore=` if the weapon has one), point (pointing hand: dir, reach), free.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exosuit as X  # noqa: E402
from sdfkit import unit, v3  # noqa: E402

_PATHS = (Path(r"E:\unified-CAD-MCP\src\unified_cad_mcp\miniature_pose.py"),
          Path(__file__).resolve().parents[2] / "unified-CAD-MCP" / "src" / "unified_cad_mcp" / "miniature_pose.py")
spec = next((importlib.util.spec_from_file_location("miniature_pose", p) for p in _PATHS if p.exists()), None)
if spec is None:
    raise ImportError("unified-CAD-MCP miniature_pose.py not found next to this repo")
MP = importlib.util.module_from_spec(spec)
sys.modules["miniature_pose"] = MP
spec.loader.exec_module(MP)

Z = v3(0, 0, 1)
PRESETS = MP.PRESETS


def _pose_kwargs(v):
    p = v["pose"]
    kw = dict(pelvis=p["pelvis"], yaw=p["yaw"], lean=p["lean"], twist=p["twist"], ankles=p["ankles"], feet_yaw=p["feet_yaw"],
              knee_poles=p["knee_poles"], elbow_poles=p["elbow_poles"], head_yaw=p["head_yaw"])
    if v.get("knees"):
        kw["knees"] = tuple(v["knees"])
    return kw


def resolve(v, fore=None, shrink=1.0):
    """Variant -> (Pose, hands). Raises SystemExit (exosuit.ik) when a hand is out of reach."""
    kw = _pose_kwargs(v)
    probe = X.Pose(**kw)
    hands = [dict(h) for h in v["hands"]]
    fists = [None, None]
    for i, h in enumerate(hands):                                    # pass 1: grips, free hands, pointing hands
        sh = probe.sh[i]
        t = h["type"]
        if t in ("weapon", "weapon_up", "weapon_vert"):
            d = unit(v3(h["dir"]))
            h["fist"] = sh + v3(h["off"]) * shrink
            h["M"] = X.place(h["fist"], d, {"weapon": Z, "weapon_up": (0, 1, 0), "weapon_vert": (0, -1, 0)}[t])
            fists[i] = h["fist"]
        elif t == "free":
            h["fist"] = sh + v3(h["off"]) * shrink
            fists[i] = h["fist"]
        elif t == "point":
            h["fist"] = sh + unit(v3(h["dir"])) * h["reach"] * shrink
            fists[i] = h["fist"]
    for i, h in enumerate(hands):                                    # pass 2: hands on the other hand's weapon
        if h["type"] == "on_weapon":
            src = next(o for o in hands if o["type"] == "weapon")
            fx, fz = fore if fore else h["fore"]
            h["fist"] = X.apply(src["M"], (fx, 0, fz))
            h["M"] = src["M"]
            fists[i] = h["fist"]
    pose = X.Pose(fists=tuple(fists), **kw)
    return pose, hands


def pose_for(preset, seed=0, amount=1.0, mirror=False, fore=None):
    """The named preset (seeded variation) as (Pose, hands). On an unreachable hand the jitter amount and then the hand
    offsets are reduced until the IK solves; the variant actually used is returned as hands[0]... see `variant`."""
    last = None
    for a, shrink in ((amount, 1.0), (amount * 0.5, 1.0), (0.0, 1.0), (0.0, 0.94), (0.0, 0.88)):
        v = MP.make_variant(preset, seed, a, mirror)
        try:
            pose, hands = resolve(v, fore, shrink)
            pose.variant = v
            return pose, hands
        except SystemExit as e:
            last = e
    raise SystemExit(f"{preset} seed {seed}: no reachable pose ({last})")


def squad(roles, count=6, seed=0, min_distance=0.25, **kw):
    """`count` different stances for a squad: list of (name, Pose, hands) validated against the IK."""
    gen = MP.generate(roles=roles, count=count, seed=seed, min_distance=min_distance, **kw)
    out = []
    for v in gen["poses"]:
        pose, hands = resolve(v)
        pose.variant = v
        out.append((v["preset"], pose, hands))
    return out


def validate_all(seeds=range(12)):
    """Every preset x seed (and mirrored where allowed) must resolve (possibly after the retry ladder)."""
    bad = []
    for name, p in PRESETS.items():
        for s in seeds:
            for m in ((False, True) if p["mirror_ok"] else (False,)):
                try:
                    pose_for(name, s, 1.0, m)
                except SystemExit as e:
                    bad.append((name, s, m, str(e)[:80]))
    return bad
