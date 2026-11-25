"""A Rich console that writes into memory, for tests that look at what is printed."""

import io
from dataclasses import dataclass

from rich.console import Console


@dataclass
class Captured:
    """A console that writes into memory, and what it has written."""

    console: Console
    buffer: io.StringIO

    @property
    def text(self) -> str:
        return self.buffer.getvalue()

    @property
    def lines(self) -> list[str]:
        return [line.rstrip() for line in self.text.splitlines() if line.strip()]


def capture(*, terminal: bool = False, width: int = 100) -> Captured:
    """A console like a pipe (the default) or like a terminal, writing into memory."""
    buffer = io.StringIO()
    console = Console(
        file=buffer,
        width=width,
        force_terminal=terminal,
        color_system=None,
        legacy_windows=False,
    )
    return Captured(console, buffer)
