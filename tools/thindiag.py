#!/usr/bin/env python3
"""Diagnose miniature_printability_check thin-wall hits: replicate its centroid inward-ray sampling (every
ceil(n/30000)-th triangle, area*step weight, probe 0.9 mm) with trimesh rays and classify every hit < 0.4 mm by
what the ray struck: 'sheet' (opposing face, dot < -0.7: a real thin wall) or 'crease' (dot >= -0.7: knife edge,
acute lip or fold). Usage: python thindiag.py a.stl [b.stl ...]"""
import sys
import json
import numpy as np
import trimesh


def diag(path, probe=0.9, lim=0.4):
    m = trimesh.load(path, process=False)
    n = len(m.faces)
    step = max(1, -(-n // 30000))
    idx = np.arange(0, n, step)
    idx = idx[m.area_faces[idx] > 0]
    nrm = m.face_normals[idx]
    org = m.triangles_center[idx]
    tri_id, ray_id, loc = m.ray.intersects_id(org, -nrm, multiple_hits=True, return_locations=True)
    d = np.einsum('ij,ij->i', loc - org[ray_id], -nrm[ray_id])
    keep = (tri_id != idx[ray_id]) & (d > 1e-6)
    tri_id, ray_id, d = tri_id[keep], ray_id[keep], d[keep]
    best = np.full(len(idx), np.inf)
    hit = np.full(len(idx), -1)
    order = np.argsort(-d)
    best[ray_id[order]] = d[order]
    hit[ray_id[order]] = tri_id[order]
    thin = np.where(best < lim)[0]
    area = m.area_faces[idx[thin]] * step
    dots = np.einsum('ij,ij->i', nrm[thin], m.face_normals[hit[thin]])
    fv = m.faces
    adj = np.array([len(set(fv[idx[t]]) & set(fv[hit[t]])) > 0 for t in thin], bool)
    cls = np.where(dots < -0.7, 'sheet', 'crease')
    bd = best[thin]
    out = {'file': str(path).split('/')[-1], 'tris': n, 'step': step, 'thin_area': round(float(area.sum()), 3)}
    for c in ('sheet', 'crease'):
        s = cls == c
        out[c] = {'area': round(float(area[s].sum()), 3), 'n': int(s.sum()), 'adjacent': int((adj & s).sum()),
                  'median_d': round(float(np.median(bd[s])), 3) if s.any() else None}
    out['bands'] = {b: round(float(area[(bd >= lo) & (bd < hi)].sum()), 3)
                    for b, lo, hi in (('<0.05', 0, .05), ('0.05-0.2', .05, .2), ('0.2-0.4', .2, .4))}
    cells = {}
    for k, t in enumerate(thin):
        key = tuple(np.round(org[t] / 0.5).astype(int))
        c = cells.setdefault(key, [0.0, 9.0, org[t], {}])
        c[0] += area[k]
        c[3][cls[k]] = c[3].get(cls[k], 0) + 1
        c[1] = min(c[1], bd[k])
    top = sorted(cells.values(), key=lambda c: -c[0])[:8]
    out['spots'] = [(round(float(c[0]), 3), round(float(c[1]), 3), np.round(c[2], 2).tolist(), c[3]) for c in top]
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(diag(p)), flush=True)
