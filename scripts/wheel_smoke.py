"""Checks that an installed rayohx-cli wheel loads and runs. The release build runs it per wheel.

It does not repeat the unit tests, which pull requests already run on the source. It proves what
they cannot: the compiled binary for this platform and Python version imports, reports the version
it was built as, and starts the command.

Usage: ``python scripts/wheel_smoke.py [--compiled]``. With ``--compiled`` it fails when the
loaded package is plain Python instead of the compiled binary.
"""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys


def main() -> int:
    import rayohx_cli

    # Nuitka modules report __file__ as rayohx_cli/__init__.py, so check the loader instead.
    loader = type(rayohx_cli.__spec__.loader).__name__
    compiled = "nuitka" in loader.lower() or "Extension" in loader
    print(f"rayohx-cli {rayohx_cli.__version__} from {rayohx_cli.__file__} (loader: {loader})")
    if "--compiled" in sys.argv and not compiled:
        print("FAIL: the loaded package is not the compiled build", file=sys.stderr)
        return 1

    installed = importlib.metadata.version("rayohx-cli")
    if installed != rayohx_cli.__version__:
        print(f"FAIL: metadata says {installed}, the package says {rayohx_cli.__version__}")
        return 1

    result = subprocess.run(
        [sys.executable, "-m", "rayohx_cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.startswith("rayohx "):
        print(f"FAIL: `rayohx --version` gave {result.returncode}: {result.stdout}{result.stderr}")
        return 1

    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
