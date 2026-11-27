"""Output options."""

from pathlib import Path
from typing import Annotated

import typer
from rayohx import OutputFormat, RemuxBackend

from rayohx_cli.params.panels import OUTPUT

OutputPath = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        help="Where to save. A name without an extension gets the right one. "
        "By default it is named after the address, in the current folder.",
        rich_help_panel=OUTPUT,
    ),
]
Directory = Annotated[
    Path | None,
    typer.Option(
        "--directory",
        "-d",
        envvar="RAYOHX_DIRECTORY",
        help="The folder for a file that --output does not name. Created if missing.",
        rich_help_panel=OUTPUT,
    ),
]
Format = Annotated[
    OutputFormat,
    typer.Option(
        "--format",
        envvar="RAYOHX_FORMAT",
        case_sensitive=False,
        help="auto, ts, mp4, or segments (one file per segment, in a folder).",
        rich_help_panel=OUTPUT,
    ),
]
Overwrite = Annotated[
    bool,
    typer.Option(
        "--overwrite/--no-overwrite",
        envvar="RAYOHX_OVERWRITE",
        help="Replace an existing output file.",
        rich_help_panel=OUTPUT,
    ),
]
Validate = Annotated[
    bool,
    typer.Option(
        "--validate/--no-validate",
        envvar="RAYOHX_VALIDATE",
        help="Check the finished file before putting it in place.",
        rich_help_panel=OUTPUT,
    ),
]
RemuxBackendOption = Annotated[
    RemuxBackend,
    typer.Option(
        "--remux-backend",
        envvar="RAYOHX_REMUX_BACKEND",
        case_sensitive=False,
        help="Who re-wraps streams into MP4: auto (built in, then FFmpeg), native or ffmpeg.",
        rich_help_panel=OUTPUT,
    ),
]
Ffmpeg = Annotated[
    Path | None,
    typer.Option(
        "--ffmpeg",
        envvar="RAYOHX_FFMPEG",
        help="The FFmpeg program to use, if it is not on the PATH. FFmpeg is optional.",
        rich_help_panel=OUTPUT,
    ),
]
