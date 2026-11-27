"""Events, progress snapshots and consoles for testing how a download is shown."""

from typing import Any

from rayohx import DownloadProgress, DownloadState, EventType
from rayohx.events import DownloadEvent

from tests.helpers.console import Captured, capture

__all__ = ["Captured", "capture", "make_event", "make_progress", "progress_event"]


def make_event(
    kind: EventType,
    /,
    *,
    progress: DownloadProgress | None = None,
    segment: int | None = None,
    message: str | None = None,
    **data: Any,
) -> DownloadEvent:
    """An event as the engine would send it; ``data`` becomes the event's data."""
    return DownloadEvent(
        type=kind,
        download_id="test",
        state=DownloadState.DOWNLOADING,
        progress=progress,
        segment_index=segment,
        message=message,
        data=data,
    )


def make_progress(
    done: int,
    total: int,
    *,
    downloaded: int = 0,
    speed: float = 0.0,
    eta: float | None = None,
) -> DownloadProgress:
    """A snapshot with ``done`` of ``total`` segments finished."""
    return DownloadProgress(
        state=DownloadState.DOWNLOADING,
        downloaded_bytes=downloaded,
        completed_segments=done,
        total_segments=total,
        speed=speed,
        eta_seconds=eta,
    )


def progress_event(done: int, total: int, **options: Any) -> DownloadEvent:
    """A progress event with ``done`` of ``total`` segments finished."""
    return make_event(EventType.DOWNLOAD_PROGRESS, progress=make_progress(done, total, **options))
