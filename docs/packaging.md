# CLI packaging

How the `rayohx` command is packaged: the `rayohx-cli` package on PyPI. For how a release is made, see [releasing](releasing.md).

## What is built

| Where | What you get | Built with |
| --- | --- | --- |
| Windows, Linux or macOS with Python 3.11 or newer | the `rayohx-cli` compiled wheels on PyPI (no sdist) | `PYD_BUILD=1 uv build --wheel` |
| Windows | the setup and a portable zip, from the [RayoHX-Installer](https://github.com/coldsofttech/RayoHX-Installer) repository | PyInstaller and NSIS |
| Linux | `.deb` and `.rpm` packages, from the [RayoHX-Installer](https://github.com/coldsofttech/RayoHX-Installer) repository | PyInstaller and nfpm |
| macOS | no installer: install the PyPI package | |

The installers are not built here. They bundle the published command line, and they are built and released from the RayoHX-Installer repository.

## The PyPI package: `rayohx-cli`

The distribution is named `rayohx-cli` and installs the `rayohx` command (`rayohx = rayohx_cli.cli:run` in `[project.scripts]`). It holds only the command line code (`rayohx_cli`), compiled into one binary (`rayohx_cli.<tag>.pyd` on Windows, `.so` elsewhere) with `.pyi` stubs beside it and no `.py` sources. `python -m rayohx_cli` works from a source checkout but not from the compiled wheel; use the `rayohx` command. It depends on the `rayohx` library on PyPI, and on Typer, Rich and Click.

```bash
PYD_BUILD=1 uv build --wheel           # dist/rayohx_cli-<version>-<tag>.whl
uvx twine check --strict dist/*        # the metadata PyPI will show
uvx --find-links dist --from dist/rayohx_cli-*.whl rayohx --version
```

The version is `__version__` in `src/rayohx_cli/__init__.py`; setuptools reads it from there. `setup.py` compiles the package with Nuitka (it needs a C compiler) when `PYD_BUILD=1`, and builds plain Python otherwise, so local development is unaffected. The `build` job in `ci.yml` does these steps on every change, and also checks that the wheel holds the compiled command line and no `.py` sources, so a release never meets a metadata problem for the first time.

Users install it with `uv tool install rayohx-cli` or `pipx install rayohx-cli`, and remove it with `uv tool uninstall rayohx-cli` or `pipx uninstall rayohx-cli`.

## macOS

There is no installer. Install the PyPI package: `uv tool install rayohx-cli` or `pipx install rayohx-cli`.

## Checking a build by hand

The [smoke test](../scripts/smoke/README.md) builds the compiled wheel, installs it into a fresh virtual environment and runs `rayohx info` from it. It is a manual check for the compiled build on your own machine.

## Checks in CI

- The `build` job in `ci.yml` builds the compiled wheel, checks its metadata and contents, and runs the installed wheel.
- `tests/integration/test_frozen_cli.py` starts a built PyInstaller program and checks it answers. It is skipped when there is no build; see [testing](testing.md#the-frozen-tests).

## Build time

Starting targets, to be revisited after the first real runs and recorded here:

| Job | Target | `timeout-minutes` |
| --- | --- | --- |
| Package build in CI | under 5 minutes | 10 |
| Compiled wheels per platform in a release | under 30 minutes | 45 |

A job that passes its timeout fails instead of hanging. uv caches keep builds inside the targets.
