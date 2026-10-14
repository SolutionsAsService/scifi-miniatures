"""Package builder shared by every Aster Compact Vigilant figure: sculpt the parts, export the package, render images.

A package build.py supplies the pose (spec) and the figure-specific extras (hands, weapon, gear); this module turns
them into the same part set every figure ships with: figure (with integral footplate), helm, backpack, 32 mm base.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import exosuit as X
from render import render
from sdfkit import Package, translate

COLORS = {"figure": "#7d8c96", "helm": "#8a98a1", "backpack": "#5d6a73", "base": "#6c6863"}


def build_figure(pkg, spec, pose, extras, helm_variant, pack_variant, notes):
    pkg = Path(pkg)
    mid = spec["id"]
    H0 = X.BASE["h"]
    body = X.figure(pose, h=spec.get("voxel_mm", 0.085), extras=extras, bbox=spec.get("bbox")).mesh("figure", 140_000)
    helm = X.helm(helm_variant).mesh("helm", 50_000)
    pack = X.backpack(pack_variant).mesh("backpack", 40_000)
    base = X.base32(pose, seed=spec.get("base_seed", 1)).mesh("base", 90_000)
    k = Package(mid, pkg)
    lift = translate(0, 0, H0)
    k.add(notes["figure"][0], body, stl="figure", color=COLORS["figure"], group="figure", note=notes["figure"][1],
          explode=(0, 0, 6), placement=lift)
    k.add(notes["helm"][0], helm, stl="helm", color=COLORS["helm"], group="helm", note=notes["helm"][1],
          explode=(0, 0, 14), placement=lift @ X.helm_placement(pose))
    back = pose.Rc @ np.array([0, 1.0, 0])
    k.add(notes["backpack"][0], pack, stl="backpack", color=COLORS["backpack"], group="backpack", note=notes["backpack"][1],
          explode=tuple(np.round(back * 9 + np.array([0, 0, 6]), 2)), placement=lift @ X.pack_placement(pose))
    k.add("32 mm base", base, stl="base", color=COLORS["base"], group="base",
          note="32 mm round deck-plate base: keyed recess for the footplate, 5 x 2 mm magnet pocket vented to the rim.")
    rep = k.write()
    # measured figure heights (assembled, above the base top): visor line and crown
    asm_helm = [p for p in k.parts if p["stl"] == "helm"][0]["asm"]
    crown = float(asm_helm.bounds[1][2] - H0)
    visor = float(pose.neck_cut[2] + X.HEAD_UP + 0.12 * X.HS)
    rep["heights_above_base_top_mm"] = {"visor_line": round(visor, 2), "crown": round(crown, 2),
                                        "method": "visor: neck cut + helm centre height + lens centre offset (exosuit.py); "
                                                  "crown: assembled helm mesh max z minus the base top"}
    if helm_variant == "warden":
        rep["heights_above_base_top_mm"]["crown_note"] = "includes the command crest and whip antenna"
    (pkg / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    images(pkg, mid, [(p["asm"], p["color"]) for p in k.parts], spec["name"])
    return rep


def build_loose(pkg, spec, parts):
    """Bits packages: parts laid out side by side for the viewer, each printed on its own."""
    pkg = Path(pkg)
    k = Package(spec["id"], pkg)
    for name, mesh, stl, color, note, at in parts:
        k.add(name, mesh, stl=stl, color=color, group=stl, note=note, explode=(0, 0, 4), placement=translate(*at))
    rep = k.write()
    images(pkg, spec["id"], [(p["asm"], p["color"]) for p in k.parts], spec["name"])
    return rep


def images(pkg, mid, meshes, title):
    out = Path(pkg) / "images"
    out.mkdir(exist_ok=True)
    render(meshes, out / f"{mid}-turnaround.png", size=480, title=f"{title}: 3/4, front, right side, back (orthographic)")
    render(meshes, out / f"{mid}-hero.png", views=((-32, 10, "3/4 front"),), size=900)
