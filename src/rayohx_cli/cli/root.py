"""The root command: the program's name, help, and the options every command takes."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from typer.core import TyperGroup

from rayohx_cli import output
from rayohx_cli.cli.common import loaded_commands, usage_error

if TYPE_CHECKING:
    from typer import _click as click

# Each command lives in its own module, which is imported only when the command is needed.
COMMAND_MODULES = {
    "clean": "rayohx_cli.cli.clean",
    "config": "rayohx_cli.cli.config",
    "download": "rayohx_cli.cli.download",
    "info": "rayohx_cli.cli.info",
}


class LazyGroup(TyperGroup):
    """A command group that imports a command's module the first time it is looked up."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(set(super().list_commands(ctx)) | set(COMMAND_MODULES))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        command = super().get_command(ctx, cmd_name)
        if command is None and cmd_name in COMMAND_MODULES:
            module = importlib.import_module(COMMAND_MODULES[cmd_name])
            command = typer.main.get_command(module.cli)
            command.name = cmd_name
            self.add_command(command)
        return command


app = typer.Typer(
    name="rayohx",
    cls=LazyGroup,
    help=(
        "Download HLS (.m3u8) streams: pick the quality, audio and subtitles, and save "
        "one file. Use [bold]rayohx info URL[/bold] to look first, "
        "[bold]rayohx download URL[/bold] to save."
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
    # run() reports errors briefly; Typer's own traceback would show local variables.
    pretty_exceptions_enable=False,
)


def _show_version(value: bool) -> None:
    if value:
        from rayohx import __version__

        output.console.print(f"rayohx {__version__}")
        raise typer.Exit


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_show_version,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", envvar="RAYOHX_VERBOSE", help="Show extra detail."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet", "-q", envvar="RAYOHX_QUIET", help="Show only errors (and the result)."
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", envvar="RAYOHX_NO_COLOR", help="Disable colored output."),
    ] = False,
    log_file: Annotated[
        Path | None,
        typer.Option(
            "--log-file",
            envvar="RAYOHX_LOG_FILE",
            help="Also write a detailed log to this file (secrets are removed).",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            envvar="RAYOHX_CONFIG",
            help="A settings file (TOML) with defaults for the options.",
        ),
    ] = None,
    no_config: Annotated[bool, typer.Option("--no-config", help="Ignore settings files.")] = False,
) -> None:
    """Options that apply to every command."""
    if verbose and quiet:
        raise typer.BadParameter("--verbose and --quiet cannot be used together.")
    if config is not None and no_config:
        raise typer.BadParameter("--config and --no-config cannot be used together.")
    output.configure(no_color=no_color, verbose=verbose, quiet=quiet)
    level = logging.DEBUG if verbose else logging.ERROR if quiet else logging.WARNING
    output.configure_logging(level, verbose=verbose, log_file=log_file)
    if no_config:
        return
    from rayohx.errors import ConfigurationError

    from rayohx_cli.settings import find_config, load_config

    try:
        path = find_config(config)
        if path is None:
            return
        commands = loaded_commands(ctx)
        known = {opt.name for command in commands.values() for opt in command.params if opt.name}
        loaded = load_config(path, known)
    except ConfigurationError as exc:
        usage_error(exc)
    ctx.default_map = {
        name: {k: v for k, v in loaded.items() if k in {o.name for o in command.params}}
        for name, command in commands.items()
    }
    logging.getLogger("rayohx.cli").debug("Using settings from %s", path)
