"""Download engine options."""

from pathlib import Path
from typing import Annotated

import typer
from rayohx import StorageStrategy

from rayohx_cli.params.panels import ENGINE

Concurrency = Annotated[
    int | None,
    typer.Option(
        "--concurrency",
        "-j",
        envvar="RAYOHX_CONCURRENCY",
        min=1,
        max=64,
        help="Segments to download at the same time (default 4).",
        rich_help_panel=ENGINE,
    ),
]
Resume = Annotated[
    bool,
    typer.Option(
        "--resume/--no-resume",
        envvar="RAYOHX_RESUME",
        help="Continue an interrupted download where it stopped.",
        rich_help_panel=ENGINE,
    ),
]
Storage = Annotated[
    StorageStrategy,
    typer.Option(
        "--storage",
        envvar="RAYOHX_STORAGE",
        case_sensitive=False,
        help="Where finished segments wait: auto, direct, streaming, buffered, temporary, hybrid.",
        rich_help_panel=ENGINE,
    ),
]
Workspace = Annotated[
    Path | None,
    typer.Option(
        "--workspace",
        envvar="RAYOHX_WORKSPACE",
        help="A folder for working files (default: beside the output).",
        rich_help_panel=ENGINE,
    ),
]
BufferSize = Annotated[
    str | None,
    typer.Option(
        "--buffer-size",
        envvar="RAYOHX_BUFFER_SIZE",
        help="Memory for the segment buffer, for example 64M.",
        rich_help_panel=ENGINE,
    ),
]
MaxTempSize = Annotated[
    str | None,
    typer.Option(
        "--max-temp-size",
        envvar="RAYOHX_MAX_TEMP_SIZE",
        help="Most working disk space to use, for example 2G.",
        rich_help_panel=ENGINE,
    ),
]
SpaceCheck = Annotated[
    bool,
    typer.Option(
        "--space-check/--no-space-check",
        envvar="RAYOHX_SPACE_CHECK",
        help="Check that the disk has room (turn off if the free space is reported wrongly).",
        rich_help_panel=ENGINE,
    ),
]
ReserveSpace = Annotated[
    str | None,
    typer.Option(
        "--reserve-space",
        envvar="RAYOHX_RESERVE_SPACE",
        help="Free disk space that must remain after the download, for example 1G "
        "(default 256M; 0 for none).",
        rich_help_panel=ENGINE,
    ),
]
KeepState = Annotated[
    bool,
    typer.Option(
        "--keep-state/--no-keep-state",
        envvar="RAYOHX_KEEP_STATE",
        help="Keep what a resume needs after a failure or Ctrl-C (on by default).",
        rich_help_panel=ENGINE,
    ),
]
AllowFileKeys = Annotated[
    bool,
    typer.Option(
        "--allow-file-keys/--no-allow-file-keys",
        envvar="RAYOHX_ALLOW_FILE_KEYS",
        help="Let a playlist's file: key addresses read a key from this machine. Off by default; "
        "only for streams you trust.",
        rich_help_panel=ENGINE,
    ),
]
