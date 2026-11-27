"""What the command tests share: addresses, a type for the ``serve`` fixture, and small helpers."""

from collections.abc import Callable

from rayohx.config import DownloadConfig
from rayohx_pytest.site import Site
from typer.testing import CliRunner

from rayohx_cli.cli import app
from tests.conftest import FakeDownloader

BASE = "https://media.example.com/"
MASTER = BASE + "ts/master.m3u8"
Serve = Callable[[Site], Site]


def last(fake: type[FakeDownloader]) -> FakeDownloader:
    """The download the command started most recently."""
    return fake.instances[-1]


def run_with(
    runner: CliRunner,
    fake: type[FakeDownloader],
    arguments: list[str],
    env: dict[str, str] | None = None,
) -> DownloadConfig:
    """Run a command that must succeed and return the settings it gave the engine."""
    result = runner.invoke(app, arguments, env=env)
    assert result.exit_code == 0, result.output
    config = last(fake).config
    assert config is not None
    return config
