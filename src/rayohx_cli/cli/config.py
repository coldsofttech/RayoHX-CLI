"""The ``config`` command: show which settings are in effect."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from rayohx_cli import output
from rayohx_cli.cli.common import usage_error
from rayohx_cli.cli.root import app

if TYPE_CHECKING:
    from collections.abc import Mapping

_SECRET_WORDS = ("PASSWORD", "PROXY", "COOKIE", "HEADER", "KEY", "TOKEN", "SECRET")
_HIDDEN = "***"


def environment_settings(environ: Mapping[str, str]) -> dict[str, str]:
    """The ``RAYOHX_*`` variables that are set, with anything that may be secret hidden."""
    return {
        name: _HIDDEN if any(word in name for word in _SECRET_WORDS) else value
        for name, value in sorted(environ.items())
        if name.startswith("RAYOHX_")
    }


@app.command()
def config(
    ctx: typer.Context,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print the result as JSON on stdout.")
    ] = False,
) -> None:
    """Show the settings file in use and the RAYOHX_ environment variables that are set.

    Values that may be secret (proxies, passwords, cookies, headers, keys) are hidden.
    """
    import os

    from rayohx.errors import ConfigurationError

    from rayohx_cli.settings import FILE_NAME, find_config, load_config, user_config_file

    parent = ctx.parent.params if ctx.parent else {}
    given = parent.get("config")
    explicit, ignored = (Path(given) if given else None), bool(parent.get("no_config"))
    path = None
    values: dict[str, object] = {}
    if not ignored:
        try:
            path = find_config(explicit)
            if path is not None:
                commands = getattr(typer.main.get_command(app), "commands", {})
                known = {o.name for c in commands.values() for o in c.params if o.name}
                values = load_config(path, known)
        except ConfigurationError as exc:
            usage_error(exc)
    hidden = {
        key: _HIDDEN if any(word in key.upper() for word in _SECRET_WORDS) else value
        for key, value in values.items()
    }
    environment = environment_settings(os.environ)
    document: dict[str, object] = {
        "settings_file": str(path) if path else None,
        "searched": [FILE_NAME, str(user_config_file())],
        "ignored": ignored,
        "settings": hidden,
        "environment": environment,
    }
    if json_output:
        output.print_json(document)
        return
    output.data(f"settings file: {document['settings_file'] or 'none'}")
    if not path and not ignored:
        output.message(f"Looked for ./{FILE_NAME} and {user_config_file()}")
    for key, value in hidden.items():
        output.data(f"  {key} = {value!r}")
    for name, value in environment.items():
        output.data(f"{name}={value}")
