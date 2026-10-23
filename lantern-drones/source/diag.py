#!/usr/bin/env python3
"""Memory-light local twin of the two ray screens in unified-CAD-MCP (miniature_gap_check and the wall part of
miniature_printability_check). Same sampling as the tools (every ceil(n/30000)-th triangle centroid) and the same
grid-limited short probe, vectorised per ray with numpy (no rtree / trimesh ray engine, which ran past a 1.5 GB cap
on 160k triangles):
  gap : outward ray, nearest surface facing back (dot < -0.2) within the gap limit (0.5 mm)
  thin: inward ray, nearest surface within the supported-wall limit (0.4 mm); split sheet (dot < -0.7) / crease
Prints narrow/thin areas (mm2) and the worst 0.5 mm cells. The MCP tools remain the evidence.
Usage: python diag.py [--gap 0.5] [--thin 0.4] a.stl [b.stl ...]"""
import json
import sys
from collections import defaultdict

import numpy as np
import trimesh


def grid_of(tri, h):
    lo = np.floor(tri.min(axis=1) / h).astype(int)
    hi = np.floor(tri.max(axis=1) / h).astype(int)
    g = defaultdict(list)
    for i in range(len(tri)):
        for a in range(lo[i, 0], hi[i, 0] + 1):
            for b in range(lo[i, 1], hi[i, 1] + 1):
                for c in range(lo[i, 2], hi[i, 2] + 1):
                    g[(a, b, c)].append(i)
    return {k: np.array(v) for k, v in g.items()}


def cast(tri, fn, grid, h, o, d, probe, self_i, facing):
    e = o + d * probe
    lo = np.floor(np.minimum(o, e) / h).astype(int)
    hi = np.floor(np.maximum(o, e) / h).astype(int)
    parts = [grid[k] for k in ((a, b, c) for a in range(lo[0], hi[0] + 1) for b in range(lo[1], hi[1] + 1)
                               for c in range(lo[2], hi[2] + 1)) if k in grid]
    if not parts:
        return np.inf, 1.0
    j = np.unique(np.concatenate(parts))
    j = j[j != self_i]
    A, B, C = tri[j, 0], tri[j, 1], tri[j, 2]
    e1, e2 = B - A, C - A
    p = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    t_ = o - A
    u = np.einsum('ij,ij->i', t_, p) * inv
    q = np.cross(t_, e1)
    v = (q @ d) * inv
    t = np.einsum('ij,ij->i', e2, q) * inv
    dots = fn[j] @ d * (-1 if facing else 1)
    hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 1e-6) & (t <= probe)
    if facing:
        hit &= (fn[j] @ d) < -0.2
    if not hit.any():
        return np.inf, 1.0
    k = np.argmin(np.where(hit, t, np.inf))
    return float(t[k]), float(fn[j[k]] @ d)


def cells_of(org, area, dist, sel):
    cells = {}
    for k in np.where(sel)[0]:
        key = tuple(np.round(org[k] / 0.5).astype(int))
        c = cells.setdefault(key, [0.0, 9.0, org[k]])
        c[0] += area[k]
        c[1] = min(c[1], dist[k])
    top = sorted(cells.values(), key=lambda c: -c[0])[:10]
    return [[round(float(c[0]), 3), round(float(c[1]), 3), [round(float(v), 2) for v in c[2]]] for c in top]


def diag(path, gap=0.5, thin=0.4, do=('gap', 'thin')):
    m = trimesh.load(path, process=False)
    tri = np.asarray(m.triangles, dtype=np.float64)
    fn = np.asarray(m.face_normals)
    n = len(tri)
    step = max(1, -(-n // 30000))
    idx = np.arange(0, n, step)
    idx = idx[m.area_faces[idx] > 0]
    org = tri[idx].mean(axis=1)
    area = m.area_faces[idx] * step
    out = {'file': str(path).split('/')[-1], 'tris': n}
    h = 0.5
    grid = grid_of(tri, h)
    if 'gap' in do:
        r = [cast(tri, fn, grid, h, org[k], fn[i], gap, i, True) for k, i in enumerate(idx)]
        d = np.array([x[0] for x in r])
        g = d < gap
        out['gap'] = {'area': round(float(area[g].sum()), 3), 'min': round(float(d[g].min()), 3) if g.any() else None,
                      'cells': cells_of(org, area, d, g)}
    if 'thin' in do:
        r = [cast(tri, fn, grid, h, org[k], -fn[i], 0.6, i, False) for k, i in enumerate(idx)]
        d = np.array([x[0] for x in r])
        dot = np.array([x[1] for x in r])       # hit normal . inward dir: > 0.7 means the far face points back out = sheet
        t = d < thin
        sheet = t & (dot > 0.7)
        out['thin'] = {'area': round(float(area[t].sum()), 3), 'sheet': round(float(area[sheet].sum()), 3),
                       'crease': round(float(area[t & ~sheet].sum()), 3), 'min': round(float(d[t].min()), 3) if t.any() else None,
                       'area_lt_0.6': round(float(area[d < 0.6].sum()), 3), 'cells': cells_of(org, area, d, t)}
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    kw = {}
    for k in ('gap', 'thin'):
        if '--' + k in a:
            i = a.index('--' + k)
            kw[k] = float(a[i + 1])
            del a[i:i + 2]
    for p in a:
        print(json.dumps(diag(p, **kw)), flush=True)
