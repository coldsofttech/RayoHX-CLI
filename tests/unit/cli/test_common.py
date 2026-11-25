"""What every command shares: exit codes, and bad settings reported as usage errors."""

from pathlib import Path

import pytest
import typer
from rayohx.errors import ConfigurationError
from typer.testing import CliRunner

from rayohx_cli.cli import app
from rayohx_cli.cli.common import (
    EXIT_CANCELLED,
    EXIT_FAILED,
    EXIT_USAGE,
    gather_urls,
    make_config,
    usage_error,
)
from tests.helpers.cli import MASTER


def test_the_exit_codes() -> None:
    assert (EXIT_FAILED, EXIT_USAGE, EXIT_CANCELLED) == (1, 2, 130)


def test_a_usage_error_prints_the_message_and_hint_and_exits_with_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as raised:
        usage_error(ConfigurationError("Bad value.", hint="Try another."))
    assert raised.value.exit_code == EXIT_USAGE
    error = capsys.readouterr().err
    assert "Error: Bad value." in error
    assert "Try another." in error


def test_a_bad_value_becomes_a_usage_error() -> None:
    with pytest.raises(typer.Exit) as raised:
        make_config(quality="hd")
    assert raised.value.exit_code == EXIT_USAGE


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["download", "not a url"], "absolute http or https"),
        (["download", MASTER, "--quality", "hd"], "quality 'hd'"),
        (["download", MASTER, "-H", "nocolon"], "Name: value"),
        (["download", MASTER, "--cookie", "x"], "name=value"),
        (["download", MASTER, "--rate-limit", "fast"], "rate limit"),
        (["download", MASTER, "--proxy", "ftp://h:1"], "proxy address"),
        (["info", "ftp://host/x.m3u8"], "absolute http or https"),
        (["info", MASTER, "--max-bitrate", "lots"], "bitrate"),
    ],
)
def test_bad_settings_are_explained_on_stderr(
    runner: CliRunner, arguments: list[str], message: str
) -> None:
    result = runner.invoke(app, arguments)
    assert result.exit_code == 2
    assert message in result.stderr
    assert result.stderr.startswith("Error:")
    assert result.stdout == ""


def test_the_number_conflicts_with_other_choices_and_must_be_positive(runner: CliRunner) -> None:
    result = runner.invoke(app, ["info", MASTER, "--variant", "1", "--resolution", "1280x720"])
    assert result.exit_code == 2
    assert "by itself" in result.stderr
    assert runner.invoke(app, ["download", MASTER, "--variant", "0"]).exit_code == 2
    assert runner.invoke(app, ["download", MASTER, "--resolution", "720p"]).exit_code == 2


def test_arguments_come_before_the_listed_addresses(tmp_path: Path) -> None:
    listing = tmp_path / "urls.txt"
    listing.write_text("# comment\n\n https://b.test/b.m3u8 \n", encoding="utf-8")
    assert gather_urls(["https://a.test/a.m3u8"], listing) == [
        "https://a.test/a.m3u8",
        "https://b.test/b.m3u8",
    ]


def test_without_addresses_it_is_a_usage_error() -> None:
    with pytest.raises(typer.Exit) as raised:
        gather_urls([], None)
    assert raised.value.exit_code == EXIT_USAGE
