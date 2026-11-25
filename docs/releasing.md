# Releasing

How a release of the `rayohx` command is made. This repository releases one thing, the `rayohx-cli` package on PyPI, so the only tag is `v<version>`. For what the package contains, see [packaging](packaging.md).

## How it works

Publishing a GitHub release runs `release.yml`. The tag must equal the package version, and the job that publishes waits for a reviewer of the `pypi` environment (Settings > Environments), after everything has been built.

| Tag | Releases | Environment |
| --- | --- | --- |
| `v<version>` | the command line, `rayohx-cli`, on PyPI as compiled wheels (no sources) | `pypi` |

The installers (the Windows setup and the Linux packages) are not released from here. They are built and released from the [RayoHX-Installer](https://github.com/coldsofttech/RayoHX-Installer) repository, from the published command line.

## Making a release

1. Release the core library first if the command needs a newer one: `rayohx-cli` depends on the `rayohx` package on PyPI, so that version must already be there.
2. Bump `__version__` in `src/rayohx_cli/__init__.py`, and move the `[Unreleased]` entries in `CHANGELOG.md` under a `## [x.y.z]` heading.
3. Merge that pull request, then publish a GitHub release tagged `v<version>`, for example `v0.2.0` for `__version__ = "0.2.0"`.
4. `release.yml` does the rest:

| Job | Result |
| --- | --- |
| `check` | the tag must be `v` plus `__version__` in `src/rayohx_cli/__init__.py`, or the release stops here |
| `build` | compiled wheels of `rayohx-cli` only (one Nuitka `.pyd` on Windows, `.so` elsewhere), built with cibuildwheel for Linux (x86_64 and arm64), Windows and macOS (Intel and Apple silicon), one per Python version from 3.11 to 3.15, with no sdist |
| `publish` | waits for a reviewer of the `pypi` environment, then uploads the wheels to PyPI through trusted publishing |

Every wheel is built, and tested by cibuildwheel, before the approval, so the reviewer approves a release that already works. Release notes are written on the GitHub release by hand (or with its "Generate release notes" button); `.github/release.yml` groups the generated ones into features, bug fixes and other changes.

To check a published release: `uvx --from rayohx-cli==<version> rayohx --version`.

## PyPI trusted publishing

No tokens are stored. On PyPI, add a trusted publisher for the `rayohx-cli` project with the repository `coldsofttech/RayoHX-CLI`, the workflow `release.yml` and the environment `pypi`. The environment `pypi` (Settings > Environments) is also where the required reviewers are set. Check the first publish: PyPI matches the workflow and environment names exactly, and a mismatch shows as a clear error in the `publish` job.

## Before the first release

- Release the `rayohx` core library to PyPI. `rayohx-cli` cannot be installed without it.
- Create the `pypi` environment with its reviewers, and the trusted publisher for `rayohx-cli` on PyPI.
- Check that the version in `src/rayohx_cli/__init__.py` and the heading in `CHANGELOG.md` match the tag you are about to publish.
