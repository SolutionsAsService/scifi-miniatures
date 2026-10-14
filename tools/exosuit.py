"""Kestrel-pattern exosuit: the shared armour kit of the Aster Compact Vigilants (original design, see README).

Design language (one kit, every figure):
- heavy powered armour over a ribbed bodysuit: broad chest and shoulders, armoured thighs and greaves, big boots;
- plates are the body grown outward and cut to an oval outline (plate()), so every rim steps off the suit;
- a sternum KEEL ridge on the faceted cuirass that continues as the helm crest;
- layered shoulder caps that hug the deltoid and sweep back (a soldier's shoulder, not a pauldron);
- the helm: a smooth egg with a split CHEVRON visor (two lenses in a V, split by the keel) over a respirator muzzle,
  and ear-pod sensor fins sweeping back.

A pose is a handful of targets (pelvis, ankles, fists, head yaw); two-bone IK fills in knees and elbows (knees can be
given explicitly for kneeling), so every figure keeps the same proportions.
Frame: mm, z up, the figure faces -y, its left hand on +x.
"""
from __future__ import annotations

import math

import numpy as np

from sdfkit import Sculpt, Shape, capsule, cyl, d_peg, ellipsoid, frame, half, rbox, rot, round_cone, sphere, torus, tube, unit, v3

Z = v3(0, 0, 1)
I3 = np.eye(3)
RY = (0, 1, 0)

# proportions (mm at print scale): about 30 mm heroic to the visor line
L_THIGH, L_SHIN, ANKLE_H = 7.6, 7.3, 1.9
L_UPPER, L_FORE = 5.4, 4.9      # elbow to wrist; the fist centre sits 1.0 beyond the wrist
SPINE, NECK = 5.6, 3.4
SH_W, SH_UP, HIP_W = 5.5, 2.2, 2.6
GORGET_UP = 0.55                # neck cut above the neck base: the helm part starts here
HS = 1.12                       # helm scale (heroic head)
HEAD_UP = 2.5 * HS              # neck cut to helm centre

# joint sizes from miniature_base_and_peg (msla_resin, glue fit 0.1 mm per side): see tools/checkplan.py
PEG_HEAD = {"d": 1.6, "len": 2.0, "sock_depth": 2.2}
PEG_PACK = {"d": 2.0, "len": 2.5, "sock_depth": 2.7}
PLINTH_T, PLINTH_R = 1.1, 3.1   # integral footplate under the boots, sunk flush into the base recess


def ik(a, t, l1, l2, pole):
    a, t, pole = v3(a), v3(t), v3(pole)
    d = t - a
    L = float(np.linalg.norm(d))
    if L > l1 + l2 - 0.15:
        raise SystemExit(f"IK target out of reach: {L:.2f} > {l1 + l2 - 0.15:.2f}")
    n = d / L
    c = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L)
    p = pole - n * (pole @ n)
    p = p / np.linalg.norm(p)
    return a + n * l1 * c + p * l1 * math.sqrt(max(0.0, 1 - c * c))


def place(origin, xdir, up):
    """4x4 that maps a local frame (x forward, z up) to world."""
    x = unit(xdir)
    z = unit(v3(up) - x * (v3(up) @ x))
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, :3] = np.stack([x, y, z], axis=1)
    M[:3, 3] = origin
    return M


def apply(M, p):
    return (M @ np.append(v3(p), 1.0))[:3]


class Pose:
    def __init__(self, pelvis=(0, 0, 15.8), yaw=0.0, lean=6.0, twist=0.0, tilt=0.0,
                 ankles=((-3.2, 0.6, ANKLE_H), (3.2, -0.6, ANKLE_H)), feet_yaw=(-8.0, 8.0),
                 fists=((-6.0, -1.0, 15.0), (6.0, -1.0, 15.0)),
                 elbow_poles=((-1, 1.2, -0.4), (1, 1.2, -0.4)), knee_poles=((-0.3, -1, 0), (0.3, -1, 0)),
                 knees=(None, None), head_yaw=0.0):
        self.pelvis = v3(pelvis)
        self.Rp = rot(Z, yaw)
        self.Rc = self.Rp @ rot(Z, twist) @ rot(RY, tilt) @ rot((1, 0, 0), lean)
        self.Rmid = self.Rp @ rot(Z, twist / 2) @ rot((1, 0, 0), lean / 2)
        Rc, Rp = self.Rc, self.Rp
        self.fwd = Rp @ v3(0, -1, 0)
        self.cfwd = Rc @ v3(0, -1, 0)
        self.chest = self.pelvis + self.Rmid @ v3(0, 0.15, SPINE * 0.45) + Rc @ v3(0, 0, SPINE * 0.55)
        self.neck = self.chest + Rc @ v3(0, 0.25, NECK)
        self.cut_z = float(self.neck[2] + GORGET_UP)
        self.neck_cut = v3(self.neck[0], self.neck[1], self.cut_z)
        self.head_yaw = head_yaw + math.degrees(math.atan2(self.cfwd[0], -self.cfwd[1]))
        self.sh = [self.chest + Rc @ v3(s * SH_W, 0.35, SH_UP) for s in (-1, 1)]       # 0 = right (-x), 1 = left
        self.hip = [self.pelvis + Rp @ v3(s * HIP_W, 0.1, -0.55) for s in (-1, 1)]
        self.ankle = [v3(a) for a in ankles]
        self.feet_yaw = feet_yaw
        self.knee = [v3(knees[i]) if knees[i] is not None else ik(self.hip[i], self.ankle[i], L_THIGH, L_SHIN, Rp @ v3(knee_poles[i]))
                     for i in range(2)]
        self.fist = [v3(f) for f in fists]
        self.elbow = [ik(self.sh[i], self.fist[i], L_UPPER, L_FORE + 1.0, Rc @ v3(elbow_poles[i])) for i in range(2)]
        self.wrist = [self.elbow[i] + unit(self.fist[i] - self.elbow[i]) * L_FORE for i in range(2)]

    def key_dir(self):
        """Forward direction of the helm (the D-flat key of the neck socket)."""
        return rot(Z, self.head_yaw) @ v3(0, -1, 0)


def groove(shape, p, n, width=0.42, depth=0.4):
    """Panel line: a band (width along n at p) carved depth into the surface of 'shape' only."""
    n = unit(n)
    p = v3(p)
    band = Shape(lambda Q: np.abs((Q - p) @ n) - width / 2, shape.lo, shape.hi)
    return (band & shape.offset(0.6)) - shape.offset(-depth)


def plate(body, t, c, radii, R):
    """Armour plate: the body grown by t, cut to the oval outline of an ellipsoid (centre c, radii along R's columns)
    placed on its surface. The plate hugs the form and its whole rim steps t off the bodysuit."""
    return body.offset(t) & ellipsoid(c, radii, R)


def side_frame(out, axis):
    """Frame whose 2nd column is 'out' made normal to axis and 3rd column is the axis."""
    a = unit(axis)
    o = unit(out - a * (out @ a))
    return np.stack([np.cross(o, a), o, a], axis=1), o


# ------------------------------------------------------------------------------------------------ body
def figure(pose, h=0.085, extras=(), bbox=None):
    """The armoured body without helm and backpack. extras: callables(sculpt, pose) for hands, weapons and gear."""
    P = pose
    lo, hi = bbox or ((-10.5, -15.0, -PLINTH_T - 0.2), (10.5, 8.0, P.cut_z + 3.2))
    g = Sculpt(lo, hi, h)
    Rc, Rp, Rm = P.Rc, P.Rp, P.Rmid
    up_c = Rc @ Z

    # ---------------- bodysuit: smooth anatomical masses (heavy frame)
    pelvis = ellipsoid(P.pelvis + Rp @ v3(0, 0.1, 0.25), (2.85, 2.05, 2.1), Rp)
    abdomen = ellipsoid(P.pelvis + Rm @ v3(0, 0.05, 2.8), (3.15, 2.3, 2.6), Rm)
    ribs = ellipsoid(P.chest + Rc @ v3(0, 0.05, 0.35), (4.6, 3.05, 3.4), Rc)
    lats = ellipsoid(P.chest + Rc @ v3(0, 0.55, -1.0), (4.2, 2.3, 2.8), Rc)
    for s in (pelvis, abdomen, ribs, lats):
        g.add(s, 0.9)
    for i, sgn in ((0, -1), (1, 1)):
        g.add(round_cone(P.neck + Rc @ v3(0, 0.1, -0.3), P.sh[i] + Rc @ v3(-sgn * 0.3, 0, 0.2), 1.45, 1.05), 0.7)  # trapezius
        g.add(sphere(P.sh[i], 1.75), 0.6)                                                                          # deltoid
        g.add(ellipsoid(P.hip[i] + Rp @ v3(-sgn * 0.25, 0.7, 0.3), (1.35, 1.0, 1.35), Rp), 0.5)                   # glute
    g.add(capsule(P.neck + Rc @ v3(0, 0, -1.0), P.neck + v3(0, 0, GORGET_UP + 0.9), 1.4), 0.4)   # neck: 0.4 mm wall round the socket

    thighs, shins, uppers, fores = [], [], [], []
    for i in range(2):
        hip, knee, ank = P.hip[i], P.knee[i], P.ankle[i]
        ax = knee - hip
        R = frame(ax, P.fwd)
        thighs.append(round_cone(hip + v3(0, 0, 0.3), knee, 2.15, 1.6))
        g.add(thighs[i], 0.8)
        g.add(ellipsoid(hip + ax * 0.45 + R[:, 1] * 0.35, (1.6, 1.5, 2.7), R), 0.5)                  # quads
        sx = ank - knee
        Rs = frame(sx, P.fwd)
        shins.append(round_cone(knee, ank, 1.55, 1.2))
        g.add(shins[i], 0.5)
        g.add(ellipsoid(knee + sx * 0.32 - Rs[:, 1] * 0.5, (1.3, 1.35, 2.3), Rs), 0.5)               # calf
    for i in range(2):
        sh, el, wr = P.sh[i], P.elbow[i], P.wrist[i]
        ua, fa = el - sh, wr - el
        uppers.append(round_cone(sh, el, 1.5, 1.2))
        g.add(uppers[i], 0.5)
        g.add(ellipsoid(sh + ua * 0.5, (1.45, 1.4, 2.0), frame(ua, P.cfwd)), 0.5)                    # biceps / triceps
        fores.append(round_cone(el, wr, 1.4, 1.1))
        g.add(fores[i], 0.45)
        g.add(ellipsoid(el + fa * 0.3, (1.4, 1.35, 1.7), frame(fa, P.cfwd)), 0.4)                    # forearm mass

    # ---------------- bodysuit ribbing (flex panels) at the waist
    for t in (1.7, 2.5, 3.3):
        g.cut(groove(abdomen, P.pelvis + Rm @ v3(0, 0, t), Rm @ Z, 0.4, 0.24))

    # ---------------- armour
    cuirass = ribs.offset(0.45).clip(half(P.chest + Rc @ v3(0, 0, -2.2), -up_c), half(P.chest + Rc @ v3(0, 0, 3.15), up_c),
                                     half(P.chest + Rc @ v3(0, -3.3, 0), Rc @ unit((0.36, -1, 0.12))),
                                     half(P.chest + Rc @ v3(0, -3.3, 0), Rc @ unit((-0.36, -1, 0.12))))   # two chest facets
    g.add(cuirass, 0.15)
    g.add(round_cone(P.chest + Rc @ v3(0, -3.4, 2.2), P.chest + Rc @ v3(0, -3.3, -2.0), 0.45, 0.38), 0.1)   # keel
    g.add(ellipsoid(P.chest + Rc @ v3(0, 2.5, 0.6), (3.6, 1.1, 2.6), Rc), 0.2)                              # back plate
    g.add(plate(abdomen, 0.4, P.pelvis + Rm @ v3(0, -2.35, 2.95), (1.6, 1.5, 1.55), Rm), 0.1)              # abdominal plate
    g.cut(groove(abdomen.offset(0.4), P.pelvis + Rm @ v3(0, 0, 2.9), Rm @ Z, 0.4, 0.3))
    g.add(torus(P.neck + Rc @ v3(0, 0.1, 0.05), up_c, 1.85, 0.62), 0.25)                                   # gorget
    g.add(ellipsoid(P.neck + Rc @ v3(0, 1.2, 0.15), (2.0, 0.7, 0.95), Rc), 0.2)
    g.add(torus(P.pelvis + Rp @ v3(0, 0.1, 1.15), Rp @ Z, 2.85, 0.45), 0.25)                               # belt
    g.add(rbox(P.pelvis + Rp @ v3(0, -2.75, 1.1), (0.95, 0.38, 0.6), Rp, 0.25), 0.1)                       # buckle
    g.add(plate(pelvis, 0.42, P.pelvis + Rp @ v3(0, -2.25, -0.3), (1.3, 1.3, 1.45), Rp), 0.1)              # codpiece
    g.add(plate(pelvis, 0.4, P.pelvis + Rp @ v3(0, 2.2, 0.55), (2.1, 1.3, 1.2), Rp), 0.1)                  # kidney plate
    for i, sgn in ((0, -1), (1, 1)):
        g.add(plate(pelvis, 0.4, P.pelvis + Rp @ v3(sgn * 2.85, -0.3, -0.1), (1.1, 1.55, 1.45), Rp), 0.1)  # tassets

    # shoulder caps: two layers that hug the deltoid and sweep back, with a ridge
    for i, sgn in ((0, -1), (1, 1)):
        sh = P.sh[i]
        out = Rc @ v3(sgn, 0, 0)
        cap = plate(sphere(sh + out * 0.3 + up_c * 0.15, 1.95), 0.5, sh + out * 1.05 + up_c * 1.4 + Rc @ v3(0, 0.25, 0),
                    (2.45, 2.65, 1.8), Rc @ rot(RY, -sgn * 35))
        low = plate(sphere(sh + out * 0.5 - up_c * 0.5, 1.8), 0.36, sh + out * 2.1 - up_c * 0.75 + Rc @ v3(0, 0.3, 0),
                    (1.5, 2.25, 1.5), Rc @ rot(RY, -sgn * 60))
        g.add(low, 0.08)
        g.add(cap, 0.08)
        g.add(round_cone(sh + out * 0.45 + up_c * 2.4 + Rc @ v3(0, -1.0, 0), sh + out * 0.85 + up_c * 2.1 + Rc @ v3(0, 1.8, 0),
                         0.34, 0.3), 0.12)

    # arms: outer biceps plate, elbow cop, heavy bracer
    for i, sgn in ((0, -1), (1, 1)):
        sh, el, wr = P.sh[i], P.elbow[i], P.wrist[i]
        ua, fa = el - sh, wr - el
        Ru, out = side_frame(Rc @ v3(sgn, 0, 0), ua)
        g.add(plate(uppers[i], 0.32, sh + ua * 0.55 + out * 1.55, (1.45, 1.4, 1.75), Ru), 0.1)
        ep = el - (sh + wr) / 2
        ep = unit(ep) if np.linalg.norm(ep) > 0.3 else -P.cfwd
        g.add(ellipsoid(el + ep * 0.7, (1.05, 1.05, 1.2), frame(ua, ep)), 0.15)
        Rf, back = side_frame(out, fa)
        g.add(plate(fores[i], 0.38, el + fa * 0.55 + back * 1.3, (1.65, 1.65, 2.3), Rf), 0.1)
        g.add(fores[i].offset(0.3).clip(half(el + fa * 0.97, unit(fa)), half(el + fa * 0.8, -unit(fa))), 0.1)  # cuff ring
        g.cut(groove(fores[i].offset(0.38), el + fa * 0.6, unit(fa), 0.4, 0.25))

    # legs: front, outer and rear thigh plates, knee guard, greave with a shin ridge, calf guard, boots
    for i, sgn in ((0, -1), (1, 1)):
        hip, knee, ank = P.hip[i], P.knee[i], P.ankle[i]
        ax = knee - hip
        R = frame(ax, P.fwd)
        w = R[:, 1]
        g.add(plate(thighs[i], 0.4, hip + ax * 0.5 + w * 2.0, (1.7, 1.8, 3.1), R), 0.1)               # front
        Ro, _ = side_frame(P.Rp @ v3(sgn, 0, 0), ax)
        g.add(plate(thighs[i], 0.32, hip + ax * 0.32 + Ro[:, 1] * 2.0, (1.6, 1.7, 2.3), Ro), 0.1)     # outer, layered
        g.add(plate(thighs[i], 0.3, hip + ax * 0.58 - w * 1.9, (1.5, 1.5, 2.2), R), 0.1)              # rear
        kp = knee - (hip + ank) / 2
        kp = unit(kp) if np.linalg.norm(kp) > 0.4 else w
        kp = unit(kp + w * 0.6)
        sx = ank - knee
        ns = unit(sx)
        Rs = frame(sx, kp)
        g.add(ellipsoid(knee + kp * 1.2 + ns * 0.25, (1.25, 0.9, 1.6), Rs).clip(
            half(knee + kp * 1.75, unit(kp - ns * 0.6))), 0.15)                                         # knee guard, pointed
        g.add(plate(shins[i], 0.45, knee + sx * 0.55 + Rs[:, 1] * 1.55, (1.75, 1.7, 3.5), Rs), 0.1)     # greave
        g.add(plate(shins[i], 0.32, knee + sx * 0.33 - Rs[:, 1] * 1.8, (1.4, 1.5, 1.8), Rs), 0.1)       # calf guard
        g.add(round_cone(knee + sx * 0.3 + Rs[:, 1] * 1.95, ank + Rs[:, 1] * 1.6 + v3(0, 0, 0.5), 0.36, 0.32), 0.15)
        fd = unit(rot(Z, P.feet_yaw[i]) @ P.fwd)
        Rf = np.stack([np.cross(fd, Z), fd, Z], axis=1)
        boot = rbox(ank + fd * 0.9 + v3(0, 0, -1.0), (1.6, 2.85, 1.0), Rf, 0.5)
        boot = boot | ellipsoid(ank + fd * 2.75 + v3(0, 0, -0.95), (1.5, 1.45, 1.0), Rf)           # toe cap
        boot = boot | round_cone(ank + v3(0, 0, -1.0), ank + v3(0, 0, 1.0), 1.6, 1.45)               # ankle cuff
        g.add(boot.clip(half(v3(0, 0, 0), -Z)), 0.3)
        g.cut(groove(boot, ank + v3(0, 0, -1.25), Z, 0.4, 0.25))  # sole line (on the unclipped boot: clip planes fool groove())

    # ---------------- hands, weapons and gear
    for fn in extras:
        fn(g, P)

    # ---------------- joints: plinth, neck socket, backpack boss and socket
    plinth(g, P)
    g.cut(cyl(P.neck_cut, P.neck_cut + v3(0, 0, 8), 2.2))                                            # nothing above the neck cut
    g.cut(d_peg(P.neck_cut + v3(0, 0, 0.01), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["sock_depth"], key=P.key_dir(), grow=0.1))
    mount = pack_mount(P)
    g.add(rbox(mount - Rc @ v3(0, 0.5, 0), (1.7, 0.5, 1.9), Rc, 0.3), 0.15)                          # backpack boss
    g.cut(d_peg(mount + Rc @ v3(0, 0.01, 0), Rc @ v3(0, -1, 0), PEG_PACK["d"], PEG_PACK["sock_depth"], key=Rc @ Z, grow=0.1))
    return g


def pack_mount(P):
    """Centre of the flat backpack mounting face on the back plate."""
    return P.chest + P.Rc @ v3(0, 3.95, 0.55)


def plinth(g, P):
    """Integral footplate under the feet, PLINTH_T thick, top at z = 0; its outline keys it into the base recess."""
    g.add(plinth_shape(P).clip(half(v3(0, 0, 0), Z), half(v3(0, 0, -PLINTH_T), -Z)), 0.2)


def plinth_shape(P, grow=0.0):
    """Stadium joining the two feet plus a key lobe behind the right foot (vertical prism, any z)."""
    pts = [P.ankle[i] + rot(Z, P.feet_yaw[i]) @ P.fwd * 1.0 for i in range(2)]
    a, b = v3(pts[0][0], pts[0][1], 0), v3(pts[1][0], pts[1][1], 0)
    k = P.ankle[0] + P.Rp @ v3(-1.6, 2.8, 0)
    k = v3(k[0], k[1], 0)
    r, rk = PLINTH_R + grow, 1.5 + grow
    ab = b - a
    L2 = float(ab @ ab)

    def f(Q):
        q = Q.copy()
        q[:, 2] = 0
        t = np.clip(((q - a) @ ab) / L2, 0, 1)
        return np.minimum(np.linalg.norm(q - (a + np.outer(t, ab)), axis=1) - r, np.linalg.norm(q - k, axis=1) - rk)

    lo = np.minimum(np.minimum(a, b) - r, k - rk)
    hi = np.maximum(np.maximum(a, b) + r, k + rk)
    return Shape(f, v3(lo[0], lo[1], -20), v3(hi[0], hi[1], 20))


# ------------------------------------------------------------------------------------------------ hands
def fist(g, center, grip_axis, forearm_dir, k=0.25):
    """Armoured gauntlet closed around a grip running along grip_axis (the held part passes through it)."""
    c = v3(center)
    n = unit(grip_axis)
    fa = unit(forearm_dir)
    w = unit(fa - n * (fa @ n))
    u = np.cross(w, n)
    R = np.stack([u, w, n], axis=1)
    g.add(rbox(c, (0.85, 1.0, 1.05), R, 0.55), k)
    g.add(rbox(c + w * 0.45 + u * 0.2, (0.62, 0.6, 1.0), R, 0.32), 0.1)                                # knuckle plate
    g.add(capsule(c - w * 0.35 - n * 0.9 + u * 0.45, c + w * 0.1 - n * 0.65 - u * 0.65, 0.38), 0.15)  # thumb


def open_hand(g, center, point_dir, palm_normal, sgn):
    """Pointing gauntlet: palm block, index finger extended, the rest curled."""
    c, d, pn = v3(center), unit(point_dir), unit(palm_normal)
    side = np.cross(pn, d)
    R = np.stack([side, pn, d], axis=1)
    g.add(rbox(c, (0.9, 0.6, 0.95), R, 0.4), 0.25)
    g.add(capsule(c + d * 0.8 + side * 0.5 * sgn, c + d * 2.4 + side * 0.55 * sgn, 0.38), 0.12)         # index
    g.add(rbox(c + d * 0.95 + pn * 0.3 - side * 0.18 * sgn, (0.65, 0.52, 0.5), R, 0.32), 0.15)          # curled fingers
    g.add(capsule(c - side * 0.65 * sgn + d * 0.1, c - side * 0.85 * sgn + d * 0.9 + pn * 0.25, 0.36), 0.12)  # thumb


# ------------------------------------------------------------------------------------------------ helm
def helm(variant="vigil", h=0.06):
    """Separate helm part in its own frame: neck cut at z = 0 (sits on the gorget), peg down, faces -y.
    Variants: vigil (line standard), warden (command crest and whip antenna), breacher (armoured face, slit lens),
    seeker (monocular sensor)."""
    hc = v3(0, 0, HEAD_UP)
    H = lambda x, y, z: hc + HS * v3(x, y, z)          # helm-local point, scaled
    r = lambda *a: tuple(HS * x for x in a)
    top = HEAD_UP + HS * (6.5 if variant == "warden" else 3.4)
    g = Sculpt((-4.0, -4.4, -PEG_HEAD["len"] - 0.3), (4.0, 4.6, top), h)
    g.add(ellipsoid(H(0, 0.25, 0.25), r(2.2, 2.55, 2.55)))                                              # dome
    g.add(ellipsoid(H(0, -1.45, -1.05), r(1.45, 1.25, 1.15), rot((1, 0, 0), 10)), 0.55 * HS)          # muzzle
    for s in (-1, 1):  # cheek plates flaring back
        g.add(ellipsoid(H(s * 1.55, -0.5, -0.85), r(0.7, 1.55, 1.2), rot(Z, s * 18)), 0.35)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                          # neck seal
    for s in (-1, 1):  # chevron visor: two lenses in a V, recessed
        g.cut(rbox(H(s * 1.0, -2.55, 0.12), r(1.05, 0.65, 0.3), rot(RY, s * 24), 0.12))
    crest = [H(0, 0.25, 0.25) + HS * v3(0, -2.55 * math.cos(a) * 1.04, 2.55 * math.sin(a) * 1.04)
             for a in np.radians(np.linspace(25, 160, 12))]
    g.add(tube(crest, 0.32), 0.15)                                                                     # keel crest
    g.add(round_cone(H(0, -2.6, -0.15), H(0, -2.55, -1.6), 0.32, 0.3), 0.12)                         # keel between the lenses
    for s in (-1, 1):  # respirator slots
        for j in range(3):
            g.cut(rbox(H(s * (0.55 + 0.33 * j), -2.25 + 0.16 * j, -1.45), (0.13, 0.55, 0.38), rot(Z, s * 25), 0.06))
    for s in (-1, 1):  # ear pods with swept sensor fins
        g.add(cyl(H(s * 1.95, 0.1, -0.05), H(s * 2.4, 0.1, -0.05), 0.68 * HS, 0.18), 0.12)
        g.add(tube([H(s * 2.2, 0.45, 0.25), H(s * 2.05, 1.6, 0.95), H(s * 1.7, 2.6, 1.5)], 0.36, 0.32), 0.15)
    if variant == "warden":
        g.add(rbox(H(0, 0.6, 2.9), r(0.32, 1.7, 0.55), rot((1, 0, 0), -14), 0.3), 0.25)
        g.add(capsule(H(-2.3, 0.6, 0.4), H(-2.55, 1.6, 5.6), 0.42), 0.15)
    elif variant == "breacher":
        g.add(ellipsoid(H(0, -1.95, -0.2), r(1.75, 0.8, 1.75)), 0.25)
        g.cut(rbox(H(0, -2.9, 0.2), r(1.35, 0.6, 0.22), I3, 0.1))
        g.add(rbox(H(0, -2.55, -0.9), r(0.9, 0.35, 0.18), I3, 0.12), 0.1)
    elif variant == "seeker":
        g.add(cyl(H(1.05, -1.9, 0.75), H(1.25, -3.3, 0.85), 0.6 * HS, 0.15), 0.15)
        g.cut(cyl(H(1.24, -3.4, 0.85), H(1.2, -2.9, 0.85), 0.33 * HS))
        g.add(capsule(H(1.0, -1.5, 0.8), H(2.2, -0.2, 0.3), 0.34), 0.15)
    g.cut(Shape(lambda Q: Q[:, 2], (-9, -9, -9), (9, 9, 0)))                                         # flat seat at z = 0
    g.add(d_peg((0, 0, 0.3), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["len"] + 0.3, key=(0, -1, 0)))
    return g


# ------------------------------------------------------------------------------------------------ backpacks
def backpack(variant="power", h=0.06):
    """Separate pack in its own frame: front face on y = 0 (against the back boss), peg toward -y, up z."""
    lo = (-6.9 if variant == "jump" else -4.8, -PEG_PACK["len"] - 0.3, -6.4)
    hi = {"comms": (4.8, 5.4, 10.4), "jump": (6.9, 5.2, 4.8)}.get(variant, (4.8, 5.2, 4.8))
    g = Sculpt(lo, hi, h)
    g.add(rbox(v3(0, 1.15, 0.2), (2.4, 1.15, 3.0), I3, 0.7))                                             # core
    g.add(rbox(v3(0, 2.2, 0.6), (1.7, 0.8, 2.2), I3, 0.5), 0.25)                                         # cell
    g.add(round_cone(v3(0, 3.0, 2.7), v3(0, 3.0, -1.6), 0.42, 0.4), 0.12)                                # keel spine
    for j in range(3):
        g.cut(rbox(v3(0.0, 3.05, -0.8 + j * 0.9), (1.8, 0.55, 0.21), I3, 0.08))                           # vents
    if variant == "power":
        for s in (-1, 1):
            d = unit((s * 0.35, 0.45, -1))
            n0 = v3(s * 1.6, 1.3, -2.6)
            g.add(round_cone(n0, n0 + d * 1.9, 0.8, 1.0), 0.3)
            g.cut(round_cone(n0 + d * 1.0, n0 + d * 2.5, 0.38, 0.66))
    elif variant == "jump":
        for s in (-1, 1):
            a, b = v3(s * 2.4, 1.4, 1.2), v3(s * 3.4, 2.1, -3.3)
            g.add(round_cone(a, b, 1.0, 1.25), 0.4)
            g.cut(round_cone(b - unit(b - a) * 0.9, b + unit(b - a) * 0.8, 0.48, 0.84))
            g.add(rbox(v3(s * 4.7, 1.6, 1.6), (1.9, 0.36, 0.78), rot(RY, -s * 35) @ rot(Z, s * 12), 0.3), 0.3)
    elif variant == "comms":
        g.add(cyl(v3(-1.3, 1.4, 2.6), v3(-1.3, 1.4, 3.6), 0.6, 0.15), 0.15)
        g.add(capsule(v3(-1.3, 1.4, 3.4), v3(-1.7, 2.4, 9.2), 0.44), 0.1)                                    # antenna
        g.add(sphere(v3(-1.7, 2.4, 9.2), 0.58), 0.1)
        g.add(rbox(v3(1.3, 1.5, 2.8), (0.65, 0.65, 0.65), I3, 0.3), 0.2)
        for s in (-1, 1):
            g.add(round_cone(v3(s * 1.5, 1.2, -2.5), v3(s * 1.65, 1.6, -3.8), 0.72, 0.85), 0.3)
    g.cut(Shape(lambda Q: Q[:, 1], (-9, -9, -9), (9, 0, 12)))                                              # flat front at y = 0
    g.add(d_peg((0, 0.3, 0), (0, -1, 0), PEG_PACK["d"], PEG_PACK["len"] + 0.3, key=(0, 0, 1)))
    return g


def pack_placement(P):
    M = np.eye(4)
    M[:3, :3] = P.Rc
    M[:3, 3] = pack_mount(P)
    return M


def helm_placement(P):
    M = np.eye(4)
    M[:3, :3] = rot(Z, P.head_yaw)
    M[:3, 3] = P.neck_cut
    return M


# ------------------------------------------------------------------------------------------------ weapons (local: x to the muzzle, z up, origin = grip / fist centre)
def lance_rifle():
    """'Lance' bullpup rifle: 14 mm long, 2.3 mm deep receiver, 1.3 mm barrel, box magazine behind the grip, optic."""
    s = rbox(v3(0.5, 0, 1.05), (3.4, 0.8, 1.15), I3, 0.35)                                   # receiver
    s = s | rbox(v3(5.3, 0, 1.3), (1.7, 0.68, 0.75), I3, 0.3).clip(half(v3(6.7, 0, 1.9), unit((1, 0, 0.8))))  # shroud
    s = s | cyl(v3(6.5, 0, 1.3), v3(8.9, 0, 1.3), 0.65, 0.12)                                # barrel, 1.3 mm
    s = s | cyl(v3(8.4, 0, 1.3), v3(9.4, 0, 1.3), 0.85, 0.2)                                 # muzzle brake
    s = s | rbox(v3(-3.9, 0, 0.95), (0.9, 0.72, 1.25), rot(RY, 8), 0.35)                     # butt
    s = s | rbox(v3(0.9, 0, 2.65), (1.5, 0.5, 0.5), I3, 0.22)                                # optic
    s = s | cyl(v3(2.3, 0, 2.7), v3(2.75, 0, 2.7), 0.62, 0.12)                               # optic hood
    s = s | rbox(v3(0, 0, -0.4), (0.45, 0.48, 0.95), rot(RY, -14), 0.22)                     # grip
    s = s | rbox(v3(-1.95, 0, -0.6), (0.8, 0.62, 1.2), rot(RY, 10), 0.25)                    # magazine (bullpup)
    s = s | rbox(v3(2.9, 0, -0.1), (0.42, 0.45, 0.8), rot(RY, -8), 0.2)                      # fore grip
    return s


def needle_rifle():
    """'Needle' marksman rifle: long 1.3 mm barrel in a shroud, big scope, box magazine."""
    s = rbox(v3(0.6, 0, 1.0), (3.0, 0.72, 1.0), I3, 0.3)
    s = s | cyl(v3(3.4, 0, 1.3), v3(11.6, 0, 1.3), 0.65, 0.12)                               # barrel
    s = s | cyl(v3(3.4, 0, 1.3), v3(6.6, 0, 1.3), 0.88, 0.2)                                 # shroud
    s = s | cyl(v3(11.0, 0, 1.3), v3(12.3, 0, 1.3), 0.85, 0.2)                               # brake
    s = s | rbox(v3(-3.8, 0, 0.8), (1.4, 0.62, 1.1), rot(RY, 6), 0.3)                        # stock
    s = s | cyl(v3(-1.0, 0, 2.8), v3(3.6, 0, 2.8), 0.62, 0.15)                               # scope tube
    s = s | cyl(v3(2.7, 0, 2.8), v3(4.0, 0, 2.8), 0.88, 0.15)                                # objective bell
    s = s | rbox(v3(1.2, 0, 2.1), (0.45, 0.42, 0.55), I3, 0.15)                              # scope mount
    s = s | rbox(v3(0, 0, -0.4), (0.45, 0.48, 0.95), rot(RY, -14), 0.22)                     # grip
    s = s | rbox(v3(-1.6, 0, -0.45), (0.72, 0.58, 0.95), rot(RY, 10), 0.22)                  # magazine
    return s


def maul_cannon():
    """'Maul' heavy arc-cannon: origin at the rear grip, 16 mm long; rails braced by two rings."""
    s = rbox(v3(1.8, 0, 1.35), (4.0, 1.25, 1.35), I3, 0.5)                                   # body
    s = s | cyl(v3(-2.9, 0, 1.55), v3(-0.9, 0, 1.55), 1.55, 0.4)                             # capacitor drum
    s = s | rbox(v3(6.6, 0, 1.45), (1.8, 1.1, 1.1), I3, 0.45)                                # coil housing
    for a in (90, 210, 330):                                                                 # three emitter rails
        o = v3(0, 0.62 * math.cos(math.radians(a)), 1.45 + 0.62 * math.sin(math.radians(a)))
        s = s | cyl(v3(7.8, 0, 0) + o, v3(11.4, 0, 0) + o, 0.45, 0.1)
    s = s | torus(v3(10.0, 0, 1.45), (1, 0, 0), 0.65, 0.34) | torus(v3(11.1, 0, 1.45), (1, 0, 0), 0.65, 0.34)
    s = s | rbox(v3(0, 0, -0.2), (0.45, 0.45, 0.95), rot(RY, -10), 0.2)                      # rear grip
    s = s | capsule(v3(2.2, 0, 2.8), v3(4.9, 0, 2.8), 0.44) | capsule(v3(2.2, 0, 2.8), v3(1.9, 0, 2.2), 0.44) \
        | capsule(v3(4.9, 0, 2.8), v3(5.2, 0, 2.2), 0.44)                                     # carry handle
    return s


def sidearm():
    """'Spur' sidearm."""
    s = rbox(v3(1.0, 0, 1.0), (1.85, 0.5, 0.6), I3, 0.2)
    s = s | cyl(v3(2.7, 0, 1.1), v3(3.5, 0, 1.1), 0.45, 0.1)
    s = s | rbox(v3(0, 0, 0.1), (0.42, 0.42, 0.85), rot(RY, -16), 0.18)
    return s


# ------------------------------------------------------------------------------------------------ base
BASES = {25: {"d": 25.0, "h": 3.8}, 32: {"d": 32.0, "h": 4.0}}
MAGNET = {"name": "5x2", "pocket_d": 5.2, "pocket_depth": 2.1}       # glue fit from miniature_base_and_peg
BASE_INSET, VENT_W, VENT_D, RECESS_CLEAR = 1.0, 1.0, 0.6, 0.1


def base(P, d=25, seed=1, h=0.08):
    """Round deck-plate base (25 or 32 mm): bevelled rim, engraved deck seams, a riveted hatch, a conduit and rubble;
    a recess that takes the figure's footplate (outline keyed, 0.1 mm glue clearance per side) and a 5 x 2 mm magnet
    pocket under it, vented to the rim."""
    rng = np.random.default_rng(seed)
    R0, H0 = BASES[d]["d"] / 2, BASES[d]["h"]
    s = R0 / 16
    g = Sculpt((-R0, -R0, 0), (R0, R0, H0 + 2.2), h)
    k = BASE_INSET / H0

    def body(Q):
        rr = np.hypot(Q[:, 0], Q[:, 1])
        side = (rr - (R0 - k * np.clip(Q[:, 2], 0, H0))) / math.sqrt(1 + k * k)
        return np.maximum(side, np.maximum(-Q[:, 2], Q[:, 2] - H0))
    g.add(Shape(body, (-R0, -R0, 0), (R0, R0, H0)))
    top = Shape(lambda Q: np.maximum(body(Q), H0 - 0.6 - Q[:, 2]), (-R0, -R0, H0 - 0.6), (R0, R0, H0))
    inner = Shape(lambda Q: np.hypot(Q[:, 0], Q[:, 1]) - (R0 - BASE_INSET - 0.6), (-R0,) * 3, (R0,) * 3)
    Rg = rot(Z, rng.uniform(0, 90))
    for t in np.array([-9.0, -3.2, 2.6, 8.4]) * s:
        for ax in (0, 1):
            n = Rg[:, ax]
            seam = Shape(lambda Q, n=n, t=t: np.abs(Q @ n - t) - 0.225, (-R0, -R0, H0 - 1), (R0, R0, H0 + 1))
            g.cut((seam & top).clip(inner))
    feet = plinth_shape(P)
    hc = Rg @ v3(-8.5 * s, 5.5 * s, 0)
    if feet(v3(hc[0], hc[1], 0)[None])[0] > 3.0 * s:
        g.add(rbox(v3(hc[0], hc[1], H0 + 0.2), (2.6 * s, 1.9 * s, 0.45), Rg, 0.25), 0.1)            # hatch
        for dx in (-2.0, 2.0):
            for dy in (-1.4, 1.4):
                q = hc + Rg @ v3(dx * s, dy * s, 0)
                g.add(sphere(v3(q[0], q[1], H0 + 0.62), 0.32), 0.05)
    a, b = Rg @ v3(6.0 * s, -11.5 * s, 0), Rg @ v3(11.0 * s, 1.0 * s, 0)
    if min(feet(np.array([a, b, (a + b) / 2]))) > 1.0:
        g.add(tube([v3(a[0], a[1], H0 + 0.05), v3((a[0] + b[0]) / 2 + 1.0 * s, (a[1] + b[1]) / 2, H0 + 0.35), v3(b[0], b[1], H0 + 0.05)], 0.5), 0.15)
    for _ in range(4):
        rr, th = rng.uniform(8.5, 12.0) * s, rng.uniform(0, 2 * math.pi)
        q = v3(rr * math.cos(th), rr * math.sin(th), H0 + 0.15)
        if feet(v3(q[0], q[1], 0)[None])[0] < 1.5:
            continue
        g.add(rbox(q, tuple(rng.uniform(0.5, 1.0, 3)), rot(unit(rng.normal(size=3)), rng.uniform(0, 90)), 0.15), 0.1)
    g.cut(plinth_shape(P, RECESS_CLEAR).clip(half(v3(0, 0, H0 + 3), Z), half(v3(0, 0, H0 - PLINTH_T), -Z)))
    g.cut(cyl(v3(0, 0, -1), v3(0, 0, MAGNET["pocket_depth"]), MAGNET["pocket_d"] / 2))
    g.cut(rbox(v3(R0 / 2, 0, 0), (R0 / 2 + 1, VENT_W / 2, VENT_D), I3, 0.0))
    return g
