"""The reporter that prints plain lines."""

from concurrent.futures import ThreadPoolExecutor

from rayohx import EventType

from rayohx_cli import format as fmt
from rayohx_cli.progress.reporters import PlainReporter
from tests.helpers.progress import capture, make_event, progress_event


def test_the_steps_are_printed_as_lines() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    reporter(make_event(EventType.STREAM_SELECTED, resolution="1280x720", bandwidth=2_800_000))
    reporter(make_event(EventType.PLAYLIST_LOADED, audio="en"))
    reporter(make_event(EventType.FINALIZATION_STARTED))
    assert out.lines == ["Stream: 1280x720, 2.8 Mbit/s", "Audio track: en", "Finalizing..."]


def test_a_failed_segment_is_reported() -> None:
    out = capture()
    PlainReporter(out.console)(make_event(EventType.SEGMENT_FAILED, segment=3, message="timed out"))
    assert out.lines == ["Segment 3 failed: timed out"]


def test_detail_lines_appear_only_when_verbose() -> None:
    start = make_event(EventType.DOWNLOAD_STARTED, message="https://example.com/a.m3u8")
    quiet = capture()
    PlainReporter(quiet.console)(start)
    loud = capture()
    PlainReporter(loud.console, verbose=True)(start)
    assert quiet.lines == []
    assert loud.lines == ["Downloading https://example.com/a.m3u8"]


def test_progress_is_printed_at_every_tenth_percent() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    for done in range(0, 101):
        reporter(progress_event(done, 100))
    assert [line.split()[0] for line in out.lines] == [f"{step}%" for step in range(0, 101, 10)]


def test_a_percent_that_was_already_printed_is_not_printed_again() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    for done in (10, 10, 11, 15, 10, 19):
        reporter(progress_event(done, 100))
    assert len(out.lines) == 1
    assert out.lines[0].split()[0] == "10%"


def test_a_jump_prints_the_step_it_lands_on() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    reporter(progress_event(0, 100))
    reporter(progress_event(55, 100))
    assert [line.split()[0] for line in out.lines] == ["0%", "50%"]


def test_a_progress_line_shows_the_size_speed_and_time_left() -> None:
    out = capture()
    progress = progress_event(50, 100, downloaded=5 * 1024**2, speed=1024**2, eta=65)
    PlainReporter(out.console)(progress)
    expected = f"{fmt.size(5 * 1024**2)}  {fmt.rate(1024**2)}  ETA {fmt.duration(65)}"
    assert out.lines == [f" 50%  {expected}"]


def test_the_percent_is_right_aligned_so_the_columns_line_up() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    reporter(progress_event(5, 100))
    reporter(progress_event(100, 100))
    assert [line[:4] for line in out.lines] == ["  0%", "100%"]


def test_a_progress_event_without_a_snapshot_prints_nothing() -> None:
    out = capture()
    PlainReporter(out.console)(make_event(EventType.DOWNLOAD_PROGRESS))
    assert out.lines == []


def test_starting_and_closing_print_nothing() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    reporter.start()
    reporter.close()
    assert out.text == ""


def test_events_from_several_threads_never_print_a_percent_twice() -> None:
    out = capture()
    reporter = PlainReporter(out.console)
    events = [progress_event(done, 100) for done in range(101)] * 4
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(reporter, events))
    percents = [line.split()[0] for line in out.lines]
    assert len(percents) == len(set(percents))
    assert set(percents) <= {f"{step}%" for step in range(0, 101, 10)}
