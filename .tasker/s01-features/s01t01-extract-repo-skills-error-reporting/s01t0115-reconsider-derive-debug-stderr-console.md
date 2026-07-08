---
id: s01t0115
slug: reconsider-derive-debug-stderr-console
status: done
---

# Debug stderr console inherits user intent (no_color + theme), not per-stream geometry

## Context

Follow-up from s01t06. `_debug_console()` builds a fresh `make_console(stderr=True)` with hardcoded defaults, so a caller who customizes their (stdout) console gets a debug traceback that shares none of it — most visibly, a `--no-color` run still emits a colored traceback. This slice derives the debug console's config from the injected console. Layers on s01t18 (the theme inheritance is what lets `debug_cmd`/`debug_output` honor a customized `misc`).

See ADR `docs/adr/0002-cli-reporter-output-facade.md`.

## Decisions

- **Inherit user *intent*, not per-stream geometry** — build the stderr console from the injected console's `no_color` and re-resolved theme roles, but NOT its width / color-system / force-terminal. Those are per-stream properties Rich detects independently; copying stdout's (e.g. piped, width 80, no color) onto a live-TTY stderr would *introduce* inconsistency. *Rejected: full derivation of width/color-system/force-terminal (corrupts stderr when streams differ); keep fully independent (leaves the real `--no-color` inconsistency unfixed).*
- **Re-resolve `DEFAULT_STYLES` roles off the injected console** — `styles={role: self._console.get_style(role) for role in DEFAULT_STYLES}` fed to `make_console`, reusing the repo's existing theme-cloning idiom (the `theme_from` helper s01t19 extracts). `get_style` returns `Style` objects, which `make_console(styles=...)` accepts. *Rejected: cloning Rich's internal theme stack (no public API, buys nothing — we only emit canonical roles).*
- **Construction stays internal; `console_err` remains the escape hatch** — honors s01t06's "reporter owns its stderr console" invariant; this is a config refinement, not a reversal. Derivation applies only when no `console_err` was injected.

## Edge cases

- `console_err` explicitly injected → skip derivation entirely, use it as-is.
- Injected console with a customized `misc` role → `debug_cmd`/`debug_output` (s01t18) must render in that custom style.
- Theme inheritance is inert for `print_exception` (Rich uses its own traceback theme) but load-bearing for the subprocess helpers — test the `no_color` path via the traceback, the theme path via a `misc`-styled debug helper.

## Key files

- `src/cli_error/_reporter.py` — `_debug_console()`.
- `src/cli_error/_console.py` — `make_console` / `DEFAULT_STYLES` (no signature change expected).
- `tests/test_reporter.py`.

## Acceptance criteria

- With an injected `no_color=True` console and no `console_err`, the debug traceback carries no ANSI escapes; a positive control with a colored console proves the flag is load-bearing.
- With an injected console overriding `misc`, a `debug_cmd`/`debug_output` line renders in the overridden style.
- Width/color-system are NOT copied from the injected console (left to Rich per-stream detection).
- `uv run tox` green.

## Out of scope

- `show_locals` (s01t16). The `print`/`debug`/subprocess API itself (s01t18).
