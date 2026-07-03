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


def make_console(*, stderr: bool = False) -> Console:
    """Return a Rich console themed with the default style roles.

    Set ``stderr`` to route output to ``sys.stderr`` instead of ``sys.stdout``.
    """
    return Console(theme=Theme(_DEFAULT_STYLES), highlight=False, stderr=stderr)
