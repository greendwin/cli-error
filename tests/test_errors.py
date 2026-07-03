from collections.abc import Callable

import pytest
from rich.console import Console

from cli_error import CliError, CliExit, escape, make_console

PROP_METHODS = ["prop_id", "prop_path", "prop_data", "prop_cmd", "prop_misc", "prop"]


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


def test_builder_methods_return_self(error: CliError) -> None:
    assert error.prop_id("k", "v") is error
    assert error.prop_path("k", "v") is error
    assert error.prop_data("k", "v") is error
    assert error.prop_cmd("k", "v") is error
    assert error.prop_misc("k", "v") is error
    assert error.prop("k", "v") is error
    assert error.hint("h") is error
    assert error.detail("d") is error


def test_typed_props_tag_correct_role(error: CliError) -> None:
    error.prop_id("a", "1")
    error.prop_path("b", "2")
    error.prop_data("c", "3")
    error.prop_cmd("d", "4")
    error.prop_misc("e", "5")
    roles = [(p.key, p.value, p.role) for p in error.props]
    assert roles == [
        ("a", "1", "id"),
        ("b", "2", "path"),
        ("c", "3", "data"),
        ("d", "4", "cmd"),
        ("e", "5", "misc"),
    ]


def test_prop_is_role_less(error: CliError) -> None:
    error.prop("k", "v")
    assert error.props[0].key == "k"
    assert error.props[0].value == "v"
    assert error.props[0].role is None


def test_props_preserve_insertion_order(error: CliError) -> None:
    error.prop("first", "1").prop_id("second", "2").prop("third", "3")
    assert [p.key for p in error.props] == ["first", "second", "third"]


def test_duplicate_keys_are_kept(error: CliError) -> None:
    error.prop("k", "one").prop("k", "two")
    assert [(p.key, p.value) for p in error.props] == [("k", "one"), ("k", "two")]


@pytest.mark.parametrize("method", PROP_METHODS)
def test_prop_value_is_escaped_at_store_time(method: str, error: CliError) -> None:
    getattr(error, method)("k", "a[b]c")
    assert error.props[0].value == escape("a[b]c")


@pytest.mark.parametrize("method", PROP_METHODS)
def test_prop_key_is_stored_verbatim(method: str, error: CliError) -> None:
    getattr(error, method)("a[b]", "v")
    assert error.props[0].key == "a[b]"


def test_prop_value_is_stringified(error: CliError) -> None:
    error.prop_data("count", 42)
    assert error.props[0].value == "42"


class _Markup:
    def __str__(self) -> str:
        return "x[y]"


@pytest.mark.parametrize(
    ("store", "read"),
    [
        (lambda e, v: e.prop_data("k", v), lambda e: e.props[0].value),
        (lambda e, v: e.detail(v), lambda e: e.details[0]),
    ],
)
def test_non_str_value_is_stringified_then_escaped(
    store: Callable[[CliError, object], object],
    read: Callable[[CliError], str],
    error: CliError,
) -> None:
    value = _Markup()
    store(error, value)
    assert read(error) == escape(str(value))


def test_detail_is_escaped_and_ordered(error: CliError) -> None:
    error.detail("a[b]c").detail("plain")
    assert error.details == [escape("a[b]c"), "plain"]


def test_hint_is_stored_verbatim(error: CliError) -> None:
    error.hint("see [id]main[/id]")
    assert error.hint_text == "see [id]main[/id]"


def test_hint_last_wins(error: CliError) -> None:
    error.hint("first").hint("second")
    assert error.hint_text == "second"


def test_arbitrary_chaining_order_works(error: CliError) -> None:
    result = error.hint("h").prop_id("k", "v").detail("d").prop("x", "y")
    assert result is error
    assert error.hint_text == "h"
    assert [p.key for p in error.props] == ["k", "x"]
    assert error.details == ["d"]


def test_building_does_not_alter_message_or_str() -> None:
    error = CliError("in [id]{commit}[/id]", commit="a[b]c")
    original_message = error.message
    error.prop_id("k", "v").hint("h").detail("d")
    assert error.message == original_message
    assert str(error) == "in a[b]c"


def test_fresh_error_has_empty_containers(error: CliError) -> None:
    assert error.props == []
    assert error.details == []
    assert error.hint_text is None
