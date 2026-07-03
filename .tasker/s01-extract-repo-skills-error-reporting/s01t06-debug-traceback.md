---
id: s01t06
slug: debug-traceback
status: done
---

# Debug traceback

## Goal

When `reporter.debug` is set, an unhandled exception's full traceback prints to the reporter's own themed **stderr** console (in addition to the rendered `Error:` line on stdout). Off by default.

## Decisions & constraints

- **`ErrorReporter` owns the `debug` flag** and constructs its **own themed stderr console** (tracebacks are an error-reporting concern, not the general console's). *Rejected: factory returning a stdout+stderr+debug wrapper; passing an explicit stderr console.*
- **Framework-agnostic wiring** — the consumer flips `reporter.debug = True` from their own `--debug` option (Typer/argparse/Click/whatever); `cli-error` ships no framework callback helper.
- Traceback is emitted via Rich (`Console.print_exception()`) on the stderr console; gated entirely by `debug` (no output when false).
- Ordering mirrors repo-skills: the debug traceback is emitted as part of handling before/around the rendered error line — match repo-skills' `render_error` (which calls `console.debug_traceback()` first).

## Edge cases

- `debug` false — zero stderr output.
- `CliExit` path — no traceback (it's a clean exit, not an error), regardless of `debug`.
- Ensure stdout `Error:` line and stderr traceback don't interleave confusingly (separate streams).

## Key files

- `src/cli_error/_reporter.py` — add `debug: bool` attribute + stderr console to `ErrorReporter`; emit traceback in the `Exception` branch when `debug`.
- `tests/test_reporter.py` — assert traceback present on stderr when `debug=True`, absent when `False`, and never for `CliExit`.

## Acceptance criteria

- With `reporter.debug = True`, a generic exception yields a full traceback on the stderr console plus the `Error:` line on stdout; exit code still 1.
- With `debug = False`, no traceback is emitted.
- `CliExit` never emits a traceback.
- `uv run tox` is green.
