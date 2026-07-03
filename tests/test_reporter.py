import pytest
from rich.console import Console

from cli_error import CliError, CliExit, ErrorReporter, make_console


@pytest.fixture
def console() -> Console:
    return make_console()


@pytest.fixture
def reporter(console: Console) -> ErrorReporter:
    return ErrorReporter(console)


@pytest.fixture
def debug_reporter(console: Console) -> ErrorReporter:
    return ErrorReporter(console, debug=True)


def run_handler(
    console: Console,
    reporter: ErrorReporter,
    error: BaseException,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str, str]:
    with console.capture() as capture:
        with pytest.raises(SystemExit) as exc:
            with reporter.handler():
                raise error
    code = exc.value.code
    assert isinstance(code, int)
    return code, capture.get().strip(), capsys.readouterr().err


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
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, output, _ = run_handler(console, reporter, error, capsys)
    assert code == expected_code
    assert output == expected_output


def test_cli_error_with_hint_and_prop_is_rendered(
    console: Console,
    reporter: ErrorReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    error = CliError("boom").hint("try X").prop_id("id", "42")
    code, output, _ = run_handler(console, reporter, error, capsys)
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


def test_debug_emits_traceback_on_stderr_and_error_on_stdout(
    console: Console,
    debug_reporter: ErrorReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, output, err = run_handler(console, debug_reporter, ValueError("boom"), capsys)
    assert code == 1
    assert "Error: boom" in output
    assert "Traceback" not in output
    assert "Traceback" in err
    assert "ValueError" in err


def test_debug_false_emits_no_stderr_output(
    console: Console,
    reporter: ErrorReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, output, err = run_handler(console, reporter, ValueError("boom"), capsys)
    assert code == 1
    assert "Error: boom" in output
    assert err == ""


def test_debug_set_after_construction_emits_traceback(
    console: Console,
    reporter: ErrorReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert reporter.debug is False
    reporter.debug = True
    code, _, err = run_handler(console, reporter, ValueError("boom"), capsys)
    assert code == 1
    assert "Traceback" in err
    assert "ValueError" in err


def test_system_exit_propagates_without_traceback_under_debug(
    console: Console,
    debug_reporter: ErrorReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _, err = run_handler(console, debug_reporter, SystemExit(2), capsys)
    assert code == 2
    assert err == ""


def test_cli_exit_never_emits_traceback_even_with_debug(
    console: Console,
    debug_reporter: ErrorReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _, err = run_handler(console, debug_reporter, CliExit("done"), capsys)
    assert code == 0
    assert err == ""
