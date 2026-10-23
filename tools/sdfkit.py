"""Signed-distance sculpting kit for the scifi-miniatures generators.

Why SDF: organic anatomy and armour that hugs it need smooth blends (muscle into muscle, plate edge over bodysuit),
which booleans of B-rep primitives cannot give. Every part is a sequence of sculpt operations on a dense distance grid
(smooth union, hard union, carve, plate = offset body clipped by planes), meshed with marching cubes, so each part is
watertight and one body by construction (asserted).

Frame (same as fantasy-miniatures): millimetres at print scale, z up, table at z = 0, the figure faces -y,
the figure's right hand is on -x.

Run with the sculpt venv (numpy, scikit-image, trimesh, manifold3d, pillow):
    /mnt/d/ai-stack/venvs/scifi-sculpt/bin/python <mini>/source/build.py
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import manifold3d
import numpy as np
import trimesh
from skimage.measure import marching_cubes

F = np.float32
FREECAD_PYTHON = "/mnt/d/ai-stack/bin/freecad-python"


# ---------------------------------------------------------------- vector helpers
def v3(*a):
    return np.array(a[0] if len(a) == 1 else a, dtype=np.float64)


def unit(a):
    a = v3(a)
    return a / np.linalg.norm(a)


def frame(axis, fwd=(0, -1, 0)):
    """Orthonormal frame (columns u, w, n): n along axis, w = the part of fwd normal to it, u = w x n (side)."""
    n = unit(axis)
    w = v3(fwd) - n * np.dot(fwd, n)
    if np.linalg.norm(w) < 1e-6:
        w = v3(0, 0, 1) - n * n[2]
    w = unit(w)
    u = np.cross(w, n)
    return np.stack([u, w, n], axis=1)


def rot(axis, deg):
    a = unit(axis)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


# ---------------------------------------------------------------- primitives: f(P[N,3]) -> d[N], plus a bbox
class Shape:
    def __init__(self, f, lo, hi):
        self.f, self.lo, self.hi = f, v3(lo), v3(hi)

    def __call__(self, P):
        return self.f(P)

    def __or__(self, o):
        return Shape(lambda P: np.minimum(self(P), o(P)), np.minimum(self.lo, o.lo), np.maximum(self.hi, o.hi))

    def __and__(self, o):
        return Shape(lambda P: np.maximum(self(P), o(P)), np.maximum(self.lo, o.lo), np.minimum(self.hi, o.hi))

    def __sub__(self, o):
        return Shape(lambda P: np.maximum(self(P), -o(P)), self.lo, self.hi)

    def smooth(self, o, k):
        return Shape(lambda P: smin(self(P), o(P), k), np.minimum(self.lo, o.lo) - k, np.maximum(self.hi, o.hi) + k)

    def offset(self, t):
        """Grow (t > 0) or shrink the surface by t: the plate trick (offset body, then clip)."""
        return Shape(lambda P: self(P) - t, self.lo - max(t, 0), self.hi + max(t, 0))

    def clip(self, *halfspaces):
        """Intersect with unbounded half-spaces, keeping this shape's bbox."""
        fs = [self] + list(halfspaces)
        return Shape(lambda P: np.max(np.stack([g(P) for g in fs]), axis=0), self.lo, self.hi)

    def moved(self, M):
        """Rigid transform by a 4x4 matrix."""
        M = np.asarray(M, dtype=np.float64)
        Ri, t = M[:3, :3].T, M[:3, 3]
        c = np.array([[x, y, z] for x in (self.lo[0], self.hi[0]) for y in (self.lo[1], self.hi[1]) for z in (self.lo[2], self.hi[2])])
        c = c @ M[:3, :3].T + t
        return Shape(lambda P: self((P - t) @ Ri.T), c.min(axis=0), c.max(axis=0))


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def sphere(c, r):
    c = v3(c)
    return Shape(lambda P: np.linalg.norm(P - c, axis=1) - r, c - r, c + r)


def round_cone(a, b, ra, rb):
    """Capsule with different end radii (Inigo Quilez sdRoundCone, arbitrary end points)."""
    a, b = v3(a), v3(b)
    ba = b - a
    l2 = float(ba @ ba)
    rr = ra - rb
    a2 = l2 - rr * rr
    il2 = 1.0 / l2

    def f(P):
        pa = P - a
        y = pa @ ba
        z = y - l2
        x2 = np.sum((pa * l2 - np.outer(y, ba)) ** 2, axis=1)
        y2, z2 = y * y * l2, z * z * l2
        k = math.copysign(1, rr) * rr * rr * x2
        d_mid = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - ra
        d_b = np.sqrt(x2 + z2) * il2 - rb
        d_a = np.sqrt(x2 + y2) * il2 - ra
        return np.where(np.sign(z) * a2 * z2 > k, d_b, np.where(np.sign(y) * a2 * y2 < k, d_a, d_mid))

    r = max(ra, rb)
    return Shape(f, np.minimum(a, b) - r, np.maximum(a, b) + r)


def capsule(a, b, r):
    return round_cone(a, b, r, r)


def _local(c, R):
    c, R = v3(c), np.asarray(R, dtype=np.float64)
    return lambda P: (P - c) @ R


def ellipsoid(c, radii, R=np.eye(3)):
    """Ellipsoid with semi-axes along the columns of R (iq bound approximation, good near the surface)."""
    r = v3(radii)
    loc = _local(c, R)

    def f(P):
        q = loc(P)
        k0 = np.linalg.norm(q / r, axis=1)
        k1 = np.linalg.norm(q / (r * r), axis=1)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)

    e = np.abs(np.asarray(R)) @ r
    return Shape(f, v3(c) - e, v3(c) + e)


def rbox(c, half, R=np.eye(3), r=0.0):
    """Rounded box: half extents along the columns of R, edge radius r (included in half)."""
    h = v3(half) - r
    loc = _local(c, R)

    def f(P):
        q = np.abs(loc(P)) - h
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - r

    e = np.abs(np.asarray(R)) @ v3(half)
    return Shape(f, v3(c) - e, v3(c) + e)


def cyl(a, b, r, edge=0.0):
    """Capped cylinder between points a and b with a rounded edge."""
    a, b = v3(a), v3(b)
    ax = b - a
    L = float(np.linalg.norm(ax))
    n = ax / L
    e = min(edge, r * 0.9, L / 2 * 0.9)

    def f(P):
        pa = P - a
        y = pa @ n
        x = np.linalg.norm(pa - np.outer(y, n), axis=1)
        dx, dy = x - (r - e), np.abs(y - L / 2) - (L / 2 - e)
        return np.minimum(np.maximum(dx, dy), 0) + np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) - e

    return Shape(f, np.minimum(a, b) - r, np.maximum(a, b) + r)


def torus(c, axis, R_, r):
    c = v3(c)
    n = unit(axis)

    def f(P):
        q = P - c
        y = q @ n
        x = np.linalg.norm(q - np.outer(y, n), axis=1) - R_
        return np.hypot(x, y) - r

    e = R_ + r
    return Shape(f, c - e, c + e)


def half(p, n):
    """Half-space {x : (x - p) . n <= 0} (solid on the side opposite n)."""
    p, n = v3(p), unit(n)
    return Shape(lambda P: (P - p) @ n, (-1e3,) * 3, (1e3,) * 3)


def tube(points, r0, r1=None):
    """Swept tube through a polyline (cables, hoses): union of round cones."""
    r1 = r0 if r1 is None else r1
    pts = [v3(p) for p in points]
    n = len(pts) - 1
    s = None
    for i in range(n):
        seg = round_cone(pts[i], pts[i + 1], r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n)
        s = seg if s is None else s | seg
    return s


def bezier(p0, p1, p2, p3, n=10):
    p0, p1, p2, p3 = map(v3, (p0, p1, p2, p3))
    return [(1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3 for t in np.linspace(0, 1, n)]


def d_peg(base, axis, d, length, flat_frac=0.3, key=(0, -1, 0), chamfer=0.2, grow=0.0):
    """D-flat peg (or its socket cutter, grow = clearance per side) from base along axis; the flat faces key.
    Sizes from miniature_base_and_peg: flat at 0.3 d from the axis; the socket adds the fit clearance per side."""
    base, n = v3(base), unit(axis)
    R = frame(n, key)
    w = R[:, 1]
    body = cyl(base, base + n * length, d / 2 + grow, chamfer if grow == 0 else 0.0)
    return body.clip(half(base + w * (flat_frac * d + grow), w))


# ---------------------------------------------------------------- the grid
class Sculpt:
    """Dense distance grid over a bbox. Operations touch only the voxels inside the operand's padded bbox."""

    def __init__(self, lo, hi, h=0.07):
        self.h = h
        self.lo = v3(lo) - 3 * h - 0.3137 * h  # keep modelled planes (z = 0 seats) off grid nodes: no zero-area MC faces
        self.n = np.ceil((v3(hi) + 3 * h - self.lo) / h).astype(int) + 1
        self.D = np.full(tuple(self.n), 5.0, dtype=F)

    def _block(self, s, pad):
        i0 = np.clip(np.floor((s.lo - pad - self.lo) / self.h).astype(int), 0, self.n - 1)
        i1 = np.clip(np.ceil((s.hi + pad - self.lo) / self.h).astype(int) + 1, 0, self.n)
        if np.any(i1 <= i0):
            return None, None
        ax = [self.lo[k] + self.h * np.arange(i0[k], i1[k]) for k in range(3)]
        X, Y, Z = np.meshgrid(*ax, indexing="ij")
        P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
        return tuple(slice(i0[k], i1[k]) for k in range(3)), P

    def _apply(self, s, op, k=0.0):
        sl, P = self._block(s, 3 * self.h + 2 * k + 0.3)
        if sl is None:
            return self
        cur = self.D[sl]
        d = s(P).reshape(cur.shape).astype(F)
        if op == "add":
            self.D[sl] = np.minimum(cur, d) if k == 0 else smin(cur, d, F(k))
        else:  # carve
            self.D[sl] = np.maximum(cur, -d) if k == 0 else -smin(-cur, d, F(k))
        return self

    def add(self, s, k=0.0):
        return self._apply(s, "add", k)

    def cut(self, s, k=0.0):
        return self._apply(s, "cut", k)

    def mesh(self, name, target_tris=None, dust_mm3=0.05):
        """Marching cubes -> one closed, manifold, outward-wound body (asserted), optionally simplified (manifold3d)."""
        D = self.D.copy()
        D[[0, -1], :, :] = 5.0
        D[:, [0, -1], :] = 5.0
        D[:, :, [0, -1]] = 5.0
        # no field value at (or within 2 um of) zero on a node: MC would make zero-area faces that welding opens up
        D = np.where(np.abs(D) < 2e-3, np.where(D < 0, F(-2e-3), F(2e-3)), D)
        v, f, _, _ = marching_cubes(D, 0.0, spacing=(self.h,) * 3, method="lewiner")
        m = trimesh.Trimesh(v + self.lo, f, process=False)
        m = largest_body(m, name, dust_mm3)
        if target_tris and len(m.faces) > target_tris:
            m = decimate(m, target_tris, name, dust_mm3)
        trimesh.repair.fix_normals(m)
        st = mesh_stats(m)
        if not (st["watertight"] and st["non_manifold_edges"] == 0 and st["bodies"] == 1 and m.volume > 0):
            raise SystemExit(f"{name}: mesh not one closed manifold body: {st}")
        return m


def mesh_stats(m):
    u, c = np.unique(m.edges_sorted, axis=0, return_counts=True)
    return {"triangles": len(m.faces), "watertight": bool(m.is_watertight), "open_edges": int((c == 1).sum()),
            "non_manifold_edges": int((c > 2).sum()), "degenerate": int((m.area_faces < 1e-9).sum()),
            "bodies": len(m.split(only_watertight=False))}


def largest_body(m, name, dust_mm3=0.05):
    parts = m.split(only_watertight=False)
    if len(parts) == 1:
        return m
    keep = max(parts, key=lambda p: abs(p.volume))
    junk = sorted(round(abs(p.volume), 4) for p in parts if p is not keep)
    if max(junk) > dust_mm3:
        raise SystemExit(f"{name}: {len(parts)} bodies, stray volumes {junk[-5:]} mm3 (a piece is not joined)")
    return keep  # sub-voxel dust


def decimate(m, n, name="mesh", dust_mm3=0.05, coarse=False):
    """Manifold-preserving simplification (manifold3d Manifold.simplify, a tolerance in mm): pick the smallest
    tolerance that brings the mesh to <= n triangles. Quadric decimation (fast-simplification) pinched non-manifold
    edges on these sculpts; Manifold keeps the result closed and manifold by construction. coarse=True allows
    tolerances up to 0.4 mm, for reference exports only (faceted STEP), never for print or viewer meshes."""
    if len(m.faces) <= n:
        return m
    M = manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                                            tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    if M.status() != manifold3d.Error.NoError:
        raise SystemExit(f"{name}: not a manifold input ({M.status()})")
    tols = (0.002, 0.003, 0.004, 0.005, 0.006, 0.008, 0.01, 0.013, 0.017, 0.022, 0.03, 0.04, 0.055, 0.075, 0.1, 0.14)
    for tol in tols + ((0.2, 0.28, 0.4) if coarse else ()):
        S = M.simplify(tol)
        if S.num_tri() <= n:
            break
    out = S.to_mesh()
    d = trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts), process=False)
    d.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(d)
    d.metadata["simplify_tol_mm"] = tol
    return d


# ---------------------------------------------------------------- package writer
class Package:
    def __init__(self, mid, pkg):
        self.id, self.pkg = mid, Path(pkg)
        self.parts = []

    def add(self, name, mesh, *, stl, color, group, note, explode=(0, 0, 0), placement=None):
        """placement: 4x4 matrix (or None) that puts the as-modelled part into the assembly (viewer, STEP)."""
        if not mesh.is_watertight:
            raise SystemExit(f"{name}: not watertight")
        self.parts.append(dict(name=name, mesh=mesh, stl=stl, color=color, group=group, note=note, explode=list(explode),
                               placement=placement))

    def write(self, viewer_tris=26_000, step_tris=5_000):
        up = self.pkg / "build" / "upright"
        for d in (up, self.pkg / "cad", self.pkg / "viewer", self.pkg / "reports"):
            d.mkdir(parents=True, exist_ok=True)
        rows, viewer, step_parts, done = {}, [], [], set()
        for p in self.parts:
            m = p["mesh"]
            if p["stl"] not in done:
                m.export(up / f"{p['stl']}.stl")
                bb = m.bounds
                rows[p["stl"]] = {"volume_mm3": round(float(m.volume), 2), "bodies": len(m.split(only_watertight=False)),
                                  "watertight": bool(m.is_watertight), "bbox_mm": [round(float(x), 2) for x in bb[1] - bb[0]],
                                  "triangles": len(m.faces), "instances": 0}
                done.add(p["stl"])
            rows[p["stl"]]["instances"] += 1
            a = m.copy()
            if p["placement"] is not None:
                a.apply_transform(p["placement"])
            p["asm"] = a
            vm = decimate(a, viewer_tris)
            viewer.append({"name": p["name"], "group": p["group"], "color": p["color"], "note": p["note"], "explode": p["explode"],
                           "printStl": f"print/stl/{p['stl']}.stl",
                           "vertices": np.round(vm.vertices, 3).tolist(), "triangles": vm.faces.tolist()})
            sm = decimate(a, step_tris, coarse=True)
            step_parts.append({"name": p["name"], "vertices": sm.vertices.tolist(), "faces": sm.faces.tolist()})
        (self.pkg / "viewer" / f"{self.id}.parts.json").write_text(json.dumps(viewer, separators=(",", ":")))
        step = self.pkg / "cad" / f"{self.id}-assembly.step"
        write_step(step, step_parts)
        interference = []
        for i in range(len(self.parts)):
            for j in range(i + 1, len(self.parts)):
                v = overlap_volume(self.parts[i]["asm"], self.parts[j]["asm"])
                if v > 0.02:
                    interference.append({"a": self.parts[i]["name"], "b": self.parts[j]["name"], "overlap_mm3": round(v, 3)})
        allv = np.vstack([p["asm"].vertices for p in self.parts])
        ext = allv.max(axis=0) - allv.min(axis=0)
        report = {"id": self.id, "generator": "source/build.py (tools/sdfkit.py: SDF sculpt, marching cubes, manifold3d simplification)",
                  "assembled_bbox_mm": [round(float(x), 2) for x in ext], "parts": rows, "interference": interference,
                  "step": {"file": f"cad/{step.name}", "kind": f"faceted B-rep reference (about {step_tris} triangles per part) written by FreeCAD"}}
        (self.pkg / "reports" / "build.json").write_text(json.dumps(report, indent=1))
        print(json.dumps({"id": self.id, "parts": {k: (v["volume_mm3"], v["bbox_mm"], v["triangles"]) for k, v in rows.items()},
                          "assembled_bbox_mm": report["assembled_bbox_mm"], "interference": interference}, indent=1))
        return report


def to_manifold(m):
    return manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                                               tri_verts=np.asarray(m.faces, dtype=np.uint32)))


def overlap_volume(a, b):
    """Interference between two closed meshes: exact volume of their boolean intersection (manifold3d)."""
    lo, hi = np.maximum(a.bounds[0], b.bounds[0]), np.minimum(a.bounds[1], b.bounds[1])
    if np.any(hi <= lo):
        return 0.0
    return float((to_manifold(a) ^ to_manifold(b)).volume())


def write_step(path, parts):
    """Faceted STEP (one solid per part) through FreeCAD: mesh topology -> shell -> solid -> compound."""
    tmp = Path(path).with_suffix(".tmp.json")
    tmp.write_text(json.dumps(parts))
    code = f"""
import json, FreeCAD, Part
parts = json.load(open({str(tmp)!r}))
solids = []
for p in parts:
    sh = Part.Shape()
    sh.makeShapeFromMesh(([tuple(v) for v in p['vertices']], [tuple(f) for f in p['faces']]), 0.01)
    shell = Part.makeShell(sh.Faces)
    assert shell.isClosed(), p['name']  # faceted reference: a coarse copy may self-touch, so OCC isValid() is not required
    s = Part.makeSolid(shell)
    assert abs(s.Volume) > 0, p['name']
    solids.append(s)
Part.makeCompound(solids).exportStep({str(path)!r})
print('step ok', len(solids))
"""
    r = subprocess.run([FREECAD_PYTHON, "-c", code], capture_output=True, text=True, timeout=3600)
    tmp.unlink(missing_ok=True)
    if "step ok" not in r.stdout:
        raise SystemExit(f"STEP export failed: {r.stdout[-800:]} {r.stderr[-800:]}")


def translate(x, y, z):
    T = np.eye(4)
    T[:3, 3] = (x, y, z)
    return T
