"""``rayohx download`` with several addresses or an address list."""

import json
from pathlib import Path

from rayohx_pytest.site import Site, hls_site
from typer.testing import CliRunner

from rayohx_cli.cli import app
from tests.helpers.cli import BASE, Serve

ONE = BASE + "one/master.m3u8"
TWO = BASE + "two/master.m3u8"
GONE = BASE + "gone/master.m3u8"


def two_streams() -> Site:
    return Site({**hls_site("ts", "one").files, **hls_site("ts", "two").files})


def test_several_addresses_go_into_a_folder(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    folder = tmp_path / "out"
    result = runner.invoke(app, ["download", ONE, TWO, "-o", str(folder)])
    assert result.exit_code == 0, result.stderr
    printed = result.stdout.split()
    assert len(printed) == 2
    assert all(Path(path).exists() and Path(path).parent == folder for path in printed)
    assert "[1/2]" in result.stderr
    assert "[2/2]" in result.stderr


def test_an_address_list_file_is_read_with_comments_skipped(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    listing = tmp_path / "urls.txt"
    listing.write_text(f"# my streams\n\n{ONE}\n  {TWO}  \n", encoding="utf-8")
    result = runner.invoke(app, ["download", "-i", str(listing), "-o", str(tmp_path / "o")])
    assert result.exit_code == 0, result.stderr
    assert len(result.stdout.split()) == 2


def test_the_list_can_come_from_standard_input(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    result = runner.invoke(
        app, ["download", "-i", "-", "-o", str(tmp_path / "o")], input=f"{ONE}\n{TWO}\n"
    )
    assert result.exit_code == 0, result.stderr
    assert len(result.stdout.split()) == 2


def test_one_failure_does_not_stop_the_rest_but_sets_the_exit_code(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    result = runner.invoke(app, ["download", GONE, TWO, "-o", str(tmp_path / "o")])
    assert result.exit_code == 1
    assert len(result.stdout.split()) == 1  # only TWO was saved
    assert "Error" in result.stderr


def test_stop_on_error_leaves_the_rest_alone(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    result = runner.invoke(
        app, ["download", GONE, TWO, "-o", str(tmp_path / "o"), "--stop-on-error"]
    )
    assert result.exit_code == 1
    assert result.stdout.strip() == ""


def test_json_output_is_one_array(runner: CliRunner, serve: Serve, tmp_path: Path) -> None:
    serve(two_streams())
    result = runner.invoke(app, ["download", ONE, GONE, "-o", str(tmp_path / "o"), "--json"])
    assert result.exit_code == 1
    documents = json.loads(result.stdout)
    assert [doc["success"] for doc in documents] == [True, False]


def test_a_file_cannot_be_the_output_of_several_addresses(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    target = tmp_path / "file.mp4"
    target.write_bytes(b"x")
    result = runner.invoke(app, ["download", ONE, TWO, "-o", str(target)])
    assert result.exit_code == 2
    assert "folder" in result.stderr


def test_no_address_is_a_usage_error(runner: CliRunner) -> None:
    result = runner.invoke(app, ["download"])
    assert result.exit_code == 2
    assert "nothing to download" in result.stderr


def test_an_unreadable_list_is_a_usage_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["download", "-i", str(tmp_path / "missing.txt")])
    assert result.exit_code == 2
    assert "cannot be read" in " ".join(result.stderr.split())  # the long path wraps the line


def test_directory_sets_where_a_single_download_goes(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    folder = tmp_path / "made" / "here"
    result = runner.invoke(app, ["download", ONE, "-d", str(folder)])
    assert result.exit_code == 0, result.stderr
    assert Path(result.stdout.strip()).parent == folder


def test_directory_is_the_folder_for_several_addresses(
    runner: CliRunner, serve: Serve, tmp_path: Path
) -> None:
    serve(two_streams())
    result = runner.invoke(app, ["download", ONE, TWO, "-d", str(tmp_path / "d")])
    assert result.exit_code == 0, result.stderr
    assert {Path(p).parent for p in result.stdout.split()} == {tmp_path / "d"}
