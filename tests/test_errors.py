from rich.console import Console

from cli_error import CliError, CliExit, escape, make_console


def test_public_import_surface() -> None:
    assert callable(escape)
    assert callable(make_console)
    assert issubclass(CliError, Exception)
    assert issubclass(CliExit, Exception)


def test_escape_re_export_escapes_open_bracket() -> None:
    assert escape("a[b]c") == "a\\[b]c"


def test_args_are_escaped_and_template_markup_preserved() -> None:
    error = CliError("in [id]{commit}[/id]", commit="a[b]c")
    assert escape("a[b]c") in error.message
    assert "[id]" in error.message
    assert "[/id]" in error.message


def test_str_strips_markup_from_resolved_message() -> None:
    error = CliError("in [id]{commit}[/id]", commit="a[b]c")
    assert str(error) == "in a[b]c"


def test_str_of_plain_message() -> None:
    assert str(CliError("plain")) == "plain"


def test_no_arg_construction_keeps_braces_verbatim() -> None:
    error = CliError("plain {value} message")
    assert error.message == "plain {value} message"
    assert str(error) == "plain {value} message"


def test_literal_braces_use_double_brace_escaping() -> None:
    error = CliError("show {{literal}} for [id]{name}[/id]", name="x")
    assert "{literal}" in error.message
    assert str(error) == "show {literal} for x"


def test_cli_exit_carries_message() -> None:
    exit_signal = CliExit("done")
    assert exit_signal.message == "done"
    assert str(exit_signal) == "done"


def test_make_console_returns_console() -> None:
    console = make_console()
    assert isinstance(console, Console)
    with console.capture() as capture:
        console.print("[err]x[/err]")
    assert "x" in capture.get()


def test_make_console_wires_default_style_palette() -> None:
    console = make_console()
    err_color = console.get_style("err").color
    id_color = console.get_style("id").color
    data_color = console.get_style("data").color
    assert err_color is not None and err_color.name == "red"
    assert id_color is not None and id_color.name == "green"
    assert data_color is not None and data_color.name == "cyan"
