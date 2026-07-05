"""Error handling and reporting utilities for CLI applications."""

__all__ = [
    "CliError",
    "CliExit",
    "CliReporter",
    "DEFAULT_STYLES",
    "escape",
    "make_console",
    "make_theme",
    "print_error",
    "render_error",
    "render_template",
]

from rich.markup import escape

from ._console import DEFAULT_STYLES, make_console, make_theme
from ._errors import CliError, CliExit, print_error
from ._render import render_error, render_template
from ._reporter import CliReporter
