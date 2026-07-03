from rich.console import Console
from rich.style import Style
from rich.theme import Theme

from cli_error import DEFAULT_STYLES, make_console, make_theme

_ROLES = ("id", "data", "path", "cmd", "misc", "warn", "err")


def _forced(theme: Theme, *, no_color: bool = False) -> Console:
    """A forced-ANSI console carrying ``theme``; ``no_color`` strips escapes."""
    return Console(
        theme=theme,
        force_terminal=True,
        color_system="standard",
        no_color=no_color,
        highlight=False,
        width=80,
    )


def _terminal(theme_source: Console) -> Console:
    """A forced-ANSI console carrying ``theme_source``'s resolved roles."""
    return _forced(Theme({role: theme_source.get_style(role) for role in _ROLES}))


def _capture(console: Console, markup: str) -> str:
    with console.capture() as capture:
        console.print(markup)
    return capture.get()


def test_default_console_maps_roles_to_canonical_styles() -> None:
    console = make_console()
    for role, spec in DEFAULT_STYLES.items():
        assert console.get_style(role) == Style.parse(spec)


def test_default_roles_render_as_distinct_ansi_runs() -> None:
    console = _terminal(make_console())
    out = _capture(console, "[id]a[/id][path]b[/path][err]c[/err]")

    id_run = console.get_style("id").render("a")
    path_run = console.get_style("path").render("b")
    err_run = console.get_style("err").render("c")

    assert id_run in out
    assert path_run in out
    assert err_run in out
    assert id_run != path_run
    assert id_run != err_run
    assert path_run != err_run


def test_none_and_empty_styles_are_identical_to_defaults() -> None:
    default = make_console()
    none_styles = make_console(styles=None)
    empty_styles = make_console(styles={})

    for role in _ROLES:
        expected = default.get_style(role)
        assert none_styles.get_style(role) == expected
        assert empty_styles.get_style(role) == expected


def test_overriding_one_role_leaves_the_others_at_defaults() -> None:
    default = make_console()
    console = make_console(styles={"id": "bold green"})

    assert console.get_style("id") == Style.parse("bold green")
    assert console.get_style("id") != default.get_style("id")
    for role in _ROLES:
        if role == "id":
            continue
        assert console.get_style(role) == default.get_style(role)


def test_unknown_role_key_is_added_and_never_raises() -> None:
    console = make_console(styles={"custom": "magenta"})
    assert console.get_style("custom") == Style.parse("magenta")
    # An undefined role degrades to plain text on a colour terminal, no error.
    terminal = _terminal(make_console())
    assert _capture(terminal, "[undefined]x[/undefined]") == "x\n"


def test_no_color_suppresses_ansi_on_a_forced_terminal() -> None:
    # Positive control: an identical forced terminal DOES emit ANSI, proving the
    # no_color flag below is load-bearing rather than vacuously satisfied.
    coloured = _forced(make_theme(), no_color=False)
    plain = _forced(make_theme(), no_color=True)

    coloured_out = _capture(coloured, "[id]x[/id]")
    plain_out = _capture(plain, "[id]x[/id]")

    assert "\x1b" in coloured_out
    assert "\x1b" not in plain_out
    assert plain_out == "x\n"


def test_no_color_console_exposes_flag_and_renders_plain_text() -> None:
    console = make_console(no_color=True)
    out = _capture(console, "[id]x[/id]")

    assert out == "x\n"
    assert "\x1b" not in out
    assert console.no_color is True


def test_stderr_routes_output_to_stderr() -> None:
    assert make_console(stderr=True).stderr is True
    assert make_console().stderr is False


def test_default_styles_is_public_and_has_the_seven_roles() -> None:
    assert set(DEFAULT_STYLES) == set(_ROLES)
    assert DEFAULT_STYLES == {
        "id": "green",
        "data": "cyan",
        "path": "dim",
        "cmd": "blue",
        "misc": "dim",
        "warn": "yellow",
        "err": "red",
    }


def test_make_theme_is_attachable_to_a_plain_console() -> None:
    console = _forced(make_theme())
    out = _capture(console, "[id]x[/id]")
    assert console.get_style("id").render("x") in out


def test_make_theme_merges_overrides_over_defaults() -> None:
    theme = make_theme(styles={"id": "bold green"})
    assert theme.styles["id"] == Style.parse("bold green")
    assert theme.styles["data"] == Style.parse("cyan")


def test_override_value_may_be_a_prebuilt_style_object() -> None:
    override = Style(color="magenta")
    console = make_console(styles={"id": override})

    assert console.get_style("id") == override
    assert _capture(console, "[id]x[/id]") == "x\n"
