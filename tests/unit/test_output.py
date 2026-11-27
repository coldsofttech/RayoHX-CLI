"""The consoles and every way the command prints."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pytest
from rayohx.errors import ConfigurationError

from rayohx_cli import output
from tests.helpers.console import Captured, capture


@dataclass
class Consoles:
    """What went to stdout and what went to stderr."""

    out: Captured
    err: Captured


@pytest.fixture
def consoles(monkeypatch: pytest.MonkeyPatch) -> Consoles:
    """Replace the two consoles with ones that write into memory, and start from fresh options."""
    out = capture()
    err = capture()
    monkeypatch.setattr(output, "console", out.console)
    monkeypatch.setattr(output, "err_console", err.console)
    monkeypatch.setattr(output, "settings", output.Settings())
    monkeypatch.setattr(output, "_handler", None)
    return Consoles(out, err)


# --- the global options ---------------------------------------------------------------------------


def test_the_options_start_off() -> None:
    fresh = output.Settings()
    assert (fresh.verbose, fresh.quiet) == (False, False)


def test_configure_records_verbose_and_quiet(consoles: Consoles) -> None:
    output.configure(no_color=False, verbose=True)
    assert (output.settings.verbose, output.settings.quiet) == (True, False)
    output.configure(no_color=False, verbose=False, quiet=True)
    assert (output.settings.verbose, output.settings.quiet) == (False, True)


def test_no_color_turns_colour_off_on_both_consoles_and_never_back_on(consoles: Consoles) -> None:
    consoles.out.console.no_color = False
    consoles.err.console.no_color = False
    output.configure(no_color=False, verbose=False)
    assert not consoles.out.console.no_color
    assert not consoles.err.console.no_color
    output.configure(no_color=True, verbose=False)
    assert consoles.out.console.no_color
    assert consoles.err.console.no_color
    output.configure(no_color=False, verbose=False)
    assert consoles.out.console.no_color  # the NO_COLOR variable or an earlier option stays


# --- data and messages ----------------------------------------------------------------------------


def test_data_goes_to_stdout_exactly_as_given(consoles: Consoles) -> None:
    line = "[bold]/very/long/path/" + "x" * 200 + ".mp4"
    output.data(line)
    assert consoles.out.text == line + "\n"  # no markup, no wrapping
    assert consoles.err.text == ""


def test_a_message_goes_to_stderr(consoles: Consoles) -> None:
    output.message("Saved movie.mp4", style="green")
    assert consoles.err.text == "Saved movie.mp4\n"
    assert consoles.out.text == ""


def test_a_message_is_left_out_when_quiet(consoles: Consoles) -> None:
    output.configure(no_color=False, verbose=False, quiet=True)
    output.message("Saved movie.mp4")
    assert consoles.err.text == ""


def test_data_is_still_printed_when_quiet(consoles: Consoles) -> None:
    output.configure(no_color=False, verbose=False, quiet=True)
    output.data("result")
    assert consoles.out.text == "result\n"


# --- errors ---------------------------------------------------------------------------------------


def test_an_error_goes_to_stderr_with_the_hint_below_it(consoles: Consoles) -> None:
    output.error("It broke.", "Try again.")
    assert consoles.err.lines == ["Error: It broke.", "Try again."]
    assert consoles.out.text == ""


def test_an_error_without_a_hint_is_one_line(consoles: Consoles) -> None:
    output.error("It broke.")
    assert consoles.err.lines == ["Error: It broke."]


def test_an_error_is_shown_even_when_quiet(consoles: Consoles) -> None:
    output.configure(no_color=False, verbose=False, quiet=True)
    output.error("It broke.")
    assert consoles.err.lines == ["Error: It broke."]


def test_a_library_error_is_shown_with_its_hint(consoles: Consoles) -> None:
    output.error_from(ConfigurationError("Bad value.", hint="Use another."))
    assert consoles.err.lines == ["Error: Bad value.", "Use another."]


def test_an_unexpected_error_is_short_unless_verbose(consoles: Consoles) -> None:
    try:
        raise RuntimeError("something odd")
    except RuntimeError as exc:
        output.print_exception(exc)
    assert consoles.err.lines == [
        "Error: RuntimeError: something odd",
        "Run with --verbose for details.",
    ]


def test_an_unexpected_error_without_a_message_shows_its_type(consoles: Consoles) -> None:
    try:
        raise KeyError
    except KeyError as exc:
        output.print_exception(exc)
    assert consoles.err.lines[0] == "Error: KeyError"


def test_verbose_adds_a_traceback_but_never_local_variables(consoles: Consoles) -> None:
    def fails() -> None:
        # Built at run time, so the value is not in the source line a traceback prints.
        password = "-".join(["s3cret", "value"])  # noqa: F841
        raise RuntimeError("something odd")

    output.configure(no_color=False, verbose=True)
    try:
        fails()
    except RuntimeError as exc:
        output.print_exception(exc)
    text = consoles.err.text
    assert "Traceback" in text
    assert "something odd" in text
    assert "s3cret-value" not in text
    assert "Run with --verbose" not in text


# --- JSON -----------------------------------------------------------------------------------------


def test_json_is_printed_to_stdout_and_reads_back(consoles: Consoles) -> None:
    value = {"url": "https://example.com/a.m3u8", "segments": 3, "ok": True, "tags": ["a", "b"]}
    output.print_json(value)
    assert json.loads(consoles.out.text) == value
    assert consoles.err.text == ""


def test_json_keeps_non_ascii_text_and_is_indented(consoles: Consoles) -> None:
    output.print_json({"name": "Français"})
    assert "Français" in consoles.out.text
    assert '\n  "name"' in consoles.out.text


def test_json_text_that_looks_like_markup_is_left_alone(consoles: Consoles) -> None:
    output.print_json({"note": "[red]not styled[/red]"})
    assert "[red]not styled[/red]" in consoles.out.text


# --- logging --------------------------------------------------------------------------------------


def _console_handlers() -> list[logging.Handler]:
    logger = logging.getLogger("rayohx")
    return [h for h in logger.handlers if isinstance(h, output._ConsoleHandler)]


def test_log_records_appear_on_stderr_at_the_chosen_level(consoles: Consoles) -> None:
    output.configure_logging(logging.WARNING, verbose=False)
    logger = logging.getLogger("rayohx.test")
    logger.info("hidden detail")
    logger.warning("something to know")
    assert consoles.err.lines == ["something to know"]
    assert consoles.out.text == ""


def test_errors_in_the_log_are_shown_even_at_the_strictest_level(consoles: Consoles) -> None:
    output.configure_logging(logging.ERROR, verbose=False)
    logging.getLogger("rayohx.test").warning("only a warning")
    logging.getLogger("rayohx.test").error("a real problem")
    assert consoles.err.lines == ["a real problem"]


def test_verbose_logging_adds_the_time_and_the_logger(consoles: Consoles) -> None:
    output.configure_logging(logging.DEBUG, verbose=True)
    logging.getLogger("rayohx.test").debug("a detail")
    assert "rayohx.test: a detail" in consoles.err.text


def test_configuring_again_replaces_the_handler(consoles: Consoles) -> None:
    output.configure_logging(logging.WARNING, verbose=False)
    output.configure_logging(logging.WARNING, verbose=False)
    assert len(_console_handlers()) == 1
    logging.getLogger("rayohx.test").warning("once")
    assert consoles.err.lines == ["once"]


def test_secrets_are_removed_from_log_records(consoles: Consoles) -> None:
    output.configure_logging(logging.WARNING, verbose=False)
    logging.getLogger("rayohx.test").warning("Fetching https://h.example/a.m3u8?token=abc123")
    assert "abc123" not in consoles.err.text
    assert "Fetching" in consoles.err.text


def test_a_log_file_gets_everything_with_secrets_removed(
    consoles: Consoles, tmp_path: Path
) -> None:
    log = tmp_path / "run.log"
    output.configure_logging(logging.ERROR, verbose=False, log_file=log)
    logger = logging.getLogger("rayohx.test")
    logger.debug("a debug detail")
    logger.warning("Fetching https://h.example/a.m3u8?token=abc123")
    text = log.read_text(encoding="utf-8")
    assert "a debug detail" in text
    assert "Fetching" in text
    assert "abc123" not in text
    assert consoles.err.text == ""  # the screen still shows only errors
