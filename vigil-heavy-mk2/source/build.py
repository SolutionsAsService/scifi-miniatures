#!/usr/bin/env python3
"""Vigilant Heavy Gunner Mk2: Kestrel exosuit body braced behind the VHW-01 Bombard rotary repeater (tools/arsenal3.py),
belt-fed from an ammunition drum backpack, VH2-04 Bastion helm, 40 mm base; plus the three VHW heavy weapons as loose
bits. Aster Compact Vigilant line, 30 mm heroic, MSLA resin.

Run with the sculpt venv:  ~/projects/venvs/scifi-sculpt/bin/python source/build.py [--images]
Frame: mm, z up, base underside at z = 0, the figure faces -y. Pose numbers from spec/vigil-heavy-mk2.spec.json.

Uses the existing pipeline unchanged (tools/exosuit.py figure(), fist(), base(); tools/vh2.py helm; tools/sdfkit.py
Package). Additive runtime registrations only: exosuit.BASES[40] for the 40 mm base and a note writer in place of
sdfkit.write_step (FreeCAD is not installed on this host). Print meshes are never decimated: if a part is over the
checker budget its SDF is re-meshed at a coarser pitch.
"""
import json
import math
import sys
import time
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
import numpy as np  # noqa: E402
import trimesh  # noqa: E402

import arsenal3 as A3  # noqa: E402
import exosuit as X  # noqa: E402
import sdfkit  # noqa: E402
import vh2  # noqa: E402
from render import render  # noqa: E402
from sdfkit import Package, bezier, decimate, rbox, translate, tube, unit, v3  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-heavy-mk2.spec.json").read_text())
X.BASES.setdefault(40, {"d": 40.0, "h": 4.0})
STEP_NOTE = ("STEP SKIPPED: FreeCAD is not installed on this build host (WSL), so tools/sdfkit.write_step could not "
             "run; the STLs are the deliverable.")
sdfkit.write_step = lambda path, parts: Path(str(path) + ".SKIPPED.txt").write_text(STEP_NOTE + "\n")
BUDGET = S["max_print_triangles"]

pz = S["pose"]
gz = pz["gun"]
M = X.place(v3(gz["grip"]), unit(gz["dir"]), (0, 0, 1))
GRIP = X.apply(M, (0, 0, 0))
HANDLE = X.apply(M, A3.HANDLE3["VHW-01"][0])
pose = X.Pose(pelvis=pz["pelvis"], yaw=pz["yaw"], lean=pz["lean"], twist=pz["twist"], ankles=pz["ankles"],
              feet_yaw=pz["feet_yaw"], fists=(GRIP, HANDLE), elbow_poles=pz["elbow_poles"], knee_poles=pz["knee_poles"],
              head_yaw=pz["head_yaw"])
PACK_M = X.pack_placement(pose)
FEED_PORT_LOCAL = (1.6, 2.45, 2.1)             # Bombard feed port, weapon frame: the LEFT (inboard) face, toward the body


def pk(p):
    """Pack frame -> figure frame."""
    return X.apply(PACK_M, p)


def catmull(pts, n=8):
    """Centripetal-free uniform Catmull-Rom through the control points (smooth belt route)."""
    P = [np.asarray(pts[0]) * 2 - np.asarray(pts[1])] + [np.asarray(p) for p in pts] + [np.asarray(pts[-1]) * 2 - np.asarray(pts[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def chute_path(P):
    """Feed belt route: out of the Bombard's inboard feed port, back onto the waist, round the right flank over the
    belt line (hugging, and fused to, the body the whole way: no free span longer than ~2 mm), up the lower back to
    the drum pack's throat, ending in a coupler whose face stops 0.1 mm short of FEED_FACE."""
    fx, fy, fz = A3.FEED_FACE
    wp = lambda x, y, z: P.pelvis + P.Rp @ v3(x, y, z)
    a = X.apply(M, FEED_PORT_LOCAL)
    a1 = X.apply(M, (FEED_PORT_LOCAL[0] - 0.6, FEED_PORT_LOCAL[1] + 1.0, FEED_PORT_LOCAL[2] - 0.5))
    end = pk((fx, fy - 0.6, fz))                                             # coupler centre
    down = pk((fx, fy - 0.9, fz - 1.6))
    ctrl = [a, a1, wp(-1.9, -2.95, 1.0), wp(-3.35, -1.1, 0.75), wp(-3.45, 1.0, 0.8), wp(-2.6, 2.95, 1.2), down, end]
    pts = catmull(ctrl, 8)
    return pts, wp(-3.45, 0.0, 0.78), end


def gunner(g, P):
    g.add(A3.weapon_shape("VHW-01").moved(M))
    X.fist(g, GRIP, X.apply(M, (-0.17, 0, -0.98)) - GRIP, GRIP - P.elbow[0])
    X.fist(g, HANDLE, M[:3, 0], HANDLE - P.elbow[1])
    pts, clip, end = chute_path(P)
    belt = A3.Build("belt")
    A3.belt_links(belt, pts, w=1.0, t=0.62, step=0.65, up=(0, 0, 1))
    g.add(belt.shape(), 0.25)                                                                  # fused where it hugs the body
    g.add(rbox(clip, (0.45, 0.8, 0.75), P.Rp, 0.2), 0.2)                                       # belt clip on the right flank
    fx, fy, fz = A3.FEED_FACE
    g.add(rbox(pk((fx, fy - 0.1 - 0.45, fz)), (0.85, 0.45, 0.7), P.Rc, 0.2), 0.15)             # coupler, face 0.1 mm short
    # enlarged backpack boss (4.6 x 4.8 mm face on the standard mount plane): the 2.0 mm socket keeps a 1.2 mm wall
    hb = S["pack_boss_half_mm"]
    g.add(rbox(X.pack_mount(P) - P.Rc @ v3(0, hb[1], 0), tuple(hb), P.Rc, 0.3), 0.15)
    g.add(rbox(P.pelvis + P.Rp @ v3(3.0, 1.2, 0.6), (0.85, 1.05, 1.15), P.Rp, 0.35), 0.15)     # ammunition pouch, left hip


MESHLOG = {}
OPEN_R = 0.22          # HM5: morphological opening (arsenal3.open_slivers) before meshing every part


def mesh_fit(make, name, h0):
    h = h0
    while True:
        g = make(h)
        removed = A3.open_slivers(g, OPEN_R)
        m = g.mesh(name, None)
        n = len(m.faces)
        MESHLOG[name] = {"pitch_mm": h, "triangles": n, "opening_r_mm": OPEN_R, "opened_away_mm3": round(removed, 4)}
        if n <= BUDGET or h > 0.2:
            return m, h
        h = round(h * math.sqrt(n / (BUDGET * 0.93)) + 0.0005, 4)


def build():
    t0 = time.time()
    bd = S["base"]["d"]
    H0 = X.BASES[bd]["h"]
    lift = translate(0, 0, H0)
    body, hb = mesh_fit(lambda h: X.figure(pose, h=h, extras=[gunner], bbox=S["bbox"]), "figure", S["voxel_mm"])
    print(f"figure {len(body.faces)} tris at {hb} mm ({time.time() - t0:.0f} s)", flush=True)
    helm, hh = mesh_fit(lambda h: vh2.helm("VH2-04", h), "helm", 0.05)
    pack, hp = mesh_fit(lambda h: A3.drum_pack(h), "backpack", 0.06)
    base, hbase = mesh_fit(lambda h: X.base(pose, d=bd, seed=S["base_seed"], h=h), "base", 0.1)
    print(f"helm {len(helm.faces)}@{hh} pack {len(pack.faces)}@{hp} base {len(base.faces)}@{hbase}", flush=True)
    k = Package(S["id"], PKG)
    k.add("Vigilant heavy gunner Mk2", body, stl="figure", color="#8a8f96", group="figure",
          note="Kestrel exosuit body braced behind the integral VHW-01 Bombard; feed belt, coupler, hip pouch, enlarged pack boss, keyed footplate.",
          explode=(0, 0, 6), placement=lift)
    k.add("VH2-04 Bastion helm", helm, stl="helm", color="#c8a24a", group="helm",
          note="Heavy helm from tools/vh2.py: split chevron visor, keel crest, 1.6 mm D-flat peg.",
          explode=(0, 0, 14), placement=lift @ X.helm_placement(pose))
    back = pose.Rc @ np.array([0, 1.0, 0])
    k.add("VHW-01P ammunition drum pack", pack, stl="backpack", color="#5b6168", group="backpack",
          note="Power core and keel spine carrying a large ribbed drum; feed throat butts the belt coupler; 2.0 mm D-flat peg.",
          explode=tuple(np.round(back * 9 + np.array([0, 0, 6]), 2)), placement=lift @ PACK_M)
    k.add(f"{bd} mm base", base, stl="base", color="#3d4248", group="base",
          note=f"{bd} mm round deck-plate base: keyed footplate recess, 5 x 2 mm magnet pocket vented to the rim.")
    pitches = {"figure": hb, "helm": hh, "backpack": hp, "base": hbase}
    for j, ident in enumerate(A3.HEAVY3):
        name, note = A3.HEAVY3[ident][:2]
        stl = f"{ident.lower()}-{name.lower().replace(' ', '-')}"
        m, hw = A3.sculpt_fit(A3.item(ident), f"{ident} {name}", S["bit_voxel_mm"], BUDGET, h_max=0.09, open_r=OPEN_R, log=MESHLOG)
        pitches[stl] = hw
        print(f"{ident} {len(m.faces)} tris at {hw} mm", flush=True)
        k.add(f"{ident} {name} (loose)", m, stl=stl, color="#4d5257", group=stl, note=f"{ident} {name}: {note}",
              explode=(0, 0, 4), placement=translate(30.0, 18.0 - j * 9.0, 0.0))
    rep = k.write()
    asm_helm = [p for p in k.parts if p["stl"] == "helm"][0]["asm"]
    rep["voxel_mm"] = pitches
    rep["mesh_log"] = MESHLOG
    rep["placements"] = {p["stl"]: (p["placement"] if p["placement"] is not None else np.eye(4)).tolist() for p in k.parts}
    rep["names"] = {p["stl"]: p["name"] for p in k.parts}
    rep["print_mesh_policy"] = "marching cubes at the listed pitch, largest body kept, no decimation"
    rep["step"] = {"file": None, "status": "SKIPPED", "reason": STEP_NOTE}
    rep["heights_above_base_top_mm"] = {"crown": round(float(asm_helm.bounds[1][2] - H0), 2),
                                        "visor_line": round(float(pose.neck_cut[2] + X.HEAD_UP + 0.12 * X.HS), 2)}
    pts, _, end = chute_path(pose)
    face = pk(A3.FEED_FACE)
    rep["feed_joint"] = {"coupler_face_to_throat_face_mm": 0.1, "throat_face_centre_mm": np.round(face + v3(0, 0, H0), 2).tolist(),
                         "belt_length_mm": round(float(sum(np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1))), 1)}
    rep["pose"] = {"grip": np.round(GRIP, 2).tolist(), "handle": np.round(HANDLE, 2).tolist(),
                   "elbows": [np.round(e, 2).tolist() for e in pose.elbow],
                   "reach_mm": [round(float(np.linalg.norm(pose.fist[i] - pose.sh[i])), 2) for i in range(2)],
                   "reach_max_mm": X.L_UPPER + X.L_FORE + 1.0}
    (PKG / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    images(k)
    return rep


def images(k=None):
    import sheet
    sheet.all_images(PKG, k)


if __name__ == "__main__":
    if "--images" in sys.argv:
        images()
    else:
        build()
