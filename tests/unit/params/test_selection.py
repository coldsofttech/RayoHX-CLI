"""The options that choose what to download."""

import pytest
from typer.models import ArgumentInfo
from typer.testing import CliRunner

from rayohx_cli import params
from rayohx_cli.params.panels import SELECTION
from tests.helpers.params import Declared, check_declaration, declaration, option, parse

CASES = [
    Declared("quality", params.Quality, ("--quality",), "RAYOHX_QUALITY"),
    Declared(
        "max-resolution", params.MaxResolution, ("--max-resolution",), "RAYOHX_MAX_RESOLUTION"
    ),
    Declared("max-bitrate", params.MaxBitrate, ("--max-bitrate",), "RAYOHX_MAX_BITRATE"),
    Declared("variant", params.Variant, ("--variant",), "RAYOHX_VARIANT"),
    Declared("resolution", params.Resolution, ("--resolution",), "RAYOHX_RESOLUTION"),
    Declared("bandwidth", params.Bandwidth, ("--bandwidth",), "RAYOHX_BANDWIDTH"),
    Declared("variant-name", params.VariantName, ("--variant-name",), "RAYOHX_VARIANT_NAME"),
    Declared("audio", params.Audio, ("--audio", "-a"), None),
    Declared("audio-name", params.AudioName, ("--audio-name",), None),
    Declared("subtitles", params.Subtitles, ("--subtitles", "-s"), None),
    Declared("subtitle-name", params.SubtitleName, ("--subtitle-name",), None),
    Declared("video-only", params.VideoOnly, ("--video-only",), "RAYOHX_VIDEO_ONLY"),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_the_options_are_declared(case: Declared) -> None:
    check_declaration(case, SELECTION)


# --- the address ----------------------------------------------------------------------------------


def test_the_address_is_a_required_argument_shown_as_url() -> None:
    info = declaration(params.Url)
    assert isinstance(info, ArgumentInfo)
    assert info.metavar == "URL"
    assert info.help


def test_the_address_is_passed_on_as_typed(runner: CliRunner) -> None:
    parsed = parse(runner, params.Url, ..., ["https://example.com/a.m3u8?x=1&y=2"])
    assert parsed.value == "https://example.com/a.m3u8?x=1&y=2"


def test_the_address_is_required(runner: CliRunner) -> None:
    assert parse(runner, params.Url, ..., []).exit_code == 2


# --- quality --------------------------------------------------------------------------------------


def test_the_quality_can_be_typed_or_come_from_the_environment(runner: CliRunner) -> None:
    assert parse(runner, params.Quality, "best", []).value == "best"
    assert parse(runner, params.Quality, "best", ["--quality", "720p"]).value == "720p"
    env = {"RAYOHX_QUALITY": "worst"}
    assert parse(runner, params.Quality, "best", [], env).value == "worst"
    assert parse(runner, params.Quality, "best", ["--quality", "720p"], env).value == "720p"


@pytest.mark.parametrize(
    ("annotated", "flag", "variable"),
    [
        (params.MaxResolution, "--max-resolution", "RAYOHX_MAX_RESOLUTION"),
        (params.MaxBitrate, "--max-bitrate", "RAYOHX_MAX_BITRATE"),
        (params.Resolution, "--resolution", "RAYOHX_RESOLUTION"),
        (params.Bandwidth, "--bandwidth", "RAYOHX_BANDWIDTH"),
        (params.VariantName, "--variant-name", "RAYOHX_VARIANT_NAME"),
    ],
    ids=["max-resolution", "max-bitrate", "resolution", "bandwidth", "variant-name"],
)
def test_limits_and_exact_choices_are_passed_on_as_typed(
    runner: CliRunner, annotated: object, flag: str, variable: str
) -> None:
    # Units such as "4M" or "720p" are understood later, where the engine settings are built.
    assert parse(runner, annotated, None, []).value is None
    assert parse(runner, annotated, None, [flag, "4M"]).value == "4M"
    assert parse(runner, annotated, None, [], {variable: "from-env"}).value == "from-env"


# --- the stream's number --------------------------------------------------------------------------


def test_the_variant_counts_from_one(runner: CliRunner) -> None:
    assert option(params.Variant).min == 1
    assert parse(runner, params.Variant, None, []).value is None
    assert parse(runner, params.Variant, None, ["--variant", "3"]).value == 3
    assert parse(runner, params.Variant, None, [], {"RAYOHX_VARIANT": "2"}).value == 2


@pytest.mark.parametrize("value", ["0", "-1", "first"])
def test_a_variant_that_is_not_a_positive_number_is_a_usage_error(
    runner: CliRunner, value: str
) -> None:
    assert parse(runner, params.Variant, None, ["--variant", value]).exit_code == 2


# --- tracks ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("annotated", "flag"),
    [
        (params.Audio, "--audio"),
        (params.AudioName, "--audio-name"),
        (params.Subtitles, "--subtitles"),
        (params.SubtitleName, "--subtitle-name"),
    ],
    ids=["audio", "audio-name", "subtitles", "subtitle-name"],
)
def test_tracks_can_be_asked_for_more_than_once(
    runner: CliRunner, annotated: object, flag: str
) -> None:
    assert parse(runner, annotated, None, []).value is None
    assert parse(runner, annotated, None, [flag, "en", flag, "fr"]).value == ["en", "fr"]


def test_audio_and_subtitles_have_short_forms(runner: CliRunner) -> None:
    assert parse(runner, params.Audio, None, ["-a", "en", "-a", "fr"]).value == ["en", "fr"]
    assert parse(runner, params.Subtitles, None, ["-s", "en"]).value == ["en"]


@pytest.mark.parametrize(
    "annotated", [params.Audio, params.AudioName, params.Subtitles, params.SubtitleName]
)
def test_tracks_are_never_read_from_the_environment(annotated: object) -> None:
    assert option(annotated).envvar is None


def test_video_only_is_a_flag_that_is_off_by_default(runner: CliRunner) -> None:
    assert parse(runner, params.VideoOnly, False, []).value is False
    assert parse(runner, params.VideoOnly, False, ["--video-only"]).value is True
    assert parse(runner, params.VideoOnly, False, [], {"RAYOHX_VIDEO_ONLY": "true"}).value is True
