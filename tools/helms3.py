"""VH3 helm library: Vigil helm Mk 3, eight silhouette-first variants (original design) for the Aster Compact line.

VH-01..10 (tools/armory.py, tools/exosuit.py) and VH2-01..12 (tools/vh2.py) are untouched; this module only imports
their building blocks. Every VH3 helm keeps the line's family marks while changing the silhouette:

- SPLIT CHEVRON: the glass (one wrap visor, two lenses, a dome window or goggles) has a lower edge that falls to a V
  at the centre and is split by the KEEL bar; the glass is a separate recessed surface (>= 0.25 mm below a raised
  frame >= 0.42 mm wide) so it takes a gloss or a lens paint on its own.
- KEEL LINE: one ridge runs from the nape over the crown and down the face (crest tube, flat ridge plate or fin).

What changes from helm to helm is the outline seen at arm's length (front and side silhouettes are measured, see
vigil-helms-mk3/source/silhouettes.py): a flared, brow-shelved drop helm; an asymmetric recon helm with a side optic
pod; a squat assault helm with a portcullis faceplate and hoses to a collar; a tall officer helm with a stepped fin
and a comm mast; a round sealed void globe with a back pack; a low open-face crew cap with big ear cups; a sniper helm
with a sallet tail and a flip-down monocular; and a battle-scarred helm whose faceplate is an original relief
"death's head" built from Vigil parts (chevron lenses as eye sockets, a vent as the nose, jaw vents as teeth).

Reference sheets were used for qualities only (silhouette rhythm, chunkiness, proportion, detail density); no helm
copies a recognisable game or film design or carries a faction mark.

Frame (same as every Vigil helm): neck cut at z = 0, 1.6 mm D-flat peg down (exosuit.PEG_HEAD), faces -y, mm;
H(x, y, z) is a helm-local point in helm units (x HS = 1.12 mm). Glass outlines are polygons in (s, z) with s the arc
length about the skull axis (vh2.wrap_prism).
Feature floor (MSLA resin): raised details >= 0.5 mm wide, engraved slots >= 0.3 mm wide and <= 0.35 mm deep with
ribs >= 0.42 mm, frames >= 0.42 mm wide, wires >= 0.76 mm diameter.
"""
from __future__ import annotations

import math

import numpy as np

from exosuit import HEAD_UP, HS, PEG_HEAD, RY, Z
from sdfkit import Sculpt, Shape, capsule, cyl, ellipsoid, half, rbox, rot, round_cone, smin, sphere, torus, tube, unit, v3
from vh2 import (ALL, HC, R0, RX, SK_C, SK_R, SKULL, VISOR, H, Helm, _loc, crest_pt, gouge, mirror, pit, r, sd_polygon, snorm,
                 surf)

# ------------------------------------------------------------------------------------------------ glass outlines (s, z)
VISOR_WRAP = mirror([(0.0, 0.88), (1.6, 0.92), (2.75, 0.85), (3.2, 0.6), (3.05, 0.3), (2.1, 0.12), (1.05, -0.05), (0.0, -0.5)])
LENS_L = [(0.34, 0.62), (1.5, 0.95), (2.45, 1.2), (2.72, 0.95), (1.6, 0.42), (0.44, 0.02)]   # recon: left lens (s > 0)
LENS_R = [(-s, z) for s, z in LENS_L]
VISOR_SLIT = mirror([(0.0, 0.52), (1.3, 0.57), (2.45, 0.74), (2.64, 0.48), (1.3, 0.2), (0.0, 0.04)])
VISOR_FROWN = mirror([(0.0, 0.95), (1.4, 0.8), (2.55, 0.62), (2.75, 0.32), (1.5, 0.02), (0.0, -0.48)])
WINDOW = mirror([(0.0, 1.75), (1.5, 1.65), (2.7, 1.2), (3.1, 0.4), (2.8, -0.45), (1.6, -0.85), (0.0, -1.25)])
VISOR_SNIPE = mirror([(0.0, 0.72), (1.1, 0.84), (2.2, 1.02), (2.5, 0.76), (2.2, 0.36), (1.1, 0.0), (0.0, -0.45)])

GLOBE_C, GLOBE_R = (0.0, 0.15, 0.35), (2.45, 2.65, 2.6)
GLOBE = ellipsoid(H(*GLOBE_C), r(*GLOBE_R))                  # the void helm's round shell


def rwrap_prism(V, c=SK_C, radii=SK_R):
    """Radial version of vh2.wrap_prism: the (s, z) outline V is wrapped round the shell and its walls run along rays
    from the shell centre (z is the height where that ray meets the ellipsoid), so every glass, frame and shelf wall
    meets the shell square instead of as a horizontal ceiling over a sloping surface (which left knife-edge lips:
    VH3 first check, thin spots along the window rims)."""
    V = np.asarray(V, float)
    c, rad = np.asarray(c, float), np.asarray(radii, float)

    def f(Q):
        q = (Q - HC) / HS
        u = (q - c) / rad
        th = np.arctan2(q[:, 0], -(q[:, 1] - c[1]))
        zp = c[2] + rad[2] * u[:, 2] / np.maximum(np.linalg.norm(u, axis=1), 1e-6)
        return HS * sd_polygon(np.stack([R0 * th, zp], axis=1), V)
    return Shape(f, (-4.2, -4.6, HC[2] + HS * (c[2] - rad[2]) - 0.8), (4.2, 4.6, HC[2] + HS * (c[2] + rad[2]) + 0.8))


def sinter(a, b, k):
    """Smooth intersection (rounded edge of radius about k) with a's bbox: clipped plates without knife edges."""
    return Shape(lambda P: -smin(-a(P), -b(P), k), a.lo, a.hi)


def notch(g, p, n, w=0.6, depth=0.7):
    """Clean V notch (a battle bite) at p into the surface with normal n: two half-spaces, no random slivers."""
    n = unit(n)
    t = unit(np.cross(n, (1, 0, 0))) if abs(n[0]) < 0.9 else unit(np.cross(n, (0, 1, 0)))
    a = half(p - n * depth, unit(-n + t * (depth / w)))
    b = half(p - n * depth, unit(-n - t * (depth / w)))
    g.cut((a & b) & sphere(p, w + depth))


def hu(z):
    """Helm-unit height -> mm."""
    return HC[2] + HS * z


# ------------------------------------------------------------------------------------------------ building blocks
class Helm3(Helm):
    """A VH3 helm on its own grid. Adds glass bookkeeping (self.glass: callables c -> bool for the display sheets)."""

    def __init__(self, h=0.05, top=3.6, front=-4.4, side=3.7, back=3.9):
        self.g = Sculpt((-side, front, -PEG_HEAD["len"] - 0.3), (side, back, HEAD_UP + HS * top), h)
        self.visor_poly = VISOR
        self.glass = []

    # glass ------------------------------------------------------------------------------------------
    def glass_visor(self, poly, depth=0.34, frame=0.45, frame_h=0.16, facet=True, shell=SKULL, c=SK_C, radii=SK_R):
        """Recessed glass inside a raised frame. Glass floor depth under the shell, frame width, frame_h proud."""
        g = self.g
        P = rwrap_prism(poly, c, radii)
        g.add(P.offset(frame) & shell.offset(frame_h), 0.06)
        g.cut((P & shell.offset(0.9)) - shell.offset(-depth))
        if facet:                                                                                 # upper facet, 0.15 mm proud
            zc = float(np.asarray(poly)[:, 1].mean()) + 0.12

            def upper(Q):
                q, th = _loc(Q)
                return HS * (zc + 0.12 * np.abs(R0 * th) - q[:, 2])
            g.add(P.offset(-0.14) & shell.offset(-depth + 0.15) & Shape(upper, *ALL))
        self.glass.append(lambda c, P=P, sh=shell: (P(c) < -0.03) & (sh(c) < -0.06))
        return self

    def lens(self, a, b, rad, depth=0.28, rim=0.45):
        """Lens housing along a -> b (b is the front), glass recessed depth behind its rim."""
        g = self.g
        n = unit(b - a)
        g.add(cyl(a, b, rad + rim, 0.12), 0.06)
        cutter = cyl(b - n * depth, b + n * 1.0, rad)
        g.cut(cutter)
        self.glass.append(lambda c, k=cutter: k(c) < 0.03)
        return self

    # shell features ---------------------------------------------------------------------------------
    def shelf(self, poly, t, k=0.12):
        """Brow shelf: the shell grown by t mm inside the (s, z) outline, cut by radial walls (a ledge square to the
        shell; the earlier ramped underside met the visor frame in a knife-edge crevice)."""
        P = rwrap_prism(poly)
        self.g.add(sinter(P, SKULL.offset(t), 0.12), k)
        return self

    def ridge(self, half_w=0.45, proud=0.62, z_min=1.0, shell=SKULL, x0=0.0):
        """Flat keel ridge plate over the crown (|x - x0| < half_w), proud mm over the shell, above helm height z_min."""
        band = Shape(lambda Q: np.abs(Q[:, 0] - x0) - half_w, *ALL)
        self.g.add(sinter(band & shell.offset(proud), half(H(0, 0, z_min), -Z), 0.25), 0.1)
        return self

    def prow_vents(self, rows=(-0.85, -1.47), xl=0.62, length=0.3, w=0.15, depth=0.28, ang=12):
        """VH2 vents moved inboard and shortened so the slot ends stay on the flat facet (the VH2 slots ran out over the
        prow's rounded edge: 0.002 mm slivers in the first VH3 check)."""
        return Helm.prow_vents(self, rows, xl, length, w, depth, ang)

    def cheeks(self, vents=3, dz=0.0, size=1.0):
        Helm.cheeks(self, vents, dz, size)
        for s in (-1, 1):                                                                          # web: cheek guard to ear
            self.g.add(ellipsoid(H(s * 1.85, -0.45, -0.65 + dz), r(0.38, 0.5, 0.42)), 0.15)
        return self

    def facet_frame(self, s, xl, zl, extra=0.0):
        """Point and frame (t along the facet, n out of it, up) on prow facet s at helm-unit x, z."""
        p, n = self.facet_point(s, xl, zl, extra)
        t = unit(np.cross(n, Z))
        if t[0] * s < 0:
            t = -t
        return p, np.stack([t, n, np.cross(t, n)], axis=1)

    def faceplate(self, c, half_r, apex, slope, chin=(-2.25, -1.95), k=0.3):
        """Faceted faceplate: a rounded block cut to a shallow V-prow (apex y in helm units, facet slope)."""
        fp = rbox(H(*c), r(*half_r), rot(RX, 4), 0.2 * HS)
        fp = fp.clip(half(H(0, apex, 0), unit((slope, -1, 0))), half(H(0, apex, 0), unit((-slope, -1, 0))),
                     half(H(0, chin[0], chin[1]), unit((0, -0.75, -1))))
        self.g.add(fp, k * HS)
        self.prow_apex, self.prow_slope = apex, slope
        return self

    def collar(self, z=-1.85, R=2.15, rr=0.4):
        self.g.add(torus(H(0, 0.15, z), Z, R * HS, rr), 0.25)
        return self

    def hose(self, pts, rad=0.34, bead=0.42, pitch=0.55):
        """Corrugated hose: a tube with a bead every pitch mm (beads >= 0.5 mm wide, so they print)."""
        g = self.g
        g.add(tube(pts, rad), 0.08)
        P = [v3(p) for p in pts]
        L = [0.0]
        for i in range(1, len(P)):
            L.append(L[-1] + float(np.linalg.norm(P[i] - P[i - 1])))
        for d in np.arange(pitch, L[-1] - pitch * 0.5, pitch):
            i = int(np.searchsorted(L, d)) - 1
            i = min(max(i, 0), len(P) - 2)
            t = (d - L[i]) / max(L[i + 1] - L[i], 1e-9)
            g.add(sphere(P[i] + (P[i + 1] - P[i]) * t, bead), 0.12)
        return self


# ------------------------------------------------------------------------------------------------ VH3-01 drop trooper
def drop(h=0.05):
    """VH3-01 Plummet: drop trooper. Wide wrap-around chevron visor under a ramped brow shelf, flat keel ridge plate,
    jaw armour that flares out and down (a trapezoid front silhouette), V-prow respirator, rear drop beacon."""
    m = Helm3(h, top=3.75, side=4.0).skull().plates(crown_t=0.3, temple_t=0.15, brow_lift=0.45)
    m.glass_visor(VISOR_WRAP, depth=0.34, frame=0.45, frame_h=0.16).jaw("std")                     # glass first: prow overrides its V tip
    g = m.g
    for s in (-1, 1):                                                                              # flared jaw armour
        c = H(s * 1.95, -0.7, -1.3)
        R = rot(Z, s * 14) @ rot(RY, -s * 27)
        g.add(rbox(c, r(0.44, 1.5, 1.05), R, 0.16 * HS), 0.3)
        g.add(ellipsoid(H(s * 1.5, -0.75, -1.2), r(0.55, 1.2, 0.8)), 0.3)                         # web into the jaw
        face = c + R[:, 0] * s * (0.44 * HS)
        for j in range(3):
            g.cut(rbox(face + R[:, 1] * (j - 1) * 0.74, (0.25, 0.15, 0.46), R, 0.06))           # three vents, ribs 0.44
    m.prow_vents().chin_puck()
    shelf_poly = mirror([(0.0, 2.0), (2.0, 2.0), (3.3, 1.7), (3.45, 1.06), (2.0, 1.1), (0.0, 1.14)])
    m.shelf(shelf_poly, 0.8)                                                           # brow ridge
    m.keel(z0=0.86, z1=-1.0)
    m.ridge(half_w=0.48, proud=0.62, z_min=0.6)                                                    # flat keel ridge plate
    g.add(sphere(H(0, 2.55, 1.35), 0.55), 0.12)                                                    # rear drop beacon
    for s in (-1, 1):
        g.add(capsule(H(s * 1.35, 1.95, 1.45), H(s * 1.5, 2.55, 0.65), 0.34), 0.1)                 # grab-bar studs
    return m


# ------------------------------------------------------------------------------------------------ VH3-02 recon
def recon(h=0.05):
    """VH3-02 Sightline: recon. Two narrow chevron lenses split by the keel, a big optic/rangefinder pod clamped to the
    right side on a bracket (the silhouette goes asymmetric), whip antenna swept back along the left side."""
    m = Helm3(h, top=3.7, side=4.5, back=4.6).skull().plates(crown_t=0.22)
    m.glass_visor(LENS_L, depth=0.32, facet=False).glass_visor(LENS_R, depth=0.32, facet=False)
    m.jaw("std").ears(hose=False).prow_vents(rows=(-1.0,)).chin_puck()
    m.keel(z0=0.7).crest(0.3)
    g = m.g
    c = H(-3.0, -0.45, 0.8)
    Rp = rot(Z, -8)
    g.add(rbox(H(-2.3, -0.1, 0.6), (0.85, 0.8, 0.52), Rp, 0.15), 0.1)                              # clamp bracket
    g.add(rbox(c, (1.0, 1.45, 0.85), Rp, 0.24), 0.08)                                              # optic pod
    fwd, side, up = Rp @ v3(0, -1, 0), Rp @ v3(-1, 0, 0), v3(0, 0, 1)
    front = c + fwd * 1.4
    m.lens(front - fwd * 0.3 + up * 0.2, front + fwd * 0.4 + up * 0.2, 0.5)                       # main objective
    m.lens(front - fwd * 0.3 - up * 0.38 - side * 0.3, front + fwd * 0.2 - up * 0.38 - side * 0.3, 0.22, rim=0.3)  # rangefinder
    for j in range(3):                                                                             # cooling slots, outboard face
        p = c + side * 1.0 + fwd * (j - 1) * 0.72 + up * 0.05
        g.cut(rbox(p, (0.15, 0.25, 0.42), np.stack([fwd, side, up], axis=1), 0.06))
    g.add(rbox(c + up * 0.85 - fwd * 0.35, (0.5, 0.45, 0.22), Rp, 0.1), 0.06)                       # range dial cap
    a = H(2.3, 0.45, 0.35)                                                                          # swept whip antenna, left
    g.add(cyl(a - v3(0.3, 0, 0), a + v3(0.2, 0, 0), 0.55, 0.12), 0.1)
    b = H(1.85, 3.1, 1.5)
    g.add(capsule(a, b, 0.38), 0.06)
    g.add(sphere(b, 0.5), 0.05)
    return m


# ------------------------------------------------------------------------------------------------ VH3-03 heavy assault
def assault(h=0.05):
    """VH3-03 Ironclad: heavy assault. Squat thick shell, a broad V-faceted faceplate with a portcullis grille (vertical
    slots; the centre bar is the keel), a narrow armoured slit visor under a brow hood, corrugated breathing hoses
    from the faceplate round the jaw into a collar ring."""
    m = Helm3(h, top=3.6, front=-4.7, side=4.3).skull().plates(crown_t=0.4, temple_t=0.24, brow_lift=0.1)
    g = m.g
    g.cut(Shape(lambda Q: hu(2.0) - Q[:, 2], (-9, -9, hu(2.0)), (9, 9, 20)))                       # flat-topped: crown cut off
    g.add(rbox(H(0, 0.3, 1.95), r(1.9, 2.2, 0.32), np.eye(3), 0.14), 0.25)                          # armoured cap plate
    g.add(rbox(H(0, 0.3, 2.25), r(0.3, 2.2, 0.2), np.eye(3), 0.1), 0.06)                           # keel ridge on the cap
    m.glass_visor(VISOR_SLIT, depth=0.3, frame=0.45, frame_h=0.18, facet=False)                    # glass first
    m.faceplate((0, -1.75, -1.05), (1.72, 1.0, 1.05), apex=-2.78, slope=0.33)
    for s in (-1, 1):                                                                              # jowls
        cj = H(s * 1.9, -0.95, -1.2)
        Rj = rot(Z, s * 22) @ rot(RY, -s * 10)
        g.add(rbox(cj, r(0.5, 1.0, 0.85), Rj, 0.16 * HS), 0.14)
    for s in (-1, 1):                                                                              # portcullis grille
        for j, xm in enumerate((0.5, 1.24)):
            ztop, zbot = -0.5, -1.72 + 0.22 * j
            p, R = m.facet_frame(s, s * xm / HS, (ztop + zbot) / 2)
            g.cut(rbox(p, (0.16, 0.34, HS * (ztop - zbot) / 2), R, 0.06))
    p, R = m.facet_frame(1, 0.0, -0.32, 0.0)
    g.add(rbox(p + v3(0, -0.05, 0), (1.55, 0.2, 0.24), np.eye(3), 0.08), 0.05)                     # grille header bar
    m.shelf(mirror([(0.0, 1.35), (2.0, 1.35), (2.75, 1.15), (2.85, 0.82), (2.0, 0.84), (0.0, 0.86)]), 0.52)  # brow hood
    m.ears(hose=False)
    m.collar(z=-1.85, R=2.3, rr=0.45)
    for s in (-1, 1):
        g.add(cyl(H(s * 1.3, -2.15, -1.35), H(s * 1.75, -2.75, -1.5), 0.5, 0.12), 0.08)            # hose ports
        m.hose([H(s * 1.6, -2.5, -1.45), H(s * 2.25, -1.7, -1.72), H(s * 2.5, -0.4, -1.82), H(s * 2.25, 0.95, -1.88),
                H(s * 1.45, 1.85, -1.88)], rad=0.32, bead=0.4)
    m.keel(z0=0.56, z1=-0.42, r_mm=0.28)
    g.add(tube([crest_pt(a, 0.25) for a in (14, 30, 46, 54)], 0.3), 0.08)                          # keel from the cap down to the visor
    return m


# ------------------------------------------------------------------------------------------------ VH3-04 officer
def officer(h=0.05):
    """VH3-04 Herald: officer. Stern 'frown' visor (top edge falls outward), a tall stepped keel fin crest, a comm mast
    with two cross spars on the right rear, three raised rank chevrons on the left side."""
    m = Helm3(h, top=5.9, side=4.0, back=4.4).skull().plates().glass_visor(VISOR_FROWN)
    m.jaw("std").cheeks().ears().prow_vents().chin_puck().keel(z0=1.4)
    prof = [(-1.8, 1.7), (-1.0, 2.95), (0.0, 3.6), (1.0, 4.3), (2.0, 5.05), (2.7, 5.45), (3.15, 5.2), (3.1, 4.1),
            (2.7, 1.5), (1.0, 2.1), (-0.5, 2.1), (-1.5, 1.3)]
    m.blade_crest(prof, 0.4)
    g = m.g
    a = H(-2.15, 0.95, 0.55)
    up = unit(v3(-0.1, 0.22, 1))
    g.add(cyl(a + v3(0.35, 0, 0), a - v3(0.25, 0, 0), 0.62, 0.12), 0.1)                            # mast boss
    top = a + up * 5.0
    g.add(capsule(a, top, 0.4), 0.06)
    for d in (3.3, 4.3):                                                                           # cross spars
        p = a + up * d
        g.add(capsule(p - v3(0, 0.55, 0), p + v3(0, 0.55, 0), 0.38), 0.06)
    g.add(sphere(top, 0.52), 0.05)
    for j in range(2):                                                                             # rank chevrons
        zc = 1.95 - 0.55 * j
        arm = [surf(sv, zc - 0.4 * (1 - abs(sv - 3.05) / 0.85), 0.12) for sv in np.linspace(2.2, 3.9, 7)]
        g.add(tube(arm, 0.28), 0.1)
    return m


# ------------------------------------------------------------------------------------------------ VH3-05 sealed void
def gpt(a_deg, lift=0.3):
    """Point on the globe's mid-plane at angle a from the front (0 = front, 90 = top), lifted by lift mm."""
    a = math.radians(a_deg)
    return H(0, 0.15 - 2.65 * math.cos(a), 0.35 + 2.6 * math.sin(a)) + v3(0, -math.cos(a), math.sin(a)) * lift


def void(h=0.05):
    """VH3-05 Stillwater: sealed void helm. A round globe with a big domed window (arched top, V lower edge) split by
    an external keel rib running from the back over the crown, down the glass to the chin; heavy collar ring with six
    bolts, a life-support pack on the back with hoses to the collar, two temple lamps, an antenna stub."""
    m = Helm3(h, top=3.9, side=4.0, back=4.6)
    g = m.g
    g.add(GLOBE)
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                        # neck seal
    m.glass_visor(WINDOW, depth=0.3, frame=0.5, frame_h=0.22, facet=False, shell=GLOBE, c=GLOBE_C, radii=GLOBE_R)
    g.add(tube([gpt(a, -0.04) for a in np.linspace(-38, 172, 18)], 0.32), 0.06)                     # keel rib, seated on the glass
    m.collar(z=-1.9, R=2.05, rr=0.42)
    for k in range(6):
        t = math.radians(30 + 60 * k)
        g.add(sphere(H(2.38 * math.cos(t), 0.15 + 2.38 * math.sin(t), -1.9), 0.3), 0.04)            # collar bolts
    pc = H(0, 2.85, -0.25)
    g.add(rbox(pc, r(1.2, 0.55, 1.05), np.eye(3), 0.22), 0.15)                                       # life-support pack
    for s in (-1, 1):
        g.cut(rbox(pc + v3(s * 0.45, 0.62, 0.1), (0.15, 0.3, 0.6), np.eye(3), 0.06))                # pack vents
        m.hose([H(s * 1.05, 2.75, -0.95), H(s * 2.15, 1.75, -1.5), H(s * 2.3, 0.4, -1.75)], rad=0.3, bead=0.38)
        base = surf(s * R0 * 1.32, 1.05, 0.0)                                                       # temple lamps
        m.lens(base + v3(0, 0.35, 0), base + v3(0, -0.55, 0), 0.3, depth=0.25, rim=0.42)
    g.add(capsule(H(-0.9, 1.6, 2.25), H(-1.0, 2.2, 3.1), 0.38), 0.1)                                 # antenna stub
    g.add(sphere(H(-1.0, 2.2, 3.1), 0.48), 0.05)
    return m


# ------------------------------------------------------------------------------------------------ VH3-06 open-face crew
def crew(h=0.05):
    """VH3-06 Deckhand: open-face crew cap. A low padded cap (keel ridge and two side ribs) cut away above the face,
    big headset ear cups, one-piece chevron goggles worn up on the brim, boom mic, chin strap; the face is bare."""
    m = Helm3(h, top=3.3, side=4.3)
    g = m.g
    g.add(ellipsoid(H(0, -0.35, -0.45), r(1.2, 1.6, 1.55)))                                         # head
    g.add(cyl(v3(0, 0.15, -0.3), H(0, 0.2, -1.2), 1.3), 0.4)                                        # neck
    cut_n, cut_p = unit((0, -0.5, -1)), H(0, 0, -0.25)
    cap = SKULL.offset(0.1).clip(half(cut_p, cut_n))
    g.add(cap, 0.25)
    rim = Shape(lambda Q: np.maximum((Q - cut_p) @ cut_n, -((Q - cut_p) @ cut_n) - 0.42), *ALL)
    g.add(SKULL.offset(0.32) & rim, 0.06)                                                           # rolled brim lip
    m.ridge(half_w=0.42, proud=0.42, z_min=0.9, shell=SKULL)                                        # keel ridge
    for s in (-1, 1):
        k_ = math.sqrt(1 - (1.05 / HS / 2.15) ** 2)                                                # padded side ribs (tubes:
        rib = [H(s * 1.05 / HS, 0.25 - 2.5 * k_ * math.cos(a), 0.3 + 2.5 * k_ * math.sin(a)) +             #  round ends, no wedges)
               v3(0, -math.cos(a), math.sin(a)) * 0.12 for a in np.radians(np.linspace(48, 150, 9))]
        g.add(tube(rib, 0.27), 0.08)
    face = [
        (capsule(H(-0.55, -1.86, 0.25), H(0.55, -1.86, 0.25), 0.21), 0.12),                       # brow
        (round_cone(H(0, -1.92, 0.05), H(0, -2.16, -0.5), 0.17, 0.25), 0.1),                      # nose
        (ellipsoid(H(-0.6, -1.7, -0.45), r(0.3, 0.24, 0.22)), 0.12),                              # cheekbones
        (ellipsoid(H(0.6, -1.7, -0.45), r(0.3, 0.24, 0.22)), 0.12),
        (ellipsoid(H(0, -1.66, -1.3), r(0.55, 0.4, 0.36)), 0.15),                                  # chin
    ]
    for sh, k in face:
        g.add(sh, k)
    for s in (-1, 1):
        g.cut(sphere(H(s * 0.42, -1.97, -0.05), 0.24), 0.06)                                        # eye sockets
        g.add(sphere(H(s * 0.42, -1.84, -0.08), 0.16), 0.02)                                        # eyes
    g.cut(capsule(H(-0.28, -1.98, -0.92), H(0.28, -1.98, -0.92), 0.15))                            # mouth
    gog = mirror([(0.0, 1.38), (1.5, 1.52), (2.35, 1.62), (2.5, 1.32), (1.5, 1.02), (0.0, 0.88)])  # goggles worn up
    P = rwrap_prism(gog)
    g.add((P.offset(0.45) & SKULL.offset(0.5)) - SKULL.offset(0.0), 0.06)                          # goggle body
    g.cut((P & SKULL.offset(1.2)) - SKULL.offset(0.24))                                             # lenses
    g.add((Shape(lambda Q: np.abs(Q[:, 0]) - 0.3, *ALL) & P.offset(0.5)) & SKULL.offset(0.5), 0.04)  # bridge = keel split
    m.glass.append(lambda c, P=P: (P(c) < -0.03) & (SKULL(c) < 0.3) & (np.abs(c[:, 0]) > 0.32))
    for s in (-1, 1):
        g.add(tube([surf(s * 2.75, 1.25, 0.25), surf(s * 3.4, 0.75, 0.25), H(s * 2.05, 0.0, 0.35)], 0.27), 0.06)  # strap
        a, b = H(s * 1.85, 0.0, -0.35), H(s * 2.6, 0.0, -0.35)
        g.add(cyl(a, b, 0.95, 0.28), 0.12)                                                         # ear cup
        g.cut(cyl(b - v3(s * 0.18, 0, 0), b + v3(s * 0.5, 0, 0), 0.55))
        g.add(sphere(b - v3(s * 0.12, 0, 0), 0.27), 0.04)
        g.add(tube([H(s * 1.95, -0.35, -0.95), H(s * 1.05, -1.3, -1.6), H(0, -1.5, -1.72)], 0.27), 0.1)  # chin strap, under the chin
    g.add(tube([H(2.4, -0.45, -0.75), H(1.95, -1.25, -1.0), H(1.1, -1.82, -0.98)], 0.27), 0.06)     # boom mic
    g.add(sphere(H(0.95, -1.86, -0.98), 0.38), 0.06)
    return m


# ------------------------------------------------------------------------------------------------ VH3-07 sniper
def sniper(h=0.05):
    """VH3-07 Longsight: sniper. Compact chevron visor, a long sallet tail sweeping back over the neck (two lames),
    a flip-down monocular on a brow hinge sitting in front of the right lens, a low crest."""
    m = Helm3(h, top=3.6, side=3.9, front=-4.6, back=5.3).skull().plates(crown_t=0.22, nape=False)
    m.glass_visor(VISOR_SNIPE).jaw("std").cheeks(vents=2).ears().prow_vents(rows=(-0.95,)).chin_puck()
    g = m.g
    tail = ellipsoid(H(0, 0.9, -0.1), r(2.4, 3.5, 2.3))
    tail = sinter(sinter(tail, half(H(0, 1.0, 0), (0, -1, 0)) & half(H(0, 0, 1.2), Z) & half(H(0, 3.75, 0), (0, 1, 0)), 0.25),
                  half(H(0, 1.3, -1.95), unit((0, 0.5, -1))), 0.35)                                 # rounded rim, no knife edge
    g.add(tail, 0.35)
    for zl in (0.35, -0.4):                                                                      # two lames across the tail
        band = Shape(lambda Q, z0=hu(zl): np.abs(Q[:, 2] - z0) - 0.16, *ALL)
        side = Shape(lambda Q: np.abs(Q[:, 0]) - 1.45, *ALL)
        back = Shape(lambda Q: HS * 1.6 + HC[1] - Q[:, 1], *ALL)
        g.cut(((band & side & back) & tail.offset(0.6)) - tail.offset(-0.3))
    m.keel(z0=1.2).crest(0.27)
    hub = surf(-R0 * 0.55, 1.62, 0.32)                                                              # flip-down monocular
    g.add(sphere(hub, 0.5), 0.08)
    g.add(cyl(hub - v3(0.45, 0, 0), hub + v3(0.45, 0, 0), 0.38, 0.1), 0.05)                        # hinge pin housing
    eye = surf(-1.15, 0.6, 0.0)
    bc = eye + v3(0, -0.95, 0)
    g.add(capsule(hub, bc + v3(0, 0.25, 0.45), 0.32), 0.06)                                         # drop arm
    m.lens(bc + v3(0, 0.95, 0), bc + v3(0, -0.75, 0), 0.38, depth=0.28, rim=0.24)                   # barrel, glass at the front
    g.add(torus(bc + v3(0, -0.2, 0), (0, 1, 0), 0.62, 0.14), 0.04)                                  # focus ring
    return m


# ------------------------------------------------------------------------------------------------ VH3-08 scarred, relief face
def grim(h=0.05, seed=31):
    """VH3-08 Grimward: veteran's helm with an original relief death's-head faceplate made of Vigil parts (chevron
    lenses as eye sockets under raised brow arcs, a V vent as the nose, cheek ridges, jaw vents as teeth), then
    battle damage: gouges, pits, a bitten crest, a torn cheek corner, a cracked lens and a snapped antenna."""
    m = Helm3(h, top=3.7, side=3.9).skull().plates(crown_t=0.3, brow_lift=0.25)
    g = m.g
    m.faceplate((0, -1.3, -0.45), (1.8, 1.28, 1.6), apex=-2.55, slope=0.28, chin=(-2.05, -1.85), k=0.4)
    m.cheeks(vents=2).ears()
    for s in (-1, 1):
        p, R = m.facet_frame(s, s * 0.95, 0.38)                                                      # chevron eye lenses
        Rl = R @ rot((0, 1, 0), s * 22)
        cutter = rbox(p, (0.62, 0.3, 0.3), Rl, 0.12)
        g.cut(cutter)
        m.glass.append(lambda c, k=cutter: k(c) < 0.03)
        arc = [m.facet_point(s, s * x, z, 0.04)[0] for x, z in ((0.25, 0.86), (0.85, 1.05), (1.55, 0.82), (1.85, 0.42))]
        g.add(tube(arc, 0.26), 0.05)                                                                 # brow arc
        g.add(capsule(m.facet_point(s, s * 0.5, -0.12, 0.04)[0], m.facet_point(s, s * 1.6, -0.42, 0.04)[0], 0.25), 0.05)  # cheek ridge
        g.cut(capsule(m.facet_point(s, 0.0, -0.08, 0.0)[0], m.facet_point(s, s * 0.32, -0.55, 0.0)[0], 0.15))  # nasal vent
    g.add(capsule(m.facet_point(1, -1.25, -0.9, 0.04)[0], m.facet_point(1, 1.25, -0.9, 0.04)[0], 0.26), 0.05)  # upper lip bar
    for s in (-1, 1):                                                                              # teeth = jaw vents
        for xm in (0.36, 1.08):
            p, R = m.facet_frame(s, s * xm / HS, -1.42)
            g.cut(rbox(p, (0.15, 0.32, 0.3), R, 0.05))
    m.crest(0.3, a0=12, a1=78)
    prof = [(-1.2, 2.4), (-0.6, 3.1), (-0.2, 2.8), (0.3, 3.35), (0.6, 3.0), (1.2, 3.95), (2.2, 4.25), (2.8, 3.75),
            (2.9, 2.6), (2.5, 1.4), (0.8, 2.0), (-0.6, 2.0)]
    m.blade_crest(prof, 0.38)                                                                       # shattered keel fin
    g.add(tube([crest_pt(14, 0.1), crest_pt(4, 0.0), m.facet_point(1, 0.0, 0.7, 0.0)[0]], 0.27), 0.05)  # keel to the brow split
    a = H(-2.25, 0.55, 0.3)                                                                         # snapped antenna
    g.add(cyl(a + v3(0.35, 0, 0), a - v3(0.15, 0, 0), 0.55, 0.12), 0.1)
    b = a + unit(v3(-0.12, 0.35, 1)) * 1.5
    g.add(cyl(a, b, 0.42, 0.06), 0.06)                                                             # snapped antenna: flat stump
    g.cut(sphere(b + unit(v3(-0.12, 0.35, 1)) * 0.1, 0.24))                                         # broken core
    gouge(g, surf(0.45, 2.75, 0.24), surf(1.3, 2.3, 0.24), 0.3)                                    # battle damage, inside the crown plate
    gouge(g, surf(0.7, 2.45, 0.24), surf(1.3, 2.1, 0.24), 0.27)
    gouge(g, surf(-0.5, 2.6, 0.24), surf(-1.3, 2.15, 0.24), 0.28)
    notch(g, crest_pt(100, 1.0), (0, 0.17, 0.98), 0.55, 0.75)                                       # crest bitten through
    for q_ in ((-1.45, -2.05, -1.45), (-1.25, -2.2, -1.2)):                                        # shrapnel strikes, right cheek
        pit(g, H(*q_), (-0.5, -0.8, -0.2), 0.3)
    for s, z in ((-2.0, 1.7), (2.2, 1.95), (-3.3, 0.85), (-0.5, 2.45), (3.5, 0.1)):
        pit(g, surf(s, z, 0.25), snorm(s, z), 0.32)
    p, R = m.facet_frame(1, 0.95, 0.38)                                                             # cracked left lens
    for d in ((0.55, 0.35), (-0.5, 0.3), (0.3, -0.42)):
        g.cut(capsule(p + R[:, 1] * 0.05, p + R[:, 0] * d[0] + R[:, 2] * d[1] + R[:, 1] * 0.05, 0.15))
    return m


VH3 = {
    "VH3-01": ("Plummet", "drop trooper: wide wrap chevron visor under a brow shelf, flat keel ridge, flared jaw armour", drop),
    "VH3-02": ("Sightline", "recon: twin chevron lenses, side optic/rangefinder pod, swept whip antenna", recon),
    "VH3-03": ("Ironclad", "heavy assault: portcullis grille faceplate, slit visor, corrugated hoses to a collar ring", assault),
    "VH3-04": ("Herald", "officer: stern frown visor, stepped keel fin crest, comm mast with spars, rank chevrons", officer),
    "VH3-05": ("Stillwater", "sealed void: round globe, domed window split by the keel rib, collar, back pack and hoses", void),
    "VH3-06": ("Deckhand", "open-face crew: low padded cap, chevron goggles worn up, headset cups, boom mic", crew),
    "VH3-07": ("Longsight", "sniper: sallet tail, flip-down monocular, compact chevron visor, low crest", sniper),
    "VH3-08": ("Grimward", "scarred veteran: relief death's-head faceplate of Vigil parts, gouges, bitten crest", grim),
}


def helm_obj(ident, h=0.05):
    """The Helm3 object (sculpt + glass masks) before finishing."""
    return VH3[ident][2](h)


def helm(ident, h=0.05):
    """Finished sculpt (flat neck seat + 1.6 mm D-flat peg) with .glass = list of face-centre masks for display."""
    m = helm_obj(ident, h)
    g = m.finish()
    g.glass = m.glass
    return g


def glass_mask(glass, centres):
    mask = np.zeros(len(centres), bool)
    for f in glass:
        mask |= f(centres)
    return mask
