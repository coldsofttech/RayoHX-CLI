"""Turning download events into text for the reporters."""

from rayohx import DownloadProgress, EventType
from rayohx.events import DownloadEvent

from rayohx_cli import format as fmt


def narrate(event: DownloadEvent, *, verbose: bool = False) -> list[str]:
    """What an event means to a person, as lines of text (usually none or one)."""
    kind = event.type
    data = event.data
    if kind is EventType.STREAM_SELECTED:
        parts = [str(data["resolution"])] if data.get("resolution") else []
        parts.append(fmt.bitrate(int(data["bandwidth"])))
        codecs = ", ".join(data.get("codecs") or [])
        lines = [f"Stream: {', '.join(parts)}" + (f" ({codecs})" if codecs else "")]
        lines += [f"Note: {note}" for note in data.get("notes", [])]
        return lines
    if kind is EventType.PLAYLIST_LOADED:
        if data.get("audio"):
            return [f"Audio track: {data['audio']}"]
        if data.get("subtitles"):
            return [f"Subtitles: {data['subtitles']}"]
        return [f"Loaded the {data.get('kind', '')} playlist"] if verbose else []
    if kind is EventType.FINALIZATION_STARTED:
        return ["Finalizing..."]
    if kind is EventType.SEGMENT_FAILED:
        return [f"Segment {event.segment_index} failed: {event.message}"]
    if kind is EventType.DOWNLOAD_STARTED and verbose:
        return [f"Downloading {event.message}"]
    return []


def detail(progress: DownloadProgress) -> str:
    parts = [fmt.size(progress.downloaded_bytes)]
    if progress.speed > 0:
        parts.append(fmt.rate(progress.speed))
    if progress.eta_seconds is not None:
        parts.append(f"ETA {fmt.duration(progress.eta_seconds)}")
    return "  ".join(parts)


def percent(progress: DownloadProgress) -> float:
    if progress.total_segments:
        return min(1.0, progress.completed_segments / progress.total_segments)
    return 0.0
