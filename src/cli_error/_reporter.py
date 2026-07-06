import shlex
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from rich.console import Console

from ._console import make_console
from ._errors import CliExit, print_error
from ._render import render_template


class CliReporter:
    """Single integration point for a CLI's terminal output."""

    def __init__(
        self,
        console: Console,
        *,
        debug: bool = False,
        show_locals: bool = False,
        console_err: Console | None = None,
    ) -> None:
        self.debug = debug
        self.show_locals = show_locals
        self.console = console
        self.console_err = console_err or make_console(stderr=True)

    def print(self, template: str, /, *, end: str = "\n", **args: Any) -> None:
        """Render a trusted template with escaped args to the stdout console."""
        _emit(self.console, template, end, **args)

    def debug_print(self, template: str, /, *, end: str = "\n", **args: Any) -> None:
        """Render a trusted template with escaped args to the stderr console.

        Silent no-op unless ``debug`` is set. The template is emitted unchanged
        (no forced styling), so a consumer can emit e.g. a ``[warn]`` line.
        """
        if self.debug:
            _emit(self.console_err, template, end, **args)

    def debug_traceback(self, *, show_locals: bool | None = None) -> None:
        """Emit the currently-handled traceback to the stderr console.

        No-op unless ``debug`` is set. Safely no-ops outside an ``except``
        block: ``print_exception`` reads ``sys.exc_info()``.

        ``show_locals`` overrides the instance default per call; when left as
        ``None`` the traceback defers to the ``show_locals`` flag the reporter
        was constructed with.

        Caution: ``show_locals`` renders every frame's local variables verbatim
        to stderr, which may expose secrets (tokens, passwords). Keep it gated
        behind an explicit developer-only flag.
        """
        if not self.debug:
            return

        if sys.exc_info()[0] is None:
            return

        effective = show_locals
        if effective is None:
            effective = self.show_locals

        self.console_err.print_exception(show_locals=effective)

    def debug_cmd(self, cmd: list[str], cwd: Path | None = None) -> None:
        """Emit a subprocess command (and optional cwd) as a debug diagnostic."""
        if not self.debug:
            return

        self.debug_print("[misc]COMMAND: {cmd}[/misc]", cmd=shlex.join(cmd))
        if cwd is not None:
            self.debug_print("[misc]  cwd: {cwd}[/misc]", cwd=cwd)

    def debug_output(self, stdout: str, stderr: str) -> None:
        """Emit captured subprocess output as debug diagnostics.

        Each non-empty stream is emitted as a header line followed by the
        captured text as one escaped ``misc`` block; empty streams are skipped.
        """
        if not self.debug:
            return

        for label, text in (("stdout", stdout), ("stderr", stderr)):
            trimmed = text.rstrip()
            if not trimmed:
                continue

            # TODO: this layout is ugly, lets prepend each line 'stdout: ' prefix
            self.debug_print("[misc]  {label}:[/misc]", label=label)
            self.debug_print("[misc]{text}[/misc]", text=trimmed)

    @contextmanager
    def handler(self) -> Generator[None]:
        """Report errors and translate them into process exit codes.

        * ``CliExit`` prints its message and exits 0;
        * any other ``Exception`` is rendered via ``print_error`` and exits 1,
          additionally emitting a full traceback to the ``stderr`` console when
          ``debug`` is set.
        * ``KeyboardInterrupt``, ``SystemExit`` and any other ``BaseException``
        propagate untouched.
        """
        try:
            yield
        except CliExit as ex:
            self.print(ex.message)
            raise SystemExit(0) from None
        except Exception as ex:
            self.debug_traceback()
            print_error(ex, self.console)
            raise SystemExit(1) from None


def _emit(console: Console, template: str, end: str, /, **args: Any) -> None:
    console.print(render_template(template, **args), end=end)
