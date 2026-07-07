from cli_error import CliError, make_console, print_error, render_error
from tests.helpers import capture_emit, forced_terminal, theme_from


def _render(ex: Exception) -> str:
    console = make_console()
    return capture_emit(console, lambda c: print_error(ex, c))


def test_full_layout_renders_in_documented_order() -> None:
    error = (
        CliError("bad [id]thing[/id]")
        .prop_id("id", "abc")
        .prop_path("path", "/tmp/x")
        .detail("some\noutput")
        .hint("try [cmd]--force[/cmd]")
    )
    assert _render(error).splitlines() == [
        "Error: bad thing",
        "  id: abc",
        "  path: /tmp/x",
        "some",
        "output",
        "",
        "try --force",
    ]


def test_bare_cli_error_renders_error_prefix_and_message() -> None:
    assert _render(CliError("boom")).strip() == "Error: boom"


def test_non_cli_error_renders_error_prefix_and_str() -> None:
    assert _render(ValueError("nope")).strip() == "Error: nope"


def test_non_cli_error_message_is_escaped() -> None:
    assert _render(ValueError("a[b]c")).strip() == "Error: a[b]c"


def test_empty_non_cli_error_falls_back_to_type_name() -> None:
    assert _render(ValueError()).splitlines() == ["Error: ValueError"]


def test_whitespace_only_non_cli_error_falls_back_to_type_name() -> None:
    assert _render(ValueError("   ")).splitlines() == ["Error: ValueError"]


def test_prop_value_key_and_detail_render_brackets_literally() -> None:
    error = CliError("m").prop_id("a[b]", "x[y]").detail("d[e]")
    out = _render(error)
    assert "  a[b]: x[y]" in out
    assert "d[e]" in out


def test_hint_without_props_still_gets_blank_line_separator() -> None:
    error = CliError("m").hint("h")
    assert _render(error).splitlines() == ["Error: m", "", "h"]


def test_empty_message_still_prints_error_prefix() -> None:
    out = _render(CliError(""))
    assert out.splitlines()[0].rstrip() == "Error:"


def test_no_props_detail_or_hint_emits_only_message() -> None:
    assert _render(CliError("m")).splitlines() == ["Error: m"]


def test_role_markup_is_applied_to_values_on_a_terminal() -> None:
    palette = make_console()
    console = forced_terminal(theme_from(palette, roles=("id", "path", "misc", "err")))
    error = CliError("m").prop_id("who", "abc").prop_path("where", "/p").detail("dee")
    out = capture_emit(console, lambda c: print_error(error, c))

    id_run = console.get_style("id").render("abc")
    path_run = console.get_style("path").render("/p")
    misc_run = console.get_style("misc").render("dee")
    err_run = console.get_style("err").render("Error:")

    # The id value is emitted in the id role's colour (green), distinct from the
    # path role (dim) and the err prefix (red); a role swap or drop fails here.
    assert id_run in out
    assert path_run in out
    assert misc_run in out
    assert err_run in out
    assert id_run != path_run
    assert id_run != err_run
    assert path_run != err_run


def test_detail_without_hint_has_no_trailing_or_leading_blank_line() -> None:
    error = CliError("m").prop_id("k", "v").detail("d")
    assert _render(error).splitlines() == ["Error: m", "  k: v", "d"]


def test_duplicate_prop_key_renders_last_value_in_original_slot() -> None:
    error = CliError("m").prop_id("k", "a").prop_id("k", "b")
    assert _render(error).splitlines() == ["Error: m", "  k: b"]


def test_render_error_returns_body_without_error_prefix() -> None:
    error = (
        CliError("bad [id]thing[/id]")
        .prop_id("id", "abc")
        .detail("some output")
        .hint("try [cmd]--force[/cmd]")
    )
    assert render_error(error.desc).splitlines() == [
        "bad [id]thing[/id]",
        "  id: [id]abc[/id]",
        "[misc]some output[/misc]",
        "",
        "try [cmd]--force[/cmd]",
    ]


def test_render_error_of_bare_message_is_just_the_message() -> None:
    assert render_error(CliError("boom").desc) == "boom"


def _with_cause(ex: Exception, cause: Exception) -> Exception:
    ex.__cause__ = cause
    return ex


def _with_context(ex: Exception, context: Exception) -> Exception:
    ex.__context__ = context
    return ex


class _FooError(CliError):
    pass


def _raise_with_context(*, suppress: bool) -> CliError:
    try:
        try:
            raise ValueError("root")
        except ValueError:
            if suppress:
                raise CliError("top") from None
            raise CliError("top")  # noqa: B904
    except CliError as err:
        return err


def test_cli_error_appends_single_cause() -> None:
    error = _with_cause(CliError("top"), ValueError("root"))
    assert _render(error).splitlines() == ["Error: top", "  caused by: root"]


def test_multi_level_chain_renders_one_line_per_cause_in_order() -> None:
    mid = _with_cause(RuntimeError("mid"), ValueError("root"))
    top = _with_cause(CliError("top"), mid)
    assert _render(top).splitlines() == [
        "Error: top",
        "  caused by: mid",
        "  caused by: root",
    ]


def test_implicit_context_is_surfaced_when_cause_is_none() -> None:
    error = _raise_with_context(suppress=False)
    assert _render(error).splitlines() == ["Error: top", "  caused by: root"]


def test_explicit_cause_is_preferred_over_context() -> None:
    error = _with_context(CliError("top"), RuntimeError("context"))
    error.__cause__ = ValueError("cause")
    assert _render(error).splitlines() == ["Error: top", "  caused by: cause"]


def test_cyclic_chain_terminates_without_repeats() -> None:
    a = ValueError("a")
    b = ValueError("b")
    a.__cause__ = b
    b.__cause__ = a
    error = _with_cause(CliError("top"), a)
    assert _render(error).splitlines() == [
        "Error: top",
        "  caused by: a",
        "  caused by: b",
    ]


def test_cause_str_markup_is_escaped() -> None:
    error = _with_cause(CliError("top"), ValueError("a[b]c"))
    assert _render(error).splitlines() == ["Error: top", "  caused by: a[b]c"]


def test_non_cli_error_subject_renders_chain() -> None:
    error = _with_cause(ValueError("boom"), RuntimeError("root"))
    assert _render(error).splitlines() == ["Error: boom", "  caused by: root"]


def test_no_cause_appends_nothing() -> None:
    assert _render(CliError("top")).splitlines() == ["Error: top"]


def test_suppressed_context_is_not_surfaced() -> None:
    error = _raise_with_context(suppress=True)
    assert _render(error).splitlines() == ["Error: top"]


def test_context_fallback_applies_at_every_link() -> None:
    mid = _with_context(RuntimeError("mid"), ValueError("root"))
    top = _with_cause(CliError("top"), mid)
    assert _render(top).splitlines() == [
        "Error: top",
        "  caused by: mid",
        "  caused by: root",
    ]


def test_cause_chain_follows_the_hint_block() -> None:
    error = _with_cause(
        CliError("top").prop_id("id", "abc").hint("try [cmd]--force[/cmd]"),
        ValueError("root"),
    )
    assert _render(error).splitlines() == [
        "Error: top",
        "  id: abc",
        "",
        "try --force",
        "  caused by: root",
    ]


def test_cli_error_cause_renders_via_markup_stripped_str() -> None:
    error = _with_cause(CliError("top"), CliError("root [id]x[/id]"))
    assert _render(error).splitlines() == [
        "Error: top",
        "  caused by: root x",
    ]


def test_empty_cause_falls_back_to_type_name() -> None:
    error = _with_cause(CliError("top"), ValueError())
    assert _render(error).splitlines() == ["Error: top", "  caused by: ValueError"]


def test_empty_mid_chain_cause_falls_back_to_type_name() -> None:
    error = _with_cause(
        CliError("top"), _with_cause(ValueError(), RuntimeError("root"))
    )
    assert _render(error).splitlines() == [
        "Error: top",
        "  caused by: ValueError",
        "  caused by: root",
    ]


def test_whitespace_only_cause_falls_back_to_type_name() -> None:
    error = _with_cause(CliError("top"), ValueError("   "))
    assert _render(error).splitlines() == ["Error: top", "  caused by: ValueError"]


def test_empty_cli_error_cause_falls_back_to_type_name() -> None:
    error = _with_cause(CliError("top"), CliError(""))
    assert _render(error).splitlines() == ["Error: top", "  caused by: CliError"]


def test_empty_context_cause_falls_back_to_type_name() -> None:
    error = _with_context(CliError("top"), ValueError())
    assert _render(error).splitlines() == ["Error: top", "  caused by: ValueError"]


def test_empty_cli_error_subclass_cause_falls_back_to_subclass_name() -> None:
    error = _with_cause(CliError("top"), _FooError(""))
    assert _render(error).splitlines() == ["Error: top", "  caused by: _FooError"]


def test_self_referential_cause_terminates() -> None:
    error = CliError("top")
    error.__cause__ = error
    assert _render(error).splitlines() == ["Error: top"]
