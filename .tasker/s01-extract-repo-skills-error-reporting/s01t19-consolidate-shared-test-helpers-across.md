---
id: s01t19
slug: consolidate-shared-test-helpers-across
status: pending
---

# Consolidate shared test helpers across test modules

## Goal

Extract the console-test idioms repeated across `tests/test_console.py`, `tests/test_render.py`, `tests/test_errors.py`, and `tests/test_reporter.py` into a single shared module (`tests/conftest.py` or `tests/_helpers.py`), removing cross-module duplication.

## Scope (surfaced as a delayed refactor item during s01t07)

- **`forced_terminal(theme, *, no_color=False) -> Console`** — the `Console(..., force_terminal=True, color_system=\"standard\", highlight=False, width=80)` construction currently duplicated (e.g. `_forced` in test_console.py and the inline builder in test_render.py).
- **`theme_from(console, roles=_ROLES) -> Theme`** — build a Theme by re-resolving roles off an already-themed console (test_console.py `_terminal` and test_render.py both do this; test_render hard-codes a partial role subset).
- **`capture(console, markup) -> str`** — the `with console.capture() as c: console.print(...); return c.get()` idiom repeated in test_console.py (`_capture`), test_render.py, test_errors.py, test_reporter.py.
- **derived `_ROLES`** — define the iteration role list as `tuple(DEFAULT_STYLES)` in the shared helper (leave the deliberate exact-dict/set palette-pin assertion in `test_default_styles_is_public_and_has_the_seven_roles` untouched as the contract guard).

## Constraints

- Behavior-preserving; keep all assertion values identical.
- `uv run tox` green.
- Typed signatures, top-level imports only, monkeypatch only.
