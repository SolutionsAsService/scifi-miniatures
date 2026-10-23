"""Renders for the Wayfarer package (transport_kit z-buffer rasteriser: flat shading, key/fill/rim lights fixed in the
world, ink lines on creases and depth steps, soft ground shadow). Called by source/build.py.

Camera convention (transport_kit.camera): az 0 = camera in front of the vehicle (+x), 90 = on the vehicle's left (+y),
el = elevation in degrees. Every sheet states its views; renders are evidence of shape, not of paint or material.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import transport_kit as TK

AMBER = "#c9a246"
COLOR_CREST = False     # R2 (Debord/Brancusi): renders are evidence of shape; the printed kit is one grey


def crest_split(m, S):
    """Colour the keel-crest faces amber: faces near the centreline standing proud of the glacis / roof."""
    H = S["hull"]
    RZ = H["roof_z"]
    c = m.triangles_center
    zg = RZ - (c[:, 0] - H["glacis_x"]) * (RZ - 25.5) / (H["x_bow"] - H["glacis_x"])
    top = np.where(c[:, 0] > H["glacis_x"], zg, RZ)
    if not COLOR_CREST:
        return [(m, None)]
    mask = (np.abs(c[:, 1]) < 1.45) & (c[:, 2] > top + 0.25) & (c[:, 0] > 16.5)
    if not mask.any():
        return [(m, None)]
    a = m.submesh([np.nonzero(~mask)[0]], append=True)
    b = m.submesh([np.nonzero(mask)[0]], append=True)
    return [(a, None), (b, AMBER)]


def scene_parts(asm, S, swap=None):
    out = []
    for name, stl, m, group, col, note, ex in asm:
        if swap and name in swap:
            m = swap[name]
            if m is None:
                continue
        if stl.startswith("hull"):
            for sub, c in crest_split(m, S):
                out.append((sub, c or col))
        else:
            out.append((m, col))
    return out


def sheet_hero(parts, path, title, sub, notes, az=38, el=22, W=1800, H=1150, ss=2, figure=True, xfig=None):
    sc_parts = list(parts)
    if figure:
        sc_parts += TK.figure_parts(pos=xfig or (60, 52, 0), yaw=115)
    sc = TK.Scene(sc_parts)
    x0, x1, y0, y1 = sc.extent(az, el)
    ih = H - 220
    k = min((W - 160) / (x1 - x0), (ih - 60) / (y1 - y0))
    im = TK.raster(sc, az, el, k * ss, W * ss, ih * ss, shadow=True).resize((W, ih), Image.LANCZOS)
    sheet = Image.new("RGB", (W, H), TK.BG)
    sheet.paste(im, (0, 120), im)
    dr = ImageDraw.Draw(sheet)
    dr.text((40, 26), title, font=TK.font(40, True), fill=(28, 32, 40))
    dr.text((40, 78), sub, font=TK.font(22), fill=(70, 76, 86))
    TK._scalebar(dr, 40, H - 70, k, 50)
    y = H - 64
    for line in notes:
        dr.text((W - 40, y), line, font=TK.font(18), fill=(70, 76, 86), anchor="ra")
        y += 24
    dr.text((W - 40, 34), "PRINT KIT RENDER · manifold3d CSG", font=TK.font(18, True), fill=(160, 120, 40), anchor="ra")
    dr.text((W - 40, 60), "Aster Compact · Vigil support vehicles · 1:56", font=TK.font(18), fill=(90, 96, 106), anchor="ra")
    sheet.save(path)
    return path


def sheet_turn(parts, path, title, views=((38, 20, "3/4 front"), (0, 3, "front"), (90, 2, "left side"), (205, 16, "3/4 rear")),
               P=700, ss=2):
    sc = TK.Scene(parts)
    ks = []
    for az, el, _ in views:
        x0, x1, y0, y1 = sc.extent(az, el)
        ks.append(min((P - 60) / (x1 - x0), (P - 90) / (y1 - y0)))
    k = min(ks)      # one common scale for all panels
    W = P * len(views)
    sheet = Image.new("RGB", (W, P + 60), TK.BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((20, 14), title, font=TK.font(26, True), fill=(28, 32, 40))
    for i, (az, el, label) in enumerate(views):
        im = TK.raster(sc, az, el, k * ss, P * ss, P * ss, shadow=False).resize((P, P), Image.LANCZOS)
        sheet.paste(im, (i * P, 60), im)
        dr.text((i * P + 16, 64), f"{label} (az {az}, el {el})", font=TK.font(18, True), fill=(80, 86, 96))
    TK._scalebar(dr, W - 420, P + 10, k, 50)
    sheet.save(path)
    return path


def render_all(PKG, S, asm, parts, st, ramp_open_A, hatch_open_As):
    PKG = Path(PKG)
    panel = PKG / "build" / "panel"
    panel.mkdir(parents=True, exist_ok=True)
    sp = scene_parts(asm, S)
    name = S["name"]
    lo = np.min([m.bounds[0] for _, _, m, *_ in asm], axis=0)
    hi = np.max([m.bounds[1] for _, _, m, *_ in asm], axis=0)
    dims = hi - lo
    notes = [f"assembled {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm at 1:56  ({dims[0] * 0.056:.2f} x {dims[1] * 0.056:.2f} x {dims[2] * 0.056:.2f} m)",
             "Vigilant proxy (32 mm base) for scale; lights fixed in the world"]
    sub = "Wheeled 8x8 amphibious APC · AW-8A standard, Tally RWS · stage %d" % st if st < 6 else "Wheeled 8x8 amphibious APC · AW-8A standard, Tally RWS on the 30 mm ring"
    outs = [sheet_hero(sp, panel / f"stage{st}-hero.png", name, sub, notes),
            sheet_turn(sp, panel / f"stage{st}-turnaround.png", f"{name} · stage {st} · orthographic turnaround, common scale")]
    if st >= 5 and ramp_open_A is not None:
        swap = {}
        ramp = [x for x in asm if x[1] == "ramp"][0]
        ro = parts["ramp"][0].copy()
        ro.apply_transform(ramp_open_A)
        swap[ramp[0]] = ro
        hatches = [x for x in asm if x[1] == "hatch"]
        for (nm, *_), A in zip(hatches[:2], hatch_open_As[:2]):
            hm = parts["hatch"][0].copy()
            hm.apply_transform(A)
            swap[nm] = hm
        for nm, *_ in hatches[2:]:
            swap[nm] = None
        dp = scene_parts(asm, S, swap)
        outs.append(sheet_hero(dp, panel / f"stage{st}-deployed.png", name + " · deployed",
                               "Ramp open on its drop-in hinge, two hatches swung open, two lifted off", notes, az=215, el=30,
                               xfig=(-92, 26, 0)))
    if st >= 6:
        img = PKG / "images"
        img.mkdir(exist_ok=True)
        import shutil
        shutil.copy(outs[0], img / f"{S['id']}-hero.png")
        shutil.copy(outs[1], img / f"{S['id']}-turnaround.png")
        if len(outs) > 2:
            shutil.copy(outs[2], img / f"{S['id']}-deployed.png")
    print("images:", [str(o) for o in outs])
    return outs
