#!/usr/bin/env python3
"""Images for the Vigilant Heavy Gunner Mk2: turnaround and hero of the assembled figure (figure + helm + drum pack +
base), the heavy weapons display sheet (side profile, one common scale) and the parts as printed.
Renderer: tools/render.py lighting; render copies are simplified with manifold3d (preview only, never the print STLs).
Run: ~/projects/venvs/scifi-sculpt/bin/python source/build.py --images
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG.parent / "vigil-arsenal-vw3" / "source"))
from render import render  # noqa: E402
from sdfkit import decimate  # noqa: E402

FIG = ("figure", "helm", "backpack", "base")


def _assembled(pkg):
    """Assembled meshes from the viewer manifest placements applied to the print STLs."""
    man = json.loads((pkg / "viewer" / "manifest.json").read_text()) if (pkg / "viewer" / "manifest.json").exists() else None
    rep = json.loads((pkg / "reports" / "build.json").read_text())
    out = []
    for stl, col in zip(FIG, ("#8a8f96", "#c8a24a", "#5b6168", "#3d4248")):
        m = trimesh.load(pkg / "build" / "upright" / f"{stl}.stl")
        m.apply_transform(np.array(rep["placements"][stl]))
        out.append((m, col))
    return out, man


def all_images(pkg, k=None):
    pkg = Path(pkg)
    out = pkg / "images"
    out.mkdir(exist_ok=True)
    mid = "vigil-heavy-mk2"
    if k is not None:
        fig = [(decimate(p["asm"], 90_000 if p["stl"] == "figure" else 40_000), p["color"]) for p in k.parts if p["stl"] in FIG]
        bits = [(p["name"], p["mesh"]) for p in k.parts if p["stl"] not in FIG]
        parts = [(decimate(p["mesh"], 60_000), p["color"]) for p in k.parts if p["stl"] in FIG]
    else:
        fig, _ = _assembled(pkg)
        fig = [(decimate(m, 90_000), c) for m, c in fig]
        rep = json.loads((pkg / "reports" / "build.json").read_text())
        bits = [(rep["names"][s], trimesh.load(pkg / "build" / "upright" / f"{s}.stl")) for s in rep["parts"] if s not in FIG]
        parts = [(decimate(trimesh.load(pkg / "build" / "upright" / f"{s}.stl"), 60_000), c)
                 for s, c in (("figure", "#8a8f96"), ("helm", "#c8a24a"), ("backpack", "#5b6168"), ("base", "#3d4248"))]
    paths = [render(fig, out / f"{mid}-turnaround.png", views=((0, 8, "front"), (-90, 8, "right"), (180, 8, "back"), (-35, 18, "3/4")), size=760),
             render(fig, out / f"{mid}-hero.png", views=((-38, 16, "Vigilant heavy gunner Mk2"),), size=1100)]
    # parts as printed, side by side
    lay, x = [], 0.0
    for m, c in parts:
        m = m.copy()
        lo, hi = m.bounds
        m.apply_translation((x - lo[0], -(lo[1] + hi[1]) / 2, -lo[2]))
        x += (hi[0] - lo[0]) + 4.0
        lay.append((m, c))
    paths.append(render(lay, out / f"{mid}-parts.png", views=((-30, 22, "parts as printed"),), size=1100))
    import sheet as vw3sheet                                        # the VW3 side-profile sheet renderer
    items = [(lbl.split(" ")[0], " ".join(lbl.split(" ")[1:]).replace(" (loose)", ""), decimate(m, 80_000)) for lbl, m in bits]
    paths.append(heavy_sheet(vw3sheet, items, out / f"{mid}-heavies.png"))
    return paths


def heavy_sheet(vs, items, path, k=34.0):
    from PIL import Image, ImageDraw
    R = vs.view_matrix(0, 0)
    W = int(max(m.bounds[1][0] - m.bounds[0][0] for _, _, m in items) * k + 120)
    heights = [(m.bounds[1][2] - m.bounds[0][2]) * k + 80 for _, _, m in items]
    top, ss = 90, 2
    H = int(top + sum(heights) + 50)
    img = Image.new("RGB", (W * ss, H * ss), vs.BG)
    y, labels = top, []
    for (ident, name, m), hgt in zip(items, heights):
        bb = m.bounds
        vs.draw_mesh(img, m, R, k, W / 2, y + (hgt - 44) / 2, ((bb[0][0] + bb[1][0]) / 2, (bb[0][2] + bb[1][2]) / 2), vs.GUN, ss)
        ext = bb[1] - bb[0]
        labels.append(((24, y + hgt - 36), f"{ident}  {name}   ({ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm)"))
        y += hgt
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    d.text((24, 22), "Vigil heavy weapons VHW-01..03 (loose bits)", fill=vs.INK, font=vs.font(30))
    d.text((24, 58), f"Side profile, orthographic, common scale {k:.0f} px/mm (30 mm heroic). Muzzle to the right.", fill=(80, 84, 92), font=vs.font(17))
    for (x, yy), t in labels:
        d.text((x, yy), t, fill=vs.INK, font=vs.font(18))
    vs.scale_bar(d, W, H, k)
    img.save(path)
    return path
