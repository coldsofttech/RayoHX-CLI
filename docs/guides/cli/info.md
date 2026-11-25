# info

`rayohx info` shows what a stream offers without downloading any media: the video qualities, the
audio and subtitle tracks, and which of them a download with the same options would pick.

[Back to the command line guide](../cli.md)

```bash
rayohx info URL_OR_FILE [OPTIONS]
```

```bash
rayohx info https://cdn.example.com/vod/master.m3u8 --max-resolution 720p
rayohx info https://cdn.example.com/vod/master.m3u8 --playlist-file master.m3u8
```

`--playlist-file PATH` reads the playlist from a file instead of fetching it (the address is still
needed to resolve relative addresses), like [`rayohx.inspect_text`](https://github.com/coldsofttech/RayoHX/blob/main/packages/core/docs/guides/python/inspecting.md#inspect_text). The file can also be given in
place of the address, with `--base-url` for its relative addresses.

It does the same work as [`rayohx.inspect`](https://github.com/coldsofttech/RayoHX/blob/main/packages/core/docs/guides/python/inspecting.md) followed by
[`rayohx.select_stream`](https://github.com/coldsofttech/RayoHX/blob/main/packages/core/docs/guides/python/selecting.md).

## What it shows

For a **master playlist** (a stream with several qualities) it prints three tables and a summary:

```text
Master playlist: https://media.example.com/vod/title/master.m3u8
Streams
┌───┬───┬────────────┬────────────┬───────┬───────────┬────────────────────────┐
│   │ # │ Size       │ Bit rate   │ Audio │ Subtitles │ Codecs                 │
├───┼───┼────────────┼────────────┼───────┼───────────┼────────────────────────┤
│   │ 0 │ 1280x720   │ 2.0 Mbit/s │ aud   │ subs      │ avc1.64001f, mp4a.40.2 │
│ * │ 1 │ 1920x1080  │ 4.5 Mbit/s │ aud   │ subs      │ avc1.640028, mp4a.40.2 │
│   │ 2 │ audio only │ 64 kbit/s  │ aud   │           │ mp4a.40.2              │
└───┴───┴────────────┴────────────┴───────┴───────────┴────────────────────────┘
Audio tracks
...
Subtitle tracks
...
With these settings a download would take:
  stream 1: 1920x1080, 4.5 Mbit/s
  audio: Français
  subtitles: none
```

- The `*` marks the stream the options you gave would pick. Change `--quality`, `--max-resolution`,
  `--max-bitrate`, `--variant`, `--audio` or `--subtitles` and the mark moves.
- Streams are numbered from 1. `--variant 3` picks stream 3 by itself; `--resolution 1280x720`,
  `--bandwidth` (matches the bit rate or the average) and `--variant-name` narrow the choice and can
  be combined, and `--quality` then picks among what is left. A choice that matches nothing lists
  the streams that exist.
- If a wish cannot be met (for example no French audio exists), the summary says so in plain words
  and shows the closest choice.

For a **media playlist** (a single stream with no choices) it shows the number of segments, the
duration, the container, whether it is a complete video or still live, and the encryption method.

Addresses are shown with tokens and signatures removed.

## Options

`info` accepts the options that choose a stream or reach it. The rest, such as output and engine
settings, belong to [`download`](download.md).

### Choosing what to download

These only decide which stream is marked with `*`; nothing is downloaded.

| Option | Short | Description |
|---|---|---|
| `--quality` | | `best` (default), `worst`, `auto` (up to 1080p), or a height such as `720p` (the best at or below it). |
| `--max-resolution` | | Never pick a picture taller than this, for example `1080p`. |
| `--max-bitrate` | | Never pick a stream above this many bits per second, for example `4M`. |
| `--codec` | | Prefer this video codec: `h264`, `hevc`, `vp9` or `av1`. Others are used if it is missing. |
| `--video-range` | | Prefer this dynamic range: `sdr`, `pq`, `hlg` or `hdr` (`pq` or `hlg`). |
| `--max-frame-rate` | | Never pick a stream above this many frames per second, for example `30`. |
| `--variant` | | Download this stream, by its number in `rayohx info` (the first is 1). |
| `--resolution` | | Only streams with exactly this size, such as `1280x720`. |
| `--bandwidth` | | Only streams with exactly this bit rate, in bits per second (for example `2800000`). |
| `--variant-name` | | Only streams with exactly this name (ignoring case). |
| `--codec` | | Prefer this video codec: `h264`, `hevc`, `vp9` or `av1`. Others are used if it is missing. |
| `--video-range` | | Prefer this dynamic range: `sdr`, `pq`, `hlg` or `hdr` (`pq` or `hlg`). |
| `--max-frame-rate` | | Never pick a stream above this many frames per second, for example `30`. |
| `--audio` | `-a` | Audio language to pick (repeat for several), for example `en`. |
| `--audio-name` | | Pick the audio track with this exact name (repeatable). |
| `--subtitles` | `-s` | Subtitle language to pick (repeat for several). |
| `--subtitle-name` | | Pick the subtitle track with this exact name (repeatable). |
| `--video-only` | | Leave out separate audio and subtitle tracks. |

### Network

| Option | Short | Description |
|---|---|---|
| `--header` | `-H` | Send a header, as `Name: value` (repeatable). `@file` reads them from a file. |
| `--cookie` | | Send a cookie, as `name=value` (repeatable). `@file` reads them from a file. |
| `--cookie-file` | | Read cookies from a browser-exported `cookies.txt` (Netscape format). Domains are not checked. |
| `--user-agent` | | The `User-Agent` to send. |
| `--referer` | | The `Referer` to send. |
| `--origin` | | The `Origin` to send. |
| `--proxy` | | An `http://`, `https://`, `socks5://` or `socks5h://` proxy, for example `http://user:pass@host:3128`. Prefer the environment variable. |
| `--proxy-username` | | The proxy user name, if it is not in the `--proxy` address. Needs `--proxy`. |
| `--proxy-password` | | The proxy password. Prefer the environment variable `RAYOHX_PROXY_PASSWORD`. |
| `--insecure` | | Do not check TLS certificates. Only for servers you trust. |
| `--proxy-username`, `--proxy-password` | | The proxy login, if it is not in the `--proxy` address. Both are needed, with `--proxy`. Prefer the environment variables. |
| `--cookie-file` | | Read cookies from a Netscape-format `cookies.txt` (as exported by browsers). Domains are not checked. |
| `--base-url` | | When the playlist is a local file, resolve its relative addresses against this web address. |
| `--env-proxy` / `--no-env-proxy` | | Use `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY` when `--proxy` is not given. Off by default. |
| `--client-cert` | | A client certificate (PEM) for servers that require mutual TLS. |
| `--client-key` | | The private key for `--client-cert`, if it is a separate file. |
| `--client-key-password` | | The password of an encrypted client key. Prefer the environment variable `RAYOHX_CLIENT_KEY_PASSWORD`. |
| `--ca-bundle` | | A file of trusted certificate authorities (PEM), instead of the system's. |
| `--client-cert` | | A client certificate (PEM) for servers that require mutual TLS. |
| `--client-key` | | The private key (PEM) for `--client-cert`, if it is in a separate file. |
| `--client-key-password` | | The password of an encrypted client key. Prefer the environment variable. |
| `--connect-timeout` | | Seconds to wait to connect. |
| `--read-timeout` | | Seconds to wait for data. |
| `--timeout` | | Most seconds one request may take, retries included. |
| `--backoff` | | Back-off factor between retries: the wait is this times 2 to the attempt number (default 0.5 seconds). |
| `--max-redirects` | | Most redirects to follow for one request (default 10). |
| `--retries` | | Extra attempts after a failure. |
| `--backoff` | | Back-off factor between retries: the wait is this times 2 to the attempt number (default 0.5 seconds). |
| `--max-redirects` | | Most redirects to follow for one request (default 10). |
| `--credential-host` | | Also send headers like `Authorization` and your cookies to this host (repeatable). By default they go only to the host of the URL. |

See [Settings](settings.md) for sizes (`4M`), `@file` values and `RAYOHX_` environment variables.

### Display

| Option | Description |
|---|---|
| `--json` | Print the result as JSON on stdout, for other programs. |

## JSON output

`--json` replaces the tables with one JSON document. For a master playlist:

```json
{
  "type": "master",
  "url": "https://media.example.com/vod/title/master.m3u8",
  "variants": [
    {
      "index": 1,
      "name": null,
      "resolution": "1920x1080",
      "bandwidth": 4500000,
      "average_bandwidth": null,
      "frame_rate": null,
      "codecs": ["avc1.640028", "mp4a.40.2"],
      "video_range": null,
      "audio_group": "aud",
      "subtitle_group": "subs",
      "url": "https://media.example.com/vod/title/video/1080.m3u8"
    }
  ],
  "audio_tracks": [
    {
      "group": "aud",
      "name": "English",
      "language": "en",
      "default": true,
      "autoselect": true,
      "forced": false,
      "separate": true,
      "channels": "2",
      "url": "https://media.example.com/vod/title/audio/en.m3u8"
    }
  ],
  "subtitle_tracks": [],
  "video_tracks": [],
  "selection": {
    "variant": 1,
    "audio": ["Français"],
    "subtitles": [],
    "notes": []
  }
}
```

(Shortened: a real document lists every variant and track.) `selection.variant` is the `index` of
the chosen stream, and `selection.notes` holds the plain-words explanations of wishes that could not
be met.

For a media playlist the fields are `type` (`"media"`), `url`, `segments`, `duration`,
`target_duration`, `container`, `complete`, `media_sequence`, `encryption` (a list of methods),
`initialization_section`, `byte_ranges` and `discontinuities`.

The same document is returned by [`rayohx.playlist_to_dict`](https://github.com/coldsofttech/RayoHX/blob/main/packages/core/docs/guides/python/inspecting.md), so a Python
program and a shell script see the same thing.

## Errors

A web address that is not found, a playlist that cannot be read and other expected failures exit
with code `1` and print `Error: <message>` with a hint on stderr; nothing is written to stdout. A
bad option or setting exits with `2`. See [Exit codes and errors](exit-codes.md).
