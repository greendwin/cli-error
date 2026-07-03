---
id: s01t08
slug: library-documentation-readme
status: pending
---

# Library documentation (README)

## Goal

`README.md` documents `cli-error` for a consumer: install, the opt-in theme + semantic style roles, wiring `ErrorReporter` in `main()`, raising `CliError` with the fluent builder, `CliExit` for clean exits, and `--debug` wiring. Replaces the `greet` placeholder README.

## Decisions & constraints

- Document **only the shipped public API**: `CliError`, `CliExit`, `ErrorReporter`, `make_console`, `DEFAULT_STYLES`, `escape`.
- **Coloring is opt-in** — show applying the theme via `make_console` (and that undefined tokens degrade to plain text, so a no-theme project just works, uncolored).
- **Safety boundary explicit** — untrusted values go through template args (`CliError("... [id]{x}[/id]", x=x)`) or `prop_*`, which escape by default; inline f-string interpolation is the deliberate unescaped escape-hatch. Make this the headline usage guidance.
- Show the **style roles** table (`id`/`data`/`path`/`cmd`/`misc`/`warn`/`err` + defaults) and how to override via `make_console(styles=...)`.
- Show the end-to-end `main()` pattern: build console → `ErrorReporter(console)` → `with reporter.handler():` → map `--debug` onto `reporter.debug`.
- CONTEXT.md (glossary) and `docs/adr/0001-error-formatting-and-theming.md` already exist — link to the ADR rather than restating rationale.

## Edge cases

- Keep examples copy-pasteable and framework-agnostic (a plain `argparse`/`sys.argv` example, not Typer-specific), since the library has no framework dep.

## Key files

- `README.md` — full rewrite.
- (Optional) link from README to `CONTEXT.md` and `docs/adr/0001`.

## Acceptance criteria

- README covers: install, theme opt-in + roles table, `ErrorReporter` in `main()`, `CliError` builder example, `CliExit` example, `--debug` wiring, and the escape-hatch safety note.
- No references to `greet`/`app_error` remain.
- Code snippets are valid against the shipped API (import paths and signatures match).
- `uv run tox` is green.
