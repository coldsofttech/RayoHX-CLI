# download

`rayohx download` takes a web address to a finished file. It picks the stream you asked for,
downloads the segments in parallel, checks every one, and puts the finished file in place.

[Back to the command line guide](../cli.md)

```bash
rayohx download [URL]... [OPTIONS]
```

```bash
rayohx download https://cdn.example.com/vod/master.m3u8 -o movie.mp4
rayohx download https://cdn.example.com/vod/master.m3u8 --quality 720p -a en -s en
file=$(rayohx download https://cdn.example.com/vod/master.m3u8 --quiet)
rayohx download URL1 URL2 -o videos
rayohx download --input-file urls.txt -o videos
```

It does the same work as [`rayohx.download`](https://github.com/coldsofttech/RayoHX/blob/main/docs/guides/python/downloading.md) and
[`Downloader`](https://github.com/coldsofttech/RayoHX/blob/main/docs/guides/python/downloading.md#downloader), and every option maps to a field of
[`DownloadConfig`](https://github.com/coldsofttech/RayoHX/blob/main/docs/guides/python/settings.md).

Put the web address in quotes if it contains `&` or `?`, so your shell does not cut it short.

## Several addresses

Give more than one address, or a list with `--input-file` (one address per line; empty lines and
lines starting with `#` are skipped; `-` reads standard input), and they are downloaded one after
another. The two can be combined.

- `--output` names a **folder**, created if needed. Files are named after the addresses, and
  repeated names get `-2`, `-3` and so on.
- Every address and setting is checked before anything is downloaded.
- A failure does not stop the others unless you pass `--stop-on-error`; the exit code is that of
  the first failure. Ctrl-C always stops the whole list (exit code 130).
- Each saved path is printed on stdout. With `--json`, stdout holds one JSON array with a document
  per download.

## A playlist you already have

`--playlist-file PATH` reads the playlist from a file instead of fetching it. Give the address it
came from as well: relative addresses inside the playlist (segments, keys, tracks) are resolved
against it, and the playlist itself is never requested. It works with one address, not with
several or `--input-file`.

```bash
rayohx download https://cdn.example.com/vod/master.m3u8 --playlist-file master.m3u8
```

You can also give the file in place of the address. Use `--base-url` to say where its relative
addresses resolve; without it, the playlist's addresses must all be absolute.

```bash
rayohx download master.m3u8 --base-url https://cdn.example.com/vod/
```

It does the same work as `Downloader(playlist_text=...)` in the [Python guide](https://github.com/coldsofttech/RayoHX/blob/main/docs/guides/python/downloading.md#downloader).

## What it prints

- On **stdout**: the path of the saved file, and nothing else. With `--json`, one JSON document
  instead (see [JSON output](#json-output)).
- On **stderr**: the chosen stream, notes about wishes that could not be met, progress, and a
  closing line such as `Saved movie.mp4 (812 MiB) in 2m 14s`.

`--quiet` shows only errors and the result. `--verbose` adds detail.

## Output files

An existing output file is never replaced unless you pass `--overwrite`.

- **Where it goes.** `--output` / `-o` names the file. A name without an extension gets the right
  one. Without `-o` the file is named after the address and saved in the current folder.
- **Which container.** `--format auto` (the default) saves MPEG-TS streams as `.ts` and fragmented
  MP4 streams as `.mp4`. A name that does not match what is inside is refused with an explanation,
  never quietly mislabelled. An MPEG-TS stream can also be saved as `.mp4` with `--format mp4`.
- **Separate audio.** A stream that keeps its audio in a separate track is joined into one `.mp4`
  automatically, with the language set. Choose the tracks with `--audio`, or leave them out with
  `--video-only`.
- **Subtitles.** `-s en` saves `movie.en.vtt` beside the video, lined up with it.
- **Segments.** `--format segments` saves one file per segment in a folder instead of one file.
- **No FFmpeg needed.** Re-wrapping into MP4 is done by RayoHX itself for H.264 and HEVC video with
  AAC, AC-3, E-AC-3 and MP3 audio, and nothing is converted or re-encoded. For anything else (MPEG-2
  video, for example) an [FFmpeg](https://ffmpeg.org/) you have installed is used if there is one.
  FFmpeg is optional and is never installed or shipped by RayoHX.
- **Checked.** Every segment and the finished file are checked, so an error page, a cut-off file or
  a wrong key is caught instead of producing a corrupt file. `--no-validate` turns the final check
  off.
- **Not supported.** Encrypted streams (plain AES-128) work. Protected (DRM) streams and live
  streams are refused with an explanation.

## Pausing

On Linux and macOS, `kill -USR1 <pid>` pauses a running download (segments already in progress
finish) and a second `kill -USR1` continues it. Windows has no such signal.

Press P (or the space bar) to pause a download and again to resume it. Downloads already
running finish first, so the pause takes a moment to show. This works when you type into a
terminal; it is off when input is piped.

## Resuming

An interrupted or cancelled download continues where it stopped when you run the same command
again, and needs disk space for the video only, not twice that. Use `--no-resume` to start over.
Joining separate audio into the video is the one case that starts again.

Press Ctrl+C once to stop cleanly and keep what a resume needs. A second press quits at once. See
[Exit codes and errors](exit-codes.md#stopping-with-ctrlc).

## Progress

`--progress` chooses how progress is shown, always on stderr:

| Mode | What you see |
|---|---|
| `auto` | A live bar on a terminal; a line every 10 percent otherwise (the default) |
| `bar` | A live bar with size, speed and time left |
| `plain` | One line per milestone and step, good for logs |
| `none` | Nothing |

`--quiet` and `--json` show no progress.

`--events` replaces the display with one JSON line per download event on stderr, for other programs
to follow; stdout still holds only the result.

## Options

Options are grouped the same way in `rayohx download --help`.

### Output

| Option | Short | Description |
|---|---|---|
| `--output` | `-o` | Where to save. A name without an extension gets the right one. By default it is named after the address, in the current folder. With several addresses, a folder. |
| `--directory` | `-d` | The folder for a file that `--output` does not name, and for several addresses. Created if missing. |
| `--input-file` | | A file listing addresses, one per line (`-` for standard input). |
| `--base-url` | | The web address a local playlist's relative addresses resolve against. |
| `--stop-on-error` | | With several addresses, stop at the first failure. |
| `--format` | | `auto` (default), `ts`, `mp4`, or `segments` (one file per segment, in a folder). |
| `--overwrite` / `--no-overwrite` | | Replace an existing output file. Off by default. |
| `--validate` / `--no-validate` | | Check the finished file before putting it in place. On by default. |
| `--remux-backend` | | Who re-wraps streams into MP4: `auto` (built in, then FFmpeg), `native` or `ffmpeg`. |
| `--ffmpeg` | | The FFmpeg program to use, if it is not on the `PATH`. FFmpeg is optional. |

### Choosing what to download

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
| `--audio` | `-a` | Audio language to download (repeat for several), for example `en`. |
| `--audio-name` | | Download the audio track with this exact name (repeatable). |
| `--subtitles` | `-s` | Subtitle language to save beside the video (repeat for several). |
| `--subtitle-name` | | Save the subtitle track with this exact name (repeatable). |
| `--video-only` | | Download only the video, leaving out separate audio and subtitle tracks. |
| `--input-file` | `-i` | Also download the addresses listed in this file (see [Several addresses](#several-addresses)). |
| `--playlist-file` | | Read the playlist from this file instead of fetching it (see [A playlist you already have](#a-playlist-you-already-have)). |
| `--stop-on-error` | | With several addresses, stop at the first failure. |

If a wish cannot be met (no audio in the language you asked for), the closest track is used and a
note on stderr says why. Use [`rayohx info`](info.md) first to see what exists.

### Network

| Option | Short | Description |
|---|---|---|
| `--header` | `-H` | Send a header, as `Name: value` (repeatable). `@file` reads them from a file. |
| `--cookie` | | Send a cookie, as `name=value` (repeatable). `@file` reads them from a file. |
| `--cookie-file` | | Read cookies from a browser-exported `cookies.txt` (Netscape format). Domains are not checked. |
| `--user-agent` | | The `User-Agent` to send. |
| `--referer` | | The `Referer` to send. |
| `--origin` | | The `Origin` to send. |
| `--proxy` | | An `http://`, `https://`, `socks5://` or `socks5h://` proxy, for example `http://user:pass@host:3128`. Prefer the environment variable, since command lines can be seen by other users. |
| `--proxy-username` | | The proxy user name, if it is not in the `--proxy` address. Needs `--proxy`. |
| `--proxy-password` | | The proxy password. Prefer the environment variable `RAYOHX_PROXY_PASSWORD`. |
| `--env-proxy` / `--no-env-proxy` | off | Use `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY` when `--proxy` is not given. |
| `--insecure` | | Do not check TLS certificates. Only for servers you trust. |
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
| `--retries` | | Extra attempts after a failure (0 or more). |
| `--rate-limit` | | Most bytes per second to download in total, for example `2M`. |
| `--credential-host` | | Also send headers like `Authorization` and your cookies to this host (repeatable). By default they go only to the host of the URL, and redirects never carry them elsewhere. |

Requests retry with back-off, follow redirects, and support proxies, TLS settings, headers, cookies
and a speed limit.

### Download engine

| Option | Short | Description |
|---|---|---|
| `--concurrency` | `-j` | Segments to download at the same time, from 1 to 64 (default 4). |
| `--resume` / `--no-resume` | | Continue an interrupted download where it stopped. On by default. |
| `--allow-file-keys` / `--no-allow-file-keys` | | Let a playlist's `file:` key addresses read a key from this machine. Off by default; only for streams you trust. |
| `--storage` | | Where finished segments wait: `auto` (default), `direct`, `streaming`, `buffered`, `temporary`, `hybrid`. |
| `--workspace` | | A folder for working files (default: beside the output). |
| `--buffer-size` | | Memory for the segment buffer, for example `64M`. |
| `--max-temp-size` | | Most working disk space to use, for example `2G`. |
| `--allow-file-keys` / `--no-allow-file-keys` | | Let a playlist's `file:` key addresses read a key from this machine. Off by default; only for streams you trust. |
| `--reserve-space` | | Free disk space that must remain after the download, for example `1G` (default 256M; `0` for none). |
| `--keep-state` / `--no-keep-state` | | Keep what a resume needs after a failure or Ctrl-C (on by default). |
| `--space-check` / `--no-space-check` | | Check that the disk has room (on by default). Turn it off if the free space is reported wrongly, for example on some network drives. |

### Display

| Option | Description |
|---|---|
| `--json` | Print the result as JSON on stdout, for other programs. |
| `--events` | Write every download event as one JSON line on stderr, for other programs. Replaces the progress display. |
| `--progress` | How to show progress: `auto` (default), `bar`, `plain`, `none`. |

Sizes accept `K`, `M` and `G`. Sizes are binary (`4M` is 4 MiB); bitrates are decimal (`4M` is
4,000,000 bit/s). See [Settings](settings.md) for `@file` values and `RAYOHX_` environment
variables.

## JSON output

With `--json`, stdout holds one JSON document, also when the download fails or is cancelled:

```json
{
  "download_id": "7f3c9e2a",
  "state": "COMPLETED",
  "success": true,
  "cancelled": false,
  "url": "https://cdn.example.com/vod/master.m3u8",
  "elapsed_seconds": 134.2,
  "output": {
    "path": "movie.mp4",
    "size_bytes": 851443712,
    "container": "mp4"
  },
  "error": null,
  "progress": {
    "state": "COMPLETED",
    "downloaded_bytes": 851443712,
    "written_bytes": 851443712,
    "total_bytes": 851443712,
    "completed_segments": 412,
    "total_segments": 412,
    "fraction": 1.0,
    "speed": 6402113.0,
    "average_speed": 6344012.5,
    "eta_seconds": 0.0,
    "active_workers": 0,
    "peak_temporary_bytes": 0
  }
}
```

When it fails, `success` is `false`, `output` is `null` and `error` says why. The same document is
returned by [`rayohx.result_to_dict`](https://github.com/coldsofttech/RayoHX/blob/main/docs/guides/python/downloading.md), and the progress block by
`rayohx.progress_to_dict`.

## Examples

Download 720p with English audio and subtitles:

```bash
rayohx download "$URL" --quality 720p -a en -s en -o show.mp4
```

Several audio languages and a bitrate budget:

```bash
rayohx download "$URL" --max-bitrate 3M -a en -a de
```

Only the picture, as one `.ts` file:

```bash
rayohx download "$URL" --video-only --format ts -o clip.ts
```

A slower, gentler download behind a proxy, using the environment for the secret:

```bash
export RAYOHX_PROXY=http://user:pass@proxy.example.com:3128
rayohx download "$URL" --concurrency 2 --rate-limit 1M --retries 5
```

Replace an existing file, and write a log for a bug report:

```bash
rayohx --log-file rayohx.log download "$URL" -o movie.mp4 --overwrite
```
