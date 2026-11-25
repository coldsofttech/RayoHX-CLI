"""The reporter that prints plain lines."""

import threading

from rayohx import EventType
from rayohx.events import DownloadEvent
from rich.console import Console
from rich.text import Text

from rayohx_cli.progress._text import detail, narrate, percent


class PlainReporter:
    """One line per milestone, for logs and pipes: every 10 percent, and each step."""

    def __init__(self, console: Console, *, verbose: bool = False) -> None:
        self._console = console
        self._verbose = verbose
        self._last = -1
        self._lock = threading.Lock()

    def __call__(self, event: DownloadEvent) -> None:
        with self._lock:
            for line in narrate(event, verbose=self._verbose):
                self._console.print(Text(line), soft_wrap=True)
            if event.type is EventType.DOWNLOAD_PROGRESS and event.progress is not None:
                step = int(percent(event.progress) * 10)
                if step > self._last:
                    self._last = step
                    self._console.print(
                        Text(f"{step * 10:3d}%  {detail(event.progress)}"), soft_wrap=True
                    )

    def start(self) -> None:
        return None

    def close(self) -> None:
        return None
