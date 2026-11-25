"""The output options."""

from pathlib import Path

import pytest
from rayohx import OutputFormat, RemuxBackend
from typer.testing import CliRunner

from rayohx_cli import params
from rayohx_cli.params.panels import OUTPUT
from tests.helpers.params import Declared, check_declaration, option, parse

CASES = [
    Declared("output", params.OutputPath, ("--output", "-o"), None),
    Declared("directory", params.Directory, ("--directory", "-d"), "RAYOHX_DIRECTORY"),
    Declared("format", params.Format, ("--format",), "RAYOHX_FORMAT"),
    Declared("overwrite", params.Overwrite, ("--overwrite/--no-overwrite",), "RAYOHX_OVERWRITE"),
    Declared("validate", params.Validate, ("--validate/--no-validate",), "RAYOHX_VALIDATE"),
    Declared(
        "remux-backend", params.RemuxBackendOption, ("--remux-backend",), "RAYOHX_REMUX_BACKEND"
    ),
    Declared("ffmpeg", params.Ffmpeg, ("--ffmpeg",), "RAYOHX_FFMPEG"),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_the_options_are_declared(case: Declared) -> None:
    check_declaration(case, OUTPUT)


# --- where to save --------------------------------------------------------------------------------


def test_the_output_is_a_path_given_in_full_or_short(runner: CliRunner) -> None:
    assert parse(runner, params.OutputPath, None, []).value is None
    assert parse(runner, params.OutputPath, None, ["--output", "a.mp4"]).value == Path("a.mp4")
    assert parse(runner, params.OutputPath, None, ["-o", "b.mp4"]).value == Path("b.mp4")


def test_the_output_is_never_taken_from_the_environment() -> None:
    # One variable would send every download to the same file.
    assert option(params.OutputPath).envvar is None


def test_the_directory_is_a_path_given_in_full_or_short(runner: CliRunner) -> None:
    assert parse(runner, params.Directory, None, []).value is None
    assert parse(runner, params.Directory, None, ["--directory", "out"]).value == Path("out")
    assert parse(runner, params.Directory, None, ["-d", "out"]).value == Path("out")
    assert parse(runner, params.Directory, None, [], {"RAYOHX_DIRECTORY": "x"}).value == Path("x")


# --- format ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("auto", OutputFormat.AUTO),
        ("TS", OutputFormat.TS),
        ("Mp4", OutputFormat.MP4),
        ("segments", OutputFormat.SEGMENTS),
    ],
)
def test_the_format_is_not_case_sensitive(
    runner: CliRunner, text: str, expected: OutputFormat
) -> None:
    parsed = parse(runner, params.Format, OutputFormat.AUTO, ["--format", text])
    assert parsed.value is expected


def test_the_format_defaults_to_the_one_given(runner: CliRunner) -> None:
    assert parse(runner, params.Format, OutputFormat.AUTO, []).value is OutputFormat.AUTO


def test_an_unknown_format_is_a_usage_error(runner: CliRunner) -> None:
    assert parse(runner, params.Format, OutputFormat.AUTO, ["--format", "mkv"]).exit_code == 2


def test_the_format_can_come_from_the_environment(runner: CliRunner) -> None:
    env = {"RAYOHX_FORMAT": "ts"}
    assert parse(runner, params.Format, OutputFormat.AUTO, [], env).value is OutputFormat.TS


# --- the on and off switches ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("annotated", "on", "off", "variable"),
    [
        (params.Overwrite, "--overwrite", "--no-overwrite", "RAYOHX_OVERWRITE"),
        (params.Validate, "--validate", "--no-validate", "RAYOHX_VALIDATE"),
    ],
    ids=["overwrite", "validate"],
)
def test_overwrite_and_validate_are_switches(
    runner: CliRunner, annotated: object, on: str, off: str, variable: str
) -> None:
    assert parse(runner, annotated, False, [on]).value is True
    assert parse(runner, annotated, True, [off]).value is False
    assert parse(runner, annotated, False, [], {variable: "true"}).value is True
    assert parse(runner, annotated, True, [], {variable: "false"}).value is False
    assert parse(runner, annotated, True, [off], {variable: "true"}).value is False


# --- FFmpeg ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("auto", RemuxBackend.AUTO),
        ("Native", RemuxBackend.NATIVE),
        ("FFMPEG", RemuxBackend.FFMPEG),
    ],
)
def test_the_remux_backend_is_not_case_sensitive(
    runner: CliRunner, text: str, expected: RemuxBackend
) -> None:
    parsed = parse(runner, params.RemuxBackendOption, RemuxBackend.AUTO, ["--remux-backend", text])
    assert parsed.value is expected


def test_an_unknown_remux_backend_is_a_usage_error(runner: CliRunner) -> None:
    arguments = ["--remux-backend", "magic"]
    assert parse(runner, params.RemuxBackendOption, RemuxBackend.AUTO, arguments).exit_code == 2


def test_the_remux_backend_can_come_from_the_environment(runner: CliRunner) -> None:
    env = {"RAYOHX_REMUX_BACKEND": "ffmpeg"}
    parsed = parse(runner, params.RemuxBackendOption, RemuxBackend.AUTO, [], env)
    assert parsed.value is RemuxBackend.FFMPEG


def test_the_ffmpeg_program_is_a_path(runner: CliRunner) -> None:
    assert parse(runner, params.Ffmpeg, None, []).value is None
    assert parse(runner, params.Ffmpeg, None, ["--ffmpeg", "tools/ff"]).value == Path("tools/ff")
    env = {"RAYOHX_FFMPEG": "other"}
    assert parse(runner, params.Ffmpeg, None, [], env).value == Path("other")
