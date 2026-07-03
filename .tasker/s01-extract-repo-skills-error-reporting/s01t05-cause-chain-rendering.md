---
id: s01t05
slug: cause-chain-rendering
status: pending
---

# Cause chain rendering

## Goal

Rendered errors append the cause chain: for each linked cause, a `  caused by: <cause>` line, walking `__cause__` (falling back to `__context__`), with each cause's `str()` escaped, stopping on cycles via `id()` dedup.

## Decisions & constraints

- **Extends `render_error`** — after the message/props/detail/hint, walk `cause = ex.__cause__ or ex.__context__`; while `cause` is not `None` and `id(cause)` unseen: print `  caused by: {escape(str(cause))}`, record `id(cause)`, advance. Mirrors repo-skills behavior exactly.
- Applies to both `CliError` and non-`CliError` exceptions (it's a property of `render_error`, not the type).

## Edge cases

- No cause — nothing appended.
- Cyclic `__cause__`/`__context__` — dedup by `id()` prevents infinite loop.
- Cause `str()` containing markup characters — escaped.
- `raise X from Y` (sets `__cause__`) vs. implicit chaining (`__context__`) — both surfaced, `__cause__` preferred.

## Key files

- `src/cli_error/_reporter.py` — extend `render_error` with the chain walk.
- `tests/test_render.py` — add chained-exception cases (explicit `from`, implicit context, cyclic guard).

## Acceptance criteria

- `raise CliError("top") from ValueError("root")` renders the error then `  caused by: root`.
- A multi-level chain renders one `caused by:` line per distinct cause, in order.
- A constructed cycle terminates (no hang, no duplicate lines).
- `uv run tox` is green.
