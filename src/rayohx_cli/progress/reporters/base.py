"""The shape every reporter has."""

from typing import Protocol

from rayohx.events import DownloadEvent


class Reporter(Protocol):
    """Receives events from a running download."""

    def __call__(self, event: DownloadEvent) -> None: ...

    def start(self) -> None:
        """Called before the download starts."""
        ...

    def close(self) -> None:
        """Called after it ends, however it ended."""
        ...
