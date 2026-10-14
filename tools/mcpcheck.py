"""Shared printability driver: runs the unified-CAD-MCP miniature_* tools in-process (the same MCP calls an agent makes).

Copied from SolutionsAsService/fantasy-miniatures tools/mcpcheck.py (same package format); scifi changes: the mini.json
it writes carries "line": "scifi" and the spec's images, and parts may set expected_bodies / thin_area_tolerance_mm2.

Run with a Python that has unified-cad-mcp installed, e.g.
    /mnt/d/ai-stack/repos/unified-CAD-MCP/.venv/bin/python <mini>/source/check.py
For every part in the plan it
  1. picks the print pose: flat on the plate as modelled, or the best rotation from miniature_support_plan,
  2. writes the part in that pose to print/stl/<part>.stl (+ units sidecar): the file you slice is the file that was checked,
  3. runs miniature_printability_check on that file and fails if any fail-severity check fails,
then writes reports/printability.json, reports/printability.md and mini.json (catalogue entry for the miniature viewer).
"""
import asyncio
import json
import struct
import sys
from pathlib import Path

from fastmcp import Client

from unified_cad_mcp.config import AirframeConfig, Configuration
from unified_cad_mcp.flotation import read_stl
from unified_cad_mcp.miniature import rotate
from unified_cad_mcp.server import create_server

PRINTERS = {
    "msla_resin": {"name": "8K 7-inch class MSLA (e.g. Elegoo Saturn/Mars class)", "build_volume_mm": [153.36, 77.76, 165]},
    "fdm_0.2_nozzle": {"name": "Prusa MK4-class FDM, 0.2 mm nozzle", "build_volume_mm": [250, 210, 220]},
}


def write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"scifi-miniatures print pose".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            f.write(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))


def to_plate(tris):
    lo = [min(q[k] for t in tris for q in t) for k in range(3)]
    hi = [max(q[k] for t in tris for q in t) for k in range(3)]
    d = [-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]]
    return [tuple(tuple(q[k] + d[k] for k in range(3)) for q in t) for t in tris]


def describe_pose(part, rot):
    if part.get("orientation"):
        return part["orientation"]
    if rot == [0.0, 0.0, 0.0] or rot == [0, 0, 0]:
        return "upright as modelled" + (", flat on the plate" if part.get("on_build_plate") else ", on supports")
    return f"tilted {rot[0]:+.0f} deg about x, {rot[1]:+.0f} deg about y, on supports"


async def run_checks(pkg: Path, spec: dict, plan: dict) -> int:
    process = spec["process"]
    printer = PRINTERS[process]
    up, out = pkg / "build" / "upright", pkg / "print" / "stl"
    out.mkdir(parents=True, exist_ok=True)
    (pkg / "reports").mkdir(exist_ok=True)
    cfg = Configuration(project_root=str(pkg), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(pkg / "print"), read_roots=[str(pkg / "build")]))
    report = {"process": process, "printer": printer, "tool_calls": []}
    problems = []
    async with Client(create_server(cfg), timeout=1800) as c:
        async def call(tool, args):
            data = (await c.call_tool(tool, args)).data
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
            report.setdefault("extra", []).append({"tool": extra["tool"], "result": r})
            if r.get("all_checks_pass") is False:
                problems.append(f"{extra['tool']}: failed")
        report["parts"] = {}
        for part in plan["parts"]:
            name = part["stl"]
            entry = {}
            rot = part.get("rotate_deg", [0.0, 0.0, 0.0])
            if part.get("plan"):
                sp = await call("miniature_support_plan", {"stl_path": str(up / f"{name}.stl"), "process": process})
                entry["support_plan"] = {k: sp[k] for k in ("as_modelled", "best", "orientations_sampled", "score")}
                rot = sp["best"][0]["rotate_deg"]
            tris = to_plate(rotate(read_stl(up / f"{name}.stl"), *rot))
            write_stl(out / f"{name}.stl", tris)
            (out / f"{name}.stl.meta.json").write_text(json.dumps({"units": "mm", "format": "unified-cad-mcp/stl-meta@1",
                                                                     "source": "source/build.py + tools/mcpcheck.py (print pose)",
                                                                     "rotate_deg_from_model": rot}, indent=1, sort_keys=True))
            args = {"stl_path": str(out / f"{name}.stl"), "process": process, "on_build_plate": bool(part.get("on_build_plate")),
                    "build_volume_mm": printer["build_volume_mm"]}
            args.update({k: part[k] for k in ("expected_bodies", "thin_area_tolerance_mm2") if k in part})
            if process.startswith("fdm"):
                args["max_cup_area_mm2"] = 100000  # suction cups are vat-film physics (MSLA); an FDM nozzle has no peel
            r = await call("miniature_printability_check", args)
            entry.update(rotate_deg=rot, pose=describe_pose(part, rot), qty=part.get("qty", 1), label=part["label"],
                         supports=part.get("supports") or ("none (flat on the plate)" if part.get("on_build_plate") else "light/medium resin supports"),
                         printability=r)
            if name in plan.get("hollow", []):
                entry["hollow_plan"] = await call("miniature_hollow_plan", {"stl_path": str(out / f"{name}.stl"), "process": process})
            report["parts"][name] = entry
            problems += [f"{name}: {ch['name']} = {ch['value']} (limit {ch['limit']})" for ch in r["checks"] if not ch["pass"] and ch["severity"] == "fail"]
        if plan.get("plate_printer"):
            report["plate_pack"] = await call("miniature_plate_pack", {"printer": plan["plate_printer"], "parts": [
                {"name": e["label"], "qty": e["qty"], "footprint_mm": e["printability"]["bounding_box_mm"]["size"][:2],
                 "height_mm": e["printability"]["bounding_box_mm"]["size"][2]} for e in report["parts"].values()]})
    report["problems"] = problems
    report["all_pass"] = not problems
    (pkg / "reports" / "printability.json").write_text(json.dumps(report, indent=1))
    write_markdown(pkg, spec, report)
    write_mini_json(pkg, spec, report)
    print(json.dumps({"all_pass": report["all_pass"], "problems": problems,
                      "parts": {k: {"pose": v["pose"], "ml": v["printability"]["resin_ml"], "warnings": v["printability"]["warnings"]}
                                for k, v in report["parts"].items()}}, indent=1))
    return 0 if not problems else 1


def write_markdown(pkg, spec, rep):
    L = [f"# {spec['name']}: printability report", "",
         f"Generated by `source/check.py` through the unified-CAD-MCP `miniature_*` tools. Process `{rep['process']}`, "
         f"printer class: {rep['printer']['name']} (build volume {' x '.join(str(v) for v in rep['printer']['build_volume_mm'])} mm).", "",
         f"**Result: {'PASS' if rep['all_pass'] else 'FAIL'}** (all fail-severity checks on every part).", ""]
    if rep.get("scale_convert"):
        L += ["## Scale (miniature_scale_convert)", "", f"Scale {rep['scale_convert'].get('scale', spec['scale']['tool_scale'])}, ratio 1:{rep['scale_convert']['ratio']:.1f}.", "",
              "| Feature | Real mm | Model mm | Limit | Printable as converted |", "|---|---|---|---|---|"]
        for f in rep["scale_convert"]["features"]:
            L.append(f"| {f['name']} | {f['real_mm']} | {f['model_mm']} | {f.get('limit_mm', '')} | {'yes' if f['printable'] else 'no: exaggerated in the model'} |")
        L.append("")
    for b in rep.get("base_and_peg", []):
        L += ["## Base and joints (miniature_base_and_peg)", "", "| Check | Value | Limit | Pass |", "|---|---|---|---|"]
        L += [f"| {c['name']} | {c['value']} | {c['limit']} | {'yes' if c['pass'] else 'NO'} |" for c in b["checks"]]
        L.append("")
    L += ["## Parts (miniature_printability_check, in print pose)", "",
          "| Part | Qty | Pose | Volume ml | Min wall mm | Islands | Largest cup mm2 | Largest layer mm2 | Fails | Warnings |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for name, e in rep["parts"].items():
        r = e["printability"]
        fails = [c["name"] for c in r["checks"] if not c["pass"] and c["severity"] == "fail"]
        cup = max((c["max_area_mm2"] for c in r["suction_cups"]), default=0)
        L.append(f"| {e['label']} | {e['qty']} | {e['pose']} | {r['resin_ml']} | {r['thickness']['min_mm']} | {r['islands']['count']} | {cup} | "
                 f"{r['largest_layer']['area_mm2']} | {', '.join(fails) or 'none'} | {', '.join(r['warnings']) or 'none'} |")
    for name, e in rep["parts"].items():
        if e.get("hollow_plan"):
            h = e["hollow_plan"]
            L += [f"## Hollowing: {e['label']} (miniature_hollow_plan)", "", f"Hollow: {'yes' if h['recommend_hollow'] else 'no'}; "
                  f"{h['volume_ml']} ml solid, shell {h['shell_mm']} mm would save {h['resin_saved_ml']} ml. " + "; ".join(h["reasons"]) + ".", ""]
    for x in rep.get("extra", []):
        L += [f"## {x['tool']}", "", "```json", json.dumps(x["result"], indent=1)[:2500], "```", ""]
    if rep.get("plate_pack"):
        pp = rep["plate_pack"]
        L += ["## Print batch (miniature_plate_pack)", "", f"One full set on a {pp['printer']}: {pp['plates']} plate(s), "
              f"fill {pp['plate_fill']:.0%}, per plate {pp['per_plate']}" + (f", too big: {pp['too_big']}" if pp["too_big"] else "") + ".", ""]
    L += ["", "Warnings are advisory (supports are planned for every part not printed flat on the plate). This is a heuristic "
          "screen, not a slicer: confirm supports and suction in Lychee/CHITUBOX/PrusaSlicer and print a test piece.", ""]
    (pkg / "reports" / "printability.md").write_text("\n".join(L))


def write_mini_json(pkg, spec, rep):
    cat = spec["catalog"]
    parts = rep["parts"]
    total_ml = sum(e["printability"]["resin_ml"] * e["qty"] for e in parts.values())
    warn = sorted({w for e in parts.values() for w in e["printability"]["warnings"]})
    resin = rep["process"] == "msla_resin"
    mini = {
        "scale": {"label": spec["scale"]["label"], "ratio": spec["scale"]["ratio"]},
        "base": cat["base"], "footprint": cat["footprint"],
        "process": ("MSLA resin" if resin else "FDM, 0.2 mm nozzle") + f" · {rep['printer']['name']}",
        "volumeMl": round(total_ml, 1), "volumeLabel": "Resin volume" if resin else "Filament volume",
        "printHeightMm": round(max(e["printability"]["bounding_box_mm"]["size"][2] for e in parts.values()), 1),
        "printability": {"verdict": "pass" if rep["all_pass"] else "fail", "preset": rep["process"],
                         "checkedBy": "unified-CAD-MCP miniature_printability_check" + (" + support_plan" if any("support_plan" in e for e in parts.values()) else ""),
                         "summary": f"{len(parts)} print files checked in their print pose; no fail-severity findings." if rep["all_pass"] else "; ".join(rep["problems"])[:400],
                         "issues": [f"Advisory: {w}" for w in warn], "report": "reports/printability.md"},
        "printParts": [{"name": e["label"], "qty": e["qty"], "orientation": e["pose"], "supports": e["supports"]} for e in parts.values()],
    }
    meta = {"id": spec["id"], "name": spec["name"], "line": spec.get("line", "scifi"), "family": cat["family"],
            "revision": f"{spec['revision']} · {cat['revision_note']}",
            "description": cat["description"], "images": cat.get("images", []), "defaultExplode": cat.get("defaultExplode", 0),
            "buildNotes": cat.get("buildNotes", []), "limitations": cat.get("limitations", ""), "mini": mini}
    (pkg / "mini.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")


def main(pkg_file, plan):
    pkg = Path(pkg_file).resolve().parents[1]
    spec = json.loads(next((pkg / "spec").glob("*.spec.json")).read_text())
    sys.exit(asyncio.run(run_checks(pkg, spec, plan)))
