from collections.abc import Callable

from rich.console import Console
from rich.theme import Theme

from cli_error import DEFAULT_STYLES

_ROLES = tuple(DEFAULT_STYLES)


def forced_terminal(theme: Theme, *, no_color: bool = False) -> Console:
    return Console(
        theme=theme,
        force_terminal=True,
        color_system="standard",
        no_color=no_color,
        highlight=False,
        width=80,
    )


def theme_from(console: Console, roles: tuple[str, ...] = _ROLES) -> Theme:
    return Theme({role: console.get_style(role) for role in roles})


def capture_emit(console: Console, emit: Callable[[Console], None]) -> str:
    with console.capture() as cap:
        emit(console)
    return cap.get()


def capture(console: Console, markup: str) -> str:
    return capture_emit(console, lambda c: c.print(markup))
