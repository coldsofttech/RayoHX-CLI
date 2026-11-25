# Global options

Global options apply to every command. They go **before** the command name:

```bash
rayohx --quiet download URL
rayohx --verbose info URL
```

[Back to the command line guide](../cli.md)

| Option | Short | Environment variable | Description |
|---|---|---|---|
| `--help` | | | Show help for the tool, or for a command when it follows the command name. |
| `--version` | `-V` | | Show the version and exit. |
| `--verbose` | `-v` | `RAYOHX_VERBOSE` | Show extra detail on stderr, and a traceback for unexpected errors. |
| `--quiet` | `-q` | `RAYOHX_QUIET` | Show only errors and the result. Cannot be combined with `--verbose`. |
| `--no-color` | | `RAYOHX_NO_COLOR` | Disable colored output. The standard `NO_COLOR` variable has the same effect. |
| `--log-file` | | `RAYOHX_LOG_FILE` | Also write a detailed log to this file. Secrets are removed. |
| `--config` | | `RAYOHX_CONFIG` | Use this settings file. See [Settings](settings.md). |
| `--no-config` | | | Ignore settings files. Cannot be combined with `--config`. |
| `--install-completion` | | | Install shell completion for the current shell. |
| `--show-completion` | | | Print the completion script instead of installing it. |

## Version and help

```bash
rayohx --version          # rayohx 0.1.0
rayohx --help             # the commands
rayohx download --help    # one command's options, grouped by purpose
```

`--version` prints `rayohx <version>` on stdout and exits with `0`. Running `rayohx` with nothing
after it shows the help.

## Verbose and quiet

- `--verbose` shows extra detail on stderr: the playlists loaded, the file being downloaded, and
  a traceback if something unexpected goes wrong. Local variables are never shown, because they can
  contain secrets.
- `--quiet` shows only errors and the result, which makes it suited to scripts. Progress is not
  shown.
- Asking for both is a usage error (exit code `2`).

## Log file

`--log-file` writes a detailed log of what the library did, in addition to what appears on the
screen:

```bash
rayohx --log-file rayohx.log download URL
```

Tokens, signatures, passwords, cookies and proxy credentials are removed from the log, so it is
safe to attach to a bug report. See also [Logging](https://github.com/coldsofttech/RayoHX/blob/main/packages/core/docs/guides/python/logging.md) for what the library logs.

## Shell completion

```bash
rayohx --install-completion      # for the shell you are using
rayohx --show-completion         # print the script to put somewhere yourself
```

Restart your shell afterwards. Completion knows the commands and their options.
