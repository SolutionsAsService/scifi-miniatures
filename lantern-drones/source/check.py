#!/usr/bin/env python3
"""Printability check for the Lantern drone kit through the unified-CAD-MCP miniature_* tools (tools/mcpcheck.py driver).

Run: PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check.py
For every part: miniature_support_plan picks the print pose, the part is written in that pose to print/stl/ (+ units
sidecar) and miniature_printability_check runs on that file. Before that: scale_convert, detail_advice, base_and_peg
(every joint), base_layout_check (both bases), slender_feature_check (duct wall, arms, legs, mast, antenna, barrel,
plough arms, stem), gap_check (narrow slits), then shell_audit on every print file and mesh_budget per part.
Fails (exit 1) on any fail-severity finding, a slender/gap/layout check that does not pass, or an unclean shell audit.
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
import mcpcheck  # noqa: E402

S = json.loads((PKG / "spec" / "lantern-drones.spec.json").read_text())
UP = PKG / "build" / "upright"
B = S["base"]
sb = B["stem_boss"]
lean = math.radians(S["stem"]["lean_deg"])
pad_top = B["h"] + sb["h"] + 0.15
bore_plan_d = sb["socket_d"] / math.cos(lean) + sb["socket_depth"] * math.sin(lean)
bore_mid_y = sb["xy"][1] + sb["socket_depth"] / 2 * math.sin(lean)
bore_vert = sb["socket_depth"] * math.cos(lean) + sb["socket_d"] / 2 * math.sin(lean)
T = S["tick"]
W = S["wisp"]
dx, dy, dz = W["duct_centre"]
up = lambda n: str(UP / f"{n}.stl")  # noqa: E731


def slender(stl, feats):
    return {"tool": "miniature_slender_feature_check", "args": {"stl_path": up(stl), "process": S["process"], "features": feats}}


def gap(stl, handles=None):
    a = {"stl_path": up(stl), "process": S["process"]}
    if handles is not None:
        a["expected_handles"] = handles
    return {"tool": "miniature_gap_check", "args": a}


wall_x = dx + (W["duct_r"] + W["duct_bore_r"]) / 2
PLAN = {
    "scale_features": [
        {"name": "Wisp span (0.9 m)", "real_mm": 900},
        {"name": "Tick length (1.05 m)", "real_mm": 1050},
        {"name": "Wisp duct wall (6 mm)", "kind": "wall", "real_mm": 6},
        {"name": "Wisp arm (60 mm)", "kind": "wall", "real_mm": 60},
        {"name": "Tick mast shaft (40 mm, 220 mm free)", "kind": "wire", "real_mm": 40, "wire_length_real_mm": 220},
        {"name": "relay antenna (30 mm, 330 mm free)", "kind": "wire", "real_mm": 30, "wire_length_real_mm": 330},
        {"name": "sensor lens bar (20 mm)", "kind": "engraved", "real_mm": 20},
        {"name": "track shoe gap (12 mm)", "kind": "engraved", "real_mm": 12},
    ],
    "exaggerated": ["Wisp duct wall (6 mm)", "Tick mast shaft (40 mm, 220 mm free)", "relay antenna (30 mm, 330 mm free)",
                    "sensor lens bar (20 mm)", "track shoe gap (12 mm)", "Wisp arm (60 mm)"],
    "base_and_peg": [
        {"base": "32", "magnet": B["magnet"], "base_height_mm": B["h"]},                                            # magnet pocket
        {"base": "32", "magnet": None, "peg_diameter_mm": S["cradle"]["peg_d"], "host_section_mm": 3.6},          # cradle peg in the saddle boss
        {"base": "32", "magnet": None, "peg_diameter_mm": T["weapon_socket"]["peg_d"], "host_section_mm": 2 * T["hull_half_w"]},  # module peg in the deck
        {"base": "32", "magnet": None, "peg_diameter_mm": T["mast_socket"]["peg_d"],
         "host_section_mm": round(2 * (T["hull_half_w"] - abs(T["mast_socket"]["xy"][0])), 2)},                 # mast peg near the hull side
        {"base": "32", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * W["stem_socket"]["boss_r"]},  # stem in the Wisp boss
        {"base": "32", "magnet": None, "peg_diameter_mm": S["stem"]["d"], "host_section_mm": 2 * sb["r"]},         # stem in the base pad
    ],
    "extra_calls": [
        {"tool": "miniature_detail_advice", "args": {"scale": "1:56", "process": S["process"], "features": [
            {"kind": "panel_line", "real_mm": 8, "name": "panel line / lens bar"},
            {"kind": "wall", "real_mm": 6, "name": "duct wall"},
            {"kind": "weapon_haft", "real_mm": 40, "name": "periscope mast", "length_mm": 3.5},
            {"kind": "weapon_haft", "real_mm": 30, "name": "relay antenna", "length_mm": 6.0},
            {"kind": "rivet", "real_mm": 10, "name": "hub / wheel boss"}]}},
        {"tool": "miniature_base_layout_check", "args": {
            "base_d_mm": B["d"], "base_height_mm": round(pad_top, 3), "top_inset_mm": B["top_inset"], "process": S["process"],
            "parts": [{"name": "launch pad (stem)", "xy": sb["xy"], "r": [sb["r"], sb["r"]],
                       "socket": {"xy": [sb["xy"][0], round(bore_mid_y, 3)], "d": round(bore_plan_d, 3), "depth": round(bore_vert, 3)}}],
            "magnet": {"xy": [0, 0], "d": B["pocket_d"], "h": B["pocket_depth"]}}},
        {"tool": "miniature_base_layout_check", "args": {
            "base_d_mm": B["d"], "base_height_mm": B["h"], "top_inset_mm": B["top_inset"], "process": S["process"],
            "parts": [{"name": "Tick (tracks)", "xy": [0, 0], "r": [T["width"] / 2, T["length"] / 2]}],
            "magnet": {"xy": [0, 0], "d": B["pocket_d"], "h": B["pocket_depth"]}}},
        {"tool": "miniature_base_layout_check", "args": {
            "base_d_mm": B["d"], "base_height_mm": B["h"], "top_inset_mm": B["top_inset"], "process": S["process"],
            "parts": [{"name": "landed Wisp (skids)", "xy": [0, 0], "r": [3.8, 5.5]}],
            "magnet": {"xy": [0, 0], "d": B["pocket_d"], "h": B["pocket_depth"]}}},
        slender("wisp-a-recon", [
            {"name": "duct wall (rear left)", "start_mm": [wall_x, dy - 1.0, dz], "end_mm": [wall_x, dy + 1.0, dz], "min_mm": 0.8,
             "stations": 5, "search_radius_mm": 1.2, "end_margin": 0.2},
            {"name": "arm (front left)", "start_mm": [1.9, -2.85, 0.1], "end_mm": [2.8, -3.2, 0.12], "min_mm": 0.9,
             "stations": 4, "search_radius_mm": 1.2, "end_margin": 0.1}]),
        slender("wisp-landed", [
            {"name": "leg (front left)", "start_mm": [2.75, -3.5, -1.0], "end_mm": [3.2, -3.85, -2.5], "min_mm": 0.9,
             "stations": 5, "search_radius_mm": 1.0, "end_margin": 0.1}]),
        slender("tick-mast", [
            {"name": "periscope shaft", "start_mm": [0, 0, 0.8], "end_mm": [0, 0, 3.3], "min_mm": T["min_feature_mm"],
             "stations": 6, "search_radius_mm": 1.0}]),
        slender("tick-weapon-c-relay", [
            {"name": "relay antenna", "start_mm": [0.5, 0.8, 2.6], "end_mm": [0.5, 0.8, 6.5], "min_mm": T["min_feature_mm"],
             "stations": 8, "search_radius_mm": 1.0}]),
        slender("tick-weapon-a-talon", [
            {"name": "Talon barrel (VW-05)", "start_mm": [0, -2.6, 3.95], "end_mm": [0, -4.3, 3.95], "min_mm": T["min_feature_mm"],
             "stations": 5, "search_radius_mm": 1.0}]),
        slender("tick-weapon-b-plough", [
            {"name": "plough arm (left)", "start_mm": [1.2, -1.6, 2.1], "end_mm": [1.2, -7.6, -1.2], "min_mm": T["min_feature_mm"],
             "stations": 8, "search_radius_mm": 1.0}]),
        slender("flight-stem", [
            {"name": "flight stem", "start_mm": [0, 0, 1.0], "end_mm": [0, 0, 26.0], "min_mm": 1.5, "stations": 10,
             "search_radius_mm": 1.5}]),
        gap("wisp-a-recon"), gap("wisp-b-designator"), gap("wisp-landed"), gap("tick-hull"), gap("tick-mast"),
        gap("tick-weapon-a-talon"), gap("tick-weapon-b-plough"), gap("tick-weapon-c-relay"), gap("sdc-cradle"),
        gap("sdc-pack-saddle"), gap("base-32-stem"), gap("base-32-plain"),
    ],
    "parts": [
        {"stl": "wisp-a-recon", "label": "SD-1 Wisp A (recon)", "plan": True},
        {"stl": "wisp-b-designator", "label": "SD-1 Wisp B (designator / munition)", "plan": True},
        {"stl": "wisp-landed", "label": "SD-1 Wisp, landed", "plan": True},
        {"stl": "flight-stem", "label": "Flight stem 1.6 mm", "plan": True, "qty": 2},
        {"stl": "tick-hull", "label": "SD-2 Tick hull + tracks", "plan": True},
        {"stl": "tick-mast", "label": "Tick periscope mast", "plan": True},
        {"stl": "tick-weapon-a-talon", "label": "Tick module A: Talon mount", "plan": True},
        {"stl": "tick-weapon-b-plough", "label": "Tick module B: mine-plough", "plan": True},
        {"stl": "tick-weapon-c-relay", "label": "Tick module C: relay + smoke", "plan": True},
        {"stl": "sdc-cradle", "label": "SD-C cradle with folded Wisp", "plan": True},
        {"stl": "sdc-pack-saddle", "label": "SD-C pack saddle", "plan": True},
        {"stl": "base-32-stem", "label": "32 mm base, stem socket", "plan": True, "qty": 2},
        {"stl": "base-32-plain", "label": "32 mm base, plain", "plan": True, "qty": 2},
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


async def run(pkg, spec, plan):
    """Same flow and report shape as tools/mcpcheck.run_checks, but every tool result is cached under build/checkcache
    keyed by tool + arguments + the sha256 of every STL it reads, so a killed run resumes and unchanged parts are not
    re-checked (a 250k-triangle printability check takes ~5 min on this host)."""
    from fastmcp import Client
    from unified_cad_mcp.config import AirframeConfig, Configuration
    from unified_cad_mcp.server import create_server
    CACHE.mkdir(parents=True, exist_ok=True)
    process = spec["process"]
    printer = mcpcheck.PRINTERS[process]
    up, out = pkg / "build" / "upright", pkg / "print" / "stl"
    out.mkdir(parents=True, exist_ok=True)
    (pkg / "reports").mkdir(exist_ok=True)
    cfg = Configuration(project_root=str(pkg), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(pkg / "print"), read_roots=[str(pkg / "build")]))
    report = {"process": process, "printer": printer, "tool_calls": []}
    problems = []
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
            sp = await call("miniature_support_plan", {"stl_path": str(up / f"{name}.stl"), "process": process})
            entry["support_plan"] = {k: sp[k] for k in ("as_modelled", "best", "orientations_sampled", "score")}
            rot = sp["best"][0]["rotate_deg"]
            tris = mcpcheck.to_plate(mcpcheck.rotate(mcpcheck.read_stl(up / f"{name}.stl"), *rot))
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
        # shell audit on every print file, mesh budget per part
        build = json.loads((pkg / "reports" / "build.json").read_text())
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
    md += "\n## Problems\n\n" + ("\n".join(f"- {p}" for p in rep["problems"]) or "none") + "\n"
    (pkg / "reports" / "printability.md").write_text(md)
    mcpcheck.write_mini_json(pkg, S, rep)
    print(json.dumps({"all_pass": rep["all_pass"], "problems": rep["problems"],
                      "parts": {k: {"pose": v["pose"], "ml": v["printability"]["resin_ml"], "warnings": v["printability"]["warnings"]}
                                for k, v in rep["parts"].items()}}, indent=1))
    sys.exit(0 if rep["all_pass"] else 1)


if __name__ == "__main__":
    main()
