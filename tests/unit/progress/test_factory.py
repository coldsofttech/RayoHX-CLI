"""Choosing how to show a download's progress."""

import pytest
from rayohx import EventType

from rayohx_cli.progress import MODES, BarReporter, NullReporter, PlainReporter, make_reporter
from tests.helpers.progress import capture, make_event


def test_the_modes_are_auto_bar_plain_and_none() -> None:
    assert MODES == ("auto", "bar", "plain", "none")


def _make(
    mode: str,
    *,
    terminal: bool = False,
    quiet: bool = False,
    json_output: bool = False,
    verbose: bool = False,
) -> object:
    return make_reporter(
        mode,
        capture(terminal=terminal).console,
        quiet=quiet,
        json_output=json_output,
        verbose=verbose,
    )


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("terminal", [True, False])
def test_quiet_and_json_output_show_nothing_in_any_mode(mode: str, terminal: bool) -> None:
    assert isinstance(_make(mode, terminal=terminal, quiet=True), NullReporter)
    assert isinstance(_make(mode, terminal=terminal, json_output=True), NullReporter)


def test_none_shows_nothing() -> None:
    assert isinstance(_make("none"), NullReporter)
    assert isinstance(_make("none", terminal=True), NullReporter)


def test_plain_always_prints_lines() -> None:
    assert isinstance(_make("plain"), PlainReporter)
    assert isinstance(_make("plain", terminal=True), PlainReporter)


def test_bar_always_draws_a_bar() -> None:
    assert isinstance(_make("bar"), BarReporter)
    assert isinstance(_make("bar", terminal=True), BarReporter)


def test_auto_draws_a_bar_on_a_terminal_and_prints_lines_otherwise() -> None:
    assert isinstance(_make("auto", terminal=True), BarReporter)
    assert isinstance(_make("auto", terminal=False), PlainReporter)


def test_an_unknown_mode_falls_back_to_lines() -> None:
    # The command rejects unknown modes before this point; lines are the safe choice.
    assert isinstance(_make("sparkles"), PlainReporter)


def test_verbose_reaches_the_reporter() -> None:
    quiet = capture()
    loud = capture()
    start = make_event(EventType.DOWNLOAD_STARTED, message="https://example.com/a.m3u8")
    make_reporter("plain", quiet.console, quiet=False, json_output=False, verbose=False)(start)
    make_reporter("plain", loud.console, quiet=False, json_output=False, verbose=True)(start)
    assert quiet.text == ""
    assert "Downloading https://example.com/a.m3u8" in loud.text
