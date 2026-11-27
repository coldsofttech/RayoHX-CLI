"""The ``info`` command: what a stream offers, and what the options would pick."""

from pathlib import Path

import httpx
from rayohx_pytest.site import Site, fixture, hls_site
from typer.testing import CliRunner

from rayohx_cli.cli import app
from tests.conftest import parsed
from tests.helpers.cli import BASE, MASTER, Serve


def test_info_lists_the_streams_and_the_choice(runner: CliRunner, serve: Serve) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["info", MASTER])
    assert result.exit_code == 0, result.stderr
    out = result.stdout
    assert "Master playlist: " + MASTER in out
    assert "320x240" in out
    assert "218 kbit/s" in out
    assert "avc1.64000d" in out
    assert "audio_1" in out
    assert "eng" in out
    assert "With these settings a download would take" in out
    assert "subtitles: none" in out
    assert result.stderr == ""


def test_info_json_is_machine_readable(runner: CliRunner, serve: Serve) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["info", MASTER, "--json"])
    assert result.exit_code == 0
    data = parsed(result.stdout)
    assert data["type"] == "master"
    assert data["variants"][0]["bandwidth"] == 217800
    assert data["audio_tracks"][0]["language"] == "eng"
    assert data["selection"]["audio"] == ["audio_1"]


def test_info_shows_what_the_options_would_pick(runner: CliRunner, serve: Serve) -> None:
    master = (
        "#EXTM3U\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360\nlow.m3u8\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720\nmid.m3u8\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080\nhigh.m3u8\n"
    )
    serve(Site({"m/master.m3u8": master.encode()}))
    url = BASE + "m/master.m3u8"
    best = parsed(runner.invoke(app, ["info", url, "--json"]).stdout)
    worst = parsed(runner.invoke(app, ["info", url, "--json", "--quality", "worst"]).stdout)
    capped = parsed(runner.invoke(app, ["info", url, "--json", "--max-resolution", "720p"]).stdout)
    nothing = parsed(runner.invoke(app, ["info", url, "--json", "--max-bitrate", "100k"]).stdout)
    assert [d["selection"]["variant"] for d in (best, worst, capped, nothing)] == [3, 1, 2, 1]
    assert nothing["selection"]["notes"]
    table = runner.invoke(app, ["info", url, "--quality", "720p"]).stdout
    assert "*" in table.split("1280x720")[0].splitlines()[-1]  # the picked row is marked


def test_info_reports_unmet_wishes(runner: CliRunner, serve: Serve) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["info", MASTER, "--audio", "ja", "--subtitles", "en"])
    assert "note:" in result.stdout
    assert "'ja'" in result.stdout


def test_info_on_a_media_playlist(runner: CliRunner, serve: Serve) -> None:
    serve(hls_site("ts", "ts"))
    result = runner.invoke(app, ["info", BASE + "ts/v0.m3u8"])
    assert result.exit_code == 0
    assert "Media playlist" in result.stdout
    assert "Segments" in result.stdout
    assert "mpeg-ts" in result.stdout
    data = parsed(runner.invoke(app, ["info", BASE + "ts/v0.m3u8", "--json"]).stdout)
    assert data["segments"] == 2
    assert data["container"] == "mpeg-ts"
    assert data["complete"] is True


def test_info_sends_the_headers_and_cookies(runner: CliRunner, serve: Serve) -> None:
    site = serve(hls_site("ts", "ts"))
    runner.invoke(
        app,
        [
            "info",
            MASTER,
            "-H",
            "X-Test: yes",
            "--cookie",
            "sid=abc",
            "--user-agent",
            "Tester/1",
            "--referer",
            "https://site/",
        ],
    )
    request: httpx.Request = site.requests[0]
    assert request.headers["x-test"] == "yes"
    assert request.headers["cookie"] == "sid=abc"
    assert request.headers["user-agent"] == "Tester/1"
    assert request.headers["referer"] == "https://site/"


def test_info_hides_secrets_in_addresses(runner: CliRunner, serve: Serve) -> None:
    site = Site({"m.m3u8": b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000\nv.m3u8?token=hunter2\n"})
    serve(site)
    result = runner.invoke(app, ["info", BASE + "m.m3u8?sig=topsecret", "--json"])
    assert "hunter2" not in result.stdout
    assert "topsecret" not in result.stdout
    assert "hunter2" not in runner.invoke(app, ["info", BASE + "m.m3u8"]).stdout


def test_info_failures(runner: CliRunner, serve: Serve) -> None:
    serve(Site({"page.m3u8": b"<html>denied</html>"}))
    missing = runner.invoke(app, ["info", BASE + "nope.m3u8"])
    assert missing.exit_code == 1
    assert missing.stdout == ""
    assert "playlist was not found" in missing.stderr
    assert "Check the address" in missing.stderr
    page = runner.invoke(app, ["info", BASE + "page.m3u8", "--json"])
    assert page.exit_code == 1
    assert page.stdout == ""
    assert "did not return an HLS playlist" in page.stderr


# --- choosing a stream exactly --------------------------------------------------------------------


def _chosen(runner: CliRunner, serve: Serve, *options: str) -> int:
    serve(Site({"m/master.m3u8": fixture("ladder.m3u8")}))
    result = runner.invoke(app, ["info", BASE + "m/master.m3u8", "--json", *options])
    assert result.exit_code == 0, result.stderr
    return int(parsed(result.stdout)["selection"]["variant"])


def test_streams_are_numbered_from_one(runner: CliRunner, serve: Serve) -> None:
    serve(Site({"m/master.m3u8": fixture("ladder.m3u8")}))
    data = parsed(runner.invoke(app, ["info", BASE + "m/master.m3u8", "--json"]).stdout)
    assert [v["index"] for v in data["variants"]] == [1, 2, 3, 4]
    table = runner.invoke(app, ["info", BASE + "m/master.m3u8", "--variant", "2"]).stdout
    assert "1280x720" in table.split("*")[1].splitlines()[0]


def test_a_stream_can_be_chosen_by_number_size_bandwidth_or_name(
    runner: CliRunner, serve: Serve
) -> None:
    assert _chosen(runner, serve, "--variant", "1") == 1
    assert _chosen(runner, serve, "--resolution", "1280x720") == 3
    assert _chosen(runner, serve, "--resolution", "1280x720", "--quality", "worst") == 2
    assert _chosen(runner, serve, "--bandwidth", "2800000") == 2
    assert _chosen(runner, serve, "--bandwidth", "2.8M") == 2
    assert _chosen(runner, serve, "--variant-name", "ALT") == 3


def test_a_choice_that_matches_nothing_is_explained(runner: CliRunner, serve: Serve) -> None:
    serve(Site({"m/master.m3u8": fixture("ladder.m3u8")}))
    result = runner.invoke(app, ["info", BASE + "m/master.m3u8", "--resolution", "800x600"])
    assert result.exit_code == 2
    assert "No stream has size 800x600" in result.stderr
    assert "1: 640x360" in result.stderr


def test_info_reads_a_playlist_file_without_fetching_it(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    site = serve(hls_site("ts", "ts"))
    playlist = tmp_path / "master.m3u8"
    playlist.write_bytes(site.files["ts/master.m3u8"])
    site.files.clear()  # any request would now fail
    result = runner.invoke(app, ["info", MASTER, "--playlist-file", str(playlist)])
    assert result.exit_code == 0, result.stderr
    assert "Master playlist: " + MASTER in result.stdout


def test_info_refuses_a_playlist_file_that_is_not_a_playlist(
    runner: CliRunner, tmp_path: Path
) -> None:
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    result = runner.invoke(app, ["info", MASTER, "--playlist-file", str(page)])
    assert result.exit_code == 1
    assert "EXTM3U" in result.stderr


def test_info_cannot_read_a_missing_playlist_file(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["info", MASTER, "--playlist-file", str(tmp_path / "no.m3u8")])
    assert result.exit_code == 2
    assert "The playlist file" in result.stderr
