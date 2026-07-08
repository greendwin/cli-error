---
id: s01t0116
slug: optionally-show-locals-in-debug
status: done
---

# Add opt-in show_locals to the debug traceback

## Context

Follow-up from s01t06. The debug traceback runs `print_exception()` with `show_locals=False`. Per-frame locals are often the most useful debug signal, but this is a reusable library adopted by arbitrary CLIs — turning locals on by default would dump whatever is in scope (tokens, passwords, connection strings) to stderr on every `--debug` error. This slice adds a deliberate opt-in. Layers on s01t18's public `debug_traceback()`.

See ADR `docs/adr/0002-cli-reporter-output-facade.md`.

## Decisions

- **Opt-in, default off** — locals are high-value but a genuine info-leak risk; default-off preserves today's behavior for everyone who doesn't ask. *Rejected: always-on under `debug` (silent leak); keep off entirely (loses a high-value debug signal).*
- **Constructor flag `show_locals: bool = False` on `CliReporter`** — honored by BOTH the automatic `handler()` traceback and `debug_traceback()`. The automatic path is where tracebacks usually originate, so the toggle must be reachable there. Name mirrors Rich's own `print_exception(show_locals=...)` param — no invented `debug_locals`. *Rejected: a flag only on `debug_traceback()` (can't reach the automatic path).*
- **Per-call override `debug_traceback(*, show_locals: bool | None = None)`** — `None` defers to the instance flag; an explicit bool overrides for that call.

## Edge cases

- `show_locals=None` on `debug_traceback` → use the instance flag.
- Both `handler()` auto-emission and explicit `debug_traceback()` must respect the instance flag.
- Interaction with s01t15's derived console: `show_locals` is orthogonal to console config — it's a `print_exception` param, not a console setting.

## Key files

- `src/cli_error/_reporter.py` — constructor flag, `handler()`, `debug_traceback()`.
- `tests/test_reporter.py`.

## Acceptance criteria

- Default (`show_locals` unset) → traceback contains no frame-locals table.
- `CliReporter(..., show_locals=True)` → a chained/simple error through `handler()` under `debug=True` shows frame locals in captured stderr.
- `debug_traceback(show_locals=True)` overrides an instance default of False; `show_locals=None` defers to the instance flag.
- `uv run tox` green.

## Out of scope

- Verbosity levels beyond the single boolean. Console config inheritance (s01t15).
