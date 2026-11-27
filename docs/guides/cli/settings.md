# Settings

Every option has a default that you can change in two ways: with environment variables, or in a
settings file. That way the options you always use do not have to be typed every time.

[Back to the command line guide](../cli.md)

## Precedence

From highest to lowest:

1. The command line.
2. An environment variable: `RAYOHX_` plus the option name in capitals, for example
   `RAYOHX_QUALITY` or `RAYOHX_CONCURRENCY`.
3. The settings file.
4. The built-in default.

So `rayohx download URL --quality 480p` always wins, whatever the other layers say.

## Environment variables

Every option that takes a single value has a variable named after it:

```bash
export RAYOHX_QUALITY=720p
export RAYOHX_CONCURRENCY=8
export RAYOHX_PROXY=http://user:pass@proxy.example.com:3128
rayohx download URL
```

The variable for each option is shown in `rayohx download --help` as `[env var: ...]`. The
repeatable options (`--header`, `--cookie`, `--audio`, `--subtitles` and so on) are not read from
the environment; put them in a [settings file](#the-settings-file) or pass them on the command line.

Environment variables are the safer place for secrets such as a proxy password: other users of the
machine can see your command line, but not your environment.

## The settings file

The settings file is [TOML](https://toml.io/). Keys are option names without the leading `--`
(dashes or underscores both work):

```toml
# rayohx.toml
quality = "720p"
concurrency = 8
audio = ["en"]
header = ["Accept-Language: en"]
retries = 5
```

### Where it is read from

The first of these that exists:

1. The file named with `--config` (or `RAYOHX_CONFIG`). If you name a file that does not exist, that
   is an error.
2. `rayohx.toml` in the current folder.
3. `rayohx/config.toml` in your user configuration folder:
   - Windows: `%APPDATA%\rayohx\config.toml`
   - Linux and macOS: `$XDG_CONFIG_HOME/rayohx/config.toml`, or `~/.config/rayohx/config.toml`

`--no-config` ignores all of them.

### What can be in it

Any option of `info` and `download` except `url`, `output`, `help` and `json`, which make no sense
as defaults. A key applies to every command that has that option, so `quality` is used by both
`info` and `download`.

A key that is not an option is an error with a suggestion (`quaity` gives `Did you mean
'quality'?`), so a typo never silently does nothing. A value of the wrong type or outside its range
is a usage error (exit code `2`).

Do not put secrets in a settings file you share. Use `@file` references or environment variables.

## Sizes, bitrates and `@file`

- **Sizes** accept `K`, `M`, `G` and `T`, and are binary: `64M` is 64 MiB. This applies to
  `--buffer-size`, `--max-temp-size`, `--reserve-space` and `--rate-limit` (bytes per second).
- **Bitrates** (`--max-bitrate`) are decimal: `4M` is 4,000,000 bit/s.
- **`@file`**: `--header`, `--cookie` and the other repeatable options accept `@file` to read their
  values from a file, one per line (blank lines and lines starting with `#` are skipped). That keeps secrets out of your shell history and out of the
  process list.

```bash
printf 'Authorization: Bearer abc123\nX-Client: rayohx\n' > headers.txt
rayohx download URL --header @headers.txt
```

## Examples

A settings file for a home server that needs a header and a slower pace:

```toml
quality = "1080p"
concurrency = 2
rate_limit = "4M"
user_agent = "Mozilla/5.0"
header = ["Accept-Language: en"]
audio = ["en"]
subtitles = ["en"]
```

Try something different once, without touching the file:

```bash
rayohx download URL --quality 480p
```

Use a project-specific file:

```bash
rayohx --config ./work.toml download URL
```
