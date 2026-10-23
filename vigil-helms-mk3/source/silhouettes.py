#!/usr/bin/env python3
"""Silhouette variety metric for a helm library (3dada measurement for the 'variety in silhouette' goal).

Each helm STL (helm frame: neck cut at z = 0, faces -y) is projected orthographically onto the front (x, z) and side
(y, z) planes and rasterised at 0.04 mm on a fixed canvas, everything above the neck seat (z > 0; the peg is common to
all and excluded). Reported per helm: silhouette areas, widths, heights; per pair: intersection-over-union of the
front and of the side masks. Distinctness of a helm = 1 - its highest IoU with any other helm of the set (front and
side averaged). Run: <sculpt python> source/silhouettes.py <out.json> <stl> [<stl> ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

PX = 0.04
BOX = {"front": ((-6.0, 6.0), (0.0, 11.0)), "side": ((-6.0, 6.0), (0.0, 11.0))}


def mask(m, view):
    (u0, u1), (v0, v1) = BOX[view]
    W, Hh = int((u1 - u0) / PX), int((v1 - v0) / PX)
    img = Image.new("1", (W, Hh), 0)
    d = ImageDraw.Draw(img)
    a = 0 if view == "front" else 1
    T = m.vertices[m.faces]
    U = (T[:, :, a] - u0) / PX
    V = (v1 - np.maximum(T[:, :, 2], 0.0)) / PX
    for i in range(len(T)):
        d.polygon([(U[i, 0], V[i, 0]), (U[i, 1], V[i, 1]), (U[i, 2], V[i, 2])], fill=1)
    M = np.array(img, bool)
    return M


def stats(M):
    ys, xs = np.nonzero(M)
    return {"area_mm2": round(M.sum() * PX * PX, 2), "width_mm": round((xs.max() - xs.min() + 1) * PX, 2),
            "height_mm": round((ys.max() - ys.min() + 1) * PX, 2)}


def iou(a, b):
    return float((a & b).sum() / max((a | b).sum(), 1))


def run(paths):
    names, masks, per = [], [], {}
    for p in paths:
        m = trimesh.load(p, process=False)
        f, s = mask(m, "front"), mask(m, "side")
        n = Path(p).stem
        names.append(n)
        masks.append((f, s))
        per[n] = {"front": stats(f), "side": stats(s)}
    N = len(names)
    F = np.zeros((N, N))
    S = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            F[i, j] = iou(masks[i][0], masks[j][0])
            S[i, j] = iou(masks[i][1], masks[j][1])
    A = (F + S) / 2
    np.fill_diagonal(A, 0)
    for i, n in enumerate(names):
        j = int(A[i].argmax())
        per[n]["closest"] = names[j]
        per[n]["max_mean_iou"] = round(float(A[i, j]), 3)
        per[n]["distinctness"] = round(1 - float(A[i, j]), 3)
    off = ~np.eye(N, dtype=bool)
    summary = {"helms": N, "pixel_mm": PX, "mean_pair_iou_front": round(float(F[off].mean()), 3),
               "mean_pair_iou_side": round(float(S[off].mean()), 3), "max_pair_iou_mean": round(float(A.max()), 3),
               "min_distinctness": round(1 - float(A.max()), 3),
               "mean_distinctness": round(float(np.mean([per[n]["distinctness"] for n in names])), 3)}
    return {"summary": summary, "helms": per, "iou_front": np.round(F, 3).tolist(), "iou_side": np.round(S, 3).tolist(),
            "names": names}


if __name__ == "__main__":
    out = run(sys.argv[2:])
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"]))
    for n, v in out["helms"].items():
        print(n, v["front"], v["side"], "closest", v["closest"], v["max_mean_iou"])
