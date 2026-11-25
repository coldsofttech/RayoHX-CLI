"""How a download runs and ends: pausing with a key, stopping on Ctrl-C, and the result."""

import signal
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from types import FrameType

import typer
from rayohx import Downloader, DownloadResult, result_to_dict
from rayohx.errors import RayoHXError

from rayohx_cli import format as fmt
from rayohx_cli import output
from rayohx_cli.cli.common import EXIT_CANCELLED, EXIT_FAILED


@contextmanager
def graceful_interrupt(downloader: Downloader) -> Generator[None]:
    """The first Ctrl-C stops the download cleanly; a second one quits at once."""
    presses = 0

    def handler(signum: int, frame: FrameType | None) -> None:
        nonlocal presses
        presses += 1
        if presses == 1:
            downloader.cancel()
            output.message("Stopping... press Ctrl-C again to quit at once.")
        else:
            raise KeyboardInterrupt

    def toggle_pause(signum: int, frame: FrameType | None) -> None:
        if downloader.is_paused:
            downloader.resume()
            output.message("Resumed.")
        else:
            downloader.pause()
            output.message("Paused. Send the same signal again to continue.")

    try:
        previous = signal.signal(signal.SIGINT, handler)
    except ValueError:  # not the main thread: signals cannot be handled here
        yield
        return
    # SIGUSR1 pauses and continues where the system has it (not on Windows).
    pause_signal = getattr(signal, "SIGUSR1", None)
    previous_pause = signal.signal(pause_signal, toggle_pause) if pause_signal else None
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)
        if pause_signal is not None and previous_pause is not None:
            signal.signal(pause_signal, previous_pause)


PAUSE_KEYS = frozenset("pP ")
POLL_SECONDS = 0.1


@contextmanager
def _key_source() -> Generator[Callable[[float], str | None] | None]:
    """Yield a function that waits up to a timeout for one key press, or None with no keyboard."""
    try:
        interactive = sys.stdin is not None and sys.stdin.isatty()
    except (OSError, ValueError):
        interactive = False
    if not interactive:
        yield None
        return
    if sys.platform == "win32":
        import msvcrt
        import time

        def poll_windows(timeout: float) -> str | None:
            deadline = time.monotonic() + timeout
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getwch()
                    if key in ("\x00", "\xe0"):  # the first half of an arrow or function key
                        msvcrt.getwch()
                        return None
                    return key
                if time.monotonic() >= deadline:
                    return None
                time.sleep(0.02)

        yield poll_windows
        return
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    try:
        saved = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except termios.error:
        yield None
        return

    def poll_unix(timeout: float) -> str | None:
        ready, _, _ = select.select([fd], [], [], timeout)
        return sys.stdin.read(1) if ready else None

    try:
        yield poll_unix
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


@contextmanager
def pause_toggle(
    downloader: Downloader,
    *,
    source: Callable[[float], str | None] | None = None,
) -> Generator[None]:
    """While the download runs, the P key (or the space bar) pauses it and resumes it again.

    Does nothing when there is no keyboard to read, such as when input is piped. ``source`` is
    for tests: a function that waits up to a timeout for one key and returns it.
    """
    import threading

    with _key_source() as found:
        poll = source or found
        if poll is None:
            yield
            return
        stop = threading.Event()

        def watch() -> None:
            paused = False
            while not stop.is_set():
                key = poll(POLL_SECONDS)
                if key is None or key not in PAUSE_KEYS:
                    continue
                paused = not paused
                if paused:
                    downloader.pause()
                    output.message("Paused. Press P to resume.", style="yellow")
                else:
                    downloader.resume()
                    output.message("Resumed.")

        output.message("Press P to pause or resume, Ctrl-C to stop.")
        thread = threading.Thread(target=watch, name="rayohx-keys", daemon=True)
        thread.start()
        try:
            yield
        finally:
            stop.set()
            thread.join(1)


def finish(
    result: DownloadResult,
    downloader: Downloader,
    *,
    json_output: bool,
    documents: list[dict[str, object]] | None = None,
) -> None:
    """Report how the download ended and set the exit code.

    With ``documents`` (several downloads), the JSON result is added to it instead of printed,
    so the caller can print one array at the end.
    """
    if json_output and documents is not None:
        documents.append(result_to_dict(result))
    elif json_output:
        output.print_json(result_to_dict(result))
    if result.success and result.output is not None:
        if not json_output:
            output.data(str(result.output.path))
        output.message(
            f"Saved {result.output.path.name} ({fmt.size(result.output.size_bytes)}) "
            f"in {fmt.duration(result.elapsed_seconds)}",
            style="green",
        )
        return
    if result.cancelled:
        output.message("Cancelled.", style="yellow")
        raise typer.Exit(EXIT_CANCELLED)
    exc = downloader.exception
    if isinstance(exc, RayoHXError):
        output.error_from(exc)
    elif exc is not None:
        raise exc  # unexpected: reported once, by run()
    else:
        output.error(result.error or "The download failed.")
    raise typer.Exit(EXIT_FAILED)
