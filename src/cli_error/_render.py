from dataclasses import dataclass, field
from typing import Any

from rich.markup import escape
from rich.text import Text


@dataclass
class ErrorDesc:
    message: str
    props: dict[str, str] = field(default_factory=dict)
    detail: str = ""
    hint: str = ""


def render_error(desc: ErrorDesc) -> str:
    r = []
    r.append(desc.message)

    for key, value in desc.props.items():
        r.append(f"  {escape(key)}: {value}")

    if desc.detail:
        r.append(desc.detail)

    if desc.hint:
        r.append("")
        r.append(desc.hint)

    return "\n".join(r)


def render_template(template: str, **args: Any) -> str:
    if not args:
        return template

    return template.format(**{key: escape(str(value)) for key, value in args.items()})


def strip_markup(text: str) -> str:
    return Text.from_markup(text).plain
