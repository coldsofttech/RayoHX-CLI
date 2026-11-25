"""Showing a download's events: a progress bar, plain lines, or nothing.

The library reports what happens as events. These reporters turn them into text, using the
error console (stderr) so that a command's result on stdout stays clean.
"""

from rayohx_cli.progress._factory import MODES, make_reporter
from rayohx_cli.progress._text import narrate
from rayohx_cli.progress.reporters import (
    BarReporter,
    NullReporter,
    PlainReporter,
    Reporter,
)

__all__ = [
    "MODES",
    "BarReporter",
    "NullReporter",
    "PlainReporter",
    "Reporter",
    "make_reporter",
    "narrate",
]
