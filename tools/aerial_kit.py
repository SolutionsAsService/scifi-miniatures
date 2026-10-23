"""Aerial kit helpers for the scifi-miniatures SDF generators (rotors, plates, flight stems, raked stem bases).

Built for vigil-aerial-drones (2026-10-14); reusable by any package that sculpts airframes on tools/sdfkit.py.
Frame (as sdfkit): millimetres at print scale, z up, parts face -y (left side on +x).

What lives here
- Ops: an ordered add / cut list that is sculpted onto one grid at a chosen pitch (re-meshable without re-authoring).
- poly_sdf / plate: exact 2D polygon distance extruded to a rounded slab in any plane (fins, blades, stabilisers,
  winglets, launcher cheeks). Thickness may be a function of the in-plane coordinates (tapered blades).
- blade / prop: an n-blade rotor / propeller (pitch, taper, swept tip) built from plates.
- scaled: anisotropic scaling of a Shape (elliptic pods from round cones); distance is rescaled by the smallest factor,
  which keeps the field conservative (never over-estimates), so smooth unions stay well behaved.
- chain: smooth union of round cones through stations (teardrop pods, cigar fuselages, booms).
- split_chevron_cuts: the Vigil split-chevron lens pair (two bars canted +-a), cut into a sensor face.
- base_body / deck_seams / magnet_pocket / launch_pad: round base with bevel, chevron deck seams, vented magnet pocket
  and a raked flight-stem launch pad.
- flight_stem: a printed round stem the size of a clear acrylic rod (same sockets).
- mesh_in_budget: mesh at a pitch, re-mesh coarser if over the checker triangle budget. Never decimates.
"""
from __future__ import annotations

import math

import numpy as np

from sdfkit import Sculpt, Shape, cyl, rbox, rot, round_cone, smin, unit, v3

I3 = np.eye(3)


# ------------------------------------------------------------------------------------------------ op lists
class Ops:
    """Ordered add / cut operations (k = smooth-blend radius in mm)."""

    def __init__(self):
        self.ops = []

    def add(self, s, k=0.0):
        self.ops.append(("add", s, k))
        return s

    def cut(self, s, k=0.0):
        self.ops.append(("cut", s, k))
        return s

    def bounds(self):
        adds = [s for o, s, _ in self.ops if o == "add"]
        return np.min([s.lo for s in adds], axis=0), np.max([s.hi for s in adds], axis=0)

    def sculpt(self, h, pad=0.4):
        lo, hi = self.bounds()
        g = Sculpt(lo - pad, hi + pad, h)
        for o, s, k in self.ops:
            (g.add if o == "add" else g.cut)(s, k)
        return g


def mat(R=I3, t=(0, 0, 0)):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    return M


def along(a, b, hw, hh, r=0.2, ext=0.0, up=(0, 0, 1)):
    """Rounded bar from a to b: hw half width (sideways), hh half height (toward 'up')."""
    a, b = v3(a), v3(b)
    d = b - a
    L = float(np.linalg.norm(d))
    n = d / L
    upv = unit(v3(up) - n * float(np.dot(up, n)))
    u = np.cross(n, upv)
    return rbox((a + b) / 2, (hw, L / 2 + ext, hh), np.stack([u, n, upv], axis=1), r)


def mesh_in_budget(ops, name, h0, budget=250_000, limit=290_000):
    """Mesh at pitch h0; if the marched mesh is over the budget, re-mesh the field coarser (triangles ~ 1 / pitch^2,
    the miniature_mesh_budget rule). The print mesh is never decimated (QEM decimation folds SDF meshes)."""
    h = h0
    for _ in range(3):
        m = ops.sculpt(h).mesh(name)
        if len(m.faces) <= limit:
            m.metadata["pitch_mm"] = h
            return m
        h = round(h * math.sqrt(len(m.faces) / budget) * 1.01, 4)
        print(f"{name}: {len(m.faces)} triangles over budget, re-meshing at {h} mm", flush=True)
    raise SystemExit(f"{name}: could not reach the triangle budget")


# ------------------------------------------------------------------------------------------------ 2D polygons, plates
def poly_sdf(q, V):
    """Signed distance from points q (N, 2) to the closed polygon V (M, 2) (negative inside; any winding)."""
    V = np.asarray(V, dtype=np.float64)
    d = np.full(len(q), np.inf)
    s = np.ones(len(q))
    j = len(V) - 1
    for i in range(len(V)):
        e = V[j] - V[i]
        w = q - V[i]
        t = np.clip((w @ e) / (e @ e), 0, 1)
        b = w - np.outer(t, e)
        d = np.minimum(d, np.einsum("ij,ij->i", b, b))
        c1 = q[:, 1] >= V[i, 1]
        c2 = q[:, 1] < V[j, 1]
        c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
        j = i
    return s * np.sqrt(d)


def plate(origin, u, v, poly, thick, r=0.2):
    """Rounded slab: the polygon poly (in-plane coordinates a along u, b along v) extruded +-thick/2 along n = u x v.
    thick may be a number or f(a, b) -> full thickness (arrays in, array out). Edge radius r (<= 0.49 thick)."""
    o, u = v3(origin), unit(u)
    v = unit(v3(v) - u * float(u @ v3(v)))
    n = np.cross(u, v)
    V = np.asarray(poly, dtype=np.float64)
    if np.isscalar(thick):
        tmax = tmin = float(thick)
    else:
        tv = np.asarray(thick(V[:, 0], V[:, 1]), dtype=np.float64)
        tmax, tmin = float(tv.max()), float(tv.min())
    r = min(r, 0.49 * tmin)

    def f(P):
        w = P - o
        a, b, c = w @ u, w @ v, w @ n
        d2 = poly_sdf(np.stack([a, b], axis=1), V)
        t = thick if np.isscalar(thick) else thick(a, b)
        dz = np.abs(c) - t / 2
        q0, q1 = d2 + r, dz + r
        return np.hypot(np.maximum(q0, 0), np.maximum(q1, 0)) + np.minimum(np.maximum(q0, q1), 0) - r

    C = np.array([o + u * a + v * b + n * s * tmax / 2 for a, b in V for s in (-1, 1)])
    return Shape(f, C.min(axis=0) - 0.05, C.max(axis=0) + 0.05)


def blade(hub, e, axis, r0, r1, chord0, chord1, thick, pitch_deg=0.0, sweep_tip=0.0, r=0.25):
    """One rotor blade from radius r0 to r1 along e (normal to axis), chord chord0 -> chord1, pitched pitch_deg about
    e; sweep_tip (mm) rakes the leading-edge tip back. Keep thick >= 0.8 mm for resin blades."""
    e = unit(e)
    ax = unit(axis)
    w = rot(e, pitch_deg) @ np.cross(ax, e)          # chord direction (leading edge on -w)
    c0, c1 = chord0 / 2, chord1 / 2
    poly = [(r0, -c0), (r1 - sweep_tip, -c1), (r1, -c1 + sweep_tip * 0.6), (r1, c1), (r0, c0)]
    return plate(v3(hub), e, w, poly, thick, r)


def prop(o, hub, axis, radius, n=2, chord0=1.3, chord1=1.0, thick=0.84, phase_deg=0.0, pitch_deg=10.0, r0=0.4,
         sweep_tip=0.35, k=0.15, ref=None):
    """Add an n-blade prop about axis through hub (blade 0 along ref projected normal to the axis, then rotated by
    phase_deg); the hub itself is added by the caller."""
    ax = unit(axis)
    if ref is None:
        ref = v3(1, 0, 0) if abs(ax[0]) < 0.9 else v3(0, 1, 0)
    e0 = unit(v3(ref) - ax * float(v3(ref) @ ax))
    for i in range(n):
        e = rot(ax, phase_deg + 360.0 * i / n) @ e0
        o.add(blade(hub, e, ax, r0, radius, chord0, chord1, thick, pitch_deg, sweep_tip), k)


def scaled(s, sx=1.0, sy=1.0, sz=1.0):
    """Anisotropic scale of a Shape about the origin (conservative distance: scaled by the smallest factor)."""
    sc = v3(sx, sy, sz)
    m = float(sc.min())
    return Shape(lambda P: s(P / sc) * m, s.lo * sc, s.hi * sc)


def chain(pts, smooth=0.0):
    """Union of round cones through stations [(point, radius), ...] (smooth union radius smooth)."""
    segs = [round_cone(pts[i][0], pts[i + 1][0], pts[i][1], pts[i + 1][1]) for i in range(len(pts) - 1)]
    lo = np.min([g.lo for g in segs], axis=0) - smooth
    hi = np.max([g.hi for g in segs], axis=0) + smooth

    def f(P):
        d = segs[0](P)
        for g in segs[1:]:
            d = smin(d, g(P), smooth) if smooth > 0 else np.minimum(d, g(P))
        return d
    return Shape(f, lo, hi)


# ------------------------------------------------------------------------------------------------ Vigil language
def split_chevron_cuts(o, centre, fwd, up=(0, 0, 1), spread=0.48, bar=(0.5, 0.45, 0.22), cant=28.0):
    """Cut the Vigil split-chevron lens pair into a sensor face at centre (on the surface), facing fwd: two bars
    (half sizes: length across, depth into the face along fwd, width; 0.44 mm wide engravings) canted +-cant."""
    f = unit(fwd)
    upv = unit(v3(up) - f * float(f @ v3(up)))
    side = np.cross(f, upv)
    R0 = np.stack([side, f, upv], axis=1)
    for s in (-1, 1):
        R = rot(f, s * cant) @ R0
        o.cut(rbox(v3(centre) + side * s * spread, bar, R, 0.06))


# ------------------------------------------------------------------------------------------------ stems and bases
def stem_dir(rake_deg):
    """Direction of a stem raked rake_deg from vertical, leaning toward -y (the model's front): an airframe on a
    perpendicular socket pitches nose-down by the same angle (forward-flight / dive attitude)."""
    a = math.radians(rake_deg)
    return v3(0, -math.sin(a), math.cos(a))


def flight_stem(d, length, edge=0.2):
    """Printed round flight stem along z (bottom at z = 0); a clear acrylic rod of the same diameter fits the sockets."""
    o = Ops()
    o.add(cyl(v3(0, 0, 0), v3(0, 0, length), d / 2, edge))
    return o


def base_body(o, d, h, inset):
    """Bevelled round base body (top smaller by inset all round), z 0..h."""
    R0 = d / 2
    k = inset / h

    def body(Q):
        rr = np.hypot(Q[:, 0], Q[:, 1])
        side = (rr - (R0 - k * np.clip(Q[:, 2], 0, h))) / math.sqrt(1 + k * k)
        return np.maximum(side, np.maximum(-Q[:, 2], Q[:, 2] - h))
    o.add(Shape(body, (-R0, -R0, 0), (R0, R0, h)))


def deck_seams(o, d, h, inset, pitch=7.0, keep_out=4.0, w=0.45, depth=0.35, angle=35.0, rim=1.5, clear=()):
    """Chevron deck-plate pattern on a base top: two families of engraved seams (w x depth, >= 0.4 mm resin), stopped
    rim inside the rim and outside keep_out; clear = [(x, y, r)] discs left untouched (pads, feet, sockets)."""
    R0 = d / 2
    rr_out = R0 - inset - rim

    def ring(Q):
        rho = np.hypot(Q[:, 0], Q[:, 1])
        dd = np.maximum(rho - rr_out, keep_out - rho)
        for (cx, cy, cr) in clear:
            dd = np.maximum(dd, cr - np.hypot(Q[:, 0] - cx, Q[:, 1] - cy))
        return dd
    ringS = Shape(ring, (-R0, -R0, 0), (R0, R0, h + 1))
    for ang in (angle, -angle):
        n = v3(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)
        for t in np.arange(-R0 + pitch / 2, R0, pitch):
            seam = Shape(lambda Q, n=n, t=t: np.maximum(np.abs(Q @ n - t) - w / 2, h - depth - Q[:, 2]),
                         (-R0, -R0, h - depth - 0.3), (R0, R0, h + 0.6))
            o.cut(seam.clip(ringS))


def magnet_pocket(o, pocket_d, pocket_depth, vent_w, vent_d, R0, vent_dir=(-1.0, 0.0)):
    """Underside magnet pocket (5x2 magnet: 5.2 x 2.1 glue fit) with a vent groove out to the rim, so the pocket is
    never a sealed suction cup in any print pose."""
    o.cut(cyl(v3(0, 0, -1), v3(0, 0, pocket_depth), pocket_d / 2))
    dx, dy = vent_dir
    c = v3(dx * R0 / 2, dy * R0 / 2, 0)
    R = np.stack([v3(dy, -dx, 0), v3(dx, dy, 0), v3(0, 0, 1)], axis=1)
    o.cut(rbox(c, (vent_w / 2, R0 / 2 + 1, vent_d), R, 0.0))


def launch_pad(o, xy, h0, pad_r, pad_h, rake_deg, socket_d, socket_depth, ring=True):
    """Raised launch pad with a raked round stem socket (glue fit for the printed stem or a clear rod). Returns the
    socket mouth point and the stem direction."""
    x, y = xy
    top = h0 + pad_h
    o.add(cyl(v3(x, y, h0 - 0.3), v3(x, y, top), pad_r, 0.5), 0.3)
    lift = 0.0
    if ring:
        o.add(cyl(v3(x, y, top - 0.2), v3(x, y, top + 0.15), pad_r - 0.7, 0.1), 0.05)
        lift = 0.15
    u = stem_dir(rake_deg)
    p = v3(x, y, top + lift)
    o.cut(cyl(p + u * 1.0, p - u * socket_depth, socket_d / 2))
    return p, u
