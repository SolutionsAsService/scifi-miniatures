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
