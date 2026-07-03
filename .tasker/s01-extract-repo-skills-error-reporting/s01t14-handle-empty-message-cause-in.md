---
id: s01t14
slug: handle-empty-message-cause-in
status: done
---

# Handle empty-message cause in cause-chain rendering

## Context

`print_error`'s cause-chain walk (in `src/cli_error/_errors.py`) renders each cause as `  caused by: {str(cause)}`. When a cause's `str()` is empty — a bare `ValueError()`, or a `CliError("")` — this produces a dead `  caused by: ` line (trailing space, no content). Surfaced as a nit by the `thermo-nuclear` and `general` review lenses during dev-loop of s01t05, and deferred because fixing it changes observable output and so needs a deliberate product decision plus its own test rather than a behavior-preserving refactor. Goal: make every empty-message error line informative instead of blank.

## Decisions

- **Empty-message cause → type-name fallback** — when a cause's message is empty, render the exception's class name (`  caused by: ValueError`) instead of a blank line. *Rejected: skipping the link (mis-parents any deeper cause onto the wrong error); emitting a bare `  caused by:` label (says "a cause exists" but not what — worst of both worlds).*
- **Name form = `type(exc).__name__`** — the bare class name, matching the short, un-namespaced style of every other rendered line. *Rejected: `__qualname__` (only differs for rare nested classes) and fully-qualified `module.Class` (noise for a terminal-facing diagnostic).*
- **Trigger = `not str(exc).strip()`** — whitespace-only messages count as empty and get the fallback too, killing the whole class of blank/dead lines rather than only the exact-empty case.
- **Uniform trigger on cause links** — the fallback fires for any exception type on a cause link, `CliError` subclasses included; an empty `CliError` cause is as uninformative as a bare `ValueError()`, and keeping one branch keeps the walk predictable.
- **Fallback extends to top-level non-`CliError` subjects** — a top-level `ValueError()` renders `Error: ValueError` (currently the dead `Error: `). A top-level `CliError("")` is exempt and still renders `Error:` — its empty message is the author's deliberate primary text and is respected (existing `test_empty_message_still_prints_error_prefix` unchanged).
- **Positional asymmetry for empty `CliError` is intended** — the same empty `CliError` prints `Error:` at the top level but `  caused by: CliError` as a cause link. Governing principle: the author's top-level `CliError` message is sacred; every other empty message, including a wrapped `CliError`, gets a type name. A top-level error is authored; a cause is incidental context.

## Edge cases

- Whitespace-only message (`ValueError("   ")`, `ValueError("\n")`) — treated as empty, gets the type name; the original whitespace is discarded, not rendered.
- Empty cause in the middle of a chain (`top → ValueError() → root`) — the fallback keeps the link present so the deeper `root` still renders beneath it; it must not be mis-parented onto `top`.
- Empty `CliError` cause — renders its class name (`CliError`, or a consumer subclass name), not blank.
- Top-level `CliError("")` — must remain exempt: still renders `Error:` (no type name).
- The fallback text still passes through `escape()` at each site (harmless for a class name, keeps both call sites uniform).

## Key files

- `src/cli_error/_errors.py` — `print_error`: the cause-walk loop and the non-`CliError` `else` branch. Add one small helper (e.g. `str(exc)` if `str(exc).strip()` else `type(exc).__name__`) called before escaping at both sites; leave the `CliError` branch (`render_error(ex.desc)`) untouched.
- `tests/test_render.py` — behavior tests via the existing `_render` / `_with_cause` / `_with_context` helpers.

## Acceptance criteria

- `_with_cause(CliError("top"), ValueError())` → `["Error: top", "  caused by: ValueError"]`.
- Mid-chain `top → ValueError() → RuntimeError("root")` → `["Error: top", "  caused by: ValueError", "  caused by: root"]`.
- Whitespace-only cause `ValueError("   ")` → `["Error: top", "  caused by: ValueError"]`.
- Empty `CliError` cause `_with_cause(CliError("top"), CliError(""))` → `["Error: top", "  caused by: CliError"]`.
- Top-level `ValueError()` → `["Error: ValueError"]`.
- Guard: top-level `CliError("")` still renders `Error:` (existing test unchanged).
- `uv run tox` green.

## Open questions

- None outstanding — the design tree is fully resolved.

## Out of scope

- Reworking how top-level `CliError("")` renders (stays `Error:` — deliberately exempt).
- Fully-qualified or module-qualified cause names — only revisit if a real ambiguity case appears.
- Any change to non-empty cause rendering, the `__suppress_context__` handling, or the layout/ordering settled in s01t05.
