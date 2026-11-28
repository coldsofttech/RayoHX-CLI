"""Builds the portable command line: compiled wheels, then a frozen one-folder app.

It builds the compiled (Nuitka) rayohx-cli wheel into ``dist/`` (needs a C compiler), installs it
with its dependencies into a fresh environment at ``.freeze/venv`` with PyInstaller, runs
``installer/pyinstaller/rayohx.spec`` and writes ``dist/rayohx-cli-<version>-<os>-<arch>.zip``
(Windows) or ``.tar.gz`` (Linux). The archive holds ``rayohx/rayohx(.exe)`` and ``rayohx/lib/``.
``--no-build`` freezes the wheel already in the folder, such as the one a release builds with
cibuildwheel. With ``--setup`` (Windows) it also wraps the frozen command in an NSIS setup
(``installer/windows/setup.nsi``, settings in ``[setup]`` of ``installer/build.toml``) and writes
``dist/rayohx-cli-<version>-windows-x64-setup.exe``; that needs NSIS (``makensis``). With
``--packages`` (Linux) it writes the ``.deb`` and ``.rpm`` with nfpm
(``installer/linux/nfpm.yaml``). Tool versions are in ``installer/tools.toml``.

Usage: ``python scripts/build.py [--no-build] [--setup | --packages] [--wheels DIR]
[--python 3.15]``
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".freeze"
VENV = WORK / "venv"
SPEC = ROOT / "installer" / "pyinstaller" / "rayohx.spec"
REQUIREMENTS = ROOT / "installer" / "pyinstaller" / "requirements.txt"
INIT = ROOT / "src" / "rayohx_cli" / "__init__.py"
NAME = "rayohx"
BUILD_TOML = ROOT / "installer" / "build.toml"
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


def nsis_text(value: str) -> str:
    return value.replace("$", "$$").replace('"', '$\\"')


def write_files(folder: Path) -> Path:
    """The uninstall macro of the setup: the files it installs, so only those are removed."""
    lines = ["; Written by build.py: what setup puts in the install folder.", "!macro Remove_files"]
    found = sorted(folder.rglob("*"))
    for path in found:
        if path.is_file():
            lines.append(f'  Delete "$INSTDIR\\{nsis_text(str(path.relative_to(folder)))}"')
    for path in sorted((p for p in found if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        lines.append(f'  RMDir "$INSTDIR\\{nsis_text(str(path.relative_to(folder)))}"')
    lines.append("!macroend")
    target = WORK / "files.nsh"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def find_makensis() -> str:
    found = shutil.which("makensis")
    if found:
        return found
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        candidate = Path(os.environ.get(variable, "")) / "NSIS" / "makensis.exe"
        if candidate.is_file():
            return str(candidate)
    raise SystemExit("makensis not found. Install NSIS (version in installer/tools.toml).")


def numeric_version(text: str) -> str:
    numbers = re.findall(r"\d+", text)[:4]
    return ".".join(numbers + ["0"] * (4 - len(numbers)))


def build_setup(folder: Path, out: Path) -> Path:
    """Wrap the frozen command line folder in an NSIS setup and return it."""
    config = tomllib.loads(BUILD_TOML.read_text(encoding="utf-8"))
    setup = config["setup"]
    install_dir = setup["install-dir"]
    start_menu_dir = setup["start-menu-dir"]
    target = out / f"rayohx-cli-{version()}-windows-x64-setup.exe"
    target.unlink(missing_ok=True)
    flags = {
        "GUID": setup["guid"],
        "APP_NAME": setup["title"],
        "APP_VERSION": version(),
        "APP_VERSION_NUMERIC": numeric_version(version()),
        "STAGE_DIR": folder,
        "FILES_FILE": write_files(folder),
        "CLI_EXE": f"{NAME}.exe",
        "OUT_FILE": target,
        "PATH_SCRIPT": ROOT / setup["path-script"],
        "ICON_FILE": ROOT / setup["icon"],
        "HEADER_IMAGE": ROOT / setup["header-image"],
        "WELCOME_IMAGE": ROOT / setup["welcome-image"],
        "LICENSE_FILE": ROOT / setup["licence"],
        "PUBLISHER": config["freeze"]["publisher"],
        "INSTALL_DIR": install_dir.replace("/", "\\"),
        "INSTALL_DIR_DEPTH": len(install_dir.split("/")),
        "START_MENU_DIR": start_menu_dir.replace("/", "\\"),
        "START_MENU_DIR_DEPTH": len(start_menu_dir.split("/")),
        "URL": setup["homepage"],
        "SUPPORT_URL": setup["issues"],
        "UPDATE_URL": setup["changelog"],
    }
    run(find_makensis(), "/V2", *(f"/D{key}={value}" for key, value in flags.items()),
        ROOT / setup["nsi"])  # fmt: skip
    return target


def normalise_modes(folder: Path) -> None:
    """Folders 755, files 644, and 755 for anything executable, whatever the build umask was."""
    for path in [folder, *folder.rglob("*")]:
        if path.is_symlink():
            continue
        if path.is_dir() or path.stat().st_mode & stat.S_IXUSR or ".so" in path.name:
            path.chmod(0o755)
        else:
            path.chmod(0o644)


def build_packages(folder: Path, out: Path, arch: str) -> list[Path]:
    """Package the frozen command line folder as a .deb and an .rpm with nfpm."""
    config = tomllib.loads(BUILD_TOML.read_text(encoding="utf-8"))["setup"]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    author = project["authors"][0]
    maintainer = author["name"] + (f" <{author['email']}>" if "email" in author else "")
    nfpm = shutil.which("nfpm")
    if nfpm is None:
        raise SystemExit("nfpm not found. Install it (version in installer/tools.toml).")
    normalise_modes(folder)
    env = {
        **os.environ,
        "PKG_NAME": NAME,
        "PKG_VERSION": version(),
        "PKG_ARCH": {"x64": "amd64"}.get(arch, arch),
        "PKG_DESCRIPTION": project["description"],
        "PKG_MAINTAINER": maintainer,
        "PKG_HOMEPAGE": config["homepage"],
        "PKG_LICENSE": project["license"],
        "PKG_SOURCE_DIR": str(folder),
        "PKG_LICENSE_FILE": str(ROOT / config["licence"]),
        "PKG_ICON_DIR": str(ROOT / config["icon-dir"]),
    }
    before = set(out.iterdir())
    for packager in ("deb", "rpm"):
        run(nfpm, "package", "--config", ROOT / config["nfpm"], "--packager", packager,
            "--target", out, env=env)  # fmt: skip
    return sorted(set(out.iterdir()) - before)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the portable command line.")
    parser.add_argument(
        "--no-build", action="store_true", help="freeze the wheel already in --wheels"
    )
    parser.add_argument(
        "--setup", action="store_true", help="also build the NSIS setup (Windows, needs NSIS)"
    )
    parser.add_argument(
        "--packages", action="store_true", help="also build the .deb and .rpm (Linux, needs nfpm)"
    )
    parser.add_argument("--wheels", type=Path, default=ROOT / "dist", help="folder with the wheel")
    parser.add_argument("--python", default="3.15", help="Python version of the frozen app")
    args = parser.parse_args()
    args.wheels = args.wheels.resolve()  # makensis resolves a relative output path against the .nsi
    if args.setup and not WINDOWS:
        parser.error("--setup builds the Windows setup, so it needs Windows.")
    if args.packages and WINDOWS:
        parser.error("--packages builds the Linux packages, so it needs Linux.")
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
    if args.setup:
        print(f"wrote {build_setup(folder, args.wheels)}")
    if args.packages:
        for package in build_packages(folder, args.wheels, arch):
            print(f"wrote {package}")


if __name__ == "__main__":
    main()
