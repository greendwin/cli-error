from rich.console import Console
from rich.theme import Theme

from cli_error import CliError, make_console, print_error


def _render(ex: Exception) -> str:
    console = make_console()
    with console.capture() as capture:
        print_error(ex, console)
    return capture.get()


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
    theme = Theme(
        {role: palette.get_style(role) for role in ("id", "path", "misc", "err")}
    )
    console = Console(
        theme=theme,
        force_terminal=True,
        color_system="standard",
        highlight=False,
        width=80,
    )
    error = CliError("m").prop_id("who", "abc").prop_path("where", "/p").detail("dee")
    with console.capture() as capture:
        print_error(error, console)
    out = capture.get()

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
