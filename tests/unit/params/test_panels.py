"""The help panels that group the options."""

from typer.models import OptionInfo

from rayohx_cli import params
from rayohx_cli.params import panels
from tests.helpers.params import declaration

TITLES = {
    "SELECTION": "Choosing what to download",
    "NETWORK": "Network",
    "ENGINE": "Download engine",
    "OUTPUT": "Output",
    "DISPLAY": "Display",
}
PANELS = set(TITLES.values())


def _options() -> dict[str, OptionInfo]:
    found = {}
    for name in params.__all__:
        info = declaration(getattr(params, name))
        if isinstance(info, OptionInfo):
            found[name] = info
    return found


def test_the_panels_have_their_help_titles() -> None:
    for name, title in TITLES.items():
        assert getattr(panels, name) == title


def test_every_option_is_in_a_panel_that_exists() -> None:
    options = _options()
    assert options
    for name, info in options.items():
        assert info.rich_help_panel in PANELS, name


def test_every_panel_has_options() -> None:
    used = {info.rich_help_panel for info in _options().values()}
    assert used == PANELS


def test_everything_exported_is_an_option_or_the_url() -> None:
    arguments = [
        name
        for name in params.__all__
        if not isinstance(declaration(getattr(params, name)), OptionInfo)
    ]
    assert arguments == ["Url", "Urls"]
