"""How a download ends: the result, the exit code, and Ctrl-C."""

import signal
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from rayohx import DownloadState
from rayohx_pytest.site import hls_site
from typer.testing import CliRunner

from rayohx_cli.cli import app
from rayohx_cli.cli.lifecycle import graceful_interrupt, pause_toggle
from tests.conftest import FakeDownloader, parsed
from tests.helpers.cli import MASTER, Serve

# --- reporting the result -------------------------------------------------------------------------


def test_a_failure_exits_with_1_and_explains(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    site = hls_site("ts", "ts")
    site.fail.add("ts/v0_1.ts")
    serve(site)
    result = runner.invoke(app, ["download", MASTER, "-o", str(tmp_path / "f.mp4")])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Error: " in result.stderr
    assert "Segment 1" in result.stderr


def test_a_failure_in_json_mode_still_reports_on_stdout(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    site = hls_site("ts", "ts")
    site.fail.add("ts/v0_1.ts")
    serve(site)
    result = runner.invoke(app, ["download", MASTER, "-o", str(tmp_path / "f.mp4"), "--json"])
    assert result.exit_code == 1
    data = parsed(result.stdout)
    assert data["state"] == "failed"
    assert data["success"] is False
    assert data["output"] is None
    assert "Segment 1" in data["error"]
    assert "Error:" in result.stderr


def test_a_cancelled_download_exits_with_130(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    fake_downloader.state = DownloadState.CANCELLED
    result = runner.invoke(app, ["download", MASTER])
    assert result.exit_code == 130
    assert "Cancelled." in result.stderr
    assert result.stdout == ""


def test_an_unexpected_error_is_reported_once_with_a_short_message(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    fake_downloader.state = DownloadState.FAILED
    fake_downloader.error = RuntimeError("something odd")
    result = runner.invoke(app, ["download", MASTER])
    assert result.exit_code != 0
    assert isinstance(result.exception, RuntimeError)  # surfaced to run(), which reports it briefly


def test_a_failed_result_without_an_exception_still_explains(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    fake_downloader.state = DownloadState.FAILED
    result = runner.invoke(app, ["download", MASTER])
    assert result.exit_code == 1
    assert "Error: it broke" in result.stderr


# --- Ctrl-C ---------------------------------------------------------------------------------------


class _Downloader:
    """Counts the times it is asked to stop."""

    def __init__(self) -> None:
        self.cancelled = 0

    def cancel(self) -> None:
        self.cancelled += 1


def test_the_first_ctrl_c_stops_cleanly_and_the_second_quits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    downloader = _Downloader()
    with graceful_interrupt(downloader):  # type: ignore[arg-type]
        signal.raise_signal(signal.SIGINT)
        assert downloader.cancelled == 1
        with pytest.raises(KeyboardInterrupt):
            signal.raise_signal(signal.SIGINT)
    assert "press Ctrl-C again to quit at once" in capsys.readouterr().err


def test_the_previous_ctrl_c_handler_comes_back() -> None:
    before = signal.getsignal(signal.SIGINT)
    with graceful_interrupt(_Downloader()):  # type: ignore[arg-type]
        assert signal.getsignal(signal.SIGINT) is not before
    assert signal.getsignal(signal.SIGINT) is before


# --- pausing with a key ---------------------------------------------------------------------------


class _Pausable:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.changed = threading.Event()

    def pause(self) -> None:
        self.calls.append("pause")
        self.changed.set()

    def resume(self) -> None:
        self.calls.append("resume")
        self.changed.set()


def _keys(*keys: str | None) -> Callable[[float], str | None]:
    queue: Iterator[str | None] = iter(keys)

    def poll(timeout: float) -> str | None:
        return next(queue, None)

    return poll


def test_the_p_key_pauses_and_resumes_and_other_keys_are_ignored(
    capsys: pytest.CaptureFixture[str],
) -> None:
    downloader = _Pausable()
    with pause_toggle(downloader, source=_keys("x", "p", None, " ", "P")):  # type: ignore[arg-type]
        for _ in range(100):
            if len(downloader.calls) == 3:
                break
            downloader.changed.wait(0.05)
            downloader.changed.clear()
    assert downloader.calls == ["pause", "resume", "pause"]
    err = capsys.readouterr().err
    assert "Press P to pause or resume" in err
    assert "Paused. Press P to resume." in err
    assert "Resumed." in err


def test_there_is_no_key_watching_without_a_keyboard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", None)
    downloader = _Pausable()
    with pause_toggle(downloader):  # type: ignore[arg-type]
        pass
    assert downloader.calls == []


@pytest.mark.skipif(not hasattr(signal, "SIGUSR1"), reason="no SIGUSR1 on this system")
def test_sigusr1_pauses_and_resumes(capsys: pytest.CaptureFixture[str]) -> None:
    class Pausable(_Downloader):
        is_paused = False

        def pause(self) -> None:
            self.is_paused = True

        def resume(self) -> None:
            self.is_paused = False

    usr1: int = getattr(signal, "SIGUSR1", 0)  # missing on Windows, where the test is skipped
    downloader = Pausable()
    before = signal.getsignal(usr1)
    with graceful_interrupt(downloader):  # type: ignore[arg-type]
        signal.raise_signal(usr1)
        assert downloader.is_paused
        signal.raise_signal(usr1)
        assert not downloader.is_paused
    assert signal.getsignal(usr1) is before
    assert "Paused" in capsys.readouterr().err
