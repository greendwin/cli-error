---
id: s01t15
slug: reconsider-derive-debug-stderr-console
status: pending
---

# Reconsider: derive debug stderr console config from injected console

## Context

Follow-up from s01t06 (Debug traceback). Surfaced by the `general` code-review lens.

`ErrorReporter` currently builds its **own** themed stderr console via `make_console(stderr=True)`, hardcoding default width/color-system/`no_color`/`force_terminal`/file target. A caller who customizes the injected (stdout) `console` gets a debug traceback that shares none of that configuration, so debug output can look inconsistent with the rest of the CLI in redirected/non-TTY contexts (e.g. differing width or color handling).

## ⚠️ Tension with s01t06 decision

s01t06 explicitly decided the reporter **owns and constructs its own** themed stderr console — *rejecting* "factory returning a stdout+stderr+debug wrapper" and "passing an explicit stderr console". This follow-up partially revisits that: it would derive the stderr console's *options* (not inject the console object) from the injected one so it inherits width/color handling. Evaluate whether inheriting `console.options`-derived settings is compatible with the "own console" decision, or whether the decision should stand as-is.

## Possible approach

Build the stderr console from the injected console's relevant options (e.g. width, color system, `no_color`, `force_terminal`) while keeping construction internal, rather than always a fresh default `make_console(stderr=True)`.

## Acceptance criteria

- Decision recorded (adopt vs. keep independent, with rationale; update CONTEXT.md/ADR if it changes the documented decision).
- If adopted: debug traceback inherits the injected console's width/color handling; behavior-level test covers a non-default (e.g. narrow/no-color) console.
- `uv run tox` green.
