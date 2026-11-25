"""The reporter that draws a live progress bar."""

import threading

from rayohx import EventType
from rayohx.events import DownloadEvent
from rich.console import Console
from rich.text import Text

from rayohx_cli.progress._text import detail, narrate, percent


class BarReporter:
    """A live progress bar with size, speed and time left."""

    def __init__(self, console: Console, *, verbose: bool = False) -> None:
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
        )

        self._verbose = verbose
        self._console = console
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("{task.fields[detail]}"),
            console=console,
            transient=True,
        )
        self._task = self._progress.add_task("Downloading", total=1.0, detail="")
        self._lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        with self._lock:
            self._progress.start()
            self._running = True

    def __call__(self, event: DownloadEvent) -> None:
        with self._lock:
            for line in narrate(event, verbose=self._verbose):
                self._progress.console.print(Text(line), soft_wrap=True)
            if event.type is EventType.DOWNLOAD_PROGRESS and event.progress is not None:
                self._progress.update(
                    self._task, completed=percent(event.progress), detail=detail(event.progress)
                )
            elif event.type is EventType.FINALIZATION_STARTED:
                self._progress.update(self._task, description="Finalizing", detail="")

    def close(self) -> None:
        with self._lock:
            if self._running:
                self._progress.stop()
                self._running = False
