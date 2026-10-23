#!/usr/bin/env python3
"""Printability of the phase 2 option parts through the unified-CAD-MCP miniature_* tools (same route as check.py).

Run after source/options.py:
    PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check_options.py [part ...]
For every build/options/*.stl it picks the print pose (flat on the plate, or miniature_support_plan's best rotation),
writes print/stl/options/<part>.stl (+ units sidecar), runs miniature_printability_check on that file (plus
miniature_shell_audit and miniature_mesh_budget on the SDF commander), then writes reports/options-printability.{json,md}
and adds an "options" block to mini.json (run AFTER check.py, which rewrites mini.json). AW-8A's reports stay untouched.
"""
import asyncio
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from mcpcheck import PRINTERS, describe_pose, to_plate, write_stl  # noqa: E402

from fastmcp import Client  # noqa: E402
from unified_cad_mcp.config import AirframeConfig, Configuration  # noqa: E402
from unified_cad_mcp.flotation import read_stl  # noqa: E402
from unified_cad_mcp.miniature import rotate  # noqa: E402
from unified_cad_mcp.server import create_server  # noqa: E402

S = json.loads((PKG / "spec" / "wayfarer-apc.spec.json").read_text())
FLAT = {"opt-crate-large": "on its bottom", "opt-crate-small": "on its bottom", "opt-roll": "on its glue strip",
        "opt-jerrican-rack": "on the rack floor", "opt-tow-cable": "on its glue strip", "opt-damage-a": "on its back face",
        "opt-damage-b": "on its back face"}
ROT = {"opt-headlight-cage": ([0.0, -90.0, 0.0], "on its back frame (grille up)")}


async def main():
    process = S["process"]
    printer = PRINTERS[process]
    src, out = PKG / "build" / "options", PKG / "print" / "stl" / "options"
    out.mkdir(parents=True, exist_ok=True)
    opts = json.loads((PKG / "reports" / "options.json").read_text())["parts"]
    cfg = Configuration(project_root=str(PKG), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(PKG / "print"), read_roots=[str(PKG / "build")]))
    rep = {"process": process, "printer": printer, "parts": {}, "tool_calls": []}
    problems = []
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    async with Client(create_server(cfg), timeout=3600) as c:
        async def call(tool, args):
            rep["tool_calls"].append({"tool": tool, "args": args})
            return (await c.call_tool(tool, args)).data
        for name, row in opts.items():
            if only and name not in only:
                continue
            stl = src / f"{name}.stl"
            entry = {"label": row["label"], "qty": row["qty"]}
            if name in FLAT:
                rot, pose, flat = [0.0, 0.0, 0.0], f"flat on the plate ({FLAT[name]})", True
            elif name in ROT:
                rot, pose, flat = ROT[name][0], f"flat on the plate ({ROT[name][1]})", True
            else:
                sp = await call("miniature_support_plan", {"stl_path": str(stl), "process": process})
                entry["support_plan"] = {k: sp.get(k) for k in ("as_modelled", "best", "orientations_sampled")}
                rot, flat = sp["best"][0]["rotate_deg"], False
                pose = describe_pose({}, rot)
            tris = to_plate(rotate(read_stl(stl), *rot))
            write_stl(out / f"{name}.stl", tris)
            (out / f"{name}.stl.meta.json").write_text(json.dumps({"units": "mm", "format": "unified-cad-mcp/stl-meta@1",
                                                                     "source": "source/options.py + source/check_options.py (print pose)",
                                                                     "rotate_deg_from_model": rot}, indent=1, sort_keys=True))
            r = await call("miniature_printability_check", {"stl_path": str(out / f"{name}.stl"), "process": process, "on_build_plate": flat,
                                                            "build_volume_mm": printer["build_volume_mm"]})
            entry.update(rotate_deg=rot, pose=pose, supports="none (flat on the plate)" if flat else "light/medium resin supports", printability=r)
            if name == "opt-commander":
                entry["shell_audit"] = await call("miniature_shell_audit", {"stl_path": str(out / f"{name}.stl")})
                entry["mesh_budget"] = await call("miniature_mesh_budget", {"stl_path": str(out / f"{name}.stl")})
            rep["parts"][name] = entry
            problems += [f"{name}: {ch['name']} = {ch['value']} (limit {ch['limit']})" for ch in r["checks"] if not ch["pass"] and ch["severity"] == "fail"]
            print(name, r["resin_ml"], r["thickness"]["min_mm"], [ch["name"] for ch in r["checks"] if not ch["pass"]], flush=True)
    rep["problems"] = problems
    rep["all_pass"] = not problems
    name = "options-printability" + ("-partial" if only else "")
    (PKG / "reports" / f"{name}.json").write_text(json.dumps(rep, indent=1, default=str))
    L = [f"# {S['name']}: phase 2 option parts, printability", "",
         "Generated by source/check_options.py through the unified-CAD-MCP miniature_* tools (in-process, same server code as "
         f"the live MCP). Process {process}, {printer['name']} ({' x '.join(map(str, printer['build_volume_mm']))} mm).", "",
         f"**Result: {'PASS' if rep['all_pass'] else 'FAIL'}** (fail-severity checks on every option part).", "",
         "| Part | Qty | Pose | Resin ml | Min wall mm | Islands | Largest cup mm2 | Fails | Warnings |", "|---|---|---|---|---|---|---|---|---|"]
    for n, e in rep["parts"].items():
        r = e["printability"]
        fails = [ch["name"] for ch in r["checks"] if not ch["pass"] and ch["severity"] == "fail"]
        cup = max((q.get("max_area_mm2", 0) for q in r.get("suction_cups", [])), default=0)
        L.append(f"| {e['label']} | {e['qty']} | {e['pose']} | {r['resin_ml']} | {r['thickness']['min_mm']} | {r['islands']['count']} | {cup} | "
                 f"{', '.join(fails) or 'none'} | {'; '.join(r['warnings']) or 'none'} |")
    if "opt-commander" in rep["parts"]:
        e = rep["parts"]["opt-commander"]
        L += ["", "Commander (SDF figure): miniature_shell_audit " + json.dumps(e["shell_audit"], default=str)[:600],
              "", "miniature_mesh_budget " + json.dumps(e["mesh_budget"], default=str)[:600]]
    L += ["", "Heuristic screen, not a slicer: confirm supports and suction in your slicer and print a test piece.", ""]
    (PKG / "reports" / f"{name}.md").write_text("\n".join(L))
    if not only:
        mj = json.loads((PKG / "mini.json").read_text())
        mj["options"] = {"verdict": "pass" if rep["all_pass"] else "fail", "report": "reports/options-printability.md",
                         "resinMlAllQty": round(sum(e["printability"]["resin_ml"] * e["qty"] for e in rep["parts"].values()), 2),
                         "parts": [{"name": e["label"], "qty": e["qty"], "orientation": e["pose"], "supports": e["supports"],
                                    "printStl": f"print/stl/options/{n}.stl"} for n, e in rep["parts"].items()]}
        (PKG / "mini.json").write_text(json.dumps(mj, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"all_pass": rep["all_pass"], "problems": problems}, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
