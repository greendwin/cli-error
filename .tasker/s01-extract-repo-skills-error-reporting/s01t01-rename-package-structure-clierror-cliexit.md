---
id: s01t01
slug: rename-package-structure-clierror-cliexit
status: done
---

# Rename package, structure, CliError/CliExit types

## Goal

The `cli_error` package exists and exposes the two exception types. `CliError("File not found in [id]{commit}[/id]", commit=c)` stores an escaped-resolved message string; `CliExit("msg")` exists as a plain message-carrying exception; a param-free `make_console()` returns a Rich console themed with the internal default styles. The old `app_error`/`greet` scaffold is gone.

## Decisions & constraints

- **Rename** `app_error` → `cli_error` (import package) and distribution `app-error` → `cli-error`. Remove the `greet` placeholder (`core.py`) and its test.
- **Rich is a hard dependency** — add `rich` to `pyproject.toml` dependencies (was empty). Rich is already ubiquitous (Typer pulls it in); no optional extra, no plain-text fallback.
- **Private modules, flat public API** — internals live in `_errors.py`, `_reporter.py`, `_console.py`; `__init__.py` is the only public surface. This slice creates `_errors.py` (CliError, CliExit) and `_console.py` (param-free `make_console`).
- **Message = format-template + escaped args** — `CliError(template, **args)` resolves the template by substituting `escape()`-d argument values into placeholders, so untrusted data (brackets in a commit/branch/path) cannot break or inject markup. Template markup is trusted (developer-authored). Values interpolated inline in an f-string are a deliberate unescaped escape-hatch (caller's responsibility). Store the resolved markup string as the message; keep `str(ex)` a plain one-line message.
- **Structured fields deferred to render** — props/hint/details are added by the builder (next slice) and laid out at render time; this slice only needs the message-template behavior on `CliError` plus a bare `CliExit`.
- **`CliExit` is a clean exit, not a failure** — here it is just an exception storing a (markup-capable) message; its exit-0 handling arrives with the error handler slice.
- Naming: `AppError`→`CliError`, `NoopError`→`CliExit` (matches library identity; `CliExit` names the mechanism).

## Edge cases

- Argument value containing `[` / `]` must render literally (escaped), not as markup.
- A template with literal braces needs standard `{{`/`}}` escaping — document/confirm behavior.
- No-arg call `CliError("plain message")` must work unchanged.

## Key files

- `pyproject.toml` — `name = "cli-error"`, add `rich` dep, `[tool.hatch.build.targets.wheel] packages = ["src/cli_error"]`.
- `src/app_error/` → `src/cli_error/`: new `_errors.py` (CliError, CliExit), `_console.py` (param-free `make_console`), rewrite `__init__.py`, delete `core.py`.
- `tests/` — replace `test_core.py`; add `tests/test_errors.py`.
- `README.md` — minimal update so imports resolve (full docs come in the documentation slice).

## Acceptance criteria

- `from cli_error import CliError, CliExit, escape, make_console` succeeds.
- `CliError("in [id]{commit}[/id]", commit="a[b]c").message` contains the escaped `a[b]c` and does not corrupt the `[id]` styling.
- `str(CliError("plain"))` is `"plain"`.
- `CliExit("done")` constructs and carries its message.
- `make_console()` returns a Rich `Console` that renders `[err]x[/err]` without raising.
- `uv run tox` is green (no references to `app_error`/`greet` remain).
