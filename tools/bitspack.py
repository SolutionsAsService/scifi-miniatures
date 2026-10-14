"""Build a bits package (helm library, weapon/armour sprue) from tools/armory.py registries.

Each item becomes its own print file named after its identifier (e.g. vh-06-raptor.stl) and viewer part
"VH-06 Raptor", laid out on a grid for the viewer. Used by vigil-helms/ and vigil-armory/.
"""
import json
from pathlib import Path

import armory as A
from vigil import build_loose

COLORS = {"VH": "#6f7a83", "VW": "#4d5257", "VA": "#7b8590"}


def slug(ident, name):
    return f"{ident.lower()}-{name.lower().replace(',', '').replace(' ', '-')}"


def build(pkg, items, cols=5, dx=11.0, dy=12.0, h=0.07, tris=150_000, at_fn=None):
    """items: list of (ident, name, note, mesh_fn(h) -> mesh). at_fn(i, ident) -> (x, y, z) overrides the grid.
    Writes the package and returns the part plan for check.py."""
    pkg = Path(pkg)
    spec = json.loads(next((pkg / "spec").glob("*.spec.json")).read_text())
    parts, plan = [], []
    for i, (ident, name, note, fn) in enumerate(items):
        stl = slug(ident, name)
        mesh = fn(h, f"{ident} {name}", tris)
        at = at_fn(i, ident) if at_fn else ((i % cols - (cols - 1) / 2) * dx, -(i // cols) * dy, 0.0)
        parts.append((f"{ident} {name}", mesh, stl, COLORS[ident[:2]], f"{ident} {name}: {note}", at))
        plan.append({"stl": stl, "label": f"{ident} {name}", "plan": True})
        print(f"{ident} {name}: built", flush=True)
    build_loose(pkg, spec, parts)
    (pkg / "build").mkdir(exist_ok=True)
    (pkg / "build" / "parts-plan.json").write_text(json.dumps(plan, indent=1))
    return plan


def helm_items(idents=None):
    out = []
    for k, (name, note, fn) in A.HELMS.items():
        if idents and k not in idents:
            continue
        out.append((k, name, note, lambda h, nm, t, fn=fn: fn(h).mesh(nm, t)))
    return out


def armory_at(i, ident, n_weapons=len(A.WEAPONS)):
    """Weapons are 20-50 mm long (x -> muzzle, origin at the grip): one per row; armour bits on a row below."""
    if ident.startswith("VW"):
        return (-20.0, -i * 9.0, 0.0)
    j = i - n_weapons
    return ((j - 2) * 11.0, -n_weapons * 9.0 - 4.0, 0.0)


def armory_items():
    out = []
    for reg in (A.WEAPONS, A.ARMOUR):
        for k, (name, note, fn) in reg.items():
            out.append((k, name, note, lambda h, nm, t, fn=fn: A.sculpt_shape(fn(), nm, h, t)))
    return out
