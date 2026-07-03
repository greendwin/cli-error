from typing import Any

from rich.markup import escape
from rich.text import Text


class CliError(Exception):
    """An application error carrying a Rich-markup message.

    The template is developer-authored (trusted markup). Any ``**args`` are
    escaped before substitution so untrusted values cannot inject or break
    markup. When no args are given the template is stored verbatim, so plain
    ``{...}`` braces do not need escaping.

    Passing any arg switches the template into ``str.format`` mode, at which
    point every ``{placeholder}`` must have a matching arg and literal braces
    must be doubled (``{{``/``}}``); an arg-free call stores the template as-is.
    """

    def __init__(self, template: str, **args: Any) -> None:
        if args:
            self.message = template.format(
                **{key: escape(str(value)) for key, value in args.items()}
            )
        else:
            self.message = template

        super().__init__(self.message)

    def __str__(self) -> str:
        return Text.from_markup(self.message).plain


class CliExit(Exception):
    """A clean-exit signal carrying a message."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
