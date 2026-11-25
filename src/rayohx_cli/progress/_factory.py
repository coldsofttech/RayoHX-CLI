"""Choosing how to show a download's progress."""

from rich.console import Console

from rayohx_cli.progress.reporters import BarReporter, NullReporter, PlainReporter, Reporter

MODES = ("auto", "bar", "plain", "none")


def make_reporter(
    mode: str, console: Console, *, quiet: bool, json_output: bool, verbose: bool
) -> Reporter:
    """Choose how to show progress. Quiet and JSON output show none."""
    if quiet or json_output or mode == "none":
        return NullReporter()
    if mode == "plain":
        return PlainReporter(console, verbose=verbose)
    if mode == "bar" or (mode == "auto" and console.is_terminal):
        return BarReporter(console, verbose=verbose)
    return PlainReporter(console, verbose=verbose)
