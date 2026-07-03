from typing import Any, Self

from rich.console import Console
from rich.markup import escape

from ._render import (
    ErrorDesc,
    render_error,
    render_template,
    strip_markup,
)


class CliError(Exception):
    """An application error carrying a Rich-markup message."""

    def __init__(self, template: str, **args: Any) -> None:
        self.desc = ErrorDesc(render_template(template, **args))
        super().__init__(self.desc.message)

    def hint(self, template: str, **args: Any) -> Self:
        self.desc.hint = render_template(template, **args)
        return self

    def detail(self, text: str) -> Self:
        self.desc.detail = render_template("[misc]{detail}[/misc]", detail=text)
        return self

    def prop(self, key: str, template: str, **args: Any) -> Self:
        self.desc.props[key] = render_template(template, **args)
        return self

    def prop_id(self, key: str, value: Any) -> Self:
        return self.prop(key, "[id]{value}[/id]", value=value)

    def prop_path(self, key: str, value: Any) -> Self:
        return self.prop(key, "[path]{value}[/path]", value=value)

    def prop_data(self, key: str, value: Any) -> Self:
        return self.prop(key, "[data]{value}[/data]", value=value)

    def prop_cmd(self, key: str, value: Any) -> Self:
        return self.prop(key, "[cmd]{value}[/cmd]", value=value)

    def prop_misc(self, key: str, value: Any) -> Self:
        return self.prop(key, "[misc]{value}[/misc]", value=value)

    def __str__(self) -> str:
        return strip_markup(self.desc.message)


class CliExit(Exception):
    """A clean-exit signal carrying a message."""

    def __init__(self, template: str, **args: Any) -> None:
        self.message = render_template(template, **args)
        super().__init__(self.message)

    def __str__(self) -> str:
        return strip_markup(self.message)


def print_error(ex: Exception, console: Console) -> None:
    if isinstance(ex, CliError):
        console.print(f"[err]Error:[/err] {render_error(ex.desc)}")
    else:
        console.print(render_template("[err]Error:[/err] {ex}", ex=ex))

    seen = {id(ex)}
    cause = _next_link(ex)
    while cause is not None and id(cause) not in seen:
        # note: markup-stripped for CliError via its __str__,
        # not the full props/detail/hint layout
        console.print(f"  caused by: {escape(str(cause))}")
        seen.add(id(cause))
        cause = _next_link(cause)


def _next_link(exc: BaseException) -> BaseException | None:
    if exc.__cause__ is not None:
        return exc.__cause__

    return None if exc.__suppress_context__ else exc.__context__
