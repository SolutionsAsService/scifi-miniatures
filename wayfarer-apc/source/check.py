#!/usr/bin/env python3
"""Printability and fit checks for the Wayfarer-class APC through the unified-CAD-MCP miniature_* tools.

Run (after source/build.py):
    PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/check.py

1. Fit (reports/fit.json, reports/fit.md): miniature_floor_clearance_check for a 30 mm Vigilant against the stern door and
   the roof hatches, plus the geometric envelope test build.py measured (reports/build.json "fit"). This is a scale /
   gameplay check, reported separately: at true 1:56 the bay is 1.1-1.2 m clear high, so the storey and door-height checks
   fail by design (DESIGN-LOG.md, M5) and must not mask the printability verdict.
2. Printability (tools/mcpcheck.py): print poses, print/stl/*.stl (+ units sidecars), reports/printability.{json,md}, mini.json.
"""
import asyncio
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parent / "tools"))
from mcpcheck import main  # noqa: E402

from fastmcp import Client  # noqa: E402
from unified_cad_mcp.config import AirframeConfig, Configuration  # noqa: E402
from unified_cad_mcp.server import create_server  # noqa: E402

S = json.loads((PKG / "spec" / "wayfarer-apc.spec.json").read_text())
H, RP, HT = S["hull"], S["ramp"], S["hatches"]
T, RZ = H["wall"], H["roof_z"]
door_w = max(y for y, z in RP["aperture"]) - min(y for y, z in RP["aperture"])
door_h = max(z for y, z in RP["aperture"]) - min(z for y, z in RP["aperture"])
bay_h = RZ - T - RP["floor_z"][1]


async def fit():
    cfg = Configuration(project_root=str(PKG), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(PKG / "print"), read_roots=[str(PKG / "build")]))
    out = {"tool_calls": []}
    async with Client(create_server(cfg), timeout=600) as c:
        for label, base in (("Vigilant on a 32 mm base (rifleman / heavy)", 32.0), ("Vigilant on a 25 mm base", 25.0)):
            args = {"scale": "30mm", "storey_clear_mm": round(bay_h, 2), "door_mm": [round(door_w, 2), round(door_h, 2)],
                    "base_height_mm": 4.0, "figure_base_mm": base, "hatch_mm": HT["opening"], "process": S["process"]}
            r = (await c.call_tool("miniature_floor_clearance_check", args)).data
            out["tool_calls"].append({"tool": "miniature_floor_clearance_check", "label": label, "args": args, "result": r})
    b = json.loads((PKG / "reports" / "build.json").read_text())
    out["envelope_test"] = b.get("fit")
    (PKG / "reports" / "fit.json").write_text(json.dumps(out, indent=1))
    L = ["# Wayfarer APC: does a 30 mm Vigilant fit the openings?", "",
         "Two independent measurements. (1) `miniature_floor_clearance_check` (unified-CAD-MCP) with the door and hatch openings "
         f"from the spec: door {door_w:.1f} x {door_h:.1f} mm, hatch {HT['opening'][0]} x {HT['opening'][1]} mm, bay clear height {bay_h:.1f} mm. "
         "(2) The envelope test in `reports/build.json` (build.py `fit_report`): the measured plan envelope of the assembled Vigilant "
         "figures (every Vigil figure package with a viewer mesh, base excluded) slid through the door polygon and the hatch rectangle with 0.5 mm clearance a side; crouched = 65 % of height (Dreyfuss).", ""]
    for call in out["tool_calls"]:
        r = call["result"]
        L += [f"## {call['label']}", "", "| Check | Value | Limit | Pass |", "|---|---|---|---|"]
        for ch in r.get("checks", []):
            L.append(f"| {ch.get('name')} | {ch.get('value')} | {ch.get('limit')} | {'yes' if ch.get('pass') else 'NO'} |")
        L += ["", f"all_checks_pass: **{r.get('all_checks_pass')}**", ""]
    e = out["envelope_test"] or {}
    if e:
        L += ["## Envelope test (measured figures through the openings)", "", "| Figure | Opening | Needs (mm) | Fits |", "|---|---|---|---|"]
        for row in e["openings"]:
            need = row.get("needs_mm") or [row.get("needs_height_mm"), "door " + str(row.get("door_clear_height_mm"))]
            L.append(f"| {row['figure']} | {row['opening']} | {need} | {'yes' if row['fits'] else 'NO'} |")
        L += ["", f"Aisle between the benches {e['aisle_between_benches_mm']} mm; bay clear height {e['bay_clear_height_mm']} mm; "
              f"seat pitch {e['seat_pitch_mm']} mm.", ""]
    L += ["## Reading", "",
          "At true 1:56 the Wayfarer's bay is 1.1-1.2 m clear high (the concept's 2.2 m hull with a V-hull floor), so a standing "
          "1.8 m trooper does not fit the storey or door height: those checks fail by design and are an owner decision "
          "(DESIGN-LOG.md M5, 'true 1:56 kept'). The openings do pass the figure itself: the door width clears a 32 mm base "
          "(tool), a Vigilant passes the door lengthwise and passes a hatch, and the hatches take a Vigilant's upper body "
          "standing in them (open-hatch pose).", ""]
    (PKG / "reports" / "fit.md").write_text("\n".join(L))
    print(json.dumps({"fit": [(c["label"], c["result"].get("all_checks_pass")) for c in out["tool_calls"]]}))


PLAN = {
    "scale_features": [
        {"name": "hull length (8.43 m)", "real_mm": 8430},
        {"name": "hull wall as modelled (1.8 mm = 101 mm)", "kind": "wall", "real_mm": 101},
        {"name": "heavy repeater barrel (70 mm jacket)", "kind": "wire", "real_mm": 70, "wire_length_real_mm": 600},
        {"name": "smoke discharger tube (76 mm)", "kind": "wire", "real_mm": 76, "wire_length_real_mm": 190},
        {"name": "antenna whip (20 mm)", "kind": "wire", "real_mm": 20, "wire_length_real_mm": 2000},
        {"name": "panel line (25 mm)", "kind": "engraved", "real_mm": 25},
        {"name": "periscope lens slit (40 mm)", "kind": "engraved", "real_mm": 40},
        {"name": "tread block height (56 mm)", "kind": "embossed", "real_mm": 56},
        {"name": "drain hole (196 mm)", "kind": "hole", "real_mm": 196},
    ],
    "exaggerated": ["heavy repeater barrel (70 mm jacket)", "smoke discharger tube (76 mm)", "antenna whip (20 mm)",
                    "panel line (25 mm)", "periscope lens slit (40 mm)"],
    "base_and_peg": [
        # RWS turntable underside pocket: 5x2 magnet under the 1.8 mm disc + 4.4 mm pedestal
        {"base": "32", "magnet": "5x2", "base_height_mm": 6.2},
        # hull ring seat: roof wall + 3.0 mm boss under it
        {"base": "32", "magnet": "5x2", "base_height_mm": round(T + S["ring"]["boss_depth"], 2)},
        # wheel D-flat stub in the 7.2 mm wheel boss; split pin in its 6.2 mm boss
        {"base": "32", "magnet": None, "peg_diameter_mm": S["wheels"]["peg"]["d"], "host_section_mm": 2 * S["wheels"]["dish_r"][0]},
        {"base": "32", "magnet": None, "peg_diameter_mm": S["split_pins"]["d"], "host_section_mm": 6.0},
    ],
    "extra_calls": [
        {"tool": "miniature_split_plan", "args": {"size_mm": [152.4, 59.0, 46.2], "printer": "elegoo_mars_5_ultra", "process": "msla_resin"}},
    ],
    "parts": [
        {"stl": "hull-front", "label": "Hull, front half", "rotate_deg": [0.0, -90.0, 0.0], "on_build_plate": True,
         "orientation": "standing on its split face (nose up), flat on the plate",
         "supports": "internal only (under the glacis ceiling inside the cavity); none on show faces"},
        {"stl": "hull-rear", "label": "Hull, rear half", "rotate_deg": [0.0, 90.0, 0.0], "on_build_plate": True,
         "orientation": "standing on its split face (stern up), flat on the plate",
         "supports": "internal only (under the stern-wall ceiling); light supports under the waterjet nozzles and hinge cheeks"},
        {"stl": "wheel", "label": "Wheel", "qty": 8, "rotate_deg": [90.0, 0.0, 0.0],
         "orientation": "standing on its tread (axis horizontal) so neither hub dish faces the film", "supports": "light supports on the lower tread blocks"},
        {"stl": "rws", "label": "Tally RWS", "plan": True},
        {"stl": "ramp", "label": "Stern ramp", "plan": True},
        {"stl": "hatch", "label": "Roof hatch", "qty": 4, "plan": True},
        {"stl": "split-pin", "label": "Split pin (3 mm D-flat; 1 spare)", "qty": 3, "on_build_plate": True,
         "orientation": "lying on its D-flat, flat on the plate"},
    ],
    "hollow": ["hull-front", "hull-rear"],
    "plate_printer": "elegoo_mars_5_ultra",
}

if __name__ == "__main__":
    if "--no-fit" not in sys.argv:
        asyncio.run(fit())
    main(__file__, PLAN)
