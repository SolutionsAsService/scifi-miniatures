"""Point tools/sdfkit.py's STEP export at a FreeCAD Python that runs script files only.

sdfkit.write_step() calls "<FREECAD_PYTHON> -c <code>". Some FreeCAD launchers (e.g. the WSL shim
~/ai-stack/freecad-shim/bin/python, which runs "import FreeCAD, Part, runpy; runpy.run_path(argv[0])") take a script path
and treat "-c" as a file name. use() picks the FreeCAD Python ($FREECAD_PYTHON, else the configured path, else the shim)
and, for script-only launchers, writes the code to a temporary .py file. sdfkit.py itself is not modified.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import sdfkit

SHIM = Path.home() / "ai-stack" / "freecad-shim" / "bin" / "python"


class _ScriptRunner:
    """Stands in for the subprocess module inside sdfkit: rewrites [py, "-c", code] to [py, script.py]."""

    @staticmethod
    def run(cmd, **kw):
        if len(cmd) >= 3 and cmd[1] == "-c":
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(cmd[2])
            try:
                return subprocess.run([cmd[0], f.name, *cmd[3:]], **kw)
            finally:
                os.unlink(f.name)
        return subprocess.run(cmd, **kw)


def use():
    py = os.environ.get("FREECAD_PYTHON")
    if not py:
        py = sdfkit.FREECAD_PYTHON if Path(sdfkit.FREECAD_PYTHON).exists() else str(SHIM)
    sdfkit.FREECAD_PYTHON = py
    if "freecad-shim" in py:
        sdfkit.subprocess = _ScriptRunner
    return py
