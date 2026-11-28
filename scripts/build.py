"""Builds the portable command line: compiled wheels, then a frozen one-folder app.

It builds the compiled (Nuitka) rayohx-cli wheel into ``dist/`` (needs a C compiler), installs it
with its dependencies into a fresh environment at ``.freeze/venv`` with PyInstaller, runs
``installer/pyinstaller/rayohx.spec`` and writes ``dist/rayohx-cli-<version>-<os>-<arch>.zip``
(Windows) or ``.tar.gz`` (Linux). The archive holds ``rayohx/rayohx(.exe)`` and ``rayohx/lib/``.
``--no-build`` freezes the wheel already in the folder, such as the one a release builds with
cibuildwheel.

Usage: ``python scripts/build.py [--no-build] [--wheels DIR] [--python 3.15]``
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".freeze"
VENV = WORK / "venv"
SPEC = ROOT / "installer" / "pyinstaller" / "rayohx.spec"
REQUIREMENTS = ROOT / "installer" / "pyinstaller" / "requirements.txt"
INIT = ROOT / "src" / "rayohx_cli" / "__init__.py"
NAME = "rayohx"
WINDOWS = sys.platform == "win32"
ARCHITECTURES = {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}


def run(*command: str | Path, env: dict[str, str] | None = None) -> None:
    """Run a command, stopping the script if it fails."""
    subprocess.run([str(part) for part in command], check=True, cwd=ROOT, env=env)


def version() -> str:
    """The command's ``__version__``, which names the archive."""
    match = re.search(r'^__version__ = "([^"]+)"', INIT.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise SystemExit(f"No __version__ in {INIT}.")
    return match.group(1)


def wheel(folder: Path) -> Path:
    """The one compiled rayohx-cli wheel for this Python in ``folder``."""
    found = sorted(folder.glob("rayohx_cli-*.whl"))
    if len(found) != 1:
        raise SystemExit(f"Expected one rayohx_cli wheel in {folder}, found {len(found)}.")
    return found[0]


def archive(folder: Path, target: Path) -> None:
    """Pack ``folder`` as ``target``: a zip on Windows, a tar.gz elsewhere (keeps permissions)."""
    target.unlink(missing_ok=True)
    if WINDOWS:
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    out.write(path, Path(NAME) / path.relative_to(folder))
    else:
        with tarfile.open(target, "w:gz") as out:
            out.add(folder, arcname=NAME)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the portable command line.")
    parser.add_argument(
        "--no-build", action="store_true", help="freeze the wheel already in --wheels"
    )
    parser.add_argument("--wheels", type=Path, default=ROOT / "dist", help="folder with the wheel")
    parser.add_argument("--python", default="3.15", help="Python version of the frozen app")
    args = parser.parse_args()
    if sys.platform not in {"win32", "linux"}:
        raise SystemExit("The portable build is for Windows and Linux only.")
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv must be on PATH.")
    if not args.no_build:
        for old in args.wheels.glob("rayohx_cli-*.whl"):
            old.unlink()
        run(uv, "build", "--wheel", "--python", args.python, "--out-dir", args.wheels,
            env={**os.environ, "PYD_BUILD": "1"})  # fmt: skip
    built = wheel(args.wheels)

    shutil.rmtree(WORK, ignore_errors=True)
    run(uv, "venv", "--python", args.python, VENV)
    python = VENV / ("Scripts/python.exe" if WINDOWS else "bin/python")
    run(uv, "pip", "install", "--python", python, "-r", REQUIREMENTS, built)

    out = WORK / "dist"
    run(python, "-m", "PyInstaller", SPEC, "--noconfirm", "--distpath", out,
        "--workpath", WORK / "work")  # fmt: skip
    folder = out / NAME
    run(folder / (f"{NAME}.exe" if WINDOWS else NAME), "--version")  # starts and imports the app

    system = "windows" if WINDOWS else "linux"
    arch = ARCHITECTURES.get(platform.machine().lower(), platform.machine().lower())
    suffix = "zip" if WINDOWS else "tar.gz"
    target = args.wheels / f"rayohx-cli-{version()}-{system}-{arch}.{suffix}"
    archive(folder, target)
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
