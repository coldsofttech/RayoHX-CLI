# Smoke test for the compiled build

A manual check that the compiled `rayohx-cli` wheel (a single Nuitka `.pyd` or `.so` plus type stubs)
installs and runs in a fresh virtual environment. It is separate from the pytest suites.

## What you need

- Python 3.11 or newer. Use `--python` to ask [uv](https://docs.astral.sh/uv/) for another version.
- A C compiler, because Nuitka compiles the package.
- Network access, to install dependencies and to reach the test stream.

## Steps

Run these from the repository root. They work on Windows, Linux and macOS.

```sh
python scripts/smoke/setup_venv.py   # builds the wheel and installs it into scripts/smoke/.venv
python scripts/smoke/test_cli.py     # runs `rayohx info` from the installed build
```

### `setup_venv.py`

Creates a fresh `scripts/smoke/.venv`, installs the dependencies, builds the compiled wheel into
`scripts/smoke/wheels/`, installs it and prints where `rayohx_cli` was loaded from. Any earlier
environment and wheels are removed first.

| Option | What it does |
|---|---|
| `--python VERSION` | Create the environment with another Python version through uv, for example `--python 3.12`. Without it, the Python that runs the script is used. |
| `--core-wheels DIR` | Install `rayohx` (core) from a folder of compiled wheels first. Without it, `rayohx` comes from PyPI. |

### `test_cli.py`

Runs `rayohx info` from the environment on the **first line** of `test_links.txt` and fails if the
command exits with an error. It stops with "Run setup_venv.py first" when there is no environment.

To try another stream, put its URL on the first line of `test_links.txt`; any further lines are
ignored. The file is kept in the repository, so use a stream you are allowed to share.

## Files

| File | What it is |
|---|---|
| `setup_venv.py` | Builds and installs the compiled wheel |
| `test_cli.py` | Runs `rayohx info` from the installed build |
| `test_links.txt` | Test stream addresses; the first line is used |

The virtual environment, `wheels/`, `data/` and logs in this folder are git-ignored.
