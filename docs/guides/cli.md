# Command line guide

`rayohx` downloads HLS streams (`.m3u8`) to a file from your terminal. It is a thin front end over the
Python package: the command line only reads your options and shows results, and all the work is done
by the `rayohx` library. Nothing it does is hidden from the [Python guide](https://github.com/coldsofttech/RayoHX/blob/main/docs/guides/python.md).

```bash
rayohx info https://cdn.example.com/vod/master.m3u8
rayohx download https://cdn.example.com/vod/master.m3u8 -o movie.mp4
```

`info` looks at the stream and tells you what it offers. `download` saves it. The path of the saved
file is the only thing printed on stdout, so it is easy to use in a script:

```bash
file=$(rayohx download https://cdn.example.com/vod/master.m3u8 --quiet)
```

> **What works today.** You can look at a stream without downloading it, choose the quality, audio and
> subtitles, and download MPEG-TS and fragmented MP4 streams (including AES-128 encrypted ones) to a
> file or a folder of segments. Streams with a separate audio track are joined into one MP4, and
> interrupted downloads continue where they stopped. Protected (DRM) and live streams are refused with
> an explanation.

## Contents

| Page | What it covers |
|---|---|
| [info](cli/info.md) | `rayohx info`: what a stream offers, the table and `--json` output, which tracks a download would pick |
| [download](cli/download.md) | `rayohx download`: every option, output files, progress, resume, examples |
| [clean](cli/clean.md) | `rayohx clean`: remove leftover working folders from interrupted downloads |
| [config](cli/config.md) | `rayohx config`: which settings file and `RAYOHX_` variables are in effect |
| [Global options](cli/global-options.md) | `--verbose`, `--quiet`, `--no-color`, `--log-file`, `--config`, shell completion |
| [Settings](cli/settings.md) | The settings file, `RAYOHX_` environment variables, `@file` values, precedence |
| [Exit codes and errors](cli/exit-codes.md) | What each exit code means, how errors look, stopping with Ctrl+C |

## Installation

`rayohx` needs Python 3.11 or newer. The recommended way to install a command line tool is in its own
isolated environment:

```bash
uv tool install rayohx-cli
```

or with pipx:

```bash
pipx install rayohx-cli
```

You can also run it once without installing it:

```bash
uvx --from rayohx-cli rayohx --help
```

Ready-made installers (Windows setup, Linux `.deb` and `.rpm` packages) are on the
[releases page](https://github.com/coldsofttech/RayoHX-CLI/releases). The package name is
`rayohx-cli`; the command is `rayohx`.

```bash
rayohx --version
```

FFmpeg is not needed. It is used only as an optional fallback for codecs the built-in remuxer cannot
copy (see [download](cli/download.md#output-files)).

## Commands at a glance

| Command | Purpose | Page |
|---|---|---|
| `rayohx info URL` | Show a stream's qualities, audio and subtitle tracks, and what a download would pick | [info](cli/info.md) |
| `rayohx download URL` | Download a stream to a file or a folder of segments | [download](cli/download.md) |
| `rayohx --version` | Show the version and exit | [Global options](cli/global-options.md) |
| `rayohx --help` | Show help for the tool; add a command name for that command's help | [Global options](cli/global-options.md) |

## Conventions

- **Results on stdout, messages on stderr.** The saved path, the tables and the JSON go to stdout so
  they can be piped. Progress, notes and errors go to stderr.
- **JSON for programs.** `--json` prints a single JSON document to stdout, also when a download
  fails, so a script can always read it.
- **Never replaces a file by accident.** An existing output file is kept unless you pass
  `--overwrite`.
- **Resumable.** Run the same download command again and it continues where it stopped.
- **Pausable.** Press P (or the space bar) during a download to pause it, and again to resume.
- **Secrets stay out.** Addresses are shown with tokens, signatures and passwords hidden, and the
  log file has them removed too. Use `@file` or environment variables for headers, cookies and
  proxies, not the command line, where other users of the machine can see them.
- **Color only when it helps.** Color is turned off when output is piped, when the standard
  `NO_COLOR` variable is set, or with `--no-color`.
- **Every option can be a default.** Any option that takes one value can also be set with a
  `RAYOHX_<NAME>` environment variable or in a settings file. See [Settings](cli/settings.md).
- **Clear exit codes.** `0` success, `1` the operation failed, `2` invalid usage or settings, `130`
  stopped with Ctrl+C. See [Exit codes and errors](cli/exit-codes.md).

## Examples

Look at a stream, limited to 720p, before deciding:

```bash
rayohx info https://cdn.example.com/vod/master.m3u8 --max-resolution 720p
```

Download 720p with English audio and English subtitles:

```bash
rayohx download https://cdn.example.com/vod/master.m3u8 --quality 720p -a en -s en -o show.mp4
```

Stay under a data budget, with German as a fallback audio language:

```bash
rayohx download https://cdn.example.com/vod/master.m3u8 --max-bitrate 3M -a en -a de
```

Use the result in a script, with progress hidden:

```bash
rayohx download "$URL" --json --progress none | jq -r '.output.path'
```

Download from a server that wants a token, without the token landing in your shell history:

```bash
echo "Authorization: Bearer abc123" > headers.txt
rayohx download "$URL" --header @headers.txt
```

Make 1080p the default for every download:

```bash
mkdir -p ~/.config/rayohx
echo 'quality = "1080p"' > ~/.config/rayohx/config.toml
```
