"""Turning download events into text."""

import pytest
from rayohx import EventType

from rayohx_cli import format as fmt
from rayohx_cli.progress._text import detail, narrate, percent
from tests.helpers.progress import make_event, make_progress

# --- narrate --------------------------------------------------------------------------------------


def test_the_chosen_stream_is_described_with_its_size_bit_rate_and_codecs() -> None:
    event = make_event(
        EventType.STREAM_SELECTED,
        resolution="1280x720",
        bandwidth=2_800_000,
        codecs=["avc1.64001f", "mp4a.40.2"],
    )
    assert narrate(event) == ["Stream: 1280x720, 2.8 Mbit/s (avc1.64001f, mp4a.40.2)"]


def test_a_stream_without_a_size_or_codecs_is_described_by_its_bit_rate() -> None:
    event = make_event(EventType.STREAM_SELECTED, bandwidth=800_000)
    assert narrate(event) == ["Stream: 800 kbit/s"]
    assert narrate(make_event(EventType.STREAM_SELECTED, bandwidth=800_000, codecs=[])) == [
        "Stream: 800 kbit/s"
    ]


def test_notes_about_the_choice_follow_the_stream() -> None:
    event = make_event(
        EventType.STREAM_SELECTED,
        bandwidth=800_000,
        notes=["No audio in this language.", "Using the best match."],
    )
    assert narrate(event) == [
        "Stream: 800 kbit/s",
        "Note: No audio in this language.",
        "Note: Using the best match.",
    ]


def test_an_audio_track_and_subtitles_are_named_when_loaded() -> None:
    audio = make_event(EventType.PLAYLIST_LOADED, audio="en")
    subtitles = make_event(EventType.PLAYLIST_LOADED, subtitles="English")
    assert narrate(audio) == ["Audio track: en"]
    assert narrate(subtitles) == ["Subtitles: English"]


def test_a_loaded_playlist_is_mentioned_only_when_verbose() -> None:
    event = make_event(EventType.PLAYLIST_LOADED, kind="master")
    assert narrate(event) == []
    assert narrate(event, verbose=True) == ["Loaded the master playlist"]


def test_finalizing_is_announced() -> None:
    assert narrate(make_event(EventType.FINALIZATION_STARTED)) == ["Finalizing..."]


def test_a_failed_segment_is_reported_with_its_number_and_reason() -> None:
    event = make_event(EventType.SEGMENT_FAILED, segment=4, message="timed out")
    assert narrate(event) == ["Segment 4 failed: timed out"]


def test_the_start_of_a_download_is_mentioned_only_when_verbose() -> None:
    event = make_event(EventType.DOWNLOAD_STARTED, message="https://example.com/a.m3u8")
    assert narrate(event) == []
    assert narrate(event, verbose=True) == ["Downloading https://example.com/a.m3u8"]


@pytest.mark.parametrize(
    "kind",
    [
        EventType.SEGMENT_STARTED,
        EventType.SEGMENT_COMPLETED,
        EventType.DOWNLOAD_PROGRESS,
        EventType.FINALIZATION_COMPLETED,
        EventType.DOWNLOAD_COMPLETED,
        EventType.DOWNLOAD_FAILED,
        EventType.DOWNLOAD_CANCELLED,
    ],
)
def test_other_events_say_nothing(kind: EventType) -> None:
    event = make_event(kind, message="anything")
    assert narrate(event) == []
    assert narrate(event, verbose=True) == []


# --- detail ---------------------------------------------------------------------------------------


def test_the_detail_starts_with_the_size_downloaded() -> None:
    assert detail(make_progress(1, 10, downloaded=5 * 1024**2)) == fmt.size(5 * 1024**2)


def test_the_detail_adds_the_speed_and_the_time_left_when_known() -> None:
    progress = make_progress(1, 10, downloaded=1024**2, speed=2 * 1024**2, eta=65)
    assert detail(progress) == (
        f"{fmt.size(1024**2)}  {fmt.rate(2 * 1024**2)}  ETA {fmt.duration(65)}"
    )


def test_a_speed_of_zero_is_left_out_and_so_is_an_unknown_time() -> None:
    assert detail(make_progress(1, 10, downloaded=1024, speed=0.0, eta=None)) == fmt.size(1024)
    assert "ETA" in detail(make_progress(1, 10, downloaded=1024, eta=0))


# --- percent --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("done", "total", "expected"),
    [(0, 10, 0.0), (5, 10, 0.5), (10, 10, 1.0), (12, 10, 1.0), (3, 0, 0.0), (0, 0, 0.0)],
)
def test_the_share_done_comes_from_the_segments_and_never_passes_one(
    done: int, total: int, expected: float
) -> None:
    assert percent(make_progress(done, total)) == expected
