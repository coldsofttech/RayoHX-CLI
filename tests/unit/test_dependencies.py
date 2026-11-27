"""The command line imports only what it declares, and declares only what it uses."""

import ast
import sys
import tomllib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
SOURCE = PACKAGE / "src" / "rayohx_cli"
#: The command line may import itself and the core library it is built on.
OWN = {"rayohx", "rayohx_cli"}


def _declared() -> set[str]:
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    names = set()
    for requirement in project["dependencies"]:
        name = requirement
        for separator in ">=<~! ;[":
            name = name.split(separator)[0]
        names.add(name.lower().replace("-", "_"))
    return names


def _imported() -> set[str]:
    found: set[str] = set()
    for path in SOURCE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def test_every_third_party_import_is_a_declared_dependency() -> None:
    third_party = {name for name in _imported() if name not in sys.stdlib_module_names | OWN}
    assert third_party <= _declared(), f"imported but not declared: {third_party - _declared()}"


def test_every_declared_dependency_is_used() -> None:
    unused = _declared() - _imported()
    assert not unused, f"declared but never imported: {unused}"
