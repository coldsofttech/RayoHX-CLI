"""The display options: ``--json`` and ``--progress``."""

import pytest
from typer.testing import CliRunner

from rayohx_cli import params
from rayohx_cli.params.panels import DISPLAY
from tests.helpers.params import Declared, check_declaration, option, parse

CASES = [
    Declared("json", params.JsonOutput, ("--json",), None),
    Declared("progress", params.ProgressMode, ("--progress",), "RAYOHX_PROGRESS"),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_the_options_are_declared(case: Declared) -> None:
    check_declaration(case, DISPLAY)


def test_json_is_a_flag_that_is_off_by_default(runner: CliRunner) -> None:
    assert parse(runner, params.JsonOutput, False, []).value is False
    assert parse(runner, params.JsonOutput, False, ["--json"]).value is True


def test_json_cannot_be_turned_on_from_the_environment() -> None:
    assert option(params.JsonOutput).envvar is None


def test_progress_passes_the_mode_on_as_text(runner: CliRunner) -> None:
    assert parse(runner, params.ProgressMode, "auto", []).value == "auto"
    assert parse(runner, params.ProgressMode, "auto", ["--progress", "bar"]).value == "bar"


def test_progress_leaves_checking_the_mode_to_the_command(runner: CliRunner) -> None:
    parsed = parse(runner, params.ProgressMode, "auto", ["--progress", "sparkles"])
    assert parsed.exit_code == 0
    assert parsed.value == "sparkles"


def test_progress_can_come_from_the_environment(runner: CliRunner) -> None:
    env = {"RAYOHX_PROGRESS": "plain"}
    assert parse(runner, params.ProgressMode, "auto", [], env).value == "plain"
    assert parse(runner, params.ProgressMode, "auto", ["--progress", "none"], env).value == "none"
