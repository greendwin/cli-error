from collections.abc import Generator
from contextlib import contextmanager

from rich.console import Console

from ._errors import CliExit, print_error


class ErrorReporter:
    """Single integration point for reporting CLI errors and clean exits."""

    def __init__(self, console: Console) -> None:
        self._console = console

    @contextmanager
    def handler(self) -> Generator[None]:
        """Report errors and translate them into process exit codes.

        * ``CliExit`` prints its message and exits 0;
        * any other ``Exception`` is rendered via ``print_error`` and exits 1.
        * ``KeyboardInterrupt``, ``SystemExit`` and any other ``BaseException``
        propagate untouched.
        """
        try:
            yield
        except CliExit as ex:
            self._console.print(ex.message)
            raise SystemExit(0) from None
        except Exception as ex:
            print_error(ex, self._console)
            raise SystemExit(1) from None
