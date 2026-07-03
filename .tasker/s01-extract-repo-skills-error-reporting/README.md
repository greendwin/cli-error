---
id: s01
slug: extract-repo-skills-error-reporting
status: pending
---

# Extract repo-skills error reporting into cli-error library

## Context

`cli-error` unifies error reporting across CLI tools: consistent semantic coloring, uniform error-report formatting, `--debug` tracebacks, and clean no-op exits. We are extracting the error-reporting solution from the repo-skills project and reimplementing its coloring — replacing helper functions (`fmt_ident()` etc.) with Rich named-style markup tokens (`[id]`, `[data]`, `[path]`, ...) that a project opts into via a Theme. Coloring must be optional per project, and interpolating untrusted values into styled messages must not be able to break or inject terminal markup. Decisions are recorded in `docs/adr/0001-error-formatting-and-theming.md`; domain vocabulary in `CONTEXT.md`.

## Decisions

- **Extract essentials only** — `CliError`, `CliExit`, `ErrorReporter`, render layout, `--debug` traceback, and the theme. *Rejected: pulling in repo-skills' `Console` spinner (`running`/`finish`), `debug_cmd`, `debug_output` — those are git/subprocess ergonomics, not error reporting; they stay in consuming apps.*
- **Package rename** — `app_error` → `cli_error` (distribution `cli-error`); base class `AppError` → `CliError`, `NoopError` → `CliExit`. Matches library identity; `CliExit` names the mechanism (clean exit-0), not a failure. *Rejected: keeping `AppError`/`NoopError` (mismatch with package name; "Error" suffix misleads for a success exit).*
- **Private modules, flat public API** — `_errors.py`, `_reporter.py`, `_console.py`; `__init__.py` re-exports `CliError`, `CliExit`, `ErrorReporter`, `make_console`, `DEFAULT_STYLES`, `escape` (re-exported from `rich.markup`). Domain subclasses (e.g. `FileNotInCommitError`) stay OUT of the library.
- **Rich is a hard dependency; theme is optional** — Rich is already transitively required by Typer, so it costs nothing. Only applying the theme is optional. *Verified: undefined tokens like `[id]…` degrade to plain text with no exception even on a forced color terminal — so a no-theme project runs cleanly and uncolored.* *Rejected: a `[rich]` extra with a plain-text fallback path (doubles rendering code for a ubiquitous dep).*
- **Consumer owns the console; no global singleton** — coloring is Rich named-style markup resolved by a Theme the consumer applies. *Rejected: global monkeypatching of styles; a library-owned global `console` singleton.*
- **Style roles + defaults** — `id`=green, `data`=cyan, `path`=dim, `cmd`=blue, `misc`=dim, `warn`=yellow, `err`=red. Roles are distinct even when they share a default color (a consumer may recolor any). `misc` = additional detail.
- **Merging factory** — `make_console(*, styles=None, no_color=False, ...)` builds a themed console from `DEFAULT_STYLES` updated with the caller's `styles` (override one role without redeclaring the palette); also expose the derived `Theme` for attaching to a pre-existing console. *Rejected: exposing only a full `Theme` object that must be redeclared wholesale.*
- **Structured fields, render at seam** — `CliError` stores message template + props + hint + details; layout happens in `ErrorReporter` at render time, not eagerly in `__init__`. Keeps `str(ex)` a plain one-line message and centralizes layout for uniformity. *Rejected: repo-skills' eager `fmt_message` string-building in `__init__`.*
- **Format-template + escaped args** — the message is a trusted template mixing markup and placeholders filled from ESCAPED arguments: `CliError("File not found in [id]{commit}[/id]", commit=commit)`. Untrusted data passed as args is safe by default; inline f-string interpolation is a deliberate unescaped escape-hatch (caller's responsibility). *Rejected: manual-escape-everywhere (foot-gun); a custom markup/parse layer (reinvents Rich's parser).*
- **Fluent, typed builder** — chained snake_case methods returning `self`: `prop_id`/`prop_path`/`prop_data`/`prop_cmd`/`prop_misc` (each escapes value + wraps in its role token), a role-less `prop(key, value)` (escaped; for no-theme/custom), `hint(text)` (markup-capable), and `detail(text)` (keyless block, escaped, styled `misc`, own line(s), no `key:` prefix). Props stay caller-unstyled; styling applied at the render seam. *Rejected: kwargs-only `props={...}` (can't express per-prop roles); PascalCase method names (non-idiomatic); the empty-string-key "hack" for detail blocks (reads as a bug).*
- **ErrorReporter is the single integration point** — `ErrorReporter(console)` constructed once in `main()`. Owns the `debug` flag (consumer sets `reporter.debug = True` from their own `--debug` wiring) and creates its OWN themed stderr console for tracebacks. Framework-agnostic — Rich-only, no Typer/Click dependency. *Rejected: passing the console to every call; a module-level "current console"; baking in a Typer callback helper.*
- **Handler + render behavior** — the context manager catches `CliExit` → print message through the themed stdout console (markup-capable) + `SystemExit(0)`; catches `Exception` → render + `SystemExit(1)`. `render_error` prints `[err]Error:[/err] <message>`, then props as `  <key>: <styled value>` (plain key, role-styled value, insertion order), a blank line before the hint, then the hint; then walks the cause chain (`__cause__ ?? __context__`) printing `  caused by: {escape(str(cause))}`, dedup by `id()`. When `reporter.debug` is set, the full traceback prints to the stderr console.

## Open questions

- None outstanding — all grill questions resolved.

## Out of scope

- Spinner / progress (`running`/`finish`) and subprocess-debug helpers (`debug_cmd`, `debug_output`) — remain in consuming apps.
- A Typer (or other framework) integration helper — may be added later if a real second consumer needs it.
- A `[rich]` optional-extra / plain-text (no-Rich) fallback path.
- Domain-specific `CliError` subclasses (they live in each consuming app).
- Migrating repo-skills itself to depend on `cli-error` (separate effort).

## Subtasks

- [x] [s01t01](s01t01-rename-package-structure-clierror-cliexit.md): Rename package, structure, CliError/CliExit types
- [x] [s01t02](s01t02-fluent-builder-for-clierror-context.md): Fluent builder for CliError context
- [x] [s01t03](s01t03-render-formatted-error.md): Render formatted error
- [x] [s01t04](s01t04-error-handler-errorreporter-context-manager.md): Error handler (ErrorReporter context manager)
- [ ] [s01t05](s01t05-cause-chain-rendering.md): Cause chain rendering
- [ ] [s01t06](s01t06-debug-traceback.md): Debug traceback
- [ ] [s01t07](s01t07-console-creation-with-style-overrides.md): Console creation with style overrides
- [ ] [s01t08](s01t08-library-documentation-readme.md): Library documentation (README)
- [ ] [s01t09](s01t09-deployment-setup-ci-release-workflows.md): Deployment setup (CI + release workflows)
- [x] [s01t10](s01t10-unify-markup-construction-template-args.md): Unify markup construction — template + args for hint and CliExit
- [x] [s01t11](s01t11-refine-detail-single-last-wins.md): Refine detail — single last-wins str block
- [x] [s01t12](s01t12-revisit-props-markup-first-prop.md): Revisit props: markup-first `prop` with template+args, roles as thin helpers
- [x] [s01t13](s01t13-store-detail-as-ready-to.md): Store detail as ready-to-print [misc] markup (restore render-seam invariant)
