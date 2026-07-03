import pytest
from rich.console import Console

from cli_error import CliError, CliExit, ErrorReporter, make_console


@pytest.fixture
def console() -> Console:
    return make_console()


@pytest.fixture
def reporter(console: Console) -> ErrorReporter:
    return ErrorReporter(console)


def run_handler(
    console: Console, reporter: ErrorReporter, error: BaseException
) -> tuple[int, str]:
    with console.capture() as capture:
        with pytest.raises(SystemExit) as exc:
            with reporter.handler():
                raise error
    code = exc.value.code
    assert isinstance(code, int)
    return code, capture.get().strip()


@pytest.mark.parametrize(
    ("error", "expected_code", "expected_output"),
    [
        (CliExit("done"), 0, "done"),
        (CliError("boom"), 1, "Error: boom"),
        (ValueError("x"), 1, "Error: x"),
        (SystemExit(2), 2, ""),
        (CliExit(""), 0, ""),
    ],
)
def test_handler_exit_paths(
    console: Console,
    reporter: ErrorReporter,
    error: BaseException,
    expected_code: int,
    expected_output: str,
) -> None:
    code, output = run_handler(console, reporter, error)
    assert code == expected_code
    assert output == expected_output


def test_cli_error_with_hint_and_prop_is_rendered(
    console: Console, reporter: ErrorReporter
) -> None:
    error = CliError("boom").hint("try X").prop_id("id", "42")
    code, output = run_handler(console, reporter, error)
    assert code == 1
    assert "try X" in output
    assert "id" in output
    assert "42" in output


def test_keyboard_interrupt_propagates_without_output(
    console: Console, reporter: ErrorReporter
) -> None:
    with console.capture() as capture:
        with pytest.raises(KeyboardInterrupt):
            with reporter.handler():
                raise KeyboardInterrupt
    assert capture.get() == ""


def test_no_error_yields_and_prints_nothing(
    console: Console, reporter: ErrorReporter
) -> None:
    with console.capture() as capture:
        with reporter.handler():
            pass
    assert capture.get() == ""
