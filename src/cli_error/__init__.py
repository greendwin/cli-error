"""Error handling and reporting utilities for CLI applications."""

__all__ = [
    "CliError",
    "CliExit",
    "escape",
    "make_console",
]

from rich.markup import escape

from ._console import make_console
from ._errors import CliError, CliExit
