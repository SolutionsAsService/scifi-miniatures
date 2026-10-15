#!/usr/bin/env python3
"""Vigil aerial wing (VA-1 Belfry, VA-2 Angelus, VA-3 Knell + launcher, loadout bits, stems, bases): 1:56, MSLA resin.

Run: ~/projects/venvs/scifi-sculpt/bin/python source/build.py [part ...]
     (no arguments: whole package; with part names: only those print meshes into build/upright, for iteration)
Frame: mm, z up, parts face -y. Key dimensions from spec/vigil-aerial-drones.spec.json; sculpts in
source/vigil_aerial.py on tools/aerial_kit.py + tools/sdfkit.py.
Writes build/upright/*.stl, viewer/vigil-aerial-drones.parts.json, reports/build.json, images/*.png.
Fit references read (never written): ../wayfarer-apc/build/upright/{hull-front,hull-rear,rws}.stl (roof launcher fit).
STEP: tools/sdfkit.write_step needs FreeCAD, absent on this host (no tools/freecadshim target either): skipped, UNKNOWN.
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import sdfkit  # noqa: E402
import vigil_aerial as V  # noqa: E402
from aerial_kit import flight_stem, mat, mesh_in_budget, stem_dir  # noqa: E402
from render import render  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-aerial-drones.spec.json").read_text())
WAYFARER = PKG.parent / "wayfarer-apc" / "build" / "upright"
AIR, ROT, LOAD, LAUN, STEMC, BASEC = "#7d8a78", "#4d524c", "#5d6560", "#6d7468", "#b8c6cf", "#4a4d52"
ST = S["stem"]
STEM_LEN = ST["visible_mm"] + ST["insert_air"] + ST["insert_base"]

# name -> (label, colour, ops factory, start pitch mm, triangle budget, note)
PARTS = {
    "belfry": ("VA-1 Belfry heavy-lift coaxial hexacopter", AIR, lambda: V.belfry(S), 0.1, 250_000,
               "Chevron-hex hull with keel crest, six arms with coaxial motor pairs (12 two-blade props, 0.84 mm blades), chin gimbal turret with split-chevron lenses, tubular skids; 1.2 D-flat mast socket, 1.6 D-flat payload hardpoint on the CG, 1.8 stem / tether socket."),
    "angelus": ("VA-2 Angelus observation helicopter (airframe)", AIR, lambda: V.angelus(S), 0.1, 250_000,
                "Teardrop pod, keel crest into the mast fairing, exposed mast + swashplate + head with a 1.4 rotor pin, chin sensor ball, tubular skids, slender boom, swept fin with a 1.0 tail-rotor pin, chevron tail plane; 1.8 stem socket on the CG."),
    "angelus-main-rotor": ("VA-2 Angelus main rotor (separate)", ROT, lambda: V.main_rotor(S), 0.06, 250_000,
                           "Two 1.8 x 0.9 mm blades with swept tips, 36.3 mm disc; prints flat on the plate with no supports; 1.6 through-bore slides on the 1.4 pin."),
    "angelus-tail-rotor": ("VA-2 Angelus tail rotor (separate)", ROT, lambda: V.tail_rotor(S), 0.04, 160_000,
                           "Two 1.0 x 0.84 mm blades, 6.4 mm disc; prints flat; 1.2 through-bore on the 1.0 pin."),
    "knell": ("VA-3 Knell flying-wing loitering UAV", AIR, lambda: V.knell(S), 0.1, 250_000,
              "Cropped-delta wing blended into a cigar fuselage, split-chevron winglets, pusher prop (0.8 mm blades), keel spine, split-chevron nose windows, elevon lines, hatch, blisters; 1.8 stem socket on the CG (sized by drone_fixed_wing_analysis)."),
    "launcher-rail": ("VA-3 Knell rail launcher", LAUN, lambda: V.launcher_rail(S), 0.08, 250_000,
                      "2.6 m-class box rail at 12 deg, lightening pockets, guide strips, launch ram, shuttle with a 1.6 pin for the Knell's stem socket; 2.0 mm D-flat peg (Wayfarer roof pad or tripod)."),
    "launcher-tripod": ("Launcher ground tripod", LAUN, lambda: V.launcher_tripod(S), 0.07, 250_000,
                        "Head with the 2.0 mm D-flat socket, three 1.4 mm legs on foot pads, spreader bars."),
    "launcher-roof-pad": ("Launcher roof pad (glue to the Wayfarer roof)", LAUN, lambda: V.roof_pad(S), 0.06, 160_000,
                          "10 x 10 x 1.2 mm glue plate, boss with a through 2.0 mm D-flat socket, engraved launch-direction chevron."),
    "vl-01-eo-turret": ("VL-01 long-range EO/IR turret (hardpoint)", LOAD, lambda: V.bit_eo_turret(S), 0.05, 160_000,
                        "Yoke + ball with split-chevron lenses; 1.6 D-flat peg."),
    "vl-02-sar-pod": ("VL-02 SAR radar pod (hardpoint)", LOAD, lambda: V.bit_sar_pod(S), 0.05, 160_000,
                      "Capsule pod with flat side arrays and a radome nose; 1.6 D-flat peg."),
    "vl-03-twin-munitions": ("VL-03 twin glide munitions (hardpoint)", LOAD, lambda: V.bit_twin_munitions(S), 0.05, 160_000,
                             "Cross-bar rack, two finned glide munitions (0.8 mm fins); 1.6 D-flat peg."),
    "vl-04-cargo-pod": ("VL-04 cargo / supply pod (hardpoint)", LOAD, lambda: V.bit_cargo_pod(S), 0.05, 160_000,
                        "Sling bar and a chevron-ribbed container; 1.6 D-flat peg."),
    "vl-10-eo-mast": ("VL-10 EO / radar ball mast (mast socket)", LOAD, lambda: V.bit_eo_mast(S), 0.05, 160_000,
                      "1.4 mm mast, ball with split-chevron lenses and a rain cap; 1.2 D-flat peg."),
    "vl-11-relay-mast": ("VL-11 relay antenna mast (mast socket)", LOAD, lambda: V.bit_relay_mast(S), 0.05, 160_000,
                         "Two dipole bars and a 1.0 mm whip; 1.2 D-flat peg."),
    "vl-12-radar-mast": ("VL-12 rotating surveillance radar (mast socket)", LOAD, lambda: V.bit_radar_mast(S), 0.05, 160_000,
                         "Turntable and a 7.2 x 2.6 mm array tilted back 15 deg; 1.2 D-flat peg."),
    "flight-stem": ("Flight stem 1.6 mm (printed)", STEMC, lambda: flight_stem(ST["d"], STEM_LEN), 0.1, 160_000,
                    f"{STEM_LEN:g} mm x 1.6 mm resin stem; a 1.6 mm clear acrylic rod cut to {STEM_LEN:g} mm fits every flight socket; it is also the tether on the tether base."),
    "base-50-stem": ("50 mm flight base (10 deg raked stem)", BASEC, lambda: V.base_stem(S, "base-50-stem"), 0.2, 250_000,
                     "50 x 4 mm bevelled base, chevron deck seams, 5 x 2 mm magnet pocket vented to the rim, launch pad with a 10 deg raked 1.8 stem socket (Belfry, Angelus)."),
    "base-40-stem": ("40 mm flight base (15 deg raked stem)", BASEC, lambda: V.base_stem(S, "base-40-stem"), 0.18, 250_000,
                     "40 x 4 mm base, as above with a 15 deg dive rake (Knell)."),
    "base-50-tether": ("50 mm tether-station base (tethered Belfry)", BASEC, lambda: V.base_tether(S), 0.16, 250_000,
                       "Generator with louvres and exhaust, cable spool on A-frames, cable to a fairlead with a vertical 1.8 socket: the stem is the tether."),
}


def build_mesh(name):
    t0 = time.time()
    label, col, fn, h0, budget, note = PARTS[name]
    m = mesh_in_budget(fn(), name, h0, budget, limit=int(budget * 1.15))
    print(f"{name}: {len(m.faces)} tris at {m.metadata['pitch_mm']} mm, vol {m.volume:.2f} mm3, "
          f"bbox {np.round(m.extents, 2).tolist()} ({time.time() - t0:.0f} s)", flush=True)
    return m


T = sdfkit.translate
RXa = lambda d: mat(sdfkit.rot((1, 0, 0), d))   # noqa: E731
RZa = lambda d: mat(sdfkit.rot((0, 0, 1), d))   # noqa: E731


def flyer_stack(base_key, x0, drone_sock, y0=0.0):
    """Placements for base + stem + drone on a raked base at (x0, y0): returns (base M, stem M, drone M)."""
    B = S["bases"][base_key]
    pad = B["pad"]
    rake = B["rake_deg"]
    u = stem_dir(rake)
    Ru = sdfkit.rot((1, 0, 0), rake)
    p = np.array([x0 + pad["xy"][0], y0 + pad["xy"][1], B["h"] + pad["h"] + 0.15])
    bottom = p - u * ST["insert_base"]
    top = bottom + u * STEM_LEN
    anchor = np.array([drone_sock["xy"][0], drone_sock["xy"][1], drone_sock["boss_bottom_z"] + ST["insert_air"]])
    return T(x0, y0, 0), mat(Ru, bottom), mat(Ru, top) @ T(*(-anchor))


def tether_stack(x0, y0=0.0):
    B = S["bases"]["base-50-tether"]
    fl = B["fairlead"]
    p = np.array([x0 + fl["xy"][0], y0 + fl["xy"][1], fl["top_z"]])
    bottom = p - np.array([0, 0, ST["insert_base"]])
    top = bottom + np.array([0, 0, STEM_LEN])
    sk = S["belfry"]["stem_socket"]
    anchor = np.array([sk["xy"][0], sk["xy"][1], sk["boss_bottom_z"] + ST["insert_air"]])
    return T(x0, y0, 0), mat(np.eye(3), bottom), T(*top) @ T(*(-anchor))


def belfry_bits(Mb, hard=None, mast=None):
    """Placements of a hardpoint bit and a mast bit on a Belfry placed at Mb."""
    Bf = S["belfry"]
    out = []
    if hard:
        hp = Bf["hardpoint"]
        out.append((hard, Mb @ T(hp["xy"][0], hp["xy"][1], hp["boss_bottom_z"]), (0, 0, -6)))
    if mast:
        ms = Bf["mast_socket"]
        out.append((mast, Mb @ T(ms["xy"][0], ms["xy"][1], ms["top_z"]), (0, 0, 6)))
    return out


def angelus_rotors(Ma):
    A = S["angelus"]
    mx, my = A["mast_xy"]
    tr = A["tail_rotor"]
    c = np.array(tr["c"])
    return [("angelus-main-rotor", Ma @ T(mx, my, A["head_top_z"]) @ RZa(28), (0, 0, 6)),
            ("angelus-tail-rotor", Ma @ T(c[0] + tr["inner_x"], c[1], c[2]) @ mat(sdfkit.rot((0, 1, 0), 90)) @ RZa(35), (4, 0, 0))]


def knell_on_launcher(Ml):
    """Knell seated on the shuttle pin of a launcher placed at Ml (boss bottom on the shuttle top)."""
    st = V.shuttle_top(S)
    e = S["launcher"]["elev_deg"]
    K = S["knell"]["stem_socket"]
    return Ml @ T(*st) @ RXa(-e) @ T(-K["xy"][0], -K["xy"][1], -K["boss_bottom_z"])


def assemble():
    out = []
    # 1 Belfry flying on the 50 mm base, EO ball mast + SAR pod
    b, s, d = flyer_stack("base-50-stem", 0.0, S["belfry"]["stem_socket"])
    out += [("base-50-stem", b, (0, 0, 0)), ("flight-stem", s, (0, 0, 4)), ("belfry", d, (0, 0, 10))]
    out += belfry_bits(d, "vl-02-sar-pod", "vl-10-eo-mast")
    # 2 Belfry tethered on the tether-station base, relay mast + EO turret
    b, s, d = tether_stack(62.0)
    out += [("base-50-tether", b, (0, 0, 0)), ("flight-stem", s, (0, 0, 4)), ("belfry", d, (0, 0, 10))]
    out += belfry_bits(d, "vl-01-eo-turret", "vl-11-relay-mast")
    out.append(("vl-12-radar-mast", T(62.0, 0, 0) @ T(*V.tether_mast_top(S)), (0, 0, 5)))      # M8: radar on the station
    # 3 Angelus flying on a 50 mm base with both rotors
    b, s, d = flyer_stack("base-50-stem", 124.0, S["angelus"]["stem_socket"])
    out += [("base-50-stem", b, (0, 0, 0)), ("flight-stem", s, (0, 0, 4)), ("angelus", d, (0, 0, 10))]
    out += angelus_rotors(d)
    # 4 Knell diving on the 40 mm base
    b, s, d = flyer_stack("base-40-stem", 180.0, S["knell"]["stem_socket"])
    out += [("base-40-stem", b, (0, 0, 0)), ("flight-stem", s, (0, 0, 4)), ("knell", d, (0, 0, 10))]
    # 5 launcher on the tripod with a Knell on the shuttle; roof pad and the spare bits laid out in front
    Mt = T(40.0, -62.0, 0.0)
    Ml = Mt @ T(0, 0, S["launcher"]["tripod"]["head_top_z"])
    out += [("launcher-tripod", Mt, (0, 0, 0)), ("launcher-rail", Ml, (0, 0, 5)), ("knell", knell_on_launcher(Ml), (0, 0, 10))]
    out.append(("launcher-roof-pad", T(80.0, -62.0, 0.0), (0, 0, 0)))
    for i, n in enumerate(("vl-03-twin-munitions", "vl-04-cargo-pod", "vl-10-eo-mast")):
        z = 4.0 if n.startswith("vl-0") else 2.0
        out.append((n, T(104.0 + 14.0 * i, -62.0, z), (0, 0, 0)))
    return out


# ------------------------------------------------------------------------------------------------ package writer
def write_package(meshes, placements, viewer_tris=26_000, image_tris=90_000):
    """Same outputs as sdfkit.Package.write (viewer/<id>.parts.json, reports/build.json rows, interference), but memory
    light for a shared 8 GB host: one viewer LOD and one image LOD per unique part (manifold simplify, never used for
    print), placed per instance; interference on the full print meshes, only for instance pairs whose boxes overlap.
    STEP: skipped (FreeCAD absent)."""
    for d in (PKG / "viewer", PKG / "reports"):
        d.mkdir(parents=True, exist_ok=True)
    used = sorted({n for n, _, _ in placements})
    rows, lod_v, lod_i = {}, {}, {}
    for n in used:
        m = meshes[n]
        if not m.is_watertight:
            raise SystemExit(f"{n}: not watertight")
        bb = m.bounds
        rows[n] = {"volume_mm3": round(float(m.volume), 2), "bodies": len(m.split(only_watertight=False)), "watertight": True,
                   "bbox_mm": [round(float(x), 2) for x in bb[1] - bb[0]], "triangles": len(m.faces), "instances": 0}
        lod_v[n] = sdfkit.decimate(m, viewer_tris, n)
        lod_i[n] = sdfkit.decimate(m, image_tris, n)
    viewer, parts, boxes = [], [], []
    lo_all, hi_all = np.full(3, np.inf), np.full(3, -np.inf)
    for name, M, ex in placements:
        label, col, _, _, _, note = PARTS[name]
        rows[name]["instances"] += 1
        vm = tm(lod_v[name], M)
        viewer.append({"name": label, "group": name.split("-")[0], "color": col, "note": note, "explode": list(ex),
                       "printStl": f"print/stl/{name}.stl", "vertices": np.round(vm.vertices, 3).tolist(), "triangles": vm.faces.tolist()})
        V = meshes[name].vertices @ M[:3, :3].T + M[:3, 3]
        lo, hi = V.min(axis=0), V.max(axis=0)
        boxes.append((lo, hi))
        lo_all, hi_all = np.minimum(lo_all, lo), np.maximum(hi_all, hi)
        parts.append({"name": label, "stl": name, "color": col, "placement": M, "asm": tm(lod_i[name], M)})
    (PKG / "viewer" / f"{S['id']}.parts.json").write_text(json.dumps(viewer, separators=(",", ":")))
    interference = []
    for i in range(len(placements)):
        for j in range(i + 1, len(placements)):
            (la, ha), (lb, hb) = boxes[i], boxes[j]
            if np.any(np.minimum(ha, hb) <= np.maximum(la, lb)):
                continue
            a = tm(meshes[placements[i][0]], placements[i][1])
            b = tm(meshes[placements[j][0]], placements[j][1])
            v = sdfkit.overlap_volume(a, b)
            if v > 0.02:
                interference.append({"a": parts[i]["name"], "b": parts[j]["name"], "overlap_mm3": round(v, 3)})
    rep = {"id": S["id"], "generator": "source/build.py (tools/sdfkit.py + tools/aerial_kit.py: SDF sculpt, marching cubes; viewer LODs by manifold3d simplify)",
           "assembled_bbox_mm": [round(float(x), 2) for x in hi_all - lo_all], "parts": rows, "interference": interference,
           "step": {"file": None, "status": "skipped",
                    "reason": "FreeCAD is not installed on the build host (WSL) and tools/freecadshim has no target here; tools/sdfkit.write_step needs it. UNKNOWN until rebuilt where FreeCAD exists."}}
    print(json.dumps({"assembled_bbox_mm": rep["assembled_bbox_mm"], "interference": interference}, indent=1), flush=True)
    return rep, parts


# ------------------------------------------------------------------------------------------------ fits
def tm(m, M):
    a = m.copy()
    a.apply_transform(M)
    return a


def min_gap(a, b):
    """Smallest vertex-to-vertex distance between two meshes (mm), by k-d tree. Both meshes are dense marched surfaces
    (edges <= ~0.12 mm), so this is within one edge length above the true surface gap; interpenetration is caught by
    the separate boolean overlap volume. (trimesh signed_distance on 250k-triangle meshes was OOM-killed on this host.)"""
    from scipy.spatial import cKDTree
    d, _ = cKDTree(b.vertices).query(a.vertices, k=1)
    return round(float(d.min()), 3)


def fits(meshes):
    rep = {}
    Bf = S["belfry"]
    zs = Bf["skid_z"]
    # flying stacks: drone centre offset and heights
    for key, base_key, drone in (("belfry_flying", "base-50-stem", "belfry"), ("angelus_flying", "base-50-stem", "angelus"),
                                 ("knell_flying", "base-40-stem", "knell")):
        b, s, d = flyer_stack(base_key, 0.0, S[drone]["stem_socket"])
        a = tm(meshes[drone], d)
        stem = tm(meshes["flight-stem"], s)
        base = meshes[base_key]
        rep[key] = {"rake_deg": S["bases"][base_key]["rake_deg"],
                    "drone_centre_offset_from_base_centre_mm": round(float(np.linalg.norm(a.bounds.mean(axis=0)[:2])), 2),
                    "drone_bottom_above_base_top_mm": round(float(a.bounds[0][2] - S["bases"][base_key]["h"]), 2),
                    "drone_top_above_table_mm": round(float(a.bounds[1][2]), 2),
                    "stem_drone_overlap_mm3": round(sdfkit.overlap_volume(a, stem), 4),
                    "stem_base_overlap_mm3": round(sdfkit.overlap_volume(base, stem), 4),
                    "drone_base_overlap_mm3": round(sdfkit.overlap_volume(a, base), 4)}
    b, s, d = flyer_stack("base-50-stem", 0.0, S["angelus"]["stem_socket"])
    ax = d @ np.array([*S["angelus"]["mast_xy"], S["angelus"]["head_top_z"], 1.0])
    rep["angelus_flying"]["rotor_axis_offset_from_base_centre_mm"] = round(float(np.hypot(ax[0], ax[1])), 2)
    # tether stack
    b, s, d = tether_stack(0.0)
    a = tm(meshes["belfry"], d)
    stem = tm(meshes["flight-stem"], s)
    st_bit = {}
    for n in ("vl-10-eo-mast", "vl-11-relay-mast", "vl-12-radar-mast"):
        bit = tm(meshes[n], T(*V.tether_mast_top(S)))
        st_bit[n] = {"overlap_with_station_mm3": round(sdfkit.overlap_volume(bit, meshes["base-50-tether"]), 4),
                     "overlap_with_tethered_belfry_mm3": round(sdfkit.overlap_volume(bit, a), 4),
                     "gap_to_tethered_belfry_mm": min_gap(bit, a), "top_z_mm": round(float(bit.bounds[1][2]), 2)}
    rep["belfry_tethered_station_masts"] = st_bit
    rep["belfry_tethered"] = {"drone_centre_offset_from_base_centre_mm": round(float(np.linalg.norm(a.bounds.mean(axis=0)[:2])), 2),
                              "drone_bottom_above_base_top_mm": round(float(a.bounds[0][2] - S["bases"]["base-50-tether"]["h"]), 2),
                              "drone_bottom_above_station_top_mm": round(float(a.bounds[0][2] - meshes["base-50-tether"].bounds[1][2]), 2),
                              "stem_drone_overlap_mm3": round(sdfkit.overlap_volume(a, stem), 4),
                              "stem_base_overlap_mm3": round(sdfkit.overlap_volume(meshes["base-50-tether"], stem), 4)}
    # Belfry loadouts: interference with the airframe and with a flying stem, clearance above the skid plane
    bel = meshes["belfry"]
    _, s, d = flyer_stack("base-50-stem", 0.0, Bf["stem_socket"])
    stem_local = tm(meshes["flight-stem"], np.linalg.inv(d) @ s)
    lo = {}
    for n in ("vl-01-eo-turret", "vl-02-sar-pod", "vl-03-twin-munitions", "vl-04-cargo-pod", "vl-10-eo-mast", "vl-11-relay-mast", "vl-12-radar-mast"):
        hard = n.startswith("vl-0")
        M = belfry_bits(np.eye(4), n if hard else None, None if hard else n)[0][1]
        a = tm(meshes[n], M)
        r = {"overlap_with_belfry_mm3": round(sdfkit.overlap_volume(a, bel), 4),
             "gap_to_belfry_mm": min_gap(a, bel)}
        if hard:
            r["lowest_z_mm"] = round(float(a.bounds[0][2]), 3)
            r["clearance_above_skid_plane_mm"] = round(float(a.bounds[0][2] - zs), 3)
            r["overlap_with_flying_stem_mm3"] = round(sdfkit.overlap_volume(a, stem_local), 4)
            r["gap_to_flying_stem_mm"] = min_gap(a, stem_local)
        else:
            r["top_z_mm"] = round(float(a.bounds[1][2]), 3)
        lo[n] = r
    rep["belfry_loadouts"] = lo
    # Angelus rotors
    ang = meshes["angelus"]
    ro = {}
    for n, M, _ in angelus_rotors(np.eye(4)):
        a = tm(meshes[n], M)
        ro[n] = {"overlap_with_airframe_mm3": round(sdfkit.overlap_volume(a, ang), 4)}
    mr = tm(meshes["angelus-main-rotor"], angelus_rotors(np.eye(4))[0][1])
    tr = tm(meshes["angelus-tail-rotor"], angelus_rotors(np.eye(4))[1][1])
    ro["main_rotor_disc_mm"] = round(float(max(meshes["angelus-main-rotor"].extents[:2])), 2)
    ro["tail_rotor_disc_mm"] = round(float(max(meshes["angelus-tail-rotor"].extents[:2])), 2)
    ro["main_rotor_aft_reach_y_mm"] = round(float(mr.bounds[1][1]), 2)
    ro["tail_rotor_fore_y_mm"] = round(float(tr.bounds[0][1]), 2)
    ro["main_to_tail_rotor_gap_mm"] = min_gap(tr, mr)
    ro["tail_rotor_gap_to_airframe_mm"] = min_gap(tr, ang)
    ro["main_rotor_gap_to_airframe_mm"] = min_gap(mr, ang)
    ro["airframe_extent_mm"] = [round(float(v), 2) for v in ang.extents]
    rep["angelus_rotors"] = ro
    # Knell on the launcher (tripod)
    Mt = np.eye(4)
    Ml = Mt @ T(0, 0, S["launcher"]["tripod"]["head_top_z"])
    kn = tm(meshes["knell"], knell_on_launcher(Ml))
    rl = tm(meshes["launcher-rail"], Ml)
    rep["knell_on_launcher"] = {"overlap_knell_rail_mm3": round(sdfkit.overlap_volume(kn, rl), 4),
                                "overlap_rail_tripod_mm3": round(sdfkit.overlap_volume(rl, meshes["launcher-tripod"]), 4),
                                "knell_lowest_z_on_tripod_mm": round(float(kn.bounds[0][2]), 2),
                                "rail_length_mm": S["launcher"]["rail_len"],
                                "stroke_mm": round(S["launcher"]["rail_len"] / 2 - S["launcher"]["shuttle_s"] - 0.6, 2),
                                "stroke_in_world_m": round((S["launcher"]["rail_len"] / 2 - S["launcher"]["shuttle_s"] - 0.6) * 56 / 1000, 3)}
    rep["wayfarer_roof"] = wayfarer_fit(meshes)
    for n in ("belfry", "angelus", "knell"):
        rep.setdefault("extents_mm", {})[n] = [round(float(v), 2) for v in meshes[n].extents]
    return rep


def wayfarer_placements():
    W = S["launcher"]["wayfarer"]
    c = np.array(W["pad_centre"])
    Rz = sdfkit.rot((0, 0, 1), 90)                         # launcher -y -> Wayfarer +x
    Mp = mat(Rz, c)
    Ml = Mp @ T(0, 0, S["launcher"]["roof_pad"]["boss_top_z"])
    return Mp, Ml, knell_on_launcher(Ml)


def wayfarer_fit(meshes):
    """Roof pad + launcher + Knell on the Wayfarer APC roof (Wayfarer meshes read, never written)."""
    names = ("hull-front", "hull-rear", "rws")
    if not all((WAYFARER / f"{n}.stl").exists() for n in names):
        return {"status": "UNKNOWN", "reason": "wayfarer-apc/build/upright meshes not present"}
    hull = trimesh.util.concatenate([trimesh.load(WAYFARER / f"{n}.stl") for n in names[:2]])
    rws = trimesh.load(WAYFARER / "rws.stl")
    rws.apply_translation((0, 0, 38.52))
    Mp, Ml, Mk = wayfarer_placements()
    pad, rail, kn = tm(meshes["launcher-roof-pad"], Mp), tm(meshes["launcher-rail"], Ml), tm(meshes["knell"], Mk)
    # roof flatness under the pad: ray-cast the hull on a 1 mm grid over the pad footprint
    P = S["launcher"]["roof_pad"]
    W = S["launcher"]["wayfarer"]
    cx, cy, cz = W["pad_centre"]
    xs = np.arange(cx - P["half"][1] + 0.5, cx + P["half"][1], 1.0)
    ys = np.arange(cy - P["half"][0] + 0.5, cy + P["half"][0], 1.0)
    O = np.array([(x, y, 80.0) for x in xs for y in ys])
    loc, idx, _ = hull.ray.intersects_location(O, np.tile([0, 0, -1.0], (len(O), 1)), multiple_hits=True)
    top = np.full(len(O), -np.inf)
    np.maximum.at(top, idx, loc[:, 2])                    # topmost hit per ray (single-hit mode returned inner faces)
    zr = top[np.isfinite(top)]
    stack = trimesh.util.concatenate([pad, rail, kn])
    blocked = []
    for yaw in range(0, 360, 5):
        r = rws.copy()
        r.apply_transform(RZa(yaw))
        if sdfkit.overlap_volume(r, stack) > 0.02:
            blocked.append(yaw)
    clear = [y for y in range(0, 360, 5) if y not in blocked]
    return {"pad_centre_wayfarer_frame": W["pad_centre"], "yaw": W["yaw_note"],
            "roof_z_under_pad_min_max": [round(float(zr.min()), 3), round(float(zr.max()), 3)], "roof_samples": int(len(zr)),
            "roof_fraction_at_plane": round(float(np.mean(np.abs(zr - W["roof_flat_zone"]["z"]) < 0.03)), 4),
            "roof_max_above_plane_mm": round(float(zr.max() - W["roof_flat_zone"]["z"]), 3),
            "overlap_pad_hull_mm3": round(sdfkit.overlap_volume(pad, hull), 4),
            "overlap_rail_hull_mm3": round(sdfkit.overlap_volume(rail, hull), 4),
            "overlap_knell_hull_mm3": round(sdfkit.overlap_volume(kn, hull), 4),
            "overlap_stack_rws_at_yaw0_mm3": round(sdfkit.overlap_volume(stack, rws), 4),
            "rws_yaw_blocked_deg": blocked, "rws_yaw_clear_count_of_72": len(clear),
            "knell_lowest_z_above_roof_mm": round(float(kn.bounds[0][2] - 38.5), 2),
            "stack_top_z_above_roof_mm": round(float(stack.bounds[1][2] - 38.5), 2),
            "method": "manifold3d intersection volumes; RWS rotated about the ring axis (0, 0) in 5 deg steps; roof heights by downward ray cast on a 1 mm grid"}


# ------------------------------------------------------------------------------------------------ images
def images(parts, meshes):
    out = PKG / "images"
    out.mkdir(exist_ok=True)
    allp = [(p["asm"], p["color"]) for p in parts]
    render(allp, out / "vigil-aerial-turnaround.png", size=520, title="Vigil aerial wing: 3/4, front, right side, back (orthographic)")
    hero = [(p["asm"], p["color"]) for p in parts if p["placement"][1, 3] > -30]
    render(hero, out / "vigil-aerial-hero.png", views=((-30, 16, "3/4 front: Belfry flying (SAR pod, EO mast) and tethered (EO turret, relay), Angelus, Knell diving"),), size=1000)
    col = {n: PARTS[n][1] for n in PARTS}
    views4 = ((-35, 18, "3/4 front"), (0, 2, "front"), (90, 2, "side (right)"), (0, 90, "top (front down)"))
    # Belfry with its loadout combinations
    bl = []
    combos = (("vl-02-sar-pod", "vl-10-eo-mast"), ("vl-01-eo-turret", "vl-11-relay-mast"), ("vl-04-cargo-pod", "vl-12-radar-mast"), ("vl-03-twin-munitions", None))
    for i, (h, m) in enumerate(combos):
        M = T(i * 44.0, 0, 0)
        bl.append((tm(meshes["belfry"], M), col["belfry"]))
        for n, Mb, _ in belfry_bits(M, h, m):
            bl.append((tm(meshes[n], Mb), col[n]))
    render(bl, out / "vigil-aerial-belfry.png", views=views4, size=520, title="VA-1 Belfry with loadouts: SAR pod + EO mast, EO turret + relay, cargo pod + radar, twin munitions")
    an = [(meshes["angelus"], col["angelus"])] + [(tm(meshes[n], M), col[n]) for n, M, _ in angelus_rotors(np.eye(4))]
    render(an, out / "vigil-aerial-angelus.png", views=views4, size=520, title="VA-2 Angelus observation helicopter with its separate main and tail rotors")
    Ml = T(40, 0, S["launcher"]["tripod"]["head_top_z"])
    kn = [(meshes["knell"], col["knell"]), (tm(meshes["launcher-tripod"], T(40, 0, 0)), col["launcher-tripod"]),
          (tm(meshes["launcher-rail"], Ml), col["launcher-rail"]), (tm(meshes["knell"], knell_on_launcher(Ml)), col["knell"])]
    render(kn, out / "vigil-aerial-knell.png", views=views4, size=520, title="VA-3 Knell loitering UAV, and on its rail launcher + tripod")
    bits = []
    order = ("vl-01-eo-turret", "vl-02-sar-pod", "vl-03-twin-munitions", "vl-04-cargo-pod", "vl-10-eo-mast", "vl-11-relay-mast", "vl-12-radar-mast", "launcher-roof-pad")
    for i, n in enumerate(order):
        bits.append((tm(meshes[n], T(i * 11.0, 0, 0)), col[n]))
    render(bits, out / "vigil-aerial-loadout.png", views=((-35, 20, "3/4 front"), (0, 2, "front")), size=640, title="Loadout bits VL-01..04 (hardpoint), VL-10..12 (mast), launcher roof pad")
    names = ("hull-front", "hull-rear", "rws")
    if all((WAYFARER / f"{n}.stl").exists() for n in names):
        ref = [(trimesh.load(WAYFARER / f"{n}.stl"), "#a2a7ad") for n in names[:2]]
        r = trimesh.load(WAYFARER / "rws.stl")
        r.apply_translation((0, 0, 38.52))
        ref.append((r, "#a2a7ad"))
        Mp, Ml, Mk = wayfarer_placements()
        ref += [(tm(meshes["launcher-roof-pad"], Mp), col["launcher-roof-pad"]), (tm(meshes["launcher-rail"], Ml), col["launcher-rail"]),
                (tm(meshes["knell"], Mk), col["knell"])]
        render(ref, out / "vigil-aerial-launcher-wayfarer.png", views=((-40, 22, "3/4 front-left"), (90, 2, "left side"), (0, 90, "top")), size=560,
               title="Knell launcher on the Wayfarer APC roof pad (grey: Wayfarer reference, not in this kit)")
    bases = [(tm(meshes[n], T(i * 58.0, 0, 0)), col[n]) for i, n in enumerate(("base-50-stem", "base-40-stem", "base-50-tether"))]
    render(bases, out / "vigil-aerial-bases.png", views=((-35, 30, "3/4"), (0, 90, "top")), size=560, title="Bases: 50 mm flight (10 deg), 40 mm flight (15 deg), 50 mm tether station")


def main(only):
    """No arguments: sculpt everything. Part names: sculpt only those into build/upright (iteration).
    --reuse [part ...]: load every other part from build/upright (pitches from build/upright/pitch.json), re-sculpt the
    named ones, then assemble, measure the fits and render (a full rebuild without re-meshing unchanged parts)."""
    t0 = time.time()
    up = PKG / "build" / "upright"
    up.mkdir(parents=True, exist_ok=True)
    pj = up / "pitch.json"
    pitches = json.loads(pj.read_text()) if pj.exists() else {}
    reuse = bool(only) and only[0] == "--reuse"
    if reuse:
        only = only[1:]
    need = list(PARTS) if (reuse or not only) else only
    meshes = {}
    for n in need:
        if reuse and n not in only and (up / f"{n}.stl").exists() and n in pitches:
            m = trimesh.load(up / f"{n}.stl")
            m.metadata["pitch_mm"] = pitches[n]
            meshes[n] = m
            continue
        meshes[n] = build_mesh(n)
        pitches[n] = meshes[n].metadata["pitch_mm"]
        meshes[n].export(up / f"{n}.stl")
        pj.write_text(json.dumps(pitches, indent=1))
    if only and not reuse:
        print(f"partial build done in {time.time() - t0:.0f} s")
        return
    rep, parts = write_package(meshes, assemble())
    for n, m in meshes.items():
        rep["parts"][n]["pitch_mm"] = m.metadata.get("pitch_mm")
    rep["fits"] = fits(meshes)
    (PKG / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep["fits"], indent=1), flush=True)
    images(parts, meshes)
    print(f"build done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
