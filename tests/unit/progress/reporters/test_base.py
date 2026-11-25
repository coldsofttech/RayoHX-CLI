"""The shape every reporter has."""

import pytest
from rayohx import EventType

from rayohx_cli.progress.reporters import BarReporter, NullReporter, PlainReporter, Reporter
from tests.helpers.progress import capture, make_event, progress_event


def _reporters() -> list[Reporter]:
    # Each is typed as a Reporter, so mypy checks that it has the shape.
    return [
        NullReporter(),
        PlainReporter(capture().console),
        BarReporter(capture(terminal=True).console),
    ]


@pytest.fixture(params=range(3), ids=["null", "plain", "bar"])
def reporter(request: pytest.FixtureRequest) -> Reporter:
    return _reporters()[int(request.param)]


def test_a_reporter_can_be_started_fed_events_and_closed(reporter: Reporter) -> None:
    reporter.start()
    reporter(make_event(EventType.DOWNLOAD_STARTED, message="https://example.com/a.m3u8"))
    reporter(progress_event(5, 10, downloaded=1024))
    reporter(make_event(EventType.FINALIZATION_STARTED))
    reporter.close()


def test_a_reporter_can_be_closed_twice(reporter: Reporter) -> None:
    reporter.start()
    reporter.close()
    reporter.close()


def test_a_reporter_can_be_closed_without_being_started(reporter: Reporter) -> None:
    reporter.close()


def test_a_reporter_ignores_events_that_have_nothing_to_show(reporter: Reporter) -> None:
    reporter.start()
    reporter(make_event(EventType.SEGMENT_STARTED, segment=1))
    reporter(make_event(EventType.DOWNLOAD_PROGRESS))  # a progress event with no snapshot
    reporter.close()
