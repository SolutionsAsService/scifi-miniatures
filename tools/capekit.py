"""Cape kit: a cape that hangs from the shoulders and drapes over the armour (unified-CAD-MCP `cape_plan` cloth model), swept into an SDF shell.

    import capekit
    capekit.cape(g, P, length=17.0, wind=(0.08, 0.3, 0.0))       # g = the figure Sculpt, P = the Pose; adds one blended sheet with fold ribs

Replaces legion.cape (a flat board standing off the back): the top row is pinned on the shoulder line (over each pauldron dome, across the
back of the neck), so the cloth sits ON the shoulders, falls round the chest-back and pack, and the hem trails with the wind.
Body proxies (ellipsoids) come from the Pose: cuirass, both pauldron domes, pelvis, both thighs.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exosuit as X  # noqa: E402
from sdfkit import capsule, frame, rbox, unit, v3  # noqa: E402

_PATHS = (Path(r"E:\unified-CAD-MCP\src\unified_cad_mcp\miniature_cape.py"),
          Path(__file__).resolve().parents[2] / "unified-CAD-MCP" / "src" / "unified_cad_mcp" / "miniature_cape.py")
_spec = next((importlib.util.spec_from_file_location("miniature_cape", p) for p in _PATHS if p.exists()), None)
if _spec is None:
    raise ImportError("unified-CAD-MCP miniature_cape.py not found next to this repo")
MC = importlib.util.module_from_spec(_spec)
sys.modules["miniature_cape"] = MC
_spec.loader.exec_module(MC)

Z = v3(0, 0, 1)


def _body_proxies(P, pauldron=(4.1, 4.3, 3.0)):
    Rc, Rp = P.Rc, P.Rp
    rows = lambda R: tuple(tuple(float(x) for x in R[i]) for i in range(3))  # noqa: E731
    out = [dict(center=list(P.chest + Rc @ v3(0, 0.05, 0.35)), radii=[4.7, 3.15, 3.5], rot=rows(Rc)),
           dict(center=list(P.pelvis + Rp @ v3(0, 0.1, 0.25)), radii=[3.0, 2.2, 2.3], rot=rows(Rp))]
    for i, sgn in ((0, -1), (1, 1)):
        c = P.sh[i] + Rc @ v3(sgn * 1.55, 0, 1.35)
        out.append(dict(center=list(c), radii=list(pauldron), rot=rows(Rc)))
        t = (P.hip[i] + P.knee[i]) / 2
        out.append(dict(center=list(t), radii=[2.5, 2.5, 3.6]))
    return out


def plan(P, length=17.0, wind=(0.08, 0.3, 0.0), rows=15, cols=11, flare=0.3, margin=0.7, floor_z=0.3, steps=260):
    """The cloth plan for pose P: attach points follow the shoulder line (over the pauldron tops, back of the neck)."""
    Rc = P.Rc
    back = Rc @ v3(0, 1, 0)
    up = Rc @ Z
    lft, rgt = P.sh[0], P.sh[1]
    attach = [lft + Rc @ v3(-1.7, 0.6, 3.5), lft + Rc @ v3(1.4, 1.3, 3.1), P.neck_cut + back * 3.0 + up * -0.6,
              rgt + Rc @ v3(-1.4, 1.3, 3.1), rgt + Rc @ v3(1.7, 0.6, 3.5)]
    pl = MC.cape_plan([[float(x) for x in a] for a in attach], length, _body_proxies(P), rows=rows, cols=cols, flare=flare,
                      wind=tuple(float(w) for w in wind), floor_z=floor_z, margin=margin, steps=steps,
                      back_hint=tuple(float(b) for b in back), collar_margin=-0.5)
    return pl


def cape(g, P, length=17.0, wind=(0.08, 0.3, 0.0), thickness=1.0, folds=True, rib_r=0.55, **kw):
    """Add the draped cape to the Sculpt g. Returns the plan (clearance / stretch checks)."""
    pl = plan(P, length, wind, **kw)
    G = np.array(pl["grid"], float)                       # rows x cols x 3
    rows, cols = G.shape[:2]
    half_t = thickness / 2
    for r in range(rows - 1):
        for c in range(cols):
            a, b = G[r, c], G[r + 1, c]
            seg = b - a
            if np.linalg.norm(seg) < 1e-6:
                continue
            cl, cr = G[r, max(c - 1, 0)], G[r, min(c + 1, cols - 1)]
            side = cr - cl
            n = np.cross(side, seg)
            n = unit(n) if np.linalg.norm(n) > 1e-6 else v3(0, 1, 0)
            if n @ v3(0, 1, 0) < 0:                       # outer face away from the body (the back is +y in the figure frame)
                n = -n
            R = frame(seg, n)
            L = float(np.linalg.norm(seg)) / 2 + 0.35
            half_w = float(np.linalg.norm(side)) / (4.0 if 0 < c < cols - 1 else 2.0) + 0.35
            mid = (a + b) / 2
            g.add(rbox(mid, (half_w, half_t, L), R, min(0.3, half_t)), 0.8)
            if folds and 0 < c < cols - 1 and c % 2 == 1:
                g.add(capsule(mid - R[:, 2] * L + R[:, 1] * (half_t - 0.05), mid + R[:, 2] * L + R[:, 1] * (half_t - 0.05), rib_r), 0.25)
    return pl
