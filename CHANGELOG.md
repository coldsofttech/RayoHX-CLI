# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Releases ship as compiled wheels (a single `.pyd` on Windows, `.so` elsewhere) with type stubs and no source files, one per platform and Python version.
- CLI tests now use the test fixtures and helpers shared across the project.

## [0.1.0] - 2026-11-21

### Added

- `rayohx clean` removes leftover working folders, and `rayohx config` shows the settings in effect.
- `--playlist-file` on `download` and `info` reads a playlist you already have from a file instead of fetching it, and `--base-url` sets the address its relative links resolve against. A local playlist file can also be given in place of the address.
- `--events` writes every download event as one JSON line on stderr, for other programs.
- Tune retries and redirects (`--backoff`, `--max-redirects`), sign in to a proxy (`--proxy-username`, `--proxy-password`) and read cookies from a browser's `cookies.txt` (`--cookie-file`).
- `--directory` picks the folder to save into, `--reserve-space` keeps some disk space free, and `--no-keep-state` clears what a resume needs after a failure.
- Press P (or the space bar) during a download to pause it, and again to resume. On Linux and macOS, `kill -USR1` does the same.
- `rayohx download` accepts several addresses, or a list in a file with `--input-file` (`-` reads standard input). `--output` then names a folder, and `--stop-on-error` stops at the first failure.
- `--allow-file-keys` lets a stream's local key files be read; streams with keys inside the playlist now download.
- Prefer a video codec (`--codec`) or dynamic range (`--video-range`), and cap the frame rate (`--max-frame-rate`), when choosing a stream.
- SOCKS5 proxies, `--env-proxy` to use the proxy environment variables, and client certificates for mutual TLS (`--client-cert`, `--client-key`, `--client-key-password`).
- The `rayohx` command: `rayohx info URL` shows a stream's qualities and tracks and what a download would pick, and `rayohx download URL` saves it as one file.
- Choose what to download: a quality (`--quality`, `--max-resolution`, `--max-bitrate`), a stream exactly (`--variant N` from `rayohx info`, counting from 1, `--resolution 1280x720`, `--bandwidth`, `--variant-name`), and audio and subtitle tracks (`--audio`, `--subtitles`, `--video-only`).
- Choose how to save: `--format` (`auto`, `ts`, `mp4` or one file per segment), `--overwrite` and `--validate`. FFmpeg is optional (`--ffmpeg`, `--remux-backend`).
- Network options for protected streams: headers, cookies, user agent, referer, origin, a proxy, TLS settings (`--insecure`, `--ca-bundle`), timeouts, retries and a rate limit. Secret values can be read from a file with `@file`, and credentials go only to the stream's own host and the hosts you list.
- Interrupted downloads continue where they stopped when you run the same command again, and Ctrl-C stops one cleanly.
- A progress bar (or plain lines), `--json` output for other programs, `--quiet`, `--verbose` and `--no-color`, and `--log-file` with secrets removed.
- Defaults from a `rayohx.toml` settings file (or `--config`) and `RAYOHX_` environment variables, with exit codes 0, 1, 2 and 130.
- `--no-space-check` turns off the disk-space check, for drives that report free space wrongly.
- A Windows setup (with an optional `PATH` entry) and a portable zip, and Linux `.deb` and `.rpm` packages for x86_64 and ARM64 with an icon.
- The command is also available as the `rayohx-cli` package.
