from collections.abc import Mapping

from rich.console import Console
from rich.style import Style
from rich.theme import Theme

DEFAULT_STYLES: Mapping[str, str] = {
    "id": "green",
    "data": "cyan",
    "path": "dim",
    "cmd": "blue",
    "misc": "dim",
    "warn": "yellow",
    "err": "red",
}


def make_theme(*, styles: Mapping[str, str | Style] | None = None) -> Theme:
    """Return a Rich theme built from the default roles plus ``styles``"""
    return Theme({**DEFAULT_STYLES, **(styles or {})})


def make_console(
    *,
    styles: Mapping[str, str | Style] | None = None,
    no_color: bool = False,
    stderr: bool = False,
) -> Console:
    """Return a Rich console themed with the default style roles.

    ``styles`` overrides or extends :data:`DEFAULT_STYLES` for this console.
    Set ``no_color`` to render styled markup as plain text (no ANSI escapes).
    Set ``stderr`` to route output to ``sys.stderr`` instead of ``sys.stdout``.
    """
    return Console(
        theme=make_theme(styles=styles),
        highlight=False,
        stderr=stderr,
        no_color=no_color,
    )
