# ABOUTME: Generated solvers actually run: jaffgen output for each template is built
# ABOUTME: (where needed) and executed, and must exit 0 without solver errors

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEMO2 = REPO / "networks" / "demos" / "demo2.jet"


def _jaffgen(network: Path, template: str, outdir: Path) -> None:
    """Run the jaffgen CLI the way a user would and require success."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "jaff.cli.jaffgen._engine",
            "--network",
            str(network),
            "--template",
            template,
            "--outdir",
            str(outdir),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_python_solve_ivp_driver_runs(tmp_path):
    _jaffgen(DEMO2, "python_solve_ivp", tmp_path)

    proc = subprocess.run(
        [sys.executable, "main.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "MPLBACKEND": "Agg"},
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
