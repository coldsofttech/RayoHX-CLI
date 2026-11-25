"""The ``download`` command: its options, the engine settings they become, and the result."""

from pathlib import Path

import pytest
from rayohx import OutputFormat, RemuxBackend, StorageStrategy
from rayohx_pytest.site import hls_site, single_file_site
from typer.testing import CliRunner

from rayohx_cli.cli import app
from tests.conftest import FakeDownloader, parsed
from tests.helpers.cli import BASE, MASTER, Serve, last, run_with


def test_the_download_help_lists_the_options_by_group(runner: CliRunner) -> None:
    output = runner.invoke(app, ["download", "--help"]).output
    for option in (
        "--output",
        "--quality",
        "--max-resolution",
        "--audio",
        "--subtitles",
        "--header",
        "--cookie",
        "--proxy",
        "--concurrency",
        "--resume",
        "--json",
        "--progress",
        "--remux-backend",
        "--rate-limit",
    ):
        assert option in output
    for panel in ("Choosing what to download", "Network", "Download engine", "Output"):
        assert panel in output
    assert "RAYOHX_QUALITY" in output


def test_an_unknown_progress_mode(runner: CliRunner) -> None:
    result = runner.invoke(app, ["download", MASTER, "--progress", "sparkles"])
    assert result.exit_code == 2
    assert "must be one of" in result.output


# --- the result ----------------------------------------------------------------------------------


def test_a_download_prints_the_path_and_keeps_messages_on_stderr(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(hls_site("ts", "ts"))
    out = tmp_path / "movie.mp4"
    result = runner.invoke(app, ["download", MASTER, "-o", str(out)])
    assert result.exit_code == 0, result.stderr
    assert result.stdout.strip() == str(out)
    assert out.exists()
    assert "Stream: 320x240" in result.stderr
    assert "Audio track: audio_1" in result.stderr
    assert "Finalizing..." in result.stderr
    assert "Saved movie.mp4" in result.stderr
    assert "%" in result.stderr  # plain progress lines (this is not a terminal)


def test_json_output_has_the_result_and_nothing_else_on_stdout(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["download", MASTER, "-o", str(tmp_path / "j.mp4"), "--json"])
    assert result.exit_code == 0
    data = parsed(result.stdout)
    assert data["state"] == "completed"
    assert data["success"] is True
    assert data["output"]["path"] == str(tmp_path / "j.mp4")
    assert data["output"]["container"] == "fmp4"
    assert data["progress"]["completed_segments"] > 0
    assert "%" not in result.stderr  # no progress in JSON mode


def test_an_existing_file_is_not_replaced_unless_asked(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(hls_site("ts", "ts"))
    target = tmp_path / "keep.mp4"
    target.write_bytes(b"precious")
    refused = runner.invoke(app, ["download", MASTER, "-o", str(target)])
    assert refused.exit_code == 1
    assert "already exists" in refused.stderr
    assert "allow overwriting" in refused.stderr
    assert target.read_bytes() == b"precious"
    allowed = runner.invoke(app, ["download", MASTER, "-o", str(target), "--overwrite"])
    assert allowed.exit_code == 0
    assert target.read_bytes() != b"precious"


def test_progress_modes(runner: CliRunner, serve: Serve, tmp_path: Path) -> None:
    serve(hls_site("ts", "ts"))
    none = runner.invoke(
        app, ["download", MASTER, "-o", str(tmp_path / "n.mp4"), "--progress", "none"]
    )
    assert "%" not in none.stderr
    assert "Saved" in none.stderr
    plain = runner.invoke(
        app, ["download", MASTER, "-o", str(tmp_path / "p.mp4"), "--progress", "plain"]
    )
    assert "100%" in plain.stderr
    bar = runner.invoke(
        app, ["download", MASTER, "-o", str(tmp_path / "b.mp4"), "--progress", "bar"]
    )
    assert bar.exit_code == 0


def test_subtitles_and_audio_options_reach_the_download(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    site = single_file_site("h264_aac.ts")
    site.files["show/master.m3u8"] = (
        b'#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="s",NAME="English",LANGUAGE="en",URI="en.m3u8"\n'
        b'#EXT-X-STREAM-INF:BANDWIDTH=300000,SUBTITLES="s"\nindex.m3u8\n'
    )
    site.files["show/en.m3u8"] = (
        b"#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\nen0.vtt\n#EXT-X-ENDLIST\n"
    )
    site.files["show/en0.vtt"] = b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n"
    serve(site)
    result = runner.invoke(
        app,
        ["download", BASE + "show/master.m3u8", "-o", str(tmp_path / "clip.mp4"), "-s", "en"],
    )
    assert result.exit_code == 0, result.stderr
    assert (tmp_path / "clip.en.vtt").exists()
    assert "Subtitles: English" in result.stderr


# --- options reach the engine ------------------------------------------------------------------


def test_options_are_turned_into_settings(
    runner: CliRunner, fake_downloader: type[FakeDownloader], tmp_path: Path
) -> None:
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("example.com\tTRUE\t/\tFALSE\t0\tf\t1\n", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "download", MASTER, "-o", str(tmp_path / "x.mp4"),
            "--quality", "720p", "--max-resolution", "1080p", "--max-bitrate", "4M",
            "-a", "en", "-a", "fr", "--audio-name", "Commentary",
            "-s", "en", "--subtitle-name", "SDH", "--video-only",
            "--format", "mp4", "--overwrite", "--no-validate",
            "--remux-backend", "ffmpeg", "--ffmpeg", str(tmp_path / "ff"),
            "-H", "X-A: 1", "--cookie", "a=b", "--user-agent", "U/1",
            "--referer", "https://r/", "--origin", "https://o/",
            "--proxy", "http://p:3128", "--insecure",
            "--connect-timeout", "3", "--read-timeout", "9", "--timeout", "99", "--retries", "7",
            "--rate-limit", "2M", "--credential-host", "cdn.example.com",
            "-j", "12", "--no-resume", "--storage", "hybrid", "--workspace", str(tmp_path),
            "--buffer-size", "16M", "--max-temp-size", "1G",
            "--proxy-username", "u", "--proxy-password", "pw", "--backoff", "1.5",
            "--max-redirects", "3", "--cookie-file", str(cookies),
            "--reserve-space", "1G", "--no-keep-state",
        ],
    )  # fmt: skip
    assert result.exit_code == 0, result.output
    fake = last(fake_downloader)
    assert fake.url == MASTER
    assert fake.requested_output == tmp_path / "x.mp4"
    config = fake.config
    assert config is not None
    assert config.selection.quality == "720p"
    assert config.selection.max_bitrate == 4_000_000
    assert config.selection.audio_languages == ("en", "fr")
    assert config.selection.subtitle_names == ("SDH",)
    assert config.selection.video_only
    assert config.output.format is OutputFormat.MP4
    assert config.output.overwrite
    assert not config.output.validate
    assert config.output.remux_backend is RemuxBackend.FFMPEG
    assert dict(config.network.headers) == {
        "Referer": "https://r/",
        "Origin": "https://o/",
        "X-A": "1",
    }
    assert config.network.verify_tls is False
    assert config.network.retries == 7
    assert config.network.backoff_factor == 1.5
    assert config.network.max_redirects == 3
    assert config.network.cookies == {"f": "1", "a": "b"}
    assert config.network.proxy is not None
    assert (config.network.proxy.username, config.network.proxy.password) == ("u", "pw")
    assert config.network.rate_limit == 2 * 1024**2
    assert config.concurrency == 12
    assert not config.resume
    assert config.storage.strategy is StorageStrategy.HYBRID
    assert config.storage.buffer_bytes == 16 * 1024**2
    assert config.storage.reserve_bytes == 1024**3
    assert not config.storage.keep_state_on_failure


def test_option_values_are_case_insensitive_for_choices(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    runner.invoke(app, ["download", MASTER, "--storage", "TEMPORARY", "--format", "Segments"])
    config = last(fake_downloader).config
    assert config is not None
    assert config.storage.strategy is StorageStrategy.TEMPORARY
    assert config.output.format is OutputFormat.SEGMENTS


def test_secrets_can_be_read_from_files_and_never_appear_in_output(
    runner: CliRunner, fake_downloader: type[FakeDownloader], tmp_path: Path
) -> None:
    headers = tmp_path / "h.txt"
    headers.write_text("Authorization: Bearer s3cret\n", encoding="utf-8")
    result = runner.invoke(app, ["--verbose", "download", MASTER, "-H", f"@{headers}"])
    assert result.exit_code == 0
    config = last(fake_downloader).config
    assert config is not None
    assert dict(config.network.headers) == {"Authorization": "Bearer s3cret"}
    assert "s3cret" not in result.output


def test_environment_variables_set_options(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    config = run_with(
        runner,
        fake_downloader,
        ["download", MASTER],
        {
            "RAYOHX_QUALITY": "worst",
            "RAYOHX_CONCURRENCY": "6",
            "RAYOHX_PROXY": "http://env-proxy:8080",
            "RAYOHX_OVERWRITE": "true",
            "RAYOHX_STORAGE": "temporary",
            "RAYOHX_RATE_LIMIT": "1M",
        },
    )
    assert config.selection.quality == "worst"
    assert config.concurrency == 6
    assert config.network.proxy is not None
    assert config.network.proxy.url == "http://env-proxy:8080"
    assert config.output.overwrite
    assert config.storage.strategy is StorageStrategy.TEMPORARY
    assert config.network.rate_limit == 1024**2


def test_the_command_line_beats_the_environment(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    config = run_with(
        runner,
        fake_downloader,
        ["download", MASTER, "--quality", "720p"],
        {"RAYOHX_QUALITY": "worst"},
    )
    assert config.selection.quality == "720p"


# --- exact stream choices and the space check ----------------------------------------------------


def test_the_stream_choices_and_the_space_check_reach_the_engine(
    runner: CliRunner, fake_downloader: type[FakeDownloader]
) -> None:
    runner.invoke(
        app,
        ["download", MASTER, "--resolution", "1280x720", "--bandwidth", "2M", "--variant-name", "x",
         "--no-space-check"],
    )  # fmt: skip
    config = last(fake_downloader).config
    assert config is not None
    assert config.selection.resolution == "1280x720"
    assert config.selection.bandwidth == 2_000_000
    assert config.selection.variant_name == "x"
    assert not config.storage.check_space
    runner.invoke(app, ["download", MASTER, "--variant", "3"], env={"RAYOHX_SPACE_CHECK": "false"})
    config = last(fake_downloader).config
    assert config is not None
    assert config.selection.variant == 3
    assert not config.storage.check_space


def test_the_space_check_is_on_by_default_and_can_be_turned_off(
    runner: CliRunner, serve: Serve, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(hls_site("ts", "ts"))
    calls: list[int] = []
    monkeypatch.setattr(
        "rayohx._download._storage.check_disk_space", lambda *a, **k: calls.append(1)
    )
    runner.invoke(app, ["download", MASTER, "-o", str(tmp_path / "a.mp4")])
    assert calls
    calls.clear()
    result = runner.invoke(
        app, ["download", MASTER, "-o", str(tmp_path / "b.mp4"), "--no-space-check"]
    )
    assert result.exit_code == 0
    assert not calls
    assert "space check is turned off" in result.stderr


def test_a_playlist_file_is_given_to_the_downloader(
    runner: CliRunner, fake_downloader: type[FakeDownloader], tmp_path: Path
) -> None:
    playlist = tmp_path / "local.m3u8"
    playlist.write_text("#EXTM3U\n", encoding="utf-8")
    result = runner.invoke(app, ["download", MASTER, "--playlist-file", str(playlist)])
    assert result.exit_code == 0, result.output
    assert last(fake_downloader).playlist_text == "#EXTM3U\n"


def test_a_playlist_file_that_cannot_be_read(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["download", MASTER, "--playlist-file", str(tmp_path / "no.m3u8")])
    assert result.exit_code == 2
    assert "The playlist file" in result.stderr


def test_a_playlist_file_needs_exactly_one_address(runner: CliRunner, tmp_path: Path) -> None:
    playlist = tmp_path / "local.m3u8"
    playlist.write_text("#EXTM3U\n", encoding="utf-8")
    result = runner.invoke(
        app, ["download", MASTER, BASE + "b/master.m3u8", "--playlist-file", str(playlist)]
    )
    assert result.exit_code == 2
    assert "one address" in result.stderr
