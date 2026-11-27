"""The reporter that shows nothing."""

import pytest
from rayohx import EventType

from rayohx_cli.progress.reporters import NullReporter
from tests.helpers.progress import make_event, progress_event


@pytest.mark.parametrize("kind", list(EventType))
def test_no_event_produces_any_output(kind: EventType, capsys: pytest.CaptureFixture[str]) -> None:
    reporter = NullReporter()
    reporter(make_event(kind, message="text", bandwidth=1, kind="master"))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_progress_and_the_start_and_end_produce_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reporter = NullReporter()
    reporter.start()
    reporter(progress_event(5, 10, downloaded=1024, speed=100.0, eta=3))
    reporter.close()
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")
