"""Error handling and reporting utilities for CLI applications."""

__all__ = [
    "CliError",
    "CliExit",
    "ErrorReporter",
    "escape",
    "make_console",
    "print_error",
    "render_error",
    "render_template",
]

from rich.markup import escape

from ._console import make_console
from ._errors import CliError, CliExit, print_error
from ._render import render_error, render_template
from ._reporter import ErrorReporter
