"""The ``clean`` command: remove working folders left behind by interrupted downloads."""

from pathlib import Path
from typing import Annotated

import typer

from rayohx_cli import format as fmt
from rayohx_cli import output
from rayohx_cli.cli.root import app


@app.command()
def clean(
    folders: Annotated[
        list[Path] | None,
        typer.Argument(
            help="Folders to look in (default: the current folder). Use the folder you gave "
            "to --workspace or --output.",
            metavar="[FOLDER]...",
        ),
    ] = None,
    older_than: Annotated[
        float,
        typer.Option(
            "--older-than", min=0, help="Only folders not used for this many days (default 0)."
        ),
    ] = 0,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Only list what would be removed.")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask first.")] = False,
) -> None:
    """Remove working folders left by interrupted downloads.

    Removing one means that download starts again from the beginning. Folders in use by a
    running download are never removed. The folders removed are printed on stdout.
    """
    from rayohx import find_workspaces, remove_workspaces

    found = find_workspaces(folders, older_than)
    candidates = [w for w in found if not w.in_use]
    skipped = len(found) - len(candidates)
    if not candidates:
        output.message("Nothing to clean." + (f" {skipped} in use." if skipped else ""))
        return
    total = sum(w.size for w in candidates)
    for w in candidates:
        output.message(f"{w.path}  {fmt.size(w.size)}, last used {w.age_days:.1f} days ago")
    if dry_run:
        output.message(f"Would remove {len(candidates)} folder(s), {fmt.size(total)}.")
        return
    if not yes and not typer.confirm(
        f"Remove {len(candidates)} folder(s) ({fmt.size(total)})?", err=True
    ):
        raise typer.Exit(1)
    for path in remove_workspaces(candidates):
        output.data(str(path))
    output.message(f"Removed {len(candidates)} folder(s), {fmt.size(total)}.", style="green")
