"""The root command: the version, the help, the options every command takes, and settings files."""

from pathlib import Path

import httpx
import pytest
from rayohx import __version__
from rayohx_pytest.site import hls_site
from typer.testing import CliRunner

from rayohx_cli.cli import app
from rayohx_cli.settings import user_config_file
from tests.conftest import FakeDownloader, parsed
from tests.helpers.cli import MASTER, Serve, run_with

# --- help, version and usage errors ------------------------------------------------------------


def test_the_version_is_printed_on_stdout(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"rayohx {__version__}"
    assert runner.invoke(app, ["-V"]).stdout.strip() == f"rayohx {__version__}"


def test_without_arguments_the_help_is_shown(runner: CliRunner) -> None:
    result = runner.invoke(app, [])
    assert "info" in result.output
    assert "download" in result.output
    assert "--verbose" in result.output


@pytest.mark.parametrize("command", [[], ["info"], ["download"]])
def test_every_command_has_help(runner: CliRunner, command: list[str]) -> None:
    result = runner.invoke(app, [*command, "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["download"],
        ["info"],
        ["download", MASTER, "--concurrency", "0"],
        ["download", MASTER, "--concurrency", "100"],
        ["download", MASTER, "--storage", "nowhere"],
        ["download", MASTER, "--format", "mkv"],
        ["download", MASTER, "--bogus"],
        ["download", MASTER, "--retries", "-1"],
        ["frobnicate"],
    ],
)
def test_usage_errors_exit_with_code_2(runner: CliRunner, arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)
    assert result.exit_code == 2
    assert result.stdout == ""


# --- the options every command takes -------------------------------------------------------------


def test_conflicting_global_options(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--verbose", "--quiet", "info", MASTER])
    assert result.exit_code == 2
    assert "cannot be used together" in result.output
    result = runner.invoke(app, ["--config", "x.toml", "--no-config", "info", MASTER])
    assert result.exit_code == 2


def test_quiet_prints_only_the_result(runner: CliRunner, serve: Serve, tmp_path: Path) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["--quiet", "download", MASTER, "-o", str(tmp_path / "q.mp4")])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(tmp_path / "q.mp4")
    assert result.stderr == ""


def test_verbose_adds_detail(runner: CliRunner, serve: Serve, tmp_path: Path) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["--verbose", "download", MASTER, "-o", str(tmp_path / "v.mp4")])
    assert result.exit_code == 0
    assert "Downloading " + MASTER in result.stderr
    assert "Loaded the master playlist" in result.stderr


def test_global_options_can_come_from_the_environment(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(
        app,
        ["download", MASTER, "-o", str(tmp_path / "e.mp4")],
        env={"RAYOHX_QUIET": "1"},
    )
    assert result.exit_code == 0
    assert result.stderr == ""


def test_retries_are_visible_and_secrets_are_not(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from rayohx._http import HttpClient

    site = hls_site("ts", "ts")
    seen: set[str] = set()

    def flaky(request: httpx.Request) -> httpx.Response:
        key = request.url.path
        if key.endswith("v0_0.ts") and key not in seen:
            seen.add(key)
            return httpx.Response(503)
        return site(request)

    def factory(config: object, **options: object) -> HttpClient:
        options["transport"] = httpx.MockTransport(flaky)
        return HttpClient(config, **options)  # type: ignore[arg-type]

    monkeypatch.setattr("rayohx._http.HttpClient", factory)
    log = tmp_path / "run.log"
    result = runner.invoke(
        app,
        [
            "--log-file", str(log), "download", MASTER + "?token=hunter2",
            "-o", str(tmp_path / "r.mp4"), "--retries", "2",
        ],
    )  # fmt: skip
    assert result.exit_code == 0, result.stderr
    assert "Retrying" in result.stderr
    text = log.read_text(encoding="utf-8")
    assert "Retrying" in text
    assert "hunter2" not in text
    assert "hunter2" not in result.stderr


# --- the settings file ----------------------------------------------------------------------------


def test_the_settings_file_gives_defaults(
    runner: CliRunner, fake_downloader: type[FakeDownloader], tmp_path: Path
) -> None:
    (Path.cwd() / "rayohx.toml").write_text(
        'quality = "720p"\nconcurrency = 8\nheader = ["X-From: file"]\nretries = 9\n',
        encoding="utf-8",
    )
    config = run_with(runner, fake_downloader, ["download", MASTER])
    assert config.selection.quality == "720p"
    assert config.concurrency == 8
    assert dict(config.network.headers) == {"X-From": "file"}
    assert config.network.retries == 9


def test_precedence_is_command_line_then_environment_then_file(
    runner: CliRunner, fake_downloader: type[FakeDownloader], tmp_path: Path
) -> None:
    file = tmp_path / "c.toml"
    file.write_text('quality = "480p"\nconcurrency = 2\nretries = 1\n', encoding="utf-8")
    config = run_with(
        runner,
        fake_downloader,
        ["--config", str(file), "download", MASTER, "--retries", "5"],
        {"RAYOHX_CONCURRENCY": "3"},
    )
    assert config.selection.quality == "480p"  # file only
    assert config.concurrency == 3  # environment beats file
    assert config.network.retries == 5  # command line beats both


def test_a_settings_file_applies_to_every_command_that_has_the_option(
    runner: CliRunner, serve: Serve
) -> None:
    serve(hls_site("ts", "ts"))
    (Path.cwd() / "rayohx.toml").write_text('quality = "worst"\n', encoding="utf-8")
    data = parsed(runner.invoke(app, ["info", MASTER, "--json"]).stdout)
    assert data["selection"]["variant"] == 1


def test_settings_files_can_be_ignored(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    (Path.cwd() / "rayohx.toml").write_text('quality = "720p"\n', encoding="utf-8")
    config = run_with(runner, fake_downloader, ["--no-config", "download", MASTER])
    assert config.selection.quality == "best"


def test_a_settings_file_with_a_typo_is_an_error(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    (Path.cwd() / "rayohx.toml").write_text('qualty = "720p"\n', encoding="utf-8")
    result = runner.invoke(app, ["download", MASTER])
    assert result.exit_code == 2
    assert "Did you mean" in result.stderr
    assert "quality" in result.stderr
    assert not fake_downloader.instances


def test_a_named_settings_file_that_is_missing_is_an_error(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--config", "missing.toml", "info", MASTER])
    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_a_wrong_value_in_the_file_is_rejected(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    (Path.cwd() / "rayohx.toml").write_text('concurrency = "lots"\n', encoding="utf-8")
    result = runner.invoke(app, ["download", MASTER])
    assert result.exit_code == 2


def test_the_personal_settings_file_is_found(
    runner: CliRunner, fake_downloader: type[FakeDownloader], tmp_path: Path
) -> None:
    personal = user_config_file()
    personal.parent.mkdir(parents=True)
    personal.write_text('quality = "worst"\n', encoding="utf-8")
    config = run_with(runner, fake_downloader, ["download", MASTER])
    assert config.selection.quality == "worst"
