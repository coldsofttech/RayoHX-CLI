# Development

How to work on this repository, the `rayohx` command line. For how it is built, see [architecture](architecture.md); for using the command, see the [command line guide](guides/cli.md). The pull request process is in the [contributing guide](../CONTRIBUTING.md), tests are described in [testing](testing.md), and packaging and releases in [packaging and releasing](packaging.md).

## Set up and run

```bash
uv sync --locked                                  # the dependencies and the dev tools
uv run rayohx --help                              # the command, from your checkout
uv run rayohx info https://example.com/master.m3u8
uv run python -m rayohx_cli download --help       # the same thing, as a module
```

The module form works here because development runs the plain Python sources. The compiled wheel a release ships has no `python -m rayohx_cli`; use the `rayohx` command there.

## Checks

Run only what your change touches:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest tests/unit --no-cov
```

How the tests are organized, the integration and frozen tests, coverage, the shared `rayohx-pytest` plugin and the smoke test of the compiled build are in [testing](testing.md). CI (`ci.yml`) runs the same checks as separate `lint`, `test`, `int-tests` and `build` jobs, with `ci (required check)` as the single check the branch ruleset needs. The `lint` job also runs pre-commit and fails on GPL-licensed dependencies (`uv run pip-licenses --from=mixed --partial-match --fail-on="GPL" --format=plain` runs the same check locally). Two more workflows run outside that check: `security.yml` (Semgrep, results in the Security tab) and `audit.yml` (`pip-audit` on the locked dependencies, weekly and when `uv.lock` changes).

## Working with the library

`rayohx-cli` depends on the `rayohx` library on PyPI, and `uv sync` installs the published version. To try the command against a local checkout of the library, install it into the environment on top of that:

```bash
uv pip install -e ../RayoHX/packages/core
```

Run `uv sync --locked` again to go back to the published library.

## Adding an option

1. Define it once in the right file in `params/` (selection, network, engine, output or display) and put it in that file's help panel.
2. Add it to the signature of each command that takes it, and pass it to `make_config(...)` in that command.
3. Handle it in `values.build_config`, and raise `ConfigurationError` for a bad value so it becomes a usage error.
4. The environment variable `RAYOHX_<NAME>` and the settings-file key work automatically, because both use the option's name.
5. Add unit tests for the value handling and for the command.
6. Update the guide in `docs/guides/cli/` and the `[Unreleased]` section of `CHANGELOG.md`.

## Adding a command

1. Add a module in `cli/` with a function decorated by `@app.command()`, and import it in `cli/__init__.py` so it registers.
2. Reuse the options in `params/`, build settings with `make_config`, and call the library for the work. Keep the command to parsing and showing.
3. Print through `output` only: the result with `output.data` or `output.print_json`, everything else with `output.message` and `output.error_from`.
4. End with one of the exit codes in `cli/common.py`.
5. Document it in `docs/guides/cli/` and the changelog.

## Rules to keep

- No `print`: the linter rejects it, and `output` keeps data on stdout and messages on stderr.
- Keep Typer's Rich help: `rich_markup_mode="rich"` on every Typer app, and escape literal square brackets in help text with a backslash.
- Never show local variables in an error, and never put headers, cookies, keys or tokens in output or logs.
- The library does the work and never imports the command line. If you need logic in the command, it probably belongs in `rayohx`.
- Explain any `# noqa` or `# nosemgrep` with a reason in the comment.

## Installers

The installers (the Windows setup and the Linux packages) are built from the [RayoHX-Installer](https://github.com/coldsofttech/RayoHX-Installer) repository, from the published command line. See [packaging](packaging.md).
