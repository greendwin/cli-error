from typing import Any, Literal, NamedTuple, Self, TypeAlias

from rich.markup import escape
from rich.text import Text

Role: TypeAlias = Literal["id", "path", "data", "cmd", "misc"]


class Prop(NamedTuple):
    key: str
    value: str
    role: Role | None


class CliError(Exception):
    """An application error carrying a Rich-markup message."""

    def __init__(self, template: str, **args: Any) -> None:
        self.message = _resolve_template(template, args)
        super().__init__(self.message)

        # TODO: TBD: props ordering could be an issue
        #       should we trust a user to that each prop will be in the same
        #       order everywheere? sshould we blame duplicates?
        self.props: list[Prop] = []
        self.detail_text: str | None = None
        self.hint_text: str | None = None

    def hint(self, template: str, **args: Any) -> Self:
        self.hint_text = _resolve_template(template, args)
        return self

    def detail(self, text: str) -> Self:
        self.detail_text = escape(text)
        return self

    def prop(self, key: str, value: Any) -> Self:
        return self._add_prop(key, value, None)

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

    def __str__(self) -> str:
        return _markup_to_str(self.message)

    def _add_prop(
        self,
        key: str,
        value: Any,
        role: Role | None,
    ) -> Self:
        self.props.append(Prop(key, escape(str(value)), role))
        return self


class CliExit(Exception):
    """A clean-exit signal carrying a message."""

    def __init__(self, template: str, **args: Any) -> None:
        self.message = _resolve_template(template, args)
        super().__init__(self.message)

    def __str__(self) -> str:
        return _markup_to_str(self.message)


def _resolve_template(template: str, args: dict[str, Any]) -> str:
    if not args:
        return template

    return template.format(**{key: escape(str(value)) for key, value in args.items()})


def _markup_to_str(rich_text: str) -> str:
    return Text.from_markup(rich_text).plain
