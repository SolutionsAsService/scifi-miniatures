"""VH2 helm library: the Vigil Mk 2 helm profile (original design) for the Aster Compact Vigilant line.

The VH-01..10 helms in tools/armory.py and tools/exosuit.py are untouched; this module is the second-generation profile.

Signature profile (what makes a VH2 helm read as Vigil at arm's length):
- GULL-WING VISOR: the split chevron of VH-01 grown into one wrap-around faceted visor whose two wings sweep UP and BACK
  to the temples while the lower edge drops into a V at the centre. A vertical KEEL BAR splits the wings; the visor glass
  is two-faceted (an upper facet 0.17 mm proud of the lower one) inside a raised 0.3 mm frame.
- KEEL LINE: one continuous ridge from the crest over the crown, down through the visor split, onto the V-prow
  respirator and its chin puck.
- LAYERED SHELL: a central crown plate (0.25 mm) over side temple plates (0.13 mm) over the skull dome, and two stepped
  nape tiers; the crown plate's front edge is the brow and follows the visor's top edge.
- V-PROW JAW with chevron vent slots that echo the visor's lower edge; cheek guards with vertical vent slots;
  aural housings with a recessed disc and a breather hose running to the jaw.

How it differs from the references (inspiration only): Halo/ODST visors are one rounded trapezoid or band with a flat or
arched top edge and no split; the Spartan visor is a single gold bubble; the Space Marine helm has two separate round
eye lenses over a beaked, slotted grille. The VH2 visor is a single wrap that is SPLIT by a keel bar and shaped like a
gull wing (outer tips rising, centre falling), set under a stepped brow plate, with a faceted V-prow below - none of the
reference silhouettes uses a rising-tip wing or a continuous crest-to-chin keel.

Frame (same as every Vigil helm): neck cut at z = 0, 1.6 mm D-flat peg down (exosuit.PEG_HEAD), faces -y, mm.
Coordinates: H(x, y, z) is a helm-local point in helm units (x HS = 1.12 mm); visor outlines are polygons in
(s, z) where s is the arc length about the skull's vertical axis (s = R0 * azimuth), so outlines wrap round the skull.
Feature floor: raised features >= 0.5 mm wide, engraved slots >= 0.28 mm wide and 0.25-0.35 mm deep, ribs between slots
>= 0.38 mm, antennas >= 0.76 mm diameter.
"""
from __future__ import annotations

import math

import numpy as np

from exosuit import HEAD_UP, HS, PEG_HEAD, RY, Z
from sdfkit import Sculpt, Shape, capsule, cyl, d_peg, ellipsoid, half, rbox, rot, round_cone, sphere, torus, tube, unit, v3

RX = (1, 0, 0)
HC = v3(0, 0, HEAD_UP)
SK_C = (0.0, 0.25, 0.3)        # skull centre, helm units
SK_R = (2.15, 2.5, 2.5)        # skull radii (y and z equal: a rotation about x through SK_C maps the skull onto itself)
R0 = 2.4                       # radius used for the visor arc-length coordinate
ALL = ((-20, -20, -20), (20, 20, 20))


def H(x, y, z):
    return HC + HS * v3(x, y, z)


def r(*a):
    return tuple(HS * x for x in a)


SKULL = ellipsoid(H(*SK_C), r(*SK_R))


def surf(s, zl, extra=0.0):
    """Point on the skull at visor coordinates (s, zl), pushed out along the radius by extra mm."""
    t = s / R0
    k = math.sqrt(max(1e-3, 1 - ((zl - SK_C[2]) / SK_R[2]) ** 2))
    a, b = SK_R[0] * k, SK_R[1] * k
    dx, dy = math.sin(t), -math.cos(t)
    rad = 1 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2) + extra / HS
    return H(dx * rad, SK_C[1] + dy * rad, zl)


def crest_pt(a_deg, lift=0.3):
    """Point on the skull's mid-plane at angle a from the front (0 = front, 90 = top, 180 = back), lifted by lift mm."""
    a = math.radians(a_deg)
    return H(0, SK_C[1] - SK_R[1] * math.cos(a), SK_C[2] + SK_R[2] * math.sin(a)) + v3(0, -math.cos(a), math.sin(a)) * lift


def snorm(s, zl):
    p = (surf(s, zl) - HC) / HS - v3(SK_C)
    return unit(p / np.array(SK_R) ** 2)


def _loc(Q):
    q = (Q - HC) / HS
    th = np.arctan2(q[:, 0], -(q[:, 1] - SK_C[1]))
    return q, th


def sd_polygon(p, V):
    """Signed distance from 2D points p (N, 2) to the polygon V (M, 2) (negative inside), vectorised iq sdPolygon."""
    d = np.sum((p - V[0]) ** 2, axis=1)
    sgn = np.ones(len(p))
    for i in range(len(V)):
        vi, vj = V[i], V[i - 1]
        e = vj - vi
        w = p - vi
        b = w - np.outer(np.clip((w @ e) / (e @ e), 0, 1), e)
        d = np.minimum(d, np.sum(b * b, axis=1))
        c1, c2, c3 = p[:, 1] >= vi[1], p[:, 1] < vj[1], e[0] * w[:, 1] > e[1] * w[:, 0]
        sgn = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -sgn, sgn)
    return sgn * np.sqrt(d)


def wrap_prism(V):
    """Infinite prism of the (s, z) polygon V wrapped round the skull axis (front half), distance in mm."""
    V = np.asarray(V, float)

    def f(Q):
        q, th = _loc(Q)
        return HS * sd_polygon(np.stack([R0 * th, q[:, 2]], axis=1), V)
    th = min(np.abs(V[:, 0]).max() / R0 + 0.35, math.pi)
    ymax = HS * (SK_C[1] + 3.0 * max(0.0, -math.cos(th))) + 0.6
    lo = (-3.8, -4.4, HC[2] + HS * V[:, 1].min() - 0.8)
    hi = (3.8, ymax, HC[2] + HS * V[:, 1].max() + 0.8)
    return Shape(f, lo, hi)


def yz_prism(V, half_w):
    """Blade: the (y, z) polygon V (helm units) extruded +-half_w mm along x."""
    V = np.asarray(V, float)

    def f(Q):
        q = (Q - HC) / HS
        return np.maximum(HS * sd_polygon(q[:, 1:3], V), np.abs(Q[:, 0]) - half_w)
    lo = (-half_w, HS * V[:, 0].min(), HC[2] + HS * V[:, 1].min())
    hi = (half_w, HS * V[:, 0].max(), HC[2] + HS * V[:, 1].max())
    return Shape(f, lo, hi)


def mirror(right):
    """Symmetric outline from its right half (s >= 0, listed top-centre -> outer -> bottom-centre)."""
    return [(s, z) for s, z in right] + [(-s, z) for s, z in reversed(right) if s > 1e-9]


# the signature gull-wing visor (s, z), and the heavy (armoured, narrowed) version of it
VISOR = mirror([(0.0, 0.3), (1.2, 0.52), (2.3, 1.12), (2.8, 1.02), (2.6, 0.38), (1.35, 0.0), (0.0, -0.62)])
VISOR_HEAVY = mirror([(0.0, 0.3), (1.3, 0.45), (2.3, 0.72), (2.62, 0.62), (2.45, 0.3), (1.3, 0.12), (0.0, -0.25)])


# ------------------------------------------------------------------------------------------------ building blocks
class Helm:
    """One helm on its own grid; methods add the VH2 parts. top is the crown clearance in helm units."""

    def __init__(self, h=0.05, top=3.6, front=-4.4, side=3.7):
        self.g = Sculpt((-side, front, -PEG_HEAD["len"] - 0.3), (side, 3.9, HEAD_UP + HS * top), h)
        self.visor_poly = VISOR

    # -------------------------------------------------------------- shell
    def skull(self):
        g = self.g
        g.add(SKULL)
        g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                     # neck seal
        return self

    def plates(self, crown_t=0.25, temple_t=0.13, brow_lift=0.34, nape=True):
        g = self.g

        def crown(Q):
            q, th = _loc(Q)
            zb = np.interp(np.abs(th), [0, .5, .96, 1.2, 1.9, 2.5, math.pi], [-.12, .1, .7, .8, .85, -.4, -1.2]) + 0.42 + brow_lift
            return HS * np.maximum(zb - q[:, 2], np.abs(q[:, 0]) - 1.5)

        def temple(Q):
            q, th = _loc(Q)
            zl = np.where(np.abs(th) < 1.12, 9.0, np.interp(np.abs(th), [1.12, 1.35, math.pi], [1.15, -0.85, -0.85]))
            return HS * np.max(np.stack([zl - q[:, 2], q[:, 2] - 1.75, q[:, 1] - 1.55, 1.1 - np.abs(q[:, 0])]), axis=0)
        g.add(SKULL.offset(temple_t) & Shape(temple, *ALL))
        g.add(SKULL.offset(crown_t) & Shape(crown, *ALL))
        if nape:
            g.add(SKULL.offset(0.2).clip(half(H(0, 0.95, 0), (0, -1, 0)), half(H(0, 0, 0.05), Z), half(H(0, 0, -1.9), -Z)))
            g.add(SKULL.offset(0.34).clip(half(H(0, 1.35, 0), (0, -1, 0)), half(H(0, 0, -0.75), Z), half(H(0, 0, -1.9), -Z)))
        return self

    def crest(self, r_mm=0.3, a0=12, a1=168, lift=0.32):
        pts = [crest_pt(a, lift) for a in np.linspace(a0, a1, 14)]
        self.g.add(tube(pts, r_mm), 0.12)
        return self

    def blade_crest(self, prof, half_w=0.4):
        self.g.add(yz_prism(prof, half_w), 0.15)
        return self

    # -------------------------------------------------------------- face
    def jaw(self, kind="std"):
        g = self.g
        if kind == "std":
            g.add(ellipsoid(H(0, -1.35, -1.05), r(1.45, 1.2, 1.1), rot(RX, 10)), 0.5 * HS)
            prow = rbox(H(0, -1.35, -1.15), r(1.42, 1.15, 0.92), rot(RX, 8), 0.28 * HS)
            self.prow_apex, self.prow_slope = -2.4, 0.45
        elif kind == "heavy":
            g.add(ellipsoid(H(0, -1.4, -1.1), r(1.6, 1.3, 1.15), rot(RX, 10)), 0.5 * HS)
            prow = rbox(H(0, -1.5, -1.2), r(1.62, 1.3, 1.0), rot(RX, 6), 0.3 * HS)
            self.prow_apex, self.prow_slope = -2.75, 0.4
        else:  # sealed
            g.add(ellipsoid(H(0, -1.35, -1.05), r(1.5, 1.22, 1.12), rot(RX, 10)), 0.5 * HS)
            prow = ellipsoid(H(0, -1.45, -1.2), r(1.45, 1.15, 0.95), rot(RX, 8))
            self.prow_apex, self.prow_slope = -2.45, 0.38
        a, k = self.prow_apex, self.prow_slope
        prow = prow.clip(half(H(0, a, 0), unit((k, -1, 0))), half(H(0, a, 0), unit((-k, -1, 0))),
                         half(H(0, -2.25, -1.95), unit((0, -0.75, -1))))
        g.add(prow, 0.3)
        return self

    def facet_point(self, s, xl, zl, extra=0.0):
        """Point on the prow facet of side s (+1 = left, +x) at helm-unit x and z."""
        n = unit((s * self.prow_slope, -1, 0))
        p0 = H(0, self.prow_apex, 0)
        x = HS * xl
        y = p0[1] - n[0] * x / n[1]
        return v3(x, y, HC[2] + HS * zl) + n * extra, n

    def prow_vents(self, rows=(-0.85, -1.47), xl=0.85, length=0.4, w=0.15, depth=0.3, ang=12):
        g = self.g
        for s in (-1, 1):
            for zl in rows:
                p, n = self.facet_point(s, s * xl, zl)
                t = unit(np.cross(n, Z))
                if t[0] * s < 0:
                    t = -t
                d = unit(t * math.cos(math.radians(ang)) + Z * math.sin(math.radians(ang)))
                R = np.stack([d, n, np.cross(d, n)], axis=1)
                g.cut(rbox(p, (length, depth, w), R, 0.06))
        return self

    def chin_puck(self, rad=0.42, z=-1.3):
        g = self.g
        p, _ = self.facet_point(1, 0.0, z)
        n = unit((0, -1, -0.25))
        g.add(cyl(p - n * 0.25, p + n * 0.38, rad, 0.1), 0.08)
        g.cut(cyl(p + n * 0.2, p + n * 0.6, rad - 0.17))
        return self

    def keel(self, z0=0.55, z1=-1.0, r_mm=0.27):
        """Keel bar: splits the visor wings and runs down the prow apex."""
        pts = [surf(0, z, -0.05) for z in np.linspace(z0, -0.35, 4)]
        p, _ = self.facet_point(1, 0.0, z1)
        pts.append(p + v3(0, 0.02, 0))
        self.g.add(tube(pts, r_mm), 0.05)
        return self

    def cheeks(self, vents=3, dz=0.0, size=1.0):
        g = self.g
        for s in (-1, 1):
            c = H(s * 1.6, -1.05, -1.0 + dz)
            R = rot(Z, s * 24) @ rot(RY, -s * 12)
            g.add(rbox(c, r(0.42, 1.0 * size, 0.75 * size), R, 0.2 * HS), 0.12)
            face = c + R[:, 0] * s * (0.42 * HS)
            for j in range(vents):
                o = (j - (vents - 1) / 2) * 0.68
                g.cut(rbox(face + R[:, 1] * o, (0.25, 0.15, 0.42 * size), R, 0.06))
        return self

    def ears(self, hose=True, big=1.0):
        g = self.g
        for s in (-1, 1):
            a, b = H(s * 1.9, 0.15, -0.15), H(s * (2.4 + 0.1 * (big - 1)), 0.15, -0.15)
            g.add(cyl(a, b, 0.72 * HS * big, 0.15), 0.12)
            g.cut(cyl(b - v3(s * 0.2, 0, 0), b + v3(s * 0.5, 0, 0), 0.42 * HS * big))                   # recessed disc
            g.add(sphere(b - v3(s * 0.12, 0, 0), 0.26), 0.04)                                         # centre stud
            if hose:
                g.add(tube([H(s * 2.15, 0.05, -0.8), H(s * 1.95, -0.6, -1.45), H(s * 1.35, -1.55, -1.8)], 0.27), 0.1)
        return self

    # -------------------------------------------------------------- visor
    def visor(self, poly=None, depth=0.38, frame=0.26, frame_h=0.18, facet=True, sealed=False):
        g = self.g
        poly = poly or self.visor_poly
        P = wrap_prism(poly)
        g.add(P.offset(frame) & SKULL.offset(frame_h), 0.06)                                        # raised frame
        g.cut((P & SKULL.offset(0.9)) - SKULL.offset(-depth))                                       # glass recess
        if sealed:
            g.add(P.offset(-0.02) & SKULL.offset(0.16))                                              # sealed pane, bulged 0.16 mm
        elif facet:
            zc = float(np.asarray(poly)[:, 1].mean()) + 0.12

            def upper(Q):
                q, th = _loc(Q)
                return HS * (zc + 0.12 * np.abs(R0 * th) - q[:, 2])
            g.add(P.offset(-0.12) & SKULL.offset(-depth + 0.17) & Shape(upper, *ALL))              # upper glass facet
        self.P = P
        return self

    # -------------------------------------------------------------- gear
    def lamp(self, s=-1, zl=1.45, th=0.95, rad=0.4):
        g = self.g
        base = surf(s * R0 * th, zl, 0.05)
        fwd = unit(v3(s * 0.15, -1, 0.02))
        g.add(rbox(base + v3(0, -0.1, 0), (0.42, 0.55, 0.38), np.eye(3), 0.15), 0.08)
        g.add(cyl(base - fwd * 0.2, base + fwd * 0.75, rad, 0.08), 0.05)
        g.cut(cyl(base + fwd * 0.6, base + fwd * 1.2, rad - 0.16))
        return self

    def antenna(self, s=1, length=4.2, r_mm=0.38):
        g = self.g
        a = H(s * 2.25, 0.55, 0.3)
        b = a + unit(v3(s * 0.12, 0.35, 1)) * length
        g.add(cyl(a - v3(s * 0.35, 0, 0), a + v3(s * 0.15, 0, 0), 0.55, 0.12), 0.1)
        g.add(capsule(a, b, r_mm), 0.08)
        g.add(sphere(b, r_mm + 0.12), 0.05)
        return self

    def finish(self):
        g = self.g
        g.cut(Shape(lambda Q: Q[:, 2], (-9, -9, -9), (9, 9, 0)))                                     # flat seat at z = 0
        g.add(d_peg((0, 0, 0.3), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["len"] + 0.3, key=(0, -1, 0)))
        return g


# ------------------------------------------------------------------------------------------------ damage
def gouge(g, a, b, r_mm=0.22):
    g.cut(capsule(a, b, r_mm))


def pit(g, p, n, r_mm=0.3):
    g.cut(sphere(v3(p) + unit(n) * 0.12, r_mm))


def chunk(g, p, seed, size=0.55):
    rng = np.random.default_rng(seed)
    s = None
    for _ in range(3):
        b = rbox(v3(p) + rng.normal(0, 0.18, 3), tuple(rng.uniform(0.6, 1.0, 3) * size), rot(unit(rng.normal(size=3)), rng.uniform(0, 90)), 0.06)
        s = b if s is None else s | b
    g.cut(s)


def damage_line(hm, seed=7):
    """Battle damage for a line helm: two gouges over the crown, a crest notch, three pits, a cracked left wing."""
    g = hm.g
    gouge(g, surf(0.6, 2.5, 0.3), surf(3.4, 1.0, 0.3), 0.3)                                          # two claw-like gouges, left crown
    gouge(g, surf(0.9, 2.15, 0.3), surf(3.5, 0.55, 0.3), 0.26)
    gouge(g, surf(-2.3, 1.85, 0.25), surf(-4.6, 0.5, 0.25), 0.26)
    chunk(g, crest_pt(78, 0.55), seed, 0.55)                                                        # notch out of the crest
    for s, z in ((-1.9, 1.75), (-3.3, 0.9), (3.3, -0.3), (-0.6, 2.3)):
        pit(g, surf(s, z, 0.2), snorm(s, z), 0.32)
    c = surf(1.85, 0.5, -0.25)                                                                      # shattered left wing: crack star + lost shard
    for d in ((0.8, 0.5), (-0.85, 0.3), (0.2, -0.6), (-0.4, -0.55), (0.95, -0.15)):
        g.cut(capsule(c, surf(1.85 + d[0], 0.5 + d[1], -0.25), 0.16))
    chunk(g, surf(2.6, 0.95, 0.15), seed + 1, 0.4)                                                  # shard out of the frame corner
    pit(g, surf(1.85, 0.5, 0.0), snorm(1.85, 0.5), 0.3)


# ------------------------------------------------------------------------------------------------ the variants
def line(h=0.05, damaged=False):
    """VH2-01 Lineguard: the signature profile."""
    m = Helm(h).skull().plates().jaw("std").cheeks().ears().prow_vents().chin_puck().visor().keel().crest().lamp(-1)
    m.g.add(capsule(H(1.7, 1.6, 1.6), H(1.85, 2.3, 2.1), 0.36), 0.1)                                 # short aerial stub, left rear
    if damaged:
        damage_line(m)
    return m.finish()


def void(h=0.05):
    """VH2-02 Tidewall: sealed void/EVA helm - flush sealed pane in a heavy frame, collar ring with lugs, life-support hoses."""
    m = Helm(h).skull().plates().jaw("sealed").ears(hose=False, big=1.1).visor(frame=0.42, frame_h=0.3, sealed=True)
    m.keel(z1=-1.05, r_mm=0.25).crest(0.32)
    g = m.g
    g.add(torus(H(0, 0.15, -1.75), Z, 2.0 * HS, 0.32 * HS), 0.25)                                     # collar seal ring
    for a in (40, 140, 220, 320):
        t = math.radians(a)
        g.add(rbox(H(2.15 * math.cos(t), 0.15 + 2.15 * math.sin(t), -1.75), (0.38, 0.38, 0.45), rot(Z, a), 0.12), 0.08)  # lugs
    for s in (-1, 1):
        g.add(tube([H(s * 1.75, -1.75, -1.45), H(s * 2.2, -0.9, -1.35), H(s * 2.35, 0.4, -1.25), H(s * 1.7, 1.9, -1.05)], 0.3), 0.12)
        g.add(cyl(H(s * 1.45, -1.25, -1.4), H(s * 1.85, -2.0, -1.5), 0.42, 0.1), 0.08)               # hose sockets on the jaw corners
    g.add(cyl(H(0, -2.3, -1.4), H(0, -2.85, -1.55), 0.55, 0.12), 0.08)                                # purge valve
    g.cut(cyl(H(0, -2.75, -1.53), H(0, -3.2, -1.65), 0.32))
    g.add(rbox(H(0, 2.55, -0.4), r(0.75, 0.3, 0.55), np.eye(3), 0.15), 0.12)                           # rear O2 port
    for s in (-1, 1):
        g.add(capsule(H(s * 0.95, 1.8, 1.7), H(s * 1.05, 2.5, 2.5), 0.38), 0.1)                        # twin antenna stubs
    return m.finish()


def recon(h=0.05):
    """VH2-03 Lookout: recon helm with a hinged optic stalk over the left wing and a whip antenna."""
    m = Helm(h).skull().plates().jaw("std").cheeks().ears().prow_vents().chin_puck().visor().keel().crest(0.28)
    g = m.g
    hub = surf(R0 * 1.05, 1.35, 0.15)
    g.add(sphere(hub, 0.55), 0.1)                                                                       # stalk hinge on the left temple
    elbow = surf(R0 * 0.72, 1.55, 0.55)
    eye = surf(R0 * 0.55, 0.6, 0.95)
    g.add(tube([hub, elbow, eye + v3(0, 0.15, 0.5)], 0.32), 0.08)                                     # articulated stalk, 0.64 mm
    fwd = v3(0, -1, 0)
    g.add(cyl(eye - fwd * 1.0, eye + fwd * 0.9, 0.62, 0.12), 0.1)                                     # monocular barrel, its back resting on the visor
    g.add(torus(eye + fwd * 0.2, fwd, 0.62, 0.14), 0.04)                                             # focus ring
    g.cut(cyl(eye + fwd * 0.65, eye + fwd * 1.4, 0.4))
    m.antenna(-1, length=4.6, r_mm=0.38)
    return m.finish()


def heavy(h=0.05, damaged=False):
    """VH2-04 Bastion: heavy helm with an armoured respirator, narrowed visor and filter cans."""
    m = Helm(h, front=-4.6).skull().plates(crown_t=0.36, temple_t=0.2, brow_lift=0.12).jaw("heavy").cheeks(dz=-0.05, size=1.08)
    m.ears().visor(VISOR_HEAVY, frame=0.36, frame_h=0.26)
    g = m.g
    g.add(rbox(H(0, -2.35, 0.95), r(1.35, 0.35, 0.22), rot(RX, -12), 0.12), 0.2)                       # armoured brow bar
    for j, z in enumerate((-0.75, -1.25, -1.75)):                                                     # respirator: three raised slats
        p, _ = m.facet_point(1, 0.0, z, 0.0)
        g.add(rbox(p + v3(0, -0.12, 0), (1.05 - 0.12 * j, 0.32, 0.2), np.eye(3), 0.08), 0.04)
    ok_cans = (-1,) if damaged else (-1, 1)
    for s in (-1, 1):
        a = H(s * 1.45, -1.95, -1.55)
        b = a + unit(v3(s * 0.5, -0.6, -0.55)) * 1.4
        if s in ok_cans:
            g.add(cyl(a, b, 0.55, 0.15), 0.1)                                                        # filter can
            g.cut(cyl(b - unit(b - a) * 0.15, b + unit(b - a) * 0.5, 0.32))
        else:
            g.add(cyl(a, a + unit(b - a) * 0.35, 0.55, 0.05), 0.1)                                   # sheared-off stub
            g.cut(cyl(a + unit(b - a) * 0.1, a + unit(b - a) * 0.6, 0.3))
    m.keel(z0=0.4, z1=-0.55, r_mm=0.28).crest(0.34)
    if damaged:
        chunk(g, H(-1.25, -2.35, -1.55), 11, 0.55)                                                    # torn respirator corner
        gouge(g, surf(-0.6, 2.6, 0.42), surf(3.0, 1.2, 0.42), 0.32)                                 # deep gash across the crown
        gouge(g, surf(-3.0, 1.1, 0.25), surf(-4.0, -0.3, 0.25), 0.26)
        chunk(g, crest_pt(110, 0.6), 13, 0.6)                                                       # crest bitten through
        for s, z in ((1.2, 1.9), (-2.2, 1.5), (2.9, -0.2), (-0.9, 2.2), (-3.4, 0.2)):
            pit(g, surf(s, z, 0.3), snorm(s, z), 0.32)
        c = surf(-1.6, 0.45, -0.22)
        for d in ((0.7, 0.2), (-0.7, 0.25), (0.3, -0.35)):
            g.cut(capsule(c, surf(-1.6 + d[0], 0.45 + d[1], -0.22), 0.16))
    return m.finish()


def warden(h=0.05):
    """VH2-05 Marshal: sergeant/warden helm with a swept keel blade crest, command antenna and rank bars."""
    m = Helm(h, top=5.3).skull().plates().jaw("std").cheeks().ears().prow_vents().chin_puck().visor().keel()
    prof = [(-1.95, 1.85), (-1.2, 3.0), (0.0, 3.55), (1.3, 4.05), (2.5, 4.5), (3.15, 4.35), (3.0, 3.0), (2.4, 1.4), (1.0, 2.0),
            (-0.5, 2.0), (-1.5, 1.4)]
    m.blade_crest(prof, 0.38)
    m.antenna(1, length=4.8).lamp(-1)
    g = m.g
    for j in range(2):                                                                              # rank bars on the right temple
        p = surf(-R0 * 1.45, 0.85 - 0.45 * j, 0.0)
        g.add(rbox(p, (0.25, 0.7, 0.18), rot(Z, -40), 0.08), 0.04)
    return m.finish()


def medic(h=0.05):
    """VH2-06 Mender: medic helm - triage scanner cluster on the brow, twin filters, painted crown stripe, rear beacon."""
    m = Helm(h).skull().plates().jaw("std").cheeks(vents=2).ears().prow_vents(rows=(-0.95,)).visor().keel(z1=-0.9).crest(0.28)
    g = m.g
    for s in (-1, 1):                                                                               # stripe channels either side of the crest
        def band(Q, s=s):
            return np.abs(Q[:, 0] - s * 0.78) - 0.16
        g.cut((Shape(band, *ALL) & SKULL.offset(0.6)) - SKULL.offset(-0.05))
    bar_c = surf(-R0 * 0.45, 1.35, 0.25)
    g.add(rbox(bar_c, (0.85, 0.35, 0.3), rot(Z, -18), 0.12), 0.08)                                     # scanner bar, right brow
    for j in range(3):
        p = bar_c + rot(Z, -18) @ v3(-0.55 + 0.55 * j, -0.3, 0)
        g.cut(sphere(p, 0.2))
    for s in (-1, 1):
        a = H(s * 0.85, -2.15, -1.45)
        b = a + unit(v3(s * 0.55, -0.7, -0.45)) * 1.05
        g.add(cyl(a, b, 0.48, 0.14), 0.1)                                                            # twin filter cans
        g.cut(cyl(b - unit(b - a) * 0.12, b + unit(b - a) * 0.5, 0.27))
    g.add(sphere(H(0, 2.55, 1.0), 0.55), 0.12)                                                        # rear beacon dome
    return m.finish()


def engineer(h=0.05):
    """VH2-07 Wright: engineer helm - brow headlamp, flip-up magnifier goggles on a strap, tool port."""
    m = Helm(h, top=3.9).skull().plates().jaw("std").cheeks().ears().prow_vents().chin_puck().visor().keel()
    g = m.g
    sn, sc = unit(v3(0, -0.55, 1)), H(0, 0.25, 1.85)
    strap = Shape(lambda Q: np.abs((Q - sc) @ sn) - 0.26, *ALL)
    g.add((strap & SKULL.offset(0.4)) - SKULL.offset(-0.2), 0.05)                                     # goggle strap hugging the dome
    for s in (-1, 1):
        c = surf(s * 0.78, 2.12, 0.5)
        n = unit(snorm(s * 0.78, 2.12) + v3(0, -0.5, 0.3))
        g.add(cyl(c - n * 0.4, c + n * 0.45, 0.6, 0.12), 0.1)                                        # goggle lens housing (flipped up)
        g.cut(cyl(c + n * 0.28, c + n * 0.9, 0.38))
    g.add(capsule(surf(-0.78, 2.12, 0.5), surf(0.78, 2.12, 0.5), 0.27), 0.05)                         # bridge
    lc = surf(0, 1.2, 0.6)
    fwd = unit(v3(0, -1, -0.1))
    g.add(rbox(lc + v3(0, 0.25, 0.0), (0.62, 0.55, 0.42), np.eye(3), 0.15), 0.1)                      # brow headlamp housing
    g.add(cyl(lc - fwd * 0.2, lc + fwd * 0.55, 0.52, 0.1), 0.05)
    g.cut(cyl(lc + fwd * 0.38, lc + fwd * 1.0, 0.34))
    g.add(tube([lc + v3(0, 0.55, 0.2)] + [crest_pt(a, 0.3) for a in (55, 85, 120, 160)], 0.28), 0.1)  # lamp cable along the crown line
    p = surf(R0 * 1.55, 0.95, 0.05)
    g.add(cyl(p - v3(0.25, 0, 0), p + v3(0.4, 0, 0), 0.5, 0.1), 0.08)                                # tool port, left
    g.cut(cyl(p + v3(0.2, 0, 0), p + v3(0.8, 0, 0), 0.26))
    return m.finish()


def marksman(h=0.05):
    """VH2-08 Plumb: marksman helm - stereo rangefinder over the right wing, flat stock-weld pad on the left cheek."""
    m = Helm(h).skull().plates().jaw("std").cheeks().ears().prow_vents().chin_puck().visor().keel().crest(0.26)
    g = m.g
    hub = surf(-R0 * 1.2, 1.2, 0.2)
    g.add(cyl(hub - v3(0.3, 0, 0), hub + v3(0.25, 0, 0), 0.55, 0.12), 0.1)                           # hinge
    box_c = surf(-R0 * 0.85, 1.25, 0.75)
    Rb = rot(Z, -30)
    g.add(rbox(box_c, (0.75, 1.0, 0.45), Rb, 0.15), 0.1)                                               # rangefinder body
    g.add(capsule(hub, box_c, 0.32), 0.08)
    fwd = Rb @ v3(0, -1, 0)
    for dz in (-0.2, 0.22):
        p = box_c + fwd * 0.95 + v3(0, 0, dz)
        g.cut(cyl(p - fwd * 0.3, p + fwd * 0.4, 0.17))                                                 # stereo lenses
    g.add(rbox(box_c + fwd * 0.2 + v3(0, 0, -0.62), (0.45, 0.55, 0.22), Rb, 0.08), 0.06)               # eyepiece hood over the wing
    pad = H(1.9, -1.1, -0.95)
    g.add(rbox(pad, (0.3, 0.8, 0.55), rot(Z, 24), 0.15), 0.08)                                         # stock-weld pad
    return m.finish()


def pilot(h=0.05):
    """VH2-09 Kite: pilot/crew helm - smooth cheeks, stowed sun shade, big ear cups, boom mic, oxygen hose."""
    m = Helm(h).skull().plates(nape=True).jaw("sealed").ears(hose=False, big=1.22).visor(frame_h=0.15)
    m.keel(z1=-1.0, r_mm=0.25).crest(0.26, a0=60)
    g = m.g
    shade = mirror([(0.0, 0.75), (1.6, 0.95), (2.6, 1.25), (2.85, 0.95), (2.5, 0.35), (0.0, 0.1)])
    piv = H(*SK_C)
    M = np.eye(4)
    M[:3, :3] = rot(RX, -34)
    M[:3, 3] = piv - M[:3, :3] @ piv
    g.add(((wrap_prism(shade) & SKULL.offset(0.62)) - SKULL.offset(0.3)).moved(M), 0.05)            # sun shade, stowed up
    for s in (-1, 1):
        g.add(capsule(H(s * 2.2, 0.15, 0.4), H(s * 2.0, -0.6, 1.9), 0.3), 0.05)                       # shade hinge arms
    g.add(tube([H(2.55, -0.1, -0.5), H(2.1, -1.1, -1.25), H(1.25, -1.95, -1.5), H(0.55, -2.35, -1.55)], 0.28), 0.06)  # boom mic
    g.add(sphere(H(0.45, -2.38, -1.55), 0.42), 0.06)
    g.add(cyl(H(-0.5, -2.1, -1.5), H(-0.55, -2.65, -1.65), 0.42, 0.1), 0.06)                          # O2 plug
    g.add(tube([H(-0.55, -2.5, -1.6), H(-1.5, -1.9, -1.85), H(-2.15, -0.6, -1.7), H(-1.75, 1.2, -1.55)], 0.3), 0.08)
    return m.finish()


def officer(h=0.05):
    """VH2-10 Provost: officer open-face helm - visor flipped up on the brow, face bare, chin strap, short blade crest."""
    m = Helm(h, top=4.6).skull().plates()
    g = m.g
    g.cut(ellipsoid(H(0, -2.05, -0.55), r(1.3, 1.25, 1.45)), 0.1)                                     # face opening
    g.add(ellipsoid(H(0, -0.45, -0.5), r(1.12, 1.6, 1.45)), 0.2)                                      # head
    face = [
        (capsule(H(-0.55, -1.98, 0.08), H(0.55, -1.98, 0.08), 0.22), 0.14),                          # brow
        (round_cone(H(0, -2.02, -0.08), H(0, -2.3, -0.62), 0.18, 0.27), 0.1),                        # nose
        (ellipsoid(H(-0.62, -1.82, -0.52), r(0.32, 0.25, 0.24)), 0.12),                              # cheekbones
        (ellipsoid(H(0.62, -1.82, -0.52), r(0.32, 0.25, 0.24)), 0.12),
        (ellipsoid(H(0, -1.82, -1.35), r(0.5, 0.42, 0.35)), 0.15),                                    # chin
    ]
    for s, k in face:
        g.add(s, k)
    for s in (-1, 1):
        g.cut(sphere(H(s * 0.42, -2.0, -0.2), 0.25), 0.06)                                            # eye sockets
        g.add(sphere(H(s * 0.42, -1.9, -0.22), 0.17), 0.02)                                            # eyes
    g.cut(capsule(H(-0.3, -2.02, -0.98), H(0.3, -2.02, -0.98), 0.12))                                 # mouth line
    for s in (-1, 1):                                                                               # cheek guards framing the face
        g.add(rbox(H(s * 1.45, -1.2, -0.8), r(0.3, 0.9, 0.85), rot(Z, s * 22) @ rot(RY, -s * 8), 0.26 * HS), 0.12)
    g.add(tube([H(-1.45, -1.3, -1.45), H(-0.7, -1.75, -1.95), H(0.7, -1.75, -1.95), H(1.45, -1.3, -1.45)], 0.25), 0.08)  # chin strap
    piv = H(*SK_C)
    M = np.eye(4)
    M[:3, :3] = rot(RX, -48)
    M[:3, 3] = piv - M[:3, :3] @ piv
    vis = (wrap_prism(VISOR) & SKULL.offset(0.62)) - SKULL.offset(0.3)
    g.add(vis.moved(M), 0.05)                                                                          # gull-wing visor, flipped up
    m.ears(hose=False)
    for s in (-1, 1):
        g.add(capsule(H(s * 2.25, 0.15, 0.3), H(s * 2.05, -0.95, 2.05), 0.3), 0.05)                   # visor arms
    prof = [(-1.6, 2.3), (-0.8, 3.15), (0.4, 3.6), (1.6, 3.85), (2.7, 3.75), (2.9, 2.8), (2.4, 1.4), (1.0, 2.0), (-0.5, 2.0), (-1.2, 1.9)]
    m.blade_crest(prof, 0.36)
    g.add(rbox(surf(R0 * 1.4, 0.9, 0.05), (0.25, 0.75, 0.45), rot(Z, 35), 0.12), 0.05)                 # rank plate, left
    return m.finish()


VH2 = {
    "VH2-01": ("Lineguard", "line trooper: gull-wing split visor, keel line, V-prow respirator, cheek vents, aural hoses", lambda h: line(h)),
    "VH2-02": ("Tidewall", "sealed void/EVA: flush pane in a heavy frame, collar ring and lugs, life-support hoses", void),
    "VH2-03": ("Lookout", "recon: hinged optic stalk over the left wing, whip antenna", recon),
    "VH2-04": ("Bastion", "heavy: armoured slatted respirator, narrowed visor, brow bar, twin filter cans", lambda h: heavy(h)),
    "VH2-05": ("Marshal", "sergeant/warden: swept keel blade crest, command antenna, rank bars", warden),
    "VH2-06": ("Mender", "medic: triage scanner on the brow, twin filters, crown stripe, rear beacon", medic),
    "VH2-07": ("Wright", "engineer: brow headlamp, flip-up magnifier goggles on a strap, tool port", engineer),
    "VH2-08": ("Plumb", "marksman: stereo rangefinder over the right wing, stock-weld cheek pad", marksman),
    "VH2-09": ("Kite", "pilot/crew: stowed sun shade, big ear cups, boom mic, oxygen hose", pilot),
    "VH2-10": ("Provost", "officer open-face: visor flipped up, bare face, chin strap, short blade crest", officer),
    "VH2-11": ("Lineguard, scarred", "battle-damaged line helm: gouges, crest notch, pits, cracked wing", lambda h: line(h, damaged=True)),
    "VH2-12": ("Bastion, breached", "battle-damaged heavy: torn respirator, sheared filter, gouges, pits, cracked visor", lambda h: heavy(h, damaged=True)),
}


def helm(ident, h=0.05):
    return VH2[ident][2](h)
