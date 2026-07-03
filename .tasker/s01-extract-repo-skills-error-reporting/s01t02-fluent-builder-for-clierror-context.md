---
id: s01t02
slug: fluent-builder-for-clierror-context
status: done
---

# Fluent builder for CliError context

## Goal

`CliError(...)` gains chained, caller-unstyled context builders: `.prop_id/.prop_path/.prop_data/.prop_cmd/.prop_misc`, a role-less `.prop`, `.hint`, and `.detail`, each returning `self` so raise sites read `raise CliError(...).prop_path("path", p).hint("...")`. This slice stores the structured context; layout/rendering comes next.

## Decisions & constraints

- **Fluent builder returning `self`** — methods mutate the exception and return it, enabling `raise CliError(...).prop_x(...).hint(...)`.
- **snake_case** method names (PEP 8; repo lints with flake8/black). *Rejected: PascalCase (`PropPath`) — reads like a type constructor.*
- **Typed per-role props** — `prop_id`, `prop_path`, `prop_data`, `prop_cmd`, `prop_misc` each take `(key, value)`, store the value tagged with its style role. The value is escaped and wrapped in its role token at the render seam (next slice), so props stay caller-unstyled and safe-by-default. *Rejected: kwargs-only `props={...}` — can't express mixed per-prop roles, which is exactly why repo-skills hand-wrapped each value with `fmt_*`.*
- **Role-less `prop(key, value)`** — escaped, no role token; the escape-hatch for projects not using the theme or wanting a plain row.
- **`detail(text)`** — a keyless block (captured subprocess output, etc.), stored to render on its own line(s) with no `key:` prefix, styled `misc`. *Rejected: repo-skills' empty-string-key hack (`props[""] = ...`) — reads as a bug.*
- **`hint(text)`** — markup-capable suggestion, stored to render after a blank line.
- Only the five context roles get typed methods; no `prop_warn`/`prop_err` (`warn`/`err` are prefix roles, not context values).

## Edge cases

- Multiple props preserve **insertion order**.
- Same `key` used twice — keep both in order (no dedup/overwrite) unless a test says otherwise; decide and cover.
- `detail` and `prop` values with markup characters must be escaped at render (assert the stored form supports it).
- Chaining order is arbitrary — `.hint(...).prop_id(...)` must work.

## Key files

- `src/cli_error/_errors.py` — add builder methods + backing structured storage (ordered props list, details list, hint) to `CliError`.
- `tests/test_errors.py` (or `tests/test_builder.py`) — one test per method + chaining/order tests.

## Acceptance criteria

- Each of `prop_id/prop_path/prop_data/prop_cmd/prop_misc/prop/hint/detail` has a dedicated test and returns `self`.
- Props render (or store) in insertion order with their role tag recoverable.
- `detail` stored as keyless; `hint` stored separately.
- Values are not styled at store time (styling is a render concern) — assert caller-unstyled storage.
- `uv run tox` is green.
