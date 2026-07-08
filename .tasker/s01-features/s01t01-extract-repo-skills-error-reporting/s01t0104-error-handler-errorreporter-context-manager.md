---
id: s01t0104
slug: error-handler-errorreporter-context-manager
status: done
---

# Error handler (ErrorReporter context manager)

## Goal

`ErrorReporter(console)` is the single integration point a CLI constructs once in `main()`. Its `handler()` context manager catches `CliExit` → print the (markup-capable) message through the themed stdout console + `SystemExit(0)`, and catches any other `Exception` → `render_error(ex, console)` + `SystemExit(1)`.

## Decisions & constraints

- **`ErrorReporter(console)` single integration point** — constructed once, owns the console; no global singleton, no per-call console passing. *Rejected: `error_handler(console)` free function passing console everywhere; a module-level "current console".*
- **Handler semantics** — `CliExit` caught **before** the generic `Exception` branch: print `ex.message` through the reporter's stdout console (message is trusted markup, like a template with no args), then `raise SystemExit(0)`. Any other `Exception`: `render_error` then `raise SystemExit(1)`.
- **Framework-agnostic** — Rich only, no Typer/Click dependency; the consumer wires their own `--debug`/entrypoint. (The `debug` flag + stderr traceback arrive in a later slice; this slice does not implement `--debug`.)
- Export `ErrorReporter` from `__init__`.

## Edge cases

- `CliExit` with empty message — still exits 0 (may print an empty line or nothing; decide + cover).
- Exception raised while already inside the handler body vs. re-raised `SystemExit` — ensure `SystemExit` from within isn't re-wrapped.
- `KeyboardInterrupt`/`SystemExit` are `BaseException`, not `Exception` — must pass through untouched.

## Key files

- `src/cli_error/_reporter.py` — `ErrorReporter` class with `handler()` (contextmanager) using `render_error`.
- `src/cli_error/__init__.py` — export `ErrorReporter`.
- `tests/test_reporter.py` — assert exit code (via `pytest.raises(SystemExit)`) and captured output for CliExit (0) and generic error (1); assert `KeyboardInterrupt` propagates.

## Acceptance criteria

- `with ErrorReporter(make_console()).handler(): raise CliExit("done")` prints `done` and raises `SystemExit` with code 0.
- Same with `raise CliError("boom")` renders `Error: boom` and exits code 1.
- Same with a plain `raise ValueError("x")` renders `Error: x` and exits code 1.
- `KeyboardInterrupt` is not swallowed.
- `uv run tox` is green.
