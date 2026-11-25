"""The ``clean`` and ``config`` commands."""

import json
import os
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rayohx_cli.cli import app


def make_workspace(
    parent: Path, name: str = ".rayohx-0123456789abcdef", age_days: float = 0
) -> Path:
    folder = parent / name
    (folder / "segments").mkdir(parents=True)
    (folder / "state.json").write_text("{}", encoding="utf-8")
    (folder / "segments" / "000001").write_bytes(b"x" * 2048)
    if age_days:
        stamp = time.time() - age_days * 86400
        os.utime(folder / "state.json", (stamp, stamp))
    return folder


def test_clean_lists_and_removes_leftover_folders(runner: CliRunner, tmp_path: Path) -> None:
    keep = tmp_path / "movie.mp4"
    keep.write_bytes(b"data")
    leftover = make_workspace(tmp_path)
    dry = runner.invoke(app, ["clean", str(tmp_path), "--dry-run"])
    assert dry.exit_code == 0, dry.stderr
    assert leftover.exists()
    assert "Would remove 1" in dry.stderr
    result = runner.invoke(app, ["clean", str(tmp_path), "--yes"])
    assert result.exit_code == 0, result.stderr
    assert result.stdout.strip() == str(leftover)
    assert not leftover.exists()
    assert keep.exists()


def test_clean_asks_first_and_can_be_declined(runner: CliRunner, tmp_path: Path) -> None:
    leftover = make_workspace(tmp_path)
    result = runner.invoke(app, ["clean", str(tmp_path)], input="n\n")
    assert result.exit_code == 1
    assert leftover.exists()


def test_clean_can_keep_recent_folders(runner: CliRunner, tmp_path: Path) -> None:
    fresh = make_workspace(tmp_path, ".rayohx-aaaaaaaaaaaaaaaa")
    stale = make_workspace(tmp_path, ".rayohx-bbbbbbbbbbbbbbbb", age_days=10)
    result = runner.invoke(app, ["clean", str(tmp_path), "--older-than", "7", "--yes"])
    assert result.exit_code == 0, result.stderr
    assert fresh.exists()
    assert not stale.exists()


def test_clean_finds_hash_named_folders_in_a_workspace_dir(
    runner: CliRunner, tmp_path: Path
) -> None:
    inside = make_workspace(tmp_path, "0123456789abcdef")
    unrelated = tmp_path / "photos"
    unrelated.mkdir()
    runner.invoke(app, ["clean", str(tmp_path), "--yes"])
    assert not inside.exists()
    assert unrelated.exists()


def test_clean_with_nothing_to_do(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["clean", str(tmp_path)])
    assert result.exit_code == 0
    assert "Nothing to clean" in result.stderr


@pytest.mark.skipif(os.name == "nt", reason="uses a POSIX file lock")
def test_clean_leaves_folders_a_download_is_using(runner: CliRunner, tmp_path: Path) -> None:
    from rayohx._download._workspace import _FileLock

    busy = make_workspace(tmp_path)
    lock = _FileLock(busy / "lock")
    assert lock.acquire()
    try:
        result = runner.invoke(app, ["clean", str(tmp_path), "--yes"])
    finally:
        lock.release()
    assert "1 in use" in result.stderr
    assert busy.exists()


def test_config_shows_the_file_and_hides_secrets(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = tmp_path / "rayohx.toml"
    settings.write_text('quality = "720p"\nproxy = "http://u:p@h:1"\n', encoding="utf-8")
    monkeypatch.setenv("RAYOHX_CONCURRENCY", "2")
    monkeypatch.setenv("RAYOHX_PROXY_PASSWORD", "hunter2")
    result = runner.invoke(app, ["--config", str(settings), "config", "--json"])
    assert result.exit_code == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["settings_file"] == str(settings)
    assert data["settings"] == {"quality": "720p", "proxy": "***"}
    assert data["environment"]["RAYOHX_CONCURRENCY"] == "2"
    assert "hunter2" not in result.output
    assert "u:p@h" not in result.output


def test_config_with_no_config_ignores_files(runner: CliRunner, tmp_path: Path) -> None:
    settings = tmp_path / "rayohx.toml"
    settings.write_text('quality = "720p"\n', encoding="utf-8")
    result = runner.invoke(app, ["--no-config", "config", "--json"])
    data = json.loads(result.stdout)
    assert data["ignored"] is True
    assert data["settings"] == {}


def test_config_prints_a_readable_summary(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = tmp_path / "rayohx.toml"
    settings.write_text('quality = "720p"\n', encoding="utf-8")
    monkeypatch.setenv("RAYOHX_CONCURRENCY", "2")
    result = runner.invoke(app, ["--config", str(settings), "config"])
    assert result.exit_code == 0, result.stderr
    assert f"settings file: {settings}" in result.stdout
    assert "quality = '720p'" in result.stdout
    assert "RAYOHX_CONCURRENCY=2" in result.stdout


def test_config_says_where_it_looked_when_there_is_no_file(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0, result.stderr
    assert "settings file: none" in result.stdout
    assert "Looked for" in result.stderr


def test_config_rejects_an_unreadable_settings_file(runner: CliRunner, tmp_path: Path) -> None:
    settings = tmp_path / "rayohx.toml"
    settings.write_text("this is = = not toml", encoding="utf-8")
    result = runner.invoke(app, ["--config", str(settings), "config"])
    assert result.exit_code == 2


def test_clean_ignores_a_folder_that_does_not_exist(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["clean", str(tmp_path / "missing")])
    assert result.exit_code == 0
    assert "Nothing to clean" in result.stderr
