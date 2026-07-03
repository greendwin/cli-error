from typing import Any, Literal, NamedTuple, Self, TypeAlias

from rich.markup import escape
from rich.text import Text

Role: TypeAlias = Literal["id", "path", "data", "cmd", "misc"]


class _Prop(NamedTuple):
    """A single rendered property: verbatim key, escaped value, optional role."""

    key: str
    value: str
    role: Role | None


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

        self.props: list[_Prop] = []
        self.details: list[str] = []
        self.hint_text: str | None = None

        super().__init__(self.message)

    def __str__(self) -> str:
        return Text.from_markup(self.message).plain

    def _add_prop(
        self,
        key: str,
        value: Any,
        role: Role | None,
    ) -> Self:
        self.props.append(_Prop(key, escape(str(value)), role))
        return self

    def prop_id(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, "id")

    def prop_path(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, "path")

    def prop_data(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, "data")

    def prop_cmd(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, "cmd")

    def prop_misc(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, "misc")

    def prop(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, None)

    def hint(self, text: str) -> Self:
        # TODO: compose same as `CliExport` constr (template and args with escape)
        # TODO: why hint replaces prev val, but `detail` appends?
        self.hint_text = text
        return self

    def detail(self, text: Any) -> Self:
        # TODO: do we need `Any`? why not str?
        self.details.append(escape(str(text)))
        return self


class CliExit(Exception):
    """A clean-exit signal carrying a message."""

    def __init__(self, message: str) -> None:
        # TODO: lets support `template` and `args` with escape
        super().__init__(message)
        self.message = message
