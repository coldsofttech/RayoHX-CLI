"""What every command shares: exit codes and turning bad settings into a usage error."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, NoReturn

import typer
from rayohx.config import DownloadConfig
from rayohx.errors import ConfigurationError, RayoHXError

from rayohx_cli import output
from rayohx_cli.values import build_config

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_CANCELLED = 130


def usage_error(exc: RayoHXError) -> NoReturn:
    output.error_from(exc)
    raise typer.Exit(EXIT_USAGE)


def make_config(**options: object) -> DownloadConfig:
    """Build the engine's settings, turning a bad value into a usage error."""
    try:
        return build_config(**options)  # type: ignore[arg-type]
    except ConfigurationError as exc:
        usage_error(exc)


def read_playlist_file(path: Path) -> str:
    """The playlist text in ``path``, or a usage error if it cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        usage_error(ConfigurationError(f"The playlist file {path} cannot be read."))
        raise exc  # unreachable: usage_error exits


def gather_urls(urls: Sequence[str], input_file: Path | None) -> list[str]:
    """The addresses given as arguments, then those listed in ``input_file`` (``-`` is stdin)."""
    found = list(urls)
    if input_file is not None:
        try:
            if str(input_file) == "-":
                text = sys.stdin.read()
            else:
                text = input_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            usage_error(ConfigurationError(f"The address list {input_file} cannot be read."))
            raise exc  # unreachable: usage_error exits
        found.extend(
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not found:
        usage_error(
            ConfigurationError(
                "There is nothing to download.",
                hint="Give an address, or a list of addresses with --input-file.",
            )
        )
    return found


@dataclass(frozen=True)
class Source:
    """Where a playlist comes from: a web address, or playlist text already read from a file."""

    url: str
    text: str | None = None

    @property
    def label(self) -> str:
        from rayohx._redaction import redact_url

        return redact_url(self.url) if self.text is None else self.url


PLACEHOLDER_HOST = "https://playlist.invalid/"


def open_source(target: str, base_url: str | None, playlist_file: Path | None = None) -> Source:
    """A web address as it is, or a local playlist file read in.

    ``playlist_file`` names the file explicitly; otherwise ``target`` is taken as a file when it
    is not a web address and exists. The playlist's relative addresses are resolved against
    ``base_url``, or the address given. A local file given alone, with no ``base_url``, gets a
    placeholder address, which suits playlists whose addresses are all absolute.
    """
    if playlist_file is not None:
        return Source(base_url or target, read_playlist_file(playlist_file))
    if target.lower().startswith(("http://", "https://")):
        return Source(target)
    from pathlib import Path

    path = Path(target).expanduser()
    if not path.is_file():
        return Source(target)  # not a file: let the address check explain what is wrong
    return Source(base_url or PLACEHOLDER_HOST + path.name, read_playlist_file(path))
