# config

`rayohx config` shows which settings are in effect, to answer "why did it use that value?".

[Back to the command line guide](../cli.md)

```bash
rayohx config
rayohx --config ./work.toml config --json
```

It prints the [settings file](settings.md#the-settings-file) that would be used (or `none` and where
it looked), the values in it, and every `RAYOHX_` environment variable that is set. `--no-config`
makes it report that settings files are ignored. Values that may be secret (proxies, passwords,
cookies, headers, keys) are shown as `***`.

`--json` prints one document with `settings_file`, `searched`, `ignored`, `settings` and
`environment`.
