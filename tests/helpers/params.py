"""Helpers for testing the option definitions in ``rayohx_cli.params``.

An option is a ``typing.Annotated`` alias that carries a Typer declaration. ``declared`` reads that
declaration, and ``parse`` runs the option through a throwaway Typer command, so a test sees what
the command line would hand to a real command.
"""

from dataclasses import dataclass
from typing import Any, NamedTuple, get_args

import typer
from typer.models import ArgumentInfo, OptionInfo
from typer.testing import CliRunner


class Declared(NamedTuple):
    """What an option is expected to declare."""

    name: str
    annotated: Any
    flags: tuple[str, ...]
    envvar: str | None


@dataclass
class Parsed:
    """What a command received for the option, and how the run ended."""

    exit_code: int
    value: Any
    output: str


def declaration(annotated: Any) -> OptionInfo | ArgumentInfo:
    """The Typer option or argument an annotated type carries."""
    info = get_args(annotated)[1]
    assert isinstance(info, OptionInfo | ArgumentInfo)
    return info


def option(annotated: Any) -> OptionInfo:
    """The Typer option an annotated type carries."""
    info = declaration(annotated)
    assert isinstance(info, OptionInfo)
    return info


def flags(info: OptionInfo) -> tuple[str, ...]:
    """The option's flags. Typer keeps the first one in ``default`` when the option is annotated."""
    first = (info.default,) if isinstance(info.default, str) else ()
    return (*first, *(info.param_decls or ()))


def check_declaration(case: Declared, panel: str) -> None:
    """The option has the expected flags and environment variable, and is in the right panel."""
    info = option(case.annotated)
    assert flags(info) == case.flags
    assert info.envvar == case.envvar
    assert info.rich_help_panel == panel
    assert info.help


def parse(
    runner: CliRunner,
    annotated: Any,
    default: Any,
    arguments: list[str],
    env: dict[str, str] | None = None,
) -> Parsed:
    """Run ``arguments`` through a command that takes just this option."""
    seen: list[Any] = []
    app = typer.Typer()

    @app.command()
    def command(value: annotated = default) -> None:
        seen.append(value)

    result = runner.invoke(app, arguments, env=env)
    return Parsed(result.exit_code, seen[0] if seen else None, result.output)
