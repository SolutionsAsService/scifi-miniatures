#!/usr/bin/env python3
"""Lantern-pattern Squad Drone Kit (SD-1 Wisp, SD-2 Tick, SD-C cradle): Aster Compact Vigil line, 1:56, MSLA resin.

Run: ~/projects/venvs/scifi-sculpt/bin/python source/build.py [part ...]
     (no arguments: the whole package; with part names: only those print meshes, into build/upright, for iteration)
Frame: mm, z up, parts face -y. Every key dimension from spec/lantern-drones.spec.json; sculpts in source/lantern.py.
Writes build/upright/*.stl, viewer/lantern-drones.parts.json, reports/build.json, images/*.png.
STEP: tools/sdfkit.write_step needs FreeCAD, which is not installed on this host, so the assembly STEP is skipped and
recorded as such in reports/build.json (no cad/*.step is produced).
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import trimesh
from scipy.ndimage import map_coordinates

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import sdfkit  # noqa: E402
import lantern as L  # noqa: E402
from render import render  # noqa: E402

S = json.loads((PKG / "spec" / "lantern-drones.spec.json").read_text())
VOX = S["voxel_mm"]
BUDGET = S["triangle_budget"]

# name -> (label, colour, ops factory, voxel key, note)
PARTS = {
    "wisp-a-recon": ("SD-1 Wisp A (recon)", "#7d8a78", lambda: L.wisp(S, "A"), "wisp",
                     "Chevron body, four ducted fans (0.85 mm walls, rotors 0.4 mm down), chin ball with split-chevron lenses; 1.8 mm stem socket."),
    "wisp-b-designator": ("SD-1 Wisp B (designator / munition)", "#76836f", lambda: L.wisp(S, "B"), "wisp",
                          "Wisp with an underslung laser designator pod (right) and a shaped-charge munition (left)."),
    "wisp-landed": ("SD-1 Wisp, landed (objective marker)", "#808c7a", lambda: L.wisp(S, "L"), "wisp",
                    "Legs and skids down, no stem socket: glue to a plain base as an objective marker."),
    "flight-stem": ("Flight stem 1.6 mm (printed)", "#b8c6cf", lambda: L.flight_stem(S), "stem",
                    "27 mm x 1.6 mm resin stem; a 1.6 mm clear acrylic rod cut to 27 mm fits the same sockets."),
    "tick-hull": ("SD-2 Tick hull + tracks", "#7d8a78", lambda: L.tick_hull(S), "tick",
                  "Chevron-prow hull, tracks with shoe grooves, road wheels, skirts, keel ridge; deck sockets for mast (1.2) and weapon (1.6)."),
    "tick-mast": ("SD-2 Tick periscope mast", "#68745f", lambda: L.tick_mast(S), "module",
                  "1.1 mm periscope shaft, sensor head with split-chevron lenses; 1.2 mm D-flat peg."),
    "tick-weapon-a-talon": ("Tick module A: Talon carbine mount", "#5d6560", lambda: L.talon_on_mount(S), "module",
                            "Turret ring, pintle and the VW-05 Talon carbine (tools/armory.py); 1.6 mm D-flat peg."),
    "tick-weapon-b-plough": ("Tick module B: mine-plough + charge layer", "#5d6560", lambda: L.plough(S), "module",
                             "Charge-layer box and a V mine-plough carried ahead of the prow; 1.6 mm D-flat peg."),
    "tick-weapon-c-relay": ("Tick module C: relay mast + smoke", "#5d6560", lambda: L.relay(S), "module",
                            "Relay box, telescopic antenna with dipole bar, two banks of smoke dischargers; 1.6 mm D-flat peg."),
    "sdc-cradle": ("SD-C cradle with folded Wisp", "#7d8a78", lambda: L.cradle(S), "cradle",
                   "Stowed Wisp (ducts stacked, covers on) on a cradle plate; standard 2.0 mm D-flat pack peg."),
    "sdc-pack-saddle": ("SD-C pack saddle (clips behind the spine pack)", "#56657a", None, "cradle",
                        "Caps the top and back of the line power pack (0.1 mm clear); 2.0 mm D-flat socket for the cradle."),
    "base-32-stem": ("32 mm base, stem socket", "#4a4d52", lambda: L.base(S, stem=True), "base",
                     "32 x 3 mm base, chevron deck plates, 5 x 2 mm magnet pocket vented to the rim, launch pad with a " + f"{S['stem']['lean_deg']:g} deg raked 1.8 mm stem socket."),
    "base-32-plain": ("32 mm base, plain", "#4a4d52", lambda: L.base(S, stem=False), "base",
                      "32 x 3 mm base, chevron deck plates, 5 x 2 mm magnet pocket vented to the rim (Tick, landed Wisp)."),
}


def power_pack():
    """The line-standard spine power pack (tools/exosuit.py) as a fit reference for the saddle: not a part of this kit."""
    import exosuit as X
    g = X.backpack("power", h=0.05)
    return g, g.mesh("reference power pack")


def build_mesh(name, hm=None):
    t0 = time.time()
    label, col, fn, vk, note = PARTS[name]
    ops = L.saddle(S, hm) if name == "sdc-pack-saddle" else fn()
    budget = S["triangle_budget_base"] if vk == "base" else BUDGET
    m = L.mesh_in_budget(ops, name, VOX[vk], budget, limit=int(budget * 1.15))
    print(f"{name}: {len(m.faces)} tris at {m.metadata['pitch_mm']} mm, vol {m.volume:.2f} mm3, "
          f"bbox {np.round(m.extents, 2).tolist()} ({time.time() - t0:.0f} s)", flush=True)
    return m


def place_on(R, t):
    return L.mat(R, t)


def assemble(meshes):
    """Assembly placements (4x4) for the viewer and the renders: two flying Wisps on stem bases, the Tick (module A),
    the landed Wisp, loose modules B and C, the cradle on its saddle."""
    B, st = S["base"], S["stem"]
    H0 = B["h"]
    sb = B["stem_boss"]
    u = L.stem_dir(S)
    Ru = sdfkit.rot((1, 0, 0), st["lean_deg"])                                 # z -> u
    W = S["wisp"]["stem_socket"]
    tick = S["tick"]
    out = []

    def flyer(x0, wisp_name):
        p = np.array([x0 + sb["xy"][0], sb["xy"][1], H0 + sb["h"] + 0.15])
        bottom = p - u * st["insert_base"]
        Lst = st["visible_mm"] + st["insert_wisp"] + st["insert_base"]
        top = bottom + u * Lst
        anchor = np.array([W["xy"][0], W["xy"][1], W["boss_bottom_z"] + st["insert_wisp"]])
        out.append(("base-32-stem", sdfkit.translate(x0, 0, 0), (0, 0, 0)))
        out.append(("flight-stem", place_on(Ru, bottom), (0, 0, 4)))
        out.append((wisp_name, place_on(Ru, top) @ sdfkit.translate(*(-anchor)), (0, 0, 8)))

    flyer(0.0, "wisp-a-recon")
    flyer(36.0, "wisp-b-designator")
    x = 72.0
    out.append(("base-32-plain", sdfkit.translate(x, 0, 0), (0, 0, 0)))
    out.append(("tick-hull", sdfkit.translate(x, 0, H0), (0, 0, 3)))
    mx, my = tick["mast_socket"]["xy"]
    wx, wy = tick["weapon_socket"]["xy"]
    out.append(("tick-mast", sdfkit.translate(x + mx, my, H0 + tick["deck_z"]), (0, 0, 7)))
    out.append(("tick-weapon-a-talon", sdfkit.translate(x + wx, wy, H0 + tick["deck_z"]), (0, 0, 7)))
    x = 108.0
    out.append(("base-32-plain", sdfkit.translate(x, 0, 0), (0, 0, 0)))
    out.append(("wisp-landed", sdfkit.translate(x, 0, H0 - S["wisp"]["landed_skid_z"]), (0, 0, 4)))
    out.append(("tick-weapon-b-plough", sdfkit.translate(66.0, -34.0, 0.0), (0, 0, 3)))
    out.append(("tick-weapon-c-relay", sdfkit.translate(86.0, -34.0, 0.0), (0, 0, 3)))
    sx, sy, sz = S["cradle"]["saddle_socket"]
    out.append(("sdc-pack-saddle", sdfkit.translate(0.0, -34.0, 8.0), (0, 0, 3)))
    out.append(("sdc-cradle", sdfkit.translate(0.0, -34.0 + sy, 8.0 + sz), (0, 4, 3)))
    return out


def trilinear_sdf(g, pts):
    idx = ((pts - g.lo) / g.h).T
    return map_coordinates(g.D, idx, order=1, mode="nearest")


def fits(meshes, pack_g, pack_m):
    """Measured fits: saddle on the pack, cradle peg in the saddle socket, stem in both sockets, assembled sizes."""
    sad, cra = meshes["sdc-pack-saddle"], meshes["sdc-cradle"]
    sx, sy, sz = S["cradle"]["saddle_socket"]
    cra_asm = cra.copy()
    cra_asm.apply_translation((sx, sy, sz))
    clear = trilinear_sdf(pack_g, sad.vertices)
    rep = {
        "saddle_on_pack": {"overlap_mm3": round(sdfkit.overlap_volume(sad, pack_m), 4),
                           "min_clearance_mm": round(float(clear.min()), 3),
                           "method": "manifold3d boolean intersection volume; clearance = pack signed distance field (exosuit.backpack('power'), 0.05 mm grid) sampled at every saddle vertex, minimum"},
        "cradle_in_saddle": {"overlap_mm3": round(sdfkit.overlap_volume(sad, cra_asm), 4)},
        "cradle_on_pack_stickout_mm": round(float(cra_asm.bounds[1][1]), 2),
        "cradle_folded_wisp_envelope_mm": [round(float(v), 2) for v in cra.extents],
    }
    t = meshes["tick-hull"].extents
    rep["tick_hull_extent_mm"] = [round(float(v), 2) for v in t]
    w = meshes["wisp-a-recon"]
    rep["wisp_a_extent_mm"] = [round(float(v), 2) for v in w.extents]
    return rep


def images(asm_parts, meshes, pack_m):
    out = PKG / "images"
    out.mkdir(exist_ok=True)
    allp = [(p["asm"], p["color"]) for p in asm_parts]
    render(allp, out / "lantern-drones-turnaround.png", size=480, title="Lantern drone kit: 3/4, front, right side, back (orthographic)")
    hero = [(p["asm"], p["color"]) for p in asm_parts
            if p["placement"] is not None and (p["placement"][0, 3] < 30 or 60 < p["placement"][0, 3] < 100) and p["placement"][1, 3] > -20]
    render(hero, out / "lantern-drones-hero.png", views=((-32, 14, "3/4 front: Wisp A on its raked stem, Tick with module A"),), size=900)
    views4 = ((-35, 18, "3/4 front"), (0, 2, "front"), (90, 2, "side (right)"), (0, 90, "top (front down)"))
    col = {n: PARTS[n][1] for n in PARTS}
    wis = []
    for i, n in enumerate(("wisp-a-recon", "wisp-b-designator", "wisp-landed")):
        m = meshes[n].copy()
        m.apply_translation((i * 20.0, 0, 0))
        wis.append((m, col[n]))
    render(wis, out / "lantern-drones-wisp.png", views=views4, size=480, title="SD-1 Wisp: A recon, B designator/munition, landed")
    ti = []
    tick = S["tick"]
    mx, my = tick["mast_socket"]["xy"]
    wx, wy = tick["weapon_socket"]["xy"]
    for i, n in enumerate(("tick-weapon-a-talon", "tick-weapon-b-plough", "tick-weapon-c-relay")):
        dx = i * 26.0
        for name, t in (("tick-hull", (dx, 0, 0)), ("tick-mast", (dx + mx, my, tick["deck_z"])), (n, (dx + wx, wy, tick["deck_z"]))):
            m = meshes[name].copy()
            m.apply_translation(t)
            ti.append((m, col[name]))
    render(ti, out / "lantern-drones-tick.png", views=views4, size=480, title="SD-2 Tick: module A Talon, B mine-plough, C relay + smoke")
    sx, sy, sz = S["cradle"]["saddle_socket"]
    c = meshes["sdc-cradle"].copy()
    c.apply_translation((sx, sy, sz))
    cr = [(pack_m, "#a2a7ad"), (meshes["sdc-pack-saddle"], col["sdc-pack-saddle"]), (c, col["sdc-cradle"])]
    render(cr, out / "lantern-drones-cradle.png", views=((145, 18, "3/4 back"), (90, 4, "side (right)"), (180, 6, "back"), (0, 90, "top")),
           size=480, title="SD-C cradle + saddle on the line power pack (grey: reference pack, not in this kit)")


def images_only(up, render_tris=40_000):
    """Renders in their own process from build/upright: each part is simplified for the render only (manifold3d,
    render_tris), never the print mesh. 13 parts x 150k triangles in one painter's-algorithm pass exceeded 1.5 GB."""
    meshes = {}
    for n in PARTS:
        m = trimesh.load(up / f"{n}.stl")
        meshes[n] = sdfkit.decimate(m, render_tris, n)
    parts = []
    for name, M, ex in assemble(meshes):
        a = meshes[name].copy()
        if M is not None:
            a.apply_transform(M)
        parts.append(dict(name=PARTS[name][0], stl=name, color=PARTS[name][1], placement=M, asm=a))
    _, pack_m = power_pack()
    images(parts, meshes, pack_m)


def main(only):
    t0 = time.time()
    up = PKG / "build" / "upright"
    up.mkdir(parents=True, exist_ok=True)
    pack_g = pack_m = hm = None
    # --reuse [part ...]: load every other part from build/upright (pitch.json), re-sculpt only the named ones, then
    # assemble, measure fits and render. Lets each part be sculpted in its own capped process (memory, 8 GB host).
    pj = up / "pitch.json"
    pitches = json.loads(pj.read_text()) if pj.exists() else {}
    if only and only[0] == "--images":
        images_only(up)
        print(f"images done in {time.time() - t0:.0f} s")
        return
    reuse = bool(only) and only[0] == "--reuse"
    if reuse:
        only = only[1:]
    need = list(PARTS) if (reuse or not only) else only
    if "sdc-pack-saddle" in need and not (reuse and "sdc-pack-saddle" not in only
                                          and (up / "sdc-pack-saddle.stl").exists()):
        pack_g, pack_m = power_pack()
        hm = L.pack_heightmap(pack_g, S["cradle"]["saddle_clearance"])
    meshes = {}
    for n in need:
        if reuse and n not in only and (up / f"{n}.stl").exists() and n in pitches:
            m = trimesh.load(up / f"{n}.stl")
            m.metadata["pitch_mm"] = pitches[n]
            meshes[n] = m
            continue
        meshes[n] = build_mesh(n, hm)
        pitches[n] = meshes[n].metadata["pitch_mm"]
        meshes[n].export(up / f"{n}.stl")
        pj.write_text(json.dumps(pitches, indent=1))
    if only and not reuse:
        print(f"partial build done in {time.time() - t0:.0f} s")
        return
    if pack_m is None:
        pack_g, pack_m = power_pack()
    sdfkit.write_step = lambda path, parts: None   # FreeCAD absent on this host: STEP skipped (see docstring)
    k = sdfkit.Package(S["id"], PKG)
    for name, M, ex in assemble(meshes):
        label, col, _, _, note = PARTS[name]
        k.add(label, meshes[name], stl=name, color=col, group=name.split("-")[0], note=note, explode=ex, placement=M)
    rep = k.write()
    rep["step"] = {"file": None, "status": "skipped",
                   "reason": "FreeCAD is not installed on the build host (WSL); tools/sdfkit.write_step needs it. UNKNOWN until rebuilt where FreeCAD exists."}
    for n, m in meshes.items():
        rep["parts"][n]["pitch_mm"] = m.metadata.get("pitch_mm")
    rep["fits"] = fits(meshes, pack_g, pack_m)
    u = L.stem_dir(S)
    wisp_parts = [p for p in k.parts if p["stl"] == "wisp-a-recon"]
    wa = wisp_parts[0]["asm"]
    base_c = np.array([0.0, 0.0])
    rep["fits"]["flying_wisp"] = {
        "stem_lean_deg": S["stem"]["lean_deg"],
        "wisp_pitch_nose_down_deg": round(math.degrees(math.atan2(-u[1], u[2])), 2),
        "wisp_centre_offset_from_base_centre_mm": round(float(np.linalg.norm(wa.bounds.mean(axis=0)[:2] - base_c)), 2),
        "wisp_top_above_table_mm": round(float(wa.bounds[1][2]), 2),
        "wisp_bottom_above_base_top_mm": round(float(wa.bounds[0][2] - S["base"]["h"]), 2),
    }
    ticks = [p["asm"] for p in k.parts if p["stl"] in ("tick-hull", "tick-mast")]
    rep["fits"]["tick_with_mast_height_mm"] = round(float(max(m.bounds[1][2] for m in ticks) - S["base"]["h"]), 2)
    (PKG / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    if reuse:
        print("renders: run build.py --images in a fresh process (the in-process render was OOM-killed at 1.5 GB)")
    else:
        images(k.parts, meshes, pack_m)
    print(json.dumps(rep["fits"], indent=1))
    print(f"build done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
