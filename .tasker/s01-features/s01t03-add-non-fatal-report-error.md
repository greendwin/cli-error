---
id: s01t03
slug: add-non-fatal-report-error
status: done
---

# Add non-fatal report_error primitive to CliReporter

## Context

`cli-error` must expose a non-fatal error-rendering primitive so `repo_skills` can render per-item failures mid-loop (no `SystemExit`), sharing exactly one render path with the fatal `handler()`. This is the prerequisite `cli-error` release ("slice 1") that must land before the `repo_skills` migration begins. Today `handler()` inlines `debug_traceback()` + `print_error()`; a loop site would otherwise have to re-implement that render, losing the `--debug` traceback or drifting from the handler. (The Python 3.10 floor from the original request already shipped as a sibling task and is not part of this work.)

## Decisions

- **Add `CliReporter.report_error(ex)` — non-fatal render** — renders `debug_traceback()` + `print_error(ex, self.console)` with no exit. It is the mirror of `handler()`: non-fatal reporting is the reporter's own job. *Rejected: leaving loop sites to re-implement the render (re-introduces the exact drift the primitive prevents) or to drop the `--debug` traceback.*
- **Refactor `handler()` to delegate to `report_error`** — the `except Exception` arm calls `self.report_error(ex)` instead of inlining `debug_traceback()` + `print_error()`, so the fatal and non-fatal paths share one primitive.
- **`SystemExit` stays in `handler()`, never in `report_error`** — `handler()` keeps `SystemExit` as the only thing it adds over rendering; it is the error→exit-code boundary and is orthogonal to the non-fatal loop case (a context-manager handler is inherently fatal-shaped; loops call `report_error` directly).

## Edge cases

- `report_error` called **outside** an `except` block: `debug_traceback()` already no-ops when `sys.exc_info()[0] is None`, and `print_error` just renders the passed exception — must not raise.
- `debug` flag off: `report_error` emits no traceback (only the rendered error via `print_error` to stdout console), matching the handler's existing behaviour.
- `report_error` must **not** raise `SystemExit` or any exit — calling it twice in a loop must render twice and return normally each time.
- `handler()` behaviour must be unchanged after delegation: `CliExit` → print + exit 0; other `Exception` → traceback (when debug) + rendered error + exit 1. The `raise SystemExit(1) from None` (suppressed context) must be preserved.

## Key files

- `src/cli_error/_reporter.py` — add `report_error`; rewrite `handler()`'s `except Exception` arm to delegate.
- `src/cli_error/__init__.py` — confirm `CliReporter` is exported (no new symbol needed; `report_error` is a method).
- `tests/test_reporter.py` — new tests for `report_error`; existing `handler()` tests must stay green.

## Acceptance criteria

- `CliReporter.report_error(ex)` renders the error message + cause chain to the stdout console and, when `debug` is set, the traceback to the stderr console — with no `SystemExit`.
- With `debug` unset, `report_error` renders the error but emits nothing to the debug/stderr console.
- Calling `report_error` outside an active exception does not raise.
- After refactor, `handler()` produces byte-for-byte the same output and exit codes as before (regression tests pass): `CliExit` → exit 0, other exceptions → exit 1 with the same rendered error.
- `uv run tox` is green across all environments.

## Open questions

- **Release version** — kept as-is (`0.1.2`); bump deferred to a later release step.

## Out of scope

- **Progress spinner `running()`/`finish()` + eoln flushing** — stays in a `repo_skills` `Reporter(CliReporter)` subclass (app-specific UI, not a general error-lib concern). Promote later only if it proves generic.
