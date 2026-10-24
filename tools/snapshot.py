"""Versioned build snapshots: freeze the exact kit code a package was built with, beside its sources.

    import snapshot
    snapshot.save(PKG)            # at the end of a build.py: copies every loaded kit module into <pkg>/source/kit/ and writes kit.json

A future rebuild of a 0.1 then does not depend on how the kits have changed since: run `python source/build.py` with
PYTHONPATH=<pkg>/source/kit first on the path (the files keep their module names). kit.json records each module's sha256 and the git
HEAD of every repo the modules came from, and the Python/numpy/skimage/trimesh/manifold3d versions.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_ROOTS = [Path(r"E:\scifi-miniatures\tools"), Path(r"E:\solar-legion-min\tools"), Path(r"E:\neowest-minatures\tools"),
              Path(r"E:\signal-eaters-min\tools"), Path(r"E:\gilded-hand-miniatures\tools"), Path(r"E:\fantasy-miniatures\tools")]


def _git_head(repo):
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def save(pkg, extra=()):
    pkg = Path(pkg)
    dest = pkg / "source" / "kit"
    mods = {}
    for name, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        f = Path(f).resolve()
        for root in TOOL_ROOTS:
            try:
                f.relative_to(root.resolve())
            except ValueError:
                continue
            mods[name] = (f, root)
    for e in extra:
        e = Path(e).resolve()
        mods[e.stem] = (e, e.parent)
    info = {}
    for name, (f, root) in sorted(mods.items()):
        sub = dest / root.parent.name
        sub.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, sub / f.name)
        info[name] = {"repo": root.parent.name, "file": f.name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()[:16]}
    repos = {r.parent.name: _git_head(r.parent) for r in TOOL_ROOTS if r.exists()}
    vers = {}
    for lib in ("numpy", "skimage", "trimesh", "manifold3d", "scipy"):
        try:
            vers[lib] = __import__(lib).__version__
        except Exception:
            pass
    (dest / "kit.json").write_text(json.dumps({"python": sys.version.split()[0], "libs": vers, "repo_heads": repos, "modules": info}, indent=1))
    return info
