# Testing

How the tests are organized, and how the shared `rayohx-pytest` plugin supplies servers, fixtures and test media.

## Where tests live

```text
tests/
  conftest.py      fixtures shared by all tests: a clean environment, restored logging,
                   a CliRunner, a fake download
  unit/            fast tests, run by default; commands through CliRunner and the pure modules
  integration/     slower end-to-end tests over real sockets or real processes
  helpers/         helpers used only by this repository
  frozen.py        finds the executables PyInstaller built
```

Anything in `integration/` is marked `integration` automatically and is skipped by a normal `pytest` run. Run it with `-m integration`.

The pytest settings in `pyproject.toml` require 80% coverage of `rayohx_cli`, so a run of a few tests fails on coverage unless you pass `--no-cov`.

## Running

Run only what your change touches:

```bash
uv run pytest tests/unit --no-cov                              # unit tests
uv run pytest tests/unit/cli/test_info.py --no-cov             # one file
uv run pytest -m integration tests --no-cov                    # real process and local servers
uv run pytest                                                  # everything not marked integration, with coverage
```

The integration tests start local servers on free ports and run the installed command as a real process. They need no network access and write only to pytest's temporary folders. CI runs the unit tests and the integration tests on Python 3.11 to 3.15 on Linux, and on 3.11 on Windows and macOS.

## The `rayohx-pytest` plugin

The test support shared by the RayoHX repositories lives in the `rayohx-pytest` package, in the [RayoHX](https://github.com/coldsofttech/RayoHX) repository (`packages/pytest`). It is not published to PyPI. `pyproject.toml` takes it from git as a development dependency (`[tool.uv.sources]`), so `uv sync` installs it and pytest loads it automatically.

### Fixtures

| Fixture | What it gives you |
| --- | --- |
| `local_server` | A factory that starts a real HTTP server on `127.0.0.1` and stops it after the test. Call it with routes, for example `local_server({"/index.m3u8": lambda _s: Reply(body=playlist)})`, and use `server.url`. |
| `tls_certificate` | A self-signed certificate and key, valid for `127.0.0.1`, for HTTPS tests (`local_server(routes, tls=tls_certificate)`). |
| `ts_payload` | Builds MPEG-TS packets that pass the engine's sync-byte check. |

The classes and helpers behind them are importable for types and for module-level code:

```python
from rayohx_pytest.plugin import ServerFactory
from rayohx_pytest.servers import Reply, Seen
from rayohx_pytest.site import Site, hls_site
```

| Module | What it gives you |
| --- | --- |
| `servers` | `LocalServer`, a real threaded HTTP/1.1 server with routes by path, per-reply delays and a log of every request, plus `Reply`, `Seen` and `Route`. |
| `site` | `Site`, an in-memory httpx mock handler that serves bytes by path and logs requests, and `hls_site` and `single_file_site`, which build HLS streams from the shared media. |
| `fixtures` | `fixture_path`, `fixture_text` and `fixture_bytes` for the shared files. |
| `hls` | A small VOD stream on top of `LocalServer`: `vod_routes`, `expected` and `segment_index`. |

### Shared test data

The plugin ships the files that several repositories read, so they are written once:

- `hls/` holds playlists, such as `ladder.m3u8` (a four-variant master playlist) and `single_segment.m3u8`.
- `media/` holds small real MPEG-TS and fragmented MP4 files and two HLS sets, made by FFmpeg.

Read them with `rayohx_pytest.fixtures` or `rayohx_pytest.site`, not with a path built from `__file__`.

### Changing the plugin

The plugin is not changed here. Change it in the RayoHX repository, tag it, and update the `tag` (or `branch`) of `rayohx-pytest` in `[tool.uv.sources]` and in `[tool.cibuildwheel] test-requires`, then run `uv lock`.

## Helpers kept here

`tests/helpers/` holds code that only the command line tests use:

| Module | What it is |
| --- | --- |
| `cli.py` | Addresses, the type of the `serve` fixture and small helpers for running the app |
| `console.py` | A Rich console that writes into memory, for tests that look at what is printed |
| `params.py` | Helpers for testing the option definitions in `rayohx_cli.params` |
| `progress.py` | Events, progress snapshots and consoles for testing how a download is shown |

Put a helper in the plugin, not here, when another repository needs it too.

## The frozen tests

`tests/integration/test_frozen_cli.py` starts the built PyInstaller program and checks it answers. They need a PyInstaller build first, which is made by the installer scripts in the [RayoHX-Installer](https://github.com/coldsofttech/RayoHX-Installer) repository. Without a build they are skipped. Set `RAYOHX_INSTALLER_DIR` to the folder that holds the build; by default it looks in `build/installer` at the repository root, with the program in a `rayohx` folder.

## The compiled build

The [smoke test](../scripts/smoke/README.md) builds the compiled wheel and runs `rayohx info` from a fresh environment. It is a manual check that needs a C compiler and network access, separate from the pytest suites.

## Writing tests

- **Unit tests** call the app with the `runner` fixture and check the exit code, stdout and stderr. Test the pure modules (`values`, `format`, `settings`) directly.
- Use `local_server` and the fixtures from the plugin instead of starting servers by hand.
- The conftest removes `RAYOHX_*` variables and settings files from the machine, so a test never depends on the developer's own set-up.
- Never put real tokens or cookies in a test; use obvious fake values such as `hunter2-very-secret`.
