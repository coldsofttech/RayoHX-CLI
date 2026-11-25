"""The download engine options."""

from pathlib import Path

import pytest
from rayohx import StorageStrategy
from typer.testing import CliRunner

from rayohx_cli import params
from rayohx_cli.params.panels import ENGINE
from tests.helpers.params import Declared, check_declaration, option, parse

CASES = [
    Declared("concurrency", params.Concurrency, ("--concurrency", "-j"), "RAYOHX_CONCURRENCY"),
    Declared("resume", params.Resume, ("--resume/--no-resume",), "RAYOHX_RESUME"),
    Declared("storage", params.Storage, ("--storage",), "RAYOHX_STORAGE"),
    Declared("workspace", params.Workspace, ("--workspace",), "RAYOHX_WORKSPACE"),
    Declared("buffer-size", params.BufferSize, ("--buffer-size",), "RAYOHX_BUFFER_SIZE"),
    Declared("max-temp-size", params.MaxTempSize, ("--max-temp-size",), "RAYOHX_MAX_TEMP_SIZE"),
    Declared(
        "space-check",
        params.SpaceCheck,
        ("--space-check/--no-space-check",),
        "RAYOHX_SPACE_CHECK",
    ),
    Declared("reserve-space", params.ReserveSpace, ("--reserve-space",), "RAYOHX_RESERVE_SPACE"),
    Declared(
        "keep-state", params.KeepState, ("--keep-state/--no-keep-state",), "RAYOHX_KEEP_STATE"
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_the_options_are_declared(case: Declared) -> None:
    check_declaration(case, ENGINE)


# --- concurrency ----------------------------------------------------------------------------------


def test_concurrency_is_left_to_the_engine_unless_given(runner: CliRunner) -> None:
    assert parse(runner, params.Concurrency, None, []).value is None


def test_concurrency_can_be_given_in_full_or_short(runner: CliRunner) -> None:
    assert parse(runner, params.Concurrency, None, ["--concurrency", "8"]).value == 8
    assert parse(runner, params.Concurrency, None, ["-j", "3"]).value == 3


def test_concurrency_is_limited_to_1_through_64() -> None:
    info = option(params.Concurrency)
    assert (info.min, info.max) == (1, 64)


@pytest.mark.parametrize("value", ["0", "65", "-2", "many"])
def test_concurrency_outside_the_limits_is_a_usage_error(runner: CliRunner, value: str) -> None:
    assert parse(runner, params.Concurrency, None, ["-j", value]).exit_code == 2


def test_concurrency_can_come_from_the_environment(runner: CliRunner) -> None:
    env = {"RAYOHX_CONCURRENCY": "6"}
    assert parse(runner, params.Concurrency, None, [], env).value == 6
    assert parse(runner, params.Concurrency, None, ["-j", "2"], env).value == 2


# --- the on and off switches ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("annotated", "off", "variable"),
    [
        (params.Resume, "--no-resume", "RAYOHX_RESUME"),
        (params.SpaceCheck, "--no-space-check", "RAYOHX_SPACE_CHECK"),
        (params.KeepState, "--no-keep-state", "RAYOHX_KEEP_STATE"),
    ],
    ids=["resume", "space-check", "keep-state"],
)
def test_resume_and_the_space_check_are_on_unless_turned_off(
    runner: CliRunner, annotated: object, off: str, variable: str
) -> None:
    assert parse(runner, annotated, True, []).value is True
    assert parse(runner, annotated, True, [off]).value is False
    assert parse(runner, annotated, True, [], {variable: "false"}).value is False
    assert parse(runner, annotated, True, [off], {variable: "true"}).value is False


# --- storage --------------------------------------------------------------------------------------


def test_storage_names_are_not_case_sensitive(runner: CliRunner) -> None:
    default = StorageStrategy.AUTO
    assert parse(runner, params.Storage, default, []).value is StorageStrategy.AUTO
    assert parse(runner, params.Storage, default, ["--storage", "TEMPORARY"]).value is (
        StorageStrategy.TEMPORARY
    )
    assert parse(runner, params.Storage, default, ["--storage", "Hybrid"]).value is (
        StorageStrategy.HYBRID
    )


def test_an_unknown_storage_is_a_usage_error(runner: CliRunner) -> None:
    parsed = parse(runner, params.Storage, StorageStrategy.AUTO, ["--storage", "nowhere"])
    assert parsed.exit_code == 2


def test_storage_can_come_from_the_environment(runner: CliRunner) -> None:
    env = {"RAYOHX_STORAGE": "buffered"}
    parsed = parse(runner, params.Storage, StorageStrategy.AUTO, [], env)
    assert parsed.value is StorageStrategy.BUFFERED


# --- working files and sizes ----------------------------------------------------------------------


def test_the_workspace_is_a_folder_path(runner: CliRunner) -> None:
    assert parse(runner, params.Workspace, None, []).value is None
    assert parse(runner, params.Workspace, None, ["--workspace", "work"]).value == Path("work")
    env = {"RAYOHX_WORKSPACE": "elsewhere"}
    assert parse(runner, params.Workspace, None, [], env).value == Path("elsewhere")


@pytest.mark.parametrize(
    ("annotated", "flag", "variable"),
    [
        (params.BufferSize, "--buffer-size", "RAYOHX_BUFFER_SIZE"),
        (params.MaxTempSize, "--max-temp-size", "RAYOHX_MAX_TEMP_SIZE"),
        (params.ReserveSpace, "--reserve-space", "RAYOHX_RESERVE_SPACE"),
    ],
    ids=["buffer-size", "max-temp-size", "reserve-space"],
)
def test_sizes_are_passed_on_as_typed(
    runner: CliRunner, annotated: object, flag: str, variable: str
) -> None:
    # The suffix ("64M", "2G") is understood later, where the engine settings are built.
    assert parse(runner, annotated, None, []).value is None
    assert parse(runner, annotated, None, [flag, "64M"]).value == "64M"
    assert parse(runner, annotated, None, [], {variable: "2G"}).value == "2G"
