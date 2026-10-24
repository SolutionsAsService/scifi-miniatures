"""Power-armour kit for the Vigil 0.2 figures (Heavy Gunner 0.2, Commander 0.2): the same posed skeleton, sockets,
footplate and base as tools/exosuit.py (so every 0.1 helm, pack and base still fits), dressed in much heavier armour.

The bulk numbers come from unified-CAD-MCP miniature_power_armor_plan (archetypes heavy / commander at a 33 mm crown):
domed pauldrons 8-10 mm across that rise to ~3 mm under the helm crown, a barrel cuirass with a raised split-chevron
emblem, a high back collar the helm sits down into, three abdominal lames, heavy tassets with trim bands, massive
bracers and greaves, knee hydraulics, big boots, and reactor / comms backpacks moved out by the thicker back plate.
Plate steps 0.66-0.83 mm, trim bands 0.6+ mm wide and 0.2 mm proud, lame gaps 0.5 mm, bolts 0.5-0.55 mm on >= 1.0 mm
pitch, piston rods >= 1.0 mm (all from the plan, floored to MSLA limits).

Exosuit is not modified: figure_pa() calls exosuit.figure() for the bodysuit and 0.1 armour, adds the power armour
over it, then re-cuts the neck socket and moves the backpack socket out to the new back face.
Use: build_pa(pkg, spec, pose, extras, helm_ident, pack, notes).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import exosuit as X
import helms04
import morph
import sdfkit
from exosuit import PEG_HEAD, PEG_PACK, RY, Z, plate, side_frame
from render import render
from sdfkit import (Package, Sculpt, Shape, capsule, cyl, d_peg, ellipsoid, frame, half, rbox, rot, round_cone, sphere,
                    torus, translate, unit, v3)

I3 = np.eye(3)
BACK_T = 1.2                    # the power-armour back plate stands this far off the 0.1 pack boss face


def ell_point(c, radii, R, d):
    """Point on the ellipsoid (centre c, radii along R's columns) in local direction d."""
    d = np.asarray(d, float)
    q = d / math.sqrt(sum((d[i] / radii[i]) ** 2 for i in range(3)))
    return v3(c) + R @ q


def band(shape, c, n, lo, hi):
    """The part of 'shape' between two planes normal to n through c + n*lo and c + n*hi."""
    return shape.clip(half(v3(c) + unit(n) * lo, -unit(n)), half(v3(c) + unit(n) * hi, unit(n)))


def collar(P, r_in=4.0, r_out=4.75, z_lo=-1.2, z_hi=2.6, front_open=0.35):
    """High back collar round the helm (the 'sunk head'): a ring r_in..r_out from the neck axis, open at the front."""
    Rc, c = P.Rc, P.neck_cut

    def f(Q):
        q = (Q - c) @ Rc
        rho = np.hypot(q[:, 0], q[:, 1])
        top = z_hi - 0.35 * np.clip(-q[:, 1] / np.maximum(rho, 1e-6), 0, 1) * 2.0     # lower at the sides than the back
        return np.max(np.stack([r_in - rho, rho - r_out, z_lo - q[:, 2], q[:, 2] - top,
                                -(q[:, 1] + front_open * rho)]), axis=0)
    return Shape(f, c - 6, c + 6)


# ------------------------------------------------------------------------------------------------ body
def figure_pa(pose, h=0.12, extras=(), bbox=None, kind="heavy", emblem=None):
    """exosuit.figure() body (no extras) + power armour + extras; sockets re-cut. kind: 'heavy' or 'commander'.
    emblem(g, front, Rc) replaces the split-chevron chest emblem (front: centre of the cuirass face)."""
    P = pose
    hv = kind == "heavy"
    lo, hi = bbox or ((-13.5, -19.5, -X.PLINTH_T - 0.2), (13.5, 10.5, P.cut_z + 5.5))
    g = X.figure(P, h=h, extras=(), bbox=(lo, hi))
    Rc, Rp, Rm = P.Rc, P.Rp, P.Rmid
    up = Rc @ Z
    t_plate = 0.83 if hv else 0.66

    # ---- pauldrons: big domes with a trim band at the rim, three bolts, two lames hanging below
    for i, sgn in ((0, -1), (1, 1)):
        sh = P.sh[i]
        out = Rc @ v3(sgn, 0, 0)
        R = Rc @ rot(RY, -sgn * 14)
        radii = (4.2, 4.4, 2.95) if hv else (3.85, 4.05, 2.75)
        c = sh + out * 1.55 + up * 1.35
        dome = ellipsoid(c, radii, R).clip(half(c - up * 1.75, -up))
        g.add(dome, 0.35)
        g.add(band(ellipsoid(c, tuple(r + 0.5 for r in radii), R), c, up, -1.75, -1.15), 0.08)               # flared rim flange
        g.add(band(ellipsoid(c, tuple(r + 0.18 for r in radii), R), c, R[:, 0] * sgn, radii[0] - 0.9, radii[0] - 0.3), 0.06)  # outer edge trim
        for a in (-35, 0, 35):                                                                               # bolts on the front
            t = math.radians(a)
            p = ell_point(c, radii, R, (sgn * math.sin(t) * 0.6, -math.cos(t), 0.15))
            g.add(sphere(p, 0.28 if hv else 0.25), 0.03)
        for j in range(2):                                                                                   # lames
            cj = c - up * (2.35 + 1.35 * j)
            rj = tuple(r * (0.82 - 0.09 * j) for r in radii)
            g.add(band(ellipsoid(cj, rj, R), cj, up, -0.45, 0.4), 0.1)
        if not hv and i == 1:                                                                                # commander: raised chevron
            p0 = ell_point(c, radii, R, (sgn * 0.55, -0.35, 0.75))
            for s2 in (-1, 1):
                g.add(capsule(p0 + Rc @ v3(s2 * 1.1, 0, 0.55), p0 + Rc @ v3(0, 0, -0.35), 0.3), 0.04)

    # ---- chest barrel with the split-chevron emblem and keel
    ribs = ellipsoid(P.chest + Rc @ v3(0, 0.05, 0.35), (4.6, 3.05, 3.4), Rc)
    cuir = ribs.offset(1.2 if hv else 1.0).clip(half(P.chest + Rc @ v3(0, 0, -2.4), -up), half(P.chest + Rc @ v3(0, 0, 3.4), up),
                                                half(P.chest + Rc @ v3(0, -4.4, 0), Rc @ unit((0.33, -1, 0.1))),
                                                half(P.chest + Rc @ v3(0, -4.4, 0), Rc @ unit((-0.33, -1, 0.1))))
    g.add(cuir, 0.3)
    front = P.chest + Rc @ v3(0, -4.45 if hv else -4.25, 0.8)
    if emblem:
        emblem(g, front, Rc)
    else:
        for s in (-1, 1):                                                                                     # split chevron, raised
            g.add(capsule(front + Rc @ v3(s * 2.3, -0.1, 1.2), front + Rc @ v3(s * 0.45, 0.0, -0.6), 0.36), 0.05)
    g.add(capsule(front + Rc @ v3(0, 0.05, 1.9), front + Rc @ v3(0, 0.3, -2.6), 0.32), 0.05)                # keel
    for s in (-1, 1):                                                                                         # side vents (raised fins)
        for j in range(3):
            p = P.chest + Rc @ v3(s * (5.25 if hv else 5.0), -0.6 + 0.95 * j, -0.9)
            g.add(rbox(p, (0.3, 0.21, 0.9), Rc, 0.08), 0.06)

    # ---- collar: the helm sits down inside it
    g.add(collar(P, r_out=4.85 if hv else 4.7, z_hi=2.8 if hv else 2.3), 0.3)

    # ---- abdominal lames, belt with pouches, tassets with trim
    abdomen = ellipsoid(P.pelvis + Rm @ v3(0, 0.05, 2.8), (3.15, 2.3, 2.6), Rm)
    for zc in (0.95, 2.25, 3.55):
        g.add(band(abdomen.offset(0.75), P.pelvis, Rm @ Z, zc - 0.4, zc + 0.4).clip(half(P.pelvis + Rm @ v3(0, 0.8, 0), Rm @ v3(0, 1, 0))), 0.12)
    g.add(torus(P.pelvis + Rp @ v3(0, 0.1, 1.15), Rp @ Z, 3.25, 0.62), 0.3)                                 # belt
    for s in (-1, 1):
        for j in (0, 1):
            g.add(rbox(P.pelvis + Rp @ v3(s * (2.2 + 1.15 * j), -1.9 + 1.7 * j, 0.95), (0.55, 0.5, 0.7), Rp @ rot(Z, s * (25 + 30 * j)), 0.2), 0.1)
    pelvis = ellipsoid(P.pelvis + Rp @ v3(0, 0.1, 0.25), (2.85, 2.05, 2.1), Rp)
    for i, sgn in ((0, -1), (1, 1)):
        tc = P.pelvis + Rp @ v3(sgn * 3.25, -0.4, -0.55)
        g.add(plate(pelvis, t_plate + 0.2, tc, (1.6, 2.1, 2.0), Rp), 0.15)
        g.add(band(plate(pelvis, t_plate + 0.4, tc, (1.7, 2.2, 2.1), Rp), tc, Rp @ Z, -2.2, -1.5), 0.05)   # trim at the hem

    # ---- arms: big upper plates, elbow cops, gauntlet housings
    for i, sgn in ((0, -1), (1, 1)):
        sh, el, wr = P.sh[i], P.elbow[i], P.wrist[i]
        ua, fa = el - sh, wr - el
        Ru, outa = side_frame(Rc @ v3(sgn, 0, 0), ua)
        upper = round_cone(sh, el, 1.5, 1.2)
        g.add(plate(upper, 0.7, sh + ua * 0.6 + outa * 1.55, (1.7, 1.6, 1.8), Ru), 0.12)
        ep = el - (sh + wr) / 2
        ep = unit(ep) if np.linalg.norm(ep) > 0.3 else -P.cfwd
        g.add(ellipsoid(el + ep * 0.85, (1.5, 1.5, 1.65), frame(ua, ep)), 0.2)                              # elbow cop
        fore = round_cone(el, wr, 1.4, 1.1)
        g.add(band(fore.offset(1.05 if hv else 0.9), el, fa, 0.15 * np.linalg.norm(fa), 0.92 * np.linalg.norm(fa)), 0.2)  # gauntlet housing
        g.add(band(fore.offset(1.3 if hv else 1.15), el, fa, 0.8 * np.linalg.norm(fa), 0.95 * np.linalg.norm(fa)), 0.05)   # cuff trim

    # ---- legs: thigh plates, knee pads with a ridge, greaves, knee hydraulics, heavy boots
    for i, sgn in ((0, -1), (1, 1)):
        hip, knee, ank = P.hip[i], P.knee[i], P.ankle[i]
        ax = knee - hip
        R = frame(ax, P.fwd)
        w = R[:, 1]
        thigh = round_cone(hip + v3(0, 0, 0.3), knee, 2.15, 1.6)
        L = float(np.linalg.norm(ax))
        g.add(band(thigh.offset(1.15 if hv else 1.0), hip, ax, 0.12 * L, 0.86 * L), 0.35)              # thigh shell (leg day)
        g.add(plate(thigh, t_plate + 0.25, hip + ax * 0.5 + w * 2.1, (2.2, 2.15, 3.4), R), 0.12)
        Ro, outl = side_frame(Rp @ v3(sgn, 0, 0), ax)
        g.add(plate(thigh, t_plate + 0.1, hip + ax * 0.35 + outl * 2.1, (2.0, 2.0, 2.6), Ro), 0.12)
        kp = knee - (hip + ank) / 2
        kp = unit(kp) if np.linalg.norm(kp) > 0.4 else w
        kp = unit(kp + w * 0.6)
        sx = ank - knee
        Rs = frame(sx, kp)
        g.add(ellipsoid(knee + kp * 1.7 + unit(sx) * 0.2, (2.25, 1.55, 2.5), Rs), 0.25)                    # knee pad
        g.add(capsule(knee + kp * 3.15 + unit(sx) * -1.3, knee + kp * 3.1 + unit(sx) * 1.6, 0.34), 0.06)    # pad ridge
        shin = round_cone(knee, ank, 1.55, 1.2)
        Ls = float(np.linalg.norm(sx))
        g.add(band(shin.offset(1.2 if hv else 1.05), knee, sx, 0.14 * Ls, 0.88 * Ls), 0.35)            # greave shell
        g.add(plate(shin, t_plate + 0.3, knee + sx * 0.55 + Rs[:, 1] * 1.6, (2.2, 2.0, 3.8), Rs), 0.12)     # greave
        g.add(plate(shin, t_plate, knee + sx * 0.38 - Rs[:, 1] * 1.8, (1.8, 1.7, 2.2), Rs), 0.12)           # calf plate
        a = knee + outl * 2.75 - ax * 0.32                                                                   # knee hydraulic
        b = knee + outl * 2.6 + sx * 0.38
        g.add(cyl(a, a + unit(b - a) * 1.6, 0.82 if hv else 0.72, 0.15), 0.1)                               # cylinder
        g.add(capsule(a, b, 0.52 if hv else 0.48), 0.06)                                                     # rod
        for p in (a, b):
            g.add(sphere(p, 0.6), 0.08)                                                                      # pivots
        fd = unit(rot(Z, P.feet_yaw[i]) @ P.fwd)
        Rf = np.stack([np.cross(fd, Z), fd, Z], axis=1)
        boot = rbox(ank + fd * 1.1 + v3(0, 0, -0.75), (2.5, 3.6, 1.4), Rf, 0.6)
        boot = boot | ellipsoid(ank + fd * 3.4 + v3(0, 0, -0.8), (2.2, 1.75, 1.3), Rf)
        boot = boot | round_cone(ank + v3(0, 0, -0.9), ank + v3(0, 0, 1.9), 2.5, 2.25)
        g.add(boot.clip(half(v3(0, 0, 0), -Z)), 0.3)
        g.add(band(boot.offset(0.18).clip(half(v3(0, 0, 0), -Z)), v3(0, 0, 0), Z, 0.05, 0.6), 0.05)        # sole band

    # ---- hands, weapons and gear
    for fn in extras:
        fn(g, P)

    # ---- sockets: neck (unchanged position) and the backpack, moved out to the new back face
    g.cut(cyl(P.neck_cut, P.neck_cut + v3(0, 0, 9), 2.2))
    g.cut(d_peg(P.neck_cut + v3(0, 0, 0.01), (0, 0, -1), PEG_HEAD["d"], PEG_HEAD["sock_depth"], key=P.key_dir(), grow=0.1))
    mount = X.pack_mount(P) + Rc @ v3(0, BACK_T, 0)
    g.add(rbox(mount - Rc @ v3(0, 0.7, 0), (1.9, 0.7, 2.1), Rc, 0.3), 0.15)
    g.cut(d_peg(mount + Rc @ v3(0, 0.01, 0), Rc @ v3(0, -1, 0), PEG_PACK["d"], PEG_PACK["sock_depth"], key=Rc @ Z, grow=0.1))
    return g


def pack_placement_pa(P):
    return X.pack_placement(P) @ translate(0, BACK_T, 0)


# ------------------------------------------------------------------------------------------------ backpacks
def reactor_pack(h=0.07):
    """Power-armour reactor pack: armoured core, a horizontal fusion-cell drum with a raised window frame, two exhaust
    stacks with open bores (0.47 mm walls), cooling fins, top armour plate. Frame as exosuit.backpack (front y = 0)."""
    g = Sculpt((-6.6, -PEG_PACK["len"] - 0.3, -6.0), (6.6, 6.2, 9.0), h)
    g.add(rbox(v3(0, 2.0, 0.6), (4.1, 2.0, 3.6), I3, 0.9))                                                   # core
    g.add(rbox(v3(0, 2.3, 4.0), (4.4, 2.2, 0.55), I3, 0.3), 0.2)                                             # top armour plate
    g.add(cyl(v3(-3.0, 4.15, 0.2), v3(3.0, 4.15, 0.2), 1.55, 0.35), 0.25)                                    # fusion-cell drum
    g.add(torus(v3(0, 5.55, 0.2), (0, 1, 0), 0.95, 0.24), 0.04)                                              # cell window frame
    g.add(sphere(v3(0, 5.3, 0.2), 0.75), 0.05)                                                               # cell window dome
    for s in (-1, 1):
        a, b = v3(s * 3.1, 2.4, 2.6), v3(s * 3.4, 2.7, 7.6)
        g.add(cyl(a, b, 0.95, 0.2), 0.2)                                                                     # exhaust stack
        g.add(cyl(b - unit(b - a) * 0.3, b + unit(b - a) * 0.15, 1.15, 0.12), 0.05)                         # stack lip
        g.cut(cyl(b - unit(b - a) * 1.4, b + unit(b - a) * 0.6, 0.48))                                       # bore (0.47 wall)
        for j in range(3):
            g.add(cyl(a + unit(b - a) * (0.9 + 0.95 * j) - unit(b - a) * 0.21, a + unit(b - a) * (0.9 + 0.95 * j) + unit(b - a) * 0.21, 1.25, 0.08), 0.03)  # fins
    for j in range(3):                                                                                        # lower vents (raised louvres)
        g.add(rbox(v3(0, 4.1, -2.3 + 0.95 * j), (2.6, 0.3, 0.22), I3, 0.08), 0.05)
    g.cut(Shape(lambda Q: Q[:, 1], (-9, -9, -9), (9, 0, 12)))                                                 # flat front at y = 0
    g.add(d_peg((0, 0.3, 0), (0, -1, 0), PEG_PACK["d"], PEG_PACK["len"] + 0.3, key=(0, 0, 1)))
    return g


def command_pack(h=0.07):
    """Commander pack: armoured core with the comms mast, a banner pole socket and a cell, two short exhausts."""
    g = Sculpt((-5.6, -PEG_PACK["len"] - 0.3, -5.6), (5.6, 5.6, 13.0), h)
    g.add(rbox(v3(0, 1.8, 0.5), (3.6, 1.8, 3.3), I3, 0.85))
    g.add(rbox(v3(0, 2.1, 3.6), (3.9, 2.0, 0.5), I3, 0.3), 0.2)
    g.add(rbox(v3(1.6, 3.6, 0.0), (1.4, 0.9, 2.2), I3, 0.4), 0.2)                                            # cell
    for j in range(3):
        g.add(rbox(v3(1.6, 4.55, -1.2 + 0.95 * j), (1.0, 0.25, 0.22), I3, 0.08), 0.05)
    g.add(cyl(v3(-1.9, 1.8, 3.8), v3(-1.9, 1.8, 4.9), 0.8, 0.2), 0.15)                                      # mast boss
    g.add(capsule(v3(-1.9, 1.8, 4.6), v3(-2.3, 2.6, 11.6), 0.45), 0.1)                                      # comms mast
    g.add(sphere(v3(-2.3, 2.6, 11.6), 0.62), 0.05)
    for z in (8.0, 9.6):                                                                                      # mast cross spars
        p = v3(-1.9, 1.8, 4.6) + unit(v3(-0.4, 0.8, 7.0)) * (z - 4.6)
        g.add(capsule(p - v3(0.8, 0, 0), p + v3(0.8, 0, 0), 0.4), 0.05)
    for s in (-1, 1):
        a = v3(s * 2.6, 2.4, -2.6)
        b = a + unit(v3(s * 0.25, 0.5, -1)) * 1.9
        g.add(cyl(a, b, 0.85, 0.2), 0.2)
        g.cut(cyl(b - unit(b - a) * 1.0, b + unit(b - a) * 0.6, 0.38))                                       # bore (0.47 wall)
    g.cut(Shape(lambda Q: Q[:, 1], (-9, -9, -9), (9, 0, 14)))
    g.add(d_peg((0, 0.3, 0), (0, -1, 0), PEG_PACK["d"], PEG_PACK["len"] + 0.3, key=(0, 0, 1)))
    return g


# ------------------------------------------------------------------------------------------------ package
COLORS = {"figure": "#7d8c96", "helm": "#8a98a1", "backpack": "#5d6a73", "base": "#6c6863"}


def build_pa(pkg, spec, pose, extras, helm_ident, pack, notes, kind):
    """Like vigil.build_figure, with figure_pa, a VH4 helm (print-safe filtered) and a power-armour pack."""
    pkg = Path(pkg)
    mid, bd = spec["id"], spec["base"]["d"]
    H0 = X.BASES[bd]["h"]
    body_g = figure_pa(pose, h=spec.get("voxel_mm", 0.12), extras=extras, bbox=spec.get("bbox"), kind=kind)
    D0 = body_g.D.copy()
    morph.print_safe_selective(body_g)          # layered plates leave knife lips at their rims: fix only those
    # Mating surfaces stay exactly as sculpted: the footplate (seats in the base recess) and the neck and pack sockets.
    n = body_g.D.shape
    ax = [body_g.lo[i] + body_g.h * np.arange(n[i]) for i in range(3)]
    Xg, Yg, Zg = np.meshgrid(*ax, indexing="ij")
    keep = Zg < 0.3
    mount = X.pack_mount(pose) + pose.Rc @ v3(0, BACK_T, 0)
    for c, rad in ((pose.neck_cut, 2.6), (mount, 3.2)):
        keep |= (Xg - c[0]) ** 2 + (Yg - c[1]) ** 2 + (Zg - c[2]) ** 2 < rad ** 2
    body_g.D = np.where(keep, D0, body_g.D)
    del D0, Xg, Yg, Zg, keep
    body = body_g.mesh("figure", 280_000)
    hg = helms04.helm(helm_ident)
    morph.print_safe_selective(hg)
    helm = hg.mesh("helm", None)
    pg = pack()
    morph.print_safe_selective(pg)
    pk = pg.mesh("backpack", 200_000)
    base = X.base(pose, d=bd, seed=spec.get("base_seed", 1)).mesh("base", 200_000)
    sdfkit.write_step = lambda path, parts: None        # no STEP for the 0.2 figures (STLs are the print files)
    k = Package(mid, pkg)
    lift = translate(0, 0, H0)
    k.add(notes["figure"][0], body, stl="figure", color=COLORS["figure"], group="figure", note=notes["figure"][1],
          explode=(0, 0, 6), placement=lift)
    k.add(notes["helm"][0], helm, stl="helm", color=COLORS["helm"], group="helm", note=notes["helm"][1],
          explode=(0, 0, 14), placement=lift @ X.helm_placement(pose))
    back = pose.Rc @ np.array([0, 1.0, 0])
    k.add(notes["backpack"][0], pk, stl="backpack", color=COLORS["backpack"], group="backpack", note=notes["backpack"][1],
          explode=tuple(np.round(back * 10 + np.array([0, 0, 6]), 2)), placement=lift @ pack_placement_pa(pose))
    k.add(f"{bd} mm base", base, stl="base", color=COLORS["base"], group="base",
          note=f"{bd} mm round deck-plate base: keyed recess for the footplate, 5 x 2 mm magnet pocket vented to the rim.")
    rep = k.write()
    asm_helm = [p for p in k.parts if p["stl"] == "helm"][0]["asm"]
    rep["heights_above_base_top_mm"] = {"crown": round(float(asm_helm.bounds[1][2] - H0), 2)}
    (pkg / "reports" / "build.json").write_text(json.dumps(rep, indent=1))
    out = pkg / "images"
    out.mkdir(exist_ok=True)
    meshes = [(p["asm"], p["color"]) for p in k.parts]
    render(meshes, out / f"{mid}-turnaround.png", size=480, title=f"{spec['name']}: 3/4, front, right side, back (orthographic)")
    render(meshes, out / f"{mid}-hero.png", views=((-32, 10, "3/4 front"),), size=900)
    return rep
