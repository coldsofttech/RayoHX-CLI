"""Builds the compiled (Nuitka) rayohx-cli wheel and installs it into scripts/smoke/.venv.

It needs a C compiler. rayohx (core) comes from PyPI unless ``--core-wheels`` names a folder with
a compiled core wheel, which is used first.

Usage: ``python scripts/smoke/setup_venv.py [--python 3.11] [--core-wheels DIR]``
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VENV = HERE / ".venv"
WHEELS = HERE / "wheels"


def venv_python() -> Path:
    """The interpreter inside the smoke environment."""
    return VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(*command: str | Path, env: dict[str, str] | None = None) -> None:
    """Run a command in the repository root, stopping the script if it fails."""
    subprocess.run([str(part) for part in command], check=True, cwd=ROOT, env=env)


def create_venv(version: str | None) -> None:
    """Make a fresh environment, with the current Python or the requested version through uv."""
    if VENV.exists():
        shutil.rmtree(VENV)
    if version:
        run("uv", "venv", "--python", version, VENV)
        run("uv", "pip", "install", "--python", venv_python(), "pip")
    else:
        run(sys.executable, "-m", "venv", VENV)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", help="Python version for the environment, for example 3.11")
    parser.add_argument("--core-wheels", type=Path, help="folder with a compiled rayohx wheel")
    args = parser.parse_args()
    if args.core_wheels and not args.core_wheels.is_dir():
        sys.exit(f"The compiled core wheel folder is missing: {args.core_wheels}")

    create_venv(args.python)
    python = venv_python()
    run(python, "-m", "pip", "install", "--upgrade", "pip", "build", "nuitka", "setuptools")
    run(python, "-m", "pip", "install", "wheel", "mypy>=1.13")

    # Install core first, then the CLI's own dependencies.
    find_links = ["--find-links", str(args.core_wheels)] if args.core_wheels else []
    run(python, "-m", "pip", "install", *find_links, "rayohx")
    run(python, "-m", "pip", "install", "click>=8.5.1", "rich>=13.9", "typer>=0.29.1")

    if WHEELS.exists():
        shutil.rmtree(WHEELS)
    run(
        python, "-m", "build", "--wheel", "--no-isolation", "--outdir", WHEELS,
        env={**os.environ, "PYD_BUILD": "1"},
    )  # fmt: skip

    wheel = next(WHEELS.glob("rayohx_cli-*.whl"))
    run(python, "-m", "pip", "install", "--force-reinstall", "--no-deps", wheel)
    run(python, "-c", "import rayohx_cli, rayohx; print('installed:', rayohx_cli.__file__)")


if __name__ == "__main__":
    main()
