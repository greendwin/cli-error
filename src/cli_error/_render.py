from dataclasses import dataclass, field
from typing import Any, Protocol

from rich.markup import escape


class Printer(Protocol):
    def print(self, text: str, /) -> None: ...


@dataclass
class ErrorDesc:
    message: str
    props: dict[str, str] = field(default_factory=dict)
    detail: str = ""
    hint: str = ""


def render_error(desc: ErrorDesc, output: Printer) -> None:
    output.print(f"[err]Error:[/err] {desc.message}")

    for key, value in desc.props.items():
        output.print(f"  {escape(key)}: {value}")

    if desc.detail:
        output.print(f"[misc]{desc.detail}[/misc]")

    if desc.hint:
        output.print("")
        output.print(desc.hint)


def render_template(template: str, **args: Any) -> str:
    if not args:
        return template

    return template.format(**{key: escape(str(value)) for key, value in args.items()})
