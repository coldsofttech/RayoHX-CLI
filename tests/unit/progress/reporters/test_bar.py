"""The reporter that draws a live progress bar."""

from collections.abc import Iterator

import pytest
from rayohx import EventType

from rayohx_cli import format as fmt
from rayohx_cli.progress.reporters import BarReporter
from tests.helpers.progress import Captured, capture, make_event, progress_event


@pytest.fixture
def terminal() -> Captured:
    return capture(terminal=True)


@pytest.fixture
def reporter(terminal: Captured) -> Iterator[BarReporter]:
    bar = BarReporter(terminal.console)
    yield bar
    bar.close()  # never leave the refresh thread running


# --- starting and closing -------------------------------------------------------------------------


def test_the_bar_is_drawn_between_start_and_close(reporter: BarReporter) -> None:
    assert not reporter._progress.live.is_started
    reporter.start()
    assert reporter._progress.live.is_started
    reporter.close()
    assert not reporter._progress.live.is_started


def test_closing_twice_or_without_starting_does_nothing(reporter: BarReporter) -> None:
    reporter.close()
    reporter.start()
    reporter.close()
    reporter.close()


# --- what it shows --------------------------------------------------------------------------------


def test_progress_moves_the_bar_and_shows_the_size_speed_and_time_left(
    reporter: BarReporter,
) -> None:
    reporter.start()
    reporter(progress_event(5, 10, downloaded=5 * 1024**2, speed=1024**2, eta=65))
    task = reporter._progress.tasks[0]
    assert task.completed == 0.5
    assert task.total == 1.0
    assert task.fields["detail"] == (
        f"{fmt.size(5 * 1024**2)}  {fmt.rate(1024**2)}  ETA {fmt.duration(65)}"
    )
    assert task.description == "Downloading"


def test_the_percent_appears_in_the_drawing(terminal: Captured, reporter: BarReporter) -> None:
    reporter.start()
    reporter(progress_event(5, 10, downloaded=1024))
    reporter.close()
    assert "50%" in terminal.text


def test_finalizing_changes_the_label_and_clears_the_detail(reporter: BarReporter) -> None:
    reporter.start()
    reporter(progress_event(10, 10, downloaded=1024))
    reporter(make_event(EventType.FINALIZATION_STARTED))
    task = reporter._progress.tasks[0]
    assert task.description == "Finalizing"
    assert task.fields["detail"] == ""


def test_a_progress_event_without_a_snapshot_changes_nothing(reporter: BarReporter) -> None:
    reporter.start()
    reporter(make_event(EventType.DOWNLOAD_PROGRESS))
    task = reporter._progress.tasks[0]
    assert task.completed == 0
    assert task.fields["detail"] == ""


# --- messages above the bar -----------------------------------------------------------------------


def test_steps_are_printed_above_the_bar(terminal: Captured, reporter: BarReporter) -> None:
    reporter.start()
    reporter(make_event(EventType.STREAM_SELECTED, resolution="1280x720", bandwidth=2_800_000))
    reporter(make_event(EventType.SEGMENT_FAILED, segment=2, message="timed out"))
    reporter(make_event(EventType.FINALIZATION_STARTED))
    reporter.close()
    assert "Stream: 1280x720, 2.8 Mbit/s" in terminal.text
    assert "Segment 2 failed: timed out" in terminal.text
    assert "Finalizing..." in terminal.text


def test_detail_lines_appear_only_when_verbose() -> None:
    start = make_event(EventType.DOWNLOAD_STARTED, message="https://example.com/a.m3u8")
    for verbose, expected in ((False, False), (True, True)):
        out = capture(terminal=True)
        bar = BarReporter(out.console, verbose=verbose)
        bar.start()
        bar(start)
        bar.close()
        assert ("Downloading https://example.com/a.m3u8" in out.text) is expected


def test_events_before_the_start_are_still_recorded(reporter: BarReporter) -> None:
    reporter(progress_event(2, 10, downloaded=1024))
    task = reporter._progress.tasks[0]
    assert task.completed == 0.2
