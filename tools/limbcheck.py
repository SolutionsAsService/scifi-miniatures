"""Measure the arms of a BUILT figure STL against the Pose that built it (unified-CAD-MCP miniature_limb.limb_check).

    import limbcheck
    r = limbcheck.check_stl("print/stl/figure.stl", P, hands, height=31.0)
    print(r["all_checks_pass"]); [print(f) for a in r["arms"] for f in a["fix"]]

Run it on the print STL (not a coarse preview): it samples plane sections along each bone, the hand wrap round the grip and ray-cast visibility
of wrist, hand and forearm from 8 azimuths (about 30 s per arm on a 300k-triangle figure; run it at below-normal priority).
"""
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import limbkit  # noqa: E402

ML = limbkit.ML


def load_stl(path):
    data = Path(path).read_bytes()
    n = struct.unpack("<I", data[80:84])[0]
    a = np.frombuffer(data[84:84 + 50 * n], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return [tuple(tuple(float(x) for x in p) for p in t) for t in a["v"]]


def arms_of(P, hands, grip_radius=0.95, grip_length=3.2):
    out = []
    for i in range(2):
        ctr, lat = limbkit.body_frame(P, i)
        out.append(dict(name="right" if i == 0 else "left", shoulder=list(P.sh[i]), elbow=list(P.elbow[i]), wrist=list(P.wrist[i]),
                        hand_center=list(hands[i]["grip"]), grip_axis=list(hands[i]["axis"]), grip_radius_mm=grip_radius, grip_length_mm=grip_length,
                        body_center=list(ctr), lateral_out=list(lat)))
    return out


def check_stl(path, P, hands, height=31.0, **kw):
    return ML.limb_check(load_stl(path), arms_of(P, hands), height, **kw)
