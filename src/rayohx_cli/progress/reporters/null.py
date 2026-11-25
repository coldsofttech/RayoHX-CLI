"""The reporter that shows nothing."""

from rayohx.events import DownloadEvent


class NullReporter:
    """Shows nothing."""

    def __call__(self, event: DownloadEvent) -> None:
        return None

    def start(self) -> None:
        return None

    def close(self) -> None:
        return None
