"""Command line interface built on Typer and Rich. It only parses input and shows output.

All the work is done by the ``rayohx`` library: ``inspect`` for ``info`` and ``Downloader`` for
``download``. Data (the result) goes to stdout and messages go to stderr, so the result can be
piped. Exit codes: 0 success, 1 the operation failed, 2 the command or a setting was invalid,
130 stopped with Ctrl-C.
"""

from rayohx_cli import output
from rayohx_cli.cli import clean, config, download, info  # noqa: F401  (registers the commands)
from rayohx_cli.cli.common import EXIT_CANCELLED, EXIT_FAILED, EXIT_USAGE
from rayohx_cli.cli.root import app

__all__ = ["EXIT_CANCELLED", "EXIT_FAILED", "EXIT_USAGE", "app", "run"]


def run() -> None:
    """Console script entry point: run the app and report unexpected errors briefly."""
    try:
        app()
    except KeyboardInterrupt:
        output.err_console.print("Interrupted.")
        raise SystemExit(EXIT_CANCELLED) from None
    except Exception as exc:
        output.print_exception(exc)
        raise SystemExit(EXIT_FAILED) from exc
