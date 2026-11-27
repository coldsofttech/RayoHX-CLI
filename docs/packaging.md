# CLI packaging and releasing

How the `rayohx` command is packaged and released to PyPI: the `rayohx-cli` package. The Windows setup and the Linux packages are built and released from their own repository.

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

Users install it with `uv tool install rayohx-cli` or `pipx install rayohx-cli` (also the way to get it on macOS), and remove it with `uv tool uninstall rayohx-cli` or `pipx uninstall rayohx-cli`.

## Checking a build

- The [smoke test](../scripts/smoke/README.md) builds the compiled wheel, installs it into a fresh virtual environment and runs `rayohx info` from it. It is a manual check for the compiled build on your own machine.
- The `build` job in `ci.yml` builds the compiled wheel, checks its metadata and contents, and runs the installed wheel.
- `tests/integration/test_frozen_cli.py` starts a built PyInstaller program and checks it answers. It is skipped when there is no build; see [testing](testing.md#the-frozen-tests).

## Releasing to PyPI

Publishing a GitHub release runs `release.yml`. This repository releases one thing, so the only tag is `v<version>`.

| Tag | Releases | Environment |
| --- | --- | --- |
| `v<version>` | the command line, `rayohx-cli`, on PyPI as compiled wheels (no sources) | `cli` |

The tag must equal the package version, for example `v0.2.0` for `__version__ = "0.2.0"`. Release the core library first if the command needs a newer one: `rayohx-cli` depends on the `rayohx` package on PyPI, so that version must already be there.

1. Bump `__version__` in `src/rayohx_cli/__init__.py`, and move the `[Unreleased]` entries in `CHANGELOG.md` under a `## [x.y.z]` heading.
2. Merge that pull request, then publish a GitHub release tagged `v<version>`.
3. `release.yml` does the rest:

| Job | Result |
| --- | --- |
| `check` | the tag must be `v` plus `__version__` in `src/rayohx_cli/__init__.py`, or the release stops here |
| `build` | compiled wheels of `rayohx-cli` only (one Nuitka `.pyd` on Windows, `.so` elsewhere), built with cibuildwheel for Linux (x86_64 and arm64), Windows and macOS (Intel and Apple silicon), one per Python version from 3.11 to 3.15, with no sdist |
| `publish` | waits for a reviewer of the `cli` environment, then uploads the wheels to PyPI through trusted publishing and attaches them, with SHA-256 checksums, to the GitHub release |

Every wheel is built, and tested by cibuildwheel, before the approval, so the reviewer approves a release that already works. Release notes are written on the GitHub release by hand (or with its "Generate release notes" button); `.github/release.yml` groups the generated ones into features, bug fixes and other changes.

After the release, check the new version on PyPI: `uvx --from rayohx-cli==<version> rayohx --version`.

### PyPI trusted publishing

No tokens are stored, and only the publish job gets the `id-token` permission. On PyPI, add a trusted publisher for the `rayohx-cli` project with the repository `coldsofttech/RayoHX-CLI`, the workflow `release.yml` and the environment `cli`. The environment `cli` (Settings > Environments) is also where the required reviewers are set. PyPI matches the workflow and environment names exactly, and a mismatch shows as a clear error in the `publish` job.

### Before the first release

- Release the `rayohx` core library to PyPI. `rayohx-cli` cannot be installed without it.
- Create the `cli` environment with its reviewers, and the trusted publisher for `rayohx-cli` on PyPI.
- Check that the version in `src/rayohx_cli/__init__.py` and the heading in `CHANGELOG.md` match the tag you are about to publish.

### If a release fails

- **The tag does not match** the version: delete the release and the tag, fix the version in a pull request, and publish again.
- **Publishing was refused:** the trusted publisher on PyPI does not match the workflow or environment above.
- **PyPI never accepts a version twice**, even after deleting it. If a version went out wrong, fix it and release the next one.

## Build time

Starting targets, to be revisited after the first real runs and recorded here:

| Job | Target | `timeout-minutes` |
| --- | --- | --- |
| Package build in CI | under 5 minutes | 10 |
| One compiled wheel (OS and Python version) in a release | under 20 minutes | 30 |

A job that passes its timeout fails instead of hanging. uv caches keep builds inside the targets.
