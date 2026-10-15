#!/usr/bin/env python3
"""Plausibility sizing for the Vigil aerial wing through the unified-CAD-MCP drone_* calculators (in-process MCP calls).

Run: PYTHONPATH=~/projects/unified-CAD-MCP/src ~/projects/unified-CAD-MCP/.venv/bin/python source/sizing.py
Writes reports/sizing.json. The in-world (1:1) numbers here fix the model proportions in spec/vigil-aerial-drones.spec.json:
rotor and prop diameters, disc loading, the Knell's CG band (its flight-stem socket sits on the chosen CG) and the Belfry
payload hardpoint (on the CG, so a payload does not shift it). check.py re-runs this file's calls and fails on drift.
"""
import asyncio
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
S = json.loads((PKG / "spec" / "vigil-aerial-drones.spec.json").read_text())
R = S["real_world"]


def belfry_mass(payload=True):
    b = R["belfry"]
    rm = b["motor_radius_mm"]
    items = [{"name": "core body + avionics", "mass_g": 7000, "position_mm": [0, 0, 20], "size_mm": [480, 600, 250]},
             {"name": "battery pack L", "mass_g": 5200, "position_mm": [90, 0, 40], "size_mm": [90, 300, 120]},
             {"name": "battery pack R", "mass_g": 5200, "position_mm": [-90, 0, 40], "size_mm": [90, 300, 120]},
             {"name": "chin gimbal turret", "mass_g": 1100, "position_mm": b["chin_turret_mm"]},
             {"name": "mast + EO/radar ball", "mass_g": 700, "position_mm": b["mast_mm"]},
             {"name": "skid gear", "mass_g": 900, "position_mm": [0, 0, -260]}]
    import math
    for k, phi in enumerate(b["arm_phi_deg"]):
        a = math.radians(phi)
        items.append({"name": f"arm + coaxial motor pair {k + 1}", "mass_g": 780,
                      "position_mm": [round(rm * math.sin(a), 1), round(-rm * math.cos(a), 1), 10]})
    if payload:
        items.append({"name": "payload on the hardpoint", "mass_g": b["payload_g"], "position_mm": b["hardpoint_mm"]})
    return items


async def main():
    from fastmcp import Client
    from unified_cad_mcp.config import AirframeConfig, Configuration
    from unified_cad_mcp.server import create_server
    cfg = Configuration(project_root=str(PKG), drone_tools=True, backends={},
                        airframe=AirframeConfig(freecad_python="unused", output_root=str(PKG / "build"), read_roots=[str(PKG / "build")]))
    out = {"note": "In-world (1:1) heuristic sizing; the model is 1:56 of these numbers plus the exaggerations listed in the spec.", "calls": []}
    async with Client(create_server(cfg), timeout=600) as c:
        async def call(tool, args):
            d = (await c.call_tool(tool, args)).data
            out["calls"].append({"tool": tool, "args": args})
            return d
        b, a, k = R["belfry"], R["angelus"], R["knell"]
        out["belfry_propulsion"] = await call("drone_propulsion_estimate", {
            "all_up_mass_g": b["auw_g"], "rotor_count": 12, "coaxial": True, "prop_diameter_in": b["prop_in"],
            "battery_cells": 12, "battery_capacity_mah": 44000, "max_thrust_per_motor_g": b["max_thrust_per_motor_g"],
            "avionics_power_w": 60})
        out["belfry_mass_cg_payload"] = await call("drone_mass_cg_budget", {"items": belfry_mass(True), "reference_point_mm": [0, 0, 0],
                                                                         "max_takeoff_mass_g": b["auw_g"], "cg_tolerance_mm": 15})
        out["belfry_mass_cg_empty"] = await call("drone_mass_cg_budget", {"items": belfry_mass(False), "reference_point_mm": [0, 0, 0],
                                                                       "cg_tolerance_mm": 15})
        out["angelus_propulsion"] = await call("drone_propulsion_estimate", {
            "all_up_mass_g": a["auw_g"], "rotor_count": 1, "prop_diameter_in": a["rotor_in"], "battery_cells": 12,
            "battery_capacity_mah": 32000, "figure_of_merit": 0.65, "avionics_power_w": 40})
        out["angelus_mass_cg"] = await call("drone_mass_cg_budget", {"items": a["mass_items"], "reference_point_mm": [0, a["mast_y_mm"], 0],
                                                                  "max_takeoff_mass_g": a["auw_g"], "cg_tolerance_mm": 25})
        out["knell_fixed_wing"] = await call("drone_fixed_wing_analysis", {"aircraft": k["aircraft"]})
    (PKG / "reports").mkdir(exist_ok=True)
    (PKG / "reports" / "sizing.json").write_text(json.dumps(out, indent=1))
    kp = out["knell_fixed_wing"]
    print(json.dumps({"belfry_prop": {kk: out["belfry_propulsion"].get(kk) for kk in list(out["belfry_propulsion"])[:12]},
                      "belfry_cg": out["belfry_mass_cg_payload"].get("cg_mm"), "belfry_cg_empty": out["belfry_mass_cg_empty"].get("cg_mm"),
                      "angelus_prop": {kk: out["angelus_propulsion"].get(kk) for kk in list(out["angelus_propulsion"])[:12]},
                      "angelus_cg": out["angelus_mass_cg"].get("cg_mm"),
                      "knell_keys": list(kp)}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    asyncio.run(main())
