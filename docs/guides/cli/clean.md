# clean

`rayohx clean` removes the working folders that interrupted downloads leave behind.

[Back to the command line guide](../cli.md)

```bash
rayohx clean [FOLDER]... [OPTIONS]
```

An interrupted or failed download keeps a hidden `.rayohx-<id>` folder beside its output (or, with
`--workspace`, a folder named by a short id inside that folder) so that running the same command
again can resume. If you will not resume, `clean` frees the space.

```bash
rayohx clean                      # look in the current folder
rayohx clean ~/Videos --dry-run   # only list what would go
rayohx clean ~/Videos --older-than 7 --yes
```

- Give the folder you saved to (or the one you passed to `--workspace`). The default is the current
  folder. Only folders directly inside it are looked at.
- Folders used by a running download are never removed.
- Removing a folder means that download starts again from the beginning. The output file itself is
  never touched.
- The removed folders are printed on stdout, one per line; the sizes and a summary go to stderr.

| Option | Short | Description |
|---|---|---|
| `--older-than` | | Only folders not used for this many days. |
| `--dry-run` | | Only list what would be removed. |
| `--yes` | `-y` | Do not ask before removing. |

Without `--yes` you are asked to confirm. If you decline, the exit code is `1`.
