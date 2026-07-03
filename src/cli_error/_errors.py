from typing import Any, Self

from rich.markup import escape
from rich.text import Text


class CliError(Exception):
    """An application error carrying a Rich-markup message."""

    def __init__(self, template: str, **args: Any) -> None:
        self._message = _resolve_template(template, args)
        super().__init__(self._message)

        self._props: dict[str, str] = {}  # key: prop-name, value: rich text
        self._detail_text: str | None = None
        self._hint_text: str | None = None

    def hint(self, template: str, **args: Any) -> Self:
        self._hint_text = _resolve_template(template, args)
        return self

    def detail(self, text: str) -> Self:
        self._detail_text = escape(text)
        return self

    def prop(self, key: str, template: str, **args: Any) -> Self:
        self._props[key] = _resolve_template(template, args)
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
        return _markup_to_str(self._message)


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
