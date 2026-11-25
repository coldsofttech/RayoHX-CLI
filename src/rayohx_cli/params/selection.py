"""Choosing what to download."""

from pathlib import Path
from typing import Annotated

import typer

from rayohx_cli.params.panels import SELECTION

Url = Annotated[
    str,
    typer.Argument(
        help="The address of the playlist (.m3u8). Quote it if it contains & or ?.",
        metavar="URL",
    ),
]

Urls = Annotated[
    list[str] | None,
    typer.Argument(
        help="The addresses of the playlists (.m3u8). Quote them if they contain & or ?.",
        metavar="[URL]...",
    ),
]
InputFile = Annotated[
    Path | None,
    typer.Option(
        "--input-file",
        "-i",
        help="Also download the addresses listed in this file, one per line (- for standard "
        "input). Blank lines and lines starting with # are skipped.",
        rich_help_panel=SELECTION,
    ),
]
PlaylistFile = Annotated[
    Path | None,
    typer.Option(
        "--playlist-file",
        help="Read the playlist from this file instead of fetching it. The address is still "
        "needed: relative addresses in the playlist are resolved against it.",
        rich_help_panel=SELECTION,
    ),
]
StopOnError = Annotated[
    bool,
    typer.Option(
        "--stop-on-error/--no-stop-on-error",
        envvar="RAYOHX_STOP_ON_ERROR",
        help="With several addresses, stop at the first one that fails. Off by default.",
        rich_help_panel=SELECTION,
    ),
]

Quality = Annotated[
    str,
    typer.Option(
        "--quality",
        envvar="RAYOHX_QUALITY",
        help="best, worst, auto (up to 1080p), or a height such as 720p (the best at or below it).",
        rich_help_panel=SELECTION,
    ),
]
MaxResolution = Annotated[
    str | None,
    typer.Option(
        "--max-resolution",
        envvar="RAYOHX_MAX_RESOLUTION",
        help="Never pick a picture taller than this, for example 1080p.",
        rich_help_panel=SELECTION,
    ),
]
MaxBitrate = Annotated[
    str | None,
    typer.Option(
        "--max-bitrate",
        envvar="RAYOHX_MAX_BITRATE",
        help="Never pick a stream above this many bits per second, for example 4M.",
        rich_help_panel=SELECTION,
    ),
]
Variant = Annotated[
    int | None,
    typer.Option(
        "--variant",
        envvar="RAYOHX_VARIANT",
        min=1,
        help="Download this stream, by its number in `rayohx info` (the first is 1).",
        rich_help_panel=SELECTION,
    ),
]
Resolution = Annotated[
    str | None,
    typer.Option(
        "--resolution",
        envvar="RAYOHX_RESOLUTION",
        help="Only streams with exactly this size, such as 1280x720.",
        rich_help_panel=SELECTION,
    ),
]
Bandwidth = Annotated[
    str | None,
    typer.Option(
        "--bandwidth",
        envvar="RAYOHX_BANDWIDTH",
        help="Only streams with exactly this bit rate, in bits per second (for example 2800000).",
        rich_help_panel=SELECTION,
    ),
]
VariantName = Annotated[
    str | None,
    typer.Option(
        "--variant-name",
        envvar="RAYOHX_VARIANT_NAME",
        help="Only streams with exactly this name (ignoring case).",
        rich_help_panel=SELECTION,
    ),
]
Codec = Annotated[
    str | None,
    typer.Option(
        "--codec",
        envvar="RAYOHX_CODEC",
        help="Prefer this video codec: h264, hevc, vp9 or av1. Others are used if it is missing.",
        rich_help_panel=SELECTION,
    ),
]
VideoRange = Annotated[
    str | None,
    typer.Option(
        "--video-range",
        envvar="RAYOHX_VIDEO_RANGE",
        help="Prefer this dynamic range: sdr, pq, hlg or hdr (pq or hlg).",
        rich_help_panel=SELECTION,
    ),
]
MaxFrameRate = Annotated[
    float | None,
    typer.Option(
        "--max-frame-rate",
        envvar="RAYOHX_MAX_FRAME_RATE",
        help="Never pick a stream above this many frames per second, for example 30.",
        rich_help_panel=SELECTION,
    ),
]
Audio = Annotated[
    list[str] | None,
    typer.Option(
        "--audio",
        "-a",
        help="Audio language to download (repeat for several), for example en.",
        rich_help_panel=SELECTION,
    ),
]
AudioName = Annotated[
    list[str] | None,
    typer.Option(
        "--audio-name",
        help="Download the audio track with this exact name (repeatable).",
        rich_help_panel=SELECTION,
    ),
]
Subtitles = Annotated[
    list[str] | None,
    typer.Option(
        "--subtitles",
        "-s",
        help="Subtitle language to save beside the video (repeat for several).",
        rich_help_panel=SELECTION,
    ),
]
SubtitleName = Annotated[
    list[str] | None,
    typer.Option(
        "--subtitle-name",
        help="Save the subtitle track with this exact name (repeatable).",
        rich_help_panel=SELECTION,
    ),
]
VideoOnly = Annotated[
    bool,
    typer.Option(
        "--video-only",
        envvar="RAYOHX_VIDEO_ONLY",
        help="Download only the video, leaving out separate audio and subtitle tracks.",
        rich_help_panel=SELECTION,
    ),
]
