"""Following a download as machine-readable events (``--events``)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from rayohx_cli import output

if TYPE_CHECKING:
    from rayohx.events import DownloadEvent


def event_to_dict(event: DownloadEvent) -> dict[str, Any]:
    """A JSON-ready view of one event. Messages and data are already free of secrets."""
    document: dict[str, Any] = {
        "type": event.type.value,
        "download_id": event.download_id,
        "state": event.state.value,
        "timestamp": round(event.timestamp, 3),
    }
    if event.segment_index is not None:
        document["segment_index"] = event.segment_index
    if event.message:
        document["message"] = event.message
    if event.data:
        document["data"] = dict(event.data)
    if event.progress is not None:
        from rayohx import progress_to_dict

        document["progress"] = progress_to_dict(event.progress)
    return document


class EventStream:
    """Writes each event as one JSON line on stderr, so stdout still holds only the result."""

    def __call__(self, event: DownloadEvent) -> None:
        line = json.dumps(event_to_dict(event), ensure_ascii=False, default=str)
        output.err_console.print(line, markup=False, highlight=False, soft_wrap=True)
