---
id: s01t07
slug: console-creation-with-style-overrides
status: pending
---

# Console creation with style overrides

## Goal

`make_console` becomes customizable: `make_console(styles={"id": "bold green"})` overrides a single role while keeping the rest of `DEFAULT_STYLES`; `no_color=True` produces an effectively plain console; the derived Rich `Theme` is exposed so a consumer can attach it to a pre-existing console instead of using the factory.

## Decisions & constraints

- **Merging factory over `DEFAULT_STYLES`** — `make_console(*, styles=None, no_color=False, ...)` builds the theme from `DEFAULT_STYLES` updated with the caller's `styles`, so overriding one role doesn't force redeclaring the palette. *Rejected: exposing only a full `Theme` that must be redeclared wholesale.*
- **Style roles + defaults** (canonical, semantic even when colors coincide): `id`=green, `data`=cyan, `path`=dim, `cmd`=blue, `misc`=dim, `warn`=yellow, `err`=red.
- **Expose `DEFAULT_STYLES`** (a `dict[str, str]`) and the derived `Theme` from the public API — deferred to this slice precisely because slices 1–6 only need the defaults.
- **`no_color`** — plain output (Rich `no_color`/`color_system=None` on both the stdout and, where relevant, stderr consoles).
- These params are additive to the param-free `make_console()` from the types slice — the no-arg call must keep working.

## Edge cases

- `styles={}` or `styles=None` — identical to defaults.
- Overriding one role leaves all others intact.
- Unknown role key in `styles` — added to the theme (harmless; degrades to plain if never used) — decide + cover.
- `no_color=True` still renders text (just unstyled), never raises.

## Key files

- `src/cli_error/_console.py` — add `DEFAULT_STYLES`, merging logic, `styles=`/`no_color=` params, and expose the derived `Theme`.
- `src/cli_error/__init__.py` — export `make_console`, `DEFAULT_STYLES` (and the `Theme` accessor).
- `tests/test_console.py` — override-one-role, no_color-strips, defaults-unchanged, Theme-exposed.

## Acceptance criteria

- `make_console()` (no args) still returns a defaults-themed console.
- `make_console(styles={"id": "bold green"})` changes `id` and leaves `data`/`path`/... at defaults.
- `make_console(no_color=True)` renders `[id]x[/id]` as plain `x` with no ANSI.
- `from cli_error import DEFAULT_STYLES` works and contains all seven roles; the derived `Theme` is attachable to a plain `rich.console.Console`.
- `uv run tox` is green.
