from rich.console import Console
from rich.theme import Theme

_DEFAULT_STYLES = {
    "id": "green",
    "data": "cyan",
    "path": "dim",
    "cmd": "blue",
    "misc": "dim",
    "warn": "yellow",
    "err": "red",
}


def make_console() -> Console:
    """Return a Rich console themed with the default style roles."""
    return Console(theme=Theme(_DEFAULT_STYLES), highlight=False)
