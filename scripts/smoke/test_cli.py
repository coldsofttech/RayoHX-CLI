"""Runs ``rayohx info`` from the environment built by setup_venv.py against the first test stream.

Usage: ``python scripts/smoke/test_cli.py``
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAYOHX = HERE / ".venv" / ("Scripts/rayohx.exe" if sys.platform == "win32" else "bin/rayohx")


def main() -> None:
    if not RAYOHX.exists():
        sys.exit("Run setup_venv.py first")
    url = (HERE / "test_links.txt").read_text(encoding="utf-8").splitlines()[0].strip()

    print(f"inspecting: {url}")
    result = subprocess.run([str(RAYOHX), "info", url], check=False)
    if result.returncode != 0:
        sys.exit(f"rayohx info failed (exit {result.returncode})")


if __name__ == "__main__":
    main()
