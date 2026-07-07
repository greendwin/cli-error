---
id: s01t19
slug: consolidate-shared-test-helpers-across
status: done
---

# Consolidate shared test helpers into tests/_helpers.py

## Goal

Extract the console-test idioms duplicated across `tests/test_console.py`, `tests/test_render.py`, `tests/test_errors.py`, and `tests/test_reporter.py` into a single shared module, removing cross-module duplication.

## Decisions

- **`tests/_helpers.py`, not `conftest.py`** — the extracted items are plain functions and a constant, not pytest fixtures; an imported module is the honest home and satisfies the "top-level imports only" constraint. *Rejected: `conftest.py` (fixture-discovery territory) and promoting per-module scaffolding into it (couples unrelated modules).*
- **Scope limited to genuinely cross-module console idioms** — leave module-local scaffolding in place: `test_reporter.py`'s `console`/`reporter`/`debug_reporter` fixtures and `run_handler`, `test_render.py`'s `_render`, `test_errors.py`'s `PROP_METHODS`.
- **`_ROLES = tuple(DEFAULT_STYLES)`** — define the iteration role list as derived, not a hardcoded 7-tuple. `theme_from`'s `roles` param defaults to it.
- **Leave the exact-dict/set palette-pin assertion** in `test_default_styles_is_public_and_has_the_seven_roles` untouched as the contract guard.

## Scope (the four extractions)

- `forced_terminal(theme, *, no_color=False) -> Console` — the `Console(..., force_terminal=True, color_system="standard", highlight=False, width=80)` construction duplicated as `_forced` (test_console.py) and inline in test_render.py.
- `theme_from(console, roles=_ROLES) -> Theme` — build a Theme by re-resolving roles off an already-themed console (`_terminal` in test_console.py; the hard-coded partial-role builder in test_render.py).
- `capture(console, markup) -> str` — the `with console.capture() as c: console.print(...); return c.get()` idiom in all four modules.
- `_ROLES` — `tuple(DEFAULT_STYLES)` in the shared helper.

## Constraints

- Behavior-preserving; keep every assertion value identical.
- Typed signatures, top-level imports only, monkeypatch only, no `type: ignore`.
- `uv run tox` green.

## Key files

- `tests/_helpers.py` — new.
- `tests/test_console.py`, `tests/test_render.py`, `tests/test_errors.py`, `tests/test_reporter.py` — import from it, drop the local duplicates.

## Acceptance criteria

- `tests/_helpers.py` exposes `forced_terminal`, `theme_from`, `capture`, `_ROLES`.
- The four test modules import these instead of re-defining them; no behavior/assertion changes.
- `test_render.py` no longer hard-codes a partial role subset — it uses `theme_from`'s default `_ROLES`.
- `uv run tox` green.

## Out of scope

- Consolidating reporter-specific `run_handler` / fixtures.
