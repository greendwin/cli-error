import pytest
from rich.console import Console

from cli_error import CliError, CliExit, escape, make_console

PROP_METHODS = ["prop_id", "prop_path", "prop_data", "prop_cmd", "prop_misc", "prop"]
PROP_HELPERS = {
    "prop_id": "id",
    "prop_path": "path",
    "prop_data": "data",
    "prop_cmd": "cmd",
    "prop_misc": "misc",
}


@pytest.fixture
def error() -> CliError:
    return CliError("boom")


def test_public_import_surface() -> None:
    assert callable(escape)
    assert callable(make_console)
    assert issubclass(CliError, Exception)
    assert issubclass(CliExit, Exception)


def test_escape_re_export_escapes_open_bracket() -> None:
    assert escape("a[b]c") == "a\\[b]c"


def test_args_are_escaped_and_template_markup_preserved() -> None:
    error = CliError("in [id]{commit}[/id]", commit="a[b]c")
    assert escape("a[b]c") in error._message
    assert "[id]" in error._message
    assert "[/id]" in error._message


def test_str_strips_markup_from_resolved_message() -> None:
    error = CliError("in [id]{commit}[/id]", commit="a[b]c")
    assert str(error) == "in a[b]c"


def test_str_of_plain_message() -> None:
    assert str(CliError("plain")) == "plain"


def test_no_arg_construction_keeps_braces_verbatim() -> None:
    error = CliError("plain {value} message")
    assert error._message == "plain {value} message"
    assert str(error) == "plain {value} message"


def test_literal_braces_use_double_brace_escaping() -> None:
    error = CliError("show {{literal}} for [id]{name}[/id]", name="x")
    assert "{literal}" in error._message
    assert str(error) == "show {literal} for x"


def test_cli_exit_carries_message() -> None:
    exit_signal = CliExit("done")
    assert exit_signal.message == "done"
    assert str(exit_signal) == "done"


def test_cli_exit_args_are_escaped_and_template_markup_preserved() -> None:
    exit_signal = CliExit("in [id]{commit}[/id]", commit="a[b]c")
    assert escape("a[b]c") in exit_signal.message
    assert "[id]" in exit_signal.message
    assert "[/id]" in exit_signal.message
    assert str(exit_signal) == "in a[b]c"


def test_cli_exit_str_strips_markup_from_resolved_message() -> None:
    exit_signal = CliExit("in [id]{commit}[/id]", commit="a[b]c")
    assert str(exit_signal) == "in a[b]c"


def test_cli_exit_no_arg_construction_keeps_braces_verbatim() -> None:
    exit_signal = CliExit("plain {value} message")
    assert exit_signal.message == "plain {value} message"


def test_cli_exit_missing_placeholder_raises() -> None:
    with pytest.raises(KeyError):
        CliExit("need [id]{name}[/id]", other="x")


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


def test_builder_methods_return_self(error: CliError) -> None:
    assert error.prop_id("k", "v") is error
    assert error.prop_path("k", "v") is error
    assert error.prop_data("k", "v") is error
    assert error.prop_cmd("k", "v") is error
    assert error.prop_misc("k", "v") is error
    assert error.prop("k", "v") is error
    assert error.hint("h") is error
    assert error.detail("d") is error


def test_prop_helpers_wrap_value_in_role_markup(error: CliError) -> None:
    error.prop_id("a", "1")
    error.prop_path("b", "2")
    error.prop_data("c", "3")
    error.prop_cmd("d", "4")
    error.prop_misc("e", "5")
    assert error._props == {
        "a": "[id]1[/id]",
        "b": "[path]2[/path]",
        "c": "[data]3[/data]",
        "d": "[cmd]4[/cmd]",
        "e": "[misc]5[/misc]",
    }


def test_plain_prop_stores_arg_free_template_verbatim(error: CliError) -> None:
    error.prop("k", "v")
    assert error._props == {"k": "v"}


def test_plain_prop_template_markup_is_preserved_verbatim(error: CliError) -> None:
    error.prop("k", "see [id]main[/id]")
    assert error._props["k"] == "see [id]main[/id]"


def test_plain_prop_args_are_escaped_and_template_markup_preserved(
    error: CliError,
) -> None:
    error.prop("k", "see [id]{ref}[/id]", ref="a[b]c")
    assert error._props["k"] == f"see [id]{escape('a[b]c')}[/id]"


def test_plain_prop_missing_placeholder_raises(error: CliError) -> None:
    with pytest.raises(KeyError):
        error.prop("k", "need [id]{name}[/id]", other="x")


def test_props_preserve_insertion_order(error: CliError) -> None:
    error.prop("first", "1").prop_id("second", "2").prop("third", "3")
    assert list(error._props) == ["first", "second", "third"]


def test_duplicate_keys_last_wins(error: CliError) -> None:
    error.prop("k", "one").prop("k", "two")
    assert error._props == {"k": "two"}


@pytest.mark.parametrize("method, tag", list(PROP_HELPERS.items()))
def test_prop_helper_escapes_value_inside_role_markup(
    method: str, tag: str, error: CliError
) -> None:
    getattr(error, method)("k", "a[b]c")
    assert error._props["k"] == f"[{tag}]{escape('a[b]c')}[/{tag}]"


def test_plain_prop_value_is_stored_verbatim_not_escaped(error: CliError) -> None:
    error.prop("k", "a[b]c")
    assert error._props["k"] == "a[b]c"


@pytest.mark.parametrize("method", PROP_METHODS)
def test_prop_key_is_stored_verbatim(method: str, error: CliError) -> None:
    getattr(error, method)("a[b]", "v")
    assert "a[b]" in error._props


def test_prop_value_is_stringified(error: CliError) -> None:
    error.prop_data("count", 42)
    assert error._props["count"] == "[data]42[/data]"


class _Markup:
    def __str__(self) -> str:
        return "x[y]"


def test_prop_data_non_str_value_is_stringified_then_escaped(error: CliError) -> None:
    value = _Markup()
    error.prop_data("k", value)
    assert error._props["k"] == f"[data]{escape(str(value))}[/data]"


def test_detail_is_escaped_at_store(error: CliError) -> None:
    error.detail("a[b]c")
    assert error._detail_text == escape("a[b]c")


def test_detail_last_wins(error: CliError) -> None:
    error.detail("first").detail("a[b]c")
    assert error._detail_text == escape("a[b]c")


def test_hint_is_stored_verbatim(error: CliError) -> None:
    error.hint("see [id]main[/id]")
    assert error._hint_text == "see [id]main[/id]"


def test_hint_no_arg_construction_keeps_braces_verbatim(error: CliError) -> None:
    error.hint("use {ref} syntax")
    assert error._hint_text == "use {ref} syntax"


def test_hint_last_wins(error: CliError) -> None:
    error.hint("first").hint("second")
    assert error._hint_text == "second"


def test_hint_args_are_escaped_and_template_markup_preserved(error: CliError) -> None:
    error.hint("see [id]{commit}[/id]", commit="a[b]c")
    assert error._hint_text is not None
    assert escape("a[b]c") in error._hint_text
    assert "[id]" in error._hint_text
    assert "[/id]" in error._hint_text


def test_hint_last_wins_with_args(error: CliError) -> None:
    error.hint("first {x}", x="1").hint("second {y}", y="2")
    assert error._hint_text == "second 2"


def test_hint_missing_placeholder_raises(error: CliError) -> None:
    with pytest.raises(KeyError):
        error.hint("need [id]{name}[/id]", other="x")


def test_arbitrary_chaining_order_works(error: CliError) -> None:
    result = error.hint("h").prop_id("k", "v").detail("d").prop("x", "y")
    assert result is error
    assert error._hint_text == "h"
    assert list(error._props) == ["k", "x"]
    assert error._detail_text == "d"


def test_building_does_not_alter_message_or_str() -> None:
    error = CliError("in [id]{commit}[/id]", commit="a[b]c")
    original_message = error._message
    error.prop_id("k", "v").hint("h").detail("d")
    assert error._message == original_message
    assert str(error) == "in a[b]c"


def test_fresh_error_has_empty_containers(error: CliError) -> None:
    assert error._props == {}
    assert error._detail_text is None
    assert error._hint_text is None
