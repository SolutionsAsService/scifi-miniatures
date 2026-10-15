#!/usr/bin/env python3
"""Printability check for the Vigil aerial wing through the unified-CAD-MCP miniature_* tools (tools/mcpcheck.py driver).

Run: PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check.py
Order: re-run the drone_* sizing calls and assert the model still matches them (source/sizing.py), assert the measured
fits in reports/build.json, then miniature_scale_convert, detail_advice, base_and_peg (every joint),
base_layout_check (every base), slender_feature_check (blades, booms, skids, struts, legs, winglets, masts, stem),
gap_check (narrow slits), then per part: miniature_support_plan picks the print pose (rotors are forced flat on the
plate), the part is written in that pose to print/stl/ (+ units sidecar) and miniature_printability_check runs on that
file; plate_pack, shell_audit on every print file and mesh_budget per part. Fails (exit 1) on any fail-severity
finding, a slender / gap / layout check that does not pass, an unclean shell audit, a sizing drift or a failed fit.
Tool results are cached under build/checkcache keyed by tool + args + the sha256 of every STL read.
"""
import asyncio
import hashlib
import json
import math
import sys
import time
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
sys.path.insert(0, str(PKG / "source"))
import mcpcheck  # noqa: E402

S = json.loads((PKG / "spec" / "vigil-aerial-drones.spec.json").read_text())
UP = PKG / "build" / "upright"
up = lambda n: str(UP / f"{n}.stl")  # noqa: E731
P = S["process"]
Bf, A, K, L = S["belfry"], S["angelus"], S["knell"], S["launcher"]
FENCE = "\x60" * 3


def slender(stl, feats):
    return {"tool": "miniature_slender_feature_check", "args": {"stl_path": up(stl), "process": P, "features": feats}}


def feat(name, a, b, mn, st=5, r=1.2, em=0.1):
    return {"name": name, "start_mm": a, "end_mm": b, "min_mm": mn, "stations": st, "search_radius_mm": r, "end_margin": em}


def gap(stl):
    return {"tool": "miniature_gap_check", "args": {"stl_path": up(stl), "process": P}}


def raked_socket(key):
    """Plan footprint of a raked stem socket for miniature_base_layout_check (same construction as lantern-drones)."""
    B = S["bases"][key]
    pad = B["pad"]
    lean = math.radians(B["rake_deg"])
    d = S["stem"]["socket_d"]
    dep = pad["socket_depth"]
    return {"xy": [pad["xy"][0], round(pad["xy"][1] + dep / 2 * math.sin(lean), 3)],
            "d": round(d / math.cos(lean) + dep * math.sin(lean), 3), "depth": round(dep * math.cos(lean) + d / 2 * math.sin(lean), 3)}


G = S["bases"]
TB = G["base-50-tether"]
MAG = {"xy": [0, 0], "d": G["pocket_d"], "h": G["pocket_depth"]}
tc = A["tail_rotor"]["c"]
ix = A["tail_rotor"]["inner_x"]
hs = K["half_span"]
WL = K["winglet"]
c12 = math.radians(WL["cant_deg"])
PLAN = {
    "scale_features": [
        {"name": "Belfry span (2.17 m)", "real_mm": 2170},
        {"name": "Angelus rotor disc (2.03 m)", "real_mm": 2032},
        {"name": "Knell span (1.8 m)", "real_mm": 1800},
        {"name": "main rotor blade thickness (25 mm)", "kind": "wall", "real_mm": 25},
        {"name": "Belfry prop blade thickness (14 mm)", "kind": "wall", "real_mm": 14},
        {"name": "Knell prop blade thickness (12 mm)", "kind": "wall", "real_mm": 12},
        {"name": "Angelus tail boom (90 mm)", "kind": "wall", "real_mm": 90},
        {"name": "Knell wing tip thickness (30 mm)", "kind": "wall", "real_mm": 30},
        {"name": "skid tube (28 mm, 700 mm free)", "kind": "wire", "real_mm": 28, "wire_length_real_mm": 700},
        {"name": "relay whip (15 mm, 160 mm free)", "kind": "wire", "real_mm": 15, "wire_length_real_mm": 160},
        {"name": "sensor lens bar (20 mm)", "kind": "engraved", "real_mm": 20},
        {"name": "panel line (8 mm)", "kind": "engraved", "real_mm": 8},
    ],
    "exaggerated": ["main rotor blade thickness (25 mm)", "Belfry prop blade thickness (14 mm)", "Knell prop blade thickness (12 mm)",
                    "Angelus tail boom (90 mm)", "Knell wing tip thickness (30 mm)", "skid tube (28 mm, 700 mm free)",
                    "relay whip (15 mm, 160 mm free)", "sensor lens bar (20 mm)", "panel line (8 mm)"],
    "base_and_peg": [
        {"base": "50", "magnet": G["magnet"], "base_height_mm": G["base-50-stem"]["h"]},
        {"base": "40", "magnet": G["magnet"], "base_height_mm": G["base-40-stem"]["h"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * Bf["stem_socket"]["boss_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * A["stem_socket"]["boss_r"]},
        {"base": "40", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * K["stem_socket"]["boss_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * G["base-50-stem"]["pad"]["r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * TB["fairlead"]["r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": Bf["hardpoint"]["peg_d"], "host_section_mm": 2 * Bf["hardpoint"]["boss_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": Bf["mast_socket"]["peg_d"], "host_section_mm": 2 * Bf["mast_socket"]["boss_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": A["pin_d"], "host_section_mm": 2 * A["rotor"]["hub_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": A["tail_rotor"]["pin_d"], "host_section_mm": 2 * A["tail_rotor"]["hub_r"]},
        {"base": "40", "magnet": None, "peg_diameter_mm": L["shuttle_pin_d"], "host_section_mm": 2 * K["stem_socket"]["boss_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": L["peg_d"], "host_section_mm": 2 * L["roof_pad"]["boss_r"]},
        {"base": "50", "magnet": None, "peg_diameter_mm": L["peg_d"], "host_section_mm": 2 * L["tripod"]["head_r"]},
    ],
    "extra_calls": [
        {"tool": "miniature_detail_advice", "args": {"scale": "1:56", "process": P, "features": [
            {"kind": "panel_line", "real_mm": 8, "name": "panel line / lens bar"},
            {"kind": "wall", "real_mm": 25, "name": "rotor blade"},
            {"kind": "weapon_haft", "real_mm": 28, "name": "skid tube", "length_mm": 12.0},
            {"kind": "weapon_haft", "real_mm": 15, "name": "relay whip", "length_mm": 2.9},
            {"kind": "rivet", "real_mm": 10, "name": "hub / blister"}]}},
        *[{"tool": "miniature_base_layout_check", "args": {
            "base_d_mm": G[k]["d"], "base_height_mm": round(G[k]["h"] + G[k]["pad"]["h"] + 0.15, 3), "top_inset_mm": G[k]["inset"],
            "process": P, "parts": [{"name": "launch pad (stem)", "xy": G[k]["pad"]["xy"], "r": [G[k]["pad"]["r"], G[k]["pad"]["r"]],
                                     "socket": raked_socket(k)}], "magnet": MAG}} for k in ("base-50-stem", "base-40-stem")],
        {"tool": "miniature_base_layout_check", "args": {
            "base_d_mm": 50, "base_height_mm": TB["h"], "top_inset_mm": TB["inset"], "process": P,
            "parts": [{"name": "generator", "xy": TB["generator"]["c"], "r": TB["generator"]["half"][:2]},
                      {"name": "cable spool", "xy": TB["spool"]["c"][:2], "r": [TB["spool"]["w"] / 2 + 1.1, 5.4]},
                      {"name": "fairlead", "xy": [0, 0], "r": [3.7, 3.7]}], "magnet": MAG}},
        {"tool": "miniature_base_layout_check", "args": {
            "base_d_mm": 50, "base_height_mm": TB["fairlead"]["top_z"], "top_inset_mm": TB["inset"], "process": P,
            "parts": [{"name": "fairlead (vertical tether socket)", "xy": [0, 0], "r": [TB["fairlead"]["r"]] * 2,
                       "socket": {"xy": [0, 0], "d": S["stem"]["socket_d"], "depth": TB["fairlead"]["socket_depth"]}}],
            "magnet": MAG}},
        slender("belfry", [feat("arm (left side)", [5.0, 0, 0.42], [11.0, 0, 0.55], 1.0),
                           feat("upper prop blade (left motor)", [13.9, 1.6, 2.35], [13.9, 4.6, 2.35], 0.8, r=1.0),
                           feat("skid strut (left rear)", [3.3, 3.48, -2.97], [4.6, 3.77, -5.3], 0.9),
                           feat("skid tube (left)", [5.2, -4.0, -6.45], [5.2, 4.5, -6.45], 0.9)]),
        slender("angelus", [feat("tail boom", [0, 11.0, 11.92], [0, 23.0, 12.5], 1.3, st=8, r=1.5),
                            feat("skid tube (left)", [4.9, -6.0, 0.5], [4.9, 4.5, 0.5], 0.85),
                            feat("skid cross tube (left front)", [4.9, -4.0, 0.9], [4.67, -4.0, 3.2], 0.9),
                            feat("fin", [0, 24.6, 13.6], [0, 25.8, 16.6], 0.8),
                            feat("rotor pin", [0, A["mast_xy"][1], 17.2], [0, A["mast_xy"][1], 18.1], 1.2, r=1.0),
                            feat("tail-rotor pin", [tc[0] + ix + 0.1, tc[1], tc[2]], [tc[0] + ix + 0.8, tc[1], tc[2]], 0.9, st=3, r=0.8)]),
        slender("angelus-main-rotor", [feat("main rotor blade", [4.0, 0, 0.45], [16.0, 0, 0.45], 0.8, st=8)]),
        slender("angelus-tail-rotor", [feat("tail rotor blade", [1.0, 0, 0.42], [2.8, 0, 0.42], 0.75, st=4, r=0.8)]),
        slender("knell", [feat("outer wing", [10.0, 5.7, 0.0], [15.0, 8.3, 0.0], 0.8, st=6, r=1.5),
                          feat("upper winglet", [hs - 0.25 + 0.8 * math.sin(c12), 9.0, 0.8 * math.cos(c12)],
                               [hs - 0.25 + 3.4 * math.sin(c12), 10.4, 3.4 * math.cos(c12)], 0.75),
                          feat("pusher prop blade", [0.6, K["prop"]["y"], 0.2 - 1.04], [1.6, K["prop"]["y"], 0.2 - 2.57], 0.75, st=4, r=1.0)]),
        slender("launcher-tripod", [feat("leg", [0, 4.42, 5.74], [0, 10.14, 2.41], 1.2, st=6)]),
        slender("vl-10-eo-mast", [feat("mast", [0, 0, 1.0], [0, 0, 5.2], 1.3)]),
        slender("vl-11-relay-mast", [feat("whip", [0, 0, 6.0], [0, 0, 7.8], 0.9, st=4, r=0.8)]),
        slender("flight-stem", [feat("flight stem", [0, 0, 1.0], [0, 0, 37.0], 1.5, st=10, r=1.5)]),
        *[gap(n) for n in ("belfry", "angelus", "angelus-main-rotor", "knell", "launcher-rail", "launcher-tripod", "launcher-roof-pad",
                           "vl-01-eo-turret", "vl-02-sar-pod", "vl-03-twin-munitions", "vl-04-cargo-pod", "vl-10-eo-mast",
                           "vl-11-relay-mast", "vl-12-radar-mast", "base-50-stem", "base-40-stem", "base-50-tether")],
    ],
    "parts": [
        {"stl": "belfry", "label": "VA-1 Belfry heavy-lift hexacopter", "qty": 1},
        {"stl": "angelus", "label": "VA-2 Angelus airframe", "qty": 1},
        {"stl": "angelus-main-rotor", "label": "VA-2 main rotor", "qty": 1, "flat": True, "on_build_plate": True,
         "orientation": "flat on the plate (underside down), no supports", "supports": "none"},
        {"stl": "angelus-tail-rotor", "label": "VA-2 tail rotor", "qty": 1, "flat": True, "on_build_plate": True,
         "orientation": "flat on the plate (underside down), no supports", "supports": "none"},
        {"stl": "knell", "label": "VA-3 Knell loitering UAV", "qty": 1},
        {"stl": "launcher-rail", "label": "Knell rail launcher", "qty": 1},
        {"stl": "launcher-tripod", "label": "Launcher tripod", "qty": 1},
        {"stl": "launcher-roof-pad", "label": "Launcher roof pad (Wayfarer)", "qty": 1},
        {"stl": "vl-01-eo-turret", "label": "VL-01 EO/IR turret", "qty": 1},
        {"stl": "vl-02-sar-pod", "label": "VL-02 SAR pod", "qty": 1},
        {"stl": "vl-03-twin-munitions", "label": "VL-03 twin glide munitions", "qty": 1},
        {"stl": "vl-04-cargo-pod", "label": "VL-04 cargo pod", "qty": 1},
        {"stl": "vl-10-eo-mast", "label": "VL-10 EO ball mast", "qty": 1},
        {"stl": "vl-11-relay-mast", "label": "VL-11 relay mast", "qty": 1},
        {"stl": "vl-12-radar-mast", "label": "VL-12 radar mast", "qty": 1},
        {"stl": "flight-stem", "label": "Flight stem 1.6 mm", "qty": 4},
        {"stl": "base-50-stem", "label": "50 mm flight base", "qty": 2},
        {"stl": "base-40-stem", "label": "40 mm flight base", "qty": 1},
        {"stl": "base-50-tether", "label": "50 mm tether station", "qty": 1},
    ],
    "plate_printer": "elegoo_mars_5_ultra",
}

CACHE = PKG / "build" / "checkcache"


def _files(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _files(v)
    elif isinstance(o, list):
        for v in o:
            yield from _files(v)
    elif isinstance(o, str) and o.endswith(".stl"):
        yield o


def _key(tool, args):
    h = hashlib.sha256(json.dumps([tool, args], sort_keys=True).encode())
    for f in sorted(set(_files(args))):
        h.update(hashlib.sha256(Path(f).read_bytes()).digest())
    return h.hexdigest()[:24]


def sizing_drift(fresh, build):
    """The model must still match the sizing: Knell socket CG inside the static-margin band, Belfry hardpoint on the
    empty CG (within 15 mm in-world), Angelus CG within the mast tolerance, launch stroke covered by the rail."""
    p = []
    kn = fresh["knell_fixed_wing"]["stability"]
    lo, hi = kn["cg_range_for_margin_x_mm"]
    if not lo <= S["knell"]["cg_x_real_mm"] <= hi:
        p.append(f"sizing: Knell socket CG {S['knell']['cg_x_real_mm']} outside the static-margin band {lo}-{hi}")
    cg_e = fresh["belfry_mass_cg_empty"]["cg_mm"]
    hp_real = Bf["hardpoint"]["xy"][1] * 56
    if abs(cg_e[1] - hp_real) > 15:
        p.append(f"sizing: Belfry hardpoint y {hp_real:.0f} mm not on the empty CG {cg_e[1]:.0f} mm")
    if not fresh["angelus_mass_cg"].get("cg_within_tolerance", False):
        p.append("sizing: Angelus CG outside the mast tolerance")
    ln = fresh["knell_fixed_wing"].get("launch") or {}
    need = ln.get("stroke_m") or ln.get("required_stroke_m")
    have = build["fits"]["knell_on_launcher"]["stroke_in_world_m"]
    if need and have < need:
        p.append(f"sizing: launcher stroke {have} m < required {need} m")
    return p


def fit_problems(build):
    f = build["fits"]
    p = []
    for k in ("belfry_flying", "angelus_flying", "knell_flying"):
        if f[k]["drone_base_overlap_mm3"] > 0.02:
            p.append(f"fit: {k} airframe touches its base")
        if f[k]["drone_bottom_above_base_top_mm"] < 5.0:
            p.append(f"fit: {k} flies less than 5 mm above the base")
    for n, r in f["belfry_loadouts"].items():
        if r["overlap_with_belfry_mm3"] > 0.05:
            p.append(f"fit: {n} overlaps the Belfry {r['overlap_with_belfry_mm3']} mm3")
        if "clearance_above_skid_plane_mm" in r and r["clearance_above_skid_plane_mm"] < Bf["payload_clear_mm"]:
            p.append(f"fit: {n} hangs below the skid plane margin ({r['clearance_above_skid_plane_mm']} mm)")
        if r.get("overlap_with_flying_stem_mm3", 0) > 0.02:
            p.append(f"fit: {n} hits the flying stem")
    for n, r in f.get("belfry_tethered_station_masts", {}).items():
        if r["overlap_with_station_mm3"] > 0.05 or r["overlap_with_tethered_belfry_mm3"] > 0.0:
            p.append(f"fit: {n} on the tether station collides")
        if r["gap_to_tethered_belfry_mm"] < 1.0:
            p.append(f"fit: {n} on the tether station within 1 mm of the tethered Belfry")
    ro = f["angelus_rotors"]
    for n in ("angelus-main-rotor", "angelus-tail-rotor"):
        if ro[n]["overlap_with_airframe_mm3"] > 0.05:
            p.append(f"fit: {n} overlaps the airframe")
    if ro["main_to_tail_rotor_gap_mm"] < 0.5:
        p.append("fit: main and tail rotor discs closer than 0.5 mm")
    kl = f["knell_on_launcher"]
    if kl["overlap_knell_rail_mm3"] > 0.05:
        p.append("fit: Knell overlaps the launcher")
    w = f["wayfarer_roof"]
    if w.get("status") != "UNKNOWN":
        if w["overlap_pad_hull_mm3"] > 0.05 or w["overlap_rail_hull_mm3"] > 0.02 or w["overlap_knell_hull_mm3"] > 0.02:
            p.append("fit: launcher stack overlaps the Wayfarer hull")
        if w["overlap_stack_rws_at_yaw0_mm3"] > 0.02:
            p.append("fit: launcher stack hits the RWS at its forward (0 deg) position")
        if w["roof_fraction_at_plane"] < 0.98 or w["roof_max_above_plane_mm"] > 0.05:
            p.append(f"fit: roof under the pad is not flat (fraction at plane {w['roof_fraction_at_plane']}, max above {w['roof_max_above_plane_mm']})")
    return p


async def run(pkg, spec, plan):
    from fastmcp import Client
    from unified_cad_mcp.config import AirframeConfig, Configuration
    from unified_cad_mcp.server import create_server
    CACHE.mkdir(parents=True, exist_ok=True)
    process = spec["process"]
    printer = mcpcheck.PRINTERS[process]
    up_, out = pkg / "build" / "upright", pkg / "print" / "stl"
    out.mkdir(parents=True, exist_ok=True)
    (pkg / "reports").mkdir(exist_ok=True)
    cfg = Configuration(project_root=str(pkg), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(pkg / "print"), read_roots=[str(pkg / "build")]))
    report = {"process": process, "printer": printer, "tool_calls": []}
    problems = []
    build = json.loads((pkg / "reports" / "build.json").read_text())
    async with Client(create_server(cfg), timeout=3600) as c:
        async def call(tool, args):
            p = CACHE / f"{tool}-{_key(tool, args)}.json"
            if p.exists():
                data = json.loads(p.read_text())
                src = "cached"
            else:
                t0 = time.time()
                data = (await c.call_tool(tool, args)).data
                p.write_text(json.dumps(data))
                src = f"{time.time() - t0:.0f} s"
            print(f"  {tool} {Path(args.get('stl_path', '')).name or ''} ({src})", flush=True)
            report["tool_calls"].append({"tool": tool, "args": args})
            return data
        import sizing
        fresh = {}
        a, k = S["real_world"]["angelus"], S["real_world"]["knell"]
        fresh["belfry_mass_cg_empty"] = await call("drone_mass_cg_budget", {"items": sizing.belfry_mass(False), "reference_point_mm": [0, 0, 0], "cg_tolerance_mm": 15})
        fresh["angelus_mass_cg"] = await call("drone_mass_cg_budget", {"items": a["mass_items"], "reference_point_mm": [0, a["mast_y_mm"], 0],
                                                                    "max_takeoff_mass_g": a["auw_g"], "cg_tolerance_mm": 25})
        fresh["knell_fixed_wing"] = await call("drone_fixed_wing_analysis", {"aircraft": k["aircraft"]})
        report["sizing"] = {"knell_stability": fresh["knell_fixed_wing"]["stability"], "knell_launch": fresh["knell_fixed_wing"].get("launch"),
                            "belfry_cg_empty_mm": fresh["belfry_mass_cg_empty"]["cg_mm"],
                            "angelus_cg_offset_mm": fresh["angelus_mass_cg"].get("cg_offset_from_reference_mm")}
        problems += sizing_drift(fresh, build)
        problems += fit_problems(build)
        if plan.get("scale_features"):
            report["scale_convert"] = await call("miniature_scale_convert", {"scale": spec["scale"]["tool_scale"], "process": process,
                                                                             "features": plan["scale_features"]})
            problems += [f"scale: {n} below the process limit and not exaggerated" for n in report["scale_convert"]["below_limit"]
                         if n not in plan.get("exaggerated", [])]
        report["base_and_peg"] = []
        for args in plan.get("base_and_peg", []):
            r = await call("miniature_base_and_peg", {**args, "process": process})
            report["base_and_peg"].append(r)
            problems += [f"base_and_peg: {ch['name']} = {ch['value']} (limit {ch['limit']})" for ch in r["checks"] if not ch["pass"]]
        for extra in plan.get("extra_calls", []):
            r = await call(extra["tool"], extra["args"])
            report.setdefault("extra", []).append({"tool": extra["tool"], "stl": extra["args"].get("stl_path"), "result": r})
            if r.get("all_checks_pass") is False:
                problems.append(f"{extra['tool']} {Path(extra['args'].get('stl_path', '')).name}: failed")
        report["parts"] = {}
        for part in plan["parts"]:
            name = part["stl"]
            entry = {}
            sp = await call("miniature_support_plan", {"stl_path": str(up_ / f"{name}.stl"), "process": process})
            entry["support_plan"] = {k: sp[k] for k in ("as_modelled", "best", "orientations_sampled", "score")}
            rot = [0.0, 0.0, 0.0] if part.get("flat") else sp["best"][0]["rotate_deg"]
            tris = mcpcheck.to_plate(mcpcheck.rotate(mcpcheck.read_stl(up_ / f"{name}.stl"), *rot))
            mcpcheck.write_stl(out / f"{name}.stl", tris)
            (out / f"{name}.stl.meta.json").write_text(json.dumps({"units": "mm", "format": "unified-cad-mcp/stl-meta@1",
                                                                     "source": "source/build.py + source/check.py (print pose)",
                                                                     "rotate_deg_from_model": rot}, indent=1, sort_keys=True))
            args = {"stl_path": str(out / f"{name}.stl"), "process": process, "on_build_plate": bool(part.get("on_build_plate")),
                    "build_volume_mm": printer["build_volume_mm"]}
            args.update({k: part[k] for k in ("expected_bodies", "thin_area_tolerance_mm2") if k in part})
            r = await call("miniature_printability_check", args)
            entry.update(rotate_deg=rot, pose=mcpcheck.describe_pose(part, rot), qty=part.get("qty", 1), label=part["label"],
                         supports=part.get("supports") or "light/medium resin supports", printability=r)
            report["parts"][name] = entry
            problems += [f"{name}: {ch['name']} = {ch['value']} (limit {ch['limit']})" for ch in r["checks"] if not ch["pass"] and ch["severity"] == "fail"]
        if plan.get("plate_printer"):
            report["plate_pack"] = await call("miniature_plate_pack", {"printer": plan["plate_printer"], "parts": [
                {"name": e["label"], "qty": e["qty"], "footprint_mm": e["printability"]["bounding_box_mm"]["size"][:2],
                 "height_mm": e["printability"]["bounding_box_mm"]["size"][2]} for e in report["parts"].values()]})
        post = {}
        for part in plan["parts"]:
            n = part["stl"]
            sa = await call("miniature_shell_audit", {"stl_path": str(out / f"{n}.stl")})
            row = build["parts"][n]
            mb = await call("miniature_mesh_budget", {"current_triangles": row["triangles"], "current_pitch_mm": row["pitch_mm"],
                                                      "min_feature_mm": 0.4})
            post[n] = {"shell_audit": {k: sa.get(k) for k in ("shell_count", "speck_shells", "inside_out_shells", "clean")},
                       "mesh_budget": {k: mb.get(k) for k in ("recommended_pitch_mm", "predicted_triangles", "under_checker_limit", "warnings")}
                       | {"pitch_mm": row["pitch_mm"], "triangles": row["triangles"]}}
            if not sa.get("clean"):
                problems.append(f"{n}: shell audit not clean")
            if mb.get("under_checker_limit") is False:
                problems.append(f"{n}: over the checker triangle limit")
        report["post_checks"] = post
    report["problems"] = problems
    report["all_pass"] = not problems
    return report


def main():
    pkg = PKG
    rep = asyncio.run(run(pkg, S, PLAN))
    (pkg / "reports" / "printability.json").write_text(json.dumps(rep, indent=1))
    mcpcheck.write_markdown(pkg, S, rep)
    md = (pkg / "reports" / "printability.md").read_text()
    md += "\n## Extra checks (detail advice, base layout, slender features, gaps)\n\n| Tool | File | Pass | Notes |\n|---|---|---|---|\n"
    for x in rep.get("extra", []):
        r = x["result"]
        fails = [f"{c['name']}={c.get('value')}" for c in r.get("checks", []) if not c.get("pass")]
        md += f"| {x['tool']} | {Path(x.get('stl') or '').name or '-'} | {r.get('all_checks_pass', 'n/a')} | {'; '.join(fails) or ''} |\n"
    md += "\n## Shell audit and mesh budget (miniature_shell_audit on print/stl, miniature_mesh_budget per part)\n\n"
    md += "| Part | Shells | Specks | Inside-out | Clean | Pitch mm | Triangles | Under limit |\n|---|---|---|---|---|---|---|---|\n"
    for n, v in rep["post_checks"].items():
        s, m = v["shell_audit"], v["mesh_budget"]
        md += f"| {n} | {s['shell_count']} | {s['speck_shells']} | {s['inside_out_shells']} | {s['clean']} | {m['pitch_mm']} | {m['triangles']} | {m['under_checker_limit']} |\n"
    md += "\n## Sizing (drone_* re-run)\n\n" + FENCE + "json\n" + json.dumps(rep["sizing"], indent=1) + "\n" + FENCE + "\n"
    md += "\n## Problems\n\n" + ("\n".join(f"- {p}" for p in rep["problems"]) or "none") + "\n"
    (pkg / "reports" / "printability.md").write_text(md)
    mcpcheck.write_mini_json(pkg, S, rep)
    print(json.dumps({"all_pass": rep["all_pass"], "problems": rep["problems"],
                      "parts": {k: {"pose": v["pose"], "ml": v["printability"]["resin_ml"], "warnings": v["printability"]["warnings"]}
                                for k, v in rep["parts"].items()}}, indent=1))
    sys.exit(0 if rep["all_pass"] else 1)


if __name__ == "__main__":
    main()
