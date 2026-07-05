# CliReporter is the CLI output façade

**Status:** accepted

## Context

`cli-error` began with an `ErrorReporter`: a single object a CLI constructs once
in `main()` that renders errors and owns the error-handling context manager. In
practice a CLI needs a themed console for more than errors — ordinary output,
and debug diagnostics (a traceback, ad-hoc trace lines, subprocess command and
captured output). Without a home for those, each consumer re-derives a themed
stderr console and re-implements the `--debug` gate.

`ErrorReporter` already owned the two things those diagnostics need: the `--debug`
flag and a themed stderr console (added for the debug traceback). Growing a
second, parallel output object would split that ownership.

## Decision

- **One façade, renamed.** `ErrorReporter` becomes **`CliReporter`**: the single
  integration point for a CLI's terminal output. It prints normal output
  (`print`), renders errors and exposes `handler()`, and emits debug diagnostics.
  Pre-1.0 with no external consumers, so this is a hard rename — no alias.
- **Debug diagnostics live on stderr and are `debug`-gated.** `debug_traceback()`,
  a general `debug(template, **args)` line, and the subprocess-oriented
  `debug_cmd(cmd, cwd)` / `debug_output(stdout, stderr)` all route through the
  reporter's themed **stderr** console and are silent no-ops unless `debug` is
  set. Stderr keeps diagnostics from polluting machine-readable stdout; the
  single gate means a consumer flips one flag. The subprocess pair are thin
  wrappers over `debug()`, styled `misc`, with all arguments escaped via the
  format-template contract (ADR 0001) — never hardcoded `[dim]` markup.
- **`print`/`debug` take `(template, /, *, end="\n", **args)`.** `template` is
  positional-only and `end` keyword-only, so neither collides with a caller's
  format-placeholder names.
- **`show_locals` is an opt-in, default off.** Frame locals are the most useful
  debug signal but can leak secrets (tokens, connection strings) to stderr; a
  reusable error library must not enable that silently. A constructor flag gates
  both the automatic `handler()` traceback and `debug_traceback()`, which also
  accepts a per-call override.
- **The debug console inherits user *intent*, not per-stream geometry.** When no
  `console_err` is injected, the reporter builds its stderr console from the
  injected console's `no_color` and re-resolved theme roles — but *not* its
  width / color-system / force-terminal, which Rich detects per stream. Copying
  stdout's detected geometry onto stderr would corrupt output when the streams
  differ (piped stdout, live-TTY stderr). Inheriting the theme matters for
  `debug_cmd`/`debug_output`, which emit `misc`-styled markup; it is inert for
  `print_exception`, which uses Rich's own traceback theme.

## Considered options

- **Keep `ErrorReporter` narrow; a separate output helper** — rejected: splits
  ownership of the `--debug` flag and the themed stderr console across two
  objects the consumer must wire together.
- **Keep the debug stderr console fully independent** (the s01t06 framing) —
  superseded: independent construction stays, but its config now derives from
  the injected console so a `--no-color` run doesn't emit a colored traceback.
  `console_err` remains the escape hatch for callers needing full control.
- **Force `misc` on the generic `debug()`** — rejected: `debug()` is the
  unopinionated primitive (parallel to `print`); auto-styling would make a
  `[warn]` debug line impossible. Only the subprocess wrappers own dim styling.
- **`show_locals` always-on under `debug`** — rejected: silent info-leak risk in
  a library adopted by arbitrary CLIs.

## Consequences

- The reporter is the one place that owns terminal output, so theming, stream
  routing, and the `--debug` gate stay uniform across every tool that adopts it.
- Adding subprocess-shaped helpers (`debug_cmd`/`debug_output`) commits a small
  amount of public surface to a subprocess opinion; they are isolated wrappers
  over `debug()`, so a consumer that never shells out simply ignores them.
- The debug traceback now respects a `--no-color` invocation without the caller
  injecting a `console_err`.
