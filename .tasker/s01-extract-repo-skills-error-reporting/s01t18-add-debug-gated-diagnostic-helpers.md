---
id: s01t18
slug: add-debug-gated-diagnostic-helpers
status: pending
---

# Rename ErrorReporter to CliReporter and grow it into the CLI output façade

## Context

Follow-up from s01t06 (Debug traceback). The reporter already owns the two things a CLI's debug diagnostics need — the `--debug` flag and a themed stderr console — but exposes no public way to emit diagnostics through them, and covers only errors. This slice reframes the object from an *error* reporter into the CLI's single **output façade**: it prints normal output, renders errors (via the existing `handler()`), and emits debug-gated diagnostics. This is the structural tracer bullet; s01t15/s01t16 layer onto its `debug_traceback()`, and s01t15's theme inheritance exists to serve the subprocess helpers here.

See ADR `docs/adr/0002-cli-reporter-output-facade.md` and the `CliReporter` / `Debug diagnostic` glossary entries.

## Decisions

- **Hard rename `ErrorReporter` → `CliReporter`** — pre-1.0, no external consumers, so an alias is dead weight and a second name to explain. Update source, `__all__`, tests, `CONTEXT.md`, ADR. *Rejected: keep a deprecation alias (no consumers to protect).*
- **`print(template, /, *, end="\n", **args)`** — routes to the stdout console via `render_template` (trusted template + escaped args); not debug-gated. `template` positional-only and `end` keyword-only so neither collides with a caller's format-placeholder names. *Rejected: `**args` then `end` (SyntaxError); dropping `end`; namespacing as `_end`.*
- **`debug(template, /, *, end="\n", **args)`** — same signature shape and template contract as `print`, but routes to the reporter's themed **stderr** console and is a silent no-op unless `debug` is set. Renders the trusted template **unchanged** — no forced styling — so a consumer can emit e.g. a `[warn]` debug line. *Rejected: auto-wrap `debug` output in `misc`/dim (would make non-dim debug lines impossible).*
- **`debug_traceback()`** — emits the currently-handled exception traceback to the stderr console when `debug`, no-op otherwise. Refactor the s01t06 inline emission in the `except Exception` branch to call this (single source of truth, behavior identical). MUST stay inside the active `except` block — `print_exception()` reads `sys.exc_info()`.
- **Subprocess wrappers are thin layers over `debug()`** — `debug_cmd(cmd: list[str], cwd: Path | None = None)` emits `[misc]COMMAND: {cmd}[/misc]` (via `shlex.join`) and, only when `cwd` is given, `[misc]  cwd: {cwd}[/misc]`. `debug_output(stdout: str, stderr: str)` emits each non-empty stream as a `  stdout:` / `  stderr:` header line followed by the captured text as one escaped `misc` block (internal newlines preserved, trailing whitespace `rstrip`ped, empty/whitespace-only streams skipped). Both pass untrusted args through `debug()`'s escaped-arg contract — never hardcoded `[dim]` markup, never inlined. *Rejected: per-line prefixing (bloats multi-line logs); required `cwd` (not every subprocess sets one); shipping only `debug_traceback` (user chose full trio for reference-repo parity).*

## Edge cases

- `debug_traceback()` called outside an active exception → `print_exception()` has nothing to render; keep it inside the `except` per the s01t06 invariant.
- A format-placeholder legitimately named `template` or `end` — prevented by positional-only / keyword-only.
- `debug_output` with both streams empty → emits nothing.
- Untrusted cmd parts / cwd / captured output containing markup → escaped by `render_template`.
- All `debug*` helpers must be silent no-ops when `debug` is false; `print` always emits.

## Key files

- `src/cli_error/_reporter.py` — the class, rename, new methods.
- `src/cli_error/__init__.py` — `__all__` + import (`ErrorReporter` → `CliReporter`).
- `tests/test_reporter.py` — rename references; add helper tests.
- `CONTEXT.md`, `docs/adr/0001-*`, `docs/adr/0002-*` — already updated during grill.

## Acceptance criteria

- `CliReporter` replaces `ErrorReporter` everywhere; importing `ErrorReporter` fails.
- `print(...)` emits on stdout with escaped args and honors `end`.
- `debug(...)` emits on stderr only when `debug=True`, silent when false, renders the trusted template unchanged with escaped args.
- `debug_traceback()` emits the handled traceback on stderr under `debug`, no-op otherwise; the `handler()` path is refactored to call it with no behavior change (exit codes, stream separation preserved).
- `debug_cmd` / `debug_output` emit `misc`-styled diagnostics on stderr only under `debug`, escape their arguments, `cwd` line omitted when `None`, empty streams skipped.
- `uv run tox` green.

## Out of scope

- `show_locals` (s01t16) and debug-console config inheritance (s01t15) — separate slices layered on this one.
