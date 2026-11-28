# RayoHX command line

[![CI](https://github.com/coldsofttech/RayoHX-CLI/actions/workflows/ci.yml/badge.svg)](https://github.com/coldsofttech/RayoHX-CLI/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/rayohx-cli)](https://pypi.org/project/rayohx-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/rayohx-cli)](https://pypi.org/project/rayohx-cli/)
[![Typer](https://img.shields.io/badge/Typer-CLI-black)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/output-Rich-blue)](https://github.com/Textualize/rich)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/github/license/coldsofttech/RayoHX-CLI)](LICENSE)

Download HLS streams from your terminal.

```sh
rayohx info https://cdn.example.com/vod/master.m3u8
rayohx download https://cdn.example.com/vod/master.m3u8 -o movie.mp4
```

## What is RayoHX?

RayoHX is a tool for saving HLS streams (`.m3u8` links) as ordinary video files. Many websites play
video as a stream made of many small pieces, which is awkward to save by hand. Give RayoHX the
stream's web address and it looks at what the stream offers, lets you choose the quality, audio and
subtitles you want, and puts everything together into a single file you can keep and play anywhere.

RayoHX comes in several forms that share the same engine: a Python library, this command line, a
Docker image and a desktop window for Windows. This repository is the **command line**: the
`rayohx` command, for use in a terminal, a script or a scheduled job.

## How it helps

- **See before you download**: check a stream's qualities, audio and subtitle tracks and encryption
  without downloading any video
- **Get exactly what you want**: pick the quality and the audio and subtitles you need, instead of
  taking whatever comes first
- **Finish what you started**: interrupted downloads continue where they stopped
- **Safe by default**: it never replaces an existing file unless you allow it, and refuses damaged
  or unsafe streams with a clear explanation instead of failing in a confusing way
- **Easy to script**: the saved file's path is the only thing printed on stdout, and `--json` and
  `--events` give output that other programs can read
- **Private**: tokens, cookies and proxy passwords are kept out of logs and error messages

## What you can do

- See a stream's qualities, audio and subtitle tracks and encryption before downloading anything
- Choose the quality, audio and subtitles, and download to a file or a folder of segments
- Download encrypted (AES-128) streams; protected (DRM) and live streams are refused with an
  explanation
- Join a separate audio track into one MP4, with nothing re-encoded
- Continue interrupted downloads where they stopped, and clean up what they leave behind
- Download several streams with one command, from addresses or a list file (`--input-file`)
- Use a playlist you already have, from a file, instead of fetching it (`--playlist-file`, `--base-url`)
- Use proxies, custom headers and cookies when a site needs them
- Follow a download from another program with `--events`
- Watch a progress bar, or get machine-readable output with `--json`
- Keep settings in a file or `RAYOHX_` environment variables
- Use `--verbose`, `--quiet`, `--no-color` and shell completion

## Install

Requires Python 3.11 or newer on Windows, Linux or macOS, where a ready-to-use compiled build is
installed for your platform. Install it in its own isolated environment:

```sh
uv tool install rayohx-cli
```

or with pipx:

```sh
pipx install rayohx-cli
```

You can also run it once without installing it:

```sh
uvx --from rayohx-cli rayohx --help
```

Check it works:

```sh
rayohx --version
```

No Python? Download the portable build for Windows (`.zip`) or Linux (`.tar.gz`) from the
[releases page](https://github.com/coldsofttech/RayoHX-CLI/releases), unpack it and run `rayohx`
from the unpacked folder (add the folder to your `PATH` to run it from anywhere).

Prefer a ready-made installer (Windows setup, Linux `.deb` and `.rpm`)? The newest ones are on the
[RayoHX-Installer releases page](https://github.com/coldsofttech/RayoHX-Installer/releases).

## Quick start

Look at a stream first, to see what it offers:

```sh
rayohx info https://cdn.example.com/vod/master.m3u8
```

Download it to a file:

```sh
rayohx download https://cdn.example.com/vod/master.m3u8 -o movie.mp4
```

Use the result in a script. The saved file's path is the only thing printed:

```sh
file=$(rayohx download https://cdn.example.com/vod/master.m3u8 --quiet)
```

Download several streams from a list file, or get the details as JSON:

```sh
rayohx download --input-file streams.txt
rayohx info https://cdn.example.com/vod/master.m3u8 --json
```

Remove the leftover folders of interrupted downloads, and see which settings are in effect:

```sh
rayohx clean
rayohx config
```

Run `rayohx --help`, or `rayohx download --help`, to see every option.

## Commands

| Command | What it does |
|---|---|
| `rayohx info` | Shows what a stream offers: qualities, audio, subtitles and encryption |
| `rayohx download` | Saves a stream, or several, to a file or a folder of segments |
| `rayohx clean` | Removes leftover working folders from interrupted downloads |
| `rayohx config` | Shows which settings file and `RAYOHX_` variables are in effect |

## Other ways to use RayoHX

| What it is | Where |
|---|---|
| Python library, to use RayoHX inside your own programs | [`rayohx`](https://pypi.org/project/rayohx/) |
| Docker image, the same command without installing Python | `ghcr.io/coldsofttech/rayohx` |
| Desktop window for Windows | The full setup on the [RayoHX-Installer releases page](https://github.com/coldsofttech/RayoHX-Installer/releases) |

## Learn more

- [Command line guide](docs/guides/cli.md): every option, settings, exit codes and examples
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Support](SUPPORT.md)
- [Report a problem](https://github.com/coldsofttech/RayoHX-CLI/issues)

## License

Apache-2.0. See [LICENSE](LICENSE).
