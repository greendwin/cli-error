---
id: s01t18
slug: add-debug-gated-diagnostic-helpers
status: pending
---

# Add debug-gated diagnostic helpers to ErrorReporter (debug_traceback / debug_cmd / debug_output)

## Context

Follow-up from s01t06 (Debug traceback). In s01t06 the traceback emission was embedded **inline** in `ErrorReporter`'s `except Exception` branch (`self._debug_console().print_exception()` gated by `self.debug`). There is currently no **public** helper a consumer can call to emit debug diagnostics through the reporter's debug-gated stderr console.

The original reference repo `repo-skills` (`~/repo-skills/src/repo_skills/console.py`) already ships this family of helpers on its `Console`, each a no-op unless `debug` is set and each writing to the themed **stderr** console:

- `debug_traceback()` → `self._con_err.print_exception()` — prints the currently-handled exception's traceback. (This is the "helper for easier debug traceback printing".)
- `debug_cmd(cmd: list[str], cwd: Path)` → prints `COMMAND: <shlex-joined>` and `  cwd: <path>` in `dim`.
- `debug_output(stdout: str, stderr: str)` → prints captured subprocess output line-by-line, prefixed `  stdout:` / `  stderr:` in `dim`.

`repo_skills.errors.render_error` calls `console.debug_traceback()` first, and CLI subprocess call sites call `debug_cmd` / `debug_output` around invocations.

## Goal

Embed the same mechanics as reusable **public** methods on `ErrorReporter`, so consumers can sprinkle debug diagnostics that only appear on stderr when `reporter.debug` is set:

- `reporter.debug_traceback()` — emit the currently-handled exception traceback to the reporter's stderr console when `debug` (no-op otherwise). Refactor the s01t06 inline emission in the `except Exception` branch to call this helper (single source of truth; keep behavior identical — must stay inside the active `except` block per the existing invariant).
- `reporter.debug_cmd(cmd, cwd)` and `reporter.debug_output(stdout, stderr)` — debug-gated stderr diagnostics for subprocess logging, escaping args and using the `misc`/`dim` style role (match this library's theme roles rather than hardcoded `[dim]`).

## Decisions to confirm during planning

- Which helpers are in scope — just `debug_traceback`, or the full trio. (`debug_cmd`/`debug_output` are subprocess-oriented; confirm they belong in a CLI-error library vs. a consumer concern.)
- Escaping: reuse this repo's escape/markup-template conventions (see CONTEXT.md "Format template") rather than repo-skills' ad-hoc `[dim]` markup.
- Keep the lazy private stderr console from s01t06; these helpers route through it.

## Acceptance criteria

- `ErrorReporter` exposes the agreed public debug helper(s); each is a no-op when `debug` is false and writes to the themed stderr console when true.
- The s01t06 inline traceback emission is refactored to use `debug_traceback()` (no behavior change; exit codes and stream separation preserved).
- Behavior-level tests: each helper emits on stderr only when `debug=True`, is silent when false, and escapes its arguments.
- `uv run tox` green.
