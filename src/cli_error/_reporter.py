from collections.abc import Generator
from contextlib import contextmanager

from rich.console import Console

from ._console import make_console
from ._errors import CliExit, print_error


class ErrorReporter:
    """Single integration point for reporting CLI errors and clean exits."""

    def __init__(
        self,
        console: Console,
        *,
        debug: bool = False,
        console_err: Console | None = None,
    ) -> None:
        self._console = console
        self._console_err: Console | None = console_err
        self.debug = debug

    def _debug_console(self) -> Console:
        if self._console_err is None:
            self._console_err = make_console(stderr=True)
        return self._console_err

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
            self._console.print(ex.message)
            raise SystemExit(0) from None
        except Exception as ex:
            if self.debug:
                # ``print_exception`` reads the currently-handled exception from
                # ``sys.exc_info()``, so it must stay inside this active
                # ``except Exception`` block to render the right traceback.
                self._debug_console().print_exception()
            print_error(ex, self._console)
            raise SystemExit(1) from None
