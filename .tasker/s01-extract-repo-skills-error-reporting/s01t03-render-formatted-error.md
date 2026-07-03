---
id: s01t03
slug: render-formatted-error
status: pending
---

# Render formatted error

## Goal

`render_error(ex, console)` prints a `CliError` (or any exception) in the unified layout: `[err]Error:[/err] <message>`, then one `  key: <role-styled value>` line per prop (plain key, insertion order), a keyless `misc`-styled detail block, and — if present — a blank line followed by the markup-capable hint.

## Decisions & constraints

- **Reporter owns layout** — formatting lives in one place for uniformity across tools (not eagerly baked into each exception). This slice implements the standalone `render_error(ex, console)`; the context manager + exit codes come in the handler slice.
- **Render layout** (from ADR-0001):
  - `[err]Error:[/err] <message>` — message already has escaped args substituted (from the types slice).
  - props: `  {key}: {styled_value}` — **key plain/uncolored**, **value styled by its per-prop role** (`prop_path`→`[path]`, `prop_id`→`[id]`, ...), value escaped at this seam; insertion order.
  - `detail` blocks: own line(s), no `key:` prefix, styled `misc`, escaped.
  - `hint`: preceded by a blank line, rendered as trusted markup.
- **Non-`CliError` exceptions** — render `[err]Error:[/err] {escape(str(ex))}` (no props/hint/detail).
- Values are escaped **here** (the render seam), consistent with the builder storing them caller-unstyled.

## Edge cases

- No props / no hint / no detail — omit those sections cleanly (no stray blank lines).
- Hint present but no props — blank line still separates message from hint.
- Prop value / detail containing `[` `]` renders literally.
- Empty message — still prints the `Error:` prefix.

## Key files

- `src/cli_error/_reporter.py` — `render_error(ex, console)`.
- `tests/test_render.py` — capture console output (`Console.capture()` / `record`) and assert the rendered text/markup for CliError-with-everything, bare CliError, and non-CliError.

## Acceptance criteria

- A `CliError` with message + props (mixed roles) + detail + hint renders in the documented order with plain keys and role-styled values.
- A bare `CliError("boom")` renders exactly `Error: boom`.
- A non-`CliError` renders `Error: <escaped str>`.
- Sections absent when their data is absent; hint always preceded by a blank line when present.
- `uv run tox` is green.
