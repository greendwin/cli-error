---
id: s01t16
slug: optionally-show-locals-in-debug
status: pending
---

# Optionally show locals in debug traceback

## Context

Follow-up from s01t06 (Debug traceback). Surfaced by the `general` code-review lens.

The debug traceback is emitted via Rich `Console.print_exception()` with defaults (`show_locals=False`). For a feature whose sole purpose is debugging, per-frame variable values are often the most useful part; without them the `debug` flag yields only a standard traceback.

## Possible approach

Consider `print_exception(show_locals=True)` — either unconditionally under `debug`, or behind a separate opt-in (e.g. a `debug_locals`/verbosity level) so consumers can choose. Weigh the risk of leaking sensitive values into stderr output.

## Acceptance criteria

- Decision recorded (always-on vs. opt-in vs. keep off, with rationale — note the info-leak trade-off).
- If enabled: a behavior-level test asserts frame locals appear in the captured stderr traceback.
- `uv run tox` green.
