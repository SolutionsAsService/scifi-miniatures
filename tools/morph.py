"""Morphological print-safety filter for sdfkit.Sculpt grids (closing then opening on the voxel field).

Why: miniature_printability_check measures wall thickness by inward rays from every triangle centroid and fails a part
when > 0.5 mm2 of surface is thinner than 0.4 mm (MSLA); miniature_gap_check casts outward rays and fails > 1.0 mm2 of
surface facing another within 0.5 mm. Hand-fixing knife lips, slivers, crease folds and hairline slots one by one
does not converge on SDF sculpts (dozens of boolean seams). A morphological opening with radius r removes every
feature that cannot hold a ball of radius r (so local wall >= 2r) and rounds convex edges to radius r; a closing with
radius c fills every slot narrower than 2c and fillets inside corners to radius c. Concave (engraved) detail wider
than 2c and convex detail thicker than 2r survive unchanged.

Implementation: exact Euclidean distance transforms (scipy.ndimage.distance_transform_edt) on the inside mask; the
result is intersected / united with the original field so untouched surfaces keep their sub-voxel smoothness.
Memory ~ 40 bytes per voxel (float64 EDT + int32 feature transform); a 0.05 mm helm grid (6 M voxels) needs ~250 MB.
"""
import math

import numpy as np
from scipy.ndimage import distance_transform_edt as edt


def _dist(mask, h):
    """Distance (mm) from each voxel of mask to the nearest voxel not in mask (0 outside mask)."""
    return (edt(mask) * h).astype(np.float32)


def close_field(D, h, c):
    """Closing: dilate by c, erode by c. Returns a field <= D (adds material only in slots/inside corners)."""
    if c <= 0:
        return D
    out = D >= 0
    dil_out = _dist(out, h) > c + 0.5 * h          # voxels still outside after dilation by c
    g = _dist(~dil_out, h)                          # distance to the dilated-outside set
    del dil_out
    closed = -(g - c)                               # inside the closed set where g > c
    return np.minimum(D, closed.astype(D.dtype))


def open_field(D, h, r):
    """Opening: erode by r, dilate by r. Returns a field >= D (removes material that cannot hold a ball of radius r)."""
    if r <= 0:
        return D
    ins = D < 0
    ero = _dist(ins, h) > r + 0.5 * h               # ball centres whose r-ball fits inside (half-voxel margin)
    del ins
    e = _dist(~ero, h)                              # distance to the nearest ball centre
    del ero
    return np.maximum(D, (e - r).astype(D.dtype))


def print_safe_selective(sculpt, r_open=0.21, r_close=0.22, deep_mm=None, blend_vox=1.5, drop_islands_mm3=0.5,
                         deep_close_mm=None):
    """Print-safety filter that leaves the sculpt untouched except where it is genuinely unprintable (helms 0.3).

    A closing by c and an opening by r change the surface in two ways: shallowly everywhere (an opening shaves at most
    (sqrt(2)-1)*r off a right-angled convex edge, a closing fillets an inside corner by as much, and the integer-voxel
    distance transforms add up to a voxel of noise on every face), and deeply where a slot is narrower than 2c or a
    wall, lip or fin thinner than 2r. print_safe / print_safe_clean applied both everywhere: edges went round, faces went
    lumpy and the detailed VH2/VH4 helms melted. Here a voxel takes the filtered value only where the filter moves the
    surface by more than deep_mm (a narrow slot filled, a thin feature removed); the mask is feathered over blend_vox
    voxels so the seam is smooth. Edges, corners and every face elsewhere keep the original field exactly.
    Guarantees: walls >= 2*r_open (0.42 mm) and slots >= 2*r_close (0.5 mm) wherever the filter acts."""
    from scipy.ndimage import gaussian_filter
    D, h = sculpt.D, sculpt.h
    # The thresholds sit above the voxel noise of the distance transforms (~1 voxel). 0.12 / 0.04 mm were set on the
    # 0.05 mm helm grid; on a 0.12 mm figure grid they sat under the noise and the filter re-wrote (terraced) every face.
    deep_mm = max(0.12, 1.6 * h) if deep_mm is None else deep_mm
    deep_close_mm = (0.04 if h <= 0.06 else 1.1 * h) if deep_close_mm is None else deep_close_mm
    v0 = int((D < 0).sum())
    g = _dist(~(_dist(D >= 0, h) > r_close + 0.5 * h), h)
    closed = -(g - r_close)
    del g
    # Closing: an inside-corner fillet is shallow but so is the middle of a 0.2 mm crack, so fills use their own,
    # smaller threshold (a 0.04 mm fillet is invisible; an unfilled crack is a fill-in defect).
    w = gaussian_filter(((D - closed) > deep_close_mm).astype(np.float32), blend_vox)  # fills: slots and cracks
    D = np.where(w > 0.02, np.minimum(D, w * closed + (1 - w) * D), D).astype(D.dtype)
    filled = int(((D < 0).sum()) - v0)
    e = _dist(~(_dist(D < 0, h) > r_open + 0.5 * h), h)
    opened = e - r_open
    del e
    w = gaussian_filter(((opened - D) > deep_mm).astype(np.float32), blend_vox)      # deep removals only (thin features)
    D = np.where(w > 0.02, np.maximum(D, w * opened + (1 - w) * D), D).astype(D.dtype)
    # Removing a thin bridge can leave a loose speck (VH4-18: a 0.1 mm3 fin shard); a floating speck cannot print, drop it.
    from scipy.ndimage import label
    lab, n = label(D < 0)
    dropped = 0.0
    if n > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        keep = sizes.argmax()
        for i in range(1, n + 1):
            if i != keep and sizes[i] * h ** 3 < drop_islands_mm3:
                D[lab == i] = np.maximum(D[lab == i], h)
                dropped += sizes[i] * h ** 3
    sculpt.D = D
    v1 = int((D < 0).sum())
    return {"r_open_mm": r_open, "r_close_mm": r_close, "deep_mm": deep_mm, "deep_close_mm": deep_close_mm, "filled_mm3": round(filled * h ** 3, 3),
            "dropped_islands_mm3": round(dropped, 3), "volume_change_mm3": round((v1 - v0) * h ** 3, 3)}


def thicken_thin(sculpt, t_min=0.44, grow=0.1, edge_depth=None, rounds=3, sigma_vox=0.7, tol_vox=0.35):
    """Grow only genuinely thin material to t_min, keeping every crisp edge (helms 0.3).

    An opening by a ball of radius t_min/2 removes two kinds of material: a shallow sliver along every convex edge (at
    most (sqrt(2)-1)*r deep on a right-angled edge) and whole thin walls, lips and fins. Opening (print_safe) deletes
    both, which rounds every edge and melted the detailed VH2 helms. Here the removed set is split by its distance from
    the opened body: deeper than edge_depth is a thin feature, and that set alone is grown by `grow` (repeated up to
    `rounds` times while anything thin is left), so a 0.26 mm visor frame becomes ~0.46 mm and edges stay sharp.
    Returns stats per round."""
    from scipy.ndimage import gaussian_filter
    h, r = sculpt.h, t_min / 2
    edge_depth = (math.sqrt(2) - 1) * r + h if edge_depth is None else edge_depth
    stats = []
    for _ in range(rounds):
        D = sculpt.D
        ins = D < 0
        core = _dist(ins, h) > r + 0.5 * h
        opened = _dist(~core, h) <= r + 0.5 * h
        del core
        thin = ins & ~opened & (_dist(~opened, h) > edge_depth)
        n = int(thin.sum())
        stats.append({"thin_voxels": n, "thin_mm3": round(n * h ** 3, 4)})
        if n == 0:
            break
        g = gaussian_filter(_dist(~thin, h) - grow, sigma_vox)
        sculpt.D = np.minimum(D, g.astype(D.dtype) + tol_vox * h)
    return stats


def print_safe_clean(sculpt, r_open=0.25, r_close=0.26, sigma_vox=1.0, tol_vox=0.35):
    """print_safe without the voxel terracing (helms 0.3). The EDT fields are integer-voxel distances, so taking
    min/max with them everywhere copied their quantisation onto every surface: the VH3 helms printed with visible
    contour rings and grain. Here each morphological field is Gaussian-smoothed (sigma_vox voxels) and only replaces
    the original where it moves the surface by more than tol_vox voxels, so untouched surfaces keep the original field.
    Guarantees with h = 0.05: walls >= 2*r_open - 2*tol*h (0.465 mm), slots narrower than 2*r_close - 2*tol*h close."""
    from scipy.ndimage import gaussian_filter
    D, h = sculpt.D, sculpt.h
    v0 = int((D < 0).sum())
    tol = tol_vox * h
    g = _dist(~(_dist(D >= 0, h) > r_close + 0.5 * h), h)
    D = np.minimum(D, gaussian_filter(-(g - r_close), sigma_vox).astype(D.dtype) + tol)
    del g
    e = _dist(~(_dist(D < 0, h) > r_open + 0.5 * h), h)
    D = np.maximum(D, gaussian_filter(e - r_open, sigma_vox).astype(D.dtype) - tol)
    del e
    sculpt.D = D
    v1 = int((D < 0).sum())
    return {"r_open_mm": r_open, "r_close_mm": r_close, "sigma_vox": sigma_vox, "tol_vox": tol_vox, "voxels_before": v0,
            "voxels_after": v1, "volume_change_mm3": round((v1 - v0) * h ** 3, 3)}


def print_safe(sculpt, r_open=0.25, r_close=0.26):
    """In place on an sdfkit.Sculpt: closing (gaps >= 2*r_close) then opening (walls >= 2*r_open). Returns stats."""
    D = sculpt.D
    v0 = int((D < 0).sum())
    D = close_field(D, sculpt.h, r_close)
    D = open_field(D, sculpt.h, r_open)
    sculpt.D = D
    v1 = int((D < 0).sum())
    return {"r_open_mm": r_open, "r_close_mm": r_close, "voxels_before": v0, "voxels_after": v1,
            "volume_change_mm3": round((v1 - v0) * sculpt.h ** 3, 3)}
