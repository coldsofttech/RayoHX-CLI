"""The installed command, started as a real process and talking to a real local server."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import rayohx
from rayohx_pytest.media import ts_payload
from rayohx_pytest.plugin import ServerFactory
from rayohx_pytest.servers import Reply, Seen
from rayohx_pytest.site import fixture

pytestmark = pytest.mark.integration

COUNT = 6
SECRET = "hunter2-very-secret"


def _run(*command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)


def _script() -> str:
    return str(
        Path(sys.executable).parent / ("rayohx.exe" if sys.platform == "win32" else "rayohx")
    )


def _routes() -> dict[str, object]:
    lines = ["#EXTM3U", "#EXT-X-TARGETDURATION:4", "#EXT-X-PLAYLIST-TYPE:VOD"]
    routes: dict[str, object] = {}
    for index in range(COUNT):
        lines += ["#EXTINF:4.0,", f"seg{index}.ts"]

        def serve(_seen: Seen, index: int = index) -> Reply:
            return Reply(body=ts_payload(index))

        routes[f"/seg{index}.ts"] = serve
    body = ("\n".join([*lines, "#EXT-X-ENDLIST"]) + "\n").encode()
    routes["/index.m3u8"] = lambda _s: Reply(body=body)
    return routes


def test_module_entrypoint() -> None:
    result = _run(sys.executable, "-m", "rayohx_cli", "--version")
    assert result.returncode == 0
    assert rayohx.__version__ in result.stdout


def test_console_script() -> None:
    result = _run(_script(), "--version")
    assert result.returncode == 0
    assert rayohx.__version__ in result.stdout


def test_usage_errors_exit_with_2() -> None:
    result = _run(sys.executable, "-m", "rayohx_cli", "download")
    assert result.returncode == 2
    assert result.stdout == ""


def test_errors_go_to_stderr(local_server: ServerFactory) -> None:
    server = local_server({})
    result = _run(_script(), "info", f"{server.url}/missing.m3u8")
    assert result.returncode == 1
    assert "was not found" in result.stderr
    assert result.stdout == ""


def test_info_and_download_against_a_server(tmp_path: Path, local_server: ServerFactory) -> None:
    server = local_server(_routes())  # type: ignore[arg-type]
    url = f"{server.url}/index.m3u8"
    info = _run(_script(), "info", url, "--json")
    out = tmp_path / "clip.ts"
    done = _run(_script(), "download", url, "-o", str(out), "--format", "ts", "--json")
    assert info.returncode == 0, info.stderr
    assert json.loads(info.stdout)["segments"] == COUNT
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result["success"] is True
    assert out.read_bytes() == b"".join(ts_payload(i) for i in range(COUNT))


def test_the_command_never_prints_secrets(tmp_path: Path, local_server: ServerFactory) -> None:
    secret_headers = tmp_path / "headers.txt"
    secret_headers.write_text(f"Authorization: Bearer {SECRET}\n", encoding="utf-8")
    log = tmp_path / "run.log"
    out = tmp_path / "clip.ts"
    seen: list[Seen] = []

    def index(request: Seen) -> Reply:
        seen.append(request)
        return Reply(body=fixture("single_segment.m3u8"))

    routes = {"/index.m3u8": index, "/s0.ts": lambda _s: Reply(body=ts_payload(0))}
    server = local_server(routes)
    command = [
        sys.executable, "-m", "rayohx_cli", "--verbose", "--log-file", str(log),
        "download", f"{server.url}/index.m3u8?token={SECRET}", "-o", str(out),
        "--format", "ts", "-H", f"@{secret_headers}", "--cookie", f"sid={SECRET}",
    ]  # fmt: skip
    done = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120)
    assert done.returncode == 0, done.stderr
    assert seen[0].headers["authorization"] == f"Bearer {SECRET}"  # the server did get it
    assert SECRET not in done.stdout
    assert SECRET not in done.stderr
    assert SECRET not in log.read_text(encoding="utf-8")
    assert not list(tmp_path.glob("*.part"))
