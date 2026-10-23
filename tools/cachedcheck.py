"""Cached, resumable printability driver (generalised from lantern-drones/source/check.py).

Same flow and report shape as tools/mcpcheck.run_checks, plus per part miniature_gap_check and miniature_shell_audit
on the print-pose file. Every MCP tool result is cached under <pkg>/build/checkcache keyed by tool + arguments + the
sha256 of every STL the call reads, so a killed run (OOM, crash) resumes and unchanged parts are never re-checked.

Use from a package check.py:   import cachedcheck; cachedcheck.main(__file__, PLAN)
    check.py stem1,stem2   -> only these parts (dev loop; reports/ and mini.json are not rewritten)
Run with the unified-CAD-MCP venv python, one process, under the memory cap (systemd-run --scope -p MemoryMax=1500M).
"""
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path

import mcpcheck


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


async def run(pkg, spec, plan, only=None):
    from fastmcp import Client
    from unified_cad_mcp.config import AirframeConfig, Configuration
    from unified_cad_mcp.server import create_server
    cache = pkg / "build" / "checkcache"
    cache.mkdir(parents=True, exist_ok=True)
    process = spec["process"]
    printer = mcpcheck.PRINTERS[process]
    up, out = pkg / "build" / "upright", pkg / "print" / "stl"
    out.mkdir(parents=True, exist_ok=True)
    (pkg / "reports").mkdir(exist_ok=True)
    cfg = Configuration(project_root=str(pkg), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(pkg / "print"), read_roots=[str(pkg / "build")]))
    report = {"process": process, "printer": printer, "tool_calls": []}
    problems = []
    parts = [p for p in plan["parts"] if not only or p["stl"] in only]
    async with Client(create_server(cfg), timeout=3600) as c:
        async def call(tool, args):
            p = cache / f"{tool}-{_key(tool, args)}.json"
            if p.exists():
                data, src = json.loads(p.read_text()), "cached"
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
        report["parts"], post = {}, {}
        for part in parts:
            name = part["stl"]
            entry = {}
            rot = part.get("rotate_deg", [0.0, 0.0, 0.0])
            if part.get("plan"):
                sp = await call("miniature_support_plan", {"stl_path": str(up / f"{name}.stl"), "process": process})
                entry["support_plan"] = {k: sp[k] for k in ("as_modelled", "best", "orientations_sampled", "score")}
                rot = sp["best"][0]["rotate_deg"]
            tris = mcpcheck.to_plate(mcpcheck.rotate(mcpcheck.read_stl(up / f"{name}.stl"), *rot))
            mcpcheck.write_stl(out / f"{name}.stl", tris)
            del tris
            (out / f"{name}.stl.meta.json").write_text(json.dumps({"units": "mm", "format": "unified-cad-mcp/stl-meta@1",
                                                                     "source": "source/build.py + tools/cachedcheck.py (print pose)",
                                                                     "rotate_deg_from_model": rot}, indent=1, sort_keys=True))
            args = {"stl_path": str(out / f"{name}.stl"), "process": process, "on_build_plate": bool(part.get("on_build_plate")),
                    "build_volume_mm": printer["build_volume_mm"]}
            args.update({k: part[k] for k in ("expected_bodies", "thin_area_tolerance_mm2") if k in part})
            r = await call("miniature_printability_check", args)
            entry.update(rotate_deg=rot, pose=mcpcheck.describe_pose(part, rot), qty=part.get("qty", 1), label=part["label"],
                         supports=part.get("supports") or ("none (flat on the plate)" if part.get("on_build_plate") else "light/medium resin supports"),
                         printability=r)
            report["parts"][name] = entry
            problems += [f"{name}: {ch['name']} = {ch['value']} (limit {ch['limit']})" for ch in r["checks"] if not ch["pass"] and ch["severity"] == "fail"]
            g = await call("miniature_gap_check", {"stl_path": str(out / f"{name}.stl"), "process": process})
            sa = await call("miniature_shell_audit", {"stl_path": str(out / f"{name}.stl")})
            post[name] = {"gap_check": g, "shell_audit": {k: sa.get(k) for k in ("shell_count", "speck_shells", "inside_out_shells", "clean")}}
            if g.get("all_checks_pass") is False or g.get("pass") is False:
                problems.append(f"{name}: gap check failed")
            if not sa.get("clean"):
                problems.append(f"{name}: shell audit not clean")
            print(f"  -> {name}: min wall {r['thickness']['min_mm']}, fails {[c['name'] for c in r['checks'] if not c['pass'] and c['severity'] == 'fail']}, "
                  f"gap pass {g.get('all_checks_pass', g.get('pass'))}, shells {sa.get('shell_count')} clean {sa.get('clean')}", flush=True)
        if plan.get("plate_printer") and not only:
            report["plate_pack"] = await call("miniature_plate_pack", {"printer": plan["plate_printer"], "parts": [
                {"name": e["label"], "qty": e["qty"], "footprint_mm": e["printability"]["bounding_box_mm"]["size"][:2],
                 "height_mm": e["printability"]["bounding_box_mm"]["size"][2]} for e in report["parts"].values()]})
        report["post_checks"] = post
    report["problems"] = problems
    report["all_pass"] = not problems
    return report


def main(pkg_file, plan):
    pkg = Path(pkg_file).resolve().parents[1]
    spec = json.loads(next((pkg / "spec").glob("*.spec.json")).read_text())
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    rep = asyncio.run(run(pkg, spec, plan, only))
    if not only:
        (pkg / "reports" / "printability.json").write_text(json.dumps(rep, indent=1))
        mcpcheck.write_markdown(pkg, spec, rep)
        md = (pkg / "reports" / "printability.md").read_text()
        md += "\n## Gap check and shell audit (miniature_gap_check, miniature_shell_audit on print/stl)\n\n"
        md += "| Part | Gap pass | Shells | Specks | Inside-out | Clean |\n|---|---|---|---|---|---|\n"
        for n, v in rep["post_checks"].items():
            s, g = v["shell_audit"], v["gap_check"]
            md += f"| {n} | {g.get('all_checks_pass', g.get('pass'))} | {s['shell_count']} | {s['speck_shells']} | {s['inside_out_shells']} | {s['clean']} |\n"
        md += "\n## Problems\n\n" + ("\n".join(f"- {p}" for p in rep["problems"]) or "none") + "\n"
        (pkg / "reports" / "printability.md").write_text(md)
        mcpcheck.write_mini_json(pkg, spec, rep)
    print(json.dumps({"all_pass": rep["all_pass"], "problems": rep["problems"]}, indent=1))
    sys.exit(0 if rep["all_pass"] else 1)
