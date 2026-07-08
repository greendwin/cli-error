---
id: s01t0110
slug: unify-markup-construction-template-args
status: done
---

# Unify markup construction — template + args for hint and CliExit

## Goal

Every trusted-markup surface accepts the `(template, **args)` form (template is markup, args auto-escaped and substituted); every untrusted-value surface auto-escapes internally. Currently only `CliError.__init__` has template+args. Extend it to `hint` and `CliExit`.

## Notes captured (verbatim TODOs)

`src/cli_error/_errors.py` · `CliError.hint()`:
> # TODO: compose same as `CliExport` constr (template and args with escape)

`src/cli_error/_errors.py` · `CliExit.__init__`:
> # TODO: lets support `template` and `args` with escape

## Decisions & constraints

- **Markup-construction rule** — a surface that accepts trusted markup takes `(template, **args)`: the template is developer-authored markup, `args` are `escape(str(value))`-substituted. A surface that accepts an untrusted value (`prop_*` values, `detail` text) auto-escapes internally. The `(template, **args)` shape itself signals "markup here."
- **Shared helper** — extract the substitution currently inline in `CliError.__init__` (arg-free → store template verbatim; args → `template.format(**{k: escape(str(v))})`) into one helper reused by `CliError`, `CliError.hint`, and `CliExit`.
- **`hint(template, **args)`** — args escaped + substituted; arg-free call stores the template verbatim (identical semantics to `CliError.__init__`). Stays last-wins.
- **`CliExit(template, **args)`** — same. **Supersedes the `s01t01` decision** that "`CliExit` is just an exception storing a plain (markup-capable) message."
- **Amend `docs/adr/0001-error-formatting-and-theming.md`** — generalize its "Format-template + escaped args" decision from the message to all markup surfaces (message, `hint`, `CliExit`); add a Consequences note that this supersedes `s01t01`'s plain-`CliExit` decision.

## Edge cases

- Arg value containing `[`/`]` renders literally (escaped) in both `hint` and `CliExit`.
- Arg-free `hint("plain")` / `CliExit("plain")` store verbatim — literal `{...}` braces need no escaping.
- Templated call with a missing placeholder arg raises the standard `str.format` error (same as `CliError`).

## Key files

- `src/cli_error/_errors.py` — shared template+args helper; `hint(template, **args)`; `CliExit.__init__(template, **args)`. Remove both TODOs.
- `docs/adr/0001-error-formatting-and-theming.md` — amend as above.
- `tests/test_errors.py` — cover `hint` and `CliExit` template+args (escape, arg-free verbatim, bracket-literal) reusing the shared-helper behavior.

## Acceptance criteria

- `hint` and `CliExit` accept `(template, **args)`; args are escaped+substituted; arg-free calls store verbatim.
- Shared helper is the single place performing template+args escaping (no duplication across `CliError`/`hint`/`CliExit`).
- ADR-0001 amended and notes the `s01t01` supersession.
- Both TODO comments removed.
- `uv run tox` is green.
