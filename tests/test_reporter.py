from pathlib import Path

import pytest
from rich.console import Console

import cli_error
from cli_error import CliError, CliExit, CliReporter, make_console, make_theme


def make_color_console() -> Console:
    """A stderr-style console that always emits ANSI so style roles resolve."""
    return Console(
        theme=make_theme(),
        highlight=False,
        force_terminal=True,
        color_system="standard",
    )


@pytest.fixture
def console() -> Console:
    return make_console()


@pytest.fixture
def reporter(console: Console) -> CliReporter:
    return CliReporter(console)


@pytest.fixture
def debug_reporter(console: Console) -> CliReporter:
    return CliReporter(console, debug=True)


@pytest.fixture
def color_reporter() -> tuple[Console, CliReporter]:
    """A forced-color stderr console paired with a debug reporter wired to it."""
    color_console = make_color_console()
    reporter = CliReporter(make_console(), debug=True, console_err=color_console)
    return color_console, reporter


def run_handler(
    console: Console,
    reporter: CliReporter,
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
    reporter: CliReporter,
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
    reporter: CliReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    error = CliError("boom").hint("try X").prop_id("id", "42")
    code, output, _ = run_handler(console, reporter, error, capsys)
    assert code == 1
    assert "try X" in output
    assert "id" in output
    assert "42" in output


def test_keyboard_interrupt_propagates_without_output(
    console: Console, reporter: CliReporter
) -> None:
    with console.capture() as capture:
        with pytest.raises(KeyboardInterrupt):
            with reporter.handler():
                raise KeyboardInterrupt
    assert capture.get() == ""


def test_no_error_yields_and_prints_nothing(
    console: Console, reporter: CliReporter
) -> None:
    with console.capture() as capture:
        with reporter.handler():
            pass
    assert capture.get() == ""


def test_debug_emits_traceback_on_stderr_and_error_on_stdout(
    console: Console,
    debug_reporter: CliReporter,
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
    reporter: CliReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, output, err = run_handler(console, reporter, ValueError("boom"), capsys)
    assert code == 1
    assert "Error: boom" in output
    assert err == ""


def test_system_exit_propagates_without_traceback_under_debug(
    console: Console,
    debug_reporter: CliReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _, err = run_handler(console, debug_reporter, SystemExit(2), capsys)
    assert code == 2
    assert err == ""


def test_cli_exit_never_emits_traceback_even_with_debug(
    console: Console,
    debug_reporter: CliReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _, err = run_handler(console, debug_reporter, CliExit("done"), capsys)
    assert code == 0
    assert err == ""


def test_error_reporter_name_is_gone() -> None:
    assert not hasattr(cli_error, "ErrorReporter")
    assert "ErrorReporter" not in cli_error.__all__
    assert "CliReporter" in cli_error.__all__


def test_print_emits_escaped_args_and_honors_end(
    console: Console, reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    with console.capture() as capture:
        reporter.print("value: {v}", v="[bold]x[/bold]", end="")
    assert capture.get() == "value: [bold]x[/bold]"
    # ``print`` must not leak onto the stderr/debug stream.
    assert capsys.readouterr().err == ""


def test_print_defaults_to_trailing_newline(
    console: Console, reporter: CliReporter
) -> None:
    with console.capture() as capture:
        reporter.print("hi")
    assert capture.get() == "hi\n"


def test_print_allows_placeholder_named_template(
    console: Console, reporter: CliReporter
) -> None:
    # ``template`` being positional-only frees the name for use as a
    # format-placeholder / escaped-arg key.
    with console.capture() as capture:
        reporter.print("{template}", template="a", end="")
    assert capture.get() == "a"


def test_print_always_emits_regardless_of_debug(
    console: Console, reporter: CliReporter
) -> None:
    with console.capture() as capture:
        reporter.print("out")
    assert capture.get() == "out\n"


def test_debug_silent_when_disabled(
    reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    reporter.debug_print("nope")
    assert capsys.readouterr().err == ""


def test_debug_emits_on_stderr_when_enabled(
    console: Console,
    debug_reporter: CliReporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with console.capture() as capture:
        debug_reporter.debug_print("line: {v}", v="hi")
    err = capsys.readouterr().err
    assert "line: hi" in err
    # ``debug`` must not leak onto the stdout console.
    assert capture.get() == ""


def test_debug_honors_end(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_print("a", end="")
    debug_reporter.debug_print("b")
    err = capsys.readouterr().err
    assert err == "ab\n"


def test_debug_renders_template_unchanged_with_escaped_args(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_print("[warn]{v}[/warn]", v="danger[x]")
    err = capsys.readouterr().err
    # Trusted markup applies (styling), the arg is escaped so its brackets
    # render literally rather than as markup.
    assert "danger[x]" in err


def test_debug_cmd_emits_command_and_cwd(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_cmd(["git", "commit", "-m", "a b"], cwd=Path("/tmp/x"))
    err = capsys.readouterr().err
    assert "COMMAND: git commit -m 'a b'" in err
    assert "cwd: /tmp/x" in err


def test_debug_cmd_omits_cwd_when_none(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_cmd(["ls"])
    err = capsys.readouterr().err
    assert "COMMAND: ls" in err
    assert "cwd:" not in err


def test_debug_cmd_silent_when_disabled(
    reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    reporter.debug_cmd(["ls"], cwd=Path("/tmp"))
    assert capsys.readouterr().err == ""


def test_debug_cmd_escapes_markup(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_cmd(["echo", "[red]hi[/red]"])
    err = capsys.readouterr().err
    assert "[red]hi[/red]" in err


def test_debug_output_emits_both_streams(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_output("out1\nout2  \n", "err1")
    err = capsys.readouterr().err
    assert "stdout:" in err
    assert "out1\nout2" in err
    assert "stderr:" in err
    assert "err1" in err


def test_debug_output_skips_empty_streams(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_output("  ", "\n\t")
    assert capsys.readouterr().err == ""


def test_debug_output_skips_only_the_empty_stream(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_output("kept", "   ")
    err = capsys.readouterr().err
    assert "stdout:" in err
    assert "kept" in err
    assert "stderr:" not in err


def test_debug_output_escapes_markup(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_output("[red]x[/red]", "")
    err = capsys.readouterr().err
    assert "[red]x[/red]" in err


def test_debug_output_silent_when_disabled(
    reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    reporter.debug_output("out", "err")
    assert capsys.readouterr().err == ""


def test_debug_cmd_wraps_payload_in_dim_misc_style(
    color_reporter: tuple[Console, CliReporter],
) -> None:
    # With color forced on, the ``misc`` role (=dim) must render its ANSI
    # escape around the diagnostic, proving the ``[misc]…[/misc]`` wrapper
    # is applied rather than dropped.
    color_console, reporter = color_reporter
    with color_console.capture() as capture:
        reporter.debug_cmd(["ls"])
    output = capture.get()
    assert "\x1b[2m" in output
    assert "COMMAND: ls" in output


def test_debug_honors_trusted_markup_but_escapes_args(
    color_reporter: tuple[Console, CliReporter],
) -> None:
    # A trusted template role (``warn`` = yellow) renders its ANSI styling,
    # while a bracketed arg stays literal (escaped, not interpreted).
    color_console, reporter = color_reporter
    with color_console.capture() as capture:
        reporter.debug_print("[warn]{v}[/warn]", v="danger[x]")
    output = capture.get()
    assert "\x1b[33m" in output
    assert "danger[x]" in output


def test_debug_traceback_silent_when_disabled(
    reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        reporter.debug_traceback()
    assert capsys.readouterr().err == ""


def test_debug_traceback_noops_outside_except_block(
    debug_reporter: CliReporter, capsys: pytest.CaptureFixture[str]
) -> None:
    debug_reporter.debug_traceback()
    assert capsys.readouterr().err == ""
