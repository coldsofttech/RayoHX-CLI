# Exit codes and errors

Every command ends with an exit code a script can test, and prints a short message when something
goes wrong.

[Back to the command line guide](../cli.md)

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | The operation failed: a network error, a missing playlist, an existing output file, an unsupported stream, and so on. |
| `2` | Invalid usage or settings, such as an unknown option, a bad value, a wrong key in the settings file, or `--verbose` together with `--quiet`. |
| `130` | Cancelled. The first Ctrl+C stops the download cleanly; a second one quits at once. |

```bash
if rayohx download "$URL" --quiet; then
    echo "saved"
else
    case $? in
        1) echo "the download failed" ;;
        2) echo "check the command" ;;
        130) echo "stopped" ;;
    esac
fi
```

## What an error looks like

Expected failures print `Error: <message>` and, where it helps, a hint on the next line, to stderr. Nothing is
written to stdout, so a script that reads stdout never mistakes an error for a result.

```text
Error: The playlist https://cdn.example.com/missing.m3u8 was not found.
Check the address, or whether the link has expired.
```

With `--json`, stdout still holds a document that describes the failure (`success` is `false` and
`error` says why), so a program always has something to read.

Messages never contain tokens, signatures, cookies or proxy passwords. Addresses are shown with
those parts removed.

## Unexpected errors

A failure RayoHX did not expect (a bug) prints a one-line message to stderr and exits with `1`:

```text
Error: RuntimeError: boom
Run with --verbose for details.
```

With `--verbose` it also shows a traceback. Local variables are never shown, because they can contain
secrets. If you report a bug, include the traceback and, if you can, a `--log-file`.

## Stopping with Ctrl+C

Press P to pause and resume a download first if you only want to wait. Ctrl+C also stops a paused
download.

The first Ctrl+C asks the download to stop cleanly:

```text
Stopping... press Ctrl-C again to quit at once.
Cancelled.
```

It keeps what a resume needs and exits with `130`. Run the same command again to continue. A second
Ctrl+C quits at once; the working files stay on disk, so the next run can still resume (a half
written output file is never left in place of the real one).

## Where the errors come from

The command line shows the library's own errors. Each one has a message and an optional hint; see
the [Errors](https://github.com/coldsofttech/RayoHX/blob/main/packages/core/docs/guides/python/errors.md) page for the full list and what each means.
