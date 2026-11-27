"""The tables that ``info`` prints."""

from typing import Any

import pytest

from rayohx_cli import output, render
from tests.helpers.console import Captured, capture

URL = "https://media.example.com/master.m3u8"


@pytest.fixture
def printed(monkeypatch: pytest.MonkeyPatch) -> Captured:
    """The standard output, captured wide enough that no table has to wrap."""
    out = capture(width=200)
    monkeypatch.setattr(output, "console", out.console)
    return out


def variant(index: int = 1, **fields: Any) -> dict[str, Any]:
    """A stream as ``playlist_to_dict`` describes it; ``fields`` change what differs."""
    described: dict[str, Any] = {
        "index": index,
        "resolution": "1280x720",
        "bandwidth": 2_800_000,
        "average_bandwidth": None,
        "frame_rate": None,
        "audio_group": None,
        "subtitle_group": None,
        "codecs": ["avc1.64001f", "mp4a.40.2"],
    }
    return described | fields


def track(**fields: Any) -> dict[str, Any]:
    """An audio or subtitle track as ``playlist_to_dict`` describes it."""
    described: dict[str, Any] = {
        "group": "aud",
        "name": "English",
        "language": "en",
        "default": True,
        "forced": False,
        "channels": None,
        "separate": True,
    }
    return described | fields


def master(
    variants: list[dict[str, Any]] | None = None,
    *,
    audio: list[dict[str, Any]] | None = None,
    subtitles: list[dict[str, Any]] | None = None,
    selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": "master",
        "url": URL,
        "variants": variants if variants is not None else [variant()],
        "audio_tracks": audio or [],
        "subtitle_tracks": subtitles or [],
        "selection": selection,
    }


def media(**fields: Any) -> dict[str, Any]:
    described: dict[str, Any] = {
        "type": "media",
        "url": "https://media.example.com/v0.m3u8",
        "segments": 12,
        "duration": 187,
        "container": "mpeg-ts",
        "complete": True,
        "encryption": [],
        "byte_ranges": False,
        "discontinuities": 0,
    }
    return described | fields


def row(text: str, cell: str) -> str:
    """The line of a table that holds ``cell`` (the summary lines below it start with a space)."""
    matches = [line for line in text.splitlines() if cell in line and not line.startswith(" ")]
    assert len(matches) == 1, matches
    return matches[0]


# --- a master playlist: the streams ---------------------------------------------------------------


def test_a_master_playlist_starts_with_its_address_and_lists_the_streams(printed: Captured) -> None:
    render.show(master([variant(1), variant(2, resolution="640x360", bandwidth=800_000)]))
    text = printed.text
    assert text.startswith(f"Master playlist: {URL}\n")
    assert "Streams" in text
    for heading in ("#", "Size", "Bit rate", "Codecs"):
        assert heading in text
    assert "1280x720" in row(text, "2.8 Mbit/s")
    assert "640x360" in row(text, "800 kbit/s")
    assert "avc1.64001f, mp4a.40.2" in text


def test_a_stream_without_a_picture_is_audio_only(printed: Captured) -> None:
    render.show(master([variant(1, resolution=None, codecs=["mp4a.40.2"])]))
    assert "audio only" in printed.text


def test_columns_nobody_fills_in_are_left_out(printed: Captured) -> None:
    render.show(master([variant(1), variant(2)]))
    for heading in ("Average", "FPS", "Subtitles"):
        assert heading not in printed.text


@pytest.mark.parametrize(
    ("fields", "heading", "cell"),
    [
        ({"average_bandwidth": 2_500_000}, "Average", "2.5 Mbit/s"),
        ({"frame_rate": 29.97}, "FPS", "29.97"),
        ({"audio_group": "aud"}, "Audio", "aud"),
        ({"subtitle_group": "subs"}, "Subtitles", "subs"),
    ],
)
def test_a_column_appears_when_any_stream_has_a_value_for_it(
    printed: Captured, fields: dict[str, Any], heading: str, cell: str
) -> None:
    render.show(master([variant(1, **fields), variant(2)]))
    assert heading in printed.text
    assert cell in printed.text


def test_the_stream_a_download_would_pick_is_marked(printed: Captured) -> None:
    selection = {"variant": 2, "audio": [], "subtitles": [], "notes": []}
    render.show(master([variant(1, bandwidth=800_000), variant(2)], selection=selection))
    assert "*" in row(printed.text, "2.8 Mbit/s")
    assert "*" not in row(printed.text, "800 kbit/s")


def test_no_stream_is_marked_without_a_choice(printed: Captured) -> None:
    render.show(master([variant(1)]))
    assert "*" not in printed.text


# --- a master playlist: the tracks ----------------------------------------------------------------


def test_audio_and_subtitle_tracks_each_get_a_table(printed: Captured) -> None:
    render.show(
        master(
            audio=[track(name="English"), track(name="Français", language="fr", default=False)],
            subtitles=[track(group="subs", name="English")],
        )
    )
    text = printed.text
    assert "Audio tracks" in text
    assert "Subtitle tracks" in text
    for heading in ("Group", "Name", "Language", "Default", "Separate"):
        assert heading in text
    assert "Français" in text


def test_no_table_is_printed_for_tracks_the_stream_does_not_have(printed: Captured) -> None:
    render.show(master())
    assert "Audio tracks" not in printed.text
    assert "Subtitle tracks" not in printed.text


def test_the_channels_and_forced_columns_appear_only_when_some_track_needs_them(
    printed: Captured,
) -> None:
    render.show(master(audio=[track()]))
    assert "Channels" not in printed.text
    assert "Forced" not in printed.text
    printed.buffer.truncate(0)
    printed.buffer.seek(0)
    render.show(master(audio=[track(channels="2", forced=True)]))
    assert "Channels" in printed.text
    assert "Forced" in printed.text


def test_subtitle_tracks_never_show_channels(printed: Captured) -> None:
    render.show(master(subtitles=[track(channels="2")]))
    assert "Channels" not in printed.text


# --- a master playlist: what a download would take ------------------------------------------------


def test_the_choice_is_summed_up(printed: Captured) -> None:
    selection = {
        "variant": 1,
        "audio": ["English", "Français"],
        "subtitles": ["English"],
        "notes": ["No audio in German."],
    }
    render.show(master(selection=selection))
    assert printed.lines[-5:] == [
        "With these settings a download would take:",
        "  stream 1: 1280x720, 2.8 Mbit/s",
        "  audio: English, Français",
        "  subtitles: English",
        "  note: No audio in German.",
    ]


def test_the_choice_says_what_it_means_by_nothing(printed: Captured) -> None:
    selection = {"variant": 1, "audio": [], "subtitles": [], "notes": []}
    render.show(master(selection=selection))
    assert "  audio: the audio in the stream" in printed.text
    assert "  subtitles: none" in printed.text


def test_an_audio_only_choice_is_described_as_audio_only(printed: Captured) -> None:
    selection = {"variant": 1, "audio": [], "subtitles": [], "notes": []}
    render.show(master([variant(1, resolution=None)], selection=selection))
    assert "  stream 1: audio only, 2.8 Mbit/s" in printed.text


def test_nothing_is_summed_up_without_a_choice(printed: Captured) -> None:
    render.show(master(selection=None))
    assert "With these settings" not in printed.text
    render.show(master(selection={}))
    assert "With these settings" not in printed.text


# --- a media playlist -----------------------------------------------------------------------------


def test_a_media_playlist_lists_its_facts(printed: Captured) -> None:
    render.show(media())
    text = printed.text
    assert text.startswith("Media playlist: https://media.example.com/v0.m3u8\n")
    assert "12" in row(text, "Segments")
    assert "3:07" in row(text, "Duration")
    assert "mpeg-ts" in row(text, "Format")
    assert "yes" in row(text, "Complete")
    assert "none" in row(text, "Encryption")
    assert "no" in row(text, "Byte ranges")
    assert "0" in row(text, "Discontinuities")


def test_a_live_stream_is_not_complete(printed: Captured) -> None:
    render.show(media(complete=False))
    assert "no (a live stream)" in row(printed.text, "Complete")


def test_encryption_and_byte_ranges_are_shown_when_present(printed: Captured) -> None:
    render.show(media(encryption=["AES-128", "SAMPLE-AES"], byte_ranges=True, discontinuities=2))
    text = printed.text
    assert "AES-128, SAMPLE-AES" in row(text, "Encryption")
    assert "yes" in row(text, "Byte ranges")
    assert "2" in row(text, "Discontinuities")


def test_an_unknown_duration_is_shown_as_dashes(printed: Captured) -> None:
    render.show(media(duration=None))
    assert "--" in row(printed.text, "Duration")
