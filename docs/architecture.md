# Architecture

How `rayohx_cli` (the `rayohx` command) is put together. For using it, see the [command line guide](guides/cli.md); for working on it, see [development](development.md).

## Layering

The command line only reads options and shows results. All the work is done by the `rayohx` library: `inspect` and `select_stream` for `info`, `Downloader` for `download`. The library never imports the command line and never prints or exits. The command line adds three runtime dependencies of its own: Typer, Click (which Typer builds on) and Rich. A unit test checks that the package imports only what it declares.

## Modules

```text
src/rayohx_cli/
  __main__.py      python -m rayohx_cli: calls run()
  cli/
    __init__.py    run(), the console script: runs the app and reports unexpected errors briefly
    root.py        the Typer app, its help text and the options every command takes
    info.py        the info command
    download.py    the download command
    lifecycle.py   Ctrl-C handling, and reporting how a download ended
    common.py      exit codes, usage_error() and make_config()
  params/          every option, defined once and shared by the commands that take it
  values.py        turns what was typed into engine settings (pure functions, no output)
  settings.py      the settings file: where it is, how it is read and checked
  output.py        the two Rich consoles and every way of printing
  render.py        the tables that info shows
  format.py        numbers as short text (sizes, speeds, durations)
  progress/        shows a download's events: a bar, plain lines, or nothing
```

Importing `rayohx_cli.cli` imports `info` and `download`, which register their commands on the app in `root.py`.

## A command, step by step

1. `run()` starts the Typer app. The root callback in `root.py` runs first: it rejects clashing global options (`--verbose` with `--quiet`, `--config` with `--no-config`), configures the output and logging, finds and loads the settings file, and hands each command its defaults.
2. The command's options come from `params`. A value is taken from the command line first, then from a `RAYOHX_<NAME>` environment variable, then from the settings file, then from the built-in default.
3. `make_config` builds the engine settings through `values.build_config`. A bad value raises `ConfigurationError`, which is shown as a usage error (exit code 2).
4. `download` creates a `Downloader`, subscribes a progress reporter to its events, and runs it inside `graceful_interrupt`: the first Ctrl-C asks the download to stop cleanly, and a second one quits at once.
5. `finish` reports how it ended. The saved path goes to stdout, a "Saved ..." line goes to stderr, and the exit code is set.

`info` skips steps 4 and 5. It inspects the playlist, marks the stream a download with the same options would pick, and prints the result as JSON (`--json`) or as tables (`render.show`).

## Output

- **Data to stdout, everything else to stderr.** `output.data` and `output.print_json` write a command's result to the `console`. Messages, errors, progress and logs go to `err_console`, so the result can be piped or captured. Nothing uses `print`.
- **`--quiet`** hides status messages and progress; errors and the result still show. **`--no-color`** and the `NO_COLOR` variable turn colour off, and Rich also drops it when output is piped.
- **Logging.** The library's log records are shown through a console handler on stderr, so they do not tear a progress bar. `--log-file` also writes a detailed log, and a redaction filter removes secrets from what is shown.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | The operation failed |
| 2 | The command or a setting was invalid |
| 130 | Stopped with Ctrl-C |

The codes are defined in `cli/common.py`. See the [exit codes guide](guides/cli/exit-codes.md) for what users see.

## Errors

Library errors carry a message and a hint, and `output.error_from` prints both. Anything unexpected travels up to `run()`, which prints the exception type and message and exits with 1. A traceback is shown only with `--verbose`, and never with local variables, since they can hold secrets. Typer's own pretty tracebacks are switched off for the same reason.

## Progress

A reporter is anything that can be called with a download event, plus `start()` and `close()`. There are three: a progress bar, plain lines, and one that shows nothing. `make_reporter` picks one from `--progress`. `--quiet` and `--json` always get the silent one, and `auto` chooses the bar on a terminal and plain lines otherwise.

## Settings file

The file is TOML whose keys are option names. It is `--config`, else `rayohx.toml` in the current folder, else the per-user file (`%APPDATA%\rayohx\config.toml` on Windows, `~/.config/rayohx/config.toml` elsewhere). A key that is not an option is an error, with a "did you mean" hint, so a typo never does nothing. `url`, `output`, `json` and `help` cannot be set there. `--no-config` ignores all settings files.

## Packaging

- The console script is `rayohx = rayohx_cli.cli:run`.
- The package is released to PyPI as compiled wheels (`setup.py` compiles it with Nuitka when `PYD_BUILD=1`); see [packaging and releasing](packaging.md).
- It depends on the `rayohx` library on PyPI for all of the work. The library lives in the [RayoHX](https://github.com/coldsofttech/RayoHX) repository. The installers, which bundle the published command line, live in [RayoHX-Installer](https://github.com/coldsofttech/RayoHX-Installer).
