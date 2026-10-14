"""Kestrel-pattern exosuit: the shared armour kit of the Aster Compact Vigilants (original design, see README).

Design language (one kit, every figure):
- an athletic bodysuit with ribbed flex panels at the waist;
- plates offset from the body they cover (sdfkit plate trick) so every edge steps off the suit;
- a sternum KEEL ridge on the cuirass that continues as the helm crest;
- swept, two-layer shoulder plates (small: a soldier's shoulder, not a pauldron);
- the helm: a smooth egg with a split CHEVRON visor (two lenses in a V, split by the keel) over a respirator muzzle,
  and ear-pod sensor fins sweeping back.

A pose is a handful of targets (pelvis, ankles, fists, head yaw); two-bone IK fills in knees and elbows,
so every figure keeps the same proportions. Frame: mm, z up, the figure faces -y, its left hand on +x.
"""
from __future__ import annotations

import math

import numpy as np

from sdfkit import Sculpt, Shape, capsule, cyl, d_peg, ellipsoid, frame, half, rbox, rot, round_cone, sphere, torus, tube, unit, v3

Z = v3(0, 0, 1)

# proportions (mm at print scale): about 30 mm heroic to the visor, 32.5 mm to the crown
L_THIGH, L_SHIN, ANKLE_H = 7.6, 7.3, 1.7
L_UPPER, L_FORE = 5.2, 4.7      # elbow to wrist; the fist centre sits 1.0 beyond the wrist
SPINE, NECK = 5.5, 3.3
SH_W, SH_UP, HIP_W = 4.7, 2.2, 2.3
GORGET_UP = 0.55                # neck cut above the neck base: the helm part starts here
HS = 1.1                        # helm scale (heroic head)
HEAD_UP = 2.5 * HS              # neck cut to helm centre

# joint sizes from miniature_base_and_peg (msla_resin, glue fit 0.1 mm per side): see source/check.py
PEG_HEAD = {"d": 1.6, "len": 2.0, "sock_depth": 2.2}
PEG_PACK = {"d": 2.0, "len": 2.5, "sock_depth": 2.7}
PLINTH_T = 1.1                  # the figure's integral footplate, sunk flush into the base recess


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
    def __init__(self, pelvis=(0, 0, 17.4), yaw=0.0, lean=6.0, twist=0.0, tilt=0.0,
                 ankles=((-2.0, 0.6, ANKLE_H), (2.0, -0.6, ANKLE_H)), feet_yaw=(-8.0, 8.0),
                 fists=((-5.2, -1.0, 15.8), (5.2, -1.0, 15.8)),
                 elbow_poles=((-1, 1.2, -0.4), (1, 1.2, -0.4)), knee_poles=((0, -1, 0), (0, -1, 0)), head_yaw=0.0):
        self.pelvis = v3(pelvis)
        self.Rp = rot(Z, yaw)
        self.Rc = self.Rp @ rot(Z, twist) @ rot((0, 1, 0), tilt) @ rot((1, 0, 0), lean)
        self.Rmid = self.Rp @ rot(Z, twist / 2) @ rot((1, 0, 0), lean / 2)
        Rc, Rp = self.Rc, self.Rp
        self.fwd = Rp @ v3(0, -1, 0)
        self.cfwd = Rc @ v3(0, -1, 0)
        self.chest = self.pelvis + self.Rmid @ v3(0, 0.15, SPINE * 0.45) + Rc @ v3(0, 0, SPINE * 0.55)
        self.neck = self.chest + Rc @ v3(0, 0.25, NECK)
        self.cut_z = float(self.neck[2] + GORGET_UP)
        self.neck_cut = v3(self.neck[0], self.neck[1], self.cut_z)
        self.head_yaw = head_yaw + math.degrees(math.atan2(self.cfwd[0], -self.cfwd[1]))
        self.head = self.neck_cut + v3(0, 0, HEAD_UP)
        self.sh = [self.chest + Rc @ v3(s * SH_W, 0.35, SH_UP) for s in (-1, 1)]       # 0 = right (-x), 1 = left
        self.hip = [self.pelvis + Rp @ v3(s * HIP_W, 0.1, -0.55) for s in (-1, 1)]
        self.ankle = [v3(a) for a in ankles]
        self.feet_yaw = feet_yaw
        self.knee = [ik(self.hip[i], self.ankle[i], L_THIGH, L_SHIN, Rp @ v3(knee_poles[i])) for i in range(2)]
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


# ------------------------------------------------------------------------------------------------ body
def figure(pose, h=0.085, extras=(), bbox=None):
    """The armoured body without helm and backpack. extras: callables(sculpt, pose) for hands, weapons and gear."""
    P = pose
    lo, hi = bbox or ((-9.5, -14.0, -PLINTH_T - 0.2), (9.5, 7.5, P.cut_z + 3.2))
    g = Sculpt(lo, hi, h)
    Rc, Rp, Rm = P.Rc, P.Rp, P.Rmid
    up_c = Rc @ Z

    # ---------------- bodysuit: smooth anatomical masses
    pelvis = ellipsoid(P.pelvis + Rp @ v3(0, 0.1, 0.25), (2.45, 1.85, 2.0), Rp)
    abdomen = ellipsoid(P.pelvis + Rm @ v3(0, 0.05, 2.75), (2.95, 2.15, 2.5), Rm)
    ribs = ellipsoid(P.chest + Rc @ v3(0, 0.05, 0.3), (4.0, 2.75, 3.2), Rc)
    lats = ellipsoid(P.chest + Rc @ v3(0, 0.55, -1.0), (3.6, 2.05, 2.6), Rc)
    for s in (pelvis, abdomen, ribs, lats):
        g.add(s, 0.9)
    for i, sgn in ((0, -1), (1, 1)):
        g.add(round_cone(P.neck + Rc @ v3(0, 0.1, -0.3), P.sh[i] + Rc @ v3(-sgn * 0.3, 0, 0.2), 1.25, 0.9), 0.7)  # trapezius
        g.add(sphere(P.sh[i], 1.45), 0.6)                                                                         # deltoid
        g.add(ellipsoid(P.hip[i] + Rp @ v3(-sgn * 0.25, 0.6, 0.3), (1.15, 0.85, 1.2), Rp), 0.5)                   # glute
    g.add(capsule(P.neck + Rc @ v3(0, 0, -1.0), P.neck + v3(0, 0, GORGET_UP + 0.9), 1.02), 0.4)

    for i in range(2):
        hip, knee, ank = P.hip[i], P.knee[i], P.ankle[i]
        ax = knee - hip
        R = frame(ax, P.fwd)
        g.add(round_cone(hip + v3(0, 0, 0.3), knee, 1.75, 1.25), 0.7)                                  # thigh
        g.add(ellipsoid(hip + ax * 0.45 + R[:, 1] * 0.3, (1.3, 1.2, 2.6), R), 0.5)                     # quads
        sx = ank - knee
        Rs = frame(sx, P.fwd)
        g.add(round_cone(knee, ank, 1.22, 0.85), 0.5)                                                 # shin
        g.add(ellipsoid(knee + sx * 0.32 - Rs[:, 1] * 0.45, (1.05, 1.1, 2.2), Rs), 0.5)                # calf
    for i in range(2):
        sh, el, wr = P.sh[i], P.elbow[i], P.wrist[i]
        ua, fa = el - sh, wr - el
        g.add(round_cone(sh, el, 1.3, 1.0), 0.5)
        g.add(ellipsoid(sh + ua * 0.5, (1.25, 1.2, 1.95), frame(ua, P.cfwd)), 0.5)                    # biceps / triceps
        g.add(round_cone(el, wr, 1.1, 0.82), 0.45)
        g.add(ellipsoid(el + fa * 0.3, (1.15, 1.08, 1.6), frame(fa, P.cfwd)), 0.4)                    # forearm mass

    # ---------------- bodysuit ribbing (flex panels) at the waist
    for t in (1.6, 2.35, 3.1):
        g.cut(groove(abdomen, P.pelvis + Rm @ v3(0, 0, t), Rm @ Z, 0.38, 0.22))

    # ---------------- armour plates: the body offset outward, cut to an oval outline (plate()) or by planes
    cuirass = ribs.offset(0.4).clip(half(P.chest + Rc @ v3(0, 0, -2.05), -up_c), half(P.chest + Rc @ v3(0, 0, 2.9), up_c),
                                    half(P.chest + Rc @ v3(0, -3.0, 0), Rc @ unit((0.36, -1, 0.12))),
                                    half(P.chest + Rc @ v3(0, -3.0, 0), Rc @ unit((-0.36, -1, 0.12))))   # two chest facets
    g.add(cuirass, 0.15)
    g.add(round_cone(P.chest + Rc @ v3(0, -3.05, 2.0), P.chest + Rc @ v3(0, -2.95, -1.9), 0.4, 0.34), 0.1)  # keel
    g.add(ellipsoid(P.chest + Rc @ v3(0, 2.2, 0.6), (3.1, 1.0, 2.4), Rc), 0.2)                              # back plate
    abs_plate = plate(abdomen, 0.38, P.pelvis + Rm @ v3(0, -2.0, 2.9), (1.45, 1.4, 1.45), Rm)
    g.add(abs_plate, 0.1)
    g.cut(groove(abdomen.offset(0.38), P.pelvis + Rm @ v3(0, 0, 2.85), Rm @ Z, 0.4, 0.3))
    # gorget: a collar ring, taller at the back
    g.add(torus(P.neck + Rc @ v3(0, 0.1, 0.05), up_c, 1.55, 0.55), 0.25)
    g.add(ellipsoid(P.neck + Rc @ v3(0, 1.05, 0.15), (1.7, 0.6, 0.85), Rc), 0.2)
    # belt with a buckle plate, codpiece and side tassets conforming to the pelvis
    g.add(torus(P.pelvis + Rp @ v3(0, 0.1, 1.1), Rp @ Z, 2.5, 0.42), 0.25)
    g.add(rbox(P.pelvis + Rp @ v3(0, -2.4, 1.05), (0.85, 0.35, 0.55), Rp, 0.25), 0.1)
    g.add(plate(pelvis, 0.4, P.pelvis + Rp @ v3(0, -2.0, -0.3), (1.15, 1.2, 1.35), Rp), 0.1)
    g.add(plate(pelvis, 0.38, P.pelvis + Rp @ v3(0, 2.0, 0.55), (1.9, 1.2, 1.15), Rp), 0.1)                   # kidney plate
    for i, sgn in ((0, -1), (1, 1)):
        g.add(plate(pelvis, 0.36, P.pelvis + Rp @ v3(sgn * 2.5, -0.3, -0.1), (0.95, 1.35, 1.3), Rp), 0.1)

    # shoulder plates: two layered caps that hug the deltoid and sweep back (a soldier's shoulder, not a pauldron)
    for i, sgn in ((0, -1), (1, 1)):
        sh = P.sh[i]
        out, up = Rc @ v3(sgn, 0, 0), up_c
        Rs = Rc @ rot((0, 1, 0), -sgn * 35)
        cap = plate(sphere(sh + out * 0.25 + up * 0.15, 1.6), 0.45, sh + out * 0.9 + up * 1.15 + Rc @ v3(0, 0.25, 0),
                    (2.05, 2.25, 1.55), Rs)
        Rl = Rc @ rot((0, 1, 0), -sgn * 60)
        low = plate(sphere(sh + out * 0.45 - up * 0.45, 1.5), 0.32, sh + out * 1.75 - up * 0.65 + Rc @ v3(0, 0.3, 0),
                    (1.25, 1.95, 1.3), Rl)
        g.add(low, 0.08)
        g.add(cap, 0.08)
        g.add(round_cone(sh + out * 0.4 + up * 2.0 + Rc @ v3(0, -0.9, 0), sh + out * 0.75 + up * 1.75 + Rc @ v3(0, 1.6, 0), 0.3, 0.26), 0.12)  # ridge

    # arms: outer biceps plate, elbow cop, bracer on the back of the forearm
    for i, sgn in ((0, -1), (1, 1)):
        sh, el, wr = P.sh[i], P.elbow[i], P.wrist[i]
        ua, fa = el - sh, wr - el
        o = Rc @ v3(sgn, 0, 0)
        out = unit(o - unit(ua) * (o @ unit(ua)))
        Ru = np.stack([np.cross(out, unit(ua)), out, unit(ua)], axis=1)
        g.add(plate(round_cone(sh, el, 1.3, 1.0), 0.3, sh + ua * 0.55 + out * 1.3, (1.25, 1.2, 1.55), Ru), 0.1)
        ep = el - (sh + wr) / 2
        ep = unit(ep) if np.linalg.norm(ep) > 0.3 else -P.cfwd
        g.add(ellipsoid(el + ep * 0.5, (0.85, 0.85, 1.0), frame(ua, ep)), 0.15)
        back = unit(out - unit(fa) * (out @ unit(fa)))
        Rf = np.stack([np.cross(back, unit(fa)), back, unit(fa)], axis=1)
        fore = round_cone(el, wr, 1.1, 0.82)
        g.add(plate(fore, 0.32, el + fa * 0.55 + back * 1.0, (1.35, 1.4, 2.1), Rf), 0.1)
        g.cut(groove(fore.offset(0.32), el + fa * 0.6, unit(fa), 0.4, 0.25))

    # legs: front and outer thigh plates, knee guard, greave with a shin ridge, boots
    for i, sgn in ((0, -1), (1, 1)):
        hip, knee, ank = P.hip[i], P.knee[i], P.ankle[i]
        ax = knee - hip
        R = frame(ax, P.fwd)
        w = R[:, 1]
        o = P.Rp @ v3(sgn, 0, 0)
        thigh = round_cone(hip + v3(0, 0, 0.3), knee, 1.75, 1.25)
        g.add(plate(thigh, 0.36, hip + ax * 0.5 + w * 1.6, (1.35, 1.5, 3.0), R), 0.1)                 # front
        out = unit(o - unit(ax) * (o @ unit(ax)))
        Ro = np.stack([np.cross(out, unit(ax)), out, unit(ax)], axis=1)
        g.add(plate(thigh, 0.3, hip + ax * 0.32 + out * 1.6, (1.3, 1.4, 2.2), Ro), 0.1)               # outer, layered
        g.add(plate(thigh, 0.28, hip + ax * 0.58 - w * 1.5, (1.2, 1.3, 2.1), R), 0.1)                 # hamstring guard
        kp = knee - (hip + ank) / 2
        kp = unit(kp) if np.linalg.norm(kp) > 0.4 else w
        kp = unit(kp + w * 0.6)
        sx = ank - knee
        ns = unit(sx)
        Rs = frame(sx, kp)
        g.add(ellipsoid(knee + kp * 0.9 + ns * 0.25, (0.95, 0.72, 1.4), Rs).clip(
            half(knee + kp * 1.4, unit(kp - ns * 0.6))), 0.15)                                           # knee guard, pointed
        shin = round_cone(knee, ank, 1.22, 0.85)
        g.add(plate(shin, 0.4, knee + sx * 0.55 + Rs[:, 1] * 1.2, (1.35, 1.35, 3.4), Rs), 0.1)          # greave
        g.add(plate(shin, 0.3, knee + sx * 0.33 - Rs[:, 1] * 1.4, (1.15, 1.2, 1.7), Rs), 0.1)          # calf guard
        g.add(round_cone(knee + sx * 0.3 + Rs[:, 1] * 1.5, ank + Rs[:, 1] * 1.2 + v3(0, 0, 0.5), 0.32, 0.28), 0.15)
        # boot
        fd = unit(rot(Z, P.feet_yaw[i]) @ P.fwd)
        side = np.cross(fd, Z)
        Rf = np.stack([side, fd, Z], axis=1)
        boot = rbox(ank + fd * 0.85 + v3(0, 0, -0.95), (1.25, 2.45, 0.8), Rf, 0.45)
        boot = boot | ellipsoid(ank + fd * 2.35 + v3(0, 0, -0.85), (1.2, 1.25, 0.85), Rf)          # toe cap
        boot = boot | round_cone(ank + v3(0, 0, -0.9), ank + v3(0, 0, 0.9), 1.2, 1.08)               # ankle cuff
        g.add(boot.clip(half(v3(0, 0, 0), -Z)), 0.3)
        g.cut(groove(boot, ank + v3(0, 0, -1.1), Z, 0.38, 0.25))  # sole line (on the unclipped boot: clip planes fool groove())

    # ---------------- hands, weapons and gear
    for fn in extras:
        fn(g, P)

    # ---------------- joints: plinth, neck socket, backpack boss and socket
    plinth(g, P)
    g.cut(cyl(P.neck_cut, P.neck_cut + v3(0, 0, 8), 1.6))                                            # neck stump above the cut
    g.cut(d_peg(P.neck_cut + v3(0, 0, 0.01), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["sock_depth"], key=P.key_dir(), grow=0.1))
    mount = pack_mount(P)
    g.add(rbox(mount - Rc @ v3(0, 0.5, 0), (1.55, 0.5, 1.8), Rc, 0.3), 0.15)                          # backpack boss
    g.cut(d_peg(mount + Rc @ v3(0, 0.01, 0), Rc @ v3(0, -1, 0), PEG_PACK["d"], PEG_PACK["sock_depth"], key=Rc @ Z, grow=0.1))
    return g


def pack_mount(P):
    """Centre of the flat backpack mounting face on the back plate."""
    return P.chest + P.Rc @ v3(0, 3.55, 0.55)


def plinth(g, P):
    """Integral footplate under the feet, PLINTH_T thick, top at z = 0; its outline keys it into the base recess."""
    g.add(plinth_shape(P).clip(half(v3(0, 0, 0), Z), half(v3(0, 0, -PLINTH_T), -Z)), 0.2)


def plinth_shape(P, grow=0.0):
    """Stadium joining the two feet plus a key lobe behind the right foot (vertical prism, any z)."""
    pts = [P.ankle[i] + rot(Z, P.feet_yaw[i]) @ P.fwd * 0.9 for i in range(2)]
    a, b = v3(pts[0][0], pts[0][1], 0), v3(pts[1][0], pts[1][1], 0)
    k = P.ankle[0] + P.Rp @ v3(-1.4, 2.6, 0)
    k = v3(k[0], k[1], 0)
    r, rk = 2.75 + grow, 1.5 + grow
    ab = b - a
    L2 = float(ab @ ab)

    def f(Q):
        q = Q.copy()
        q[:, 2] = 0
        t = np.clip(((q - a) @ ab) / L2, 0, 1)
        d1 = np.linalg.norm(q - (a + np.outer(t, ab)), axis=1) - r
        d2 = np.linalg.norm(q - k, axis=1) - rk
        return np.minimum(d1, d2)

    lo = np.minimum(np.minimum(a, b) - r, k - rk)
    hi = np.maximum(np.maximum(a, b) + r, k + rk)
    return Shape(f, v3(lo[0], lo[1], -20), v3(hi[0], hi[1], 20))


# ------------------------------------------------------------------------------------------------ hands
def fist(g, center, grip_axis, forearm_dir, k=0.25):
    """Gauntleted fist closed around a grip running along grip_axis (the held part passes through it)."""
    c = v3(center)
    n = unit(grip_axis)
    fa = unit(forearm_dir)
    w = unit(fa - n * (fa @ n))
    u = np.cross(w, n)
    R = np.stack([u, w, n], axis=1)
    g.add(rbox(c, (0.68, 0.82, 0.9), R, 0.48), k)
    g.add(rbox(c + w * 0.35 + u * 0.15, (0.5, 0.5, 0.86), R, 0.3), 0.1)                               # knuckle plate
    g.add(capsule(c - w * 0.3 - n * 0.75 + u * 0.35, c + w * 0.1 - n * 0.55 - u * 0.55, 0.32), 0.15)  # thumb


def open_hand(g, center, point_dir, palm_normal, sgn):
    """Pointing hand: palm block, index finger extended, the rest curled."""
    c, d, pn = v3(center), unit(point_dir), unit(palm_normal)
    side = np.cross(pn, d)
    R = np.stack([side, pn, d], axis=1)
    g.add(rbox(c, (0.75, 0.5, 0.8), R, 0.35), 0.25)
    g.add(capsule(c + d * 0.7 + side * 0.42 * sgn, c + d * 2.1 + side * 0.48 * sgn, 0.34), 0.12)        # index
    g.add(rbox(c + d * 0.8 + pn * 0.25 - side * 0.15 * sgn, (0.55, 0.45, 0.42), R, 0.3), 0.15)          # curled fingers
    g.add(capsule(c - side * 0.55 * sgn + d * 0.1, c - side * 0.75 * sgn + d * 0.8 + pn * 0.2, 0.3), 0.12)  # thumb


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
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.02), 0.4)                                         # neck seal
    # chevron visor: two lenses in a V, recessed
    for s in (-1, 1):
        g.cut(rbox(H(s * 1.0, -2.55, 0.12), r(1.05, 0.65, 0.3), rot((0, 1, 0), s * 24), 0.12))
    # keel crest from the brow over the dome to the nape (continues the cuirass keel)
    crest = [H(0, 0.25, 0.25) + HS * v3(0, -2.55 * math.cos(a) * 1.04, 2.55 * math.sin(a) * 1.04)
             for a in np.radians(np.linspace(25, 160, 12))]
    g.add(tube(crest, 0.32), 0.15)
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
        g.cut(rbox(H(0, -2.9, 0.2), r(1.35, 0.6, 0.22), np.eye(3), 0.1))
        g.add(rbox(H(0, -2.55, -0.9), r(0.9, 0.35, 0.18), np.eye(3), 0.12), 0.1)
    elif variant == "seeker":
        g.add(cyl(H(1.05, -1.9, 0.75), H(1.25, -3.3, 0.85), 0.6 * HS, 0.15), 0.15)
        g.cut(cyl(H(1.24, -3.4, 0.85), H(1.2, -2.9, 0.85), 0.33 * HS))
        g.add(capsule(H(1.0, -1.5, 0.8), H(2.2, -0.2, 0.3), 0.34), 0.15)
    g.cut(Shape(lambda Q: Q[:, 2], (-9, -9, -9), (9, 9, 0)))                                       # flat seat at z = 0
    g.add(d_peg((0, 0, 0.3), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["len"] + 0.3, key=(0, -1, 0)))
    return g


# ------------------------------------------------------------------------------------------------ backpacks
def backpack(variant="power", h=0.06):
    """Separate pack in its own frame: front face on y = 0 (against the back boss), peg toward -y, up z."""
    lo = (-6.9 if variant == "jump" else -4.6, -PEG_PACK["len"] - 0.3, -6.2)
    hi = {"comms": (4.6, 5.2, 10.2), "jump": (6.9, 5.0, 4.5)}.get(variant, (4.6, 5.0, 4.5))
    g = Sculpt(lo, hi, h)
    g.add(rbox(v3(0, 1.15, 0.2), (2.25, 1.15, 2.9), np.eye(3), 0.7))                                     # core
    g.add(rbox(v3(0, 2.2, 0.6), (1.6, 0.8, 2.1), np.eye(3), 0.5), 0.25)                                   # cell
    g.add(round_cone(v3(0, 3.0, 2.6), v3(0, 3.0, -1.6), 0.4, 0.38), 0.12)                                 # keel spine
    for j in range(3):
        g.cut(rbox(v3(0.0, 3.05, -0.8 + j * 0.9), (1.7, 0.55, 0.21), np.eye(3), 0.08))                     # vents
    if variant == "power":
        for s in (-1, 1):
            d = unit((s * 0.35, 0.45, -1))
            n0 = v3(s * 1.55, 1.3, -2.6)
            g.add(round_cone(n0, n0 + d * 1.8, 0.75, 0.95), 0.3)
            g.cut(round_cone(n0 + d * 0.9, n0 + d * 2.4, 0.35, 0.62))
    elif variant == "jump":
        for s in (-1, 1):
            a, b = v3(s * 2.3, 1.4, 1.2), v3(s * 3.3, 2.1, -3.2)
            g.add(round_cone(a, b, 0.95, 1.2), 0.4)
            g.cut(round_cone(b - unit(b - a) * 0.9, b + unit(b - a) * 0.8, 0.45, 0.8))
            g.add(rbox(v3(s * 4.6, 1.6, 1.6), (1.9, 0.32, 0.75), rot((0, 1, 0), -s * 35) @ rot(Z, s * 12), 0.3), 0.3)
    elif variant == "comms":
        g.add(cyl(v3(-1.2, 1.4, 2.4), v3(-1.2, 1.4, 3.4), 0.55, 0.15), 0.15)
        g.add(capsule(v3(-1.2, 1.4, 3.2), v3(-1.6, 2.4, 9.0), 0.42), 0.1)                                   # antenna
        g.add(sphere(v3(-1.6, 2.4, 9.0), 0.55), 0.1)
        g.add(rbox(v3(1.2, 1.5, 2.6), (0.6, 0.6, 0.6), np.eye(3), 0.3), 0.2)
        for s in (-1, 1):
            g.add(round_cone(v3(s * 1.4, 1.2, -2.4), v3(s * 1.55, 1.6, -3.6), 0.7, 0.8), 0.3)
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


# ------------------------------------------------------------------------------------------------ weapons
def lance_rifle():
    """'Lance' bullpup rifle, local: origin at the pistol-grip centre (fist centre), x toward the muzzle, z up.
    Heroic: about 13 mm long and 2 mm deep in the receiver, so it reads at arm's length and survives handling."""
    s = rbox(v3(0.6, 0, 1.0), (3.2, 0.62, 0.95), np.eye(3), 0.3)                           # receiver
    s = s | rbox(v3(5.0, 0, 1.15), (1.9, 0.55, 0.62), np.eye(3), 0.25).clip(half(v3(6.6, 0, 1.75), unit((1, 0, 0.8))))  # shroud
    s = s | cyl(v3(6.4, 0, 1.15), v3(8.2, 0, 1.15), 0.42, 0.1)                             # barrel
    s = s | cyl(v3(7.9, 0, 1.15), v3(8.7, 0, 1.15), 0.58, 0.18)                            # muzzle brake
    s = s | rbox(v3(-3.6, 0, 0.85), (0.9, 0.5, 1.0), rot((0, 1, 0), 8), 0.3)               # stock
    s = s | rbox(v3(0.9, 0, 2.25), (1.3, 0.42, 0.4), np.eye(3), 0.18)                      # optic
    s = s | cyl(v3(2.25, 0, 2.25), v3(2.5, 0, 2.25), 0.5, 0.1)                             # optic lens hood
    s = s | rbox(v3(0, 0, -0.35), (0.42, 0.42, 0.85), rot((0, 1, 0), -14), 0.2)            # grip
    s = s | rbox(v3(-1.9, 0, -0.3), (0.6, 0.5, 0.85), rot((0, 1, 0), 10), 0.2)             # magazine (bullpup)
    s = s | rbox(v3(2.6, 0, 0.05), (0.38, 0.38, 0.7), rot((0, 1, 0), -8), 0.18)           # fore grip
    return s


def maul_cannon():
    """'Maul' heavy arc-cannon, local: origin at the rear grip centre, x toward the muzzle, z up."""
    s = rbox(v3(1.6, 0, 1.2), (3.6, 1.05, 1.15), np.eye(3), 0.45)                           # body
    s = s | cyl(v3(-2.6, 0, 1.4), v3(-0.9, 0, 1.4), 1.35, 0.35)                             # capacitor drum
    s = s | rbox(v3(6.0, 0, 1.3), (1.6, 0.95, 0.95), np.eye(3), 0.4)                        # coil housing
    for a in (90, 210, 330):                                                                 # three emitter rails
        o = v3(0, 0.55 * math.cos(math.radians(a)), 1.3 + 0.55 * math.sin(math.radians(a)))
        s = s | cyl(v3(7.0, 0, 0) + o, v3(10.2, 0, 0) + o, 0.38, 0.1)
    s = s | torus(v3(9.0, 0, 1.3), (1, 0, 0), 0.6, 0.3) | torus(v3(10.0, 0, 1.3), (1, 0, 0), 0.6, 0.3)
    s = s | rbox(v3(0, 0, -0.15), (0.4, 0.38, 0.85), rot((0, 1, 0), -10), 0.18)             # rear grip
    s = s | capsule(v3(2.2, 0, 2.5), v3(4.6, 0, 2.5), 0.38) | capsule(v3(2.2, 0, 2.5), v3(1.9, 0, 1.9), 0.38) \
        | capsule(v3(4.6, 0, 2.5), v3(4.9, 0, 1.9), 0.38)                                     # carry handle
    return s


def sidearm():
    """'Spur' sidearm, local: origin at the grip centre, x toward the muzzle."""
    s = rbox(v3(0.9, 0, 0.95), (1.65, 0.4, 0.5), np.eye(3), 0.18)
    s = s | cyl(v3(2.4, 0, 1.05), v3(3.1, 0, 1.05), 0.32, 0.08)
    s = s | rbox(v3(0, 0, 0.1), (0.36, 0.34, 0.75), rot((0, 1, 0), -16), 0.16)
    return s


# ------------------------------------------------------------------------------------------------ base
BASE = {"d": 32.0, "h": 4.0, "top_inset": 1.0, "magnet": "5x2", "pocket_d": 5.2, "pocket_depth": 2.1, "vent_w": 1.0,
        "vent_d": 0.6, "recess_clearance": 0.1}


def base32(P, seed=1, h=0.08):
    """32 mm round deck-plate base: bevelled rim, engraved deck panels, a hatch and rubble; a recess that takes the
    figure's footplate (outline keyed, 0.1 mm glue clearance per side) and a 5 x 2 mm magnet pocket vented to the rim."""
    rng = np.random.default_rng(seed)
    R0, H0, inset = BASE["d"] / 2, BASE["h"], BASE["top_inset"]
    g = Sculpt((-R0, -R0, 0), (R0, R0, H0 + 2.2), h)
    k = inset / H0

    def body(Q):
        rr = np.hypot(Q[:, 0], Q[:, 1])
        side = (rr - (R0 - k * np.clip(Q[:, 2], 0, H0))) / math.sqrt(1 + k * k)
        return np.maximum(side, np.maximum(-Q[:, 2], Q[:, 2] - H0))
    disc = Shape(body, (-R0, -R0, 0), (R0, R0, H0))
    g.add(disc)
    top = Shape(lambda Q: np.maximum(body(Q), H0 - 0.6 - Q[:, 2]), (-R0, -R0, H0 - 0.6), (R0, R0, H0))
    # deck panels: a rotated grid of engraved seams (0.45 wide, 0.4 deep), inside the rim
    ang = rng.uniform(0, 90)
    Rg = rot(Z, ang)
    for t in (-9.0, -3.2, 2.6, 8.4):
        for ax in (0, 1):
            n = Rg[:, ax]
            seam = Shape(lambda Q, n=n, t=t: np.abs(Q @ n - t) - 0.225, (-R0, -R0, H0 - 1), (R0, R0, H0 + 1))
            g.cut((seam & top).clip(Shape(lambda Q: np.hypot(Q[:, 0], Q[:, 1]) - (R0 - inset - 0.6), (-R0,) * 3, (R0,) * 3)))
    # hatch plate with rivets, a conduit and rubble
    hc = Rg @ v3(-8.5, 5.5, 0)
    g.add(rbox(v3(hc[0], hc[1], H0 + 0.2), (2.6, 1.9, 0.45), Rg, 0.25), 0.1)
    for dx in (-2.0, 2.0):
        for dy in (-1.4, 1.4):
            q = hc + Rg @ v3(dx, dy, 0)
            g.add(sphere(v3(q[0], q[1], H0 + 0.62), 0.32), 0.05)
    a, b = Rg @ v3(6.0, -11.5, 0), Rg @ v3(11.0, 1.0, 0)
    g.add(tube([v3(a[0], a[1], H0 + 0.05), v3((a[0] + b[0]) / 2 + 1.0, (a[1] + b[1]) / 2, H0 + 0.35), v3(b[0], b[1], H0 + 0.05)], 0.48), 0.15)
    for _ in range(3):
        rr, th = rng.uniform(8.5, 12.0), rng.uniform(0, 2 * math.pi)
        q = v3(rr * math.cos(th), rr * math.sin(th), H0 + 0.15)
        if any(np.hypot(*(q[:2] - P.ankle[i][:2])) < 5.0 for i in range(2)):
            continue
        g.add(rbox(q, tuple(rng.uniform(0.5, 1.1, 3)), rot(unit(rng.normal(size=3)), rng.uniform(0, 90)), 0.15), 0.1)
    # recess for the footplate, magnet pocket and vent
    rec = plinth_shape(P, BASE["recess_clearance"]).clip(half(v3(0, 0, H0 + 3), Z), half(v3(0, 0, H0 - PLINTH_T), -Z))
    g.cut(rec)
    g.cut(cyl(v3(0, 0, -1), v3(0, 0, BASE["pocket_depth"]), BASE["pocket_d"] / 2))
    g.cut(rbox(v3(R0 / 2, 0, 0), (R0 / 2 + 1, BASE["vent_w"] / 2, BASE["vent_d"]), np.eye(3), 0.0))
    return g
